"""
Database models for the Multi-Source Data Collection System.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class Product(Base):
    """
    Product model for storing scraped product information.
    """
    __tablename__ = 'products'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Product identification
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    product_id = Column(String(100))  # Source-specific ID (ASIN, eBay item ID, etc.)
    source = Column(String(50), nullable=False)  # amazon, ebay, walmart
    
    # Pricing information
    price = Column(Float)
    original_price = Column(Float)
    currency = Column(String(10), default='USD')
    discount_percent = Column(Float)
    
    # Product details
    description = Column(Text)
    category = Column(String(200))
    brand = Column(String(100))
    condition = Column(String(50))  # new, used, refurbished
    availability = Column(String(100))
    
    # Rating and reviews
    rating = Column(Float)
    review_count = Column(Integer)
    
    # Images and media
    image_url = Column(String(1000))
    additional_images = Column(Text)  # JSON string of image URLs
    
    # Shipping and seller info
    shipping_cost = Column(Float)
    seller_name = Column(String(200))
    seller_rating = Column(Float)
    
    # Technical specifications (JSON string)
    specifications = Column(Text)
    
    # Scraping metadata
    scraped_at = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    search_keyword = Column(String(200))
    page_number = Column(Integer)
    position_on_page = Column(Integer)
    
    # Data quality and deduplication
    data_hash = Column(String(32))  # MD5 hash for deduplication
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(Text)  # JSON string of validation errors
    
    # Create indexes for better query performance
    __table_args__ = (
        Index('idx_source_product_id', 'source', 'product_id'),
        Index('idx_scraped_at', 'scraped_at'),
        Index('idx_search_keyword', 'search_keyword'),
        Index('idx_price', 'price'),
        Index('idx_data_hash', 'data_hash'),
    )
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, title='{self.title[:50]}...', source='{self.source}', price={self.price})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'product_id': self.product_id,
            'source': self.source,
            'price': self.price,
            'original_price': self.original_price,
            'currency': self.currency,
            'discount_percent': self.discount_percent,
            'description': self.description,
            'category': self.category,
            'brand': self.brand,
            'condition': self.condition,
            'availability': self.availability,
            'rating': self.rating,
            'review_count': self.review_count,
            'image_url': self.image_url,
            'shipping_cost': self.shipping_cost,
            'seller_name': self.seller_name,
            'seller_rating': self.seller_rating,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'search_keyword': self.search_keyword,
            'page_number': self.page_number,
            'position_on_page': self.position_on_page,
            'is_valid': self.is_valid
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Create Product instance from dictionary."""
        # Remove fields that aren't direct model attributes
        model_data = {k: v for k, v in data.items() 
                     if k in cls.__table__.columns.keys()}
        return cls(**model_data)

class ScrapingSession(Base):
    """
    Model for tracking scraping sessions and metadata.
    """
    __tablename__ = 'scraping_sessions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Session identification
    session_id = Column(String(36), unique=True, nullable=False)  # UUID
    source = Column(String(50), nullable=False)
    
    # Session parameters
    search_keywords = Column(Text)  # JSON array of keywords
    max_pages = Column(Integer)
    target_urls = Column(Text)  # JSON array of URLs
    
    # Session timing
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Results summary
    total_products_found = Column(Integer, default=0)
    total_products_saved = Column(Integer, default=0)
    total_pages_scraped = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    
    # Success metrics
    success_rate = Column(Float)  # percentage of successful requests
    avg_response_time = Column(Float)  # average response time in seconds
    
    # Configuration used
    scraper_config = Column(Text)  # JSON string of configuration
    
    # Session status
    status = Column(String(20), default='running')  # running, completed, failed, cancelled
    error_message = Column(Text)
    
    # System information
    python_version = Column(String(20))
    scraper_version = Column(String(20))
    user_agent = Column(String(500))
    
    # Create indexes
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_source', 'source'),
        Index('idx_started_at', 'started_at'),
        Index('idx_status', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<ScrapingSession(id={self.id}, source='{self.source}', status='{self.status}', products={self.total_products_saved})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'source': self.source,
            'search_keywords': self.search_keywords,
            'max_pages': self.max_pages,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'total_products_found': self.total_products_found,
            'total_products_saved': self.total_products_saved,
            'total_pages_scraped': self.total_pages_scraped,
            'total_errors': self.total_errors,
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'status': self.status,
            'error_message': self.error_message
        }

class PriceHistory(Base):
    """
    Model for tracking price changes over time.
    """
    __tablename__ = 'price_history'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to product
    product_id = Column(Integer, nullable=False)  # References products.id
    source_product_id = Column(String(100), nullable=False)
    source = Column(String(50), nullable=False)
    
    # Price information
    price = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    original_price = Column(Float)
    discount_percent = Column(Float)
    
    # Timing
    recorded_at = Column(DateTime, default=func.now())
    
    # Additional context
    availability = Column(String(100))
    condition = Column(String(50))
    
    # Create indexes
    __table_args__ = (
        Index('idx_product_id', 'product_id'),
        Index('idx_source_product_id', 'source_product_id'),
        Index('idx_recorded_at', 'recorded_at'),
        Index('idx_price', 'price'),
    )
    
    def __repr__(self) -> str:
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, recorded_at={self.recorded_at})>" 