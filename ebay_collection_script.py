#!/usr/bin/env python3
"""
eBay-Focused Data Collection Script
Designed to systematically collect 5,000+ records from eBay
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append('.')

from src.scrapers.manager import ScrapingManager
from src.utils.config import load_config
from src.utils.logger import setup_logger

def main():
    """Execute systematic eBay collection."""
    
    # Setup
    config = load_config('config/settings.yaml')
    logger = setup_logger(__name__)
    manager = ScrapingManager(config)
    
    # Different keyword categories for diversity
    keyword_batches = [
        # Electronics (high-value items)
        ['laptop', 'smartphone', 'tablet', 'smartwatch', 'headphones'],
        ['camera', 'gaming', 'monitor', 'speaker', 'charger'],
        
        # Fashion & Accessories
        ['shoes', 'bag', 'watch', 'jewelry', 'sunglasses'],
        ['clothing', 'jacket', 'dress', 'shirt', 'pants'],
        
        # Home & Garden
        ['furniture', 'lamp', 'chair', 'table', 'decor'],
        ['kitchen', 'bedding', 'curtains', 'mirror', 'plant'],
        
        # Books & Media
        ['book', 'vinyl', 'cd', 'dvd', 'magazine'],
        
        # Sports & Outdoor
        ['bicycle', 'fitness', 'camping', 'sports', 'outdoor'],
        
        # Collectibles & Antiques
        ['vintage', 'antique', 'collectible', 'art', 'coins'],
        
        # Tools & Hardware
        ['tools', 'hardware', 'automotive', 'parts', 'motor']
    ]
    
    total_collected = 0
    target = 5000
    output_dir = Path('data_output/ebay_systematic')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"🎯 Starting systematic eBay collection (target: {target:,} records)")
    
    for batch_num, keywords in enumerate(keyword_batches, 1):
        if total_collected >= target:
            break
            
        logger.info(f"📦 Batch {batch_num}/{len(keyword_batches)}: {keywords}")
        
        try:
            # Scrape this batch with multiple pages
            results = manager.scrape_all(
                sources=['ebay'],
                keywords=keywords,
                max_pages=8,  # Go deeper for more records
                output_dir=str(output_dir)
            )
            
            batch_count = len(results)
            total_collected += batch_count
            
            logger.info(f"✅ Batch {batch_num} complete: {batch_count:,} records")
            logger.info(f"📊 Total progress: {total_collected:,}/{target:,} ({(total_collected/target)*100:.1f}%)")
            
            # Save progress report
            progress = {
                'timestamp': datetime.now().isoformat(),
                'batch': batch_num,
                'batch_keywords': keywords,
                'batch_records': batch_count,
                'total_records': total_collected,
                'target': target,
                'progress_percent': (total_collected/target)*100
            }
            
            progress_file = output_dir / f'progress_batch_{batch_num:02d}.json'
            with open(progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
            
            if total_collected >= target:
                logger.info(f"🎉 TARGET ACHIEVED! Collected {total_collected:,} records")
                break
                
            # Delay between batches to be respectful
            delay = 60  # 1 minute between batches
            logger.info(f"⏱️ Batch delay: {delay}s...")
            time.sleep(delay)
            
        except Exception as e:
            logger.error(f"❌ Batch {batch_num} failed: {e}")
            continue
    
    # Final summary
    logger.info(f"🏁 Collection complete!")
    logger.info(f"📊 Final count: {total_collected:,} records")
    logger.info(f"📁 Data saved to: {output_dir}")
    
    if total_collected >= target:
        logger.info(f"🎉 SUCCESS: Reached target of {target:,} records!")
    else:
        logger.info(f"📈 Progress: {(total_collected/target)*100:.1f}% of target")
        logger.info(f"💡 Need {target - total_collected:,} more records")

if __name__ == '__main__':
    main() 