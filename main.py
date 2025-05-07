import requests
from bs4 import BeautifulSoup
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter


def scrape_fundamentus_fiis():
    url = "https://www.fundamentus.com.br/fii_resultado.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'tabelaResultado'})

        # Extrair cabeçalhos
        headers = [th.get_text(strip=True) for th in table.find('tr').find_all('th')]

        # Extrair dados das linhas
        data = []
        for row in table.find_all('tr')[1:]:
            row_data = [td.get_text(strip=True) for td in row.find_all('td')]
            data.append(row_data)

        # Criar DataFrame
        df = pd.DataFrame(data, columns=headers)

        # Renomear colunas para consistência (corrigindo a inversão)
        df = df.rename(columns={
            'Papel': 'Papel',
            'Segmento': 'Segmento',
            'Cotação': 'Cotacao',
            'FFO Yield': 'FFO Yield',
            'Dividend Yield': 'Dividend Yield',
            'P/VP': 'P/VP',  # Mantido como P/VP para maior clareza
            'Valor de Mercado': 'Valor de Mercado',
            'Liquidez': 'Liquidez',
            'Qtd de imóveis': 'Qtd Imoveis',
            'Preço do m2': 'Preco m2',
            'Aluguel por m2': 'Aluguel m2',
            'Cap Rate': 'Cap Rate',
            'Vacância Média': 'Vacancia Media'
        })

        return df

    except Exception as e:
        print(f"Erro ao acessar o site: {e}")
        return None


def clean_and_convert_data(df):
    # Converter valores numéricos - agora tratando corretamente Dividend Yield e P/VP
    df['Dividend Yield'] = df['Dividend Yield'].str.replace('%', '').str.replace('.', '').str.replace(',', '.').astype(
        float) / 100
    df['P/VP'] = df['P/VP'].str.replace(',', '.').astype(float)

    # Converter Valor de Mercado e Liquidez
    df['Valor de Mercado'] = df['Valor de Mercado'].apply(
        lambda x: float(x.replace('.', '')) if isinstance(x, str) else x)
    df['Liquidez'] = df['Liquidez'].apply(lambda x: float(x.replace('.', '')) if isinstance(x, str) else x)

    return df


def apply_filters(df):
    # Aplicar filtros atualizados
    filtered_df = df[
        (df['Dividend Yield'] > 0.10) &
        (df['Dividend Yield'] < 0.16) &
        (df['P/VP'] > 0.60) &
        (df['P/VP'] < 0.95) &
        (df['Liquidez'] > 1000000) &
        (df['Valor de Mercado'] > 1000000000)
        ].copy()

    return filtered_df


def calculate_score(row):
    score = 0

    # Dividend Yield (quanto maior melhor)
    if row['Dividend Yield'] >= 0.14:
        score += 2
    elif row['Dividend Yield'] >= 0.12:
        score += 1

    # P/VP (quanto menor melhor)
    if row['P/VP'] <= 0.80:
        score += 2
    elif row['P/VP'] <= 0.85:
        score += 1

    # Liquidez (quanto maior melhor)
    if row['Liquidez'] >= 5000000:
        score += 2
    elif row['Liquidez'] >= 2000000:
        score += 1

    # Valor de Mercado (quanto maior melhor)
    if row['Valor de Mercado'] >= 2000000000:
        score += 2
    elif row['Valor de Mercado'] >= 1500000000:
        score += 1

    return min(score, 8)  # Garantir que a nota máxima seja