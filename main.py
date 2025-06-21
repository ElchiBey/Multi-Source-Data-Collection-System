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
@click.option('--output', default='data_output/raw', help='Output directory')
@click.pass_context
def scrape(ctx, sources, keywords, max_pages, output):
    """Start scraping products from specified sources."""
    from src.scrapers.manager import ScrapingManager
    
    logger.info("Starting scraping operation...")
    
    try:
        # Parse inputs
        source_list = [s.strip() for s in sources.split(',')]
        keyword_list = [k.strip() for k in keywords.split(',')]
        
        # Initialize scraping manager
        manager = ScrapingManager(ctx.obj['config'])
        
        # Run scraping
        results = manager.scrape_all(
            sources=source_list,
            keywords=keyword_list,
            max_pages=max_pages,
            output_dir=output
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

if __name__ == '__main__':
    main() 