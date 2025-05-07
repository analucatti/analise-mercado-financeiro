# Fundos Imobiliários - Análise e Filtros

## Como o Programa Funciona:

1. **Raspagem de Dados**:  
   O programa acessa o site Fundamentus e extrai a tabela completa de fundos imobiliários.

2. **Limpeza e Conversão**:  
   Converte os valores textuais para formatos numéricos adequados (porcentagens, valores monetários, etc.).

3. **Aplicação de Filtros**:  
   - **Dividend Yield**: entre 10% e 16%  
   - **P/VP**: entre 0.6 e 0.95  
   - **Liquidez**: acima de 1 milhão  
   - **Valor de Mercado**: acima de 1 bilhão  

4. **Cálculo da Nota**:  
   Atribui uma nota de 0 a 8 baseada nos seguintes critérios:  
   - **Dividend Yield**: quanto maior, melhor  
   - **P/VP**: quanto menor, melhor  
   - **Liquidez**: quanto maior, melhor  
   - **Valor de Mercado**: quanto maior, melhor  

5. **Saída em Excel**:  
   Gera um arquivo Excel formatado com cores, bordas e alinhamentos profissionais.

---

## Requisitos:

- **Python**: versão 3.x  
- **Bibliotecas**:  
  - `pandas`  
  - `requests`  
  - `beautifulsoup4`  
  - `openpyxl`  

---

## Instalação das Dependências:

```bash
pip install pandas requests beautifulsoup4 openpyxl