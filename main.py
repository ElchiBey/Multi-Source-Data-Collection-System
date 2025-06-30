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
            click.echo("Using Scrapy framework...")
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
        
        click.echo(f"[SUCCESS] Scraping completed! Found {len(results)} products.")
        click.echo(f"[DATA] Saved to: {output}")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise click.ClickException(f"Scraping error: {e}")

@main.command()
@click.option('--sources', default='ebay,walmart,amazon', help='Comma-separated sources')
@click.option('--keywords', default='laptop,gaming', help='Comma-separated keywords')
@click.option('--max-pages', default=2, help='Maximum pages per source')
@click.option('--hybrid/--no-hybrid', default=True, help='Use both static and selenium scrapers')
@click.option('--output-dir', default='data_output/raw', help='Output directory')
@click.pass_context
def scrape_parallel(ctx, sources, keywords, max_pages, hybrid, output_dir):
    """🚀 HIGH-PERFORMANCE parallel scraping using both BeautifulSoup4 and Selenium."""
    from src.scrapers.manager import ScrapingManager
    
    keyword_list = [k.strip() for k in keywords.split(',')]
    source_list = [s.strip() for s in sources.split(',')]
    
    click.echo(f"🚀 [TURBO] Starting HIGH-PERFORMANCE parallel scraping")
    click.echo(f"📊 [CONFIG] Sources: {source_list}")
    click.echo(f"🔍 [CONFIG] Keywords: {keyword_list}")
    click.echo(f"📄 [CONFIG] Max pages per source: {max_pages}")
    click.echo(f"⚡ [CONFIG] Hybrid mode (static + selenium): {'ENABLED' if hybrid else 'DISABLED'}")
    
    try:
        manager = ScrapingManager(ctx.obj['config'])
        
        # Execute high-performance parallel scraping
        results = manager.scrape_all_parallel(
            sources=source_list,
            keywords=keyword_list,
            max_pages=max_pages,
            output_dir=output_dir,
            use_hybrid=hybrid
        )
        
        click.echo(f"🎉 [SUCCESS] Parallel scraping completed!")
        click.echo(f"📊 [RESULTS] Total products scraped: {len(results)}")
        click.echo(f"💾 [OUTPUT] Data saved to: {output_dir}")
        
    except Exception as e:
        click.echo(f"❌ [ERROR] Parallel scraping failed: {e}")
        logger.error(f"Parallel scraping error: {e}")

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
        # Load data first
        from src.analysis.statistics import DataStatistics
        stats = DataStatistics()
        df = stats.load_data("database")
        
        if df.empty:
            click.echo("[ERROR] No data found in database. Run collection first.")
            return
        
        # Initialize report generator
        report_gen = ReportGenerator(df)
        
        # Generate report
        if report_type == 'trend':
            result = report_gen.generate_trend_report()
        elif report_type == 'comparison':
            result = report_gen.generate_comparison_report()
        else:
            result = report_gen.generate_summary_report()
        
        click.echo(f"[SUCCESS] {report_type.capitalize()} report generated!")
        click.echo(f"[FILE] Report saved to: {result}")
        
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
        
        click.echo(f"[SUCCESS] Data exported successfully!")
        click.echo(f"[FILE] Saved to: {result}")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise click.ClickException(f"Export error: {e}")

@main.command()
@click.pass_context
def setup(ctx):
    """Initialize project structure and database."""
    logger.info("Setting up project structure...")
    
    try:
        # Create directories
        directories = [
            'data', 'data_output/raw', 'data_output/processed', 
            'data_output/reports', 'logs'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        click.echo("[SUCCESS] Directories created")
        
        # Initialize database
        from src.data.database import DatabaseManager
        db_manager = DatabaseManager()
        click.echo("[SUCCESS] Database initialized")
        
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
    """Advanced data collection with strategic approach."""
    from src.utils.data_collection_strategy import DataCollectionStrategy
    
    logger.info(f"[TARGET] Starting strategic collection (target: {target} records)")
    
    try:
        # Initialize strategic collector
        collector = DataCollectionStrategy(ctx.obj['config'])
        
        # Execute collection based on strategy
        if strategy == 'comprehensive':
            click.echo("[STRATEGY] Using comprehensive collection strategy...")
            results = collector.execute_comprehensive_collection()
        elif strategy == 'quick':
            from src.utils.optimized_collection import OptimizedCollector
            opt_collector = OptimizedCollector(ctx.obj['config'])
            click.echo("[STRATEGY] Using quick collection strategy...")
            results = opt_collector.execute_comprehensive_collection()
        else:  # focused
            click.echo("[STRATEGY] Using focused collection strategy...")
            results = collector.execute_comprehensive_collection()
        
        # Get final count from database
        from src.data.database import DatabaseManager
        db = DatabaseManager()
        final_count = db.get_total_products()
        
        # Generate collection report
        report_path = collector.generate_collection_report(results)
        
        click.echo(f"[SUCCESS] Collection completed!")
        click.echo(f"[STATS] Records collected: {final_count:,}")
        click.echo(f"[REPORT] Report saved: {report_path}")
        
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise click.ClickException(f"Collection error: {e}")

@main.command()
def test():
    """Run comprehensive system tests."""
    import subprocess
    import sys
    
    try:
        # Run the test suite
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', '-v', '--tb=short'
        ], capture_output=True, text=True)
        
        click.echo(result.stdout)
        if result.stderr:
            click.echo(result.stderr)
        
        if result.returncode == 0:
            click.echo("[SUCCESS] All tests passed!")
        else:
            click.echo("[ERROR] Some tests failed!")
            sys.exit(result.returncode)
            
    except Exception as e:
        raise click.ClickException(f"Test execution failed: {e}")

@main.command()
@click.option('--target', default=2000, help='Target number of records to collect')
@click.option('--browsers', default=4, help='Number of parallel browser instances')
@click.option('--sources', default='amazon,ebay,walmart', help='Comma-separated sources')
@click.option('--keywords', default='laptop,phone,tablet,headphones', help='Comma-separated keywords')
@click.option('--max-pages', default=3, help='Maximum pages per keyword')
@click.pass_context
def hyper(ctx, target, browsers, sources, keywords, max_pages):
    """[HYPER MODE] Parallel Selenium with maximum anti-bot protection (10-20x faster)."""
    from src.utils.parallel_selenium_manager import ParallelSeleniumManager
    
    logger.info(f"[HYPER] Starting mode: {browsers} parallel browsers targeting {target:,} records")
    
    try:
        # Parse inputs
        source_list = [s.strip() for s in sources.split(',')]
        keyword_list = [k.strip() for k in keywords.split(',')]
        
        # Initialize parallel manager
        manager = ParallelSeleniumManager(ctx.obj['config'], max_browsers=browsers)
        
        # Execute parallel scraping
        results = manager.execute_parallel_scraping(
            sources=source_list,
            keywords=keyword_list,
            max_pages=max_pages,
            target_products=target
        )
        
        # Display results
        click.echo(f"[HYPER] Results Summary:")
        click.echo(f"[TARGET] Target: {'ACHIEVED' if results['target_achieved'] else 'PARTIAL'}")
        click.echo(f"[RECORDS] Collected: {results['total_records']:,}")
        click.echo(f"[SUCCESS] Success rate: {(results['tasks_completed']/(results['tasks_completed']+results['tasks_failed'])*100):.1f}%" if results['tasks_completed']+results['tasks_failed'] > 0 else "N/A")
        click.echo(f"[TIME] Duration: {results['total_time']:.1f} seconds")
        
        # Cleanup
        manager.shutdown()
        
    except Exception as e:
        logger.error(f"Hyper mode failed: {e}")
        raise click.ClickException(f"Hyper mode error: {e}")

@main.command()
@click.option('--target', default=5000, help='Target number of records to collect')
@click.option('--workers', default=8, help='Number of parallel workers')
@click.option('--batch-size', default=12, help='Batch size for parallel processing')
@click.pass_context
def turbo(ctx, target, workers, batch_size):
    """[TURBO MODE] High-speed optimized data collection (5-10x faster)."""
    from src.utils.optimized_collection import OptimizedCollector
    
    logger.info(f"[TURBO] Starting mode: Collecting {target:,} records with {workers} workers")
    
    try:
        # Initialize optimized collector
        collector = OptimizedCollector(ctx.obj['config'])
        
        # Execute turbo collection
        results = collector.turbo_collection(target)
        
        # Display comprehensive results
        click.echo(f"[TURBO] Collection Complete!")
        click.echo(f"[BATCH] Batches processed: {results['batches_processed']}")
        click.echo(f"[WORKERS] Parallel workers: {results['workers_used']}")
        click.echo(f"[RECORDS] Final count: {results['total_records']:,} records")
        click.echo(f"[TIME] Total time: {results['total_time']:.1f} seconds")
        click.echo(f"[SPEED] Performance: {results['records_per_second']:.1f} records/second")
        
        if results['total_records'] >= target:
            click.echo(f"[TARGET] TARGET ACHIEVED! {results['total_records']:,} >= {target:,}")
        else:
            click.echo(f"[TARGET] Partial completion: {results['total_records']:,}/{target:,}")
        
    except Exception as e:
        logger.error(f"Turbo mode failed: {e}")
        raise click.ClickException(f"Turbo mode error: {e}")

@main.command()
@click.option('--format', default='html', type=click.Choice(['html', 'json', 'csv', 'all']), 
              help='Output format for the report')
@click.option('--output-dir', default='data_output/reports', help='Output directory for reports')
@click.option('--include-charts', is_flag=True, default=True, help='Include visualizations in report')
def generate_report(format, output_dir, include_charts):
    """Generate comprehensive analysis reports with statistics and visualizations."""
    click.echo("[REPORT] Generating Comprehensive Analysis Report...")
    
    try:
        from src.analysis.statistics import DataStatistics
        from src.analysis.visualization import DataVisualizer
        from src.analysis.reports import ReportGenerator
        
        # Initialize analysis components
        stats = DataStatistics()
        
        # Load data from database
        click.echo("[DATA] Loading data for analysis...")
        df = stats.load_data("database")
        
        if df.empty:
            click.echo("[ERROR] No data found in database. Run collection first.")
            return
        
        click.echo(f"[SUCCESS] Loaded {len(df)} records for analysis")
        
        # Generate reports based on format
        if format == 'html' or format == 'all':
            # Generate HTML report
            report_gen = ReportGenerator(df)
            html_path = report_gen.generate_comprehensive_report()
            
            if html_path:
                click.echo(f"[SUCCESS] HTML report saved: {html_path}")
            else:
                click.echo("[ERROR] Failed to generate HTML report")
        
        if format == 'json' or format == 'all':
            # Generate comprehensive statistics first
            click.echo("[ANALYSIS] Generating comprehensive statistics...")
            stats.generate_comprehensive_statistics()
            
            # Export statistics to JSON
            json_path = stats.export_statistics()
            if json_path:
                click.echo(f"[SUCCESS] JSON statistics saved: {json_path}")
        
        if format == 'csv' or format == 'all':
            # Export data to CSV
            import pandas as pd
            from pathlib import Path
            from datetime import datetime
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = output_path / f"products_export_{timestamp}.csv"
            
            df.to_csv(csv_path, index=False, encoding='utf-8')
            click.echo(f"[SUCCESS] CSV export saved: {csv_path}")
            
            # Export Excel with multiple sheets
            excel_path = output_path / f"products_analysis_{timestamp}.xlsx"
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Main data
                df.to_excel(writer, sheet_name='Products', index=False)
                
                # Summary by source
                if 'source' in df.columns:
                    source_summary = df.groupby('source').agg({
                        'price': ['count', 'mean', 'median', 'std']
                    }).round(2)
                    source_summary.to_excel(writer, sheet_name='Source_Summary')
                
                # Price ranges
                if 'price' in df.columns:
                    price_ranges = pd.DataFrame({
                        'Range': ['Under $100', '$100-$500', '$500-$1000', 'Over $1000'],
                        'Count': [
                            (df['price'] < 100).sum(),
                            ((df['price'] >= 100) & (df['price'] < 500)).sum(),
                            ((df['price'] >= 500) & (df['price'] < 1000)).sum(),
                            (df['price'] >= 1000).sum()
                        ]
                    })
                    price_ranges.to_excel(writer, sheet_name='Price_Analysis', index=False)
            
            click.echo(f"[SUCCESS] Excel analysis saved: {excel_path}")
        
        if include_charts:
            # Generate visualizations
            click.echo("[CHARTS] Creating visualizations...")
            visualizer = DataVisualizer(df)
            charts = visualizer.create_all_charts()
            
            if charts:
                click.echo(f"[SUCCESS] Generated {len(charts)} visualizations:")
                for chart_name, chart_path in charts.items():
                    click.echo(f"   - {chart_name}: {chart_path}")
        
        click.echo("\n[SUMMARY] Report generation completed successfully!")
        click.echo(f"\n[STATS] Summary:")
        click.echo(f"   - Total products analyzed: {len(df):,}")
        click.echo(f"   - Data sources: {df['source'].nunique() if 'source' in df.columns else 0}")
        click.echo(f"   - Average price: ${df['price'].mean():.2f}" if 'price' in df.columns else "")
        date_col = 'created_at' if 'created_at' in df.columns else 'scraped_at'
        if date_col in df.columns:
            click.echo(f"   - Date range: {df[date_col].min()} to {df[date_col].max()}")
        
    except Exception as e:
        click.echo(f"[ERROR] Report generation failed: {e}")
        logger.error(f"Report generation error: {e}")

if __name__ == '__main__':
    main() 