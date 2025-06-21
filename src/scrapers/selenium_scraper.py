"""
Dynamic scraper implementation using Selenium WebDriver.

This scraper handles JavaScript-heavy websites that require browser automation.
Ideal for dynamic content, form submissions, and complex interactions.
"""

from typing import Dict, List, Any, Optional
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    WebDriverException, ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager

from .base_scraper import BaseScraper
from src.utils.helpers import extract_price, extract_rating, clean_text, normalize_url

class SeleniumScraper(BaseScraper):
    """
    Dynamic scraper using Selenium WebDriver for JavaScript execution.
    
    Implements Strategy Pattern for dynamic content scraping.
    """
    
    def __init__(self, source: str, config: Dict[str, Any]):
        """
        Initialize Selenium scraper.
        
        Args:
            source: Source name (amazon, ebay, walmart)
            config: Configuration dictionary
        """
        super().__init__(source, config)
        
        self.driver = None
        self.wait = None
        
        # Load scraper-specific selectors
        try:
            from src.utils.config import load_config
            scraper_config = load_config('config/scrapers.yaml')
            self.selectors = scraper_config.get(source, {}).get('selectors', {})
        except Exception as e:
            self.logger.warning(f"Failed to load selectors for {source}: {e}")
            self.selectors = {}
        
        # Setup WebDriver
        self._setup_webdriver()
    
    def _setup_webdriver(self) -> None:
        """Setup Chrome WebDriver with optimal configuration."""
        try:
            # Chrome options
            chrome_options = Options()
            
            # Default options for headless browsing
            selenium_config = self.config.get('selenium', {})
            default_options = [
                "--headless",
                "--no-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images",  # Faster loading
                "--disable-javascript",  # Can be overridden if needed
            ]
            
            # Get options from config
            config_options = selenium_config.get('chrome_options', default_options)
            
            for option in config_options:
                chrome_options.add_argument(option)
            
            # Additional stealth options
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Disable loading images for faster scraping
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Setup ChromeDriver service
            service = Service(ChromeDriverManager().install())
            
            # Create WebDriver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Configure timeouts
            implicit_wait = selenium_config.get('implicit_wait', 10)
            page_load_timeout = selenium_config.get('page_load_timeout', 30)
            
            self.driver.implicitly_wait(implicit_wait)
            self.driver.set_page_load_timeout(page_load_timeout)
            
            # Setup WebDriverWait
            self.wait = WebDriverWait(self.driver, 10)
            
            # Execute stealth script
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            self.logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            raise
    
    def _scrape_page(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """
        Scrape a single page using Selenium WebDriver.
        
        Args:
            keyword: Search keyword
            page: Page number
            
        Returns:
            List of product data dictionaries
        """
        try:
            # Build search URL
            url = self._build_search_url(keyword, page)
            
            # Navigate to page
            self._navigate_to_page(url)
            
            # Wait for content to load
            self._wait_for_content_load()
            
            # Handle any popups or overlays
            self._handle_popups()
            
            # Extract products based on source
            if self.source == 'amazon':
                return self._extract_amazon_products_selenium(keyword, page)
            elif self.source == 'ebay':
                return self._extract_ebay_products_selenium(keyword, page)
            elif self.source == 'walmart':
                return self._extract_walmart_products_selenium(keyword, page)
            else:
                return self._extract_generic_products_selenium(keyword, page)
                
        except Exception as e:
            self.logger.error(f"Failed to scrape page {page} for '{keyword}': {e}")
            # Take screenshot for debugging
            self._take_screenshot(f"error_page_{page}_{keyword}")
            raise
    
    def _navigate_to_page(self, url: str) -> None:
        """Navigate to URL with error handling."""
        try:
            self.logger.debug(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Apply rate limiting
            self._rate_limit()
            
        except TimeoutException:
            self.logger.warning(f"Page load timeout for: {url}")
            raise
        except WebDriverException as e:
            self.logger.error(f"WebDriver error navigating to {url}: {e}")
            raise
    
    def _wait_for_content_load(self) -> None:
        """Wait for main content to load."""
        try:
            # Wait for body element
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Check for loading indicators and wait for them to disappear
            loading_selectors = [
                ".loading", ".spinner", "[data-loading='true']",
                ".load-more", ".lazy-load"
            ]
            
            for selector in loading_selectors:
                try:
                    self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, selector)))
                except TimeoutException:
                    pass  # Loading indicator not found or already gone
                    
        except TimeoutException:
            self.logger.warning("Content load timeout")
    
    def _handle_popups(self) -> None:
        """Handle common popups and overlays."""
        popup_selectors = [
            # Common popup close buttons
            "[data-testid='close-button']",
            ".modal-close",
            ".popup-close", 
            ".overlay-close",
            "[aria-label='Close']",
            ".close-btn",
            # Cookie banners
            "#sp-cc-accept", # Amazon cookie banner
            ".gdpr-banner button",
            "#onetrust-accept-btn-handler"
        ]
        
        for selector in popup_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    self.driver.execute_script("arguments[0].click();", element)
                    time.sleep(1)
                    self.logger.debug(f"Closed popup: {selector}")
                    break
            except (NoSuchElementException, ElementClickInterceptedException):
                continue
    
    def _extract_amazon_products_selenium(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """Extract Amazon products using Selenium."""
        products = []
        
        try:
            # Wait for search results
            container_selector = self.selectors.get('product_container', '[data-component-type="s-search-result"]')
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, container_selector)))
            
            # Find product containers
            containers = self.driver.find_elements(By.CSS_SELECTOR, container_selector)
            
            for i, container in enumerate(containers, 1):
                try:
                    product = self._extract_amazon_product_selenium(container, keyword, page, i)
                    if product:
                        products.append(product)
                except Exception as e:
                    self.logger.debug(f"Failed to extract Amazon product {i}: {e}")
                    continue
            
        except TimeoutException:
            self.logger.warning("No Amazon products found or timeout")
        
        return products
    
    def _extract_amazon_product_selenium(self, container, keyword: str, page: int, position: int) -> Optional[Dict[str, Any]]:
        """Extract single Amazon product using Selenium."""
        try:
            # Extract title
            title_selector = self.selectors.get('title', 'h2 a span')
            title_element = container.find_element(By.CSS_SELECTOR, title_selector)
            title = clean_text(title_element.text) if title_element else None
            
            if not title:
                return None
            
            # Extract link
            link_selector = self.selectors.get('link', 'h2 a')
            link_element = container.find_element(By.CSS_SELECTOR, link_selector)
            relative_url = link_element.get_attribute('href') if link_element else None
            url = normalize_url(relative_url, self.source_config.get('base_url', '')) if relative_url else None
            
            # Extract price
            price = None
            price_selectors = [
                '.a-price .a-offscreen',
                '.a-price-whole',
                '.a-price-range .a-offscreen'
            ]
            
            for price_selector in price_selectors:
                try:
                    price_element = container.find_element(By.CSS_SELECTOR, price_selector)
                    price_text = price_element.text or price_element.get_attribute('textContent')
                    price = extract_price(price_text)
                    if price:
                        break
                except NoSuchElementException:
                    continue
            
            # Extract rating
            rating = None
            try:
                rating_element = container.find_element(By.CSS_SELECTOR, '.a-icon-alt')
                rating_text = rating_element.get_attribute('alt')
                rating = extract_rating(rating_text)
            except NoSuchElementException:
                pass
            
            # Extract image
            image_url = None
            try:
                image_element = container.find_element(By.CSS_SELECTOR, '.s-image')
                image_url = image_element.get_attribute('src')
            except NoSuchElementException:
                pass
            
            # Extract ASIN
            asin = None
            if url:
                import re
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
    
    def _extract_ebay_products_selenium(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """Extract eBay products using Selenium."""
        products = []
        
        try:
            # Wait for search results
            container_selector = self.selectors.get('product_container', '.s-item')
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, container_selector)))
            
            containers = self.driver.find_elements(By.CSS_SELECTOR, container_selector)
            
            for i, container in enumerate(containers, 1):
                try:
                    product = self._extract_ebay_product_selenium(container, keyword, page, i)
                    if product:
                        products.append(product)
                except Exception as e:
                    self.logger.debug(f"Failed to extract eBay product {i}: {e}")
                    continue
            
        except TimeoutException:
            self.logger.warning("No eBay products found or timeout")
        
        return products
    
    def _extract_ebay_product_selenium(self, container, keyword: str, page: int, position: int) -> Optional[Dict[str, Any]]:
        """Extract single eBay product using Selenium."""
        try:
            # Extract title
            title_element = container.find_element(By.CSS_SELECTOR, '.s-item__title')
            title = clean_text(title_element.text) if title_element else None
            
            if not title or 'shop on ebay' in title.lower():
                return None
            
            # Extract other fields similar to static scraper but using Selenium methods
            # ... (implementation similar to static scraper but using Selenium element methods)
            
            product = {
                'source': self.source,
                'title': title,
                'search_keyword': keyword,
                'page_number': page,
                'position_on_page': position
            }
            
            return self._clean_product_data(product)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract eBay product: {e}")
            return None
    
    def _extract_walmart_products_selenium(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """Extract Walmart products using Selenium."""
        products = []
        
        try:
            # Walmart often requires scrolling to load more products
            self._scroll_to_load_content()
            
            container_selector = self.selectors.get('product_container', '[data-automation-id="product-tile"]')
            containers = self.driver.find_elements(By.CSS_SELECTOR, container_selector)
            
            for i, container in enumerate(containers, 1):
                try:
                    product = self._extract_walmart_product_selenium(container, keyword, page, i)
                    if product:
                        products.append(product)
                except Exception as e:
                    self.logger.debug(f"Failed to extract Walmart product {i}: {e}")
                    continue
            
        except Exception as e:
            self.logger.warning(f"Failed to extract Walmart products: {e}")
        
        return products
    
    def _extract_walmart_product_selenium(self, container, keyword: str, page: int, position: int) -> Optional[Dict[str, Any]]:
        """Extract single Walmart product using Selenium."""
        try:
            # Implementation similar to static scraper but using Selenium
            title_element = container.find_element(By.CSS_SELECTOR, '[data-automation-id="product-title"]')
            title = clean_text(title_element.text) if title_element else None
            
            if not title:
                return None
            
            product = {
                'source': self.source,
                'title': title,
                'search_keyword': keyword,
                'page_number': page,
                'position_on_page': position
            }
            
            return self._clean_product_data(product)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract Walmart product: {e}")
            return None
    
    def _extract_generic_products_selenium(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """Extract products using generic selectors with Selenium."""
        products = []
        
        # Generic selectors to try
        selectors_to_try = [
            '.product', '.item', '.result',
            '[data-testid*="product"]', '[class*="product"]'
        ]
        
        containers = []
        for selector in selectors_to_try:
            containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if containers:
                containers = containers[:20]  # Limit to 20 products
                break
        
        for i, container in enumerate(containers, 1):
            try:
                product = self._extract_generic_product_selenium(container, keyword, page, i)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug(f"Failed to extract generic product {i}: {e}")
                continue
        
        return products
    
    def _extract_generic_product_selenium(self, container, keyword: str, page: int, position: int) -> Optional[Dict[str, Any]]:
        """Extract product using generic selectors with Selenium."""
        try:
            # Try to find title
            title = None
            title_selectors = ['h1', 'h2', 'h3', '.title', '[class*="title"]', '[class*="name"]']
            for selector in title_selectors:
                try:
                    element = container.find_element(By.CSS_SELECTOR, selector)
                    title = clean_text(element.text)
                    break
                except NoSuchElementException:
                    continue
            
            if not title:
                return None
            
            product = {
                'source': self.source,
                'title': title,
                'search_keyword': keyword,
                'page_number': page,
                'position_on_page': position
            }
            
            return self._clean_product_data(product)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract generic product: {e}")
            return None
    
    def _scroll_to_load_content(self) -> None:
        """Scroll down to trigger lazy loading of content."""
        try:
            # Scroll to bottom to load all products
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            self.logger.debug(f"Failed to scroll: {e}")
    
    def _take_screenshot(self, filename: str) -> None:
        """Take screenshot for debugging."""
        try:
            screenshot_dir = "screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            filepath = os.path.join(screenshot_dir, f"{filename}.png")
            self.driver.save_screenshot(filepath)
            self.logger.debug(f"Screenshot saved: {filepath}")
        except Exception as e:
            self.logger.debug(f"Failed to take screenshot: {e}")
    
    def submit_form(self, form_data: Dict[str, str]) -> bool:
        """
        Submit form data for login or search.
        
        Args:
            form_data: Dictionary with field names and values
            
        Returns:
            True if form submission successful
        """
        try:
            for field_name, value in form_data.items():
                # Try different selector strategies
                selectors = [
                    f'input[name="{field_name}"]',
                    f'#{field_name}',
                    f'[data-testid="{field_name}"]'
                ]
                
                field_found = False
                for selector in selectors:
                    try:
                        field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        field.clear()
                        field.send_keys(value)
                        field_found = True
                        break
                    except NoSuchElementException:
                        continue
                
                if not field_found:
                    self.logger.warning(f"Form field not found: {field_name}")
                    return False
            
            # Submit form
            submit_selectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                '.submit-btn',
                '[data-testid="submit"]'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    submit_btn.click()
                    time.sleep(3)  # Wait for submission
                    return True
                except NoSuchElementException:
                    continue
            
            self.logger.warning("Submit button not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Form submission failed: {e}")
            return False
    
    def close(self) -> None:
        """Clean up WebDriver resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.debug("WebDriver closed successfully")
        except Exception as e:
            self.logger.debug(f"Error closing WebDriver: {e}")
        
        # Call parent close method
        super().close() 