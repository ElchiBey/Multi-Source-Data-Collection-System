"""
Comprehensive Test Suite

Tests for all major components of the Multi-Source Data Collection System.
Covers scrapers, analysis, concurrent processing, and data handling.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import pandas as pd
from datetime import datetime

# Import project modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.scrapers.static_scraper import StaticScraper
from src.scrapers.selenium_scraper import SeleniumScraper
from src.scrapers.manager import ScrapingManager
from src.analysis.statistics import ProductStatistics
from src.analysis.visualization import DataVisualizer
from src.utils.concurrent_manager import ConcurrentScrapingManager, ScrapingTask
from src.utils.config import load_config, get_config
from src.utils.helpers import (
    extract_price, extract_rating, clean_text,
    get_random_user_agent, get_random_headers, random_delay
)

class TestScrapers(unittest.TestCase):
    """Test scraper components."""
    
    def setUp(self):
        """Set up test configuration."""
        self.config = {
            'database': {'url': 'sqlite:///:memory:'},
            'scraping': {
                'delay': {'min': 0.1, 'max': 0.2},
                'retries': 2,
                'timeout': 10
            },
            'scrapers': {
                'amazon': {
                    'selectors': {
                        'product_container': '.s-result-item',
                        'title': 'h2 a span',
                        'price': '.a-price .a-offscreen'
                    }
                }
            }
        }
    
    def test_static_scraper_initialization(self):
        """Test StaticScraper initialization."""
        scraper = StaticScraper(self.config)
        self.assertIsNotNone(scraper)
        self.assertEqual(scraper.config, self.config)
    
    @patch('src.scrapers.static_scraper.requests.get')
    def test_static_scraper_get_page_success(self, mock_get):
        """Test successful page fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>Test</body></html>'
        mock_get.return_value = mock_response
        
        scraper = StaticScraper(self.config)
        response = scraper._get_page('https://example.com')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test', response.text)
    
    def test_selenium_scraper_initialization(self):
        """Test SeleniumScraper initialization."""
        with patch('src.scrapers.selenium_scraper.webdriver.Chrome'):
            scraper = SeleniumScraper(self.config)
            self.assertIsNotNone(scraper)
    
    def test_scraping_manager_initialization(self):
        """Test ScrapingManager initialization."""
        manager = ScrapingManager(self.config)
        self.assertIsNotNone(manager)
        self.assertEqual(len(manager.scrapers), 2)  # static and selenium

class TestHelperFunctions(unittest.TestCase):
    """Test utility helper functions."""
    
    def test_extract_price(self):
        """Test price extraction function."""
        # Test various price formats
        test_cases = [
            ('$29.99', 29.99),
            ('€45.50', 45.50),
            ('£15.75', 15.75),
            ('$1,299.00', 1299.00),
            ('Price: $99', 99.00),
            ('Free', 0.0),
            ('No price', None),
            ('', None)
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = extract_price(input_text)
                self.assertEqual(result, expected)
    
    def test_extract_rating(self):
        """Test rating extraction function."""
        test_cases = [
            ('4.5 out of 5 stars', 4.5),
            ('3 stars', 3.0),
            ('Rating: 4.2', 4.2),
            ('5.0', 5.0),
            ('No rating', None),
            ('', None)
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = extract_rating(input_text)
                self.assertEqual(result, expected)
    
    def test_clean_text(self):
        """Test text cleaning function."""
        test_cases = [
            ('  Extra   spaces  ', 'Extra spaces'),
            ('Text\nwith\nnewlines', 'Text with newlines'),
            ('Text\twith\ttabs', 'Text with tabs'),
            ('', ''),
            (None, '')
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = clean_text(input_text)
                self.assertEqual(result, expected)
    
    def test_get_random_user_agent(self):
        """Test user agent randomization."""
        agents = [get_random_user_agent() for _ in range(10)]
        
        # Should have variation in user agents
        unique_agents = set(agents)
        self.assertGreater(len(unique_agents), 1)
        
        # All should contain browser identifiers
        for agent in agents:
            self.assertTrue(any(browser in agent for browser in ['Chrome', 'Firefox', 'Safari', 'Edge']))
    
    def test_get_random_headers(self):
        """Test random headers generation."""
        headers1 = get_random_headers()
        headers2 = get_random_headers()
        
        # Should have required headers
        required_headers = ['User-Agent', 'Accept', 'Accept-Language']
        for header in required_headers:
            self.assertIn(header, headers1)
            self.assertIn(header, headers2)
        
        # Should have some variation
        self.assertNotEqual(headers1['User-Agent'], headers2['User-Agent'])
    
    def test_random_delay(self):
        """Test random delay functionality."""
        import time
        
        start_time = time.time()
        random_delay(min_delay=0.1, max_delay=0.2)
        elapsed = time.time() - start_time
        
        # Should be within expected range (with some tolerance)
        self.assertGreaterEqual(elapsed, 0.09)
        self.assertLessEqual(elapsed, 0.25)

class TestConcurrentProcessing(unittest.TestCase):
    """Test concurrent processing capabilities."""
    
    def setUp(self):
        """Set up test configuration."""
        self.config = {
            'scraping': {
                'max_workers': 2,
                'use_multiprocessing': False
            }
        }
    
    def test_concurrent_manager_initialization(self):
        """Test ConcurrentScrapingManager initialization."""
        manager = ConcurrentScrapingManager(self.config)
        self.assertIsNotNone(manager)
        self.assertEqual(manager.max_workers, 2)
        self.assertFalse(manager.use_multiprocessing)
    
    def test_scraping_task_creation(self):
        """Test ScrapingTask creation."""
        task = ScrapingTask(
            task_id='test_task',
            source='amazon',
            keyword='laptop',
            page=1
        )
        
        self.assertEqual(task.task_id, 'test_task')
        self.assertEqual(task.source, 'amazon')
        self.assertEqual(task.keyword, 'laptop')
        self.assertEqual(task.page, 1)
        self.assertIsNotNone(task.created_at)
    
    def test_add_scraping_tasks(self):
        """Test adding multiple scraping tasks."""
        manager = ConcurrentScrapingManager(self.config)
        
        sources = ['amazon', 'ebay']
        keywords = ['laptop', 'phone']
        max_pages = 2
        
        manager.add_scraping_tasks(sources, keywords, max_pages)
        
        # Should have 8 tasks (2 sources × 2 keywords × 2 pages)
        self.assertEqual(manager.total_tasks, 8)
        self.assertEqual(manager.task_queue.qsize(), 8)
    
    def test_progress_stats(self):
        """Test progress statistics."""
        manager = ConcurrentScrapingManager(self.config)
        manager.total_tasks = 10
        manager.completed_count = 6
        manager.failed_count = 2
        
        stats = manager.get_progress_stats()
        
        self.assertEqual(stats['total_tasks'], 10)
        self.assertEqual(stats['completed_tasks'], 6)
        self.assertEqual(stats['failed_tasks'], 2)
        self.assertEqual(stats['completion_rate'], 80.0)
        self.assertEqual(stats['success_rate'], 75.0)

class TestDataAnalysis(unittest.TestCase):
    """Test data analysis components."""
    
    def setUp(self):
        """Set up test data and configuration."""
        self.config = {
            'database': {'url': 'sqlite:///:memory:'},
            'export': {'output_dir': tempfile.mkdtemp()}
        }
        
        # Create sample DataFrame for testing
        self.sample_data = pd.DataFrame({
            'source': ['amazon', 'ebay', 'amazon', 'walmart'],
            'title': ['Laptop 1', 'Laptop 2', 'Phone 1', 'Phone 2'],
            'price': [999.99, 899.99, 599.99, 649.99],
            'rating': [4.5, 4.2, 4.8, 4.0],
            'search_keyword': ['laptop', 'laptop', 'phone', 'phone'],
            'scraped_at': [datetime.now()] * 4
        })
    
    @patch('src.analysis.statistics.ProductStatistics._get_products_dataframe')
    def test_basic_statistics(self, mock_get_df):
        """Test basic statistics generation."""
        mock_get_df.return_value = self.sample_data
        
        stats = ProductStatistics(self.config)
        basic_stats = stats.get_basic_statistics()
        
        self.assertEqual(basic_stats['total_products'], 4)
        self.assertEqual(basic_stats['unique_sources'], 3)
        self.assertIn('price_statistics', basic_stats)
        self.assertAlmostEqual(basic_stats['price_statistics']['mean_price'], 787.49, places=2)
    
    @patch('src.analysis.statistics.ProductStatistics._get_products_dataframe')
    def test_price_analysis_by_source(self, mock_get_df):
        """Test price analysis by source."""
        mock_get_df.return_value = self.sample_data
        
        stats = ProductStatistics(self.config)
        price_analysis = stats.get_price_analysis_by_source()
        
        self.assertIn('amazon', price_analysis)
        self.assertIn('ebay', price_analysis)
        self.assertIn('walmart', price_analysis)
        self.assertIn('comparison', price_analysis)
        
        # Check Amazon has 2 products
        self.assertEqual(price_analysis['amazon']['product_count'], 2)
    
    @patch('src.analysis.statistics.ProductStatistics._get_products_dataframe')
    def test_keyword_analysis(self, mock_get_df):
        """Test keyword analysis."""
        mock_get_df.return_value = self.sample_data
        
        stats = ProductStatistics(self.config)
        keyword_analysis = stats.get_keyword_analysis()
        
        self.assertIn('laptop', keyword_analysis)
        self.assertIn('phone', keyword_analysis)
        
        # Check laptop has 2 products
        self.assertEqual(keyword_analysis['laptop']['total_products'], 2)
        self.assertEqual(keyword_analysis['phone']['total_products'], 2)
    
    @patch('src.analysis.statistics.ProductStatistics._get_products_dataframe')
    def test_data_quality_report(self, mock_get_df):
        """Test data quality assessment."""
        mock_get_df.return_value = self.sample_data
        
        stats = ProductStatistics(self.config)
        quality_report = stats.get_data_quality_report()
        
        self.assertEqual(quality_report['total_records'], 4)
        self.assertEqual(quality_report['completeness']['title']['filled'], 4)
        self.assertEqual(quality_report['completeness']['price']['filled'], 4)
        self.assertEqual(quality_report['overall_quality_score'], 100.0)

class TestVisualization(unittest.TestCase):
    """Test visualization components."""
    
    def setUp(self):
        """Set up test configuration."""
        self.config = {
            'database': {'url': 'sqlite:///:memory:'},
            'export': {'output_dir': tempfile.mkdtemp()}
        }
    
    @patch('src.analysis.visualization.ProductStatistics._get_products_dataframe')
    def test_data_visualizer_initialization(self, mock_get_df):
        """Test DataVisualizer initialization."""
        mock_get_df.return_value = pd.DataFrame()
        
        visualizer = DataVisualizer(self.config)
        self.assertIsNotNone(visualizer)
        self.assertTrue(visualizer.output_dir.exists())
    
    @patch('src.analysis.visualization.ProductStatistics._get_products_dataframe')
    @patch('matplotlib.pyplot.savefig')
    def test_price_distribution_chart(self, mock_savefig, mock_get_df):
        """Test price distribution chart creation."""
        sample_data = pd.DataFrame({
            'price': [100, 200, 300, 400, 500],
            'source': ['amazon'] * 5
        })
        mock_get_df.return_value = sample_data
        
        visualizer = DataVisualizer(self.config)
        result = visualizer.create_price_distribution_chart()
        
        # Should return base64 or file path
        self.assertIsNotNone(result)

class TestConfiguration(unittest.TestCase):
    """Test configuration management functions."""
    
    def test_load_config_function(self):
        """Test load_config function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # Create test config file
            test_config = """
database:
  url: sqlite:///test.db
scraping:
  delay:
    min: 1
    max: 3
sources:
  amazon:
    enabled: true
export:
  formats: [csv, json]
"""
            with open(config_path, 'w') as f:
                f.write(test_config)
            
            # Test loading config
            config = load_config(config_path)
            
            self.assertEqual(config['database']['url'], 'sqlite:///test.db')
            self.assertEqual(config['scraping']['delay']['min'], 1)
            self.assertTrue(config['sources']['amazon']['enabled'])
    
    def test_get_config_function(self):
        """Test get_config function with key paths."""
        # Load our actual config for testing
        config = load_config('config/settings.yaml')
        
        # Test getting specific key paths
        database_config = get_config('database')
        self.assertIsInstance(database_config, dict)
        self.assertIn('url', database_config)
        
        # Test getting nested value
        db_url = get_config('database.url')
        self.assertIsInstance(db_url, str)
        
        # Test getting entire config
        full_config = get_config()
        self.assertEqual(full_config, config)

# Integration Tests
class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'database': {'url': f'sqlite:///{self.temp_dir}/test.db'},
            'export': {'output_dir': self.temp_dir},
            'scraping': {
                'delay': {'min': 0.1, 'max': 0.2},
                'max_workers': 2
            }
        }
    
    def test_complete_scraping_workflow(self):
        """Test complete scraping workflow with mock data."""
        # This would test the entire pipeline from scraping to analysis
        # For now, just test that components can be initialized together
        
        manager = ScrapingManager(self.config)
        concurrent_manager = ConcurrentScrapingManager(self.config)
        
        self.assertIsNotNone(manager)
        self.assertIsNotNone(concurrent_manager)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2) 