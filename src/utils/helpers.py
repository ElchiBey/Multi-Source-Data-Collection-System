"""
Helper functions and utilities for the Multi-Source Data Collection System.
"""

import re
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import urllib.parse
from datetime import datetime, timedelta
import hashlib
import html
import random
import time

def create_directories() -> None:
    """Create necessary directories for the application."""
    directories = [
        'data',
        'logs',
        'data_output/raw',
        'data_output/processed', 
        'data_output/reports',
        'config'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E]', '', text)
    
    return text

def extract_price(price_text: str) -> Optional[float]:
    """Extract price from text string."""
    if not price_text:
        return None
    
    # Handle "Free" explicitly
    if 'free' in price_text.lower():
        return 0.0
    
    # Remove currency symbols and non-numeric characters except decimal point
    price_clean = re.sub(r'[^\d.,]', '', price_text)
    
    # Handle different decimal separators
    if ',' in price_clean and '.' in price_clean:
        # Assume comma is thousands separator if both present
        price_clean = price_clean.replace(',', '')
    elif ',' in price_clean:
        # Could be decimal separator in some locales
        if price_clean.count(',') == 1 and len(price_clean.split(',')[1]) <= 2:
            price_clean = price_clean.replace(',', '.')
    
    try:
        return float(price_clean)
    except ValueError:
        return None

def extract_rating(rating_text: str) -> Optional[float]:
    """Extract rating from text string."""
    if not rating_text:
        return None
    
    # Look for pattern like "4.5 out of 5" or just "4.5"
    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
    if rating_match:
        try:
            rating = float(rating_match.group(1))
            # Normalize to 5-star scale if needed
            if rating > 5:
                rating = rating / 2  # Convert 10-star to 5-star
            return min(rating, 5.0)
        except ValueError:
            pass
    
    return None

def normalize_url(url: str, base_url: str = "") -> str:
    """Normalize URL by making it absolute and cleaning it."""
    if not url:
        return ""
    
    # Make absolute URL
    if url.startswith('//'):
        url = 'https:' + url
    elif url.startswith('/'):
        url = urllib.parse.urljoin(base_url, url)
    elif not url.startswith(('http://', 'https://')):
        url = urllib.parse.urljoin(base_url, url)
    
    return url

def generate_hash(data: Union[str, dict]) -> str:
    """
    Generate MD5 hash for data deduplication.
    
    Args:
        data: String data or dict to hash
        
    Returns:
        MD5 hash string
    """
    if isinstance(data, dict):
        # Create a string representation of key data fields
        key_fields = ['title', 'url', 'price', 'source']
        hash_string = ''.join(str(data.get(field, '')) for field in key_fields)
        return hashlib.md5(hash_string.encode()).hexdigest()
    else:
        return hashlib.md5(str(data).encode('utf-8')).hexdigest()

def save_json(data: Any, filepath: str) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        filepath: Path to save file
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def load_json(filepath: str) -> Any:
    """
    Load data from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is invalid JSON
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_filename(name: str, timestamp: bool = True) -> str:
    """
    Format filename with optional timestamp.
    
    Args:
        name: Base filename
        timestamp: Whether to add timestamp
        
    Returns:
        Formatted filename
    """
    # Clean filename
    name = re.sub(r'[^\w\-_\.]', '_', name)
    
    if timestamp:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        name_parts = name.rsplit('.', 1)
        if len(name_parts) == 2:
            name = f"{name_parts[0]}_{ts}.{name_parts[1]}"
        else:
            name = f"{name}_{ts}"
    
    return name

def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Yield successive n-sized chunks from list.
    
    Args:
        lst: List to chunk
        n: Chunk size
        
    Yields:
        Chunks of the list
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry function on failure.
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            from src.utils.logger import get_logger
            
            logger = get_logger(func.__module__)
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
            
        return wrapper
    return decorator

def validate_url(url: str) -> bool:
    """
    Validate if string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
        
    Returns:
        Domain name or empty string if invalid
    """
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower()
    except:
        return ''

def get_file_size(filepath: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in bytes or 0 if file doesn't exist
    """
    try:
        return os.path.getsize(filepath)
    except (OSError, FileNotFoundError):
        return 0

def is_recent_file(filepath: str, hours: int = 24) -> bool:
    """
    Check if file was modified within specified hours.
    
    Args:
        filepath: Path to file
        hours: Hours threshold
        
    Returns:
        True if file is recent, False otherwise
    """
    try:
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        threshold = datetime.now() - timedelta(hours=hours)
        return file_time > threshold
    except (OSError, FileNotFoundError):
        return False

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing periods and spaces
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext
    
    return sanitized or 'unnamed'

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result 

# Anti-bot protection utilities
def get_random_user_agent() -> str:
    """Get a random user agent string."""
    user_agents = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
        
        # Firefox on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        
        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    return random.choice(user_agents)

def get_random_headers() -> dict:
    """Get random HTTP headers to mimic real browser requests."""
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': random.choice([
            'en-US,en;q=0.9',
            'en-GB,en;q=0.9',
            'en-US,en;q=0.5',
        ]),
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    # Sometimes add additional headers
    if random.random() > 0.5:
        headers['Sec-CH-UA'] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        headers['Sec-CH-UA-Mobile'] = '?0'
        headers['Sec-CH-UA-Platform'] = random.choice(['"Windows"', '"macOS"', '"Linux"'])
    
    return headers

def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """Add random delay between requests."""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def get_proxy_list() -> List[str]:
    """Get list of proxy servers (you would populate this with real proxies)."""
    # This is a placeholder - you would add real proxy servers here
    # Free proxies are often unreliable, consider paid proxy services
    return [
        # 'http://proxy1:port',
        # 'http://proxy2:port',
        # 'https://proxy3:port',
    ]

def should_use_proxy() -> bool:
    """Decide whether to use proxy for this request."""
    # Use proxy 30% of the time (adjust as needed)
    return random.random() < 0.3

def get_selenium_options():
    """Get Selenium Chrome options for anti-bot protection."""
    from selenium.webdriver.chrome.options import Options
    
    options = Options()
    
    # Basic stealth options
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-features=VizDisplayCompositor')
    
    # Anti-detection options
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Random window size
    window_sizes = [
        '--window-size=1366,768',
        '--window-size=1920,1080', 
        '--window-size=1440,900',
        '--window-size=1536,864',
    ]
    options.add_argument(random.choice(window_sizes))
    
    # Random user agent
    options.add_argument(f'--user-agent={get_random_user_agent()}')
    
    # Disable images and CSS for faster loading (optional)
    # prefs = {
    #     "profile.managed_default_content_settings.images": 2,
    #     "profile.default_content_setting_values.notifications": 2,
    # }
    # options.add_experimental_option("prefs", prefs)
    
    return options 