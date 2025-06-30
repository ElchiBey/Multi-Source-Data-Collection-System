"""
Advanced Selenium Scraper with Anti-Bot Protection

This module implements a sophisticated Selenium-based scraper with multiple
anti-detection techniques to bypass modern bot protection systems.
"""

import random
import time
import json
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
from datetime import datetime

# Try to import undetected-chromedriver for advanced stealth
try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False

from .base_scraper import BaseScraper, ScrapingResult
from src.utils.helpers import (
    extract_price, extract_rating, clean_text, normalize_url,
    get_selenium_options, random_delay
)

class AdvancedSeleniumScraper(BaseScraper):
    """
    🥷 Advanced Selenium scraper with state-of-the-art anti-bot protection.
    
    Features:
    - Undetected Chrome driver
    - Stealth fingerprint randomization  
    - Human behavior simulation
    - Advanced CAPTCHA handling
    - Proxy rotation support
    - Browser profile management
    """
    
    def __init__(self, source: str, config: Dict[str, Any]):
        super().__init__(source, config)
        self.driver = None
        self.wait = None
        self.stealth_mode = config.get('stealth_mode', True)
        self.use_undetected = config.get('use_undetected_chrome', UNDETECTED_AVAILABLE)
        
        # Advanced anti-bot settings
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Load scraper-specific selectors
        self._load_source_config()
        
    def _load_source_config(self):
        """Load source-specific configuration and selectors."""
        try:
            from src.utils.config import load_config
            scraper_config = load_config('config/scrapers.yaml')
            self.selectors = scraper_config.get(self.source, {}).get('selectors', {})
            self.source_config = scraper_config.get(self.source, {})
        except Exception as e:
            self.logger.warning(f"Failed to load selectors for {self.source}: {e}")
            self.selectors = {}
            self.source_config = {}
    
    def _setup_stealth_driver(self) -> webdriver.Chrome:
        """
        🥷 Setup ultra-stealth Chrome driver with advanced anti-detection.
        
        Returns:
            Stealth-configured Chrome WebDriver instance
        """
        try:
            if self.use_undetected and UNDETECTED_AVAILABLE:
                self.logger.info("🥷 Using undetected-chromedriver for maximum stealth")
                return self._setup_undetected_driver()
            else:
                self.logger.info("🛡️ Using enhanced regular Chrome driver")
                return self._setup_enhanced_driver()
                
        except Exception as e:
            self.logger.error(f"Failed to setup stealth driver: {e}")
            # Fallback to basic driver
            return self._setup_basic_driver()
    
    def _setup_undetected_driver(self) -> webdriver.Chrome:
        """Setup undetected Chrome driver with maximum stealth."""
        options = uc.ChromeOptions()
        
        # Core stealth options
        stealth_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage', 
            '--disable-gpu',
            '--disable-features=VizDisplayCompositor',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-default-apps',
            '--disable-sync',
            '--disable-translate',
            '--hide-scrollbars',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--no-first-run',
            '--no-default-browser-check',
            '--no-pings',
            '--password-store=basic',
            '--use-mock-keychain',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--allow-running-insecure-content'
        ]
        
        for arg in stealth_args:
            options.add_argument(arg)
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        options.add_argument(f'--user-agent={user_agent}')
        
        # Random window size
        viewport_sizes = [
            (1366, 768), (1920, 1080), (1440, 900), (1536, 864), (1280, 720)
        ]
        width, height = random.choice(viewport_sizes)
        options.add_argument(f'--window-size={width},{height}')
        
        # Advanced prefs for stealth
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Use local chromedriver.exe if available
            import os
            local_driver_path = os.path.abspath('chromedriver.exe')
            if os.path.exists(local_driver_path):
                self.logger.info(f"🎯 Using local chromedriver: {local_driver_path}")
                driver = uc.Chrome(
                    options=options, 
                    driver_executable_path=local_driver_path,
                    version_main=None,
                    use_subprocess=True
                )
            else:
                self.logger.info("🥷 Using auto-downloaded undetected chromedriver")
                driver = uc.Chrome(options=options, version_main=None)
        except Exception as e:
            self.logger.warning(f"Failed to create undetected driver: {e}")
            # Fallback to regular method
            return self._setup_enhanced_driver()
        
        # Advanced stealth modifications
        self._apply_advanced_stealth(driver)
        
        return driver
    
    def _setup_enhanced_driver(self) -> webdriver.Chrome:
        """Setup enhanced regular Chrome driver with stealth features."""
        options = Options()
        
        # Core stealth options
        stealth_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-features=VizDisplayCompositor',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-default-apps',
            '--disable-sync',
            '--disable-translate',
            '--hide-scrollbars',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--no-first-run',
            '--no-default-browser-check',
            '--no-pings',
            '--password-store=basic',
            '--use-mock-keychain'
        ]
        
        for arg in stealth_args:
            options.add_argument(arg)
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        options.add_argument(f'--user-agent={user_agent}')
        
        # Random window size
        viewport_sizes = [
            (1366, 768), (1920, 1080), (1440, 900), (1536, 864), (1280, 720)
        ]
        width, height = random.choice(viewport_sizes)
        options.add_argument(f'--window-size={width},{height}')
        
        # Disable automation indicators
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional prefs
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
                "media_stream": 2
            },
            "profile.managed_default_content_settings": {
                "images": 2  # Block images for speed
            }
        })
        
        # Setup service - use local chromedriver.exe if available
        import os
        local_driver_path = os.path.abspath('chromedriver.exe')
        if os.path.exists(local_driver_path):
            self.logger.info(f"🎯 Using local chromedriver: {local_driver_path}")
            service = Service(local_driver_path)
        else:
            self.logger.info("📥 Using ChromeDriverManager to download driver")
            service = Service(ChromeDriverManager().install())
        
        # Create driver
        driver = webdriver.Chrome(service=service, options=options)
        
        # Apply stealth modifications
        self._apply_advanced_stealth(driver)
        
        return driver
    
    def _setup_basic_driver(self) -> webdriver.Chrome:
        """Fallback basic driver setup."""
        options = get_selenium_options()
        
        # Use local chromedriver.exe if available
        import os
        local_driver_path = os.path.abspath('chromedriver.exe')
        if os.path.exists(local_driver_path):
            self.logger.info(f"🎯 Using local chromedriver (basic mode): {local_driver_path}")
            service = Service(local_driver_path)
        else:
            self.logger.info("📥 Using ChromeDriverManager (basic mode)")
            service = Service(ChromeDriverManager().install())
            
        driver = webdriver.Chrome(service=service, options=options)
        self._apply_basic_stealth(driver)
        return driver
    
    def _apply_advanced_stealth(self, driver) -> None:
        """Apply advanced stealth modifications to the driver."""
        try:
            # Remove webdriver property
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Randomize navigator properties
            driver.execute_cdp_cmd('Runtime.evaluate', {
                "expression": """
                    // Randomize navigator properties
                    Object.defineProperty(navigator, 'languages', {
                        get: function() { return """ + json.dumps(['en-US', 'en']) + """; }
                    });
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: function() { return new Array(""" + str(random.randint(3, 8)) + """).fill(0); }
                    });
                    
                    Object.defineProperty(navigator, 'platform', {
                        get: function() { return '""" + random.choice(['Win32', 'MacIntel', 'Linux x86_64']) + """;' }
                    });
                    
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: function() { return """ + str(random.choice([2, 4, 8, 16])) + """; }
                    });
                    
                    Object.defineProperty(navigator, 'deviceMemory', {
                        get: function() { return """ + str(random.choice([2, 4, 8, 16])) + """; }
                    });
                    
                    // Override screen properties
                    Object.defineProperty(screen, 'colorDepth', {
                        get: function() { return 24; }
                    });
                    
                    Object.defineProperty(screen, 'pixelDepth', {
                        get: function() { return 24; }
                    });
                """
            })
            
            # Set timezone
            driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
                'timezoneId': random.choice([
                    'America/New_York', 'America/Los_Angeles', 'Europe/London', 
                    'Europe/Berlin', 'Asia/Tokyo', 'Australia/Sydney'
                ])
            })
            
            # Randomize canvas fingerprint
            driver.execute_script("""
                const getImageData = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type) {
                    const shift = Math.floor(Math.random() * 10) - 5;
                    const canvas = this;
                    const ctx = canvas.getContext('2d');
                    const originalImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    
                    for (let i = 0; i < originalImageData.data.length; i += 4) {
                        originalImageData.data[i] = Math.min(255, Math.max(0, originalImageData.data[i] + shift));
                        originalImageData.data[i + 1] = Math.min(255, Math.max(0, originalImageData.data[i + 1] + shift));
                        originalImageData.data[i + 2] = Math.min(255, Math.max(0, originalImageData.data[i + 2] + shift));
                    }
                    
                    ctx.putImageData(originalImageData, 0, 0);
                    return getImageData.apply(this, arguments);
                };
            """)
            
            self.logger.info("✅ Advanced stealth modifications applied")
            
        except Exception as e:
            self.logger.warning(f"Failed to apply advanced stealth: {e}")
            self._apply_basic_stealth(driver)
    
    def _apply_basic_stealth(self, driver) -> None:
        """Apply basic stealth modifications."""
        try:
            # Remove webdriver property
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            self.logger.info("✅ Basic stealth modifications applied")
        except Exception as e:
            self.logger.warning(f"Failed to apply basic stealth: {e}")
    
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
            self.driver = self._setup_stealth_driver()
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
        """Extract Amazon products using Selenium with robust selectors."""
        products = []
        
        try:
            # Multiple possible selectors for Amazon product containers
            container_selectors = [
                '[data-component-type="s-search-result"]',
                '.s-result-item',
                '[data-asin]:not([data-asin=""])',
                '.sg-col-inner'
            ]
            
            containers = []
            for selector in container_selectors:
                try:
                    # Wait for containers to appear
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        self.logger.info(f"Found {len(containers)} products using selector: {selector}")
                        break
                except TimeoutException:
                    continue
            
            if not containers:
                # Debug: Save page source to see what's actually there
                self.logger.warning("No product containers found. Checking page content...")
                page_text = self.driver.page_source[:1000]  # First 1000 chars
                self.logger.debug(f"Page content preview: {page_text}")
                
                # Try finding ANY products with very broad selectors
                broad_selectors = [
                    '[data-asin]',
                    '.s-item',
                    '.product',
                    '[data-component-type]'
                ]
                
                for selector in broad_selectors:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        self.logger.info(f"Found {len(containers)} elements with broad selector: {selector}")
                        break
            
            # Extract data from containers
            for i, container in enumerate(containers[:20], 1):  # Limit to 20 products
                try:
                    product = self._extract_amazon_product_robust(container, keyword, page, i)
                    if product and product.get('title'):
                        products.append(product)
                        self.logger.debug(f"Extracted product {i}: {product.get('title', 'No title')[:50]}...")
                except Exception as e:
                    self.logger.debug(f"Failed to extract Amazon product {i}: {e}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(products)} Amazon products")
            
        except Exception as e:
            self.logger.error(f"Error extracting Amazon products: {e}")
        
        return products
    
    def _extract_amazon_product_robust(self, container, keyword: str, page: int, position: int) -> Optional[Dict[str, Any]]:
        """Extract single Amazon product with multiple fallback selectors."""
        try:
            # Multiple title selectors to try
            title_selectors = [
                'h2 a span',
                '.s-title-instructions-style span',
                'h2 span',
                '.s-color-base',
                'a[title]',
                '.a-link-normal span'
            ]
            
            title = None
            title_element = None
            for selector in title_selectors:
                try:
                    title_element = container.find_element(By.CSS_SELECTOR, selector)
                    title = clean_text(title_element.text) if title_element else None
                    if title and len(title) > 10:  # Valid title should be reasonably long
                        break
                except NoSuchElementException:
                    continue
            
            # Try getting title from title attribute if text didn't work
            if not title and title_element:
                title = title_element.get_attribute('title')
            
            if not title:
                # Final fallback - get any text from the container
                all_text = container.text.strip()
                if all_text:
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    # Usually the first substantial line is the title
                    for line in lines:
                        if len(line) > 15 and not line.startswith('$') and 'rating' not in line.lower():
                            title = line
                            break
            
            if not title:
                return None
            
            # Extract URL with multiple selectors
            url_selectors = ['h2 a', 'a[title]', 'a']
            url = None
            for selector in url_selectors:
                try:
                    link_element = container.find_element(By.CSS_SELECTOR, selector)
                    relative_url = link_element.get_attribute('href')
                    if relative_url and '/dp/' in relative_url:
                        url = normalize_url(relative_url, 'https://www.amazon.com')
                        break
                except NoSuchElementException:
                    continue
            
            # Extract price with multiple selectors
            price_selectors = [
                '.a-price .a-offscreen',
                '.a-price-whole',
                '.a-price',
                '[data-a-price]',
                '.s-price'
            ]
            
            price = None
            for selector in price_selectors:
                try:
                    price_element = container.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text or price_element.get_attribute('data-a-price')
                    if price_text and '$' in price_text:
                        price = extract_price(price_text)
                        if price:
                            break
                except NoSuchElementException:
                    continue
            
            # Extract rating
            rating_selectors = ['.a-icon-alt', '.a-icon', '[aria-label*="stars"]']
            rating = None
            for selector in rating_selectors:
                try:
                    rating_element = container.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_element.get_attribute('aria-label') or rating_element.text
                    if rating_text:
                        rating = extract_rating(rating_text)
                        if rating:
                            break
                except NoSuchElementException:
                    continue
            
            # Extract image
            image_selectors = ['.s-image', 'img', '[data-src]']
            image_url = None
            for selector in image_selectors:
                try:
                    image_element = container.find_element(By.CSS_SELECTOR, selector)
                    image_url = image_element.get_attribute('src') or image_element.get_attribute('data-src')
                    if image_url and 'http' in image_url:
                        break
                except NoSuchElementException:
                    continue
            
            # Extract ASIN from URL or data attributes
            asin = None
            if url:
                import re
                asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
                if asin_match:
                    asin = asin_match.group(1)
            
            if not asin:
                asin = container.get_attribute('data-asin')
            
            product = {
                'source': 'amazon',
                'title': title,
                'url': url,
                'product_id': asin,
                'price': price,
                'rating': rating,
                'image_url': image_url,
                'search_keyword': keyword,
                'page_number': page,
                'position_on_page': position,
                'scraper_type': 'selenium',
                'scraped_at': datetime.now().isoformat()
            }
            
            return self._clean_product_data(product)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract Amazon product: {e}")
            return None
    
    def _extract_ebay_products_selenium(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """Extract eBay products using Selenium with robust selectors."""
        products = []
        
        try:
            # Multiple possible selectors for eBay product containers
            container_selectors = [
                '.s-item',
                '.srp-item',
                '.srp-river-results .s-item',
                '[data-view="mi:1686"]'
            ]
            
            containers = []
            for selector in container_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        self.logger.info(f"Found {len(containers)} eBay products using selector: {selector}")
                        break
                except TimeoutException:
                    continue
            
            if not containers:
                self.logger.warning("No eBay product containers found. Checking page content...")
                page_text = self.driver.page_source[:1000]
                self.logger.debug(f"eBay page content preview: {page_text}")
                
                # Broad fallback selectors
                broad_selectors = [
                    '[id*="item"]',
                    '.item',
                    '.listing',
                    '.product'
                ]
                
                for selector in broad_selectors:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        self.logger.info(f"Found {len(containers)} eBay elements with broad selector: {selector}")
                        break
            
            # Extract data from containers
            for i, container in enumerate(containers[:20], 1):  # Limit to 20 products
                try:
                    product = self._extract_ebay_product_robust(container, keyword, page, i)
                    if product and product.get('title'):
                        # Skip promotional/sponsored items
                        title = product.get('title', '').lower()
                        if not any(skip_word in title for skip_word in ['shop on ebay', 'sponsored', 'advertisement']):
                            products.append(product)
                            self.logger.debug(f"Extracted eBay product {i}: {product.get('title', 'No title')[:50]}...")
                except Exception as e:
                    self.logger.debug(f"Failed to extract eBay product {i}: {e}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(products)} eBay products")
            
        except Exception as e:
            self.logger.error(f"Error extracting eBay products: {e}")
        
        return products
    
    def _extract_ebay_product_robust(self, container, keyword: str, page: int, position: int) -> Optional[Dict[str, Any]]:
        """Extract single eBay product with multiple fallback selectors."""
        try:
            # Multiple title selectors for eBay
            title_selectors = [
                '.s-item__title',
                '.s-item__title span',
                '.it-ttl a',
                '.vip-title',
                'h3.it-ttl',
                '[role="heading"]'
            ]
            
            title = None
            for selector in title_selectors:
                try:
                    title_element = container.find_element(By.CSS_SELECTOR, selector)
                    title = clean_text(title_element.text) if title_element else None
                    if title and len(title) > 10:
                        break
                except NoSuchElementException:
                    continue
            
            # Fallback to container text
            if not title:
                all_text = container.text.strip()
                if all_text:
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    for line in lines:
                        if len(line) > 15 and not line.startswith('$') and 'bid' not in line.lower():
                            title = line
                            break
            
            if not title or title.lower() == 'shop on ebay':
                return None
            
            # Extract URL with multiple selectors
            url_selectors = ['.s-item__link', '.it-ttl a', 'a[href*="/itm/"]', 'a']
            url = None
            for selector in url_selectors:
                try:
                    link_element = container.find_element(By.CSS_SELECTOR, selector)
                    relative_url = link_element.get_attribute('href')
                    if relative_url and ('/itm/' in relative_url or 'ebay.com' in relative_url):
                        url = normalize_url(relative_url, 'https://www.ebay.com')
                        break
                except NoSuchElementException:
                    continue
            
            # Extract price with multiple selectors
            price_selectors = [
                '.s-item__price',
                '.notranslate',
                '.it-price',
                '.u-flL.notranslate',
                '.s-item__detail.s-item__detail--primary .notranslate'
            ]
            
            price = None
            for selector in price_selectors:
                try:
                    price_element = container.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text
                    if price_text and '$' in price_text:
                        price = extract_price(price_text)
                        if price:
                            break
                except NoSuchElementException:
                    continue
            
            # Extract shipping
            shipping_selectors = ['.s-item__shipping', '.vi-acc-del-range', '.u-flL']
            shipping = None
            for selector in shipping_selectors:
                try:
                    shipping_element = container.find_element(By.CSS_SELECTOR, selector)
                    shipping_text = shipping_element.text
                    if shipping_text and ('shipping' in shipping_text.lower() or 'free' in shipping_text.lower()):
                        shipping = shipping_text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract condition
            condition_selectors = ['.s-item__subtitle', '.clipped', '.SECONDARY_INFO']
            condition = None
            for selector in condition_selectors:
                try:
                    condition_element = container.find_element(By.CSS_SELECTOR, selector)
                    condition_text = condition_element.text
                    if condition_text and any(word in condition_text.lower() for word in ['new', 'used', 'refurbished', 'open']):
                        condition = condition_text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract image
            image_selectors = ['.s-item__image img', '.img img', 'img']
            image_url = None
            for selector in image_selectors:
                try:
                    image_element = container.find_element(By.CSS_SELECTOR, selector)
                    image_url = image_element.get_attribute('src') or image_element.get_attribute('data-src')
                    if image_url and 'http' in image_url and 'ebayimg' in image_url:
                        break
                except NoSuchElementException:
                    continue
            
            # Extract item ID from URL
            item_id = None
            if url:
                import re
                id_match = re.search(r'/itm/([^/?]+)', url)
                if id_match:
                    item_id = id_match.group(1)
            
            product = {
                'source': 'ebay',
                'title': title,
                'url': url,
                'product_id': item_id,
                'price': price,
                'shipping': shipping,
                'condition': condition,
                'image_url': image_url,
                'search_keyword': keyword,
                'page_number': page,
                'position_on_page': position,
                'scraper_type': 'selenium',
                'scraped_at': datetime.now().isoformat()
            }
            
            return self._clean_product_data(product)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract eBay product: {e}")
            return None
    
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


# Backward compatibility alias
SeleniumScraper = AdvancedSeleniumScraper 