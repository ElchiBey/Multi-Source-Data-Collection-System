"""
Scraping Manager Module

This module coordinates different scrapers and manages the overall scraping workflow.
"""

import logging
import asyncio
import concurrent.futures
import threading
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import time

from .static_scraper import StaticScraper
from .selenium_scraper import SeleniumScraper
from .scrapy_spider import ScrapyScraper
from ..data.database import DatabaseManager
from ..data.processors import DataProcessor
from ..utils.logger import setup_logger
from ..utils.concurrent_manager import ConcurrentScrapingManager
from ..utils.parallel_selenium_manager import ParallelSeleniumManager

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
            'selenium': SeleniumScraper,
            'scrapy': ScrapyScraper,
        }
        
        # Initialize parallel processing managers
        self.concurrent_manager = ConcurrentScrapingManager(config)
        self.parallel_selenium_manager = ParallelSeleniumManager(config, max_browsers=4)
        
        logger.info("ScrapingManager initialized with parallel processing capabilities")
    
    def scrape_all_parallel(
        self,
        sources: List[str],
        keywords: List[str],
        max_pages: int = 5,
        output_dir: str = 'data_output/raw',
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        🚀 HIGH-PERFORMANCE parallel scraping using both BeautifulSoup4 and Selenium.
        
        This method maximizes performance by:
        - Running static scrapers in parallel for fast content
        - Using parallel Selenium browsers for dynamic content  
        - Intelligently distributing tasks across scraper types
        - Concurrent processing across all sources and keywords
        
        Args:
            sources: List of source names (amazon, ebay, walmart)
            keywords: List of search keywords
            max_pages: Maximum pages to scrape per source
            output_dir: Directory to save raw data
            use_hybrid: Use both static and selenium scrapers simultaneously
            
        Returns:
            List of scraped product dictionaries
        """
        logger.info(f"🚀 Starting HIGH-PERFORMANCE parallel scraping")
        logger.info(f"📊 Sources: {sources}, Keywords: {keywords}, Pages: {max_pages}")
        logger.info(f"⚡ Hybrid mode: {'ENABLED' if use_hybrid else 'DISABLED'}")
        
        start_time = time.time()
        all_results = []
        
        try:
            if use_hybrid:
                # 🔥 HYBRID MODE: Use both static and selenium in parallel
                all_results = self._execute_hybrid_parallel_scraping(
                    sources, keywords, max_pages, output_dir
                )
            else:
                # Standard parallel using one scraper type
                all_results = self._execute_single_type_parallel(
                    sources, keywords, max_pages, output_dir, 'static'
                )
            
            execution_time = time.time() - start_time
            
            logger.info(f"🎉 HIGH-PERFORMANCE scraping completed!")
            logger.info(f"📊 Total products: {len(all_results)}")
            logger.info(f"⏱️ Execution time: {execution_time:.2f}s")
            logger.info(f"🚀 Performance: {len(all_results)/execution_time:.1f} products/second")
            
            return all_results
            
        except Exception as e:
            logger.error(f"❌ Parallel scraping failed: {e}")
            raise
    
    def _execute_hybrid_parallel_scraping(
        self,
        sources: List[str],
        keywords: List[str],
        max_pages: int,
        output_dir: str
    ) -> List[Dict[str, Any]]:
        """
        🔥 Execute hybrid parallel scraping using both static and selenium.
        
        Strategy:
        1. Static scrapers handle easy targets (eBay, Walmart) 
        2. Selenium handles dynamic content (Amazon, complex pages)
        3. Both run in parallel for maximum speed
        """
        logger.info("🔥 Executing HYBRID parallel scraping strategy")
        
        # Categorize sources by scraping difficulty
        easy_sources = ['ebay', 'walmart']  # Good for static scraping
        dynamic_sources = ['amazon']        # Need selenium for best results
        
        static_sources = [s for s in sources if s in easy_sources]
        selenium_sources = [s for s in sources if s in dynamic_sources]
        
        logger.info(f"📊 Static sources: {static_sources}")
        logger.info(f"🌐 Selenium sources: {selenium_sources}")
        
        # Run both scraper types in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_type = {}
            
            # Submit static scraping tasks
            if static_sources:
                future_static = executor.submit(
                    self._execute_concurrent_static_scraping,
                    static_sources, keywords, max_pages, output_dir
                )
                future_to_type[future_static] = 'static'
            
            # Submit selenium scraping tasks  
            if selenium_sources:
                future_selenium = executor.submit(
                    self._execute_selenium_parallel_scraping,
                    selenium_sources, keywords, max_pages, output_dir
                )
                future_to_type[future_selenium] = 'selenium'
            
            # Collect results from both scraper types
            all_results = []
            for future in concurrent.futures.as_completed(future_to_type):
                scraper_type = future_to_type[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    logger.info(f"✅ {scraper_type.capitalize()} scraping completed: {len(results)} products")
                except Exception as e:
                    logger.error(f"❌ {scraper_type.capitalize()} scraping failed: {e}")
        
        return all_results
    
    def _execute_concurrent_static_scraping(
        self,
        sources: List[str],
        keywords: List[str],
        max_pages: int,
        output_dir: str
    ) -> List[Dict[str, Any]]:
        """Execute static scraping with maximum concurrency."""
        logger.info(f"⚡ Executing concurrent static scraping: {sources}")
        
        all_results = []
        
        # Create task list for concurrent execution
        tasks = []
        for source in sources:
            for keyword in keywords:
                for page in range(1, max_pages + 1):
                    tasks.append({
                        'source': source,
                        'keyword': keyword,
                        'page': page,
                        'scraper_type': 'static'
                    })
        
        logger.info(f"📋 Generated {len(tasks)} static scraping tasks")
        
        # Execute tasks concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_task = {
                executor.submit(self._execute_single_static_task, task): task
                for task in tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    if result and result.get('products'):
                        all_results.extend(result['products'])
                        
                        # Save data incrementally
                        self._save_incremental_data(
                            result['products'], 
                            output_dir, 
                            task['source'],
                            'static'
                        )
                        
                except Exception as e:
                    logger.warning(f"⚠️ Static task failed {task['source']}/{task['keyword']}: {e}")
        
        return all_results
    
    def _execute_selenium_parallel_scraping(
        self,
        sources: List[str],
        keywords: List[str],
        max_pages: int,
        output_dir: str
    ) -> List[Dict[str, Any]]:
        """Execute selenium scraping using parallel selenium manager."""
        logger.info(f"🌐 Executing parallel Selenium scraping: {sources}")
        
        try:
            # Use the parallel selenium manager for maximum efficiency
            selenium_results = self.parallel_selenium_manager.execute_parallel_scraping(
                sources=sources,
                keywords=keywords,
                max_pages=max_pages,
                target_products=1000
            )
            
            products = []
            if selenium_results.get('success') and selenium_results.get('results'):
                for result in selenium_results['results']:
                    if result.success and result.data:
                        products.extend(result.data)
            
            logger.info(f"🌐 Selenium parallel scraping completed: {len(products)} products")
            return products
            
        except Exception as e:
            logger.error(f"❌ Selenium parallel scraping failed: {e}")
            return []
    
    def _execute_single_static_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single static scraping task."""
        try:
            source = task['source']
            keyword = task['keyword']
            page = task['page']
            
            # Create static scraper for this task
            scraper = StaticScraper(source, self.config)
            
            # Scrape single page
            result = scraper.scrape(
                keywords=[keyword],
                max_pages=1,
                start_page=page
            )
            
            products = result.data if result.success else []
            
            return {
                'success': result.success,
                'products': products,
                'source': source,
                'keyword': keyword,
                'page': page
            }
            
        except Exception as e:
            logger.error(f"Static task execution failed: {e}")
            return {'success': False, 'products': []}
    
    def _save_incremental_data(
        self,
        products: List[Dict[str, Any]],
        output_dir: str,
        source: str,
        scraper_type: str
    ):
        """Save data incrementally during parallel processing."""
        if not products:
            return
        
        try:
            # Process data
            processed_products = self.data_processor.process_scraped_data(products)
            
            # Save to database
            saved_count = self._save_products(processed_products)
            
            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{source}_{scraper_type}_parallel_{timestamp}.json"
            
            output_path = Path(output_dir) / 'parallel' 
            output_path.mkdir(parents=True, exist_ok=True)
            
            file_path = output_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Saved {saved_count} products to DB and {len(products)} to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save incremental data: {e}")
    
    def _execute_single_type_parallel(
        self,
        sources: List[str],
        keywords: List[str],
        max_pages: int,
        output_dir: str,
        scraper_type: str
    ) -> List[Dict[str, Any]]:
        """Execute parallel scraping using single scraper type."""
        if scraper_type == 'selenium':
            return self._execute_selenium_parallel_scraping(
                sources, keywords, max_pages, output_dir
            )
        else:
            return self._execute_concurrent_static_scraping(
                sources, keywords, max_pages, output_dir
            )

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
        output_dir: str = 'data_output/raw',
        scraper_type: str = 'static'
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
        session_id = self._create_scraping_session(sources, keywords, max_pages, scraper_type)
        
        try:
            # Scrape each source
            for source in sources:
                if not self._is_source_enabled(source):
                    logger.warning(f"Source {source} is disabled, skipping...")
                    continue
                
                logger.info(f"Scraping {source}...")
                
                try:
                    # Create scraper instance for this source
                    scraper_class = self.scraper_classes.get(scraper_type, self.scraper_classes['static'])
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
    
    def _create_scraping_session(self, sources: List[str], keywords: List[str], max_pages: int, scraper_type: str = 'static') -> str:
        """Create a new scraping session."""
        try:
            session = self.db_manager.create_scraping_session(
                source=','.join(sources),
                keywords=keywords,
                config={
                    'max_pages': max_pages,
                    'sources': sources,
                    'scraper_type': scraper_type
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