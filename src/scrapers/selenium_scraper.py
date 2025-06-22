"""
Selenium scraper implementation for dynamic content.

This scraper handles JavaScript-heavy websites and dynamic content loading.
Includes advanced anti-bot detection evasion techniques.
"""

import time
import random
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException,
    ElementClickInterceptedException, StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager

from .base_scraper import BaseScraper
from src.utils.helpers import (
    extract_price, extract_rating, clean_text, normalize_url,
    get_selenium_options, random_delay
)

class SeleniumScraper(BaseScraper):
    """
    Selenium scraper for dynamic content with anti-bot protection.
    
    Features:
    - Stealth mode configuration
    - Human-like behavior simulation
    - CAPTCHA detection and handling
    - Advanced evasion techniques
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
    
    def _setup_driver(self) -> webdriver.Chrome:
        """
        Setup Chrome driver with anti-bot protection.
        
        Returns:
            Configured Chrome WebDriver instance
        """
        try:
            # Get anti-bot Chrome options
            options = get_selenium_options()
            
            # Additional stealth options
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-ipc-flooding-protection')
            
            # Disable automation indicators
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Setup service
            service = Service(ChromeDriverManager().install())
            
            # Create driver
            driver = webdriver.Chrome(service=service, options=options)
            
            # Execute anti-detection script
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Modify navigator properties
            driver.execute_cdp_cmd('Runtime.evaluate', {
                "expression": """
                    Object.defineProperty(navigator, 'languages', {
                        get: function() { return ['en-US', 'en']; }
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: function() { return [1, 2, 3, 4, 5]; }
                    });
                """
            })
            
            # Set random viewport size
            viewport_sizes = [
                (1366, 768), (1920, 1080), (1440, 900), (1536, 864)
            ]
            width, height = random.choice(viewport_sizes)
            driver.set_window_size(width, height)
            
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    def _simulate_human_behavior(self) -> None:
        """Simulate human-like behavior to avoid detection."""
        # Random mouse movements
        if self.driver and random.random() > 0.7:
            try:
                actions = ActionChains(self.driver)
                
                # Move mouse to random positions
                for _ in range(random.randint(1, 3)):
                    x = random.randint(100, 800)
                    y = random.randint(100, 600)
                    actions.move_by_offset(x, y)
                    actions.pause(random.uniform(0.1, 0.5))
                
                actions.perform()
                
                # Reset mouse position
                actions = ActionChains(self.driver)
                actions.move_by_offset(-x, -y)
                actions.perform()
                
            except Exception:
                pass  # Ignore errors in behavior simulation
    
    def _check_for_captcha(self) -> bool:
        """
        Check if CAPTCHA is present on the page.
        
        Returns:
            True if CAPTCHA detected
        """
        if not self.driver:
            return False
            
        captcha_indicators = [
            "captcha",
            "recaptcha", 
            "hcaptcha",
            "verify you are human",
            "i'm not a robot",
            "prove you're human",
            "security check"
        ]
        
        try:
            page_source = self.driver.page_source.lower()
            for indicator in captcha_indicators:
                if indicator in page_source:
                    self.logger.warning(f"CAPTCHA detected: {indicator}")
                    return True
                    
            # Check for common CAPTCHA elements
            captcha_selectors = [
                "iframe[src*='recaptcha']",
                "div[class*='captcha']",
                "div[id*='captcha']",
                ".g-recaptcha",
                "#captcha"
            ]
            
            for selector in captcha_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.logger.warning(f"CAPTCHA element found: {selector}")
                    return True
                    
        except Exception as e:
            self.logger.debug(f"Error checking for CAPTCHA: {e}")
            
        return False
    
    def _handle_captcha(self) -> bool:
        """
        Handle CAPTCHA detection.
        
        Returns:
            True if CAPTCHA was handled successfully
        """
        self.logger.warning("CAPTCHA detected - implementing handling strategy")
        
        # Strategy 1: Wait and retry
        self.logger.info("Waiting for CAPTCHA to be resolved...")
        time.sleep(random.uniform(10, 30))
        
        # Strategy 2: Refresh page
        if self._check_for_captcha():
            self.logger.info("Refreshing page to bypass CAPTCHA")
            self.driver.refresh()
            time.sleep(random.uniform(5, 10))
            
        # Strategy 3: Change user agent and retry
        if self._check_for_captcha():
            self.logger.warning("CAPTCHA still present - may need manual intervention")
            return False
            
        return True
    
    def _scrape_page(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """
        Scrape a single page using Selenium.
        
        Args:
            keyword: Search keyword
            page: Page number
            
        Returns:
            List of product data dictionaries
        """
        if not self.driver:
            self.driver = self._setup_driver()
            self.wait = WebDriverWait(self.driver, 10)
        
        try:
            # Build search URL
            url = self._build_search_url(keyword, page)
            
            # Navigate to page
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Random delay to appear human
            random_delay(2.0, 5.0)
            
            # Check for CAPTCHA
            if self._check_for_captcha():
                if not self._handle_captcha():
                    raise Exception("CAPTCHA detected and could not be handled")
            
            # Simulate human behavior
            self._simulate_human_behavior()
            
            # Wait for page to load
            self._wait_for_page_load()
            
            # Scroll to load dynamic content
            self._scroll_page()
            
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
            # Don't raise immediately - try to recover
            if "CAPTCHA" not in str(e):
                # Try refreshing page once
                try:
                    self.driver.refresh()
                    time.sleep(5)
                    return []
                except:
                    pass
            raise
    
    def _wait_for_page_load(self) -> None:
        """Wait for page to fully load."""
        try:
            # Wait for document ready state
            self.wait.until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(1, 3))
            
        except TimeoutException:
            self.logger.warning("Page load timeout - continuing anyway")
    
    def _scroll_page(self) -> None:
        """Scroll page to trigger lazy loading and appear human."""
        try:
            # Get page height
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll in chunks
            current_position = 0
            scroll_chunk = random.randint(300, 600)
            
            while current_position < total_height:
                # Scroll down
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                current_position += scroll_chunk
                
                # Random pause
                time.sleep(random.uniform(0.5, 1.5))
                
                # Sometimes scroll back up a bit (human behavior)
                if random.random() > 0.8:
                    back_scroll = random.randint(50, 200)
                    self.driver.execute_script(f"window.scrollTo(0, {current_position - back_scroll});")
                    time.sleep(random.uniform(0.2, 0.8))
                    self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                
                # Check if new content loaded
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height > total_height:
                    total_height = new_height
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            self.logger.debug(f"Error during scrolling: {e}")
    
    def _extract_amazon_products_selenium(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """Extract Amazon products using Selenium."""
        products = []
        
        try:
            # Wait for product containers to load
            container_selector = self.selectors.get('product_container', '[data-component-type="s-search-result"]')
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, container_selector)))
            
            # Find all product containers
            containers = self.driver.find_elements(By.CSS_SELECTOR, container_selector)
            self.logger.info(f"Found {len(containers)} product containers")
            
            for i, container in enumerate(containers, 1):
                try:
                    product = self._extract_amazon_product_selenium(container, keyword, page, i)
                    if product:
                        products.append(product)
                except StaleElementReferenceException:
                    self.logger.debug(f"Stale element reference for product {i}")
                    continue
                except Exception as e:
                    self.logger.debug(f"Failed to extract Amazon product {i}: {e}")
                    continue
            
        except TimeoutException:
            self.logger.warning("No Amazon products found - page may not have loaded properly")
        except Exception as e:
            self.logger.error(f"Error extracting Amazon products: {e}")
        
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
            price_selector = self.selectors.get('price', '.a-price .a-offscreen')
            try:
                price_element = container.find_element(By.CSS_SELECTOR, price_selector)
                price_text = price_element.text if price_element else None
                price = extract_price(price_text) if price_text else None
            except NoSuchElementException:
                price = None
            
            # Extract rating
            rating_selector = self.selectors.get('rating', '.a-icon-alt')
            try:
                rating_element = container.find_element(By.CSS_SELECTOR, rating_selector)
                rating_text = rating_element.get_attribute('alt') if rating_element else ''
                rating = extract_rating(rating_text) if rating_text else None
            except NoSuchElementException:
                rating = None
            
            # Extract image
            image_selector = self.selectors.get('image', '.s-image')
            try:
                image_element = container.find_element(By.CSS_SELECTOR, image_selector)
                image_url = image_element.get_attribute('src') if image_element else None
            except NoSuchElementException:
                image_url = None
            
            # Extract ASIN from URL
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
                'position_on_page': position,
                'scraper_type': 'selenium'
            }
            
            return self._clean_product_data(product)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract Amazon product: {e}")
            return None
    
    def _extract_ebay_products_selenium(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """Extract eBay products using Selenium."""
        # Similar implementation to Amazon but with eBay-specific selectors
        products = []
        
        try:
            container_selector = self.selectors.get('product_container', '.s-item')
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, container_selector)))
            
            containers = self.driver.find_elements(By.CSS_SELECTOR, container_selector)
            self.logger.info(f"Found {len(containers)} eBay product containers")
            
            for i, container in enumerate(containers, 1):
                try:
                    # Extract basic product info (simplified for brevity)
                    title_element = container.find_element(By.CSS_SELECTOR, '.s-item__title')
                    title = clean_text(title_element.text) if title_element else None
                    
                    if title and 'shop on ebay' not in title.lower():
                        product = {
                            'source': self.source,
                            'title': title,
                            'search_keyword': keyword,
                            'page_number': page,
                            'position_on_page': i,
                            'scraper_type': 'selenium'
                        }
                        products.append(product)
                        
                except Exception as e:
                    self.logger.debug(f"Failed to extract eBay product {i}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error extracting eBay products: {e}")
        
        return products
    
    def _extract_walmart_products_selenium(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """Extract Walmart products using Selenium."""
        # Similar implementation for Walmart
        return []
    
    def _extract_generic_products_selenium(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """Extract products from generic website using Selenium."""
        return []
    
    def close(self) -> None:
        """Close the browser and clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def cleanup(self) -> None:
        """Alias for close() method for compatibility."""
        self.close()

    def __del__(self):
        """Ensure browser is closed when object is destroyed."""
        if hasattr(self, 'driver'):
            self.close() 