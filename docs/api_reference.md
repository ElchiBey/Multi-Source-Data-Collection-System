# API Reference - Multi-Source Data Collection System

## Table of Contents
1. [Core Modules](#core-modules)
2. [Scrapers](#scrapers)
3. [Data Management](#data-management)
4. [Analysis](#analysis)
5. [Utilities](#utilities)
6. [CLI Interface](#cli-interface)
7. [Configuration](#configuration)

## Core Modules

### src.scrapers.base_scraper

#### `BaseScraper`
Abstract base class for all scrapers implementing the Template Method pattern.

```python
class BaseScraper(ABC):
    def __init__(self, config: Dict[str, Any])
    def scrape_products(self, source: str, keywords: List[str], max_pages: int = 5) -> List[Dict]
    def add_observer(self, observer: ScrapingObserver) -> None
    def remove_observer(self, observer: ScrapingObserver) -> None
```

**Methods:**
- `scrape_products()`: Main scraping method using template pattern
- `add_observer()`: Register progress observers
- `remove_observer()`: Unregister observers
- `_get_page()`: Abstract method for page fetching (implemented by subclasses)
- `_extract_products()`: Abstract method for product extraction
- `_process_products()`: Template method for product processing

**Usage Example:**
```python
from src.scrapers.static_scraper import StaticScraper
from src.utils.config import load_config

config = load_config('config/settings.yaml')
scraper = StaticScraper(config)
products = scraper.scrape_products('amazon', ['laptop'], max_pages=3)
```

#### `ScrapingObserver`
Observer interface for monitoring scraping progress.

```python
class ScrapingObserver(ABC):
    def update(self, event: str, data: Dict[str, Any]) -> None
```

**Events:**
- `page_start`: Page scraping started
- `page_complete`: Page scraping completed
- `product_found`: Product extracted
- `error_occurred`: Error during scraping
- `scraping_complete`: All scraping finished

### src.scrapers.static_scraper

#### `StaticScraper`
BeautifulSoup4-based scraper for static HTML content.

```python
class StaticScraper(BaseScraper):
    def __init__(self, config: Dict[str, Any])
    def _get_page(self, url: str) -> requests.Response
    def _extract_products(self, soup: BeautifulSoup, source: str) -> List[Dict]
```

**Features:**
- Anti-bot protection with user agent rotation
- Configurable retry logic
- CSS selector-based extraction
- Support for Amazon, eBay, Walmart

**Usage Example:**
```python
scraper = StaticScraper(config)
products = scraper.scrape_products('ebay', ['smartphone'], max_pages=2)
print(f"Found {len(products)} products")
```

### src.scrapers.selenium_scraper

#### `SeleniumScraper`
Selenium-based scraper for dynamic JavaScript content.

```python
class SeleniumScraper(BaseScraper):
    def __init__(self, config: Dict[str, Any])
    def _setup_driver(self) -> webdriver.Chrome
    def _get_page(self, url: str) -> str
    def cleanup(self) -> None
```

**Features:**
- Headless Chrome browser
- JavaScript execution
- Stealth mode configuration
- Anti-detection measures

**Usage Example:**
```python
scraper = SeleniumScraper(config)
try:
    products = scraper.scrape_products('amazon', ['gaming laptop'])
finally:
    scraper.cleanup()  # Important: Clean up browser resources
```

### src.scrapers.manager

#### `ScrapingManager`
Orchestrates all scraping operations using Factory pattern.

```python
class ScrapingManager:
    def __init__(self, config: Dict[str, Any])
    def scrape_all(self, sources: List[str], keywords: List[str], 
                   max_pages: int = 5, output_dir: str = None) -> List[Dict]
    def scrape_single(self, source: str, keyword: str, 
                     page: int, scraper_type: str) -> List[Dict]
    def get_scraper(self, scraper_type: str) -> BaseScraper
```

**Methods:**
- `scrape_all()`: Scrape from multiple sources with multiple keywords
- `scrape_single()`: Single page scraping for concurrent processing
- `get_scraper()`: Factory method for scraper creation

**Usage Example:**
```python
manager = ScrapingManager(config)
results = manager.scrape_all(
    sources=['amazon', 'ebay'],
    keywords=['laptop', 'tablet'],
    max_pages=3
)
```

## Data Management

### src.data.models

#### `Product`
SQLAlchemy model for product data.

```python
class Product(Base):
    __tablename__ = 'products'
    
    id: int
    title: str
    price: float
    url: str
    source: str
    rating: float
    review_count: int
    image_url: str
    description: str
    category: str
    brand: str
    availability: bool
    product_id: str
    scraped_at: datetime
    session_id: int
```

**Relationships:**
- `session`: Many-to-one with ScrapingSession
- `price_history`: One-to-many with PriceHistory

#### `ScrapingSession`
Tracks scraping operations and metadata.

```python
class ScrapingSession(Base):
    __tablename__ = 'scraping_sessions'
    
    id: int
    start_time: datetime
    end_time: datetime
    source: str
    keywords: str
    total_products: int
    success_rate: float
    status: str
```

#### `PriceHistory`
Tracks price changes over time.

```python
class PriceHistory(Base):
    __tablename__ = 'price_history'
    
    id: int
    product_id: int
    price: float
    recorded_at: datetime
    source: str
```

### src.data.database

#### `DatabaseManager`
Singleton database manager with context management.

```python
class DatabaseManager:
    def __init__(self, config: Dict[str, Any])
    def get_session(self) -> Session
    def save_products(self, products: List[Dict], session_id: int) -> None
    def get_products(self, filters: Dict = None) -> List[Product]
    def get_statistics(self) -> Dict[str, Any]
    def cleanup_old_data(self, days: int = 30) -> int
```

**Context Manager Usage:**
```python
db_manager = DatabaseManager(config)
with db_manager.get_session() as session:
    products = session.query(Product).filter(Product.source == 'amazon').all()
```

**Bulk Operations:**
```python
# Save multiple products efficiently
session_id = db_manager.create_session('amazon', 'laptop')
db_manager.save_products(product_list, session_id)
```

### src.data.processors

#### `DataProcessor`
Data cleaning and transformation utilities.

```python
class DataProcessor:
    def __init__(self, config: Dict[str, Any])
    def clean_product_data(self, products: List[Dict]) -> List[Dict]
    def validate_data(self, products: List[Dict]) -> Tuple[List[Dict], List[str]]
    def aggregate_price_data(self, days: int = 30) -> pd.DataFrame
    def detect_duplicates(self, products: List[Dict]) -> List[int]
```

**Usage Example:**
```python
processor = DataProcessor(config)
cleaned_products = processor.clean_product_data(raw_products)
valid_products, errors = processor.validate_data(cleaned_products)
```

#### `DataExporter`
Export data in multiple formats.

```python
class DataExporter:
    def __init__(self, config: Dict[str, Any])
    def export_data(self, format: str, output_dir: str, 
                   filter_days: int = 7) -> str
    def export_to_csv(self, df: pd.DataFrame, output_path: str) -> str
    def export_to_json(self, df: pd.DataFrame, output_path: str) -> str
    def export_to_excel(self, df: pd.DataFrame, output_path: str) -> str
```

## Analysis

### src.analysis.statistics

#### `ProductStatistics`
Statistical analysis of product data.

```python
class ProductStatistics:
    def __init__(self, config: Dict[str, Any])
    def basic_statistics(self) -> Dict[str, Any]
    def price_analysis_by_source(self) -> Dict[str, Dict[str, float]]
    def rating_analysis(self) -> Dict[str, Any]
    def keyword_analysis(self, keywords: List[str]) -> Dict[str, Any]
    def data_quality_report(self) -> Dict[str, Any]
```

**Usage Example:**
```python
stats = ProductStatistics(config)
basic_stats = stats.basic_statistics()
price_stats = stats.price_analysis_by_source()
quality_report = stats.data_quality_report()
```

### src.analysis.visualization

#### `DataVisualizer`
Chart and graph generation.

```python
class DataVisualizer:
    def __init__(self, config: Dict[str, Any])
    def create_price_distribution_chart(self, output_path: str) -> str
    def create_source_comparison_chart(self, output_path: str) -> str
    def create_trend_chart(self, days: int, output_path: str) -> str
    def create_rating_analysis_chart(self, output_path: str) -> str
```

**Chart Types:**
- Price distribution histograms
- Source comparison box plots
- Time series trend charts
- Rating analysis scatter plots
- Interactive Plotly dashboards

### src.analysis.reports

#### `ReportGenerator`
Comprehensive report generation.

```python
class ReportGenerator:
    def __init__(self, config: Dict[str, Any])
    def generate_summary_report(self, period: int, output_dir: str) -> str
    def generate_trend_report(self, period: int, output_dir: str) -> str
    def generate_comparison_report(self, period: int, output_dir: str) -> str
```

**Report Features:**
- HTML output with embedded charts
- JSON data exports
- Statistical summaries
- Interactive visualizations

## Utilities

### src.utils.concurrent_manager

#### `ConcurrentScrapingManager`
Thread-based concurrent processing.

```python
class ConcurrentScrapingManager:
    def __init__(self, config: Dict[str, Any])
    def add_scraping_tasks(self, sources: List[str], keywords: List[str],
                          max_pages: int, scraper_type: str) -> None
    def execute_concurrent_scraping(self, worker_function: Callable) -> List[Any]
    def get_progress_stats(self) -> Dict[str, Any]
```

#### `ScrapingTask`
Task representation for concurrent processing.

```python
@dataclass
class ScrapingTask:
    task_id: str
    source: str
    keyword: str
    page: int
    scraper_type: str
    priority: int = 0
    retry_count: int = 0
```

### src.utils.helpers

#### Utility Functions
```python
def extract_price(text: str) -> Optional[float]
def extract_rating(text: str) -> Optional[float]
def clean_text(text: Optional[str]) -> str
def get_random_user_agent() -> str
def get_random_headers() -> Dict[str, str]
def random_delay(min_delay: float = 1.0, max_delay: float = 3.0) -> None
def normalize_url(url: str, base_url: str) -> str
def validate_product_data(product: Dict[str, Any]) -> Tuple[bool, List[str]]
```

### src.utils.config

#### `ConfigManager`
Configuration management and validation.

```python
class ConfigManager:
    def __init__(self, config_path: str = 'config/settings.yaml')
    def load_config(self) -> Dict[str, Any]
    def validate_config(self, config: Dict[str, Any]) -> bool
    def get_scraper_config(self, source: str) -> Dict[str, Any]
    def get_database_config(self) -> Dict[str, Any]
```

### src.utils.logger

#### Logging Setup
```python
def setup_logger(name: str, level: str = 'INFO') -> logging.Logger
def get_logger(name: str) -> logging.Logger
```

## CLI Interface

### Main Commands

#### `main.py scrape`
```bash
python main.py scrape [OPTIONS]

Options:
  --sources TEXT          Comma-separated list of sources
  --keywords TEXT         Comma-separated search keywords [required]
  --max-pages INTEGER     Maximum pages per source
  --scraper-type CHOICE   Type of scraper (static|selenium|scrapy|concurrent)
  --concurrent           Use concurrent processing
  --output TEXT          Output directory
```

#### `main.py report`
```bash
python main.py report [OPTIONS]

Options:
  --type CHOICE          Report type (trend|comparison|summary)
  --period INTEGER       Analysis period in days
  --output TEXT          Output directory
```

#### `main.py export`
```bash
python main.py export [OPTIONS]

Options:
  --format CHOICE        Export format (csv|json|excel)
  --output TEXT          Output directory
  --filter-days INTEGER  Filter data from last N days
```

## Configuration

### Settings Schema (`config/settings.yaml`)
```yaml
database:
  url: str                    # Database connection URL
  echo: bool                  # Enable SQL logging

scraping:
  delay:
    min: float               # Minimum delay between requests
    max: float               # Maximum delay between requests
  retries: int               # Number of retry attempts
  timeout: int               # Request timeout in seconds
  max_workers: int           # Maximum concurrent workers
  use_multiprocessing: bool  # Use multiprocessing instead of threading

selenium:
  headless: bool             # Run browser in headless mode
  window_size: str           # Browser window size
  user_data_dir: str         # Chrome user data directory

sources:
  amazon:
    enabled: bool            # Enable Amazon scraping
    base_urls: List[str]     # List of base URLs
  ebay:
    enabled: bool            # Enable eBay scraping
    base_urls: List[str]     # List of base URLs

analysis:
  chart_style: str           # Matplotlib style
  export_formats: List[str]  # Supported export formats
```

### Scraper Configuration (`config/scrapers.yaml`)
```yaml
amazon:
  selectors:
    product_container: str   # CSS selector for product containers
    title: str              # CSS selector for product titles
    price: str              # CSS selector for prices
    rating: str             # CSS selector for ratings
  patterns:
    price_regex: str        # Regex pattern for price extraction
    rating_regex: str       # Regex pattern for rating extraction
```

## Error Handling

### Exception Classes
```python
class ScrapingError(Exception):
    """Base exception for scraping errors"""

class RateLimitError(ScrapingError):
    """Raised when rate limiting is detected"""

class AntiBot Detection(ScrapingError):
    """Raised when anti-bot measures are detected"""

class DataValidationError(Exception):
    """Raised when data validation fails"""
```

### Error Handling Patterns
```python
try:
    products = scraper.scrape_products('amazon', ['laptop'])
except RateLimitError:
    logger.warning("Rate limit detected, increasing delays")
    time.sleep(30)
except AntiBotDetection:
    logger.error("Anti-bot protection detected")
    # Switch to different scraper or proxy
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## Performance Considerations

### Optimization Tips
1. **Use appropriate scraper types**: Static for simple sites, Selenium for complex ones
2. **Configure delays properly**: Balance speed and respectfulness
3. **Monitor resource usage**: CPU and memory consumption
4. **Use concurrent processing**: For large-scale operations
5. **Database optimization**: Use proper indexes and batch operations

### Memory Management
```python
# Proper resource cleanup
scraper = SeleniumScraper(config)
try:
    results = scraper.scrape_products(source, keywords)
finally:
    scraper.cleanup()  # Always cleanup browser resources

# Database session management
with db_manager.get_session() as session:
    # Database operations here
    pass  # Session automatically closed
```

---

This API reference covers all major components of the Multi-Source Data Collection System. For practical examples and tutorials, see the [User Guide](user_guide.md). 