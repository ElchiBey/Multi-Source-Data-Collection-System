"""
Report Generation Module

This module provides functionality for generating various types of analysis reports.
"""

import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

from ..data.database import DatabaseManager
from ..data.processors import DataProcessor
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ReportGenerator:
    """Generates various analysis reports for scraped data."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the report generator."""
        self.config = config
        self.db_manager = DatabaseManager(config)
        self.data_processor = DataProcessor(config)
        
        # Set up matplotlib style
        try:
            style_name = self.config.get('analysis', {}).get('chart_style', 'default')
            if style_name in plt.style.available:
                plt.style.use(style_name)
            else:
                plt.style.use('default')
        except Exception:
            plt.style.use('default')
        
        logger.info("ReportGenerator initialized")
    
    def generate_summary_report(self, period: int, output_dir: str) -> str:
        """
        Generate a summary report of scraped data.
        
        Args:
            period: Number of days to analyze
            output_dir: Directory to save the report
            
        Returns:
            Path to generated report file
        """
        logger.info(f"Generating summary report for last {period} days...")
        
        try:
            # Get data
            df = self.data_processor.aggregate_price_data(period)
            
            if df.empty:
                logger.warning("No data available for summary report")
                return self._generate_empty_report(output_dir, "summary")
            
            # Generate report content
            report_data = {
                'generation_time': datetime.now().isoformat(),
                'period_days': period,
                'total_products': len(df),
                'unique_sources': df['source'].nunique(),
                'price_statistics': {
                    'mean': float(df['price'].mean()),
                    'median': float(df['price'].median()),
                    'min': float(df['price'].min()),
                    'max': float(df['price'].max()),
                    'std': float(df['price'].std())
                },
                'source_breakdown': df['source'].value_counts().to_dict(),
                'category_breakdown': df['category'].value_counts().to_dict() if 'category' in df.columns else {}
            }
            
            # Create visualizations
            charts_dir = Path(output_dir) / 'charts'
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            chart_files = []
            
            # Price distribution histogram
            fig = px.histogram(df, x='price', title='Price Distribution', 
                             nbins=30, labels={'price': 'Price ($)', 'count': 'Count'})
            chart_file = charts_dir / 'price_distribution.html'
            fig.write_html(chart_file)
            chart_files.append(str(chart_file))
            
            # Source comparison
            if len(df['source'].unique()) > 1:
                fig = px.box(df, x='source', y='price', title='Price Comparison by Source')
                chart_file = charts_dir / 'source_comparison.html'
                fig.write_html(chart_file)
                chart_files.append(str(chart_file))
            
            # Save report
            report_file = self._save_report(report_data, output_dir, "summary", chart_files)
            
            logger.info(f"Summary report generated: {report_file}")
            return report_file
            
        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            raise
    
    def generate_trend_report(self, period: int, output_dir: str) -> str:
        """
        Generate a trend analysis report.
        
        Args:
            period: Number of days to analyze
            output_dir: Directory to save the report
            
        Returns:
            Path to generated report file
        """
        logger.info(f"Generating trend report for last {period} days...")
        
        try:
            # Get data
            df = self.data_processor.aggregate_price_data(period)
            
            if df.empty:
                logger.warning("No data available for trend report")
                return self._generate_empty_report(output_dir, "trend")
            
            # Prepare time series data
            df['date'] = pd.to_datetime(df['scraped_at']).dt.date
            daily_data = df.groupby(['date', 'source'])['price'].agg(['mean', 'count']).reset_index()
            
            # Generate report content
            report_data = {
                'generation_time': datetime.now().isoformat(),
                'period_days': period,
                'total_data_points': len(df),
                'date_range': {
                    'start': daily_data['date'].min().isoformat() if not daily_data.empty else None,
                    'end': daily_data['date'].max().isoformat() if not daily_data.empty else None
                },
                'trend_summary': {}
            }
            
            # Calculate trends for each source
            for source in daily_data['source'].unique():
                source_data = daily_data[daily_data['source'] == source].copy()
                source_data = source_data.sort_values('date')
                
                if len(source_data) >= 2:
                    price_change = source_data['mean'].iloc[-1] - source_data['mean'].iloc[0]
                    price_change_percent = (price_change / source_data['mean'].iloc[0]) * 100
                    
                    report_data['trend_summary'][source] = {
                        'price_change': float(price_change),
                        'price_change_percent': float(price_change_percent),
                        'avg_daily_volume': float(source_data['count'].mean())
                    }
            
            # Create visualizations
            charts_dir = Path(output_dir) / 'charts'
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            chart_files = []
            
            # Price trend over time
            if not daily_data.empty:
                fig = px.line(daily_data, x='date', y='mean', color='source',
                             title='Average Price Trends by Source',
                             labels={'mean': 'Average Price ($)', 'date': 'Date'})
                chart_file = charts_dir / 'price_trends.html'
                fig.write_html(chart_file)
                chart_files.append(str(chart_file))
            
            # Save report
            report_file = self._save_report(report_data, output_dir, "trend", chart_files)
            
            logger.info(f"Trend report generated: {report_file}")
            return report_file
            
        except Exception as e:
            logger.error(f"Failed to generate trend report: {e}")
            raise
    
    def generate_comparison_report(self, period: int, output_dir: str) -> str:
        """
        Generate a comparison report between sources.
        
        Args:
            period: Number of days to analyze
            output_dir: Directory to save the report
            
        Returns:
            Path to generated report file
        """
        logger.info(f"Generating comparison report for last {period} days...")
        
        try:
            # Get data
            df = self.data_processor.aggregate_price_data(period)
            
            if df.empty:
                logger.warning("No data available for comparison report")
                return self._generate_empty_report(output_dir, "comparison")
            
            # Source comparison analysis
            source_stats = df.groupby('source')['price'].agg([
                'count', 'mean', 'median', 'std', 'min', 'max'
            ]).round(2)
            
            # Generate report content
            report_data = {
                'generation_time': datetime.now().isoformat(),
                'period_days': period,
                'sources_compared': list(df['source'].unique()),
                'source_statistics': source_stats.to_dict('index'),
                'price_competitiveness': {}
            }
            
            # Calculate price competitiveness
            for source in df['source'].unique():
                source_data = df[df['source'] == source]
                other_data = df[df['source'] != source]
                
                if not other_data.empty:
                    avg_price = source_data['price'].mean()
                    market_avg = other_data['price'].mean()
                    competitiveness = ((market_avg - avg_price) / market_avg) * 100
                    
                    report_data['price_competitiveness'][source] = {
                        'average_price': float(avg_price),
                        'market_average': float(market_avg),
                        'competitiveness_score': float(competitiveness)
                    }
            
            # Create visualizations
            charts_dir = Path(output_dir) / 'charts'
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            chart_files = []
            
            # Source comparison chart
            if len(df['source'].unique()) > 1:
                fig = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=('Average Prices', 'Product Count'),
                    specs=[[{"secondary_y": False}, {"secondary_y": False}]]
                )
                
                # Average prices
                source_avgs = df.groupby('source')['price'].mean()
                fig.add_trace(
                    go.Bar(x=source_avgs.index, y=source_avgs.values, name='Avg Price'),
                    row=1, col=1
                )
                
                # Product counts
                source_counts = df['source'].value_counts()
                fig.add_trace(
                    go.Bar(x=source_counts.index, y=source_counts.values, name='Product Count'),
                    row=1, col=2
                )
                
                fig.update_layout(title='Source Comparison', showlegend=False)
                chart_file = charts_dir / 'source_comparison.html'
                fig.write_html(chart_file)
                chart_files.append(str(chart_file))
            
            # Save report
            report_file = self._save_report(report_data, output_dir, "comparison", chart_files)
            
            logger.info(f"Comparison report generated: {report_file}")
            return report_file
            
        except Exception as e:
            logger.error(f"Failed to generate comparison report: {e}")
            raise
    
    def _save_report(self, report_data: Dict[str, Any], output_dir: str, 
                     report_type: str, chart_files: List[str] = None) -> str:
        """Save report data to JSON file."""
        try:
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Add chart files to report data
            if chart_files:
                report_data['chart_files'] = chart_files
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{report_type}_report_{timestamp}.json"
            file_path = output_path / filename
            
            # Save report
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            raise
    
    def _generate_empty_report(self, output_dir: str, report_type: str) -> str:
        """Generate empty report when no data is available."""
        report_data = {
            'generation_time': datetime.now().isoformat(),
            'report_type': report_type,
            'status': 'empty',
            'message': 'No data available for the specified period'
        }
        
        return self._save_report(report_data, output_dir, f"{report_type}_empty") 