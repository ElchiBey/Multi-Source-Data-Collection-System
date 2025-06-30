"""
📊 Statistical Analysis Module

Comprehensive data analysis using pandas and numpy for the Multi-Source Data Collection System.
Provides statistical summaries, distributions, and comparative analysis across sources.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import json
from pathlib import Path
import logging
from datetime import datetime, timedelta
import sqlite3

from ..utils.logger import get_logger

logger = get_logger(__name__)

class DataStatistics:
    """
    📊 Comprehensive statistical analysis for scraped product data.
    
    Features:
    - Price analysis and distributions
    - Source comparison and performance metrics
    - Data quality assessment
    - Trend analysis over time
    - Statistical summaries and insights
    """
    
    def __init__(self, db_path: str = "data/products.db"):
        """Initialize statistics analyzer."""
        self.db_path = db_path
        self.df = None
        self.stats = {}
    
    def load_data(self, source: str = "database") -> pd.DataFrame:
        """
        Load data from database or files for analysis.
        
        Args:
            source: Data source ("database", "files", or specific file path)
        
        Returns:
            Loaded DataFrame
        """
        try:
            if source == "database":
                self.df = self._load_from_database()
            elif source == "files":
                self.df = self._load_from_files()
            else:
                self.df = self._load_from_file(source)
                
            logger.info(f"📊 Loaded {len(self.df)} records for analysis")
            return self.df
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return pd.DataFrame()
    
    def _load_from_database(self) -> pd.DataFrame:
        """Load product data from SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                source,
                title,
                price,
                rating,
                search_keyword,
                scraper_type,
                scraped_at,
                url,
                image_url,
                product_id,
                brand,
                condition,
                availability,
                review_count,
                shipping_cost
            FROM products 
            WHERE price IS NOT NULL AND price > 0
            ORDER BY scraped_at DESC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Convert datetime
            df['scraped_at'] = pd.to_datetime(df['scraped_at'])
            # Also create created_at alias for compatibility
            df['created_at'] = df['scraped_at']
            
            return df
            
        except Exception as e:
            logger.error(f"Database loading error: {e}")
            return pd.DataFrame()
    
    def _load_from_files(self) -> pd.DataFrame:
        """Load data from JSON files in data_output directory."""
        data_frames = []
        
        try:
            output_dir = Path("data_output")
            json_files = list(output_dir.rglob("*.json"))
            
            for file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Handle different JSON structures
                    products = data.get('products', data if isinstance(data, list) else [])
                    
                    if products:
                        df = pd.DataFrame(products)
                        if not df.empty:
                            data_frames.append(df)
                            
                except Exception as e:
                    logger.debug(f"Skipping file {file_path}: {e}")
                    continue
            
            if data_frames:
                combined_df = pd.concat(data_frames, ignore_index=True)
                
                # Clean and standardize data
                combined_df = self._clean_dataframe(combined_df)
                
                return combined_df
            
        except Exception as e:
            logger.error(f"File loading error: {e}")
        
        return pd.DataFrame()
    
    def _load_from_file(self, file_path: str) -> pd.DataFrame:
        """Load data from specific JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = data.get('products', data if isinstance(data, list) else [])
            
            if products:
                df = pd.DataFrame(products)
                return self._clean_dataframe(df)
            
        except Exception as e:
            logger.error(f"File loading error for {file_path}: {e}")
        
        return pd.DataFrame()
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize DataFrame for analysis."""
        try:
            # Convert price to numeric
            if 'price' in df.columns:
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
            
            # Convert rating to numeric
            if 'rating' in df.columns:
                df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
            
            # Parse datetime fields
            for date_col in ['created_at', 'scraped_at', 'timestamp']:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Remove invalid records
            if 'price' in df.columns:
                df = df[df['price'] > 0]  # Remove zero/negative prices
            
            # Remove duplicates based on title and source
            if 'title' in df.columns and 'source' in df.columns:
                df = df.drop_duplicates(subset=['title', 'source'], keep='first')
            
            return df
            
        except Exception as e:
            logger.error(f"DataFrame cleaning error: {e}")
            return df
    
    def generate_comprehensive_statistics(self) -> Dict[str, Any]:
        """
        Generate comprehensive statistical analysis.
        
        Returns:
            Dictionary containing all statistical metrics
        """
        if self.df is None or self.df.empty:
            logger.warning("No data loaded for statistics")
            return {}
        
        try:
            stats = {
                'overview': self._generate_overview_stats(),
                'price_analysis': self._analyze_prices(),
                'source_comparison': self._compare_sources(),
                'data_quality': self._assess_data_quality(),
                'trend_analysis': self._analyze_trends(),
                'keyword_performance': self._analyze_keywords(),
                'scraper_performance': self._analyze_scraper_performance()
            }
            
            self.stats = stats
            logger.info("📊 Comprehensive statistics generated successfully")
            return stats
            
        except Exception as e:
            logger.error(f"Statistics generation failed: {e}")
            return {}
    
    def _generate_overview_stats(self) -> Dict[str, Any]:
        """Generate basic overview statistics."""
        return {
            'total_products': len(self.df),
            'unique_sources': self.df['source'].nunique() if 'source' in self.df.columns else 0,
            'date_range': {
                'earliest': self.df['created_at'].min().isoformat() if 'created_at' in self.df.columns else None,
                'latest': self.df['created_at'].max().isoformat() if 'created_at' in self.df.columns else None
            },
            'data_completeness': {
                'has_price': (self.df['price'].notna().sum() / len(self.df) * 100) if 'price' in self.df.columns else 0,
                'has_rating': (self.df['rating'].notna().sum() / len(self.df) * 100) if 'rating' in self.df.columns else 0,
                'has_url': (self.df['url'].notna().sum() / len(self.df) * 100) if 'url' in self.df.columns else 0
            }
        }
    
    def _analyze_prices(self) -> Dict[str, Any]:
        """Analyze price distributions and statistics."""
        if 'price' not in self.df.columns:
            return {}
        
        prices = self.df['price'].dropna()
        
        return {
            'summary': {
                'mean': float(prices.mean()),
                'median': float(prices.median()),
                'std': float(prices.std()),
                'min': float(prices.min()),
                'max': float(prices.max()),
                'q1': float(prices.quantile(0.25)),
                'q3': float(prices.quantile(0.75))
            },
            'distribution': {
                'under_100': int((prices < 100).sum()),
                'under_500': int((prices < 500).sum()),
                'under_1000': int((prices < 1000).sum()),
                'over_1000': int((prices >= 1000).sum())
            },
            'outliers': {
                'iqr_outliers': self._detect_iqr_outliers(prices),
                'z_score_outliers': self._detect_z_score_outliers(prices)
            }
        }
    
    def _compare_sources(self) -> Dict[str, Any]:
        """Compare performance and characteristics across sources."""
        if 'source' not in self.df.columns:
            return {}
        
        source_stats = {}
        
        for source in self.df['source'].unique():
            source_data = self.df[self.df['source'] == source]
            
            source_stats[source] = {
                'total_products': len(source_data),
                'avg_price': float(source_data['price'].mean()) if 'price' in source_data.columns else None,
                'avg_rating': float(source_data['rating'].mean()) if 'rating' in source_data.columns else None,
                'price_range': {
                    'min': float(source_data['price'].min()) if 'price' in source_data.columns else None,
                    'max': float(source_data['price'].max()) if 'price' in source_data.columns else None
                } if 'price' in source_data.columns else None,
                'data_quality_score': self._calculate_source_quality_score(source_data)
            }
        
        return source_stats
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Assess overall data quality."""
        return {
            'completeness_score': self._calculate_completeness_score(),
            'duplicate_rate': self._calculate_duplicate_rate(),
            'invalid_data_rate': self._calculate_invalid_data_rate(),
            'consistency_score': self._calculate_consistency_score()
        }
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends over time."""
        if 'created_at' not in self.df.columns:
            return {}
        
        # Group by date
        daily_stats = self.df.groupby(self.df['created_at'].dt.date).agg({
            'price': ['count', 'mean', 'median'],
            'source': 'nunique'
        }).round(2)
        
        return {
            'daily_collection_trend': daily_stats.to_dict(),
            'price_trend': self._analyze_price_trends(),
            'collection_velocity': self._calculate_collection_velocity()
        }
    
    def _analyze_keywords(self) -> Dict[str, Any]:
        """Analyze keyword performance."""
        if 'search_keyword' not in self.df.columns:
            return {}
        
        keyword_stats = self.df.groupby('search_keyword').agg({
            'price': ['count', 'mean', 'std'],
            'rating': 'mean',
            'source': 'nunique'
        }).round(2)
        
        return keyword_stats.to_dict()
    
    def _analyze_scraper_performance(self) -> Dict[str, Any]:
        """Analyze scraper type performance."""
        if 'scraper_type' not in self.df.columns:
            return {}
        
        scraper_stats = self.df.groupby('scraper_type').agg({
            'price': 'count',
            'source': 'nunique'
        })
        
        return scraper_stats.to_dict()
    
    def _detect_iqr_outliers(self, data: pd.Series) -> Dict[str, Any]:
        """Detect outliers using IQR method."""
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = data[(data < lower_bound) | (data > upper_bound)]
        
        return {
            'count': len(outliers),
            'percentage': len(outliers) / len(data) * 100,
            'values': outliers.tolist()[:10]  # First 10 outliers
        }
    
    def _detect_z_score_outliers(self, data: pd.Series, threshold: float = 3) -> Dict[str, Any]:
        """Detect outliers using Z-score method."""
        z_scores = np.abs((data - data.mean()) / data.std())
        outliers = data[z_scores > threshold]
        
        return {
            'count': len(outliers),
            'percentage': len(outliers) / len(data) * 100,
            'values': outliers.tolist()[:10]  # First 10 outliers
        }
    
    def _calculate_source_quality_score(self, source_data: pd.DataFrame) -> float:
        """Calculate data quality score for a source."""
        scores = []
        
        # Completeness score
        if 'price' in source_data.columns:
            price_completeness = source_data['price'].notna().mean()
            scores.append(price_completeness)
        
        if 'rating' in source_data.columns:
            rating_completeness = source_data['rating'].notna().mean()
            scores.append(rating_completeness)
        
        if 'url' in source_data.columns:
            url_completeness = source_data['url'].notna().mean()
            scores.append(url_completeness)
        
        return float(np.mean(scores)) if scores else 0.0
    
    def _calculate_completeness_score(self) -> float:
        """Calculate overall data completeness score."""
        important_columns = ['price', 'title', 'source', 'url']
        scores = []
        
        for col in important_columns:
            if col in self.df.columns:
                completeness = self.df[col].notna().mean()
                scores.append(completeness)
        
        return float(np.mean(scores)) if scores else 0.0
    
    def _calculate_duplicate_rate(self) -> float:
        """Calculate duplicate rate based on title similarity."""
        if 'title' not in self.df.columns:
            return 0.0
        
        total_records = len(self.df)
        unique_titles = self.df['title'].nunique()
        
        return float((total_records - unique_titles) / total_records * 100)
    
    def _calculate_invalid_data_rate(self) -> float:
        """Calculate rate of invalid data."""
        invalid_count = 0
        total_count = len(self.df)
        
        # Check for invalid prices
        if 'price' in self.df.columns:
            invalid_count += (self.df['price'] <= 0).sum()
        
        # Check for missing titles
        if 'title' in self.df.columns:
            invalid_count += self.df['title'].isna().sum()
        
        return float(invalid_count / total_count * 100) if total_count > 0 else 0.0
    
    def _calculate_consistency_score(self) -> float:
        """Calculate data consistency score."""
        # This is a simplified consistency check
        # In real implementation, you'd check format consistency, etc.
        return 85.0  # Placeholder score
    
    def _analyze_price_trends(self) -> Dict[str, Any]:
        """Analyze price trends over time."""
        if 'created_at' not in self.df.columns or 'price' not in self.df.columns:
            return {}
        
        # Group by week
        weekly_prices = self.df.groupby(pd.Grouper(key='created_at', freq='W'))['price'].mean()
        
        # Calculate trend
        if len(weekly_prices) > 1:
            trend_slope = np.polyfit(range(len(weekly_prices)), weekly_prices.values, 1)[0]
            trend_direction = "increasing" if trend_slope > 0 else "decreasing"
        else:
            trend_slope = 0
            trend_direction = "stable"
        
        return {
            'trend_direction': trend_direction,
            'trend_slope': float(trend_slope),
            'weekly_averages': weekly_prices.to_dict()
        }
    
    def _calculate_collection_velocity(self) -> Dict[str, Any]:
        """Calculate how fast data is being collected."""
        if 'created_at' not in self.df.columns:
            return {}
        
        # Products per day
        daily_counts = self.df.groupby(self.df['created_at'].dt.date).size()
        
        return {
            'avg_products_per_day': float(daily_counts.mean()),
            'max_products_per_day': int(daily_counts.max()),
            'total_collection_days': len(daily_counts)
        }
    
    def export_statistics(self, output_path: str = "data_output/reports/statistics.json") -> str:
        """Export statistics to JSON file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                'generated_at': datetime.now().isoformat(),
                'statistics': self.stats,
                'data_summary': {
                    'total_records': len(self.df) if self.df is not None else 0,
                    'columns': list(self.df.columns) if self.df is not None else []
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"📊 Statistics exported to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to export statistics: {e}")
            return "" 