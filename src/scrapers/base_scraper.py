"""
Base scraper class implementing common scraping functionality and design patterns.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
import time
import random
import requests
from urllib.parse import urljoin, urlparse
import json

from src.utils.logger import LoggerMixin
from src.utils.helpers import clean_text, extract_price, extract_rating, normalize_url, retry_on_failure
from src.utils.config import get_source_config

@dataclass
class ScrapingResult:
    """
    Data class for scraping results.
    """
    success: bool = False
    data: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    pages_scraped: int = 0
    total_products: int = 0

class ScrapingObserver(ABC):
    """
    Observer interface for monitoring scraping progress.
    
    Implements Observer Pattern for progress tracking.
    """
    
    @abstractmethod
    def on_page_scraped(self, page: int, products_found: int, source: str) -> None:
        """Called when a page is successfully scraped."""
        pass
    
    @abstractmethod
    def on_error(self, error: str, source: str, page: Optional[int] = None) -> None:
        """Called when an error occurs."""
        pass
    
    @abstractmethod
    def on_scraping_completed(self, result: ScrapingResult) -> None:
        """Called when scraping is completed."""
        pass

class BaseScraper(ABC, LoggerMixin):
    """
    Abstract base scraper class implementing common functionality.
    
    Implements Template Method Pattern for scraping workflow.
    Provides Strategy Pattern interface for different scraping approaches.
    """
    
    def __init__(self, source: str, config: Dict[str, Any]):
        """
        Initialize base scraper.
        
        Args:
            source: Source name (amazon, ebay, walmart)
            config: Configuration dictionary
        """
        self.source = source
        self.config = config
        self.session = requests.Session()
        self.observers: List[ScrapingObserver] = []
        
        # Load source-specific configuration
        try:
            self.source_config = get_source_config(source)
        except KeyError:
            self.source_config = {}
            self.logger.warning(f"No configuration found for source: {source}")
        
        # Initialize session with headers
        self._setup_session()
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
    
    def _setup_session(self) -> None:
        """Setup HTTP session with headers and configuration."""
        # Set default headers
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Override with source-specific headers
        source_headers = self.source_config.get('headers', {})
        default_headers.update(source_headers)
        
        self.session.headers.update(default_headers)
        
        # Set timeouts
        self.session.timeout = self.config.get('scraping', {}).get('timeout', 30)
    
    def add_observer(self, observer: ScrapingObserver) -> None:
        """Add progress observer."""
        self.observers.append(observer)
    
    def remove_observer(self, observer: ScrapingObserver) -> None:
        """Remove progress observer."""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def _notify_page_scraped(self, page: int, products_found: int) -> None:
        """Notify observers of page completion."""
        for observer in self.observers:
            observer.on_page_scraped(page, products_found, self.source)
    
    def _notify_error(self, error: str, page: Optional[int] = None) -> None:
        """Notify observers of errors."""
        for observer in self.observers:
            observer.on_error(error, self.source, page)
    
    def _notify_completed(self, result: ScrapingResult) -> None:
        """Notify observers of completion."""
        for observer in self.observers:
            observer.on_scraping_completed(result)
    
    def _rate_limit(self) -> None:
        """
        Implement intelligent rate limiting.
        """
        current_time = time.time()
        
        # Get delay configuration
        delay_range = self.source_config.get('delay_range', 
                                           self.config.get('scraping', {}).get('delay_range', [1, 3]))
        
        # Calculate delay
        if isinstance(delay_range, list) and len(delay_range) == 2:
            delay = random.uniform(delay_range[0], delay_range[1])
        else:
            delay = 2.0  # default
        
        # Apply delay if needed
        time_since_last = current_time - self.last_request_time
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    @retry_on_failure(max_retries=3, delay=2.0)
    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with rate limiting and error handling.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails
        """
        self._rate_limit()
        
        self.logger.debug(f"Making request to: {url}")
        
        try:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            
            # Check for anti-bot detection
            self._check_anti_bot_response(response)
            
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise
    
    def _check_anti_bot_response(self, response: requests.Response) -> None:
        """
        Check response for anti-bot detection indicators.
        
        Args:
            response: HTTP response to check
            
        Raises:
            Exception: If anti-bot detection is detected
        """
        content_lower = response.text.lower()
        
        # Common anti-bot indicators
        anti_bot_indicators = [
            'captcha',
            'robot',
            'automation',
            'security check',
            'access denied',
            'rate limit',
            'too many requests'
        ]
        
        for indicator in anti_bot_indicators:
            if indicator in content_lower:
                self.logger.warning(f"Anti-bot detection detected: {indicator}")
                raise Exception(f"Anti-bot protection triggered: {indicator}")
    
    def _build_search_url(self, keyword: str, page: int = 1) -> str:
        """
        Build search URL for given keyword and page.
        
        Args:
            keyword: Search keyword
            page: Page number
            
        Returns:
            Complete search URL
        """
        base_url = self.source_config.get('base_url', '')
        search_path = self.source_config.get('search_path', '')
        
        if not base_url or not search_path:
            raise ValueError(f"Missing URL configuration for source: {self.source}")
        
        # Format the search path with keyword and page
        formatted_path = search_path.format(keyword=keyword, page=page)
        
        return urljoin(base_url, formatted_path)
    
    def _extract_product_data(self, element: Any, page: int, position: int) -> Dict[str, Any]:
        """
        Extract product data from HTML element.
        
        Args:
            element: HTML element containing product data
            page: Page number
            position: Position on page
            
        Returns:
            Dictionary with extracted product data
        """
        # This method should be implemented by subclasses
        # with specific extraction logic for each scraping method
        data = {
            'source': self.source,
            'page_number': page,
            'position_on_page': position,
            'scraped_at': datetime.now()
        }
        
        return data
    
    def _clean_product_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and normalize extracted product data.
        
        Args:
            data: Raw extracted data
            
        Returns:
            Cleaned data dictionary
        """
        cleaned = data.copy()
        
        # Clean text fields
        text_fields = ['title', 'description', 'brand', 'condition', 'availability']
        for field in text_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = clean_text(str(cleaned[field]))
        
        # Extract and validate price
        if 'price' in cleaned:
            if isinstance(cleaned['price'], str):
                cleaned['price'] = extract_price(cleaned['price'])
        
        # Extract and validate rating
        if 'rating' in cleaned:
            if isinstance(cleaned['rating'], str):
                cleaned['rating'] = extract_rating(cleaned['rating'])
        
        # Normalize URLs
        url_fields = ['url', 'image_url']
        base_url = self.source_config.get('base_url', '')
        for field in url_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = normalize_url(cleaned[field], base_url)
        
        return cleaned
    
    def _validate_product_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate product data quality.
        
        Args:
            data: Product data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields
        required_fields = ['title', 'url', 'source']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Price validation
        if 'price' in data and data['price'] is not None:
            try:
                price = float(data['price'])
                min_price = self.config.get('processing', {}).get('min_price', 0.01)
                max_price = self.config.get('processing', {}).get('max_price', 100000)
                
                if price < min_price or price > max_price:
                    errors.append(f"Price out of range: {price}")
            except (ValueError, TypeError):
                errors.append(f"Invalid price format: {data['price']}")
        
        # URL validation
        if 'url' in data:
            try:
                parsed = urlparse(data['url'])
                if not parsed.scheme or not parsed.netloc:
                    errors.append(f"Invalid URL format: {data['url']}")
            except Exception:
                errors.append(f"URL parsing error: {data['url']}")
        
        return len(errors) == 0, errors
    
    # Template Method Pattern: Define the scraping workflow
    def scrape(self, keywords: List[str], max_pages: int = 5) -> ScrapingResult:
        """
        Main scraping method implementing Template Method Pattern.
        
        Args:
            keywords: List of search keywords
            max_pages: Maximum pages to scrape per keyword
            
        Returns:
            ScrapingResult with scraped data and metadata
        """
        start_time = time.time()
        result = ScrapingResult()
        
        try:
            self.logger.info(f"Starting scraping for {self.source} with keywords: {keywords}")
            
            for keyword in keywords:
                for page in range(1, max_pages + 1):
                    try:
                        # Get page data using strategy-specific method
                        page_data = self._scrape_page(keyword, page)
                        
                        if page_data:
                            result.data.extend(page_data)
                            result.pages_scraped += 1
                            self._notify_page_scraped(page, len(page_data))
                            
                            self.logger.info(f"Scraped page {page} for '{keyword}': {len(page_data)} products")
                        else:
                            self.logger.warning(f"No data found on page {page} for '{keyword}'")
                            
                    except Exception as e:
                        error_msg = f"Failed to scrape page {page} for '{keyword}': {str(e)}"
                        result.errors.append(error_msg)
                        self._notify_error(error_msg, page)
                        self.logger.error(error_msg)
            
            # Set result metadata
            result.success = len(result.data) > 0
            result.total_products = len(result.data)
            result.execution_time = time.time() - start_time
            result.metadata = {
                'source': self.source,
                'keywords': keywords,
                'max_pages': max_pages,
                'request_count': self.request_count
            }
            
            self.logger.info(f"Scraping completed: {result.total_products} products in {result.execution_time:.2f}s")
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Scraping failed: {str(e)}")
            self.logger.error(f"Scraping failed: {e}")
        
        finally:
            self._notify_completed(result)
        
        return result
    
    @abstractmethod
    def _scrape_page(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """
        Scrape a single page for a keyword.
        
        This method must be implemented by subclasses using their specific
        scraping strategy (BeautifulSoup, Selenium, etc.).
        
        Args:
            keyword: Search keyword
            page: Page number
            
        Returns:
            List of product data dictionaries
        """
        pass
    
    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close() 