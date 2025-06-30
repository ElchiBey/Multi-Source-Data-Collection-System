"""
Smart Scraping Strategy - Prevention over Reaction

This module implements intelligent scraping strategies that PREVENT CAPTCHAs
rather than trying to bypass them after detection.
"""

import time
import random
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class SourceStrategy:
    """Strategy configuration for a specific source."""
    name: str
    scraper_type: str  # 'static', 'selenium'
    delay_min: float
    delay_max: float
    max_pages_per_session: int
    session_cooldown: int  # seconds
    success_rate: float
    last_used: Optional[datetime] = None
    consecutive_failures: int = 0

class SmartScrapingStrategy:
    """
    Smart scraping strategy that prevents CAPTCHAs through intelligent behavior.
    
    Key principles:
    1. Use static scraping when possible (faster, less detectable)
    2. Implement smart delays and rate limiting
    3. Rotate between sources intelligently
    4. Monitor success rates and adapt
    5. Use existing data when available
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SmartStrategy")
        
        # Define source strategies based on real-world testing
        self.source_strategies = {
            'walmart': SourceStrategy(
                name='walmart',
                scraper_type='static',
                delay_min=1.5,
                delay_max=3.0,
                max_pages_per_session=3,
                session_cooldown=30,
                success_rate=0.8
            ),
            'amazon': SourceStrategy(
                name='amazon',
                scraper_type='static',  # Try static first
                delay_min=2.0,
                delay_max=4.0,
                max_pages_per_session=2,
                session_cooldown=45,
                success_rate=0.6
            ),
            'ebay': SourceStrategy(
                name='ebay',
                scraper_type='selenium',  # Needs selenium but very slow
                delay_min=5.0,
                delay_max=10.0,
                max_pages_per_session=1,
                session_cooldown=120,
                success_rate=0.2  # Very low due to strong protection
            )
        }
        
        # Priority order for sources (easiest first)
        self.source_priority = ['walmart', 'amazon', 'ebay']
    
    def get_recommended_approach(self, target_records: int = 100) -> Dict[str, Any]:
        """
        Get the best approach for collecting target records quickly.
        
        Args:
            target_records: Desired number of records
            
        Returns:
            Recommended strategy configuration
        """
        # Check existing data first
        try:
            from src.data.database import DatabaseManager
            db = DatabaseManager()
            stats = db.get_product_stats()
            existing_records = stats.get('total_products', 0)
            
            if existing_records >= target_records:
                return {
                    'approach': 'use_existing_data',
                    'message': f'✅ You already have {existing_records:,} records! Use reports/export commands.',
                    'existing_records': existing_records,
                    'commands': [
                        'python main.py report --type summary',
                        'python main.py export --format csv',
                        'python main.py generate-report --format html'
                    ]
                }
        except Exception as e:
            self.logger.debug(f"Could not check existing data: {e}")
        
        # Calculate optimal strategy for new data collection
        needed_records = target_records
        
        if needed_records <= 50:
            return self._quick_collection_strategy(needed_records)
        elif needed_records <= 500:
            return self._moderate_collection_strategy(needed_records)
        else:
            return self._large_collection_strategy(needed_records)
    
    def _quick_collection_strategy(self, target: int) -> Dict[str, Any]:
        """Strategy for quick collection (≤50 records)."""
        return {
            'approach': 'quick_static',
            'message': f'🚀 Quick collection strategy for {target} records',
            'estimated_time': '30-60 seconds',
            'success_probability': 0.9,
            'recommended_command': f'python main.py scrape --keywords "laptop,phone" --sources walmart --scraper-type static --max-pages 2',
            'sources': ['walmart'],
            'scraper_type': 'static',
            'keywords': ['laptop', 'phone', 'tablet'],
            'max_pages': 2,
            'tips': [
                'Use static scraping for speed',
                'Target Walmart (easiest source)',
                'Use common keywords with high results'
            ]
        }
    
    def _moderate_collection_strategy(self, target: int) -> Dict[str, Any]:
        """Strategy for moderate collection (50-500 records)."""
        return {
            'approach': 'multi_source_static',
            'message': f'⚡ Multi-source strategy for {target} records',
            'estimated_time': '2-5 minutes',
            'success_probability': 0.8,
            'recommended_command': f'python main.py scrape --keywords "laptop,phone,tablet" --sources walmart,amazon --scraper-type static --max-pages 3',
            'sources': ['walmart', 'amazon'],
            'scraper_type': 'static',
            'keywords': ['laptop', 'phone', 'tablet', 'headphones', 'monitor'],
            'max_pages': 3,
            'tips': [
                'Use multiple sources for variety',
                'Still use static scraping for speed',
                'More keywords = more results'
            ]
        }
    
    def _large_collection_strategy(self, target: int) -> Dict[str, Any]:
        """Strategy for large collection (>500 records)."""
        return {
            'approach': 'turbo_mode',
            'message': f'🏎️ TURBO mode for {target} records',
            'estimated_time': '5-15 minutes',
            'success_probability': 0.7,
            'recommended_command': f'python main.py turbo --target {target} --workers 6 --batch-size 8',
            'alternative_command': f'python main.py scrape-parallel --sources walmart,amazon --keywords "laptop,phone,tablet,headphones,monitor" --max-pages 4',
            'tips': [
                'Use TURBO mode for best performance',
                'Parallel processing for speed',
                'Expect some anti-bot blocks (normal)',
                'Focus on working sources'
            ]
        }
    
    def optimize_scraping_session(self, source: str, keywords: List[str]) -> Dict[str, Any]:
        """
        Optimize a scraping session to minimize CAPTCHA risk.
        
        Args:
            source: Target source name
            keywords: List of keywords to search
            
        Returns:
            Optimized session configuration
        """
        if source not in self.source_strategies:
            source = 'walmart'  # Default to easiest
        
        strategy = self.source_strategies[source]
        
        # Check if source needs cooldown
        if strategy.last_used:
            time_since_last = (datetime.now() - strategy.last_used).seconds
            if time_since_last < strategy.session_cooldown:
                cooldown_remaining = strategy.session_cooldown - time_since_last
                return {
                    'action': 'wait',
                    'message': f'⏳ {source} needs {cooldown_remaining}s cooldown to avoid detection',
                    'wait_time': cooldown_remaining,
                    'alternative_sources': [s for s in self.source_priority if s != source]
                }
        
        # Calculate optimal session parameters
        session_config = {
            'source': source,
            'scraper_type': strategy.scraper_type,
            'keywords': keywords[:3],  # Limit keywords to avoid overload
            'max_pages': min(strategy.max_pages_per_session, 3),
            'delay_between_requests': random.uniform(strategy.delay_min, strategy.delay_max),
            'expected_success_rate': strategy.success_rate,
            'session_duration_estimate': self._estimate_session_duration(strategy, len(keywords)),
            'anti_detection_measures': self._get_anti_detection_measures(source)
        }
        
        return session_config
    
    def _estimate_session_duration(self, strategy: SourceStrategy, keyword_count: int) -> float:
        """Estimate session duration in seconds."""
        avg_delay = (strategy.delay_min + strategy.delay_max) / 2
        pages_per_keyword = strategy.max_pages_per_session
        
        base_time = keyword_count * pages_per_keyword * avg_delay
        
        # Add overhead for page loading, processing, etc.
        if strategy.scraper_type == 'selenium':
            overhead_multiplier = 3.0  # Selenium is much slower
        else:
            overhead_multiplier = 1.5  # Static scraping overhead
        
        return base_time * overhead_multiplier
    
    def _get_anti_detection_measures(self, source: str) -> List[str]:
        """Get recommended anti-detection measures for source."""
        base_measures = [
            'Random delays between requests',
            'Human-like user agent',
            'Proper request headers'
        ]
        
        if source == 'ebay':
            base_measures.extend([
                'Longer delays (5-10s)',
                'Session rotation',
                'Limited pages per session'
            ])
        elif source == 'amazon':
            base_measures.extend([
                'Medium delays (2-4s)',
                'Avoid rapid pagination'
            ])
        else:  # walmart
            base_measures.extend([
                'Standard delays (1.5-3s)',
                'Multiple keywords OK'
            ])
        
        return base_measures
    
    def get_fast_data_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for getting data quickly and reliably."""
        return {
            'immediate_options': {
                'existing_data': {
                    'command': 'python main.py report --type summary',
                    'description': '📊 View your existing 12,000+ records instantly',
                    'time': '< 5 seconds'
                },
                'quick_export': {
                    'command': 'python main.py export --format csv',
                    'description': '📁 Export existing data to CSV',
                    'time': '< 10 seconds'
                },
                'html_report': {
                    'command': 'python main.py generate-report --format html',
                    'description': '📈 Beautiful HTML report with charts',
                    'time': '< 15 seconds'
                }
            },
            'fast_new_data': {
                'walmart_static': {
                    'command': 'python main.py scrape --keywords "laptop" --sources walmart --scraper-type static --max-pages 2',
                    'description': '🚀 Fast static scraping from Walmart',
                    'time': '30-60 seconds',
                    'expected_results': '20-50 products'
                },
                'multi_source': {
                    'command': 'python main.py scrape --keywords "laptop,phone" --sources walmart,amazon --scraper-type static --max-pages 2',
                    'description': '⚡ Multiple sources with static scraping',
                    'time': '1-2 minutes',
                    'expected_results': '40-100 products'
                }
            },
            'avoid': {
                'ebay_selenium': {
                    'reason': '🐌 Very slow (4+ minutes) with high CAPTCHA risk',
                    'alternative': 'Use existing data or focus on Walmart/Amazon'
                },
                'large_selenium_sessions': {
                    'reason': '🛡️ Triggers strong anti-bot protection',
                    'alternative': 'Use static scraping or smaller batches'
                }
            }
        }

# Convenience functions for quick access
def get_quick_recommendations(target_records: int = 100) -> Dict[str, Any]:
    """Get quick recommendations for data collection."""
    strategy = SmartScrapingStrategy({})
    return strategy.get_recommended_approach(target_records)

def get_fast_data_commands() -> List[str]:
    """Get list of fast commands that work reliably."""
    return [
        # Instant (use existing data)
        'python main.py report --type summary',
        'python main.py export --format csv', 
        'python main.py generate-report --format html',
        
        # Fast new data (30-120 seconds)
        'python main.py scrape --keywords "laptop" --sources walmart --scraper-type static --max-pages 2',
        'python main.py scrape --keywords "laptop,phone" --sources walmart,amazon --scraper-type static --max-pages 2',
        'python main.py turbo --target 100 --workers 4 --batch-size 6'
    ]

def show_performance_comparison() -> Dict[str, Dict[str, Any]]:
    """Show performance comparison of different approaches."""
    return {
        'existing_data': {
            'time': '< 5 seconds',
            'success_rate': '100%',
            'records': '12,000+',
            'recommendation': '⭐⭐⭐⭐⭐ BEST for demos/reports'
        },
        'static_walmart': {
            'time': '30-60 seconds', 
            'success_rate': '90%',
            'records': '20-50',
            'recommendation': '⭐⭐⭐⭐ BEST for new data'
        },
        'static_multi_source': {
            'time': '1-2 minutes',
            'success_rate': '80%',
            'records': '50-100',
            'recommendation': '⭐⭐⭐ Good for variety'
        },
        'turbo_mode': {
            'time': '2-5 minutes',
            'success_rate': '70%',
            'records': '100-500',
            'recommendation': '⭐⭐⭐ Good for large collections'
        },
        'selenium_ebay': {
            'time': '4+ minutes',
            'success_rate': '20%',
            'records': '0-10',
            'recommendation': '⭐ AVOID - Too slow/unreliable'
        }
    } 