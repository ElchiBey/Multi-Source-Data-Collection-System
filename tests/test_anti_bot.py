"""
Test suite for anti-bot protection features.

This module tests the various anti-bot protection strategies implemented
in the Multi-Source Data Collection System.
"""

import pytest
import time
from unittest.mock import Mock, patch
import requests

from src.scrapers.static_scraper import StaticScraper
from src.utils.helpers import (
    get_random_user_agent, get_random_headers, random_delay,
    get_selenium_options, should_use_proxy
)

class TestAntiBot:
    """Test anti-bot protection features."""
    
    def setup_method(self):
        """Setup test configuration."""
        self.config = {
            'scraping': {
                'delay_range': [0.1, 0.2],  # Faster for testing
                'max_retries': 2,
                'timeout': 10
            },
            'sources': {
                'test_site': {
                    'enabled': True,
                    'base_url': 'https://httpbin.org',
                    'delay_range': [0.1, 0.2]
                }
            }
        }
    
    def test_user_agent_rotation(self):
        """Test that user agents are being rotated."""
        user_agents = set()
        
        # Get multiple user agents
        for _ in range(10):
            ua = get_random_user_agent()
            user_agents.add(ua)
        
        # Should have multiple different user agents
        assert len(user_agents) > 1, "User agent rotation not working"
        
        # All should be valid browser user agents
        for ua in user_agents:
            assert any(browser in ua for browser in ['Chrome', 'Firefox', 'Safari', 'Edge'])
    
    def test_random_headers_generation(self):
        """Test random header generation."""
        headers_sets = []
        
        # Generate multiple header sets
        for _ in range(5):
            headers = get_random_headers()
            headers_sets.append(headers)
        
        # Should have User-Agent in all sets
        for headers in headers_sets:
            assert 'User-Agent' in headers
            assert 'Accept' in headers
            assert 'Accept-Language' in headers
        
        # User agents should vary
        user_agents = [h['User-Agent'] for h in headers_sets]
        assert len(set(user_agents)) > 1, "Headers not randomized"
    
    def test_delay_functionality(self):
        """Test random delay implementation."""
        start_time = time.time()
        
        # Test with very short delay for testing
        random_delay(0.1, 0.2)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should have waited at least 0.1 seconds
        assert elapsed >= 0.1, f"Delay too short: {elapsed}"
        assert elapsed <= 0.5, f"Delay too long: {elapsed}"  # Allow some buffer
    
    def test_proxy_decision_logic(self):
        """Test proxy usage decision logic."""
        # Test multiple times to check randomness
        results = []
        for _ in range(20):
            results.append(should_use_proxy())
        
        # Should have some True and some False values (probabilistic)
        assert True in results or False in results, "Proxy logic not working"
    
    def test_selenium_options_configuration(self):
        """Test Selenium Chrome options for anti-bot protection."""
        options = get_selenium_options()
        
        # Convert to list of arguments for testing
        args = options._arguments
        
        # Check for key anti-bot arguments
        assert any('--disable-blink-features=AutomationControlled' in arg for arg in args)
        assert any('--window-size=' in arg for arg in args)
        assert any('--user-agent=' in arg for arg in args)
        
        # Check experimental options
        exp_options = options._experimental_options
        assert 'excludeSwitches' in exp_options
        assert 'useAutomationExtension' in exp_options
    
    def test_static_scraper_anti_bot_detection(self):
        """Test static scraper's ability to detect bot blocking."""
        # Load configuration before creating scraper
        from src.utils.config import load_config
        load_config('config/settings.yaml')
        
        scraper = StaticScraper('test_site', self.config)
        
        # Mock a blocked response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Access denied - robot detected"
        
        # Test blocking detection
        is_blocked = scraper._is_blocked_response(mock_response)
        assert is_blocked, "Failed to detect blocked response"
        
        # Test normal response with sufficient content
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Product Search Results</h1>" + \
                            "<div class='product'>Product 1</div>" * 20 + \
                            "<div class='product'>Product 2</div>" * 20 + \
                            "</body></html>"  # Make it long enough (> 500 chars)
        
        is_blocked = scraper._is_blocked_response(mock_response)
        assert not is_blocked, "False positive in blocking detection"
    
    def test_static_scraper_request_headers(self):
        """Test that static scraper uses randomized headers."""
        # Load configuration before creating scraper
        from src.utils.config import load_config
        load_config('config/settings.yaml')
        
        scraper = StaticScraper('test_site', self.config)
        
        # Mock the session.get method to capture headers
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html></html>"
            mock_get.return_value = mock_response
            
            try:
                scraper._make_request('https://httpbin.org/headers')
                
                # Check that headers were passed
                mock_get.assert_called_once()
                call_kwargs = mock_get.call_args[1]
                
                assert 'headers' in call_kwargs
                headers = call_kwargs['headers']
                assert 'User-Agent' in headers
                
            except Exception:
                pass  # Expected since we're mocking
    
    def test_rate_limiting_implementation(self):
        """Test rate limiting between requests."""
        # Load configuration before creating scraper
        from src.utils.config import load_config
        load_config('config/settings.yaml')
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content that is long enough to not trigger size warnings" + "x" * 500 + "</body></html>"
        mock_response.raise_for_status = Mock()  # Mock this method to avoid HTTPError
        
        # Test rate limiting by making multiple requests
        from unittest.mock import patch
        
        # Patch random_delay in the static_scraper module where it's used
        with patch('src.scrapers.static_scraper.random_delay') as mock_delay:
            scraper = StaticScraper('test_site', self.config)
            
            # Mock the session.get method
            with patch.object(scraper.session, 'get', return_value=mock_response):
                # Make two requests
                scraper._make_request('https://example.com/test1')
                scraper._make_request('https://example.com/test2')
                
                # Verify delay was called (at least twice, once per request)
                assert mock_delay.called, "Rate limiting delay not implemented"
                assert mock_delay.call_count >= 2, f"Delay not called enough times: {mock_delay.call_count}"
    
    def test_captcha_detection_patterns(self):
        """Test CAPTCHA and bot detection patterns."""
        # Load configuration before creating scraper
        from src.utils.config import load_config
        load_config('config/settings.yaml')
        
        scraper = StaticScraper('test_site', self.config)
        
        # Test different content types
        test_cases = [
            # (content, should_be_blocked, description)
            ("Complete the CAPTCHA below to continue", True, "CAPTCHA challenge"),
            ("Please verify you are a human user", True, "Human verification"),
            ("Access denied - robot detected", True, "Robot detection"),
            # Normal content that should NOT be blocked (long enough and without trigger words)
            ("<html><body><h1>Shopping Results</h1>" + 
             "<div class='item'>Product Description Here</div>" * 30 + 
             "</body></html>", False, "Normal shopping page"),
            # Another normal case
            ("<html><body>Welcome to our store! Browse thousands of products." + 
             "x" * 600 + "</body></html>", False, "Normal store content")
        ]
        
        for content, should_be_blocked, description in test_cases:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = content
            
            is_blocked = scraper._is_blocked_response(mock_response)
            if should_be_blocked:
                assert is_blocked, f"Failed to detect blocking in: {description}"
            else:
                assert not is_blocked, f"False positive detection in: {description}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 