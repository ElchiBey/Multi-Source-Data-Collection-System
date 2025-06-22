"""
Concurrent Processing Manager

This module provides thread-safe concurrent processing capabilities
for multi-source data collection with proper resource management.
"""

import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue, Empty
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

from ..utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ScrapingTask:
    """Data class for scraping tasks."""
    task_id: str
    source: str
    keyword: str
    page: int
    scraper_type: str = 'static'
    priority: int = 1
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class ConcurrentScrapingManager:
    """
    Manages concurrent scraping operations with thread/process pools.
    
    Features:
    - Thread-safe task queue management
    - Resource pooling and cleanup
    - Progress tracking and monitoring
    - Error handling and retry logic
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize concurrent manager."""
        self.config = config
        self.max_workers = config.get('scraping', {}).get('max_workers', 5)
        self.use_multiprocessing = config.get('scraping', {}).get('use_multiprocessing', False)
        
        # Task management
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.active_tasks = {}
        self.completed_tasks = []
        self.failed_tasks = []
        
        # Thread safety
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        
        # Progress tracking
        self.total_tasks = 0
        self.completed_count = 0
        self.failed_count = 0
        
        logger.info(f"Initialized concurrent manager with {self.max_workers} workers")
    
    def add_scraping_tasks(self, sources: List[str], keywords: List[str], 
                          max_pages: int = 5, scraper_type: str = 'static') -> None:
        """
        Add multiple scraping tasks to the queue.
        
        Args:
            sources: List of source websites
            keywords: List of search keywords  
            max_pages: Maximum pages per source/keyword combination
            scraper_type: Type of scraper to use
        """
        task_count = 0
        
        for source in sources:
            for keyword in keywords:
                for page in range(1, max_pages + 1):
                    task_id = f"{source}_{keyword}_{page}_{int(time.time())}"
                    
                    task = ScrapingTask(
                        task_id=task_id,
                        source=source,
                        keyword=keyword,
                        page=page,
                        scraper_type=scraper_type,
                        priority=1 if page <= 2 else 2  # Higher priority for first 2 pages
                    )
                    
                    self.task_queue.put(task)
                    task_count += 1
        
        with self.lock:
            self.total_tasks += task_count
        
        logger.info(f"Added {task_count} scraping tasks to queue")
    
    def execute_concurrent_scraping(self, worker_function: Callable) -> List[Dict[str, Any]]:
        """
        Execute scraping tasks concurrently using thread or process pools.
        
        Args:
            worker_function: Function to execute for each task
            
        Returns:
            List of scraping results
        """
        all_results = []
        
        try:
            if self.use_multiprocessing:
                all_results = self._execute_with_processes(worker_function)
            else:
                all_results = self._execute_with_threads(worker_function)
            
            logger.info(f"Concurrent scraping completed: {len(all_results)} results")
            return all_results
            
        except Exception as e:
            logger.error(f"Error in concurrent scraping execution: {e}")
            return all_results
    
    def _execute_with_threads(self, worker_function: Callable) -> List[Dict[str, Any]]:
        """Execute tasks using ThreadPoolExecutor."""
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {}
            
            while not self.task_queue.empty():
                try:
                    task = self.task_queue.get_nowait()
                    future = executor.submit(self._execute_task, worker_function, task)
                    future_to_task[future] = task
                    
                    with self.lock:
                        self.active_tasks[task.task_id] = task
                        
                except Empty:
                    break
            
            # Process completed tasks
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    
                    if result and result.get('success', False):
                        all_results.extend(result.get('data', []))
                        with self.lock:
                            self.completed_count += 1
                            self.completed_tasks.append(task)
                    else:
                        with self.lock:
                            self.failed_count += 1
                            self.failed_tasks.append(task)
                        logger.warning(f"Task failed: {task.task_id}")
                    
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed with error: {e}")
                    with self.lock:
                        self.failed_count += 1
                        self.failed_tasks.append(task)
                
                finally:
                    with self.lock:
                        if task.task_id in self.active_tasks:
                            del self.active_tasks[task.task_id]
                    
                    # Log progress
                    self._log_progress()
        
        return all_results
    
    def _execute_with_processes(self, worker_function: Callable) -> List[Dict[str, Any]]:
        """Execute tasks using ProcessPoolExecutor."""
        all_results = []
        
        # Convert tasks to list for process execution
        tasks = []
        while not self.task_queue.empty():
            try:
                tasks.append(self.task_queue.get_nowait())
            except Empty:
                break
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._execute_task, worker_function, task): task 
                for task in tasks
            }
            
            # Process results
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                
                try:
                    result = future.result(timeout=300)
                    
                    if result and result.get('success', False):
                        all_results.extend(result.get('data', []))
                        with self.lock:
                            self.completed_count += 1
                    else:
                        with self.lock:
                            self.failed_count += 1
                        logger.warning(f"Process task failed: {task.task_id}")
                    
                except Exception as e:
                    logger.error(f"Process task {task.task_id} failed: {e}")
                    with self.lock:
                        self.failed_count += 1
                
                self._log_progress()
        
        return all_results
    
    def _execute_task(self, worker_function: Callable, task: ScrapingTask) -> Dict[str, Any]:
        """
        Execute a single scraping task.
        
        Args:
            worker_function: Function to execute
            task: Scraping task to execute
            
        Returns:
            Task execution result
        """
        try:
            logger.debug(f"Executing task: {task.task_id}")
            
            # Execute the worker function with task parameters
            result = worker_function(
                source=task.source,
                keyword=task.keyword,
                page=task.page,
                scraper_type=task.scraper_type
            )
            
            return {
                'success': True,
                'task_id': task.task_id,
                'data': result if isinstance(result, list) else [result] if result else [],
                'execution_time': time.time() - task.created_at.timestamp()
            }
            
        except Exception as e:
            logger.error(f"Task execution failed {task.task_id}: {e}")
            return {
                'success': False,
                'task_id': task.task_id,
                'error': str(e),
                'data': []
            }
    
    def _log_progress(self) -> None:
        """Log current progress."""
        with self.lock:
            if self.total_tasks > 0:
                completion_rate = (self.completed_count + self.failed_count) / self.total_tasks * 100
                logger.info(f"Progress: {completion_rate:.1f}% ({self.completed_count} completed, {self.failed_count} failed)")
    
    def get_progress_stats(self) -> Dict[str, Any]:
        """Get current progress statistics."""
        with self.lock:
            return {
                'total_tasks': self.total_tasks,
                'completed_tasks': self.completed_count,
                'failed_tasks': self.failed_count,
                'active_tasks': len(self.active_tasks),
                'pending_tasks': self.task_queue.qsize(),
                'completion_rate': (self.completed_count + self.failed_count) / self.total_tasks * 100 if self.total_tasks > 0 else 0,
                'success_rate': self.completed_count / (self.completed_count + self.failed_count) * 100 if (self.completed_count + self.failed_count) > 0 else 0
            }
    
    def stop_processing(self) -> None:
        """Stop all processing operations."""
        self.stop_event.set()
        logger.info("Processing stop requested")
    
    def clear_queues(self) -> None:
        """Clear all task and result queues."""
        with self.lock:
            while not self.task_queue.empty():
                try:
                    self.task_queue.get_nowait()
                except Empty:
                    break
            
            while not self.result_queue.empty():
                try:
                    self.result_queue.get_nowait()
                except Empty:
                    break
            
            self.active_tasks.clear()
            self.completed_tasks.clear()
            self.failed_tasks.clear()
            self.total_tasks = 0
            self.completed_count = 0
            self.failed_count = 0
        
        logger.info("Queues cleared")

class ResourceManager:
    """
    Manages system resources during concurrent operations.
    
    Monitors and controls:
    - Memory usage
    - CPU utilization
    - Database connections
    - File handles
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize resource manager."""
        self.config = config
        self.max_memory_mb = config.get('resources', {}).get('max_memory_mb', 1024)
        self.max_cpu_percent = config.get('resources', {}).get('max_cpu_percent', 80)
        
        # Resource tracking
        self.start_time = time.time()
        self.peak_memory = 0
        self.peak_cpu = 0
    
    def check_resources(self) -> Dict[str, Any]:
        """
        Check current resource usage.
        
        Returns:
            Dictionary with resource usage stats
        """
        try:
            import psutil
            
            # Get current process
            process = psutil.Process()
            
            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            
            # Update peaks
            self.peak_memory = max(self.peak_memory, memory_mb)
            self.peak_cpu = max(self.peak_cpu, cpu_percent)
            
            return {
                'memory_mb': round(memory_mb, 2),
                'memory_percent': round(memory_mb / self.max_memory_mb * 100, 2),
                'cpu_percent': round(cpu_percent, 2),
                'peak_memory_mb': round(self.peak_memory, 2),
                'peak_cpu_percent': round(self.peak_cpu, 2),
                'uptime_seconds': round(time.time() - self.start_time, 2),
                'within_limits': memory_mb < self.max_memory_mb and cpu_percent < self.max_cpu_percent
            }
            
        except ImportError:
            logger.warning("psutil not available for resource monitoring")
            return {'error': 'Resource monitoring not available'}
        except Exception as e:
            logger.error(f"Error checking resources: {e}")
            return {'error': str(e)}
    
    def should_throttle(self) -> bool:
        """
        Check if processing should be throttled due to resource constraints.
        
        Returns:
            True if throttling is recommended
        """
        try:
            resources = self.check_resources()
            
            if 'error' in resources:
                return False
            
            # Throttle if memory or CPU usage is too high
            memory_high = resources['memory_mb'] > self.max_memory_mb * 0.9
            cpu_high = resources['cpu_percent'] > self.max_cpu_percent
            
            if memory_high or cpu_high:
                logger.warning(f"Resource throttling triggered - Memory: {resources['memory_mb']}MB, CPU: {resources['cpu_percent']}%")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in throttle check: {e}")
            return False 