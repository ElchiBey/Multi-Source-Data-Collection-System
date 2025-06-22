#!/usr/bin/env python3
"""
Performance Optimization Script

This script analyzes and optimizes the performance of the Multi-Source Data Collection System.
Week 3 requirement: Performance optimization and bug fixes.
"""

import time
import psutil
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import sqlite3
import pandas as pd

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.logger import setup_logger
from src.data.database import DatabaseManager

logger = setup_logger(__name__)


class PerformanceOptimizer:
    """Analyzes and optimizes system performance."""
    
    def __init__(self, config_path: str = 'config/settings.yaml'):
        """Initialize the performance optimizer."""
        self.config = load_config(config_path)
        self.db_manager = DatabaseManager(self.config)
        
    def analyze_system_performance(self) -> Dict[str, Any]:
        """Analyze current system performance metrics."""
        logger.info("Analyzing system performance...")
        
        performance_report = {
            'timestamp': time.time(),
            'system_metrics': self._get_system_metrics(),
            'database_metrics': self._get_database_metrics(),
            'file_system_metrics': self._get_filesystem_metrics(),
            'memory_usage': self._get_memory_usage(),
            'recommendations': []
        }
        
        # Generate optimization recommendations
        performance_report['recommendations'] = self._generate_recommendations(performance_report)
        
        return performance_report
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level performance metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
            'boot_time': psutil.boot_time(),
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        }
    
    def _get_database_metrics(self) -> Dict[str, Any]:
        """Analyze database performance."""
        try:
            db_path = self.config.get('database', {}).get('url', '').replace('sqlite:///', '')
            if not db_path or not os.path.exists(db_path):
                return {'error': 'Database not found'}
            
            # Get database file size
            db_size = os.path.getsize(db_path)
            
            # Analyze database structure
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get table information
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                table_info = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    row_count = cursor.fetchone()[0]
                    table_info[table] = {'row_count': row_count}
                
                # Check for indexes
                cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index';")
                indexes = cursor.fetchall()
                
                return {
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / (1024 * 1024), 2),
                    'table_count': len(tables),
                    'tables': table_info,
                    'index_count': len(indexes),
                    'indexes': indexes
                }
                
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
            return {'error': str(e)}
    
    def _get_filesystem_metrics(self) -> Dict[str, Any]:
        """Analyze file system performance."""
        project_root = Path(__file__).parent.parent
        
        metrics = {
            'data_output_size': 0,
            'logs_size': 0,
            'cache_size': 0,
            'file_counts': {}
        }
        
        # Analyze data output directory
        data_output_dir = project_root / 'data_output'
        if data_output_dir.exists():
            metrics['data_output_size'] = sum(
                f.stat().st_size for f in data_output_dir.rglob('*') if f.is_file()
            )
            metrics['file_counts']['data_output'] = len(list(data_output_dir.rglob('*.json')))
        
        # Analyze logs directory
        logs_dir = project_root / 'logs'
        if logs_dir.exists():
            metrics['logs_size'] = sum(
                f.stat().st_size for f in logs_dir.rglob('*') if f.is_file()
            )
            metrics['file_counts']['logs'] = len(list(logs_dir.rglob('*.log')))
        
        # Convert bytes to MB
        for key in ['data_output_size', 'logs_size', 'cache_size']:
            metrics[f"{key}_mb"] = round(metrics[key] / (1024 * 1024), 2)
        
        return metrics
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Analyze memory usage patterns."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': round(memory_info.rss / (1024 * 1024), 2),
            'vms_mb': round(memory_info.vms / (1024 * 1024), 2),
            'percent': process.memory_percent(),
            'num_threads': process.num_threads(),
            'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0
        }
    
    def _generate_recommendations(self, performance_report: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on performance analysis."""
        recommendations = []
        
        system_metrics = performance_report.get('system_metrics', {})
        db_metrics = performance_report.get('database_metrics', {})
        fs_metrics = performance_report.get('file_system_metrics', {})
        
        # CPU recommendations
        if system_metrics.get('cpu_percent', 0) > 80:
            recommendations.append("High CPU usage detected. Consider reducing max_workers in config.")
        
        # Memory recommendations
        if system_metrics.get('memory_percent', 0) > 85:
            recommendations.append("High memory usage. Consider processing data in smaller batches.")
        
        # Database recommendations
        if db_metrics.get('database_size_mb', 0) > 500:
            recommendations.append("Large database detected. Consider implementing data archiving.")
        
        if db_metrics.get('index_count', 0) < 3:
            recommendations.append("Few database indexes detected. Consider adding indexes for better performance.")
        
        # File system recommendations
        if fs_metrics.get('data_output_size_mb', 0) > 1000:
            recommendations.append("Large data output directory. Consider cleaning old files.")
        
        if fs_metrics.get('logs_size_mb', 0) > 100:
            recommendations.append("Large log files detected. Consider log rotation.")
        
        return recommendations
    
    def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance."""
        logger.info("Optimizing database performance...")
        
        optimization_results = {
            'vacuum_performed': False,
            'analyze_performed': False,
            'indexes_created': 0,
            'errors': []
        }
        
        try:
            db_path = self.config.get('database', {}).get('url', '').replace('sqlite:///', '')
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Vacuum database to reclaim space
                cursor.execute("VACUUM;")
                optimization_results['vacuum_performed'] = True
                logger.info("Database vacuum completed")
                
                # Analyze tables for query optimization
                cursor.execute("ANALYZE;")
                optimization_results['analyze_performed'] = True
                logger.info("Database analyze completed")
                
                # Create performance indexes if they don't exist
                indexes_to_create = [
                    "CREATE INDEX IF NOT EXISTS idx_products_source ON products(source);",
                    "CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);",
                    "CREATE INDEX IF NOT EXISTS idx_products_scraped_at ON products(scraped_at);",
                    "CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id);",
                    "CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON scraping_sessions(start_time);"
                ]
                
                for index_sql in indexes_to_create:
                    try:
                        cursor.execute(index_sql)
                        optimization_results['indexes_created'] += 1
                    except Exception as e:
                        optimization_results['errors'].append(f"Index creation failed: {e}")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            optimization_results['errors'].append(str(e))
        
        return optimization_results
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, Any]:
        """Clean up old data to improve performance."""
        logger.info(f"Cleaning up data older than {days} days...")
        
        cleanup_results = {
            'files_deleted': 0,
            'bytes_freed': 0,
            'database_records_deleted': 0,
            'errors': []
        }
        
        try:
            # Clean up old output files
            project_root = Path(__file__).parent.parent
            data_output_dir = project_root / 'data_output'
            
            if data_output_dir.exists():
                cutoff_time = time.time() - (days * 24 * 60 * 60)
                
                for file_path in data_output_dir.rglob('*'):
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        file_size = file_path.stat().st_size
                        try:
                            file_path.unlink()
                            cleanup_results['files_deleted'] += 1
                            cleanup_results['bytes_freed'] += file_size
                        except Exception as e:
                            cleanup_results['errors'].append(f"Failed to delete {file_path}: {e}")
            
            # Clean up old database records
            deleted_records = self.db_manager.cleanup_old_data(days)
            cleanup_results['database_records_deleted'] = deleted_records
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            cleanup_results['errors'].append(str(e))
        
        # Convert bytes to MB
        cleanup_results['mb_freed'] = round(cleanup_results['bytes_freed'] / (1024 * 1024), 2)
        
        return cleanup_results
    
    def optimize_configuration(self) -> Dict[str, Any]:
        """Suggest configuration optimizations."""
        system_metrics = self._get_system_metrics()
        
        suggestions = {
            'current_config': self.config.get('scraping', {}),
            'suggested_config': {},
            'reasons': []
        }
        
        # Optimize max_workers based on CPU count
        cpu_count = system_metrics.get('cpu_count', 4)
        memory_gb = system_metrics.get('memory_total', 0) / (1024**3)
        
        if memory_gb < 4:
            suggested_workers = min(2, cpu_count)
            suggestions['reasons'].append("Low memory system: reducing workers")
        elif memory_gb < 8:
            suggested_workers = min(4, cpu_count)
            suggestions['reasons'].append("Medium memory system: moderate workers")
        else:
            suggested_workers = min(8, cpu_count * 2)
            suggestions['reasons'].append("High memory system: increased workers")
        
        suggestions['suggested_config']['max_workers'] = suggested_workers
        
        # Optimize delays based on system performance
        if system_metrics.get('cpu_percent', 0) > 70:
            suggestions['suggested_config']['delay'] = {'min': 2.0, 'max': 4.0}
            suggestions['reasons'].append("High CPU usage: increasing delays")
        else:
            suggestions['suggested_config']['delay'] = {'min': 1.0, 'max': 2.0}
            suggestions['reasons'].append("Normal CPU usage: standard delays")
        
        return suggestions
    
    def run_full_optimization(self) -> Dict[str, Any]:
        """Run complete performance optimization."""
        logger.info("Starting full performance optimization...")
        
        results = {
            'start_time': time.time(),
            'performance_analysis': self.analyze_system_performance(),
            'database_optimization': self.optimize_database(),
            'cleanup_results': self.cleanup_old_data(),
            'config_suggestions': self.optimize_configuration()
        }
        
        results['end_time'] = time.time()
        results['duration_seconds'] = results['end_time'] - results['start_time']
        
        logger.info(f"Performance optimization completed in {results['duration_seconds']:.2f} seconds")
        
        return results


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance Optimization Tool')
    parser.add_argument('--analyze', action='store_true', help='Analyze performance only')
    parser.add_argument('--optimize-db', action='store_true', help='Optimize database only')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old data only')
    parser.add_argument('--cleanup-days', type=int, default=30, help='Days of data to keep')
    parser.add_argument('--full', action='store_true', help='Run full optimization')
    parser.add_argument('--config', default='config/settings.yaml', help='Configuration file')
    
    args = parser.parse_args()
    
    optimizer = PerformanceOptimizer(args.config)
    
    if args.analyze:
        results = optimizer.analyze_system_performance()
        print("=== Performance Analysis ===")
        print(f"CPU Usage: {results['system_metrics']['cpu_percent']:.1f}%")
        print(f"Memory Usage: {results['system_metrics']['memory_percent']:.1f}%")
        print(f"Database Size: {results['database_metrics'].get('database_size_mb', 'N/A')} MB")
        print(f"Data Output Size: {results['file_system_metrics']['data_output_size_mb']} MB")
        print("\nRecommendations:")
        for rec in results['recommendations']:
            print(f"- {rec}")
    
    elif args.optimize_db:
        results = optimizer.optimize_database()
        print("=== Database Optimization ===")
        print(f"Vacuum performed: {results['vacuum_performed']}")
        print(f"Analyze performed: {results['analyze_performed']}")
        print(f"Indexes created: {results['indexes_created']}")
        if results['errors']:
            print("Errors:")
            for error in results['errors']:
                print(f"- {error}")
    
    elif args.cleanup:
        results = optimizer.cleanup_old_data(args.cleanup_days)
        print("=== Cleanup Results ===")
        print(f"Files deleted: {results['files_deleted']}")
        print(f"Space freed: {results['mb_freed']} MB")
        print(f"Database records deleted: {results['database_records_deleted']}")
        if results['errors']:
            print("Errors:")
            for error in results['errors']:
                print(f"- {error}")
    
    elif args.full:
        results = optimizer.run_full_optimization()
        print("=== Full Optimization Complete ===")
        print(f"Duration: {results['duration_seconds']:.2f} seconds")
        print(f"Files cleaned: {results['cleanup_results']['files_deleted']}")
        print(f"Space freed: {results['cleanup_results']['mb_freed']} MB")
        print(f"Database optimized: {results['database_optimization']['vacuum_performed']}")
        print("\nRecommendations:")
        for rec in results['performance_analysis']['recommendations']:
            print(f"- {rec}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main() 