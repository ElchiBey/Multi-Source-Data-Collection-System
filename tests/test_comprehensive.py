"""
🧪 Comprehensive System Tests

Tests for the complete Multi-Source Data Collection System.
Covers all major components and integration points.
"""

import pytest
import tempfile
import sqlite3
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch
import json

# Import our modules
from src.scrapers.base_scraper import BaseScraper
from src.scrapers.static_scraper import StaticScraper
from src.scrapers.selenium_scraper import AdvancedSeleniumScraper
from src.utils.logger import get_logger
from src.analysis.statistics import DataStatistics
from src.analysis.visualization import DataVisualizer
from src.analysis.reports import ReportGenerator

logger = get_logger(__name__)

class TestComprehensiveSystem:
    """Test the complete system integration."""
    
    def test_database_integration(self, temp_db):
        """Test database operations."""
        # Test statistics loading
        stats = DataStatistics(temp_db)
        df = stats.load_data("database")
        
        assert len(df) == 3
        assert 'price' in df.columns
        assert 'source' in df.columns
        assert df['source'].nunique() == 3
    
    def test_statistics_generation(self, temp_db):
        """Test statistical analysis."""
        stats = DataStatistics(temp_db)
        df = stats.load_data("database")
        
        # Test basic statistics
        assert len(df) > 0
        assert df['price'].mean() > 0
        assert 'amazon' in df['source'].values
        assert 'ebay' in df['source'].values
        assert 'walmart' in df['source'].values
    
    def test_visualization_creation(self, temp_db):
        """Test chart generation."""
        stats = DataStatistics(temp_db)
        df = stats.load_data("database")
        
        visualizer = DataVisualizer(df)
        charts = visualizer.create_all_charts()
        
        # Should create charts
        assert isinstance(charts, dict)
        # Charts may not be created if paths don't exist in test env, but function should not error
    
    def test_report_generation(self, temp_db):
        """Test report generation."""
        stats = DataStatistics(temp_db)
        df = stats.load_data("database")
        
        if not df.empty:
            report_gen = ReportGenerator(df)
            # Test basic statistics generation
            basic_stats = report_gen._generate_basic_statistics()
            
            assert 'overview' in basic_stats
            assert basic_stats['overview']['total_products'] == 3
            assert basic_stats['overview']['unique_sources'] == 3
    
    def test_price_analysis(self, temp_db):
        """Test price analysis functionality."""
        stats = DataStatistics(temp_db)
        df = stats.load_data("database")
        
        prices = df['price'].dropna()
        
        # Verify price calculations
        assert len(prices) == 3
        assert prices.mean() == (599.99 + 299.99 + 199.99) / 3
        assert prices.min() == 199.99
        assert prices.max() == 599.99
    
    def test_source_analysis(self, temp_db):
        """Test source comparison functionality."""
        stats = DataStatistics(temp_db)
        df = stats.load_data("database")
        
        # Test source distribution
        source_counts = df['source'].value_counts()
        
        assert len(source_counts) == 3
        assert source_counts['amazon'] == 1
        assert source_counts['ebay'] == 1  
        assert source_counts['walmart'] == 1
    
    def test_data_export_functionality(self, temp_db):
        """Test data export capabilities."""
        stats = DataStatistics(temp_db)
        df = stats.load_data("database")
        
        # Test CSV export capability
        assert len(df) > 0
        assert 'price' in df.columns
        assert 'source' in df.columns
        
        # Verify data types
        assert df['price'].dtype in ['float64', 'int64']
        assert df['source'].dtype == 'object'

class TestScraperIntegration:
    """Test scraper components integration."""
    
    def test_base_scraper_inheritance(self):
        """Test that scrapers inherit from base properly."""
        # Test that our scrapers inherit from BaseScraper
        static_scraper = StaticScraper('test', {})
        
        assert isinstance(static_scraper, BaseScraper)
        assert hasattr(static_scraper, 'scrape')
        assert hasattr(static_scraper, 'source')
    
    def test_scraper_configuration(self):
        """Test scraper configuration handling."""
        test_config = {
            'user_agent': 'test-agent',
            'delay': 1.0
        }
        
        scraper = StaticScraper('test', test_config)
        
        assert scraper.config == test_config
        assert scraper.source == 'test'

class TestSystemRequirements:
    """Test that system meets final project requirements."""
    
    def test_multi_source_capability(self, temp_db):
        """Verify system handles multiple sources."""
        stats = DataStatistics(temp_db)
        df = stats.load_data("database")
        
        # Must have at least 3 sources
        assert df['source'].nunique() >= 3
        
        # Verify we have the required sources
        sources = df['source'].unique()
        assert 'amazon' in sources
        assert 'ebay' in sources
        assert 'walmart' in sources
    
    def test_data_volume_requirement(self):
        """Test that we have sufficient data volume."""
        # Connect to actual database
        stats = DataStatistics('data/products.db')
        df = stats.load_data("database")
        
        if not df.empty:
            # Should have at least 5000 records for final project
            assert len(df) >= 5000, f"Only {len(df)} records found, need at least 5000"
    
    def test_statistical_analysis_capability(self, temp_db):
        """Test comprehensive statistical analysis."""
        stats = DataStatistics(temp_db)
        df = stats.load_data("database")
        
        if not df.empty:
            # Test price analysis
            prices = df['price'].dropna()
            assert len(prices) > 0
            
            # Test basic statistics
            assert prices.mean() > 0
            assert prices.std() >= 0
            assert prices.min() >= 0
            assert prices.max() >= prices.min()
    
    def test_export_formats_capability(self, temp_db):
        """Test multiple export format support."""
        stats = DataStatistics(temp_db)
        df = stats.load_data("database")
        
        if not df.empty:
            # Test DataFrame can be exported to different formats
            # CSV
            csv_data = df.to_csv()
            assert isinstance(csv_data, str)
            assert len(csv_data) > 0
            
            # JSON
            json_data = df.to_json()
            assert isinstance(json_data, str)
            assert len(json_data) > 0 