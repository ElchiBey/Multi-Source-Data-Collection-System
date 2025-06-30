"""
Pytest configuration and fixtures for the Multi-Source Data Collection System.

This file sets up the test environment to ensure proper imports and path resolution.
"""

import sys
import os
import pytest
import tempfile
import sqlite3
from pathlib import Path

# Ensure project root is in Python path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Verify critical imports work
try:
    import yaml
    import src.utils.config
    import src.scrapers.static_scraper
    print("✅ All critical imports successful in conftest.py")
except ImportError as e:
    print(f"❌ Import error in conftest.py: {e}")
    # Don't fail here, let individual tests handle it

@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return PROJECT_ROOT

@pytest.fixture
def temp_config():
    """Provide a temporary configuration for testing."""
    return {
        'database': {'url': 'sqlite:///:memory:'},
        'scraping': {
            'delay': {'min': 0.1, 'max': 0.2},
            'retries': 2,
            'timeout': 10
        },
        'sources': {
            'test_source': {
                'enabled': True,
                'base_url': 'https://httpbin.org'
            }
        },
        'export': {'output_dir': '/tmp'}
    }

@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    # Create test database with sample data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create products table with complete schema matching production
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        title VARCHAR(500),
        url VARCHAR(1000),
        product_id VARCHAR(100),
        source VARCHAR(50),
        price FLOAT,
        original_price FLOAT,
        currency VARCHAR(10),
        discount_percent FLOAT,
        description TEXT,
        category VARCHAR(200),
        brand VARCHAR(100),
        condition VARCHAR(50),
        availability VARCHAR(100),
        rating FLOAT,
        review_count INTEGER,
        image_url VARCHAR(1000),
        additional_images TEXT,
        shipping_cost FLOAT,
        seller_name VARCHAR(200),
        seller_rating FLOAT,
        specifications TEXT,
        scraped_at DATETIME,
        last_updated DATETIME,
        search_keyword VARCHAR(200),
        page_number INTEGER,
        position_on_page INTEGER,
        scraper_type VARCHAR(20),
        data_hash VARCHAR(32),
        is_valid BOOLEAN,
        validation_errors TEXT,
        created_at DATETIME
    )
    ''')
    
    # Insert sample data with all required columns
    sample_data = [
        ('Gaming Laptop Dell XPS', 'http://test.com/1', 'prod1', 'amazon', 599.99, 649.99, 'USD', 7.7, 'High performance gaming laptop', 'Electronics', 'Dell', 'new', 'in stock', 4.5, 156, 'img1.jpg', '[]', 15.99, 'Amazon', 4.8, '{}', '2025-06-30 10:00:00', '2025-06-30 10:00:00', 'laptop', 1, 1, 'static', 'hash1', 1, '[]', '2025-06-30 10:00:00'),
        ('iPhone 15 Pro Max', 'http://test.com/2', 'prod2', 'ebay', 299.99, 399.99, 'USD', 25.0, 'Latest iPhone model', 'Electronics', 'Apple', 'used', 'available', 4.0, 89, 'img2.jpg', '[]', 9.99, 'TechDealer', 4.3, '{}', '2025-06-30 11:00:00', '2025-06-30 11:00:00', 'phone', 1, 2, 'selenium', 'hash2', 1, '[]', '2025-06-30 11:00:00'),
        ('Samsung Galaxy Tab S9', 'http://test.com/3', 'prod3', 'walmart', 199.99, 249.99, 'USD', 20.0, 'Premium Android tablet', 'Electronics', 'Samsung', 'new', 'limited stock', 3.8, 42, 'img3.jpg', '[]', 0.0, 'Walmart', 4.1, '{}', '2025-06-30 12:00:00', '2025-06-30 12:00:00', 'tablet', 1, 3, 'static', 'hash3', 1, '[]', '2025-06-30 12:00:00')
    ]
    
    cursor.executemany('''
    INSERT INTO products (title, url, product_id, source, price, original_price, currency, discount_percent, description, category, brand, condition, availability, rating, review_count, image_url, additional_images, shipping_cost, seller_name, seller_rating, specifications, scraped_at, last_updated, search_keyword, page_number, position_on_page, scraper_type, data_hash, is_valid, validation_errors, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_data)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink()

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Clear any cached configuration
    from src.utils.config import _config_cache
    import src.utils.config as config_module
    if hasattr(config_module, '_config_cache'):
        config_module._config_cache = None 