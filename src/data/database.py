"""
Database management module for the Multi-Source Data Collection System.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager
import json
import uuid
from datetime import datetime

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Product, ScrapingSession, PriceHistory
from src.utils.logger import LoggerMixin
from src.utils.helpers import generate_hash

class DatabaseManager(LoggerMixin):
    """
    Database manager for handling all database operations.
    
    Implements the Singleton pattern to ensure single database connection.
    """
    
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config = config or {}
        self._setup_database()
    
    def _setup_database(self) -> None:
        """Initialize database connection and create tables."""
        try:
            # Get database URL from config
            db_url = self.config.get('database', {}).get('url', 'sqlite:///data/products.db')
            
            # Ensure directory exists for SQLite databases
            if db_url.startswith('sqlite:///'):
                db_path = Path(db_url.replace('sqlite:///', ''))
                db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create engine
            self._engine = create_engine(
                db_url,
                echo=self.config.get('database', {}).get('echo', False),
                pool_size=self.config.get('database', {}).get('pool_size', 10),
                max_overflow=self.config.get('database', {}).get('max_overflow', 20)
            )
            
            # Create session factory
            self._session_factory = sessionmaker(bind=self._engine)
            
            # Create tables (checkfirst=True prevents duplicate creation errors)
            Base.metadata.create_all(self._engine, checkfirst=True)
            
            self.logger.info(f"Database initialized successfully: {db_url}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions.
        
        Yields:
            SQLAlchemy session
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def save_product(self, product_data: Dict[str, Any]) -> Optional[Product]:
        """
        Save a product to the database.
        
        Args:
            product_data: Dictionary containing product information
            
        Returns:
            Saved Product instance or None if failed
        """
        try:
            with self.get_session() as session:
                # Generate hash for deduplication
                hash_data = f"{product_data.get('source')}-{product_data.get('product_id')}-{product_data.get('title')}"
                product_data['data_hash'] = generate_hash(hash_data)
                
                # Check for existing product
                existing = session.query(Product).filter_by(
                    source=product_data.get('source'),
                    product_id=product_data.get('product_id')
                ).first()
                
                if existing:
                    # Update existing product
                    for key, value in product_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    
                    # Track price history if price changed
                    if existing.price != product_data.get('price'):
                        self._save_price_history(session, existing, product_data.get('price'))
                    
                    product = existing
                    self.logger.debug(f"Updated existing product: {product.id}")
                else:
                    # Create new product
                    product = Product.from_dict(product_data)
                    session.add(product)
                    session.flush()  # Get the ID
                    
                    # Save initial price history
                    self._save_price_history(session, product, product_data.get('price'))
                    
                    self.logger.debug(f"Created new product: {product.id}")
                
                return product
                
        except Exception as e:
            self.logger.error(f"Failed to save product: {e}")
            return None
    
    def _save_price_history(self, session: Session, product: Product, price: float) -> None:
        """Save price history entry."""
        if price is None:
            return
        
        try:
            price_entry = PriceHistory(
                product_id=product.id,
                source_product_id=product.product_id,
                source=product.source,
                price=price,
                original_price=product.original_price,
                discount_percent=product.discount_percent,
                availability=product.availability,
                condition=product.condition
            )
            session.add(price_entry)
        except Exception as e:
            self.logger.error(f"Failed to save price history: {e}")
    
    def create_scraping_session(self, source: str, keywords: List[str], config: Dict[str, Any]) -> ScrapingSession:
        """
        Create a new scraping session.
        
        Args:
            source: Source name (amazon, ebay, etc.)
            keywords: List of search keywords
            config: Scraping configuration
            
        Returns:
            Created ScrapingSession instance
        """
        try:
            with self.get_session() as session:
                scraping_session = ScrapingSession(
                    session_id=str(uuid.uuid4()),
                    source=source,
                    search_keywords=json.dumps(keywords),
                    scraper_config=json.dumps(config),
                    max_pages=config.get('max_pages', 5),
                    python_version=f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
                    scraper_version="1.0.0"
                )
                
                session.add(scraping_session)
                session.flush()
                
                self.logger.info(f"Created scraping session: {scraping_session.session_id}")
                return scraping_session
                
        except Exception as e:
            self.logger.error(f"Failed to create scraping session: {e}")
            raise
    
    def update_scraping_session(self, session_id: str, **updates) -> None:
        """
        Update scraping session with results.
        
        Args:
            session_id: Session UUID
            **updates: Fields to update
        """
        try:
            with self.get_session() as session:
                scraping_session = session.query(ScrapingSession).filter_by(
                    session_id=session_id
                ).first()
                
                if scraping_session:
                    for key, value in updates.items():
                        if hasattr(scraping_session, key):
                            setattr(scraping_session, key, value)
                    
                    # Calculate duration if completed
                    if 'completed_at' in updates and scraping_session.started_at:
                        duration = (updates['completed_at'] - scraping_session.started_at).total_seconds()
                        scraping_session.duration_seconds = int(duration)
                    
                    self.logger.debug(f"Updated scraping session: {session_id}")
                else:
                    self.logger.warning(f"Scraping session not found: {session_id}")
                    
        except Exception as e:
            self.logger.error(f"Failed to update scraping session: {e}")
    
    def get_products(
        self,
        source: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: str = 'scraped_at',
        order_desc: bool = True
    ) -> List[Product]:
        """
        Get products with filtering and pagination.
        
        Args:
            source: Filter by source
            keyword: Filter by search keyword
            limit: Maximum number of results
            offset: Offset for pagination
            order_by: Field to order by
            order_desc: Order descending
            
        Returns:
            List of Product instances
        """
        try:
            with self.get_session() as session:
                query = session.query(Product)
                
                # Apply filters
                if source:
                    query = query.filter(Product.source == source)
                
                if keyword:
                    query = query.filter(Product.search_keyword.like(f'%{keyword}%'))
                
                # Apply ordering
                if hasattr(Product, order_by):
                    order_column = getattr(Product, order_by)
                    if order_desc:
                        query = query.order_by(order_column.desc())
                    else:
                        query = query.order_by(order_column)
                
                # Apply pagination
                if offset > 0:
                    query = query.offset(offset)
                
                if limit:
                    query = query.limit(limit)
                
                return query.all()
                
        except Exception as e:
            self.logger.error(f"Failed to get products: {e}")
            return []
    
    def get_product_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            with self.get_session() as session:
                stats = {
                    'total_products': session.query(Product).count(),
                    'products_by_source': {},
                    'avg_price': 0.0,
                    'latest_scrape': None,
                    'total_sessions': session.query(ScrapingSession).count()
                }
                
                # Products by source
                source_counts = session.query(
                    Product.source,
                    func.count(Product.id)
                ).group_by(Product.source).all()
                
                stats['products_by_source'] = {source: count for source, count in source_counts}
                
                # Average price
                avg_price = session.query(func.avg(Product.price)).filter(
                    Product.price.isnot(None)
                ).scalar()
                stats['avg_price'] = float(avg_price) if avg_price else 0.0
                
                # Latest scrape
                latest = session.query(Product.scraped_at).order_by(
                    Product.scraped_at.desc()
                ).first()
                
                if latest:
                    stats['latest_scrape'] = latest[0].isoformat()
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """
        Clean up old data from the database.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of records deleted
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            with self.get_session() as session:
                # Delete old products
                old_products = session.query(Product).filter(
                    Product.scraped_at < cutoff_date
                ).delete()
                
                # Delete old sessions
                old_sessions = session.query(ScrapingSession).filter(
                    ScrapingSession.started_at < cutoff_date
                ).delete()
                
                # Delete old price history
                old_prices = session.query(PriceHistory).filter(
                    PriceHistory.recorded_at < cutoff_date
                ).delete()
                
                deleted_count = old_products + old_sessions + old_prices
                
                self.logger.info(f"Cleaned up {deleted_count} old records")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return 0

def init_database(config: Dict[str, Any]) -> DatabaseManager:
    """
    Initialize the database with configuration.
    
    Args:
        config: Application configuration
        
    Returns:
        DatabaseManager instance
    """
    return DatabaseManager(config) 