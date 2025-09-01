# 📊 Advanced Investment Analysis System

## 🚀 Overview
Complete fundamental analysis suite for the Brazilian market, with three specialized modules for data-driven decision making.

---

## 📌 Available Modules

### 1️⃣ **Real Estate Investment Funds (REITs/FIIs) Analysis**

#### 🏗️ Modular Architecture
- **`FundamentusScraper`**: Data collection with automatic retry
- **`DataProcessor`**: Data cleaning and validation
- **`FIIAnalyzer`**: Analysis and scoring engine
- **`ExcelExporter`**: Formatted report generation

#### 🔍 Main Features

**📥 Data Collection**
- Web scraping from [Fundamentus](https://www.fundamentus.com.br/fii_resultado.php)
- Session pooling for better performance
- Automatic retry with exponential backoff
- Robust error handling

**🎯 Configurable Filter System**
```python
FilterCriteria:
  - Dividend Yield: 7% - 25%
  - P/VP: 0.5 - 1.1
  - Liquidity: > R$ 1,000,000
  - Market Value: > R$ 1,000,000,000
```

**⭐ Advanced Scoring (0-10 points)**

| Metric | Excellent (+2) | Good (+1) | Weight |
|---------|---------------|----------|------|
| DY | ≥14% | ≥12% | High |
| P/VP | ≤0.80 | ≤0.85 | High |
| Liquidity | ≥R$5M | ≥R$2M | Medium |
| Market Value | ≥R$2B | ≥R$1.5B | Medium |
| Vacancy | ≤5% | ≤10% | High |

**📤 Outputs**
- Multi-tab Excel with professional formatting
- Top 5 funds by segment
- Complete statistical analysis
- Detailed logs for auditing

---

### 2️⃣ **Stock Analysis**

#### 🏗️ Optimized Architecture
- **`StatusInvestScraper`**: Parallel collection with ThreadPool
- **`SectorEnricher`**: Sector enrichment (multi-thread)
- **`StockAnalyzer`**: Fundamental analysis
- **`SectorCache`**: Thread-safe intelligent cache

#### 🔍 Advanced Features

**🚄 Performance**
- **Parallel collection**: 5-10x faster
- **Persistent cache**: Reduces requests by 90%
- **Rate limiting**: Prevents blocking
- **Session reuse**: Optimized connections

**🎯 Fundamentalist Filters**
```python
FilterCriteria:
  - P/E: 3.0 - 12.0
  - P/BV: 0.5 - 1.1  
  - ROE: 14% - 50%
  - DY: 7% - 25%
  - 5-year Growth: > 10%
  - Debt/Equity: < 2.0
  - 2-month Liquidity: > R$ 1,000,000
```

**⭐ Scoring System (0-14 points)**

| Indicator | Excellent (+2) | Good (+1) | Importance |
|-----------|---------------|----------|-------------|
| P/E | ≤5 | ≤7 | Critical |
| P/BV | ≤0.7 | ≤0.9 | Critical |
| DY | ≥12% | ≥9% | High |
| ROE | ≥20% | ≥17% | High |
| Growth | ≥20% | ≥15% | Medium |
| Debt/Equity | ≤0.5 | ≤1.0 | High |
| Liquidity | ≥R$50M | ≥R$10M | Medium |

**📊 Extra Features**
- Automatic sector identification
- JSON cache for optimization
- Top 30 ranked stocks
- Top 5 by sector
- Portfolio statistical analysis

---

### 3️⃣ **Dividend Prediction System** 🆕

#### 🏗️ Predictive Architecture
- **`StatusInvestScraper`**: Historical dividend collection
- **`DividendAnalyzer`**: Machine Learning-like predictions
- **`DividendCache`**: Cache with configurable TTL
- **`ReportGenerator`**: Multi-format reports

#### 🔮 AI Features

**📈 Predictive Analysis**
- Automatic payment pattern detection
- Monthly probability calculation
- Next payment predictions
- Confidence score for each prediction

**🎯 Statistical Metrics**
```python
MonthlyStatistics:
  - Payment probability
  - Historical average value
  - Standard deviation
  - Median values
  - Years of occurrence
  - Confidence score
```

**🔍 Detected Patterns**
- **Monthly**: Regular monthly payments
- **Quarterly**: Every 3 months
- **Semi-annual**: 2x per year
- **Annual**: 1x per year
- **Irregular**: No defined pattern

**📊 Generated Reports**

1. **Markdown** (`DIVIDEND_PREDICTION.md`)
   - Probability table
   - Predictions with confidence
   - Detailed analysis by asset

2. **Excel** (`dividend_analysis.xlsx`)
   - Probabilities tab
   - Predictions tab
   - Statistics tab

3. **JSON** (`dividend_data.json`)
   - Structured data for APIs
   - Complete metadata
   - Object serialization

---

## ⚙️ Installation and Configuration

### 📋 Requirements
```bash
Python 3.8+
```

### 📦 Dependencies
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

### 🔧 Custom Configuration

```python
# FII Configuration
from fii_analyzer import FIIApplication, ScraperConfig, FilterCriteria

config = ScraperConfig(
    timeout=30,
    max_workers=5,
    output_filename="my_reits.xlsx"
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
    max_workers=10,           # More threads
    rate_limit_delay=0.3,     # Faster
    top_stocks_limit=50,      # Top 50
    cache_filename="my_cache.json"
)

app = StockApplication(config=config)
app.run()
```

```python
# Dividend Prediction Configuration
from dividend_predictor import DividendPredictionSystem, ScraperConfig

config = ScraperConfig(
    years_to_analyze=5,        # 5 years of history
    cache_ttl_hours=48,        # 2-day cache
    min_confidence_threshold=0.7,  # 70% minimum confidence
    default_tickers=["VALE3", "PETR4", "BBDC4"]
)

system = DividendPredictionSystem(config)
system.run()
```

---

## 🚀 Execution

### Basic Mode
```bash
# REIT Analysis
python fii_analyzer.py

# Stock Analysis
python stock_analyzer.py

# Dividend Prediction
python dividend_predictor.py
```

### Advanced Mode
```python
# Custom script
from fii_analyzer import FIIApplication
from stock_analyzer import StockApplication
from dividend_predictor import DividendPredictionSystem

# Run all analyses
fii_app = FIIApplication()
fii_app.run()

stock_app = StockApplication()
stock_app.run()

dividend_system = DividendPredictionSystem()
tickers = ["BBSE3", "TAEE11", "VIVT3"]
dividend_system.run(tickers)
```

---

## 📂 Output Structure

```
📂 results/
├── 📊 Excel/
│   ├── filtered_real_estate_funds.xlsx
│   ├── filtered_stocks_fundamentus.xlsx
│   └── dividend_analysis.xlsx
├── 📝 Reports/
│   └── DIVIDEND_PREDICTION.md
├── 💾 Cache/
│   ├── sector_cache.json
│   └── .dividend_cache/
└── 📜 Logs/
    └── dividends.log
```

---

## 🎨 Visual Features

### Excel Formatting
- 🟢 **Green**: Score ≥ 8 (Excellent)
- 🟡 **Yellow**: Score 5-7 (Good)
- 🔴 **Red**: Score < 5 (Attention)

### Confidence Indicators
- ⭐⭐⭐ High confidence (>80%)
- ⭐⭐ Medium confidence (60-80%)
- ⭐ Low confidence (<60%)

---

## 🔒 Security Features

- ✅ Complete **type hints**
- ✅ Detailed **docstrings**
- ✅ Robust **error handling**
- ✅ Structured **logging**
- ✅ Guaranteed **thread-safety**
- ✅ Automatic **rate limiting**
- ✅ **Retry with backoff**
- ✅ **Data validation**

---

## 📊 Performance Metrics

| Operation | Original Time | Optimized Time | Improvement |
|----------|---------------|-----------------|----------|
| REIT Collection | ~30s | ~5s | 6x |
| Stock Analysis + Sectors | ~180s | ~20s | 9x |
| Dividend Prediction (10 assets) | ~60s | ~8s | 7.5x |
| Cache Hit Rate | 0% | 90%+ | ∞ |

---

## 🛠️ Troubleshooting

### Common Issues

**1. Request timeout**
```python
config = ScraperConfig(timeout=60)  # Increase timeout
```

**2. Rate limiting**
```python
config = ScraperConfig(rate_limit_delay=2.0)  # More delay
```

**3. Corrupted cache**
```python
system.clear_cache()  # Clear cache
```

---

## 📈 Future Roadmap

- [ ] REST API for integration
- [ ] Interactive web dashboard
- [ ] Automatic alerts
- [ ] Strategy backtesting
- [ ] Advanced Machine Learning
- [ ] Broker integration

---

## 📚 Technical Documentation

Each module includes:
- **Dataclasses** for configuration
- **Custom Exceptions** for errors
- Complete **Type Hints**
- **Docstrings** in Google format
- Configurable **Logging**
- Unit **Tests** (in development)

---

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 📧 Contact

**Support**: analucatti23@gmail.com  
**GitHub**: [github.com/your-username/investment-analyzer](https://github.com)

---

## ⚠️ Disclaimer

This software is provided for educational and informational purposes only. It does not constitute investment advice. Always consult a qualified professional before making investment decisions.

---

*Last updated: 2025 | Version 2.0.0*
