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
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text

def extract_price(text: str, currency: str = 'USD') -> Optional[float]:
    """
    Extract price value from text string.
    
    Args:
        text: Text containing price information
        currency: Expected currency (default: USD)
        
    Returns:
        Extracted price as float or None if not found
    """
    if not text:
        return None
    
    # Common price patterns
    patterns = [
        r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56 or 1234.56
        r'USD\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # USD 1234.56
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*USD',  # 1234.56 USD
        r'Price:\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Price: $1234.56
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                continue
    
    return None

def extract_rating(text: str) -> Optional[float]:
    """
    Extract rating value from text.
    
    Args:
        text: Text containing rating information
        
    Returns:
        Rating as float (0-5 scale) or None if not found
    """
    if not text:
        return None
    
    # Rating patterns
    patterns = [
        r'(\d+(?:\.\d+)?)\s*out\s*of\s*5',  # 4.5 out of 5
        r'(\d+(?:\.\d+)?)\s*\/\s*5',  # 4.5/5
        r'(\d+(?:\.\d+)?)\s*stars?',  # 4.5 stars
        r'Rating:\s*(\d+(?:\.\d+)?)',  # Rating: 4.5
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                rating = float(match.group(1))
                # Normalize to 0-5 scale
                if rating <= 5:
                    return rating
                elif rating <= 10:
                    return rating / 2
                elif rating <= 100:
                    return rating / 20
            except ValueError:
                continue
    
    return None

def normalize_url(url: str, base_url: str = '') -> str:
    """
    Normalize URL by making it absolute and cleaning it.
    
    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs
        
    Returns:
        Normalized absolute URL
    """
    if not url:
        return ''
    
    # Remove leading/trailing whitespace
    url = url.strip()
    
    # Handle relative URLs
    if url.startswith('//'):
        url = 'https:' + url
    elif url.startswith('/') and base_url:
        url = urllib.parse.urljoin(base_url, url)
    elif not url.startswith(('http://', 'https://')) and base_url:
        url = urllib.parse.urljoin(base_url, url)
    
    return url

def generate_hash(data: str) -> str:
    """
    Generate MD5 hash for data deduplication.
    
    Args:
        data: String data to hash
        
    Returns:
        MD5 hash string
    """
    return hashlib.md5(data.encode('utf-8')).hexdigest()

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
            import time
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