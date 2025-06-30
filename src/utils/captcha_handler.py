"""
Advanced CAPTCHA Detection and Handling System

This module provides comprehensive CAPTCHA detection and handling strategies
for web scraping operations. It includes multiple detection methods,
handling strategies, and anti-bot bypass techniques.
"""

import time
import random
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
import requests

logger = logging.getLogger(__name__)

@dataclass
class CaptchaDetectionResult:
    """Result of CAPTCHA detection."""
    detected: bool
    captcha_type: str
    confidence: float
    location: str
    elements_found: List[str]
    suggested_strategy: str

@dataclass
class CaptchaHandlingResult:
    """Result of CAPTCHA handling attempt."""
    success: bool
    strategy_used: str
    time_taken: float
    attempts_made: int
    final_status: str
    recommendations: List[str]

class AdvancedCaptchaDetector:
    """Advanced CAPTCHA detection with multiple detection methods."""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.logger = logging.getLogger(f"{__name__}.CaptchaDetector")
        
        # CAPTCHA indicators database
        self.text_indicators = [
            "captcha", "recaptcha", "hcaptcha", "cloudflare",
            "verify you are human", "i'm not a robot", "prove you're human",
            "security check", "suspicious activity", "unusual traffic",
            "please verify", "verify your identity", "bot detection",
            "are you a robot", "human verification", "challenge",
            "access denied", "blocked", "forbidden", "rate limit"
        ]
        
        self.element_selectors = [
            # reCAPTCHA
            "iframe[src*='recaptcha']",
            ".g-recaptcha",
            "#g-recaptcha",
            "[class*='recaptcha']",
            
            # hCaptcha
            "iframe[src*='hcaptcha']",
            ".h-captcha",
            "#h-captcha",
            "[class*='hcaptcha']",
            
            # Generic CAPTCHA
            "div[class*='captcha']",
            "div[id*='captcha']",
            "#captcha",
            ".captcha",
            
            # Cloudflare
            ".cf-browser-verification",
            "#cf-wrapper",
            "[class*='cloudflare']",
            
            # Custom challenge elements
            "[class*='challenge']",
            "[id*='challenge']",
            "[class*='verification']",
            "[id*='verification']",
            
            # Bot detection
            "[class*='bot-protection']",
            "[class*='anti-bot']",
            "[class*='security-check']"
        ]
        
        self.url_patterns = [
            "captcha", "recaptcha", "hcaptcha", "cloudflare",
            "challenge", "verify", "security", "protection"
        ]
    
    def detect_captcha(self) -> CaptchaDetectionResult:
        """
        Perform comprehensive CAPTCHA detection.
        
        Returns:
            CaptchaDetectionResult with detection details
        """
        detection_results = []
        
        # Method 1: Text-based detection
        text_result = self._detect_by_text()
        detection_results.append(text_result)
        
        # Method 2: Element-based detection
        element_result = self._detect_by_elements()
        detection_results.append(element_result)
        
        # Method 3: URL-based detection
        url_result = self._detect_by_url()
        detection_results.append(url_result)
        
        # Method 4: Behavioral detection
        behavior_result = self._detect_by_behavior()
        detection_results.append(behavior_result)
        
        # Method 5: Network-based detection
        network_result = self._detect_by_network_patterns()
        detection_results.append(network_result)
        
        # Combine results
        return self._combine_detection_results(detection_results)
    
    def _detect_by_text(self) -> Dict[str, Any]:
        """Detect CAPTCHA by analyzing page text content."""
        try:
            page_source = self.driver.page_source.lower()
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            detected_indicators = []
            confidence_score = 0
            
            for indicator in self.text_indicators:
                if indicator in page_source or indicator in page_text:
                    detected_indicators.append(indicator)
                    # Weight different indicators differently
                    if indicator in ["captcha", "recaptcha", "hcaptcha"]:
                        confidence_score += 0.3
                    elif indicator in ["verify you are human", "i'm not a robot"]:
                        confidence_score += 0.25
                    else:
                        confidence_score += 0.1
            
            return {
                "method": "text",
                "detected": len(detected_indicators) > 0,
                "confidence": min(confidence_score, 1.0),
                "indicators": detected_indicators,
                "captcha_type": self._determine_captcha_type_from_text(detected_indicators)
            }
            
        except Exception as e:
            self.logger.debug(f"Text detection error: {e}")
            return {"method": "text", "detected": False, "confidence": 0, "indicators": [], "captcha_type": "unknown"}
    
    def _detect_by_elements(self) -> Dict[str, Any]:
        """Detect CAPTCHA by analyzing DOM elements."""
        try:
            found_elements = []
            confidence_score = 0
            
            for selector in self.element_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Check if elements are visible
                        visible_elements = [elem for elem in elements if elem.is_displayed()]
                        if visible_elements:
                            found_elements.append(selector)
                            # Higher confidence for specific CAPTCHA selectors
                            if any(term in selector for term in ["recaptcha", "hcaptcha", "cloudflare"]):
                                confidence_score += 0.4
                            else:
                                confidence_score += 0.2
                except Exception:
                    continue
            
            return {
                "method": "elements",
                "detected": len(found_elements) > 0,
                "confidence": min(confidence_score, 1.0),
                "indicators": found_elements,
                "captcha_type": self._determine_captcha_type_from_elements(found_elements)
            }
            
        except Exception as e:
            self.logger.debug(f"Element detection error: {e}")
            return {"method": "elements", "detected": False, "confidence": 0, "indicators": [], "captcha_type": "unknown"}
    
    def _detect_by_url(self) -> Dict[str, Any]:
        """Detect CAPTCHA by analyzing current URL."""
        try:
            current_url = self.driver.current_url.lower()
            detected_patterns = []
            confidence_score = 0
            
            for pattern in self.url_patterns:
                if pattern in current_url:
                    detected_patterns.append(pattern)
                    if pattern in ["captcha", "recaptcha", "cloudflare"]:
                        confidence_score += 0.5
                    else:
                        confidence_score += 0.2
            
            return {
                "method": "url",
                "detected": len(detected_patterns) > 0,
                "confidence": min(confidence_score, 1.0),
                "indicators": detected_patterns,
                "captcha_type": self._determine_captcha_type_from_url(detected_patterns)
            }
            
        except Exception as e:
            self.logger.debug(f"URL detection error: {e}")
            return {"method": "url", "detected": False, "confidence": 0, "indicators": [], "captcha_type": "unknown"}
    
    def _detect_by_behavior(self) -> Dict[str, Any]:
        """Detect CAPTCHA by analyzing page behavior."""
        try:
            indicators = []
            confidence_score = 0
            
            # Check for typical CAPTCHA page behaviors
            
            # 1. Page title analysis
            title = self.driver.title.lower()
            if any(term in title for term in ["captcha", "verify", "security", "challenge"]):
                indicators.append("suspicious_title")
                confidence_score += 0.3
            
            # 2. Check for redirects to challenge pages
            if len(self.driver.window_handles) > 1:
                indicators.append("multiple_windows")
                confidence_score += 0.2
            
            # 3. Check for forms with specific patterns
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                form_html = form.get_attribute("innerHTML").lower()
                if any(term in form_html for term in ["captcha", "verify", "challenge"]):
                    indicators.append("captcha_form")
                    confidence_score += 0.4
                    break
            
            # 4. Check for iframes (common in CAPTCHAs)
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            captcha_iframes = []
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if any(term in src.lower() for term in ["captcha", "recaptcha", "hcaptcha"]):
                    captcha_iframes.append(src)
                    confidence_score += 0.5
            
            if captcha_iframes:
                indicators.append("captcha_iframes")
            
            return {
                "method": "behavior",
                "detected": len(indicators) > 0,
                "confidence": min(confidence_score, 1.0),
                "indicators": indicators,
                "captcha_type": "behavioral_analysis"
            }
            
        except Exception as e:
            self.logger.debug(f"Behavior detection error: {e}")
            return {"method": "behavior", "detected": False, "confidence": 0, "indicators": [], "captcha_type": "unknown"}
    
    def _detect_by_network_patterns(self) -> Dict[str, Any]:
        """Detect CAPTCHA by analyzing network response patterns."""
        try:
            indicators = []
            confidence_score = 0
            
            # Check response status and headers
            # This would require additional selenium extensions or CDP
            
            # For now, use basic page analysis
            page_source = self.driver.page_source
            
            # Look for CAPTCHA service CDN URLs
            captcha_services = [
                "www.google.com/recaptcha",
                "hcaptcha.com",
                "cloudflare.com",
                "funcaptcha.com"
            ]
            
            for service in captcha_services:
                if service in page_source:
                    indicators.append(f"cdn_{service}")
                    confidence_score += 0.3
            
            return {
                "method": "network",
                "detected": len(indicators) > 0,
                "confidence": min(confidence_score, 1.0),
                "indicators": indicators,
                "captcha_type": "network_analysis"
            }
            
        except Exception as e:
            self.logger.debug(f"Network detection error: {e}")
            return {"method": "network", "detected": False, "confidence": 0, "indicators": [], "captcha_type": "unknown"}
    
    def _combine_detection_results(self, results: List[Dict[str, Any]]) -> CaptchaDetectionResult:
        """Combine multiple detection results into final decision."""
        total_confidence = sum(r["confidence"] for r in results if r["detected"])
        detected_methods = [r["method"] for r in results if r["detected"]]
        all_indicators = [ind for r in results for ind in r["indicators"]]
        
        # Determine overall detection
        detected = total_confidence > 0.3  # Threshold for detection
        
        # Determine CAPTCHA type
        captcha_types = [r["captcha_type"] for r in results if r["captcha_type"] != "unknown"]
        captcha_type = max(set(captcha_types), key=captcha_types.count) if captcha_types else "unknown"
        
        # Suggest handling strategy
        strategy = self._suggest_handling_strategy(captcha_type, total_confidence, detected_methods)
        
        return CaptchaDetectionResult(
            detected=detected,
            captcha_type=captcha_type,
            confidence=min(total_confidence, 1.0),
            location=",".join(detected_methods),
            elements_found=all_indicators,
            suggested_strategy=strategy
        )
    
    def _determine_captcha_type_from_text(self, indicators: List[str]) -> str:
        """Determine CAPTCHA type from text indicators."""
        if any("recaptcha" in ind for ind in indicators):
            return "recaptcha"
        elif any("hcaptcha" in ind for ind in indicators):
            return "hcaptcha"
        elif any("cloudflare" in ind for ind in indicators):
            return "cloudflare"
        elif any("captcha" in ind for ind in indicators):
            return "generic_captcha"
        else:
            return "unknown"
    
    def _determine_captcha_type_from_elements(self, selectors: List[str]) -> str:
        """Determine CAPTCHA type from DOM elements."""
        if any("recaptcha" in sel for sel in selectors):
            return "recaptcha"
        elif any("hcaptcha" in sel for sel in selectors):
            return "hcaptcha"
        elif any("cloudflare" in sel for sel in selectors):
            return "cloudflare"
        else:
            return "generic_captcha"
    
    def _determine_captcha_type_from_url(self, patterns: List[str]) -> str:
        """Determine CAPTCHA type from URL patterns."""
        if "recaptcha" in patterns:
            return "recaptcha"
        elif "hcaptcha" in patterns:
            return "hcaptcha"
        elif "cloudflare" in patterns:
            return "cloudflare"
        else:
            return "url_based_challenge"
    
    def _suggest_handling_strategy(self, captcha_type: str, confidence: float, methods: List[str]) -> str:
        """Suggest the best handling strategy based on detection results."""
        if confidence > 0.8:
            return "aggressive_bypass"
        elif confidence > 0.5:
            if captcha_type == "cloudflare":
                return "cloudflare_bypass"
            elif captcha_type in ["recaptcha", "hcaptcha"]:
                return "advanced_stealth"
            else:
                return "standard_bypass"
        else:
            return "gentle_retry"

class AdvancedCaptchaHandler:
    """Advanced CAPTCHA handling with multiple strategies."""
    
    def __init__(self, driver: webdriver.Chrome, config: Dict[str, Any]):
        self.driver = driver
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CaptchaHandler")
        self.detector = AdvancedCaptchaDetector(driver)
        
        # User agent pool for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
    
    def handle_captcha(self, detection_result: CaptchaDetectionResult) -> CaptchaHandlingResult:
        """
        Handle detected CAPTCHA using appropriate strategy.
        
        Args:
            detection_result: Result from CAPTCHA detection
            
        Returns:
            CaptchaHandlingResult with handling outcome
        """
        start_time = time.time()
        attempts = 0
        max_attempts = 3
        
        strategy = detection_result.suggested_strategy
        self.logger.info(f"🛡️ Handling CAPTCHA using strategy: {strategy}")
        
        while attempts < max_attempts:
            attempts += 1
            self.logger.info(f"🔄 CAPTCHA handling attempt {attempts}/{max_attempts}")
            
            try:
                if strategy == "aggressive_bypass":
                    success = self._aggressive_bypass_strategy()
                elif strategy == "cloudflare_bypass":
                    success = self._cloudflare_bypass_strategy()
                elif strategy == "advanced_stealth":
                    success = self._advanced_stealth_strategy()
                elif strategy == "standard_bypass":
                    success = self._standard_bypass_strategy()
                else:  # gentle_retry
                    success = self._gentle_retry_strategy()
                
                if success:
                    break
                    
                # Wait before retry
                time.sleep(random.uniform(5, 15))
                
            except Exception as e:
                self.logger.error(f"❌ CAPTCHA handling error: {e}")
                
        # Final verification
        final_detection = self.detector.detect_captcha()
        final_success = not final_detection.detected
        
        time_taken = time.time() - start_time
        
        return CaptchaHandlingResult(
            success=final_success,
            strategy_used=strategy,
            time_taken=time_taken,
            attempts_made=attempts,
            final_status="resolved" if final_success else "persistent",
            recommendations=self._generate_recommendations(final_success, strategy, attempts)
        )
    
    def _aggressive_bypass_strategy(self) -> bool:
        """Aggressive bypass strategy for high-confidence CAPTCHA detection."""
        self.logger.info("🚀 Executing aggressive bypass strategy")
        
        strategies = [
            self._rotate_user_agent,
            self._clear_cookies_and_refresh,
            self._change_viewport_size,
            self._simulate_mouse_movements,
            self._wait_and_retry_with_delays
        ]
        
        for strategy_func in strategies:
            try:
                if strategy_func():
                    return True
            except Exception as e:
                self.logger.debug(f"Strategy failed: {e}")
                
        return False
    
    def _cloudflare_bypass_strategy(self) -> bool:
        """Specialized strategy for Cloudflare challenges."""
        self.logger.info("☁️ Executing Cloudflare bypass strategy")
        
        try:
            # Wait for Cloudflare challenge to complete
            self.logger.info("⏳ Waiting for Cloudflare challenge...")
            
            # Look for Cloudflare challenge completion
            wait = WebDriverWait(self.driver, 30)
            
            # Wait for challenge to disappear
            try:
                wait.until_not(EC.presence_of_element_located((By.CLASS_NAME, "cf-browser-verification")))
                self.logger.info("✅ Cloudflare challenge completed")
                return True
            except TimeoutException:
                self.logger.warning("⏰ Cloudflare challenge timeout")
                
            # Fallback: refresh and wait
            self.driver.refresh()
            time.sleep(random.uniform(10, 20))
            
            # Check if challenge is gone
            detection = self.detector.detect_captcha()
            return not detection.detected
            
        except Exception as e:
            self.logger.error(f"❌ Cloudflare bypass failed: {e}")
            return False
    
    def _advanced_stealth_strategy(self) -> bool:
        """Advanced stealth strategy for sophisticated CAPTCHAs."""
        self.logger.info("🥷 Executing advanced stealth strategy")
        
        try:
            # Step 1: Human-like mouse movements
            self._simulate_human_mouse_patterns()
            
            # Step 2: Random scroll behavior
            self._human_like_scrolling()
            
            # Step 3: Wait with random intervals
            wait_time = random.uniform(15, 45)
            self.logger.info(f"⏳ Human-like waiting: {wait_time:.1f}s")
            time.sleep(wait_time)
            
            # Step 4: Gentle page refresh
            self.driver.refresh()
            time.sleep(random.uniform(3, 8))
            
            # Step 5: Check if resolved
            detection = self.detector.detect_captcha()
            if not detection.detected:
                return True
                
            # Step 6: Try changing fingerprint
            self._change_browser_fingerprint()
            
            return not self.detector.detect_captcha().detected
            
        except Exception as e:
            self.logger.error(f"❌ Advanced stealth failed: {e}")
            return False
    
    def _standard_bypass_strategy(self) -> bool:
        """Standard bypass strategy for common CAPTCHAs."""
        self.logger.info("🔧 Executing standard bypass strategy")
        
        try:
            # Simple refresh and wait
            self.driver.refresh()
            time.sleep(random.uniform(5, 15))
            
            # Check if resolved
            if not self.detector.detect_captcha().detected:
                return True
                
            # Try user agent rotation
            self._rotate_user_agent()
            self.driver.refresh()
            time.sleep(random.uniform(5, 10))
            
            return not self.detector.detect_captcha().detected
            
        except Exception as e:
            self.logger.error(f"❌ Standard bypass failed: {e}")
            return False
    
    def _gentle_retry_strategy(self) -> bool:
        """Gentle retry strategy for low-confidence detections."""
        self.logger.info("🕊️ Executing gentle retry strategy")
        
        try:
            # Simple wait and check
            time.sleep(random.uniform(3, 8))
            
            return not self.detector.detect_captcha().detected
            
        except Exception as e:
            self.logger.error(f"❌ Gentle retry failed: {e}")
            return False
    
    def _rotate_user_agent(self) -> bool:
        """Rotate user agent to bypass detection."""
        try:
            new_ua = random.choice(self.user_agents)
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": new_ua})
            self.logger.info(f"🔄 Rotated user agent")
            return True
        except Exception as e:
            self.logger.debug(f"User agent rotation failed: {e}")
            return False
    
    def _clear_cookies_and_refresh(self) -> bool:
        """Clear cookies and refresh page."""
        try:
            self.driver.delete_all_cookies()
            self.driver.refresh()
            time.sleep(random.uniform(3, 8))
            self.logger.info("🍪 Cleared cookies and refreshed")
            return True
        except Exception as e:
            self.logger.debug(f"Cookie clearing failed: {e}")
            return False
    
    def _change_viewport_size(self) -> bool:
        """Change browser viewport size."""
        try:
            sizes = [(1920, 1080), (1366, 768), (1440, 900), (1280, 720)]
            width, height = random.choice(sizes)
            self.driver.set_window_size(width, height)
            self.logger.info(f"📐 Changed viewport to {width}x{height}")
            return True
        except Exception as e:
            self.logger.debug(f"Viewport change failed: {e}")
            return False
    
    def _simulate_mouse_movements(self) -> bool:
        """Simulate human-like mouse movements."""
        try:
            actions = ActionChains(self.driver)
            
            # Random mouse movements
            for _ in range(random.randint(3, 7)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                actions.move_by_offset(x, y)
                actions.pause(random.uniform(0.5, 2.0))
            
            actions.perform()
            self.logger.info("🖱️ Simulated mouse movements")
            return True
        except Exception as e:
            self.logger.debug(f"Mouse simulation failed: {e}")
            return False
    
    def _simulate_human_mouse_patterns(self) -> bool:
        """Simulate sophisticated human mouse patterns."""
        try:
            actions = ActionChains(self.driver)
            
            # Curved movements
            for _ in range(random.randint(2, 5)):
                # Create a curved path
                start_x, start_y = random.randint(50, 200), random.randint(50, 200)
                end_x, end_y = random.randint(400, 800), random.randint(300, 600)
                
                # Generate curve points
                steps = random.randint(5, 10)
                for i in range(steps):
                    t = i / steps
                    # Bezier curve simulation
                    mid_x = start_x + (end_x - start_x) * t + random.randint(-50, 50)
                    mid_y = start_y + (end_y - start_y) * t + random.randint(-50, 50)
                    
                    actions.move_by_offset(mid_x - (start_x if i == 0 else 0), 
                                         mid_y - (start_y if i == 0 else 0))
                    actions.pause(random.uniform(0.1, 0.5))
            
            actions.perform()
            return True
        except Exception as e:
            self.logger.debug(f"Human mouse patterns failed: {e}")
            return False
    
    def _human_like_scrolling(self) -> bool:
        """Perform human-like scrolling behavior."""
        try:
            # Random scroll amounts and directions
            for _ in range(random.randint(2, 5)):
                scroll_amount = random.randint(100, 500)
                direction = random.choice([1, -1])
                
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount * direction});")
                time.sleep(random.uniform(0.5, 2.0))
            
            # Return to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            return True
        except Exception as e:
            self.logger.debug(f"Human scrolling failed: {e}")
            return False
    
    def _wait_and_retry_with_delays(self) -> bool:
        """Wait with random delays and retry."""
        try:
            # Progressive waiting
            delays = [5, 10, 15, 20]
            for delay in delays:
                time.sleep(random.uniform(delay * 0.8, delay * 1.2))
                
                if not self.detector.detect_captcha().detected:
                    return True
                    
            return False
        except Exception as e:
            self.logger.debug(f"Delayed retry failed: {e}")
            return False
    
    def _change_browser_fingerprint(self) -> bool:
        """Change browser fingerprint characteristics."""
        try:
            # Change language
            languages = ["en-US,en", "en-GB,en", "es-ES,es", "fr-FR,fr"]
            lang = random.choice(languages)
            
            self.driver.execute_cdp_cmd('Emulation.setLocaleOverride', {'locale': lang.split(',')[0]})
            
            # Change timezone
            timezones = ["America/New_York", "Europe/London", "Europe/Paris", "America/Los_Angeles"]
            timezone = random.choice(timezones)
            
            self.driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {'timezoneId': timezone})
            
            self.logger.info("🛡️ Changed browser fingerprint")
            return True
        except Exception as e:
            self.logger.debug(f"Fingerprint change failed: {e}")
            return False
    
    def _generate_recommendations(self, success: bool, strategy: str, attempts: int) -> List[str]:
        """Generate recommendations based on handling results."""
        recommendations = []
        
        if not success:
            recommendations.append("Consider using proxy rotation")
            recommendations.append("Try increasing delays between requests")
            recommendations.append("Use residential proxies instead of datacenter IPs")
            
            if attempts >= 3:
                recommendations.append("Consider manual CAPTCHA solving service")
                recommendations.append("Implement session management")
        
        if strategy == "cloudflare_bypass" and not success:
            recommendations.append("Use undetected-chromedriver with latest version")
            recommendations.append("Implement browser profile rotation")
        
        if success:
            recommendations.append(f"Strategy '{strategy}' was effective")
            recommendations.append("Continue with current approach")
        
        return recommendations

# Integration functions for existing scrapers

def integrate_captcha_handler(scraper_instance):
    """
    Integrate advanced CAPTCHA handler into existing scraper.
    
    Args:
        scraper_instance: Existing scraper instance with driver
    """
    if hasattr(scraper_instance, 'driver') and scraper_instance.driver:
        scraper_instance.captcha_handler = AdvancedCaptchaHandler(
            scraper_instance.driver, 
            scraper_instance.config
        )
        
        # Replace existing CAPTCHA methods
        scraper_instance._check_for_captcha = scraper_instance.captcha_handler.detector.detect_captcha
        scraper_instance._handle_captcha = lambda: scraper_instance.captcha_handler.handle_captcha(
            scraper_instance.captcha_handler.detector.detect_captcha()
        ).success

def create_captcha_aware_driver(config: Dict[str, Any]) -> webdriver.Chrome:
    """
    Create a Chrome driver with advanced anti-detection capabilities.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured Chrome driver
    """
    options = uc.ChromeOptions()
    
    # Advanced anti-detection options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")  # Can be removed if JS is needed
    
    # Create driver
    driver = uc.Chrome(options=options)
    
    # Advanced stealth modifications
    stealth_script = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    window.chrome = {runtime: {}};
    """
    
    driver.execute_script(stealth_script)
    
    return driver 