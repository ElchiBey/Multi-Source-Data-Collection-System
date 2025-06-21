"""
Data Visualization Module

This module provides comprehensive visualization capabilities for product data analysis,
including price distributions, source comparisons, and trend analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import base64
from io import BytesIO

from ..utils.logger import setup_logger
from .statistics import ProductStatistics

logger = setup_logger(__name__)

class DataVisualizer:
    """
    Comprehensive data visualization for product analysis.
    
    Creates various charts and graphs including:
    - Price distribution histograms
    - Source comparison charts
    - Rating distributions
    - Market trend visualizations
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize visualizer with configuration."""
        self.config = config
        self.stats = ProductStatistics(config)
        
        # Set up matplotlib style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Configure output directory
        self.output_dir = Path(config.get('export', {}).get('output_dir', 'data_output')) / 'reports'
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_price_distribution_chart(self, save_path: Optional[str] = None) -> str:
        """
        Create price distribution histogram.
        
        Args:
            save_path: Optional path to save chart
            
        Returns:
            Path to saved chart or base64 encoded image
        """
        try:
            products_df = self.stats._get_products_dataframe()
            price_data = products_df[products_df['price'].notna()]
            
            if price_data.empty:
                logger.warning("No price data available for distribution chart")
                return None
            
            # Create figure with subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Price Distribution Analysis', fontsize=16, fontweight='bold')
            
            # Overall price distribution
            axes[0, 0].hist(price_data['price'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            axes[0, 0].set_title('Overall Price Distribution')
            axes[0, 0].set_xlabel('Price ($)')
            axes[0, 0].set_ylabel('Frequency')
            axes[0, 0].grid(True, alpha=0.3)
            
            # Box plot by source
            if len(price_data['source'].unique()) > 1:
                price_data.boxplot(column='price', by='source', ax=axes[0, 1])
                axes[0, 1].set_title('Price Distribution by Source')
                axes[0, 1].set_xlabel('Source')
                axes[0, 1].set_ylabel('Price ($)')
            else:
                axes[0, 1].text(0.5, 0.5, 'Single source data', ha='center', va='center', transform=axes[0, 1].transAxes)
                axes[0, 1].set_title('Price Distribution by Source')
            
            # Price range distribution
            price_ranges = ['<$50', '$50-200', '$200-500', '$500-1000', '>$1000']
            price_counts = [
                len(price_data[price_data['price'] < 50]),
                len(price_data[(price_data['price'] >= 50) & (price_data['price'] < 200)]),
                len(price_data[(price_data['price'] >= 200) & (price_data['price'] < 500)]),
                len(price_data[(price_data['price'] >= 500) & (price_data['price'] < 1000)]),
                len(price_data[price_data['price'] >= 1000])
            ]
            
            axes[1, 0].bar(price_ranges, price_counts, color='lightgreen', alpha=0.7)
            axes[1, 0].set_title('Product Count by Price Range')
            axes[1, 0].set_xlabel('Price Range')
            axes[1, 0].set_ylabel('Product Count')
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # Average price by source
            if len(price_data['source'].unique()) > 1:
                avg_prices = price_data.groupby('source')['price'].mean().sort_values()
                axes[1, 1].bar(avg_prices.index, avg_prices.values, color='coral', alpha=0.7)
                axes[1, 1].set_title('Average Price by Source')
                axes[1, 1].set_xlabel('Source')
                axes[1, 1].set_ylabel('Average Price ($)')
                axes[1, 1].tick_params(axis='x', rotation=45)
            else:
                axes[1, 1].text(0.5, 0.5, 'Single source data', ha='center', va='center', transform=axes[1, 1].transAxes)
                axes[1, 1].set_title('Average Price by Source')
            
            plt.tight_layout()
            
            # Save or return base64
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                # Return base64 encoded image
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                return f"data:image/png;base64,{image_base64}"
                
        except Exception as e:
            logger.error(f"Error creating price distribution chart: {e}")
            return None
    
    def create_source_comparison_chart(self, save_path: Optional[str] = None) -> str:
        """
        Create source comparison visualization.
        
        Args:
            save_path: Optional path to save chart
            
        Returns:
            Path to saved chart or base64 encoded image
        """
        try:
            products_df = self.stats._get_products_dataframe()
            
            if products_df.empty:
                logger.warning("No data available for source comparison chart")
                return None
            
            # Create figure with subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Source Comparison Analysis', fontsize=16, fontweight='bold')
            
            # Product count by source
            source_counts = products_df['source'].value_counts()
            axes[0, 0].pie(source_counts.values, labels=source_counts.index, autopct='%1.1f%%', startangle=90)
            axes[0, 0].set_title('Product Distribution by Source')
            
            # Average rating by source (if rating data exists)
            rating_data = products_df[products_df['rating'].notna()]
            if not rating_data.empty and len(rating_data['source'].unique()) > 1:
                avg_ratings = rating_data.groupby('source')['rating'].mean().sort_values(ascending=False)
                axes[0, 1].bar(avg_ratings.index, avg_ratings.values, color='gold', alpha=0.7)
                axes[0, 1].set_title('Average Rating by Source')
                axes[0, 1].set_xlabel('Source')
                axes[0, 1].set_ylabel('Average Rating')
                axes[0, 1].set_ylim(0, 5)
                axes[0, 1].tick_params(axis='x', rotation=45)
            else:
                axes[0, 1].text(0.5, 0.5, 'No rating data available', ha='center', va='center', transform=axes[0, 1].transAxes)
                axes[0, 1].set_title('Average Rating by Source')
            
            # Price vs Rating scatter (if both exist)
            price_rating_data = products_df[(products_df['price'].notna()) & (products_df['rating'].notna())]
            if not price_rating_data.empty:
                for source in price_rating_data['source'].unique():
                    source_data = price_rating_data[price_rating_data['source'] == source]
                    axes[1, 0].scatter(source_data['price'], source_data['rating'], alpha=0.6, label=source, s=30)
                
                axes[1, 0].set_title('Price vs Rating by Source')
                axes[1, 0].set_xlabel('Price ($)')
                axes[1, 0].set_ylabel('Rating')
                axes[1, 0].legend()
                axes[1, 0].grid(True, alpha=0.3)
            else:
                axes[1, 0].text(0.5, 0.5, 'No price/rating data', ha='center', va='center', transform=axes[1, 0].transAxes)
                axes[1, 0].set_title('Price vs Rating by Source')
            
            # Data completeness by source
            completeness_data = []
            for source in products_df['source'].unique():
                source_data = products_df[products_df['source'] == source]
                completeness = {
                    'Source': source,
                    'Title': (source_data['title'].notna().sum() / len(source_data)) * 100,
                    'Price': (source_data['price'].notna().sum() / len(source_data)) * 100,
                    'Rating': (source_data['rating'].notna().sum() / len(source_data)) * 100,
                    'URL': (source_data['url'].notna().sum() / len(source_data)) * 100
                }
                completeness_data.append(completeness)
            
            completeness_df = pd.DataFrame(completeness_data)
            completeness_df.set_index('Source', inplace=True)
            
            # Create heatmap
            sns.heatmap(completeness_df.T, annot=True, fmt='.1f', cmap='RdYlGn', 
                       ax=axes[1, 1], cbar_kws={'label': 'Completeness %'})
            axes[1, 1].set_title('Data Completeness by Source')
            axes[1, 1].set_xlabel('Source')
            axes[1, 1].set_ylabel('Data Field')
            
            plt.tight_layout()
            
            # Save or return base64
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                return f"data:image/png;base64,{image_base64}"
                
        except Exception as e:
            logger.error(f"Error creating source comparison chart: {e}")
            return None
    
    def create_keyword_analysis_chart(self, save_path: Optional[str] = None) -> str:
        """
        Create keyword analysis visualization.
        
        Args:
            save_path: Optional path to save chart
            
        Returns:
            Path to saved chart or base64 encoded image
        """
        try:
            products_df = self.stats._get_products_dataframe()
            
            if products_df.empty:
                logger.warning("No data available for keyword analysis chart")
                return None
            
            # Create figure
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Keyword Analysis', fontsize=16, fontweight='bold')
            
            # Product count by keyword
            keyword_counts = products_df['search_keyword'].value_counts()
            axes[0, 0].bar(keyword_counts.index, keyword_counts.values, color='lightblue', alpha=0.7)
            axes[0, 0].set_title('Product Count by Keyword')
            axes[0, 0].set_xlabel('Keyword')
            axes[0, 0].set_ylabel('Product Count')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Average price by keyword
            price_data = products_df[products_df['price'].notna()]
            if not price_data.empty and len(price_data['search_keyword'].unique()) > 1:
                avg_prices_keyword = price_data.groupby('search_keyword')['price'].mean().sort_values()
                axes[0, 1].bar(avg_prices_keyword.index, avg_prices_keyword.values, color='lightcoral', alpha=0.7)
                axes[0, 1].set_title('Average Price by Keyword')
                axes[0, 1].set_xlabel('Keyword')
                axes[0, 1].set_ylabel('Average Price ($)')
                axes[0, 1].tick_params(axis='x', rotation=45)
            else:
                axes[0, 1].text(0.5, 0.5, 'Insufficient price data', ha='center', va='center', transform=axes[0, 1].transAxes)
                axes[0, 1].set_title('Average Price by Keyword')
            
            # Source distribution for each keyword
            keyword_source_dist = products_df.groupby(['search_keyword', 'source']).size().unstack(fill_value=0)
            if not keyword_source_dist.empty:
                keyword_source_dist.plot(kind='bar', stacked=True, ax=axes[1, 0], alpha=0.8)
                axes[1, 0].set_title('Source Distribution by Keyword')
                axes[1, 0].set_xlabel('Keyword')
                axes[1, 0].set_ylabel('Product Count')
                axes[1, 0].legend(title='Source', bbox_to_anchor=(1.05, 1), loc='upper left')
                axes[1, 0].tick_params(axis='x', rotation=45)
            else:
                axes[1, 0].text(0.5, 0.5, 'No distribution data', ha='center', va='center', transform=axes[1, 0].transAxes)
                axes[1, 0].set_title('Source Distribution by Keyword')
            
            # Price range distribution by keyword
            if not price_data.empty:
                price_ranges = ['<$50', '$50-200', '$200-500', '$500+']
                keyword_price_ranges = {}
                
                for keyword in price_data['search_keyword'].unique():
                    keyword_prices = price_data[price_data['search_keyword'] == keyword]['price']
                    keyword_price_ranges[keyword] = [
                        len(keyword_prices[keyword_prices < 50]),
                        len(keyword_prices[(keyword_prices >= 50) & (keyword_prices < 200)]),
                        len(keyword_prices[(keyword_prices >= 200) & (keyword_prices < 500)]),
                        len(keyword_prices[keyword_prices >= 500])
                    ]
                
                # Create stacked bar chart
                bottom = np.zeros(len(keyword_price_ranges))
                colors = ['lightgreen', 'yellow', 'orange', 'red']
                
                for i, price_range in enumerate(price_ranges):
                    values = [keyword_price_ranges[keyword][i] for keyword in keyword_price_ranges.keys()]
                    axes[1, 1].bar(list(keyword_price_ranges.keys()), values, bottom=bottom, 
                                 label=price_range, color=colors[i], alpha=0.7)
                    bottom += values
                
                axes[1, 1].set_title('Price Range Distribution by Keyword')
                axes[1, 1].set_xlabel('Keyword')
                axes[1, 1].set_ylabel('Product Count')
                axes[1, 1].legend()
                axes[1, 1].tick_params(axis='x', rotation=45)
            else:
                axes[1, 1].text(0.5, 0.5, 'No price data', ha='center', va='center', transform=axes[1, 1].transAxes)
                axes[1, 1].set_title('Price Range Distribution by Keyword')
            
            plt.tight_layout()
            
            # Save or return base64
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                return f"data:image/png;base64,{image_base64}"
                
        except Exception as e:
            logger.error(f"Error creating keyword analysis chart: {e}")
            return None
    
    def create_interactive_dashboard(self) -> str:
        """
        Create interactive Plotly dashboard.
        
        Returns:
            HTML string with interactive dashboard
        """
        try:
            products_df = self.stats._get_products_dataframe()
            
            if products_df.empty:
                return "<html><body><h1>No data available for dashboard</h1></body></html>"
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Price Distribution', 'Source Comparison', 
                              'Price vs Rating', 'Keyword Analysis'),
                specs=[[{"type": "histogram"}, {"type": "bar"}],
                       [{"type": "scatter"}, {"type": "bar"}]]
            )
            
            # Price distribution
            price_data = products_df[products_df['price'].notna()]
            if not price_data.empty:
                fig.add_trace(
                    go.Histogram(x=price_data['price'], name='Price Distribution', 
                               nbinsx=30, marker_color='skyblue', opacity=0.7),
                    row=1, col=1
                )
            
            # Source comparison
            source_counts = products_df['source'].value_counts()
            fig.add_trace(
                go.Bar(x=source_counts.index, y=source_counts.values, 
                      name='Product Count', marker_color='lightgreen'),
                row=1, col=2
            )
            
            # Price vs Rating scatter
            price_rating_data = products_df[(products_df['price'].notna()) & (products_df['rating'].notna())]
            if not price_rating_data.empty:
                for source in price_rating_data['source'].unique():
                    source_data = price_rating_data[price_rating_data['source'] == source]
                    fig.add_trace(
                        go.Scatter(x=source_data['price'], y=source_data['rating'],
                                 mode='markers', name=f'{source}', opacity=0.7),
                        row=2, col=1
                    )
            
            # Keyword analysis
            keyword_counts = products_df['search_keyword'].value_counts()
            fig.add_trace(
                go.Bar(x=keyword_counts.index, y=keyword_counts.values,
                      name='Keyword Count', marker_color='coral'),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                title_text="Product Analysis Dashboard",
                title_x=0.5,
                height=800,
                showlegend=True
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="Count", row=1, col=1)
            
            fig.update_xaxes(title_text="Source", row=1, col=2)
            fig.update_yaxes(title_text="Product Count", row=1, col=2)
            
            fig.update_xaxes(title_text="Price ($)", row=2, col=1)
            fig.update_yaxes(title_text="Rating", row=2, col=1)
            
            fig.update_xaxes(title_text="Keyword", row=2, col=2)
            fig.update_yaxes(title_text="Product Count", row=2, col=2)
            
            # Convert to HTML
            html_content = fig.to_html(include_plotlyjs=True)
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error creating interactive dashboard: {e}")
            return f"<html><body><h1>Error creating dashboard: {e}</h1></body></html>"
    
    def generate_all_charts(self) -> Dict[str, str]:
        """
        Generate all visualization charts.
        
        Returns:
            Dictionary with chart names and their file paths/base64 data
        """
        try:
            charts = {}
            
            # Generate all charts
            charts['price_distribution'] = self.create_price_distribution_chart(
                save_path=str(self.output_dir / 'price_distribution.png')
            )
            
            charts['source_comparison'] = self.create_source_comparison_chart(
                save_path=str(self.output_dir / 'source_comparison.png')
            )
            
            charts['keyword_analysis'] = self.create_keyword_analysis_chart(
                save_path=str(self.output_dir / 'keyword_analysis.png')
            )
            
            # Generate interactive dashboard
            dashboard_html = self.create_interactive_dashboard()
            dashboard_path = self.output_dir / 'interactive_dashboard.html'
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_html)
            charts['interactive_dashboard'] = str(dashboard_path)
            
            logger.info(f"Generated {len(charts)} visualization charts")
            return charts
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
            return {} 