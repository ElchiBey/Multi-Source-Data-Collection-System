"""
Scraping Manager Module

This module coordinates different scrapers and manages the overall scraping workflow.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json

from .static_scraper import StaticScraper
from ..data.database import DatabaseManager
from ..data.processors import DataProcessor
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ScrapingManager:
    """
    Manages and coordinates scraping operations across multiple sources.
    
    This class implements the Coordinator pattern to manage different scrapers
    and handle the overall scraping workflow.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the scraping manager.
        
        Args:
            config: Application configuration dictionary
        """
        self.config = config
        self.db_manager = DatabaseManager(config)
        self.data_processor = DataProcessor(config)
        
        # Initialize scrapers (will create them dynamically per source)
        self.scraper_classes = {
            'static': StaticScraper,
            # TODO: Add SeleniumScraper and ScrapyScraper when implemented
        }
        
        logger.info("ScrapingManager initialized")
    
    def get_scraper(self, scraper_type: str = 'static'):
        """
        Get a scraper instance by type.
        
        Args:
            scraper_type: Type of scraper ('static', 'selenium', 'scrapy')
            
        Returns:
            Scraper instance
        """
        if scraper_type in self.scraper_classes:
            scraper_class = self.scraper_classes[scraper_type]
            return scraper_class('amazon', self.config)  # Default to amazon for testing
        else:
            logger.warning(f"Unknown scraper type: {scraper_type}")
            return None
    
    def scrape_single(self, source: str, keyword: str, page: int, scraper_type: str = 'static'):
        """
        Scrape a single page from a source.
        
        Args:
            source: Source name
            keyword: Search keyword
            page: Page number
            scraper_type: Type of scraper to use
            
        Returns:
            List of products from the page
        """
        try:
            scraper = self.get_scraper(scraper_type)
            if not scraper:
                return []
                
            # Create a minimal scraper for single page
            result = scraper.scrape(keywords=[keyword], max_pages=1)
            return result.data if result.success else []
            
        except Exception as e:
            logger.error(f"Failed to scrape single page: {e}")
            return []
    
    def scrape_all(
        self,
        sources: List[str],
        keywords: List[str],
        max_pages: int = 5,
        output_dir: str = 'data_output/raw'
    ) -> List[Dict[str, Any]]:
        """
        Scrape products from multiple sources.
        
        Args:
            sources: List of source names (amazon, ebay, walmart)
            keywords: List of search keywords
            max_pages: Maximum pages to scrape per source
            output_dir: Directory to save raw data
            
        Returns:
            List of scraped product dictionaries
        """
        logger.info(f"Starting scraping for sources: {sources}, keywords: {keywords}")
        
        all_results = []
        
        # Create scraping session
        session_id = self._create_scraping_session(sources, keywords, max_pages)
        
        try:
            # Scrape each source
            for source in sources:
                if not self._is_source_enabled(source):
                    logger.warning(f"Source {source} is disabled, skipping...")
                    continue
                
                logger.info(f"Scraping {source}...")
                
                try:
                    # Create scraper instance for this source
                    scraper_class = self.scraper_classes['static']
                    scraper = scraper_class(source, self.config)
                    
                    source_results = []
                    for keyword in keywords:
                        logger.info(f"Searching {source} for '{keyword}'...")
                        
                        # Scrape products for this keyword  
                        result = scraper.scrape(
                            keywords=[keyword],
                            max_pages=max_pages
                        )
                        products = result.data if result.success else []
                        
                        if products:
                            source_results.extend(products)
                            logger.info(f"Found {len(products)} products for '{keyword}' on {source}")
                        else:
                            logger.warning(f"No products found for '{keyword}' on {source}")
                    
                    # Process and save data
                    if source_results:
                        processed_results = self.data_processor.process_scraped_data(source_results)
                        
                        # Save to database
                        saved_count = self._save_products(processed_results)
                        logger.info(f"Saved {saved_count} products from {source}")
                        
                        # Save raw data to file
                        self._save_raw_data(source_results, output_dir, source)
                        
                        all_results.extend(processed_results)
                    
                except Exception as e:
                    logger.error(f"Failed to scrape {source}: {e}")
                    continue
            
            # Update scraping session
            self._update_scraping_session(session_id, len(all_results))
            
            logger.info(f"Scraping completed. Total products: {len(all_results)}")
            return all_results
            
        except Exception as e:
            logger.error(f"Scraping operation failed: {e}")
            self._update_scraping_session(session_id, 0, error=str(e))
            raise
    
    def _create_scraping_session(self, sources: List[str], keywords: List[str], max_pages: int) -> str:
        """Create a new scraping session."""
        try:
            session = self.db_manager.create_scraping_session(
                source=','.join(sources),
                keywords=keywords,
                config={
                    'max_pages': max_pages,
                    'sources': sources,
                    'scraper_type': 'static'
                }
            )
            return session.session_id
        except Exception as e:
            logger.error(f"Failed to create scraping session: {e}")
            return "unknown"
    
    def _update_scraping_session(self, session_id: str, products_found: int, error: Optional[str] = None):
        """Update scraping session with results."""
        try:
            updates = {
                'completed_at': datetime.utcnow(),
                'products_found': products_found,
                'status': 'failed' if error else 'completed'
            }
            
            if error:
                updates['error_message'] = error
            
            self.db_manager.update_scraping_session(session_id, **updates)
        except Exception as e:
            logger.error(f"Failed to update scraping session: {e}")
    
    def _is_source_enabled(self, source: str) -> bool:
        """Check if a source is enabled in configuration."""
        sources_config = self.config.get('sources', {})
        source_config = sources_config.get(source, {})
        return source_config.get('enabled', False)
    
    def _save_products(self, products: List[Dict[str, Any]]) -> int:
        """Save products to database."""
        saved_count = 0
        
        for product_data in products:
            try:
                result = self.db_manager.save_product(product_data)
                if result:
                    saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save product: {e}")
                continue
        
        return saved_count
    
    def _save_raw_data(self, data: List[Dict[str, Any]], output_dir: str, source: str):
        """Save raw scraped data to file."""
        try:
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{source}_raw_{timestamp}.json"
            file_path = output_path / filename
            
            # Save data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Raw data saved to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save raw data: {e}")
    
    def get_scraper_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        try:
            stats = self.db_manager.get_product_stats()
            stats['available_scrapers'] = list(self.scraper_classes.keys())
            stats['enabled_sources'] = [
                source for source in ['amazon', 'ebay', 'walmart']
                if self._is_source_enabled(source)
            ]
            return stats
        except Exception as e:
            logger.error(f"Failed to get scraper stats: {e}")
            return {}
    
    def test_scraper(self, source: str, keyword: str = "laptop") -> Dict[str, Any]:
        """
        Test scraper functionality with a simple search.
        
        Args:
            source: Source to test (amazon, ebay, walmart)
            keyword: Test keyword
            
        Returns:
            Test results dictionary
        """
        logger.info(f"Testing {source} scraper with keyword: {keyword}")
        
        if not self._is_source_enabled(source):
            return {
                'success': False,
                'error': f'Source {source} is not enabled',
                'products_found': 0
            }
        
        try:
            scraper_class = self.scraper_classes['static']
            scraper = scraper_class(source, self.config)
            
            # Test with just 1 page
            result = scraper.scrape(
                keywords=[keyword],
                max_pages=1
            )
            products = result.data if result.success else []
            
            return {
                'success': True,
                'source': source,
                'keyword': keyword,
                'products_found': len(products) if products else 0,
                'sample_product': products[0] if products else None
            }
            
        except Exception as e:
            logger.error(f"Scraper test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'products_found': 0
            } 