"""
🚀 Parallel Selenium Manager with Anti-Bot Protection

This module implements high-speed parallel Selenium scraping with advanced
anti-bot protection across multiple browser instances simultaneously.
"""

import asyncio
import time
import random
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import queue
from dataclasses import dataclass
import json

from ..scrapers.selenium_scraper import AdvancedSeleniumScraper
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ScrapingTask:
    """Individual scraping task for parallel execution."""
    source: str
    keyword: str
    page: int
    scraper_type: str = 'selenium'
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class ParallelResult:
    """Result from parallel scraping operation."""
    task: ScrapingTask
    success: bool
    data: List[Dict[str, Any]]
    execution_time: float
    error: Optional[str] = None
    browser_id: Optional[str] = None

class ParallelSeleniumManager:
    """
    🚀 High-speed parallel Selenium manager with anti-bot protection.
    
    Features:
    - Multiple browser instances running concurrently
    - Advanced anti-bot protection for each instance
    - Intelligent load balancing and task distribution
    - Real-time progress tracking and statistics
    - Automatic retry and error handling
    - Resource management and cleanup
    """
    
    def __init__(self, config: Dict[str, Any], max_browsers: int = 4):
        """
        Initialize parallel Selenium manager.
        
        Args:
            config: Application configuration
            max_browsers: Maximum number of concurrent browser instances
        """
        self.config = config
        self.max_browsers = min(max_browsers, 8)  # Reasonable limit
        self.active_browsers = {}
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_products': 0,
            'avg_speed': 0.0,
            'start_time': None,
            'active_threads': 0
        }
        self.shutdown_event = threading.Event()
        self.lock = threading.Lock()
        
        logger.info(f"🚀 ParallelSeleniumManager initialized with {self.max_browsers} browsers")
    
    def execute_parallel_scraping(
        self,
        sources: List[str],
        keywords: List[str],
        max_pages: int = 3,
        target_products: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute high-speed parallel scraping across multiple sources.
        
        Args:
            sources: List of sources to scrape
            keywords: List of keywords to search
            max_pages: Maximum pages per keyword
            target_products: Target number of products
            
        Returns:
            Comprehensive results dictionary
        """
        logger.info(f"🚀 Starting parallel scraping: {len(sources)} sources, {len(keywords)} keywords")
        
        # Reset stats
        self.stats['start_time'] = time.time()
        self.stats['tasks_completed'] = 0
        self.stats['tasks_failed'] = 0
        self.stats['total_products'] = 0
        
        # Generate tasks
        tasks = self._generate_tasks(sources, keywords, max_pages)
        logger.info(f"📋 Generated {len(tasks)} scraping tasks")
        
        # Add tasks to queue
        for task in tasks:
            self.task_queue.put(task)
        
        # Start parallel execution
        results = self._execute_parallel_workers()
        
        # Generate final report
        execution_time = time.time() - self.stats['start_time']
        
        # Save results to files by source
        saved_files = self._save_results_to_files(results)
        
        return {
            'success': True,
            'execution_time': execution_time,
            'tasks_completed': self.stats['tasks_completed'],
            'tasks_failed': self.stats['tasks_failed'],
            'total_products': self.stats['total_products'],
            'products_per_second': self.stats['total_products'] / execution_time if execution_time > 0 else 0,
            'results': results,
            'browsers_used': len(self.active_browsers),
            'target_achieved': self.stats['total_products'] >= target_products,
            'saved_files': saved_files
        }
    
    def _generate_tasks(
        self,
        sources: List[str],
        keywords: List[str],
        max_pages: int
    ) -> List[ScrapingTask]:
        """Generate optimized task list for parallel execution."""
        tasks = []
        
        # Smart task generation - interleave sources and keywords for better distribution
        for page in range(1, max_pages + 1):
            for i, keyword in enumerate(keywords):
                for j, source in enumerate(sources):
                    # Calculate priority based on success probability
                    priority = self._calculate_task_priority(source, keyword, page)
                    
                    task = ScrapingTask(
                        source=source,
                        keyword=keyword,
                        page=page,
                        priority=priority
                    )
                    tasks.append(task)
        
        # Sort by priority (higher priority first)
        tasks.sort(key=lambda x: x.priority, reverse=True)
        
        return tasks
    
    def _calculate_task_priority(self, source: str, keyword: str, page: int) -> int:
        """Calculate task priority based on success probability."""
        base_priority = 100
        
        # Page penalty (earlier pages are more likely to succeed)
        page_penalty = (page - 1) * 10
        
        # Source reliability (eBay typically easier than Amazon)
        source_bonus = {
            'ebay': 20,
            'walmart': 10,
            'amazon': 0  # Hardest, so lowest bonus
        }.get(source, 5)
        
        # Keyword popularity (common keywords might be harder)
        common_keywords = ['laptop', 'phone', 'computer', 'tablet']
        keyword_penalty = 15 if keyword.lower() in common_keywords else 0
        
        return max(1, base_priority + source_bonus - page_penalty - keyword_penalty)
    
    def _execute_parallel_workers(self) -> List[ParallelResult]:
        """Execute tasks using parallel worker threads."""
        results = []
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=self.max_browsers, thread_name_prefix="SeleniumWorker") as executor:
            # Submit worker threads
            future_to_worker = {}
            for worker_id in range(self.max_browsers):
                future = executor.submit(self._worker_thread, worker_id)
                future_to_worker[future] = worker_id
            
            # Monitor progress and collect results
            logger.info(f"⚡ Started {self.max_browsers} parallel workers")
            
            # Wait for completion or early termination
            completed_tasks = 0
            while completed_tasks < self.task_queue.qsize() and not self.shutdown_event.is_set():
                try:
                    # Get result with timeout
                    result = self.result_queue.get(timeout=1.0)
                    results.append(result)
                    completed_tasks += 1
                    
                    # Update stats
                    with self.lock:
                        if result.success:
                            self.stats['tasks_completed'] += 1
                            self.stats['total_products'] += len(result.data)
                        else:
                            self.stats['tasks_failed'] += 1
                    
                    # Log progress
                    if completed_tasks % 5 == 0:
                        self._log_progress(completed_tasks)
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error collecting results: {e}")
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Wait for workers to finish
            for future in as_completed(future_to_worker.keys(), timeout=30):
                worker_id = future_to_worker[future]
                try:
                    future.result()
                    logger.debug(f"Worker {worker_id} completed")
                except Exception as e:
                    logger.error(f"Worker {worker_id} failed: {e}")
        
        # Cleanup browsers
        self._cleanup_browsers()
        
        return results
    
    def _worker_thread(self, worker_id: int) -> None:
        """Individual worker thread that processes tasks."""
        logger.info(f"🤖 Worker {worker_id} started")
        
        browser = None
        processed_tasks = 0
        
        try:
            # Initialize browser for this worker
            browser = self._create_worker_browser(worker_id)
            
            while not self.shutdown_event.is_set():
                try:
                    # Get next task
                    task = self.task_queue.get(timeout=2.0)
                    
                    # Process task
                    result = self._process_task(browser, task, worker_id)
                    
                    # Add result to queue
                    self.result_queue.put(result)
                    processed_tasks += 1
                    
                    # Mark task as done
                    self.task_queue.task_done()
                    
                    # Small delay to prevent overwhelming
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except queue.Empty:
                    # No more tasks, continue checking
                    continue
                except Exception as e:
                    logger.error(f"Worker {worker_id} task error: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Worker {worker_id} fatal error: {e}")
        
        finally:
            # Cleanup browser
            if browser:
                try:
                    browser.close()
                    logger.debug(f"🤖 Worker {worker_id} browser closed")
                except Exception as e:
                    logger.error(f"Error closing browser for worker {worker_id}: {e}")
            
            logger.info(f"🤖 Worker {worker_id} finished (processed {processed_tasks} tasks)")
    
    def _create_worker_browser(self, worker_id: int) -> AdvancedSeleniumScraper:
        """Create a browser instance for a worker thread."""
        try:
            # Create unique config for this worker
            worker_config = self.config.copy()
            
            # Add worker-specific randomization
            worker_config['worker_id'] = worker_id
            worker_config['user_agent_seed'] = worker_id  # For consistent but different UAs
            
            # Create scraper instance
            browser = AdvancedSeleniumScraper('amazon', worker_config)  # Default to amazon
            
            # Store in active browsers
            with self.lock:
                self.active_browsers[worker_id] = browser
            
            logger.debug(f"✅ Browser created for worker {worker_id}")
            return browser
            
        except Exception as e:
            logger.error(f"Failed to create browser for worker {worker_id}: {e}")
            raise
    
    def _process_task(self, browser: AdvancedSeleniumScraper, task: ScrapingTask, worker_id: int) -> ParallelResult:
        """Process a single scraping task."""
        start_time = time.time()
        
        try:
            # Update browser source if needed
            if browser.source != task.source:
                browser.source = task.source
                browser._load_source_config()
            
            # Execute scraping
            result = browser.scrape(
                keywords=[task.keyword],
                max_pages=1  # Single page per task for parallelism
            )
            
            execution_time = time.time() - start_time
            
            if result.success and result.data:
                logger.debug(f"✅ Worker {worker_id}: {len(result.data)} products from {task.source}")
                return ParallelResult(
                    task=task,
                    success=True,
                    data=result.data,
                    execution_time=execution_time,
                    browser_id=f"worker_{worker_id}"
                )
            else:
                logger.debug(f"⚠️ Worker {worker_id}: No products from {task.source}")
                return ParallelResult(
                    task=task,
                    success=False,
                    data=[],
                    execution_time=execution_time,
                    error="No products found",
                    browser_id=f"worker_{worker_id}"
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Worker {worker_id} task failed: {e}")
            
            # Check if task should be retried
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                # Re-add to queue for retry
                self.task_queue.put(task)
                logger.info(f"🔄 Retrying task (attempt {task.retry_count}/{task.max_retries})")
            
            return ParallelResult(
                task=task,
                success=False,
                data=[],
                execution_time=execution_time,
                error=str(e),
                browser_id=f"worker_{worker_id}"
            )
    
    def _log_progress(self, completed_tasks: int) -> None:
        """Log current progress statistics."""
        elapsed = time.time() - self.stats['start_time']
        products_per_sec = self.stats['total_products'] / elapsed if elapsed > 0 else 0
        
        logger.info(
            f"📊 Progress: {completed_tasks} tasks | "
            f"{self.stats['total_products']} products | "
            f"{products_per_sec:.1f} products/sec | "
            f"{len(self.active_browsers)} browsers active"
        )
    
    def _cleanup_browsers(self) -> None:
        """Clean up all browser instances."""
        logger.info("🧹 Cleaning up browser instances...")
        
        with self.lock:
            for worker_id, browser in self.active_browsers.items():
                try:
                    browser.close()
                    logger.debug(f"Closed browser for worker {worker_id}")
                except Exception as e:
                    logger.error(f"Error closing browser {worker_id}: {e}")
            
            self.active_browsers.clear()
        
        logger.info("✅ Browser cleanup completed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        
        return {
            'elapsed_time': elapsed,
            'tasks_completed': self.stats['tasks_completed'],
            'tasks_failed': self.stats['tasks_failed'],
            'total_products': self.stats['total_products'],
            'products_per_second': self.stats['total_products'] / elapsed if elapsed > 0 else 0,
            'active_browsers': len(self.active_browsers),
            'success_rate': (
                self.stats['tasks_completed'] / 
                (self.stats['tasks_completed'] + self.stats['tasks_failed'])
            ) if (self.stats['tasks_completed'] + self.stats['tasks_failed']) > 0 else 0
        }
    
    def shutdown(self) -> None:
        """Gracefully shutdown the parallel manager."""
        logger.info("🛑 Shutting down parallel Selenium manager...")
        self.shutdown_event.set()
        self._cleanup_browsers()
        logger.info("✅ Parallel manager shutdown completed")
    
    def _save_results_to_files(self, results: List[ParallelResult]) -> Dict[str, str]:
        """Save scraping results to JSON files by source."""
        saved_files = {}
        
        try:
            # Group results by source
            source_data = {}
            for result in results:
                if result.success and result.data:
                    source = result.task.source
                    if source not in source_data:
                        source_data[source] = []
                    source_data[source].extend(result.data)
            
            # Create output directory
            output_dir = Path("data_output/selenium_parallel")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save each source to separate file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for source, products in source_data.items():
                if products:  # Only save if we have data
                    filename = f"{source}_selenium_parallel_{timestamp}.json"
                    filepath = output_dir / filename
                    
                    # Add metadata
                    output_data = {
                        'metadata': {
                            'source': source,
                            'scraper_type': 'selenium_parallel',
                            'timestamp': timestamp,
                            'total_products': len(products),
                            'extraction_method': 'parallel_browsers'
                        },
                        'products': products
                    }
                    
                    # Save to file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
                    
                    saved_files[source] = str(filepath)
                    logger.info(f"💾 Saved {len(products)} {source} products to {filename}")
            
            # Save combined file
            if source_data:
                all_products = []
                for products in source_data.values():
                    all_products.extend(products)
                
                combined_filename = f"combined_selenium_parallel_{timestamp}.json"
                combined_filepath = output_dir / combined_filename
                
                combined_data = {
                    'metadata': {
                        'scraper_type': 'selenium_parallel',
                        'timestamp': timestamp,
                        'total_products': len(all_products),
                        'sources': list(source_data.keys()),
                        'extraction_method': 'parallel_browsers'
                    },
                    'products': all_products
                }
                
                with open(combined_filepath, 'w', encoding='utf-8') as f:
                    json.dump(combined_data, f, indent=2, ensure_ascii=False, default=str)
                
                saved_files['combined'] = str(combined_filepath)
                logger.info(f"💾 Saved {len(all_products)} combined products to {combined_filename}")
        
        except Exception as e:
            logger.error(f"Failed to save results to files: {e}")
        
        return saved_files 