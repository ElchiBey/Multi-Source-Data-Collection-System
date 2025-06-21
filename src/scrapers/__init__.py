"""
Web scraping modules for the Multi-Source Data Collection System.

This package implements multiple scraping approaches:
- Static scraping with BeautifulSoup4
- Dynamic scraping with Selenium  
- Framework-based scraping with Scrapy
- Concurrent and scalable scraping architecture

Design Patterns Implemented:
- Factory Pattern: For creating different scrapers
- Strategy Pattern: For different scraping approaches  
- Observer Pattern: For progress monitoring
"""

from .base_scraper import BaseScraper, ScrapingResult
from .static_scraper import StaticScraper
from .selenium_scraper import SeleniumScraper
from .manager import ScrapingManager
from .factory import ScraperFactory

# Import Scrapy components (optional, in case Scrapy isn't installed)
try:
    from .scrapy_crawler.spider import ProductSpider
    from .scrapy_crawler.runner import ScrapyRunner
    SCRAPY_AVAILABLE = True
except ImportError:
    ProductSpider = None
    ScrapyRunner = None
    SCRAPY_AVAILABLE = False

__all__ = [
    'BaseScraper',
    'ScrapingResult',
    'StaticScraper',
    'SeleniumScraper', 
    'ScrapingManager',
    'ScraperFactory',
    'ProductSpider',
    'ScrapyRunner',
    'SCRAPY_AVAILABLE'
] 