"""
📈 Data Visualization Module

Simple and effective data visualization using matplotlib and seaborn for the Multi-Source Data Collection System.
Creates basic charts and graphs for scraped product data analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json
from pathlib import Path
import logging
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Set style for better-looking plots
plt.style.use('default')
sns.set_palette("husl")

class DataVisualizer:
    """
    📈 Simple data visualization for scraped product data.
    
    Features:
    - Price distribution charts
    - Source comparison visualizations  
    - Basic trend analysis plots
    - Export to PNG files
    """
    
    def __init__(self, df: pd.DataFrame):
        """Initialize visualizer with DataFrame."""
        self.df = df
        
        # Create output directories
        self.output_dir = Path("data_output/reports/charts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_all_charts(self) -> Dict[str, str]:
        """
        Create all basic charts for the report.
            
        Returns:
            Dictionary mapping chart names to file paths
        """
        charts = {}
        
        try:
            # Price analysis
            if 'price' in self.df.columns:
                charts['price_distribution'] = self._create_price_distribution()
                charts['price_by_source'] = self._create_price_by_source()
            
            # Source analysis
            if 'source' in self.df.columns:
                charts['source_comparison'] = self._create_source_comparison()
            
            # Time trends
            if 'created_at' in self.df.columns or 'scraped_at' in self.df.columns:
                charts['collection_trends'] = self._create_collection_trends()
            
            logger.info(f"📈 Created {len(charts)} charts")
            return charts
                
        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            return {}
    
    def _create_price_distribution(self) -> str:
        """Create price distribution chart."""
        try:
            plt.figure(figsize=(12, 8))
            
            # Get price data
            prices = self.df['price'].dropna()
            
            # Create subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Price Distribution Analysis', fontsize=16, fontweight='bold')
            
            # 1. Histogram
            ax1.hist(prices, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            ax1.set_title('Price Distribution')
            ax1.set_xlabel('Price ($)')
            ax1.set_ylabel('Frequency')
            ax1.grid(True, alpha=0.3)
            
            # 2. Box plot
            ax2.boxplot(prices, orientation='vertical')
            ax2.set_title('Price Box Plot')
            ax2.set_ylabel('Price ($)')
            ax2.grid(True, alpha=0.3)
            
            # 3. Price ranges
            ranges = ['<$100', '$100-500', '$500-1000', '>$1000']
            counts = [
                (prices < 100).sum(),
                ((prices >= 100) & (prices < 500)).sum(),
                ((prices >= 500) & (prices < 1000)).sum(),
                (prices >= 1000).sum()
            ]
            
            ax3.bar(ranges, counts, color='lightgreen', alpha=0.7)
            ax3.set_title('Products by Price Range')
            ax3.set_xlabel('Price Range')
            ax3.set_ylabel('Count')
            ax3.tick_params(axis='x', rotation=45)
            
            # 4. Statistics table
            ax4.axis('off')
            stats_data = [
                ['Mean', f'${prices.mean():.2f}'],
                ['Median', f'${prices.median():.2f}'],
                ['Min', f'${prices.min():.2f}'],
                ['Max', f'${prices.max():.2f}'],
                ['Std Dev', f'${prices.std():.2f}']
            ]
            
            table = ax4.table(cellText=stats_data,
                             colLabels=['Statistic', 'Value'],
                             cellLoc='center',
                             loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1.2, 1.5)
            ax4.set_title('Price Statistics')
            
            plt.tight_layout()
            chart_path = self.output_dir / "price_distribution.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
                
        except Exception as e:
            logger.error(f"Price distribution chart failed: {e}")
            return ""
    
    def _create_price_by_source(self) -> str:
        """Create price comparison by source."""
        try:
            if 'source' not in self.df.columns:
                return ""
            
            plt.figure(figsize=(12, 8))
            
            # Box plot by source
            price_data = self.df[self.df['price'].notna()]
            sources = price_data['source'].unique()
            
            source_prices = [price_data[price_data['source'] == source]['price'] 
                           for source in sources]
            
            plt.boxplot(source_prices, tick_labels=sources)
            plt.title('Price Distribution by Source', fontsize=14, fontweight='bold')
            plt.xlabel('Source')
            plt.ylabel('Price ($)')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            
            # Add mean values as points
            for i, source in enumerate(sources):
                source_data = price_data[price_data['source'] == source]
                mean_price = source_data['price'].mean()
                plt.plot(i+1, mean_price, 'ro', markersize=8, label=f'{source} avg: ${mean_price:.2f}')
            
            plt.legend()
            plt.tight_layout()
            
            chart_path = self.output_dir / "price_by_source.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
                
        except Exception as e:
            logger.error(f"Price by source chart failed: {e}")
            return ""
    
    def _create_source_comparison(self) -> str:
        """Create source comparison chart."""
        try:
            plt.figure(figsize=(12, 8))
            
            # Create subplots for source analysis
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Source Comparison Analysis', fontsize=16, fontweight='bold')
            
            # 1. Product count by source
            source_counts = self.df['source'].value_counts()
            colors = sns.color_palette("husl", len(source_counts))
            
            bars = ax1.bar(source_counts.index, source_counts.values, color=colors)
            ax1.set_title('Product Count by Source')
            ax1.set_xlabel('Source')
            ax1.set_ylabel('Number of Products')
            ax1.tick_params(axis='x', rotation=45)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
            
            # 2. Average price by source
            if 'price' in self.df.columns:
                avg_prices = self.df.groupby('source')['price'].mean()
                bars = ax2.bar(avg_prices.index, avg_prices.values, color=colors)
                ax2.set_title('Average Price by Source')
                ax2.set_xlabel('Source')
                ax2.set_ylabel('Average Price ($)')
                ax2.tick_params(axis='x', rotation=45)
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'${height:.0f}', ha='center', va='bottom')
            
            # 3. Source distribution pie chart
            ax3.pie(source_counts.values, labels=source_counts.index, autopct='%1.1f%%',
                   colors=colors, startangle=90)
            ax3.set_title('Source Distribution')
            
            # 4. Data completeness by source
            ax4.axis('off')
            completeness_data = []
            for source in self.df['source'].unique():
                source_data = self.df[self.df['source'] == source]
                price_complete = source_data['price'].notna().mean() * 100
                title_complete = source_data['title'].notna().mean() * 100
                completeness_data.append([source, f'{price_complete:.1f}%', f'{title_complete:.1f}%'])
            
            table = ax4.table(cellText=completeness_data,
                             colLabels=['Source', 'Price Complete', 'Title Complete'],
                             cellLoc='center',
                             loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.5)
            ax4.set_title('Data Completeness by Source')
            
            plt.tight_layout()
            chart_path = self.output_dir / "source_comparison.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"Source comparison chart failed: {e}")
            return ""
    
    def _create_collection_trends(self) -> str:
        """Create collection trends over time."""
        try:
            date_col = 'created_at' if 'created_at' in self.df.columns else 'scraped_at'
            
            plt.figure(figsize=(12, 8))
            
            # Daily collection counts
            daily_counts = self.df.groupby(self.df[date_col].dt.date).size()
            
            plt.plot(daily_counts.index, daily_counts.values, marker='o', linewidth=2)
            plt.title('Daily Data Collection Trend', fontsize=14, fontweight='bold')
            plt.xlabel('Date')
            plt.ylabel('Products Collected')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            
            # Add trend line
            if len(daily_counts) > 1:
                x = np.arange(len(daily_counts))
                z = np.polyfit(x, daily_counts.values, 1)
                p = np.poly1d(z)
                plt.plot(daily_counts.index, p(x), "r--", alpha=0.8, 
                        label=f'Trend: {z[0]:.1f} products/day')
                plt.legend()
            
            plt.tight_layout()
            
            chart_path = self.output_dir / "collection_trends.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"Collection trends chart failed: {e}")
            return "" 