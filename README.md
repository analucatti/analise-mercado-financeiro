# 📊 Análise de Investimentos - Fundos Imobiliários e Ações

## 📌 Programas Disponíveis

### 1️⃣ Análise de Fundos Imobiliários (FIIs)

#### 🔍 Como Funciona:
1. **Raspagem de Dados**  
   Acessa automaticamente o [Fundamentus](https://www.fundamentus.com.br/fii_resultado.php) e extrai todos os FIIs listados

2. **Padronização dos Dados**  
   Conversão automática de:
   - Porcentagens (DY, P/VP)
   - Valores monetários (liquidez, valor de mercado)

3. **🔎 Filtros Avançados**  
   ```
   (DY > 10%) & (DY < 16%) 
   & (P/VP > 0.6) & (P/VP < 0.95)
   & (Liquidez > 1.000.000)
   & (Valor Mercado > 1.000.000.000)
    ```
   
4. **⭐ Sistema de Pontuação (0-8 pontos)**  

   | Critério         | Peso | Bom          | Ótimo        |
   |------------------|------|--------------|--------------|
   | Dividend Yield   | 2    | >13% (+1)    | >15% (+2)    |
   | P/VP             | 2    | <0.85 (+1)   | <0.80 (+2)   |
   | Liquidez         | 2    | >2M (+1)     | >5M (+2)     |
   | Valor Mercado    | 2    | >1.5B (+1)   | >2B (+2)     |

5. **📤 Saída**  
   Gera o arquivo `fundos_imobiliarios_filtrados.xlsx` com:  
   - 🟢🟡🔴 **Cores condicionais**  
   - 📊 **Formatação profissional**  
   - 🔢 **Dados prontos para análise**  

---

### 2️⃣ Análise de Ações

#### 🔍 Como Funciona:
1. **Coleta Completa**  
   Extrai todos os dados de resultado de ações.

2. **Tratamento Inteligente**  
   - Detecta automaticamente formatos diferentes.  
   - Lida com variações nos nomes das colunas.

3. **🎯 Filtros Especializados**

```(P/L 3.5-12) & (P/VP 0.5-1.1)
& (ROE 14%-30%) & (DY 7%-20%)
& (Cresc.Rec >10%) & (Dívida<2)
& (Liquidez>1M)
```

**📈 Sistema de Pontuação (0-12 pontos)**  

   | Critério            | Peso | Meta           | Excelência     |
   |---------------------|------|----------------|----------------|
   | P/L                | 2    | <7 (+1)        | <5 (+2)        |
   | P/VP               | 2    | <0.9 (+1)      | <0.7 (+2)      |
   | DY                 | 2    | >9% (+1)       | >12% (+2)      |
   | ROE                | 2    | >17% (+1)      | >20% (+2)      |
   | Cresc. Receita     | 2    | >15% (+1)      | >20% (+2)      |
   | Dívida/Patrimônio  | 1    | <1 (+1)        | <0.5 (+2)      |
   | Liquidez           | 1    | >10M (+1)      | >50M (+2)      |

4. **📤 Saída**  
   Gera o arquivo `acoes_filtradas_fundamentus.xlsx` com:  
   - 💵 **Valores em dólar**  
   - 📈 **Gráficos condicionais**  
   - 🏆 **Top 5 ações destacadas**  

---

## ⚙️ Configuração

### 📋 Requisitos
- **Python**: versão 3.6+  
- **Dependências**:  
   ```bash
   pip install -r requirements.txt
    ```
Arquivo requirements.txt:

```plaintext
pandas>=1.3.0
   requests>=2.26.0
   beautifulsoup4>=4.10.0
   openpyxl>=3.0.9
```   

### 🚀 Execução
```
# Para FIIs
python fii_analyzer.py

# Para Ações
python stock_analyzer.py
```
### 📂 Exemplo de Saída
## **Estrutura do Relatório:**
```plaintext
📂 resultados/
├── 📄 fundos_imobiliarios_filtrados.xlsx
└── 📄 acoes_filtradas_fundamentus.xlsx
```

## **Relatório Inclui:**

- 🔢 Dados numéricos tratados
- 📊 Formatação profissional
- 🎨 Códigos de cores:
  - 🟢 Nota ≥ 8 (Excelente)
  - 🟡 Nota 5-7 (Bom)
  - 🔴 Nota <5 (Atenção)

---

# ❗ Importante
- ⚠️ Verificação automática de arquivos existentes
- 🔄 Atualização conforme mudanças no site
- ⚙️ Filtros customizáveis no código

✉️ Suporte: analucatti23@gmail.com