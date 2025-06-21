"""
Statistical Analysis Module

This module provides comprehensive statistical analysis of scraped product data,
including descriptive statistics, price analysis, and market insights.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path

from ..data.database import DatabaseManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class ProductStatistics:
    """
    Comprehensive statistical analysis for product data.
    
    Provides statistical insights including:
    - Descriptive statistics
    - Price distributions
    - Market comparison
    - Trend analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize statistics analyzer."""
        self.config = config
        self.db_manager = DatabaseManager(config)
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """
        Get basic descriptive statistics for all products.
        
        Returns:
            Dictionary with basic statistics
        """
        try:
            # Get product data
            products_df = self._get_products_dataframe()
            
            if products_df.empty:
                return {'error': 'No product data available'}
            
            # Calculate basic statistics
            stats = {
                'total_products': len(products_df),
                'unique_sources': products_df['source'].nunique(),
                'sources_breakdown': products_df['source'].value_counts().to_dict(),
                'date_range': {
                    'earliest': products_df['scraped_at'].min().isoformat() if not products_df['scraped_at'].empty else None,
                    'latest': products_df['scraped_at'].max().isoformat() if not products_df['scraped_at'].empty else None
                },
                'keywords_analyzed': products_df['search_keyword'].unique().tolist()
            }
            
            # Price statistics (only for products with prices)
            price_data = products_df[products_df['price'].notna()]
            if not price_data.empty:
                stats['price_statistics'] = {
                    'total_with_prices': len(price_data),
                    'mean_price': float(price_data['price'].mean()),
                    'median_price': float(price_data['price'].median()),
                    'min_price': float(price_data['price'].min()),
                    'max_price': float(price_data['price'].max()),
                    'std_price': float(price_data['price'].std()),
                    'price_quartiles': {
                        'q1': float(price_data['price'].quantile(0.25)),
                        'q2': float(price_data['price'].quantile(0.5)),
                        'q3': float(price_data['price'].quantile(0.75))
                    }
                }
            
            # Rating statistics
            rating_data = products_df[products_df['rating'].notna()]
            if not rating_data.empty:
                stats['rating_statistics'] = {
                    'total_with_ratings': len(rating_data),
                    'mean_rating': float(rating_data['rating'].mean()),
                    'median_rating': float(rating_data['rating'].median()),
                    'rating_distribution': rating_data['rating'].value_counts().sort_index().to_dict()
                }
            
            logger.info(f"Generated basic statistics for {stats['total_products']} products")
            return stats
            
        except Exception as e:
            logger.error(f"Error generating basic statistics: {e}")
            return {'error': str(e)}
    
    def get_price_analysis_by_source(self) -> Dict[str, Any]:
        """
        Analyze price distributions by source.
        
        Returns:
            Price analysis breakdown by source
        """
        try:
            products_df = self._get_products_dataframe()
            price_data = products_df[products_df['price'].notna()]
            
            if price_data.empty:
                return {'error': 'No price data available'}
            
            analysis = {}
            
            for source in price_data['source'].unique():
                source_data = price_data[price_data['source'] == source]
                
                analysis[source] = {
                    'product_count': len(source_data),
                    'price_stats': {
                        'mean': float(source_data['price'].mean()),
                        'median': float(source_data['price'].median()),
                        'min': float(source_data['price'].min()),
                        'max': float(source_data['price'].max()),
                        'std': float(source_data['price'].std())
                    },
                    'price_ranges': {
                        'under_50': len(source_data[source_data['price'] < 50]),
                        '50_to_200': len(source_data[(source_data['price'] >= 50) & (source_data['price'] < 200)]),
                        '200_to_500': len(source_data[(source_data['price'] >= 200) & (source_data['price'] < 500)]),
                        '500_to_1000': len(source_data[(source_data['price'] >= 500) & (source_data['price'] < 1000)]),
                        'over_1000': len(source_data[source_data['price'] >= 1000])
                    }
                }
            
            # Add comparative analysis
            analysis['comparison'] = {
                'cheapest_source': price_data.groupby('source')['price'].mean().idxmin(),
                'most_expensive_source': price_data.groupby('source')['price'].mean().idxmax(),
                'price_variance_by_source': price_data.groupby('source')['price'].std().to_dict()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in price analysis by source: {e}")
            return {'error': str(e)}
    
    def get_keyword_analysis(self) -> Dict[str, Any]:
        """
        Analyze products by search keywords.
        
        Returns:
            Keyword-based analysis
        """
        try:
            products_df = self._get_products_dataframe()
            
            if products_df.empty:
                return {'error': 'No product data available'}
            
            analysis = {}
            
            for keyword in products_df['search_keyword'].unique():
                keyword_data = products_df[products_df['search_keyword'] == keyword]
                keyword_price_data = keyword_data[keyword_data['price'].notna()]
                
                keyword_stats = {
                    'total_products': len(keyword_data),
                    'sources': keyword_data['source'].value_counts().to_dict(),
                    'avg_products_per_page': keyword_data.groupby(['source', 'page_number']).size().mean()
                }
                
                if not keyword_price_data.empty:
                    keyword_stats['price_analysis'] = {
                        'mean_price': float(keyword_price_data['price'].mean()),
                        'median_price': float(keyword_price_data['price'].median()),
                        'price_range': {
                            'min': float(keyword_price_data['price'].min()),
                            'max': float(keyword_price_data['price'].max())
                        },
                        'cheapest_source': keyword_price_data.groupby('source')['price'].mean().idxmin(),
                        'most_expensive_source': keyword_price_data.groupby('source')['price'].mean().idxmax()
                    }
                
                # Rating analysis for keyword
                keyword_rating_data = keyword_data[keyword_data['rating'].notna()]
                if not keyword_rating_data.empty:
                    keyword_stats['rating_analysis'] = {
                        'avg_rating': float(keyword_rating_data['rating'].mean()),
                        'highest_rated_source': keyword_rating_data.groupby('source')['rating'].mean().idxmax(),
                        'rating_distribution': keyword_rating_data['rating'].value_counts().sort_index().to_dict()
                    }
                
                analysis[keyword] = keyword_stats
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in keyword analysis: {e}")
            return {'error': str(e)}
    
    def get_market_insights(self) -> Dict[str, Any]:
        """
        Generate market insights and recommendations.
        
        Returns:
            Market insights and analysis
        """
        try:
            products_df = self._get_products_dataframe()
            price_data = products_df[products_df['price'].notna()]
            
            if price_data.empty:
                return {'error': 'No price data available for market insights'}
            
            insights = {}
            
            # Overall market insights
            insights['market_overview'] = {
                'total_market_size': len(price_data),
                'average_market_price': float(price_data['price'].mean()),
                'price_volatility': float(price_data['price'].std() / price_data['price'].mean()),
                'competitive_landscape': len(price_data['source'].unique())
            }
            
            # Source competitiveness
            source_analysis = price_data.groupby('source').agg({
                'price': ['mean', 'count', 'std'],
                'rating': 'mean'
            }).round(2)
            
            insights['source_competitiveness'] = {}
            for source in source_analysis.index:
                insights['source_competitiveness'][source] = {
                    'avg_price': float(source_analysis.loc[source, ('price', 'mean')]),
                    'product_variety': int(source_analysis.loc[source, ('price', 'count')]),
                    'price_consistency': float(1 / (source_analysis.loc[source, ('price', 'std')] + 0.01)),  # Lower std = higher consistency
                    'avg_rating': float(source_analysis.loc[source, ('rating', 'mean')]) if not pd.isna(source_analysis.loc[source, ('rating', 'mean')]) else None
                }
            
            # Best value recommendations
            insights['recommendations'] = self._generate_recommendations(price_data)
            
            # Market trends (if we have time-series data)
            if 'scraped_at' in products_df.columns:
                insights['temporal_trends'] = self._analyze_temporal_trends(products_df)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating market insights: {e}")
            return {'error': str(e)}
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """
        Generate data quality assessment report.
        
        Returns:
            Data quality metrics and issues
        """
        try:
            products_df = self._get_products_dataframe()
            
            if products_df.empty:
                return {'error': 'No data available for quality assessment'}
            
            total_records = len(products_df)
            
            quality_report = {
                'total_records': total_records,
                'completeness': {
                    'title': {
                        'filled': int((~products_df['title'].isna()).sum()),
                        'missing': int(products_df['title'].isna().sum()),
                        'percentage': float((~products_df['title'].isna()).sum() / total_records * 100)
                    },
                    'price': {
                        'filled': int((~products_df['price'].isna()).sum()),
                        'missing': int(products_df['price'].isna().sum()),
                        'percentage': float((~products_df['price'].isna()).sum() / total_records * 100)
                    },
                    'rating': {
                        'filled': int((~products_df['rating'].isna()).sum()),
                        'missing': int(products_df['rating'].isna().sum()),
                        'percentage': float((~products_df['rating'].isna()).sum() / total_records * 100)
                    },
                    'url': {
                        'filled': int((~products_df['url'].isna()).sum()),
                        'missing': int(products_df['url'].isna().sum()),
                        'percentage': float((~products_df['url'].isna()).sum() / total_records * 100)
                    }
                },
                'data_integrity': {
                    'duplicate_titles': int(products_df['title'].duplicated().sum()),
                    'duplicate_urls': int(products_df['url'].duplicated().sum()),
                    'invalid_prices': int((products_df['price'] < 0).sum()) if 'price' in products_df.columns else 0,
                    'invalid_ratings': int((products_df['rating'] > 5).sum()) if 'rating' in products_df.columns else 0
                },
                'source_coverage': products_df['source'].value_counts().to_dict(),
                'keyword_coverage': products_df['search_keyword'].value_counts().to_dict()
            }
            
            # Calculate overall quality score
            completeness_scores = [
                quality_report['completeness'][field]['percentage'] 
                for field in ['title', 'price', 'url']
            ]
            quality_report['overall_quality_score'] = float(np.mean(completeness_scores))
            
            return quality_report
            
        except Exception as e:
            logger.error(f"Error generating data quality report: {e}")
            return {'error': str(e)}
    
    def _get_products_dataframe(self) -> pd.DataFrame:
        """
        Get products data as pandas DataFrame.
        
        Returns:
            DataFrame with product data
        """
        try:
            with self.db_manager.get_session() as session:
                # Get all products
                from ..data.models import Product
                
                products = session.query(Product).all()
                
                if not products:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                data = []
                for product in products:
                    data.append({
                        'id': product.id,
                        'source': product.source,
                        'title': product.title,
                        'url': product.url,
                        'price': product.price,
                        'rating': product.rating,
                        'search_keyword': product.search_keyword,
                        'page_number': product.page_number,
                        'position_on_page': product.position_on_page,
                        'scraped_at': product.scraped_at,
                        'scraper_type': product.scraper_type
                    })
                
                df = pd.DataFrame(data)
                
                # Convert data types
                if not df.empty:
                    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
                    df['price'] = pd.to_numeric(df['price'], errors='coerce')
                    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting products DataFrame: {e}")
            return pd.DataFrame()
    
    def _generate_recommendations(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Generate shopping recommendations based on analysis."""
        try:
            recommendations = {}
            
            # Best value by source
            source_value_score = price_data.groupby('source').apply(
                lambda x: (x['rating'].mean() if not x['rating'].isna().all() else 3.0) / (x['price'].mean() / 100)
            ).sort_values(ascending=False)
            
            recommendations['best_value_sources'] = source_value_score.head(3).to_dict()
            
            # Price range recommendations
            price_percentiles = price_data['price'].quantile([0.25, 0.5, 0.75])
            recommendations['price_ranges'] = {
                'budget_friendly': f"Under ${price_percentiles[0.25]:.2f}",
                'mid_range': f"${price_percentiles[0.25]:.2f} - ${price_percentiles[0.75]:.2f}",
                'premium': f"Over ${price_percentiles[0.75]:.2f}"
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {}
    
    def _analyze_temporal_trends(self, products_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal trends in the data."""
        try:
            trends = {}
            
            # Daily scraping activity
            daily_activity = products_df.groupby(products_df['scraped_at'].dt.date).size()
            trends['daily_scraping_activity'] = daily_activity.to_dict()
            
            # Price trends by day (if enough temporal data)
            if len(daily_activity) > 1:
                daily_price_trends = products_df.groupby(products_df['scraped_at'].dt.date)['price'].mean()
                trends['daily_average_prices'] = daily_price_trends.to_dict()
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing temporal trends: {e}")
            return {} 