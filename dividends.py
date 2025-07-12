import requests
import pandas as pd
from datetime import datetime
import logging

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
TICKERS = ["BBAS3", "BBSE3", "CMIN3", "CMIG4", "PETR4", "ISAE4", "VBBR3", "BBDC3"]
MESES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


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


def format_currency(value):
    """Formata o valor como moeda brasileira com 2 casas decimais"""
    if pd.isna(value) or value == "":
        return ""
    try:
        # Se já estiver formatado como R$, retorna o próprio valor
        if isinstance(value, str) and value.startswith("R$"):
            return value
        # Converte para float e formata
        return f"R$ {float(value):.2f}".replace(".", ",")
    except (ValueError, TypeError):
        return value


def create_dividend_table(tickers):
    df = pd.DataFrame(index=tickers, columns=MESES)
    df.fillna("", inplace=True)

    for ticker in tickers:
        data = get_dividends(ticker)
        if not data or "assetEarningsModels" not in data:
            continue

        for provento in data["assetEarningsModels"]:
            try:
                if provento["et"] == "Dividendo":
                    data_pagamento = provento["pd"]
                    valor = provento["v"]

                    # Processa apenas se tiver dados válidos
                    if data_pagamento and valor:
                        data_pagamento = datetime.strptime(data_pagamento, "%d/%m/%Y")
                        mes = data_pagamento.strftime("%b").upper()

                        # Consolida valores por mês
                        if df.loc[ticker, mes] not in ["", None]:
                            try:
                                current = float(str(df.loc[ticker, mes]).replace('R$ ', '').replace(',', '.'))
                                new = float(valor)
                                total = current + new
                                df.loc[ticker, mes] = total
                            except ValueError:
                                continue
                        else:
                            df.loc[ticker, mes] = float(valor)

                        logging.info(f"[DIVIDENDO] {ticker}: {mes} = R$ {float(valor):.2f}")
            except ValueError as e:
                continue
            except Exception as e:
                logging.error(f"Erro inesperado ao processar {ticker}: {str(e)}")
                continue

    # Formata todos os valores como moeda
    for col in df.columns:
        df[col] = df[col].apply(lambda x: format_currency(x) if x not in ["", None] else "")
    return df


def add_summary_row(df):
    """Adiciona uma linha de soma ao final do DataFrame"""
    summary = pd.DataFrame(index=["TOTAL"], columns=df.columns)

    for mes in df.columns:
        total = 0.0
        for valor in df[mes]:
            if valor and valor != "":
                try:
                    # Remove 'R$ ' e converte vírgula para ponto
                    num = float(str(valor).replace('R$ ', '').replace(',', '.'))
                    total += num
                except ValueError:
                    continue
        if total > 0:
            summary.loc["TOTAL", mes] = format_currency(total)
        else:
            summary.loc["TOTAL", mes] = ""

    return pd.concat([df, summary])


if __name__ == "__main__":
    logging.info("==== INÍCIO DA EXECUÇÃO ====")

    tabela = create_dividend_table(TICKERS)

    # Garante todas as colunas de meses
    for mes in MESES:
        if mes not in tabela.columns:
            tabela[mes] = ""
    tabela = tabela[MESES]  # Reordena colunas

    # Cria tabela com soma para o Markdown
    tabela_com_soma = add_summary_row(tabela)


    # Prepara saída formatada
    def format_value(x):
        return x if x not in ["", None] else "-"


    # Salva os resultados
    try:
        # Excel - mantém células vazias (sem soma)
        # Remove formatação de moeda para o Excel
        tabela_sem_format = tabela.copy()
        tabela_sem_format = tabela_sem_format.applymap(
            lambda x: float(str(x).replace('R$ ', '').replace(',', '.'))
            if x not in ["", None] else "")
        tabela_sem_format.to_excel("dividendos.xlsx")
        logging.info("Planilha salva em 'dividendos.xlsx'")

        # Markdown - substitui vazios por espaço e inclui soma
        with open("dividendos.md", "w", encoding="utf-8") as f:
            f.write("# PREVISÃO DE DIVIDENDOS\n\n")
            md_table = tabela_com_soma.copy().applymap(format_value)
            f.write(md_table.to_markdown())
        logging.info("Markdown salvo em 'dividendos.md'")

        # Console - exibe tabela formatada (sem soma)
        print("\nTABELA DE DIVIDENDOS:")
        console_table = tabela.copy().applymap(format_value)
        print(console_table.to_string())

    except Exception as e:
        logging.error(f"Erro ao salvar arquivos: {str(e)}")

    logging.info("==== FIM DA EXECUÇÃO ====")