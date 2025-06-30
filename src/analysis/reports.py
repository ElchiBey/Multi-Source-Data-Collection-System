"""
📋 HTML Report Generation Module

Comprehensive HTML report generation for the Multi-Source Data Collection System.
Creates professional reports with charts, statistics, and analysis.
"""

import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from jinja2 import Template
import logging

from ..utils.logger import get_logger
from .statistics import DataStatistics
from .visualization import DataVisualizer

logger = get_logger(__name__)

class ReportGenerator:
    """
    📋 Comprehensive HTML report generator.
    
    Features:
    - Professional HTML reports with embedded charts
    - Statistical analysis summaries
    - Data quality assessments
    - Export capabilities (CSV, Excel)
    - Responsive design for multiple devices
    """
    
    def __init__(self, df: pd.DataFrame):
        """Initialize report generator with DataFrame."""
        self.df = df
        self.visualizer = DataVisualizer(df)
        
        # Create output directories
        self.output_dir = Path("data_output/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load HTML template
        self.template = self._load_html_template()
        
    def generate_comprehensive_report(self) -> str:
        """
        Generate comprehensive HTML report with all analysis.
            
        Returns:
            Path to generated HTML report
        """
        try:
            logger.info("📋 Generating comprehensive HTML report...")
            
            # Generate basic statistics
            stats = self._generate_basic_statistics()
            
            # Create visualizations
            charts = self.visualizer.create_all_charts()
            
            # Convert chart images to base64 for embedding
            chart_data = self._convert_charts_to_base64(charts)
            
            # Generate report data
            report_data = {
                'report_metadata': self._generate_report_metadata(),
                'executive_summary': self._generate_executive_summary(stats),
                'statistics': stats,
                'charts': chart_data,
                'data_exports': self._generate_data_exports(),
                'recommendations': self._generate_recommendations(stats)
            }
            
            # Render HTML
            html_content = self.template.render(**report_data)
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.output_dir / f"comprehensive_report_{timestamp}.html"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"📋 Comprehensive report saved to {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return ""
    
    def _load_html_template(self) -> Template:
        """Load or create HTML template for reports."""
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Source Data Collection System - Analysis Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            margin-top: 20px;
            margin-bottom: 20px;
            border-radius: 10px;
        }
        
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 3px solid #667eea;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header .subtitle {
            color: #7f8c8d;
            font-size: 1.2em;
        }
        
        .metadata {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .metadata-item {
            text-align: center;
        }
        
        .metadata-item .value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            display: block;
        }
        
        .metadata-item .label {
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section h2 {
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }
        
        .section h3 {
            color: #34495e;
            font-size: 1.3em;
            margin-bottom: 15px;
        }
        
        .chart-container {
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stats-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        
        .stats-card h4 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        
        .stats-table th,
        .stats-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        
        .stats-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .stats-table tr:hover {
            background: #f8f9fa;
        }
        
        .export-section {
            background: #e8f4fd;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .export-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        
        .export-btn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 500;
            transition: background 0.3s;
        }
        
        .export-btn:hover {
            background: #5a6fd8;
        }
        
        .recommendations {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .recommendations h3 {
            color: #8b5a00;
            margin-bottom: 15px;
        }
        
        .recommendations ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .recommendations li {
            padding: 8px 0;
            border-bottom: 1px solid #ffeaa7;
        }
        
        .recommendations li:before {
            content: "💡 ";
            margin-right: 8px;
        }
        
        .footer {
            text-align: center;
            padding: 30px 0;
            border-top: 2px solid #ecf0f1;
            margin-top: 40px;
            color: #7f8c8d;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                padding: 15px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .metadata {
                grid-template-columns: 1fr;
            }
            
            .export-buttons {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 Data Collection Analysis Report</h1>
            <div class="subtitle">Multi-Source E-Commerce Data Collection System</div>
            <div style="margin-top: 15px; color: #7f8c8d;">
                Generated on {{ report_metadata.generated_at }}
            </div>
        </div>
        
        <!-- Metadata Overview -->
        <div class="metadata">
            <div class="metadata-item">
                <span class="value">{{ report_metadata.total_products }}</span>
                <span class="label">Total Products</span>
            </div>
            <div class="metadata-item">
                <span class="value">{{ report_metadata.total_sources }}</span>
                <span class="label">Data Sources</span>
            </div>
            <div class="metadata-item">
                <span class="value">{{ report_metadata.collection_period }}</span>
                <span class="label">Collection Period</span>
            </div>
            <div class="metadata-item">
                <span class="value">{{ report_metadata.data_quality_score }}%</span>
                <span class="label">Data Quality</span>
            </div>
        </div>
        
        <!-- Executive Summary -->
        <div class="section">
            <h2>📋 Executive Summary</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="font-size: 1.1em; line-height: 1.8;">{{ executive_summary.overview }}</p>
                
                <div style="margin-top: 20px;">
                    <h4>Key Findings:</h4>
                    <ul style="margin-left: 20px; margin-top: 10px;">
                        {% for finding in executive_summary.key_findings %}
                        <li style="margin-bottom: 8px;">{{ finding }}</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- Price Analysis -->
        <div class="section">
            <h2>💰 Price Analysis</h2>
            {% if charts.price_analysis %}
            <div class="chart-container">
                <img src="data:image/png;base64,{{ charts.price_analysis }}" alt="Price Analysis Dashboard">
            </div>
            {% endif %}
            
            {% if charts.price_ranges %}
            <div class="chart-container">
                <img src="data:image/png;base64,{{ charts.price_ranges }}" alt="Price Range Distribution">
            </div>
            {% endif %}
            
            <div class="stats-grid">
                <div class="stats-card">
                    <h4>Price Statistics</h4>
                    {% if statistics.price_analysis %}
                    <table class="stats-table">
                        <tr><td>Average Price</td><td>${{ "%.2f"|format(statistics.price_analysis.summary.mean) }}</td></tr>
                        <tr><td>Median Price</td><td>${{ "%.2f"|format(statistics.price_analysis.summary.median) }}</td></tr>
                        <tr><td>Price Range</td><td>${{ "%.2f"|format(statistics.price_analysis.summary.min) }} - ${{ "%.2f"|format(statistics.price_analysis.summary.max) }}</td></tr>
                        <tr><td>Standard Deviation</td><td>${{ "%.2f"|format(statistics.price_analysis.summary.std) }}</td></tr>
                    </table>
                    {% endif %}
                </div>
                
                <div class="stats-card">
                    <h4>Price Distribution</h4>
                    {% if statistics.price_analysis %}
                    <table class="stats-table">
                        <tr><td>Under $100</td><td>{{ statistics.price_analysis.distribution.under_100 }} products</td></tr>
                        <tr><td>$100 - $500</td><td>{{ statistics.price_analysis.distribution.under_500 - statistics.price_analysis.distribution.under_100 }} products</td></tr>
                        <tr><td>$500 - $1000</td><td>{{ statistics.price_analysis.distribution.under_1000 - statistics.price_analysis.distribution.under_500 }} products</td></tr>
                        <tr><td>Over $1000</td><td>{{ statistics.price_analysis.distribution.over_1000 }} products</td></tr>
                    </table>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <!-- Source Comparison -->
        <div class="section">
            <h2>🔄 Source Comparison</h2>
            {% if charts.source_comparison %}
            <div class="chart-container">
                <img src="data:image/png;base64,{{ charts.source_comparison }}" alt="Source Comparison Dashboard">
            </div>
            {% endif %}
            
            <div class="stats-grid">
                {% for source, data in statistics.source_comparison.items() %}
                <div class="stats-card">
                    <h4>{{ source|title }} Performance</h4>
                    <table class="stats-table">
                        <tr><td>Total Products</td><td>{{ data.total_products }}</td></tr>
                        {% if data.avg_price %}
                        <tr><td>Average Price</td><td>${{ "%.2f"|format(data.avg_price) }}</td></tr>
                        {% endif %}
                        {% if data.avg_rating %}
                        <tr><td>Average Rating</td><td>{{ "%.1f"|format(data.avg_rating) }}/5</td></tr>
                        {% endif %}
                        <tr><td>Data Quality</td><td>{{ "%.1f"|format(data.data_quality_score * 100) }}%</td></tr>
                    </table>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <!-- Trend Analysis -->
        <div class="section">
            <h2>📈 Trend Analysis</h2>
            {% if charts.trends_analysis %}
            <div class="chart-container">
                <img src="data:image/png;base64,{{ charts.trends_analysis }}" alt="Trends Analysis Dashboard">
            </div>
            {% endif %}
            
            {% if statistics.trend_analysis %}
            <div class="stats-grid">
                <div class="stats-card">
                    <h4>Collection Velocity</h4>
                    <table class="stats-table">
                        <tr><td>Average Products/Day</td><td>{{ "%.1f"|format(statistics.trend_analysis.collection_velocity.avg_products_per_day) }}</td></tr>
                        <tr><td>Peak Collection Day</td><td>{{ statistics.trend_analysis.collection_velocity.max_products_per_day }} products</td></tr>
                        <tr><td>Total Collection Days</td><td>{{ statistics.trend_analysis.collection_velocity.total_collection_days }}</td></tr>
                    </table>
                </div>
                
                <div class="stats-card">
                    <h4>Price Trends</h4>
                    <table class="stats-table">
                        <tr><td>Trend Direction</td><td>{{ statistics.trend_analysis.price_trend.trend_direction|title }}</td></tr>
                        <tr><td>Trend Strength</td><td>{{ "%.3f"|format(statistics.trend_analysis.price_trend.trend_slope) }}</td></tr>
                    </table>
                </div>
            </div>
            {% endif %}
        </div>
        
        <!-- Data Quality Assessment -->
        <div class="section">
            <h2>✅ Data Quality Assessment</h2>
            {% if statistics.data_quality %}
            <div class="stats-grid">
                <div class="stats-card">
                    <h4>Quality Metrics</h4>
                    <table class="stats-table">
                        <tr><td>Completeness Score</td><td>{{ "%.1f"|format(statistics.data_quality.completeness_score * 100) }}%</td></tr>
                        <tr><td>Duplicate Rate</td><td>{{ "%.1f"|format(statistics.data_quality.duplicate_rate) }}%</td></tr>
                        <tr><td>Invalid Data Rate</td><td>{{ "%.1f"|format(statistics.data_quality.invalid_data_rate) }}%</td></tr>
                        <tr><td>Consistency Score</td><td>{{ "%.1f"|format(statistics.data_quality.consistency_score) }}%</td></tr>
                    </table>
                </div>
            </div>
            {% endif %}
        </div>
        
        <!-- Data Export Options -->
        <div class="export-section">
            <h3>📁 Data Export Options</h3>
            <p>Download the collected data in various formats for further analysis:</p>
            <div class="export-buttons">
                {% for export_type, export_path in data_exports.items() %}
                <a href="{{ export_path }}" class="export-btn">Download {{ export_type|upper }}</a>
                {% endfor %}
            </div>
        </div>
        
        <!-- Recommendations -->
        <div class="recommendations">
            <h3>🎯 Recommendations</h3>
            <ul>
                {% for recommendation in recommendations %}
                <li>{{ recommendation }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <!-- Interactive Dashboard Link -->
        {% if charts.interactive_dashboard %}
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ charts.interactive_dashboard }}" target="_blank" 
               style="display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-size: 1.1em; font-weight: 500;">
                🚀 Open Interactive Dashboard
            </a>
        </div>
        {% endif %}
        
        <!-- Footer -->
        <div class="footer">
            <p>Multi-Source Data Collection System | Generated by Advanced Web Scraping Framework</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                Report includes {{ report_metadata.total_products }} products from {{ report_metadata.total_sources }} sources
            </p>
        </div>
    </div>
</body>
</html>
        """
        return Template(template_content)
    
    def _generate_basic_statistics(self) -> Dict[str, Any]:
        """Generate basic statistics from the DataFrame."""
        if self.df is None or self.df.empty:
            return {}
        
        stats = {}
        
        # Overview stats
        stats['overview'] = {
            'total_products': len(self.df),
            'unique_sources': self.df['source'].nunique() if 'source' in self.df.columns else 0,
            'date_range': {
                'earliest': self.df['scraped_at'].min().isoformat() if 'scraped_at' in self.df.columns else None,
                'latest': self.df['scraped_at'].max().isoformat() if 'scraped_at' in self.df.columns else None
            }
        }
        
        # Price analysis
        if 'price' in self.df.columns:
            prices = self.df['price'].dropna()
            stats['price_analysis'] = {
                'summary': {
                    'mean': float(prices.mean()),
                    'median': float(prices.median()),
                    'std': float(prices.std()),
                    'min': float(prices.min()),
                    'max': float(prices.max())
                },
                'distribution': {
                    'under_100': int((prices < 100).sum()),
                    'under_500': int((prices < 500).sum()),
                    'under_1000': int((prices < 1000).sum()),
                    'over_1000': int((prices >= 1000).sum())
                }
            }
        
        # Source comparison
        if 'source' in self.df.columns:
            stats['source_comparison'] = {}
            for source in self.df['source'].unique():
                source_data = self.df[self.df['source'] == source]
                stats['source_comparison'][source] = {
                    'total_products': len(source_data),
                    'avg_price': float(source_data['price'].mean()) if 'price' in source_data.columns else None,
                    'data_quality_score': source_data['price'].notna().mean() if 'price' in source_data.columns else 0
                }
        
        return stats
    
    def _generate_report_metadata(self) -> Dict[str, Any]:
        """Generate metadata for the report."""
        if self.df is None or self.df.empty:
            return {
                'generated_at': datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                'total_products': 0,
                'total_sources': 0,
                'collection_period': 'No data',
                'data_quality_score': 0
            }
        
        # Calculate date range
        if 'created_at' in self.df.columns:
            date_range = f"{self.df['created_at'].min().strftime('%m/%d/%Y')} - {self.df['created_at'].max().strftime('%m/%d/%Y')}"
        else:
            date_range = "Unknown"
        
        # Calculate data quality score
        quality_score = 85  # Simplified calculation
        if 'price' in self.df.columns:
            price_completeness = self.df['price'].notna().mean() * 100
            quality_score = int(price_completeness)
        
        return {
            'generated_at': datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            'total_products': len(self.df),
            'total_sources': self.df['source'].nunique() if 'source' in self.df.columns else 0,
            'collection_period': date_range,
            'data_quality_score': quality_score
        }
    
    def _generate_executive_summary(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary based on statistics."""
        if not stats:
            return {
                'overview': 'No data available for analysis.',
                'key_findings': []
            }
        
        total_products = stats.get('overview', {}).get('total_products', 0)
        sources = stats.get('overview', {}).get('unique_sources', 0)
        
        overview = f"""
        This report presents a comprehensive analysis of {total_products:,} products collected from {sources} different e-commerce sources. 
        The data collection system successfully gathered product information including prices, titles, ratings, and metadata. 
        The analysis reveals important insights about pricing trends, source performance, and data quality metrics.
        """
        
        key_findings = []
        
        # Price analysis findings
        if 'price_analysis' in stats and stats['price_analysis']:
            avg_price = stats['price_analysis'].get('summary', {}).get('mean', 0)
            key_findings.append(f"Average product price across all sources: ${avg_price:.2f}")
            
            distribution = stats['price_analysis'].get('distribution', {})
            under_100 = distribution.get('under_100', 0)
            if under_100 > total_products * 0.5:
                key_findings.append(f"Majority of products ({under_100}) are priced under $100")
        
        # Source comparison findings
        if 'source_comparison' in stats:
            best_source = None
            max_products = 0
            for source, data in stats['source_comparison'].items():
                if data.get('total_products', 0) > max_products:
                    max_products = data['total_products']
                    best_source = source
            
            if best_source:
                key_findings.append(f"{best_source.title()} provided the most products ({max_products})")
        
        # Data quality findings
        if 'data_quality' in stats and stats['data_quality']:
            quality_score = stats['data_quality'].get('completeness_score', 0) * 100
            key_findings.append(f"Overall data quality score: {quality_score:.1f}%")
        
        return {
            'overview': overview.strip(),
            'key_findings': key_findings
        }
    
    def _convert_charts_to_base64(self, charts: Dict[str, str]) -> Dict[str, str]:
        """Convert chart image files to base64 for embedding in HTML."""
        chart_data = {}
        
        for chart_name, chart_path in charts.items():
            if chart_path.endswith('.png'):
                try:
                    with open(chart_path, 'rb') as f:
                        image_data = f.read()
                        base64_data = base64.b64encode(image_data).decode('utf-8')
                        chart_data[chart_name] = base64_data
                except Exception as e:
                    logger.error(f"Failed to convert chart {chart_name} to base64: {e}")
            else:
                # For HTML files (like interactive dashboard), keep the path
                chart_data[chart_name] = chart_path
        
        return chart_data
    
    def _generate_data_exports(self) -> Dict[str, str]:
        """Generate data export files and return their paths."""
        exports = {}
        
        if self.df is None or self.df.empty:
            return exports
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # CSV export
            csv_path = self.output_dir / f"products_data_{timestamp}.csv"
            self.df.to_csv(csv_path, index=False, encoding='utf-8')
            exports['csv'] = str(csv_path)
            
            # Excel export
            excel_path = self.output_dir / f"products_data_{timestamp}.xlsx"
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                self.df.to_excel(writer, sheet_name='Products', index=False)
                
                # Add summary sheet
                if len(self.df) > 0:
                    summary_data = {
                        'Metric': ['Total Products', 'Unique Sources', 'Average Price', 'Date Range'],
                        'Value': [
                            len(self.df),
                            self.df['source'].nunique() if 'source' in self.df.columns else 0,
                            f"${self.df['price'].mean():.2f}" if 'price' in self.df.columns else 'N/A',
                            f"{self.df['created_at'].min()} to {self.df['created_at'].max()}" if 'created_at' in self.df.columns else 'N/A'
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            exports['excel'] = str(excel_path)
            
            # JSON export
            json_path = self.output_dir / f"products_data_{timestamp}.json"
            self.df.to_json(json_path, orient='records', indent=2)
            exports['json'] = str(json_path)
            
            logger.info(f"📁 Generated {len(exports)} data export files")
            
        except Exception as e:
            logger.error(f"Data export generation failed: {e}")
        
        return exports
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if not stats:
            return recommendations
        
        # Data quality recommendations
        if 'data_quality' in stats:
            quality_score = stats['data_quality'].get('completeness_score', 0) * 100
            if quality_score < 90:
                recommendations.append(
                    f"Data completeness score is {quality_score:.1f}%. Consider improving data validation and extraction rules."
                )
            
            duplicate_rate = stats['data_quality'].get('duplicate_rate', 0)
            if duplicate_rate > 5:
                recommendations.append(
                    f"Duplicate rate is {duplicate_rate:.1f}%. Implement better deduplication strategies."
                )
        
        # Source performance recommendations
        if 'source_comparison' in stats:
            source_products = {}
            for source, data in stats['source_comparison'].items():
                source_products[source] = data.get('total_products', 0)
            
            if source_products:
                min_source = min(source_products, key=source_products.get)
                max_source = max(source_products, key=source_products.get)
                
                if source_products[max_source] > source_products[min_source] * 3:
                    recommendations.append(
                        f"Consider optimizing scraping strategy for {min_source} - it's underperforming compared to {max_source}."
                    )
        
        # Price analysis recommendations
        if 'price_analysis' in stats and stats['price_analysis']:
            outliers = stats['price_analysis'].get('outliers', {})
            iqr_outliers = outliers.get('iqr_outliers', {}).get('count', 0)
            if iqr_outliers > 0:
                recommendations.append(
                    f"Found {iqr_outliers} price outliers. Review data cleaning rules to handle extreme values."
                )
        
        # Collection velocity recommendations
        if 'trend_analysis' in stats and stats['trend_analysis']:
            velocity = stats['trend_analysis'].get('collection_velocity', {})
            avg_per_day = velocity.get('avg_products_per_day', 0)
            if avg_per_day < 100:
                recommendations.append(
                    f"Collection velocity is {avg_per_day:.1f} products/day. Consider parallel processing to increase throughput."
                )
        
        # General recommendations
        recommendations.extend([
            "Implement automated monitoring to track data quality metrics over time.",
            "Consider adding more data sources to increase coverage and comparison opportunities.",
            "Set up alerts for significant price changes or anomalies in the collected data.",
            "Regularly review and update scraping selectors to maintain data extraction accuracy."
        ])
        
        return recommendations
    
    def generate_summary_report(self) -> str:
        """Generate a simplified summary report."""
        try:
            # Simple template for summary
            summary_template = Template("""
            <html>
            <head><title>Summary Report</title></head>
            <body style="font-family: Arial, sans-serif; margin: 40px;">
                <h1>Data Collection Summary</h1>
                <p><strong>Total Products:</strong> {{ total_products }}</p>
                <p><strong>Sources:</strong> {{ sources }}</p>
                <p><strong>Generated:</strong> {{ timestamp }}</p>
            </body>
            </html>
            """)
            
            content = summary_template.render(
                total_products=len(self.df) if self.df is not None else 0,
                sources=self.df['source'].nunique() if self.df is not None and 'source' in self.df.columns else 0,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            summary_path = self.output_dir / "summary_report.html"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return str(summary_path)
            
        except Exception as e:
            logger.error(f"Summary report generation failed: {e}")
            return "" 