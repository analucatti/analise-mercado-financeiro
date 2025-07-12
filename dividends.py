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

                        # Formata o valor
                        valor_str = f"{valor:.4f}".replace(".", ",").rstrip("0").rstrip(",")

                        # Consolida valores por mês
                        if df.loc[ticker, mes]:
                            try:
                                current = float(df.loc[ticker, mes].replace(',', '.'))
                                new = float(valor_str.replace(',', '.'))
                                df.loc[ticker, mes] = f"{current + new:.4f}".replace(".", ",").rstrip("0").rstrip(",")
                            except ValueError:
                                continue
                        else:
                            df.loc[ticker, mes] = valor_str

                        logging.info(f"[DIVIDENDO] {ticker}: {mes} = R$ {valor_str}")
            except ValueError as e:
                # Ignora erros de formatação de data/valor sem logar
                continue
            except Exception as e:
                logging.error(f"Erro inesperado ao processar {ticker}: {str(e)}")
                continue

    return df


if __name__ == "__main__":
    logging.info("==== INÍCIO DA EXECUÇÃO ====")

    tabela = create_dividend_table(TICKERS)

    # Garante todas as colunas de meses
    for mes in MESES:
        if mes not in tabela.columns:
            tabela[mes] = ""
    tabela = tabela[MESES]  # Reordena colunas


    # Prepara saída formatada
    def format_value(x):
        return x if x else "-"


    # Salva os resultados
    try:
        # Excel - mantém células vazias
        tabela.to_excel("dividendos.xlsx")
        logging.info("Planilha salva em 'dividendos.xlsx'")

        # Markdown - substitui vazios por espaço
        with open("dividendos.md", "w", encoding="utf-8") as f:
            f.write("# PREVISÃO DE DIVIDENDOS\n\n")
            md_table = tabela.copy().applymap(format_value)
            f.write(md_table.to_markdown())
        logging.info("Markdown salvo em 'dividendos.md'")

        # Console - exibe tabela formatada
        print("\nTABELA DE DIVIDENDOS:")
        console_table = tabela.copy().applymap(format_value)
        print(console_table.to_string())

    except Exception as e:
        logging.error(f"Erro ao salvar arquivos: {str(e)}")

    logging.info("==== FIM DA EXECUÇÃO ====")