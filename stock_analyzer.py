import json
import os
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

# Dicionário para cache de setores
SETOR_CACHE_FILE = 'setor_cache.json'


def load_setor_cache():
    """Carrega o cache de setores do arquivo"""
    if os.path.exists(SETOR_CACHE_FILE):
        with open(SETOR_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_setor_cache(cache):
    """Salva o cache de setores no arquivo"""
    with open(SETOR_CACHE_FILE, 'w') as f:
        json.dump(cache, f)


def get_setor(papel, cache):
    """Obtém o setor de uma ação, usando cache quando possível"""
    if papel in cache:
        return cache[papel]

    url = f"https://www.fundamentus.com.br/detalhes.php?papel={papel}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrar a tabela de dados básicos
        table = soup.find('table', {'class': 'w728'})
        if not table:
            return "Setor não encontrado"

        # Procurar a linha que contém o setor
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2 and 'Setor' in cols[0].get_text():
                setor = cols[1].get_text(strip=True)
                cache[papel] = setor  # Atualizar cache
                return setor

        return "Setor não encontrado"
    except Exception as e:
        print(f"Erro ao obter setor para {papel}: {e}")
        return "Erro ao obter setor"


def scrape_fundamentus_acoes():
    """Raspa os dados principais da tabela de resultados"""
    url = "https://www.fundamentus.com.br/resultado.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'resultado'})

        if not table:
            print("Erro: Não foi possível encontrar a tabela de dados no site.")
            return None

        # Extrair cabeçalhos
        headers = [th.get_text(strip=True) for th in table.find('tr').find_all('th')]

        # Extrair dados das linhas
        data = []
        for row in table.find_all('tr')[1:]:
            row_data = [td.get_text(strip=True) for td in row.find_all('td')]
            data.append(row_data)

        # Criar DataFrame
        df = pd.DataFrame(data, columns=headers)

        return df

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar o site: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None


def clean_and_convert_data(df):
    """Limpa e converte os dados"""
    try:
        # Verificar colunas necessárias
        required_columns = ['Papel', 'P/L', 'P/VP', 'Div.Yield', 'ROE', 'Liq.2meses', 'Dív.Brut/ Patrim.',
                            'Cresc. Rec.5a']
        for col in required_columns:
            if col not in df.columns:
                print(f"Coluna não encontrada: {col}")
                return None

        # Encontrar coluna de dívida
        div_patrim_col = None
        for col in df.columns:
            if 'Dív.Brut/ Patrim.' in col:
                div_patrim_col = col
                break

        if not div_patrim_col:
            print("Coluna 'Dív.Brut/ Patrim.' não encontrada")
            return None

        # Converter valores numéricos
        df['P/L'] = df['P/L'].str.replace('.', '').str.replace(',', '.').astype(float)
        df['P/VP'] = df['P/VP'].str.replace('.', '').str.replace(',', '.').astype(float)
        df['Div.Yield'] = df['Div.Yield'].str.replace('%', '').str.replace('.', '').str.replace(',', '.').astype(float) / 100
        df['ROE'] = df['ROE'].str.replace('%', '').str.replace('.', '').str.replace(',', '.').astype(float) / 100
        df['Liq.2meses'] = df['Liq.2meses'].str.replace('.', '').str.replace(',', '.').astype(float)
        df[div_patrim_col] = df[div_patrim_col].str.replace('.', '').str.replace(',', '.').astype(float)
        df['Cresc. Rec.5a'] = df['Cresc. Rec.5a'].str.replace('%', '').str.replace('.', '').str.replace(',',
                                                                                                        '.').astype(
            float) / 100

        # Renomear colunas
        df = df.rename(columns={
            'Div.Yield': 'Div.Yield',
            'Liq.2meses': 'Ltg.2meses',
            div_patrim_col: 'Dív.Brut/Patrim',
            'Cresc. Rec.5a': 'Cresc.Rec.5a'
        })

        return df

    except Exception as e:
        print(f"Erro ao converter dados: {e}")
        return None


def apply_filters(df):
    """Aplica os filtros especificados ao DataFrame"""
    try:
        # Aplicar filtros conforme especificado
        filtered_df = df[
            (df['P/L'] > 3) &
            (df['P/L'] < 12) &
            (df['P/VP'] > 0.5) &
            (df['P/VP'] < 1.1) &
            (df['ROE'] > 0.14) &
            (df['ROE'] < 0.50) &
            (df['Div.Yield'] > 0.07) &
            (df['Div.Yield'] < 0.25) &
            (df['Cresc.Rec.5a'] > 0.10) &
            (df['Dív.Brut/Patrim'] < 2) &
            (df['Ltg.2meses'] > 1000000)
            ].copy()

        return filtered_df
    except Exception as e:
        print(f"Erro ao aplicar filtros: {e}")
        return None


def calculate_score(row):
    """Calcula a pontuação para cada ação"""
    try:
        score = 0

        # P/L (quanto menor melhor)
        if row['P/L'] <= 5:
            score += 2
        elif row['P/L'] <= 7:
            score += 1

        # P/VP (quanto menor melhor)
        if row['P/VP'] <= 0.7:
            score += 2
        elif row['P/VP'] <= 0.9:
            score += 1

        # Dividend Yield (quanto maior melhor)
        if row['Div.Yield'] >= 0.12:
            score += 2
        elif row['Div.Yield'] >= 0.09:
            score += 1

        # ROE (quanto maior melhor)
        if row['ROE'] >= 0.20:
            score += 2
        elif row['ROE'] >= 0.17:
            score += 1

        # Crescimento Receita (quanto maior melhor)
        if row['Cresc.Rec.5a'] >= 0.20:
            score += 2
        elif row['Cresc.Rec.5a'] >= 0.15:
            score += 1

        # Dívida Bruta/Patrimônio (quanto menor melhor)
        if row['Dív.Brut/Patrim'] <= 0.5:
            score += 2
        elif row['Dív.Brut/Patrim'] <= 1:
            score += 1

        # Liquidez (quanto maior melhor)
        if row['Ltg.2meses'] >= 50000000:
            score += 2
        elif row['Ltg.2meses'] >= 10000000:
            score += 1

        return min(score, 12)  # Nota máxima de 12 pontos
    except Exception as e:
        print(f"Erro ao calcular score: {e}")
        return 0


def add_setor_info(df, cache):
    """Adiciona informações de setor às ações filtradas"""
    print("\nObtendo setores para as ações selecionadas...")
    df['Setor'] = df['Papel'].apply(lambda x: get_setor(x, cache))
    time.sleep(1)  # Delay para não sobrecarregar o servidor
    return df


def get_top_by_sector(df, n=5):
    """Retorna os top N ações de cada setor"""
    if df.empty or 'Setor' not in df.columns:
        return pd.DataFrame()

    # Agrupar por setor e pegar os top N de cada grupo
    top_by_sector = df.sort_values(['Setor', 'Nota', 'Div.Yield'],
                                   ascending=[True, False, False]) \
        .groupby('Setor') \
        .head(n) \
        .sort_values(['Setor', 'Nota'], ascending=[True, False])

    return top_by_sector


def style_excel_output(writer, df, sheet_name='Top por Setor'):
    """Formata a saída do Excel"""
    try:
        workbook = writer.book
        worksheet = workbook[sheet_name]

        # Definir estilos
        header_fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
        header_font = Font(color='FFFFFF', bold=True)
        align_center = Alignment(horizontal='center', vertical='center')
        thin_border = Border(left=Side(style='thin'),
                             right=Side(style='thin'),
                             top=Side(style='thin'),
                             bottom=Side(style='thin'))

        # Aplicar estilos ao cabeçalho
        for col in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = align_center
            cell.border = thin_border

            # Ajustar largura das colunas
            column_letter = get_column_letter(col)
            worksheet.column_dimensions[column_letter].width = 12
            if df.columns[col - 1] == 'Setor':
                worksheet.column_dimensions[column_letter].width = 28

        # Aplicar estilos aos dados
        for row in range(2, len(df) + 2):
            for col in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=row, column=col)
                cell.alignment = Alignment(horizontal='center')
                cell.border = thin_border

        # Formatar porcentagens
        for col_name in ['Div.Yield', 'ROE', 'Cresc.Rec.5a']:
            if col_name in df.columns:
                col_idx = df.columns.get_loc(col_name) + 1
                for row in range(2, len(df) + 2):
                    cell = worksheet.cell(row=row, column=col_idx)
                    cell.number_format = '0.00%'

        # Formatar números decimais
        for col_name in ['P/L', 'P/VP', 'Dív.Brut/Patrim']:
            if col_name in df.columns:
                col_idx = df.columns.get_loc(col_name) + 1
                for row in range(2, len(df) + 2):
                    cell = worksheet.cell(row=row, column=col_idx)
                    cell.number_format = '0.00'

        # Formatar Liquidez como número inteiro
        if 'Ltg.2meses' in df.columns:
            ltg_col = df.columns.get_loc('Ltg.2meses') + 1
            for row in range(2, len(df) + 2):
                cell = worksheet.cell(row=row, column=ltg_col)
                cell.number_format = '#,##0'

        # Adicionar formatação condicional para a coluna Nota
        if 'Nota' in df.columns:
            nota_col = df.columns.get_loc('Nota') + 1
            for row in range(2, len(df) + 2):
                cell = worksheet.cell(row=row, column=nota_col)
                if cell.value >= 8:
                    cell.fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
                elif cell.value >= 5:
                    cell.fill = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')
                else:
                    cell.fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')

        # Congelar painel
        worksheet.freeze_panes = 'A2'
    except Exception as e:
        print(f"Erro ao formatar arquivo Excel: {e}")


def verificar_arquivo_existente(nome_arquivo):
    """Verifica se o arquivo já existe e pergunta ao usuário se deseja substituí-lo"""
    if os.path.exists(nome_arquivo):
        print(f"\nAVISO: O arquivo '{nome_arquivo}' já existe no diretório.")
        # substituir = input("Deseja substituí-lo? (S/N): ").strip().upper()
        # return substituir == 'S'
    return True


def main():
    # Carregar cache de setores
    setor_cache = load_setor_cache()

    print("\n=== Análise de Ações Fundamentus ===")
    print("Fonte: https://www.fundamentus.com.br/resultado.php")

    output_file = "acoes_filtradas_fundamentus.xlsx"

    # Verificar se o arquivo já existe
    if not verificar_arquivo_existente(output_file):
        print("Operação cancelada pelo usuário.")
        return

    print("\nIniciando raspagem de dados do Fundamentus...")
    df = scrape_fundamentus_acoes()

    if df is not None:
        print("Dados obtidos com sucesso! Processando...")
        df = clean_and_convert_data(df)

        if df is not None:
            filtered_df = apply_filters(df)

            if filtered_df is not None:
                if len(filtered_df) > 0:
                    # Calcular nota para cada ação
                    filtered_df['Nota'] = filtered_df.apply(calculate_score, axis=1)

                    # Selecionar e ordenar colunas (top 30 ações)
                    final_df = filtered_df[['Papel', 'P/L', 'P/VP', 'Div.Yield', 'ROE',
                                            'Ltg.2meses', 'Dív.Brut/Patrim', 'Cresc.Rec.5a', 'Nota']]
                    final_df = final_df.sort_values(by=['Nota', 'Div.Yield'], ascending=[False, False])
                    final_df = final_df.head(30)  # Pegar apenas as top 30 ações

                    # Adicionar informação de setor apenas para as ações selecionadas
                    final_df = add_setor_info(final_df, setor_cache)

                    # Pegar os top 5 de cada setor
                    top_by_sector = get_top_by_sector(final_df, 5)

                    try:
                        # Salvar em Excel
                        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                            # Salvar todas as ações filtradas
                            final_df.to_excel(writer, index=False, sheet_name='Top 30 Ações')

                            # Salvar os top 5 por setor (se houver setores identificados)
                            if not top_by_sector.empty and 'Setor' in final_df.columns:
                                top_by_sector.to_excel(writer, index=False, sheet_name='Top por Setor')
                                style_excel_output(writer, top_by_sector, 'Top por Setor')

                            # Formatar a aba principal
                            style_excel_output(writer, final_df, 'Top 30 Ações')

                        print(f"\nProcesso concluído com sucesso!")
                        print(f"Arquivo salvo como: {os.path.abspath(output_file)}")
                        print(f"Total de ações encontradas: {len(final_df)}")

                        if not top_by_sector.empty and 'Setor' in final_df.columns:
                            print("\nTop 5 ações por setor:")
                            for sector, group in top_by_sector.groupby('Setor'):
                                print(f"\nSetor: {sector}")
                                print(group[['Papel', 'Nota', 'Div.Yield', 'P/VP', 'ROE']].to_string(index=False))

                    except Exception as e:
                        print(f"\nErro ao salvar o arquivo: {e}")
                else:
                    print("\nNenhuma ação atende aos critérios de filtro especificados.")
            else:
                print("\nErro ao filtrar os dados.")
        else:
            print("\nErro ao processar os dados.")
    else:
        print("\nNão foi possível obter os dados do site.")

    # Salvar cache antes de sair
    save_setor_cache(setor_cache)


if __name__ == "__main__":
    main()