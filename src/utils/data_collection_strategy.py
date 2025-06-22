"""
Strategic Data Collection Manager

This module implements a comprehensive strategy to collect 5,000+ product records
using multiple approaches: different sources, keywords, scraper types, and timing.
"""

import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from pathlib import Path

from ..scrapers.manager import ScrapingManager
from ..utils.concurrent_manager import ConcurrentScrapingManager
from ..data.database import DatabaseManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class DataCollectionStrategy:
    """
    Strategic data collection to reach 5,000+ records.
    
    Uses multiple approaches:
    1. Different e-commerce sources
    2. Varied search keywords
    3. Multiple scraper types
    4. Distributed timing
    5. Fallback strategies
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize strategic collection manager."""
        self.config = config
        self.scraping_manager = ScrapingManager(config)
        self.concurrent_manager = ConcurrentScrapingManager(config)
        self.db_manager = DatabaseManager(config)
        
        # Target and tracking
        self.target_records = 5000
        self.current_records = 0
        self.collection_sessions = []
        
        # Strategic parameters
        self.sources = ['amazon', 'ebay', 'walmart']
        self.keywords = self._get_strategic_keywords()
        self.scraper_types = ['static', 'selenium']
        
    def _get_strategic_keywords(self) -> List[str]:
        """Get diverse keywords for maximum data collection."""
        return [
            # Electronics
            'laptop', 'phone', 'tablet', 'headphones', 'camera',
            'monitor', 'keyboard', 'mouse', 'speaker', 'charger',
            
            # Home & Garden
            'chair', 'table', 'lamp', 'pillow', 'blanket',
            'plant', 'vase', 'curtain', 'rug', 'mirror',
            
            # Fashion
            'shoes', 'shirt', 'jacket', 'bag', 'watch',
            'hat', 'belt', 'sunglasses', 'scarf', 'gloves',
            
            # Sports & Outdoors
            'bike', 'ball', 'tent', 'backpack', 'bottle',
            'fitness', 'yoga', 'running', 'camping', 'hiking',
            
            # Books & Media
            'book', 'game', 'puzzle', 'toy', 'dvd',
            'magazine', 'comic', 'poster', 'album', 'vinyl'
        ]
    
    def execute_comprehensive_collection(self) -> Dict[str, Any]:
        """
        Execute comprehensive data collection strategy.
        
        Returns:
            Collection results and statistics
        """
        logger.info(f"🚀 Starting strategic data collection (target: {self.target_records} records)")
        
        start_time = datetime.now()
        collection_results = {
            'sessions': [],
            'total_records': 0,
            'successful_sessions': 0,
            'failed_sessions': 0,
            'sources_used': set(),
            'keywords_used': set(),
            'start_time': start_time,
            'strategies_used': []
        }
        
        try:
            # Strategy 1: Diverse keyword collection
            logger.info("📈 Strategy 1: Diverse keyword collection")
            strategy1_results = self._execute_diverse_keywords()
            collection_results['sessions'].extend(strategy1_results)
            collection_results['strategies_used'].append('diverse_keywords')
            
            # Check progress
            current_count = self._get_current_record_count()
            logger.info(f"📊 After Strategy 1: {current_count} records")
            
            if current_count < self.target_records:
                # Strategy 2: Multiple sources per keyword
                logger.info("🔄 Strategy 2: Multiple sources per keyword")
                strategy2_results = self._execute_multi_source()
                collection_results['sessions'].extend(strategy2_results)
                collection_results['strategies_used'].append('multi_source')
                
                current_count = self._get_current_record_count()
                logger.info(f"📊 After Strategy 2: {current_count} records")
            
            if current_count < self.target_records:
                # Strategy 3: Deep pagination
                logger.info("📄 Strategy 3: Deep pagination")
                strategy3_results = self._execute_deep_pagination()
                collection_results['sessions'].extend(strategy3_results)
                collection_results['strategies_used'].append('deep_pagination')
                
                current_count = self._get_current_record_count()
                logger.info(f"📊 After Strategy 3: {current_count} records")
            
            if current_count < self.target_records:
                # Strategy 4: Alternative approaches
                logger.info("🔀 Strategy 4: Alternative approaches")
                strategy4_results = self._execute_alternatives()
                collection_results['sessions'].extend(strategy4_results)
                collection_results['strategies_used'].append('alternatives')
            
            # Final statistics
            final_count = self._get_current_record_count()
            collection_results['total_records'] = final_count
            collection_results['end_time'] = datetime.now()
            collection_results['duration'] = collection_results['end_time'] - start_time
            
            # Calculate success metrics
            successful = sum(1 for session in collection_results['sessions'] if session.get('success', False))
            collection_results['successful_sessions'] = successful
            collection_results['failed_sessions'] = len(collection_results['sessions']) - successful
            
            logger.info(f"🎉 Collection completed: {final_count} total records")
            return collection_results
            
        except Exception as e:
            logger.error(f"❌ Strategic collection failed: {e}")
            collection_results['error'] = str(e)
            return collection_results
    
    def _execute_diverse_keywords(self) -> List[Dict[str, Any]]:
        """Execute diverse keyword strategy."""
        sessions = []
        
        # Use top performing keywords with multiple sources
        priority_keywords = self.keywords[:15]  # Top 15 keywords
        
        for keyword in priority_keywords:
            for source in self.sources:
                try:
                    logger.info(f"🔍 Collecting: {keyword} from {source}")
                    
                    session_result = {
                        'strategy': 'diverse_keywords',
                        'keyword': keyword,
                        'source': source,
                        'timestamp': datetime.now()
                    }
                    
                    # Use static scraper with anti-bot protection
                    results = self.scraping_manager.scrape_all(
                        sources=[source],
                        keywords=[keyword],
                        max_pages=3,  # Moderate pagination
                        output_dir='data_output/strategic'
                    )
                    
                    session_result['success'] = True
                    session_result['records_found'] = len(results)
                    sessions.append(session_result)
                    
                    # Anti-bot delay between requests
                    delay = random.uniform(10, 20)  # 10-20 second delays
                    logger.info(f"⏱️ Waiting {delay:.1f}s before next request...")
                    time.sleep(delay)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed {keyword} on {source}: {e}")
                    sessions.append({
                        'strategy': 'diverse_keywords',
                        'keyword': keyword,
                        'source': source,
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now()
                    })
                    
                    # Longer delay after failures
                    time.sleep(random.uniform(15, 25))
        
        return sessions
    
    def _execute_multi_source(self) -> List[Dict[str, Any]]:
        """Execute multi-source strategy for popular keywords."""
        sessions = []
        
        # Focus on most popular keywords across all sources
        popular_keywords = ['laptop', 'phone', 'chair', 'book', 'shoes']
        
        for keyword in popular_keywords:
            try:
                logger.info(f"🌐 Multi-source collection for: {keyword}")
                
                session_result = {
                    'strategy': 'multi_source',
                    'keyword': keyword,
                    'sources': self.sources,
                    'timestamp': datetime.now()
                }
                
                # Collect from all sources for this keyword
                results = self.scraping_manager.scrape_all(
                    sources=self.sources,
                    keywords=[keyword],
                    max_pages=5,  # Deeper pagination for popular items
                    output_dir='data_output/strategic'
                )
                
                session_result['success'] = True
                session_result['records_found'] = len(results)
                sessions.append(session_result)
                
                # Longer delay between multi-source sessions
                delay = random.uniform(30, 45)
                logger.info(f"⏱️ Multi-source delay: {delay:.1f}s...")
                time.sleep(delay)
                
            except Exception as e:
                logger.warning(f"⚠️ Multi-source failed for {keyword}: {e}")
                sessions.append({
                    'strategy': 'multi_source',
                    'keyword': keyword,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now()
                })
        
        return sessions
    
    def _execute_deep_pagination(self) -> List[Dict[str, Any]]:
        """Execute deep pagination strategy."""
        sessions = []
        
        # Use fewer keywords but go deeper in pagination
        deep_keywords = ['laptop', 'phone', 'book']
        
        for keyword in deep_keywords:
            for source in ['ebay', 'walmart']:  # Focus on less restrictive sources
                try:
                    logger.info(f"📄 Deep pagination: {keyword} from {source}")
                    
                    session_result = {
                        'strategy': 'deep_pagination',
                        'keyword': keyword,
                        'source': source,
                        'timestamp': datetime.now()
                    }
                    
                    # Go deeper in pagination
                    results = self.scraping_manager.scrape_all(
                        sources=[source],
                        keywords=[keyword],
                        max_pages=10,  # Deep pagination
                        output_dir='data_output/strategic'
                    )
                    
                    session_result['success'] = True
                    session_result['records_found'] = len(results)
                    sessions.append(session_result)
                    
                    # Extended delay for deep pagination
                    delay = random.uniform(45, 60)
                    logger.info(f"⏱️ Deep pagination delay: {delay:.1f}s...")
                    time.sleep(delay)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Deep pagination failed {keyword} on {source}: {e}")
                    sessions.append({
                        'strategy': 'deep_pagination',
                        'keyword': keyword,
                        'source': source,
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now()
                    })
        
        return sessions
    
    def _execute_alternatives(self) -> List[Dict[str, Any]]:
        """Execute alternative collection strategies."""
        sessions = []
        
        # Alternative approaches if direct scraping is limited
        alternatives = [
            {
                'approach': 'selenium_dynamic',
                'keywords': ['tablet', 'headphones'],
                'sources': ['ebay'],
                'description': 'Use Selenium for dynamic content'
            },
            {
                'approach': 'concurrent_batch',
                'keywords': ['bag', 'watch'],
                'sources': ['walmart'],
                'description': 'Concurrent processing with smaller batches'
            }
        ]
        
        for alt in alternatives:
            try:
                logger.info(f"🔀 Alternative: {alt['description']}")
                
                session_result = {
                    'strategy': 'alternatives',
                    'approach': alt['approach'],
                    'keywords': alt['keywords'],
                    'sources': alt['sources'],
                    'timestamp': datetime.now()
                }
                
                if alt['approach'] == 'selenium_dynamic':
                    # Use Selenium scraper
                    from ..scrapers.selenium_scraper import SeleniumScraper
                    
                    for source in alt['sources']:
                        for keyword in alt['keywords']:
                            selenium_scraper = SeleniumScraper(self.config)
                            result = selenium_scraper.scrape(
                                keywords=[keyword],
                                max_pages=3
                            )
                            
                            if result.success:
                                # Save results manually
                                for product in result.data:
                                    self.db_manager.save_product(product)
                
                elif alt['approach'] == 'concurrent_batch':
                    # Use concurrent processing
                    self.concurrent_manager.add_scraping_tasks(
                        sources=alt['sources'],
                        keywords=alt['keywords'],
                        max_pages=3,
                        scraper_type='static'
                    )
                    
                    # Define worker function
                    def scrape_worker(source, keyword, page, scraper_type):
                        return self.scraping_manager.scrape_all(
                            sources=[source],
                            keywords=[keyword],
                            max_pages=1,
                            output_dir='data_output/strategic'
                        )
                    
                    results = self.concurrent_manager.execute_concurrent_scraping(scrape_worker)
                
                session_result['success'] = True
                session_result['records_found'] = len(results) if 'results' in locals() else 0
                sessions.append(session_result)
                
                # Delay between alternatives
                time.sleep(random.uniform(30, 40))
                
            except Exception as e:
                logger.warning(f"⚠️ Alternative strategy failed: {e}")
                sessions.append({
                    'strategy': 'alternatives',
                    'approach': alt.get('approach', 'unknown'),
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now()
                })
        
        return sessions
    
    def _get_current_record_count(self) -> int:
        """Get current number of records in database."""
        try:
            stats = self.db_manager.get_product_stats()
            return stats.get('total_products', 0)
        except Exception as e:
            logger.error(f"Failed to get record count: {e}")
            return 0
    
    def generate_collection_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive collection report."""
        report_lines = [
            "# Strategic Data Collection Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Collection Summary",
            f"**Target Records**: {self.target_records:,}",
            f"**Records Collected**: {results['total_records']:,}",
            f"**Success Rate**: {(results['total_records']/self.target_records)*100:.1f}%",
            f"**Duration**: {results.get('duration', 'N/A')}",
            "",
            "## Strategies Used",
        ]
        
        for strategy in results.get('strategies_used', []):
            report_lines.append(f"- {strategy.replace('_', ' ').title()}")
        
        report_lines.extend([
            "",
            "## Session Statistics",
            f"**Total Sessions**: {len(results['sessions'])}",
            f"**Successful Sessions**: {results['successful_sessions']}",
            f"**Failed Sessions**: {results['failed_sessions']}",
            ""
        ])
        
        # Save report
        report_path = Path('data_output/reports/collection_strategy_report.md')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"📋 Collection report saved: {report_path}")
        return str(report_path) 