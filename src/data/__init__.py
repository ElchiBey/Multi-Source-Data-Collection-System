"""
Data management package for the Multi-Source Data Collection System.

This package handles:
- Database models and operations
- Data processing and validation
- Export functionality
"""

from .models import Product, ScrapingSession
from .database import DatabaseManager, init_database
from .processors import DataProcessor, DataExporter

__all__ = [
    'Product',
    'ScrapingSession', 
    'DatabaseManager',
    'init_database',
    'DataProcessor',
    'DataExporter'
] 