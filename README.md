# 📊 Sistema Avançado de Análise de Investimentos

## 🚀 Visão Geral
Suite completa de análise fundamentalista para o mercado brasileiro, com três módulos especializados para tomada de decisão baseada em dados.

---

## 📌 Módulos Disponíveis

### 1️⃣ **Análise de Fundos Imobiliários (FIIs)**

#### 🏗️ Arquitetura Modular
- **`FundamentusScraper`**: Coleta dados com retry automático
- **`DataProcessor`**: Limpeza e validação de dados
- **`FIIAnalyzer`**: Motor de análise e scoring
- **`ExcelExporter`**: Geração de relatórios formatados

#### 🔍 Funcionalidades Principais

**📥 Coleta de Dados**
- Raspagem do [Fundamentus](https://www.fundamentus.com.br/fii_resultado.php)
- Session pooling para melhor performance
- Retry automático com backoff exponencial
- Tratamento robusto de erros

**🎯 Sistema de Filtros Configuráveis**
```python
FilterCriteria:
  - Dividend Yield: 7% - 25%
  - P/VP: 0.5 - 1.1
  - Liquidez: > R$ 1.000.000
  - Valor Mercado: > R$ 1.000.000.000
```

**⭐ Scoring Avançado (0-10 pontos)**

| Métrica | Excelente (+2) | Bom (+1) | Peso |
|---------|---------------|----------|------|
| DY | ≥14% | ≥12% | Alto |
| P/VP | ≤0.80 | ≤0.85 | Alto |
| Liquidez | ≥R$5M | ≥R$2M | Médio |
| Valor Mercado | ≥R$2B | ≥R$1.5B | Médio |
| Vacância | ≤5% | ≤10% | Alto |

**📤 Saídas**
- Excel multi-abas com formatação profissional
- Top 5 fundos por segmento
- Análise estatística completa
- Logs detalhados para auditoria

---

### 2️⃣ **Análise de Ações**

#### 🏗️ Arquitetura Otimizada
- **`StatusInvestScraper`**: Coleta paralela com ThreadPool
- **`SectorEnricher`**: Enriquecimento com setores (multi-thread)
- **`StockAnalyzer`**: Análise fundamentalista
- **`SectorCache`**: Cache inteligente thread-safe

#### 🔍 Funcionalidades Avançadas

**🚄 Performance**
- **Coleta paralela**: 5-10x mais rápido
- **Cache persistente**: Reduz requisições em 90%
- **Rate limiting**: Evita bloqueios
- **Session reuse**: Conexões otimizadas

**🎯 Filtros Fundamentalistas**
```python
FilterCriteria:
  - P/L: 3.0 - 12.0
  - P/VP: 0.5 - 1.1  
  - ROE: 14% - 50%
  - DY: 7% - 25%
  - Crescimento 5a: > 10%
  - Dívida/Patrimônio: < 2.0
  - Liquidez 2m: > R$ 1.000.000
```

**⭐ Sistema de Pontuação (0-14 pontos)**

| Indicador | Excelente (+2) | Bom (+1) | Importância |
|-----------|---------------|----------|-------------|
| P/L | ≤5 | ≤7 | Critical |
| P/VP | ≤0.7 | ≤0.9 | Critical |
| DY | ≥12% | ≥9% | High |
| ROE | ≥20% | ≥17% | High |
| Crescimento | ≥20% | ≥15% | Medium |
| Dívida/Patrim | ≤0.5 | ≤1.0 | High |
| Liquidez | ≥R$50M | ≥R$10M | Medium |

**📊 Recursos Extras**
- Identificação automática de setores
- Cache JSON para otimização
- Top 30 ações rankeadas
- Top 5 por setor
- Análise estatística do portfólio

---

### 3️⃣ **Sistema de Previsão de Dividendos** 🆕

#### 🏗️ Arquitetura Preditiva
- **`StatusInvestScraper`**: Coleta histórica de proventos
- **`DividendAnalyzer`**: Machine Learning-like predictions
- **`DividendCache`**: Cache com TTL configurável
- **`ReportGenerator`**: Relatórios multi-formato

#### 🔮 Funcionalidades de IA

**📈 Análise Preditiva**
- Detecção automática de padrões de pagamento
- Cálculo de probabilidades mensais
- Previsão de próximos pagamentos
- Score de confiança para cada previsão

**🎯 Métricas Estatísticas**
```python
MonthlyStatistics:
  - Probabilidade de pagamento
  - Valor médio histórico
  - Desvio padrão
  - Mediana dos valores
  - Anos de ocorrência
  - Score de confiança
```

**🔍 Padrões Detectados**
- **Mensal**: Pagamentos regulares mensais
- **Trimestral**: A cada 3 meses
- **Semestral**: 2x ao ano
- **Anual**: 1x ao ano
- **Irregular**: Sem padrão definido

**📊 Relatórios Gerados**

1. **Markdown** (`PREVISAO_DIVIDENDOS.md`)
   - Tabela de probabilidades
   - Previsões com confiança
   - Análise detalhada por ativo

2. **Excel** (`dividendos_analise.xlsx`)
   - Aba de probabilidades
   - Aba de previsões
   - Aba de estatísticas

3. **JSON** (`dividendos_data.json`)
   - Dados estruturados para APIs
   - Metadados completos
   - Serialização de objetos

---

## ⚙️ Instalação e Configuração

### 📋 Requisitos
```bash
Python 3.8+
```

### 📦 Dependências
```bash
pip install -r requirements.txt
```

**requirements.txt:**
```txt
pandas>=1.5.0
requests>=2.28.0
beautifulsoup4>=4.11.0
openpyxl>=3.1.0
numpy>=1.23.0
lxml>=4.9.0
```

### 🔧 Configuração Personalizada

```python
# FII Configuration
from fii_analyzer import FIIApplication, ScraperConfig, FilterCriteria

config = ScraperConfig(
    timeout=30,
    max_workers=5,
    output_filename="meus_fiis.xlsx"
)

filters = FilterCriteria(
    min_dividend_yield=0.08,  # 8%
    max_pvp=1.0
)

app = FIIApplication(config=config, filter_criteria=filters)
app.run()
```

```python
# Stock Configuration  
from stock_analyzer import StockApplication, ScraperConfig

config = ScraperConfig(
    max_workers=10,           # Mais threads
    rate_limit_delay=0.3,     # Mais rápido
    top_stocks_limit=50,      # Top 50
    cache_filename="meu_cache.json"
)

app = StockApplication(config=config)
app.run()
```

```python
# Dividend Prediction Configuration
from dividend_predictor import DividendPredictionSystem, ScraperConfig

config = ScraperConfig(
    years_to_analyze=5,        # 5 anos de histórico
    cache_ttl_hours=48,        # Cache de 2 dias
    min_confidence_threshold=0.7,  # 70% confiança mínima
    default_tickers=["VALE3", "PETR4", "BBDC4"]
)

system = DividendPredictionSystem(config)
system.run()
```

---

## 🚀 Execução

### Modo Básico
```bash
# Análise de FIIs
python fii_analyzer.py

# Análise de Ações
python stock_analyzer.py

# Previsão de Dividendos
python dividend_predictor.py
```

### Modo Avançado
```python
# Script customizado
from fii_analyzer import FIIApplication
from stock_analyzer import StockApplication
from dividend_predictor import DividendPredictionSystem

# Executar todas as análises
fii_app = FIIApplication()
fii_app.run()

stock_app = StockApplication()
stock_app.run()

dividend_system = DividendPredictionSystem()
tickers = ["BBSE3", "TAEE11", "VIVT3"]
dividend_system.run(tickers)
```

---

## 📂 Estrutura de Saída

```
📂 resultados/
├── 📊 Excel/
│   ├── fundos_imobiliarios_filtrados.xlsx
│   ├── acoes_filtradas_fundamentus.xlsx
│   └── dividendos_analise.xlsx
├── 📝 Relatórios/
│   └── PREVISAO_DIVIDENDOS.md
├── 💾 Cache/
│   ├── setor_cache.json
│   └── .dividend_cache/
└── 📜 Logs/
    └── dividendos.log
```

---

## 🎨 Recursos Visuais

### Formatação Excel
- 🟢 **Verde**: Nota ≥ 8 (Excelente)
- 🟡 **Amarelo**: Nota 5-7 (Bom)
- 🔴 **Vermelho**: Nota < 5 (Atenção)

### Indicadores de Confiança
- ⭐⭐⭐ Alta confiança (>80%)
- ⭐⭐ Média confiança (60-80%)
- ⭐ Baixa confiança (<60%)

---

## 🔒 Recursos de Segurança

- ✅ **Type hints** completos
- ✅ **Docstrings** detalhadas
- ✅ **Error handling** robusto
- ✅ **Logging** estruturado
- ✅ **Thread-safety** garantido
- ✅ **Rate limiting** automático
- ✅ **Retry com backoff**
- ✅ **Validação de dados**

---

## 📊 Métricas de Performance

| Operação | Tempo Original | Tempo Otimizado | Melhoria |
|----------|---------------|-----------------|----------|
| Coleta FIIs | ~30s | ~5s | 6x |
| Análise Ações + Setores | ~180s | ~20s | 9x |
| Previsão Dividendos (10 ativos) | ~60s | ~8s | 7.5x |
| Cache Hit Rate | 0% | 90%+ | ∞ |

---

## 🛠️ Troubleshooting

### Problemas Comuns

**1. Timeout em requisições**
```python
config = ScraperConfig(timeout=60)  # Aumentar timeout
```

**2. Rate limiting**
```python
config = ScraperConfig(rate_limit_delay=2.0)  # Mais delay
```

**3. Cache corrompido**
```python
system.clear_cache()  # Limpar cache
```

---

## 📈 Roadmap Futuro

- [ ] API REST para integração
- [ ] Dashboard web interativo
- [ ] Alertas automáticos
- [ ] Backtesting de estratégias
- [ ] Machine Learning avançado
- [ ] Integração com corretoras

---

## 📚 Documentação Técnica

Cada módulo possui:
- **Dataclasses** para configuração
- **Custom Exceptions** para erros
- **Type Hints** completos
- **Docstrings** no formato Google
- **Logging** configurável
- **Tests** unitários (em desenvolvimento)

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---

## 📧 Contato

**Suporte**: analucatti23@gmail.com  
**GitHub**: [github.com/seu-usuario/investment-analyzer](https://github.com)

---

## ⚠️ Disclaimer

Este software é fornecido apenas para fins educacionais e informativos. Não constitui recomendação de investimento. Sempre consulte um profissional qualificado antes de tomar decisões de investimento.

---

*Última atualização: 2024 | Versão 2.0.0*