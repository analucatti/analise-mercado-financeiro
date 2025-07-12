import requests
import pandas as pd
from datetime import datetime
import logging
from collections import defaultdict

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dividendos.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Configurações
TICKERS = ["BBSE3", "BBDC3", "BBAS3", "VIVT3", "SAPR11", "CMIG4", "ISAE4", "VBBR3", "PETR4", "CMIN3"]
MESES = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
ANOS_HISTORICO = 3  # Quantos anos de histórico analisar


def get_dividends(ticker):
    url = f"https://statusinvest.com.br/acao/companytickerprovents?ticker={ticker}&chartProventsType=2"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        logging.warning(f"Erro HTTP {response.status_code} para {ticker}")
    except Exception as e:
        logging.error(f"Falha na requisição para {ticker}: {str(e)}")
    return None


def analyze_historical_data(tickers):
    """Analisa padrões históricos e calcula probabilidades"""
    historico = {}

    for ticker in tickers:
        data = get_dividends(ticker)
        if not data or "assetEarningsModels" not in data:
            continue

        pagamentos = defaultdict(list)
        ano_atual = datetime.now().year
        anos_disponiveis = set()

        for provento in data["assetEarningsModels"]:
            try:
                if provento["et"] in ["Dividendo","JCP"]:
                    data_pagamento = provento["pd"]
                    if data_pagamento:
                        data_pag = datetime.strptime(data_pagamento, "%d/%m/%Y")
                        anos_disponiveis.add(data_pag.year)
                        mes = data_pag.strftime("%b").upper()
                        # Ajuste para os meses em português
                        mes = mes.replace("APR", "ABR").replace("MAY", "MAI").replace("AUG", "AGO").replace("SEP",
                                                                                                            "SET").replace(
                            "OCT", "OUT").replace("DEC", "DEZ")
                        pagamentos[mes].append(data_pag.year)
            except Exception as e:
                logging.error(f"Erro ao processar {ticker}: {str(e)}")
                continue

        # Calcula probabilidade para cada mês
        total_anos = len(anos_disponiveis)
        probabilidades = {}
        valores_medios = {}

        for mes, anos in pagamentos.items():
            # Probabilidade baseada na frequência histórica
            prob = len(set(anos)) / min(total_anos, ANOS_HISTORICO) * 100
            probabilidades[mes] = min(round(prob), 100)  # Limita a 100%

            # Calcula valor médio (simplificado)
            valores = [float(p["v"]) for p in data["assetEarningsModels"]
                       if p["et"] == "Dividendo" and
                       datetime.strptime(p["pd"], "%d/%m/%Y").strftime("%b").upper().replace("APR", "ABR").replace(
                           "MAY", "MAI").replace("AUG", "AGO").replace("SEP", "SET").replace("OCT", "OUT").replace(
                           "DEC", "DEZ") == mes]
            if valores:
                valores_medios[mes] = sum(valores) / len(valores)

        historico[ticker] = {
            'probabilidades': probabilidades,
            'valores_medios': valores_medios,
            'total_anos_analisados': min(total_anos, ANOS_HISTORICO)
        }

    return historico


def create_dividend_table(historico):
    """Cria tabela de dividendos com probabilidades"""
    df_prob = pd.DataFrame(index=TICKERS, columns=MESES)
    df_valores = pd.DataFrame(index=TICKERS, columns=MESES)

    for ticker, data in historico.items():
        for mes in MESES:
            if mes in data['probabilidades']:
                prob = data['probabilidades'][mes]
                valor = data['valores_medios'].get(mes, 0)

                # Formata a célula com probabilidade e valor
                df_prob.loc[ticker, mes] = f"{prob}%"
                df_valores.loc[ticker, mes] = f"R$ {valor:.2f}".replace(".", ",")

    return df_prob, df_valores


def generate_markdown(prob_table, value_table, historico):
    """Gera relatório em Markdown com os dados formatados"""
    md_content = "# PREVISÃO DE DIVIDENDOS\n\n"

    # Tabela principal
    md_content += "| Ativo | " + " | ".join(MESES) + " |\n"
    md_content += "|-------|" + "|".join(["---"] * len(MESES)) + "|\n"

    for ticker in TICKERS:
        if ticker in historico:
            md_content += f"| **{ticker}** |"
            for mes in MESES:
                prob = prob_table.loc[ticker, mes]
                valor = value_table.loc[ticker, mes]
                if pd.isna(prob):
                    md_content += " |"
                else:
                    md_content += f" {prob} ({valor}) |"
            md_content += "\n"

    # Detalhes por ativo
    md_content += "\n## Detalhes por Ativo\n"
    for ticker, data in historico.items():
        md_content += f"\n### {ticker}\n"
        md_content += f"**Anos analisados:** {data['total_anos_analisados']}\n\n"

        for mes, prob in data['probabilidades'].items():
            valor = data['valores_medios'].get(mes, 0)
            md_content += (
                f"- **{mes}:** {prob}% de probabilidade | "
                f"Valor médio: R$ {valor:.2f}\n".replace(".", ",")
            )

    return md_content


if __name__ == "__main__":
    logging.info("==== INÍCIO DA EXECUÇÃO ====")

    # 1. Analisa dados históricos
    historico = analyze_historical_data(TICKERS)

    # 2. Cria tabelas
    prob_table, value_table = create_dividend_table(historico)

    # 3. Gera Markdown
    md_content = generate_markdown(prob_table, value_table, historico)

    # 4. Salva resultados
    with open("PREVISAO_DIVIDENDOS.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    logging.info("Markdown salvo em 'PREVISAO_DIVIDENDOS.md'")

    # 5. Salva tabela de valores para Excel
    value_table.fillna("", inplace=True)
    value_table.to_excel("valores_dividendos.xlsx")
    logging.info("Planilha salva em 'valores_dividendos.xlsx'")

    logging.info("==== FIM DA EXECUÇÃO ====")