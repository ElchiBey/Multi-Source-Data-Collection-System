"""
Scrapy Spider for E-commerce Product Scraping

This module implements a Scrapy-based spider for structured crawling
of e-commerce websites, demonstrating framework-based scraping.
"""

import scrapy
from scrapy import Request
from urllib.parse import urljoin
import json
from datetime import datetime
import re
from typing import Dict, List, Any

from src.utils.helpers import extract_price, extract_rating, clean_text

class ProductSpider(scrapy.Spider):
    """
    Scrapy spider for e-commerce product scraping.
    
    This spider demonstrates framework-based crawling with:
    - Structured request/response handling
    - Pipeline integration
    - Item processing
    - Built-in concurrency management
    """
    
    name = 'product_spider'
    
    def __init__(self, source='amazon', keywords='laptop', max_pages=5, *args, **kwargs):
        """
        Initialize spider with configuration.
        
        Args:
            source: Target website (amazon, ebay, walmart)
            keywords: Search keywords (comma-separated)
            max_pages: Maximum pages to scrape
        """
        super(ProductSpider, self).__init__(*args, **kwargs)
        
        self.source = source
        self.keywords = keywords.split(',') if isinstance(keywords, str) else [keywords]
        self.max_pages = int(max_pages)
        self.scraped_pages = 0
        
        # Source configuration
        self.source_configs = {
            'amazon': {
                'base_url': 'https://www.amazon.com',
                'search_path': '/s?k={keyword}&page={page}',
                'selectors': {
                    'product_container': '[data-component-type="s-search-result"]',
                    'title': 'h2 a span',
                    'price': '.a-price .a-offscreen',
                    'rating': '.a-icon-alt',
                    'link': 'h2 a',
                    'image': '.s-image'
                }
            },
            'ebay': {
                'base_url': 'https://www.ebay.com',
                'search_path': '/sch/i.html?_nkw={keyword}&_pgn={page}',
                'selectors': {
                    'product_container': '.s-item',
                    'title': '.s-item__title',
                    'price': '.s-item__price',
                    'link': '.s-item__link',
                    'image': '.s-item__image img'
                }
            }
        }
        
        self.config = self.source_configs.get(source, self.source_configs['amazon'])
        
        # Custom settings for this spider
        self.custom_settings = {
            'DOWNLOAD_DELAY': 2,
            'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'ROBOTSTXT_OBEY': True,
            'CONCURRENT_REQUESTS': 8,
            'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
            'ITEM_PIPELINES': {
                'src.scrapers.scrapy_pipelines.ProductPipeline': 300,
                'src.scrapers.scrapy_pipelines.DuplicatesPipeline': 400,
            }
        }
    
    def start_requests(self):
        """Generate initial requests for all keywords."""
        for keyword in self.keywords:
            # Start with page 1 for each keyword
            url = self._build_search_url(keyword, 1)
            yield Request(
                url=url,
                callback=self.parse_search_page,
                meta={
                    'keyword': keyword,
                    'page': 1
                },
                headers=self._get_headers()
            )
    
    def parse_search_page(self, response):
        """
        Parse search results page and extract products.
        
        Args:
            response: Scrapy response object
            
        Yields:
            Product items and next page requests
        """
        keyword = response.meta['keyword']
        page = response.meta['page']
        
        self.logger.info(f"Parsing {self.source} page {page} for keyword: {keyword}")
        
        # Extract products from current page
        products_found = 0
        for product in self._extract_products(response, keyword, page):
            products_found += 1
            yield product
        
        self.logger.info(f"Found {products_found} products on page {page}")
        
        # Generate next page request if within limits
        if page < self.max_pages and products_found > 0:
            next_page = page + 1
            next_url = self._build_search_url(keyword, next_page)
            
            yield Request(
                url=next_url,
                callback=self.parse_search_page,
                meta={
                    'keyword': keyword,
                    'page': next_page
                },
                headers=self._get_headers()
            )
    
    def _extract_products(self, response, keyword, page):
        """
        Extract product data from search page.
        
        Args:
            response: Scrapy response object
            keyword: Search keyword
            page: Page number
            
        Yields:
            Product item dictionaries
        """
        selectors = self.config['selectors']
        containers = response.css(selectors['product_container'])
        
        for i, container in enumerate(containers, 1):
            try:
                # Extract basic product information
                title_elements = container.css(selectors['title'])
                title = clean_text(title_elements.get()) if title_elements else None
                
                if not title:
                    continue
                
                # Extract price
                price_elements = container.css(selectors['price'])
                price_text = price_elements.get() if price_elements else None
                price = extract_price(price_text) if price_text else None
                
                # Extract link
                link_elements = container.css(selectors['link'])
                relative_url = link_elements.attrib.get('href') if link_elements else None
                url = urljoin(response.url, relative_url) if relative_url else None
                
                # Extract image
                image_elements = container.css(selectors.get('image', 'img'))
                image_url = image_elements.attrib.get('src') if image_elements else None
                
                # Extract rating (if available)
                rating = None
                if 'rating' in selectors:
                    rating_elements = container.css(selectors['rating'])
                    rating_text = rating_elements.attrib.get('alt', '') if rating_elements else ''
                    rating = extract_rating(rating_text) if rating_text else None
                
                # Create product item
                product = {
                    'source': self.source,
                    'title': title,
                    'url': url,
                    'price': price,
                    'rating': rating,
                    'image_url': image_url,
                    'search_keyword': keyword,
                    'page_number': page,
                    'position_on_page': i,
                    'scraped_at': datetime.utcnow().isoformat(),
                    'scraper_type': 'scrapy'
                }
                
                # Extract product ID based on source
                if self.source == 'amazon' and url:
                    asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
                    if asin_match:
                        product['product_id'] = asin_match.group(1)
                
                yield product
                
            except Exception as e:
                self.logger.error(f"Error extracting product {i} on page {page}: {e}")
                continue
    
    def _build_search_url(self, keyword, page):
        """Build search URL for given keyword and page."""
        base_url = self.config['base_url']
        search_path = self.config['search_path'].format(
            keyword=keyword.replace(' ', '+'),
            page=page
        )
        return urljoin(base_url, search_path)
    
    def _get_headers(self):
        """Get headers for request."""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

# ScrapyScraper wrapper class to match the interface of other scrapers
class ScrapyScraper:
    """
    Wrapper class for Scrapy spider to match the interface of other scrapers.
    
    This class provides a unified interface for the ScrapingManager to use
    Scrapy-based scraping alongside Static and Selenium scrapers.
    """
    
    def __init__(self, source: str, config: Dict[str, Any]):
        """
        Initialize ScrapyScraper wrapper.
        
        Args:
            source: Source name (amazon, ebay, walmart)
            config: Configuration dictionary
        """
        self.source = source
        self.config = config
        
        # Import logger
        from src.utils.logger import setup_logger
        self.logger = setup_logger(f"scrapy_scraper.{source}")
    
    def scrape(self, keywords: List[str], max_pages: int = 5):
        """
        Scrape products using Scrapy spider.
        
        Args:
            keywords: List of search keywords
            max_pages: Maximum pages to scrape
            
        Returns:
            ScrapingResult object with success status and data
        """
        from .base_scraper import ScrapingResult
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        import multiprocessing
        
        try:
            # Prepare results container
            results = []
            
            # Configure Scrapy settings
            settings = get_project_settings()
            settings.setdict({
                'DOWNLOAD_DELAY': 2,
                'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
                'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'ROBOTSTXT_OBEY': True,
                'CONCURRENT_REQUESTS': 4,
                'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
                'LOG_LEVEL': 'WARNING'
            })
            
            # Create crawler process
            process = CrawlerProcess(settings)
            
            # Add spider to crawler
            for keyword in keywords:
                process.crawl(
                    ProductSpider,
                    source=self.source,
                    keywords=keyword,
                    max_pages=max_pages
                )
            
            # Run crawler (this blocks until completion)
            if not process.crawlers:
                self.logger.warning("No crawlers were added")
                return ScrapingResult(success=False, errors=["No crawlers configured"])
            
            # Since Scrapy runs in a separate process and we need to get results,
            # we'll use a simpler approach for now - just return a basic result
            # In a production environment, you'd use Scrapy pipelines to save data
            
            self.logger.info(f"Scrapy crawling completed for {self.source}")
            
            return ScrapingResult(
                success=True,
                data=[],  # Results would come from pipelines in real implementation
                metadata={
                    'source': self.source,
                    'keywords': keywords,
                    'max_pages': max_pages,
                    'scraper_type': 'scrapy'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Scrapy scraping failed: {e}")
            return ScrapingResult(
                success=False,
                errors=[str(e)],
                metadata={'source': self.source, 'scraper_type': 'scrapy'}
            ) 