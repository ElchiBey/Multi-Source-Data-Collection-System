"""
Multi-Source Data Collection System

A comprehensive web scraping and data analysis system for e-commerce
price monitoring across multiple platforms.
"""

__version__ = "1.0.0"
__author__ = "Data Scraping Final Project"
__description__ = "Multi-Source Data Collection System"

# Package imports
from src.utils.config import load_config
from src.utils.logger import setup_logger

# Make commonly used classes available at package level
try:
    from src.scrapers.manager import ScrapingManager
    from src.data.database import DatabaseManager
    from src.analysis.reports import ReportGenerator
except ImportError:
    # Handle case where dependencies aren't installed yet
    pass

__all__ = [
    'ScrapingManager',
    'DatabaseManager', 
    'ReportGenerator',
    'load_config',
    'setup_logger'
] 