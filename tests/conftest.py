"""
Pytest configuration and fixtures for the Multi-Source Data Collection System.

This file sets up the test environment to ensure proper imports and path resolution.
"""

import sys
import os
import pytest
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

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Clear any cached configuration
    from src.utils.config import _config_cache
    import src.utils.config as config_module
    if hasattr(config_module, '_config_cache'):
        config_module._config_cache = None 