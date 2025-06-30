#!/usr/bin/env python3
"""
Multi-Source Data Collection System
Main entry point for the E-Commerce Price Monitoring System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import click
import logging
from pathlib import Path
import time

from src.utils.logger import setup_logger
from src.utils.config import load_config

# Setup logging
logger = setup_logger(__name__)

@click.group()
@click.version_option(version='1.0.0')
@click.option('--config', default='config/settings.yaml', help='Configuration file path')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.pass_context
def main(ctx, config, verbose):
    """
    Multi-Source Data Collection System
    
    E-Commerce Price Monitoring System that scrapes product data
    from multiple sources and provides comprehensive analysis.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Set verbosity level
    if verbose >= 2:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose >= 1:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Load configuration
    try:
        ctx.obj['config'] = load_config(config)
        logger.info(f"Configuration loaded from {config}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise click.ClickException(f"Configuration error: {e}")

@main.command()
@click.option('--sources', default='amazon,ebay', help='Comma-separated list of sources')
@click.option('--keywords', required=True, help='Comma-separated search keywords')
@click.option('--max-pages', default=5, help='Maximum pages per source')
@click.option('--scraper-type', 
              type=click.Choice(['static', 'selenium', 'scrapy', 'concurrent']),
              default='static', help='Type of scraper to use')
@click.option('--concurrent', is_flag=True, help='Use concurrent processing')
@click.option('--output', default='data_output/raw', help='Output directory')
@click.pass_context
def scrape(ctx, sources, keywords, max_pages, scraper_type, concurrent, output):
    """Start scraping products from specified sources."""
    from src.scrapers.manager import ScrapingManager
    
    logger.info("Starting scraping operation...")
    
    try:
        # Parse inputs
        source_list = [s.strip() for s in sources.split(',')]
        keyword_list = [k.strip() for k in keywords.split(',')]
        
        # Initialize scraping manager
        manager = ScrapingManager(ctx.obj['config'])
        
        # Handle different scraper types
        if scraper_type == 'concurrent' or concurrent:
            from src.utils.concurrent_manager import ConcurrentScrapingManager
            
            # Use concurrent processing
            concurrent_manager = ConcurrentScrapingManager(ctx.obj['config'])
            concurrent_manager.add_scraping_tasks(
                sources=source_list,
                keywords=keyword_list,
                max_pages=max_pages,
                scraper_type='static'
            )
            
            # Define worker function
            def scrape_worker(source, keyword, page, scraper_type):
                return manager.scrape_single(source, keyword, page, scraper_type)
            
            results = concurrent_manager.execute_concurrent_scraping(scrape_worker)
            
        elif scraper_type == 'scrapy':
            # Use Scrapy spider
            click.echo("🕷️ Using Scrapy framework...")
            from scrapy.crawler import CrawlerProcess
            from src.scrapers.scrapy_spider import ProductSpider
            
            # Run Scrapy spider
            process = CrawlerProcess({
                'USER_AGENT': 'Mozilla/5.0 (compatible; ProductScraper/1.0)',
                'ROBOTSTXT_OBEY': True,
                'DOWNLOAD_DELAY': 2,
            })
            
            for source in source_list:
                for keyword in keyword_list:
                    process.crawl(ProductSpider, 
                                source=source, 
                                keywords=keyword, 
                                max_pages=max_pages)
            
            process.start()
            results = []  # Scrapy handles data differently
            
        else:
            # Use regular scraping manager with specified scraper type
            results = manager.scrape_all(
                sources=source_list,
                keywords=keyword_list,
                max_pages=max_pages,
                output_dir=output,
                scraper_type=scraper_type
            )
        
        click.echo(f"✅ Scraping completed! Found {len(results)} products.")
        click.echo(f"📁 Data saved to: {output}")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise click.ClickException(f"Scraping error: {e}")

@main.command()
@click.option('--type', 'report_type', 
              type=click.Choice(['trend', 'comparison', 'summary']),
              default='summary', help='Report type')
@click.option('--period', default=30, help='Analysis period in days')
@click.option('--output', default='data_output/reports', help='Output directory')
@click.pass_context
def report(ctx, report_type, period, output):
    """Generate analysis reports."""
    from src.analysis.reports import ReportGenerator
    
    logger.info(f"Generating {report_type} report...")
    
    try:
        # Initialize report generator
        report_gen = ReportGenerator(ctx.obj['config'])
        
        # Generate report
        if report_type == 'trend':
            result = report_gen.generate_trend_report(period, output)
        elif report_type == 'comparison':
            result = report_gen.generate_comparison_report(period, output)
        else:
            result = report_gen.generate_summary_report(period, output)
        
        click.echo(f"✅ {report_type.capitalize()} report generated!")
        click.echo(f"📁 Report saved to: {result}")
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise click.ClickException(f"Report error: {e}")

@main.command()
@click.option('--format', 'export_format',
              type=click.Choice(['csv', 'json', 'excel']),
              default='csv', help='Export format')
@click.option('--output', default='data_output/processed', help='Output directory')
@click.option('--filter-days', default=7, help='Filter data from last N days')
@click.pass_context
def export(ctx, export_format, output, filter_days):
    """Export processed data in various formats."""
    from src.data.processors import DataExporter
    
    logger.info(f"Exporting data in {export_format} format...")
    
    try:
        # Initialize exporter
        exporter = DataExporter(ctx.obj['config'])
        
        # Export data
        result = exporter.export_data(
            format=export_format,
            output_dir=output,
            filter_days=filter_days
        )
        
        click.echo(f"✅ Data exported successfully!")
        click.echo(f"📁 File saved to: {result}")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise click.ClickException(f"Export error: {e}")

@main.command()
@click.pass_context
def setup(ctx):
    """Initialize database and create necessary directories."""
    from src.data.database import init_database
    from src.utils.helpers import create_directories
    
    logger.info("Setting up project...")
    
    try:
        # Create directories
        create_directories()
        click.echo("✅ Directories created")
        
        # Initialize database
        init_database(ctx.obj['config'])
        click.echo("✅ Database initialized")
        
        click.echo("🎉 Setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise click.ClickException(f"Setup error: {e}")

@main.command()
@click.option('--target', default=5000, help='Target number of records to collect')
@click.option('--strategy', 
              type=click.Choice(['comprehensive', 'quick', 'focused']),
              default='comprehensive', help='Collection strategy')
@click.pass_context
def collect(ctx, target, strategy):
    """Execute strategic data collection to reach target records."""
    from src.utils.data_collection_strategy import DataCollectionStrategy
    
    logger.info(f"🎯 Starting strategic collection (target: {target} records)")
    
    try:
        # Initialize strategic collector
        collector = DataCollectionStrategy(ctx.obj['config'])
        collector.target_records = target
        
        if strategy == 'comprehensive':
            click.echo("🚀 Using comprehensive collection strategy...")
            results = collector.execute_comprehensive_collection()
        elif strategy == 'quick':
            click.echo("⚡ Using quick collection strategy...")
            # Quick strategy - fewer keywords, more sources
            session_results = collector._execute_diverse_keywords()
            results = {
                'sessions': session_results,
                'total_records': sum(s.get('records_found', 0) for s in session_results if s.get('success', False)),
                'successful_sessions': sum(1 for s in session_results if s.get('success', False)),
                'failed_sessions': sum(1 for s in session_results if not s.get('success', True)),
                'strategies_used': ['diverse_keywords']
            }
        else:  # focused
            click.echo("🎯 Using focused collection strategy...")
            # Focused strategy - specific high-yield keywords
            session_results = collector._execute_multi_source()
            results = {
                'sessions': session_results,
                'total_records': sum(s.get('records_found', 0) for s in session_results if s.get('success', False)),
                'successful_sessions': sum(1 for s in session_results if s.get('success', False)),
                'failed_sessions': sum(1 for s in session_results if not s.get('success', True)),
                'strategies_used': ['multi_source']
            }
        
        # Generate report
        report_path = collector.generate_collection_report(results)
        
        final_count = collector._get_current_record_count()
        click.echo(f"✅ Collection completed!")
        click.echo(f"📊 Records collected: {final_count:,}")
        click.echo(f"📋 Report saved: {report_path}")
        
        if final_count >= target:
            click.echo(f"🎉 TARGET ACHIEVED! {final_count:,} >= {target:,} records")
        else:
            click.echo(f"📈 Progress: {(final_count/target)*100:.1f}% of target")
            click.echo("💡 Consider running again with different strategy or keywords")
        
    except Exception as e:
        logger.error(f"Strategic collection failed: {e}")
        raise click.ClickException(f"Collection error: {e}")

@main.command()
def test():
    """Run the test suite."""
    import subprocess
    
    try:
        result = subprocess.run(['pytest', 'tests/', '-v'], 
                              capture_output=True, text=True)
        
        click.echo(result.stdout)
        if result.stderr:
            click.echo(result.stderr, err=True)
        
        if result.returncode == 0:
            click.echo("✅ All tests passed!")
        else:
            raise click.ClickException("❌ Some tests failed!")
            
    except FileNotFoundError:
        raise click.ClickException("pytest not found. Install with: pip install pytest")

@main.command()
@click.option('--target', default=2000, help='Target number of records to collect')
@click.option('--browsers', default=4, help='Number of parallel browser instances')
@click.option('--sources', default='amazon,ebay,walmart', help='Comma-separated sources')
@click.option('--keywords', default='laptop,phone,tablet,headphones', help='Comma-separated keywords')
@click.option('--max-pages', default=3, help='Maximum pages per keyword')
@click.pass_context
def hyper(ctx, target, browsers, sources, keywords, max_pages):
    """🚀 HYPER MODE: Parallel Selenium with maximum anti-bot protection (10-20x faster)."""
    from src.utils.parallel_selenium_manager import ParallelSeleniumManager
    
    logger.info(f"🚀 HYPER MODE: {browsers} parallel browsers targeting {target:,} records")
    
    try:
        # Parse inputs
        source_list = [s.strip() for s in sources.split(',')]
        keyword_list = [k.strip() for k in keywords.split(',')]
        
        # Create parallel Selenium manager
        parallel_manager = ParallelSeleniumManager(ctx.obj['config'], max_browsers=browsers)
        
        # Execute parallel scraping
        start_time = time.time()
        results = parallel_manager.execute_parallel_scraping(
            sources=source_list,
            keywords=keyword_list,
            max_pages=max_pages,
            target_products=target
        )
        
        execution_time = time.time() - start_time
        
        # Display results
        click.echo(f"\n🎉 HYPER MODE COMPLETED!")
        click.echo(f"⏱️  Execution time: {execution_time:.1f}s")
        click.echo(f"📦 Products collected: {results['total_products']:,}")
        click.echo(f"⚡ Speed: {results['products_per_second']:.1f} products/second")
        click.echo(f"🎯 Target: {'ACHIEVED' if results['target_achieved'] else 'PARTIAL'}")
        click.echo(f"🤖 Browsers used: {results['browsers_used']}")
        click.echo(f"✅ Success rate: {(results['tasks_completed']/(results['tasks_completed']+results['tasks_failed'])*100):.1f}%" if results['tasks_completed']+results['tasks_failed'] > 0 else "N/A")
        
    except Exception as e:
        logger.error(f"HYPER mode failed: {e}")
        raise click.ClickException(f"HYPER error: {e}")

@main.command()
@click.option('--target', default=5000, help='Target number of records to collect')
@click.option('--workers', default=8, help='Number of parallel workers')
@click.option('--batch-size', default=12, help='Batch size for parallel processing')
@click.pass_context
def turbo(ctx, target, workers, batch_size):
    """🚀 TURBO MODE: High-speed optimized data collection (5-10x faster)."""
    from src.utils.optimized_collection import OptimizedCollectionStrategy
    
    logger.info(f"🚀 TURBO MODE: Collecting {target:,} records with {workers} workers")
    
    try:
        # Update config with performance settings
        ctx.obj['config']['collection'] = {
            'max_workers': workers,
            'batch_size': batch_size
        }
        
        # Initialize optimized collector
        collector = OptimizedCollectionStrategy(ctx.obj['config'])
        
        # Execute optimized collection
        click.echo(f"⚡ Starting TURBO collection with {workers} parallel workers...")
        click.echo(f"📦 Using batch size of {batch_size} tasks per batch")
        
        start_time = time.time()
        results = collector.execute_optimized_collection(target)
        
        # Display results
        if 'error' not in results:
            click.echo(f"\n🎉 TURBO COLLECTION COMPLETED!")
            click.echo(f"📊 Final count: {results['total_records']:,} records")
            click.echo(f"⏱️  Total time: {results['total_time']:.1f} seconds")
            click.echo(f"🚀 Performance: {results['records_per_second']:.1f} records/second")
            click.echo(f"📈 Success rate: {results['success_rate']:.1f}%")
            click.echo(f"📦 Batches processed: {results['batches_processed']}")
            
            if results['target_achieved']:
                click.echo(f"🎯 TARGET ACHIEVED! {results['total_records']:,} >= {target:,}")
            else:
                click.echo(f"📈 Progress: {(results['total_records']/target)*100:.1f}% of target")
                
        else:
            click.echo(f"❌ Collection failed: {results['error']}")
            
    except Exception as e:
        logger.error(f"Turbo collection failed: {e}")
        raise click.ClickException(f"Turbo error: {e}")

if __name__ == '__main__':
    main() 