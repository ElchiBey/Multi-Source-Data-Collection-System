"""
Static scraper implementation using BeautifulSoup4.

This scraper handles static HTML content without JavaScript execution.
Ideal for simple websites with server-side rendered content.
"""

from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup, Tag
import requests
from urllib.parse import urljoin
import re
import random

from .base_scraper import BaseScraper
from src.utils.helpers import (
    extract_price, extract_rating, clean_text, normalize_url,
    get_random_headers, random_delay, get_proxy_list, should_use_proxy
)

class StaticScraper(BaseScraper):
    """
    Static scraper using BeautifulSoup4 for HTML parsing.
    
    Implements Strategy Pattern for static content scraping with anti-bot protection.
    """
    
    def __init__(self, source: str, config: Dict[str, Any]):
        """
        Initialize static scraper.
        
        Args:
            source: Source name (amazon, ebay, walmart)
            config: Configuration dictionary
        """
        super().__init__(source, config)
        
        # Initialize session for connection reuse
        self.session = requests.Session()
        
        # Load scraper-specific selectors
        try:
            import yaml
            with open('config/scrapers.yaml', 'r') as f:
                scraper_config = yaml.safe_load(f)
            self.selectors = scraper_config.get(source, {}).get('selectors', {})
        except Exception as e:
            self.logger.warning(f"Failed to load selectors for {source}: {e}")
            self.selectors = {}
    
    def _make_request(self, url: str, retries: int = 3) -> requests.Response:
        """
        Make HTTP request with anti-bot protection.
        
        Args:
            url: URL to request
            retries: Number of retry attempts
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails after retries
        """
        for attempt in range(retries):
            try:
                # Add random delay between requests
                if attempt > 0:
                    random_delay(2.0, 5.0)  # Longer delay on retries
                else:
                    random_delay(1.0, 3.0)  # Normal delay
                
                # Get random headers
                headers = get_random_headers()
                
                # Add referer header for subsequent requests
                if hasattr(self, '_last_url'):
                    headers['Referer'] = self._last_url
                
                # Configure proxy if needed
                proxies = {}
                if should_use_proxy():
                    proxy_list = get_proxy_list()
                    if proxy_list:
                        proxy = random.choice(proxy_list)
                        proxies = {'http': proxy, 'https': proxy}
                        self.logger.debug(f"Using proxy: {proxy}")
                
                # Make request
                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=30,
                    allow_redirects=True
                )
                
                # Check for common anti-bot responses
                if self._is_blocked_response(response):
                    self.logger.warning(f"Blocked response detected on attempt {attempt + 1}")
                    if attempt < retries - 1:
                        continue
                    else:
                        raise requests.RequestException("Blocked by anti-bot protection")
                
                response.raise_for_status()
                self._last_url = url
                
                self.logger.debug(f"Successfully requested {url} (attempt {attempt + 1})")
                return response
                
            except requests.RequestException as e:
                self.logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise
                
        raise requests.RequestException(f"Failed to request {url} after {retries} attempts")
    
    def _is_blocked_response(self, response: requests.Response) -> bool:
        """
        Check if response indicates we're blocked by anti-bot protection.
        
        Args:
            response: HTTP response to check
            
        Returns:
            True if response indicates blocking
        """
        # Check status codes
        if response.status_code in [403, 429, 503]:
            return True
        
        # Check for common blocking indicators in content
        if response.text:
            blocking_indicators = [
                'access denied',
                'blocked',
                'captcha',
                'cloudflare',
                'please verify you are human',
                'unusual traffic',
                'automated queries',
                'robot',
                'bot detected',
            ]
            
            content_lower = response.text.lower()
            for indicator in blocking_indicators:
                if indicator in content_lower:
                    self.logger.warning(f"Blocking indicator found: {indicator}")
                    return True
        
        # Check response size (very small responses might be blocks)
        if len(response.text) < 500:
            self.logger.warning("Suspiciously small response size")
            return True
            
        return False
    
    def _scrape_page(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """
        Scrape a single page using BeautifulSoup4.
        
        Args:
            keyword: Search keyword
            page: Page number
            
        Returns:
            List of product data dictionaries
        """
        try:
            # Build search URL
            url = self._build_search_url(keyword, page)
            
            # Make request
            response = self._make_request(url)
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract products based on source
            if self.source == 'amazon':
                return self._extract_amazon_products(soup, keyword, page)
            elif self.source == 'ebay':
                return self._extract_ebay_products(soup, keyword, page)
            elif self.source == 'walmart':
                return self._extract_walmart_products(soup, keyword, page)
            else:
                return self._extract_generic_products(soup, keyword, page)
                
        except Exception as e:
            self.logger.error(f"Failed to scrape page {page} for '{keyword}': {e}")
            raise
    
    def _extract_amazon_products(self, soup: BeautifulSoup, keyword: str, page: int) -> List[Dict[str, Any]]:
        """
        Extract products from Amazon search results.
        
        Args:
            soup: BeautifulSoup parsed HTML
            keyword: Search keyword
            page: Page number
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        # Find product containers
        product_containers = soup.select(self.selectors.get('product_container', '[data-component-type="s-search-result"]'))
        
        for i, container in enumerate(product_containers, 1):
            try:
                product = self._extract_amazon_product(container, keyword, page, i)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug(f"Failed to extract Amazon product {i}: {e}")
                continue
        
        return products
    
    def _extract_amazon_product(self, container: Tag, keyword: str, page: int, position: int) -> Optional[Dict[str, Any]]:
        """Extract single Amazon product from container."""
        try:
            # Extract title
            title_element = container.select_one(self.selectors.get('title', 'h2 a span'))
            title = clean_text(title_element.get_text()) if title_element else None
            
            if not title:
                return None
            
            # Extract link
            link_element = container.select_one(self.selectors.get('link', 'h2 a'))
            relative_url = link_element.get('href') if link_element else None
            url = normalize_url(relative_url, self.source_config.get('base_url', '')) if relative_url else None
            
            # Extract price
            price_element = container.select_one(self.selectors.get('price', '.a-price .a-offscreen'))
            price_text = price_element.get_text() if price_element else None
            price = extract_price(price_text) if price_text else None
            
            # Extract rating
            rating_element = container.select_one(self.selectors.get('rating', '.a-icon-alt'))
            rating_text = rating_element.get('alt', '') if rating_element else ''
            rating = extract_rating(rating_text) if rating_text else None
            
            # Extract image
            image_element = container.select_one(self.selectors.get('image', '.s-image'))
            image_url = image_element.get('src') if image_element else None
            
            # Extract ASIN from URL
            asin = None
            if url:
                asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
                if asin_match:
                    asin = asin_match.group(1)
            
            product = {
                'source': self.source,
                'title': title,
                'url': url,
                'product_id': asin,
                'price': price,
                'rating': rating,
                'image_url': image_url,
                'search_keyword': keyword,
                'page_number': page,
                'position_on_page': position
            }
            
            return self._clean_product_data(product)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract Amazon product: {e}")
            return None
    
    def _extract_ebay_products(self, soup: BeautifulSoup, keyword: str, page: int) -> List[Dict[str, Any]]:
        """
        Extract products from eBay search results.
        
        Args:
            soup: BeautifulSoup parsed HTML
            keyword: Search keyword
            page: Page number
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        # Find product containers
        product_containers = soup.select(self.selectors.get('product_container', '.s-item'))
        
        for i, container in enumerate(product_containers, 1):
            try:
                product = self._extract_ebay_product(container, keyword, page, i)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug(f"Failed to extract eBay product {i}: {e}")
                continue
        
        return products
    
    def _extract_ebay_product(self, container: Tag, keyword: str, page: int, position: int) -> Optional[Dict[str, Any]]:
        """Extract single eBay product from container."""
        try:
            # Extract title
            title_element = container.select_one(self.selectors.get('title', '.s-item__title'))
            title = clean_text(title_element.get_text()) if title_element else None
            
            if not title or 'shop on ebay' in title.lower():
                return None
            
            # Extract link
            link_element = container.select_one(self.selectors.get('link', '.s-item__link'))
            url = link_element.get('href') if link_element else None
            
            # Extract price
            price_element = container.select_one(self.selectors.get('price', '.s-item__price'))
            price_text = price_element.get_text() if price_element else None
            price = extract_price(price_text) if price_text else None
            
            # Extract condition
            condition_element = container.select_one(self.selectors.get('condition', '.s-item__subtitle'))
            condition = clean_text(condition_element.get_text()) if condition_element else None
            
            # Extract shipping
            shipping_element = container.select_one(self.selectors.get('shipping', '.s-item__shipping'))
            shipping_text = clean_text(shipping_element.get_text()) if shipping_element else None
            shipping_cost = extract_price(shipping_text) if shipping_text else None
            
            # Extract image
            image_element = container.select_one(self.selectors.get('image', '.s-item__image img'))
            image_url = image_element.get('src') if image_element else None
            
            # Extract item ID from URL
            item_id = None
            if url:
                item_match = re.search(r'/itm/(\d+)', url)
                if item_match:
                    item_id = item_match.group(1)
            
            product = {
                'source': self.source,
                'title': title,
                'url': url,
                'product_id': item_id,
                'price': price,
                'condition': condition,
                'shipping_cost': shipping_cost,
                'image_url': image_url,
                'search_keyword': keyword,
                'page_number': page,
                'position_on_page': position
            }
            
            return self._clean_product_data(product)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract eBay product: {e}")
            return None
    
    def _extract_walmart_products(self, soup: BeautifulSoup, keyword: str, page: int) -> List[Dict[str, Any]]:
        """
        Extract products from Walmart search results.
        
        Args:
            soup: BeautifulSoup parsed HTML
            keyword: Search keyword
            page: Page number
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        # Find product containers
        product_containers = soup.select(self.selectors.get('product_container', '[data-automation-id="product-tile"]'))
        
        for i, container in enumerate(product_containers, 1):
            try:
                product = self._extract_walmart_product(container, keyword, page, i)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug(f"Failed to extract Walmart product {i}: {e}")
                continue
        
        return products
    
    def _extract_walmart_product(self, container: Tag, keyword: str, page: int, position: int) -> Optional[Dict[str, Any]]:
        """Extract single Walmart product from container."""
        try:
            # Extract title
            title_element = container.select_one(self.selectors.get('title', '[data-automation-id="product-title"]'))
            title = clean_text(title_element.get_text()) if title_element else None
            
            if not title:
                return None
            
            # Extract link
            link_element = container.select_one(self.selectors.get('link', 'a'))
            relative_url = link_element.get('href') if link_element else None
            url = normalize_url(relative_url, self.source_config.get('base_url', '')) if relative_url else None
            
            # Extract price
            price_element = container.select_one(self.selectors.get('price', '[data-automation-id="product-price"] span'))
            price_text = price_element.get_text() if price_element else None
            price = extract_price(price_text) if price_text else None
            
            # Extract rating
            rating_element = container.select_one(self.selectors.get('rating', '.average-rating'))
            rating_text = rating_element.get_text() if rating_element else None
            rating = extract_rating(rating_text) if rating_text else None
            
            # Extract image
            image_element = container.select_one(self.selectors.get('image', 'img'))
            image_url = image_element.get('src') if image_element else None
            
            # Extract product ID from URL
            product_id = None
            if url:
                id_match = re.search(r'/ip/[^/]+/(\d+)', url)
                if id_match:
                    product_id = id_match.group(1)
            
            product = {
                'source': self.source,
                'title': title,
                'url': url,
                'product_id': product_id,
                'price': price,
                'rating': rating,
                'image_url': image_url,
                'search_keyword': keyword,
                'page_number': page,
                'position_on_page': position
            }
            
            return self._clean_product_data(product)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract Walmart product: {e}")
            return None
    
    def _extract_generic_products(self, soup: BeautifulSoup, keyword: str, page: int) -> List[Dict[str, Any]]:
        """
        Generic product extraction for unknown sources.
        
        Args:
            soup: BeautifulSoup parsed HTML
            keyword: Search keyword
            page: Page number
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        # Try to find common product patterns
        selectors_to_try = [
            '.product',
            '.item',
            '.result',
            '[data-testid*="product"]',
            '[class*="product"]'
        ]
        
        product_containers = []
        for selector in selectors_to_try:
            containers = soup.select(selector)
            if containers:
                product_containers = containers[:20]  # Limit to 20 products
                break
        
        for i, container in enumerate(product_containers, 1):
            try:
                product = self._extract_generic_product(container, keyword, page, i)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug(f"Failed to extract generic product {i}: {e}")
                continue
        
        return products
    
    def _extract_generic_product(self, container: Tag, keyword: str, page: int, position: int) -> Optional[Dict[str, Any]]:
        """Extract product using generic selectors."""
        try:
            # Try to find title
            title = None
            title_selectors = ['h1', 'h2', 'h3', '.title', '[class*="title"]', '[class*="name"]']
            for selector in title_selectors:
                element = container.select_one(selector)
                if element:
                    title = clean_text(element.get_text())
                    break
            
            if not title:
                return None
            
            # Try to find link
            url = None
            link_element = container.select_one('a')
            if link_element:
                href = link_element.get('href')
                if href:
                    url = normalize_url(href, self.source_config.get('base_url', ''))
            
            # Try to find price
            price = None
            price_selectors = ['.price', '[class*="price"]', '[data-testid*="price"]']
            for selector in price_selectors:
                element = container.select_one(selector)
                if element:
                    price_text = element.get_text()
                    price = extract_price(price_text)
                    if price:
                        break
            
            # Try to find image
            image_url = None
            img_element = container.select_one('img')
            if img_element:
                image_url = img_element.get('src')
                if image_url:
                    image_url = normalize_url(image_url, self.source_config.get('base_url', ''))
            
            product = {
                'source': self.source,
                'title': title,
                'url': url,
                'price': price,
                'image_url': image_url,
                'search_keyword': keyword,
                'page_number': page,
                'position_on_page': position
            }
            
            return self._clean_product_data(product)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract generic product: {e}")
            return None
    
    def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed product information from product page.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dictionary with detailed product information
        """
        try:
            response = self._make_request(product_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if self.source == 'amazon':
                return self._extract_amazon_details(soup)
            elif self.source == 'ebay':
                return self._extract_ebay_details(soup)
            elif self.source == 'walmart':
                return self._extract_walmart_details(soup)
            else:
                return self._extract_generic_details(soup)
                
        except Exception as e:
            self.logger.error(f"Failed to get product details from {product_url}: {e}")
            return None
    
    def _extract_amazon_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract detailed Amazon product information."""
        details = {}
        
        page_selectors = self.selectors.get('product_page', {})
        
        # Extract description
        desc_element = soup.select_one(page_selectors.get('description', '#feature-bullets ul'))
        if desc_element:
            details['description'] = clean_text(desc_element.get_text())
        
        # Extract availability
        avail_element = soup.select_one(page_selectors.get('availability', '#availability span'))
        if avail_element:
            details['availability'] = clean_text(avail_element.get_text())
        
        return details
    
    def _extract_ebay_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract detailed eBay product information."""
        details = {}
        
        page_selectors = self.selectors.get('product_page', {})
        
        # Extract seller info
        seller_element = soup.select_one(page_selectors.get('seller', '.seller-persona'))
        if seller_element:
            details['seller_name'] = clean_text(seller_element.get_text())
        
        return details
    
    def _extract_walmart_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract detailed Walmart product information."""
        details = {}
        
        page_selectors = self.selectors.get('product_page', {})
        
        # Extract specifications
        specs_element = soup.select_one(page_selectors.get('specs', '.specs-table'))
        if specs_element:
            details['specifications'] = clean_text(specs_element.get_text())
        
        return details
    
    def _extract_generic_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract generic product details."""
        details = {}
        
        # Try to find description
        desc_selectors = ['.description', '[class*="description"]', '[class*="detail"]']
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                details['description'] = clean_text(element.get_text())
                break
        
        return details 