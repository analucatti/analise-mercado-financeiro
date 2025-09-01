"""
Dividend Prediction System for Brazilian Stocks
Analyzes historical dividend patterns from StatusInvest to predict future payments.
"""

import json
import logging
import pickle
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
def setup_logging(log_file: str = "dividendos.log", level: int = logging.INFO) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


# ============= Configuration =============
@dataclass
class ScraperConfig:
    """Configuration for the dividend scraper."""
    base_url: str = "https://statusinvest.com.br/acao/companytickerprovents"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    max_workers: int = 5
    rate_limit_delay: float = 0.5
    cache_dir: str = ".dividend_cache"
    cache_ttl_hours: int = 24

    # Default tickers
    default_tickers: List[str] = field(default_factory=lambda: [
        "BBSE3", "BBDC3", "BBAS3", "VIVT3", "SAPR11",
        "CMIG3", "ISAE3", "VALE3", "PETR4", "CMIN3"
    ])

    # Analysis parameters
    years_to_analyze: int = 3
    min_confidence_threshold: float = 0.6  # 60% confidence minimum

    # Output files
    markdown_output: str = "PREVISAO_DIVIDENDOS.md"
    excel_output: str = "dividendos_analise.xlsx"
    json_output: str = "dividendos_data.json"


@dataclass
class DividendEvent:
    """Represents a single dividend event."""
    ticker: str
    type: str  # Dividendo, JCP, etc.
    value: float
    payment_date: datetime
    ex_date: Optional[datetime] = None
    record_date: Optional[datetime] = None
    yield_percent: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'ticker': self.ticker,
            'type': self.type,
            'value': self.value,
            'payment_date': self.payment_date.strftime('%Y-%m-%d'),
            'ex_date': self.ex_date.strftime('%Y-%m-%d') if self.ex_date else None,
            'record_date': self.record_date.strftime('%Y-%m-%d') if self.record_date else None,
            'yield_percent': self.yield_percent
        }


@dataclass
class MonthlyStatistics:
    """Statistics for dividends in a specific month."""
    month: str
    probability: float
    average_value: float
    median_value: float
    std_deviation: float
    occurrences: int
    years_occurred: List[int]
    confidence_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class StockDividendAnalysis:
    """Complete dividend analysis for a stock."""
    ticker: str
    total_years_analyzed: int
    total_dividends_paid: int
    average_annual_dividends: float
    monthly_statistics: Dict[str, MonthlyStatistics]
    payment_pattern: str  # "quarterly", "monthly", "irregular", etc.
    next_payment_prediction: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'ticker': self.ticker,
            'total_years_analyzed': self.total_years_analyzed,
            'total_dividends_paid': self.total_dividends_paid,
            'average_annual_dividends': self.average_annual_dividends,
            'monthly_statistics': {
                month: stats.to_dict()
                for month, stats in self.monthly_statistics.items()
            },
            'payment_pattern': self.payment_pattern,
            'next_payment_prediction': self.next_payment_prediction,
            'confidence_score': self.confidence_score,
            'last_update': self.last_update.isoformat()
        }


# ============= Exceptions =============
class DividendScraperError(Exception):
    """Base exception for dividend scraper."""
    pass


class DataFetchError(DividendScraperError):
    """Exception raised when data fetching fails."""
    pass


class DataProcessingError(DividendScraperError):
    """Exception raised when data processing fails."""
    pass


# ============= Month Translations =============
MONTH_TRANSLATIONS = {
    'JAN': 'JAN', 'FEB': 'FEV', 'MAR': 'MAR', 'APR': 'ABR',
    'MAY': 'MAI', 'JUN': 'JUN', 'JUL': 'JUL', 'AUG': 'AGO',
    'SEP': 'SET', 'OCT': 'OUT', 'NOV': 'NOV', 'DEC': 'DEZ'
}

MONTHS_PT = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
             "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]


# ============= Cache Management =============
class DividendCache:
    """Manages caching of dividend data."""

    def __init__(self, cache_dir: str, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _get_cache_path(self, ticker: str) -> Path:
        """Get cache file path for a ticker."""
        return self.cache_dir / f"{ticker.lower()}_dividends.pkl"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is still valid."""
        if not cache_path.exists():
            return False

        modified_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - modified_time < self.ttl

    def get(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached data for a ticker."""
        cache_path = self._get_cache_path(ticker)

        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                logger.debug(f"Cache hit for {ticker}")
                return data
            except Exception as e:
                logger.warning(f"Failed to load cache for {ticker}: {e}")

        return None

    def set(self, ticker: str, data: Dict[str, Any]) -> None:
        """Cache data for a ticker."""
        cache_path = self._get_cache_path(ticker)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            logger.debug(f"Cached data for {ticker}")
        except Exception as e:
            logger.warning(f"Failed to cache data for {ticker}: {e}")

    def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")
        logger.info("Cache cleared")


# ============= Data Fetching =============
class StatusInvestScraper:
    """Scraper for StatusInvest dividend data."""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.cache = DividendCache(config.cache_dir, config.cache_ttl_hours)
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set headers
        session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://statusinvest.com.br/',
        })

        return session

    def fetch_dividend_data(self, ticker: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch dividend data for a ticker.

        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use cached data if available

        Returns:
            Dictionary with dividend data or None if failed
        """
        # Check cache first
        if use_cache:
            cached_data = self.cache.get(ticker)
            if cached_data:
                return cached_data

        # Fetch from API
        url = f"{self.config.base_url}?ticker={ticker}&chartProventsType=2"

        try:
            logger.info(f"Fetching dividend data for {ticker}")
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()

            data = response.json()

            # Cache the data
            if data:
                self.cache.set(ticker, data)

            return data

        except requests.RequestException as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            raise DataFetchError(f"Failed to fetch data for {ticker}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response for {ticker}: {e}")
            raise DataFetchError(f"Invalid response format for {ticker}") from e

    def fetch_multiple_tickers(
            self,
            tickers: List[str],
            use_cache: bool = True
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch dividend data for multiple tickers in parallel.

        Args:
            tickers: List of ticker symbols
            use_cache: Whether to use cached data

        Returns:
            Dictionary mapping tickers to their data
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_ticker = {
                executor.submit(self.fetch_dividend_data, ticker, use_cache): ticker
                for ticker in tickers
            }

            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    results[ticker] = data
                    time.sleep(self.config.rate_limit_delay)  # Rate limiting
                except Exception as e:
                    logger.error(f"Failed to fetch {ticker}: {e}")
                    results[ticker] = None

        return results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


# ============= Data Processing =============
class DividendAnalyzer:
    """Analyzes dividend data and generates predictions."""

    def __init__(self, config: ScraperConfig):
        self.config = config

    def parse_dividend_events(
            self,
            ticker: str,
            raw_data: Dict[str, Any]
    ) -> List[DividendEvent]:
        """
        Parse raw dividend data into DividendEvent objects.

        Args:
            ticker: Stock ticker
            raw_data: Raw data from API

        Returns:
            List of DividendEvent objects
        """
        events = []

        if not raw_data or "assetEarningsModels" not in raw_data:
            logger.warning(f"No dividend data found for {ticker}")
            return events

        for item in raw_data["assetEarningsModels"]:
            try:
                # Parse event type
                event_type = item.get("et", "Unknown")

                # Only process dividends and JCP
                if event_type not in ["Dividendo", "JCP"]:
                    continue

                # Parse dates
                payment_date_str = item.get("pd")
                if not payment_date_str:
                    continue

                payment_date = datetime.strptime(payment_date_str, "%d/%m/%Y")

                # Parse other dates if available
                ex_date = None
                if item.get("ed"):
                    try:
                        ex_date = datetime.strptime(item["ed"], "%d/%m/%Y")
                    except:
                        pass

                # Parse value
                value = float(item.get("v", 0))
                if value <= 0:
                    continue

                # Create event
                event = DividendEvent(
                    ticker=ticker,
                    type=event_type,
                    value=value,
                    payment_date=payment_date,
                    ex_date=ex_date,
                    yield_percent=item.get("y")
                )

                events.append(event)

            except Exception as e:
                logger.debug(f"Failed to parse dividend event for {ticker}: {e}")
                continue

        # Sort by payment date
        events.sort(key=lambda x: x.payment_date)

        logger.info(f"Parsed {len(events)} dividend events for {ticker}")
        return events

    def analyze_payment_pattern(self, events: List[DividendEvent]) -> str:
        """
        Determine the payment pattern of dividends.

        Args:
            events: List of dividend events

        Returns:
            Pattern string: "monthly", "quarterly", "semi-annual", "annual", "irregular"
        """
        if len(events) < 3:
            return "insufficient_data"

        # Calculate intervals between payments
        intervals = []
        for i in range(1, len(events)):
            days_diff = (events[i].payment_date - events[i - 1].payment_date).days
            intervals.append(days_diff)

        if not intervals:
            return "irregular"

        avg_interval = np.mean(intervals)
        std_interval = np.std(intervals)

        # Determine pattern based on average interval
        if 25 <= avg_interval <= 35 and std_interval < 10:
            return "monthly"
        elif 80 <= avg_interval <= 100 and std_interval < 20:
            return "quarterly"
        elif 170 <= avg_interval <= 190 and std_interval < 30:
            return "semi-annual"
        elif 350 <= avg_interval <= 380 and std_interval < 40:
            return "annual"
        else:
            return "irregular"

    def calculate_monthly_statistics(
            self,
            events: List[DividendEvent],
            years_to_analyze: Optional[int] = None
    ) -> Dict[str, MonthlyStatistics]:
        """
        Calculate statistics for each month.

        Args:
            events: List of dividend events
            years_to_analyze: Number of years to analyze (None for all)

        Returns:
            Dictionary mapping months to their statistics
        """
        if not events:
            return {}

        # Filter events by years if specified
        if years_to_analyze:
            cutoff_date = datetime.now() - timedelta(days=365 * years_to_analyze)
            events = [e for e in events if e.payment_date >= cutoff_date]

        # Group events by month
        monthly_data = defaultdict(list)
        years_with_data = set()

        for event in events:
            month_str = event.payment_date.strftime("%b").upper()
            month_pt = MONTH_TRANSLATIONS.get(month_str, month_str)
            monthly_data[month_pt].append(event)
            years_with_data.add(event.payment_date.year)

        total_years = len(years_with_data)
        if total_years == 0:
            return {}

        # Calculate statistics for each month
        statistics = {}

        for month in MONTHS_PT:
            month_events = monthly_data.get(month, [])

            if not month_events:
                continue

            values = [e.value for e in month_events]
            years_occurred = list(set(e.payment_date.year for e in month_events))

            # Calculate probability
            probability = len(years_occurred) / total_years

            # Calculate confidence score
            confidence = min(1.0, len(month_events) / 3)  # Higher confidence with more data

            statistics[month] = MonthlyStatistics(
                month=month,
                probability=probability,
                average_value=np.mean(values),
                median_value=np.median(values),
                std_deviation=np.std(values) if len(values) > 1 else 0,
                occurrences=len(month_events),
                years_occurred=sorted(years_occurred),
                confidence_score=confidence
            )

        return statistics

    def predict_next_payment(
            self,
            events: List[DividendEvent],
            monthly_stats: Dict[str, MonthlyStatistics],
            pattern: str
    ) -> Optional[Dict[str, Any]]:
        """
        Predict the next dividend payment.

        Args:
            events: List of historical events
            monthly_stats: Monthly statistics
            pattern: Payment pattern

        Returns:
            Dictionary with prediction details
        """
        if not events or not monthly_stats:
            return None

        last_payment = events[-1]
        current_date = datetime.now()

        # Find months with high probability
        high_prob_months = [
            (month, stats) for month, stats in monthly_stats.items()
            if stats.probability >= 0.6
        ]

        if not high_prob_months:
            return None

        # Sort by probability
        high_prob_months.sort(key=lambda x: x[1].probability, reverse=True)

        # Get the next likely month
        current_month_idx = current_date.month - 1

        for month, stats in high_prob_months:
            month_idx = MONTHS_PT.index(month)

            # Check if this month is upcoming
            if month_idx > current_month_idx:
                predicted_date = datetime(current_date.year, month_idx + 1, 15)
            else:
                predicted_date = datetime(current_date.year + 1, month_idx + 1, 15)

            # Don't predict too far in the future
            if (predicted_date - current_date).days > 365:
                continue

            return {
                'predicted_month': month,
                'predicted_date': predicted_date.strftime('%Y-%m-%d'),
                'probability': stats.probability,
                'expected_value': stats.average_value,
                'confidence_score': stats.confidence_score,
                'based_on_pattern': pattern
            }

        return None

    def analyze_stock(
            self,
            ticker: str,
            raw_data: Dict[str, Any]
    ) -> Optional[StockDividendAnalysis]:
        """
        Perform complete analysis for a stock.

        Args:
            ticker: Stock ticker
            raw_data: Raw dividend data

        Returns:
            StockDividendAnalysis object or None if analysis failed
        """
        try:
            # Parse events
            events = self.parse_dividend_events(ticker, raw_data)

            if not events:
                logger.warning(f"No dividend events found for {ticker}")
                return None

            # Analyze payment pattern
            pattern = self.analyze_payment_pattern(events)

            # Calculate monthly statistics
            monthly_stats = self.calculate_monthly_statistics(
                events,
                self.config.years_to_analyze
            )

            # Calculate overall statistics
            years_with_data = set(e.payment_date.year for e in events)
            total_years = len(years_with_data)

            # Annual dividend calculation
            annual_dividends = defaultdict(float)
            for event in events:
                annual_dividends[event.payment_date.year] += event.value

            avg_annual = np.mean(list(annual_dividends.values())) if annual_dividends else 0

            # Predict next payment
            next_prediction = self.predict_next_payment(events, monthly_stats, pattern)

            # Calculate overall confidence
            confidence = np.mean([s.confidence_score for s in monthly_stats.values()]) if monthly_stats else 0

            return StockDividendAnalysis(
                ticker=ticker,
                total_years_analyzed=total_years,
                total_dividends_paid=len(events),
                average_annual_dividends=avg_annual,
                monthly_statistics=monthly_stats,
                payment_pattern=pattern,
                next_payment_prediction=next_prediction,
                confidence_score=confidence
            )

        except Exception as e:
            logger.error(f"Failed to analyze {ticker}: {e}")
            return None


# ============= Report Generation =============
class ReportGenerator:
    """Generates reports in various formats."""

    def __init__(self, config: ScraperConfig):
        self.config = config

    def generate_probability_table(
            self,
            analyses: Dict[str, StockDividendAnalysis]
    ) -> pd.DataFrame:
        """Generate probability table for all stocks."""
        data = {}

        for ticker, analysis in analyses.items():
            if not analysis:
                continue

            row_data = {}
            for month in MONTHS_PT:
                if month in analysis.monthly_statistics:
                    stats = analysis.monthly_statistics[month]
                    prob = stats.probability * 100
                    value = stats.average_value
                    row_data[month] = f"{prob:.0f}% (R${value:.2f})"
                else:
                    row_data[month] = "-"

            data[ticker] = row_data

        return pd.DataFrame(data).T

    def generate_markdown_report(
            self,
            analyses: Dict[str, StockDividendAnalysis]
    ) -> str:
        """Generate detailed Markdown report."""
        md = "# 📊 ANÁLISE DE DIVIDENDOS\n\n"
        md += f"**Data da Análise:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        md += f"**Período Analisado:** Últimos {self.config.years_to_analyze} anos\n\n"

        # Summary statistics
        md += "## 📈 Resumo Executivo\n\n"

        total_stocks = len(analyses)
        stocks_with_predictions = sum(
            1 for a in analyses.values()
            if a and a.next_payment_prediction
        )

        md += f"- **Total de Ativos Analisados:** {total_stocks}\n"
        md += f"- **Ativos com Previsões:** {stocks_with_predictions}\n\n"

        # Probability table
        md += "## 📅 Tabela de Probabilidades\n\n"
        prob_table = self.generate_probability_table(analyses)

        if not prob_table.empty:
            md += "| Ativo | " + " | ".join(MONTHS_PT) + " |\n"
            md += "|-------|" + "|".join(["-------"] * len(MONTHS_PT)) + "|\n"

            for ticker in prob_table.index:
                md += f"| **{ticker}** |"
                for month in MONTHS_PT:
                    value = prob_table.loc[ticker, month] if month in prob_table.columns else "-"
                    md += f" {value} |"
                md += "\n"

        # Predictions
        md += "\n## 🔮 Previsões de Próximos Pagamentos\n\n"

        predictions = []
        for ticker, analysis in analyses.items():
            if analysis and analysis.next_payment_prediction:
                pred = analysis.next_payment_prediction
                predictions.append({
                    'ticker': ticker,
                    'month': pred['predicted_month'],
                    'date': pred['predicted_date'],
                    'probability': pred['probability'],
                    'value': pred['expected_value'],
                    'confidence': pred['confidence_score']
                })

        if predictions:
            # Sort by date
            predictions.sort(key=lambda x: x['date'])

            for pred in predictions:
                md += f"### {pred['ticker']}\n"
                md += f"- **Mês Previsto:** {pred['month']}\n"
                md += f"- **Data Estimada:** {pred['date']}\n"
                md += f"- **Probabilidade:** {pred['probability']:.0%}\n"
                md += f"- **Valor Esperado:** R$ {pred['value']:.2f}\n"
                md += f"- **Confiança:** {pred['confidence']:.0%}\n\n"
        else:
            md += "*Nenhuma previsão disponível com confiança suficiente.*\n\n"

        # Detailed analysis per stock
        md += "## 📊 Análise Detalhada por Ativo\n\n"

        for ticker, analysis in sorted(analyses.items()):
            if not analysis:
                continue

            md += f"### {ticker}\n\n"
            md += f"**Padrão de Pagamento:** {analysis.payment_pattern}\n"
            md += f"**Anos Analisados:** {analysis.total_years_analyzed}\n"
            md += f"**Total de Pagamentos:** {analysis.total_dividends_paid}\n"
            md += f"**Média Anual:** R$ {analysis.average_annual_dividends:.2f}\n"
            md += f"**Confiança Geral:** {analysis.confidence_score:.0%}\n\n"

            if analysis.monthly_statistics:
                md += "**Estatísticas Mensais:**\n\n"

                # Sort by probability
                sorted_months = sorted(
                    analysis.monthly_statistics.items(),
                    key=lambda x: x[1].probability,
                    reverse=True
                )

                for month, stats in sorted_months[:6]:  # Top 6 months
                    md += f"- **{month}:** "
                    md += f"{stats.probability:.0%} probabilidade | "
                    md += f"R$ {stats.average_value:.2f} médio | "
                    md += f"{stats.occurrences} ocorrências\n"

                md += "\n"

        # Footer
        md += "---\n"
        md += f"*Relatório gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n"

        return md

    def generate_excel_report(
            self,
            analyses: Dict[str, StockDividendAnalysis],
            output_file: str
    ) -> None:
        """Generate Excel report with multiple sheets."""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Probability sheet
            prob_df = self.generate_probability_table(analyses)
            if not prob_df.empty:
                prob_df.to_excel(writer, sheet_name='Probabilidades')

            # Predictions sheet
            predictions_data = []
            for ticker, analysis in analyses.items():
                if analysis and analysis.next_payment_prediction:
                    pred = analysis.next_payment_prediction
                    predictions_data.append({
                        'Ativo': ticker,
                        'Mês': pred['predicted_month'],
                        'Data': pred['predicted_date'],
                        'Probabilidade': f"{pred['probability']:.0%}",
                        'Valor Esperado': f"R$ {pred['expected_value']:.2f}",
                        'Confiança': f"{pred['confidence_score']:.0%}"
                    })

            if predictions_data:
                pred_df = pd.DataFrame(predictions_data)
                pred_df.to_excel(writer, sheet_name='Previsões', index=False)

            # Statistics sheet
            stats_data = []
            for ticker, analysis in analyses.items():
                if analysis:
                    stats_data.append({
                        'Ativo': ticker,
                        'Padrão': analysis.payment_pattern,
                        'Anos Analisados': analysis.total_years_analyzed,
                        'Total Pagamentos': analysis.total_dividends_paid,
                        'Média Anual': f"R$ {analysis.average_annual_dividends:.2f}",
                        'Confiança': f"{analysis.confidence_score:.0%}"
                    })

            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='Estatísticas', index=False)

        logger.info(f"Excel report saved to {output_file}")

    def generate_json_report(
            self,
            analyses: Dict[str, StockDividendAnalysis],
            output_file: str
    ) -> None:
        """Generate JSON report for programmatic access."""
        data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'years_analyzed': self.config.years_to_analyze,
                'total_stocks': len(analyses)
            },
            'analyses': {
                ticker: analysis.to_dict() if analysis else None
                for ticker, analysis in analyses.items()
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON report saved to {output_file}")


# ============= Main Application =============
class DividendPredictionSystem:
    """Main application for dividend prediction."""

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.scraper = StatusInvestScraper(self.config)
        self.analyzer = DividendAnalyzer(self.config)
        self.reporter = ReportGenerator(self.config)

    def run(self, tickers: Optional[List[str]] = None) -> Dict[str, StockDividendAnalysis]:
        """
        Run the complete dividend analysis pipeline.

        Args:
            tickers: List of tickers to analyze (None for default)

        Returns:
            Dictionary of analyses
        """
        tickers = tickers or self.config.default_tickers

        print("\n" + "=" * 60)
        print("  💰 SISTEMA DE PREVISÃO DE DIVIDENDOS")
        print("=" * 60)
        print(f"📊 Analisando {len(tickers)} ativos")
        print(f"📅 Período: Últimos {self.config.years_to_analyze} anos")
        print("=" * 60)

        try:
            # Fetch data
            print("\n⏳ Coletando dados...")
            raw_data = self.scraper.fetch_multiple_tickers(tickers)

            # Analyze each stock
            print("🔍 Analisando padrões...")
            analyses = {}

            for ticker, data in raw_data.items():
                if data:
                    analysis = self.analyzer.analyze_stock(ticker, data)
                    analyses[ticker] = analysis

                    if analysis:
                        print(f"✅ {ticker}: {analysis.total_dividends_paid} dividendos encontrados")
                    else:
                        print(f"⚠️  {ticker}: Sem dados suficientes")
                else:
                    print(f"❌ {ticker}: Falha ao coletar dados")
                    analyses[ticker] = None

            # Generate reports
            print("\n📝 Gerando relatórios...")

            # Markdown report
            md_content = self.reporter.generate_markdown_report(analyses)
            with open(self.config.markdown_output, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"✅ Relatório Markdown: {self.config.markdown_output}")

            # Excel report
            self.reporter.generate_excel_report(analyses, self.config.excel_output)
            print(f"✅ Relatório Excel: {self.config.excel_output}")

            # JSON report
            self.reporter.generate_json_report(analyses, self.config.json_output)
            print(f"✅ Relatório JSON: {self.config.json_output}")

            # Summary
            print("\n" + "=" * 60)
            print("  📊 RESUMO DA ANÁLISE")
            print("=" * 60)

            successful = sum(1 for a in analyses.values() if a)
            with_predictions = sum(
                1 for a in analyses.values()
                if a and a.next_payment_prediction
            )

            print(f"✅ Análises bem-sucedidas: {successful}/{len(tickers)}")
            print(f"🔮 Previsões geradas: {with_predictions}")
            print("=" * 60)

            return analyses

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            print(f"\n❌ Erro na execução: {e}")
            return {}

    def clear_cache(self) -> None:
        """Clear the cache."""
        self.scraper.cache.clear()
        print("✅ Cache limpo")


def main():
    """Entry point for the application."""
    # You can customize the configuration here
    config = ScraperConfig(
        years_to_analyze=3,
        max_workers=5,
        cache_ttl_hours=24
    )

    # Initialize and run the system
    system = DividendPredictionSystem(config)

    # Optional: Clear cache if needed
    # system.clear_cache()

    # Run analysis
    analyses = system.run()

    # Print next payment predictions
    print("\n🔮 PRÓXIMOS PAGAMENTOS PREVISTOS:")
    print("-" * 40)

    for ticker, analysis in analyses.items():
        if analysis and analysis.next_payment_prediction:
            pred = analysis.next_payment_prediction
            print(f"{ticker}: {pred['predicted_month']} "
                  f"({pred['probability']:.0%} prob.) "
                  f"- R$ {pred['expected_value']:.2f}")


if __name__ == "__main__":
    main()