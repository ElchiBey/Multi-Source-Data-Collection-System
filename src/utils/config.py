"""
Configuration management module for loading and managing application settings.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Global configuration cache
_config_cache: Optional[Dict[str, Any]] = None

def load_config(config_path: str = 'config/settings.yaml') -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration settings
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    global _config_cache
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # Cache the configuration
        _config_cache = config
        
        # Validate essential configuration sections
        _validate_config(config)
        
        logger.info(f"Configuration loaded successfully from {config_path}")
        return config
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise Exception(f"Error loading configuration: {e}")

def get_config(key_path: Optional[str] = None) -> Any:
    """
    Get configuration value by key path.
    
    Args:
        key_path: Dot-separated path to config value (e.g., 'database.url')
                 If None, returns entire config
                 
    Returns:
        Configuration value or entire config
        
    Raises:
        RuntimeError: If config not loaded
        KeyError: If key path not found
    """
    if _config_cache is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    
    if key_path is None:
        return _config_cache
    
    # Navigate through nested keys
    value = _config_cache
    for key in key_path.split('.'):
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise KeyError(f"Configuration key not found: {key_path}")
    
    return value

def get_source_config(source_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific scraping source.
    
    Args:
        source_name: Name of the source (e.g., 'amazon', 'ebay')
        
    Returns:
        Source-specific configuration
        
    Raises:
        KeyError: If source not configured
    """
    sources = get_config('sources')
    if source_name not in sources:
        raise KeyError(f"Source '{source_name}' not configured")
    
    return sources[source_name]

def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate essential configuration sections.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If required sections are missing
    """
    required_sections = [
        'scraping',
        'database', 
        'sources',
        'export'
    ]
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Required configuration section missing: {section}")
    
    # Validate database URL
    if 'url' not in config['database']:
        raise ValueError("Database URL not configured")
    
    # Validate at least one source is enabled
    sources = config.get('sources', {})
    enabled_sources = [name for name, cfg in sources.items() 
                      if cfg.get('enabled', False)]
    
    if not enabled_sources:
        raise ValueError("No scraping sources are enabled")
    
    logger.debug(f"Configuration validation passed. Enabled sources: {enabled_sources}")

def update_config(key_path: str, value: Any) -> None:
    """
    Update configuration value at runtime.
    
    Args:
        key_path: Dot-separated path to config value
        value: New value to set
        
    Raises:
        RuntimeError: If config not loaded
    """
    if _config_cache is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    
    # Navigate to parent and set value
    keys = key_path.split('.')
    current = _config_cache
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    logger.debug(f"Configuration updated: {key_path} = {value}")

def save_config(config_path: str = 'config/settings.yaml') -> None:
    """
    Save current configuration to file.
    
    Args:
        config_path: Path to save configuration file
        
    Raises:
        RuntimeError: If config not loaded
    """
    if _config_cache is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(_config_cache, f, default_flow_style=False, indent=2)
    
    logger.info(f"Configuration saved to {config_path}")

def create_default_config(config_path: str = 'config/settings.yaml') -> None:
    """
    Create a default configuration file.
    
    Args:
        config_path: Path where to create the config file
    """
    default_config = {
        'scraping': {
            'delay_range': [1, 3],
            'max_retries': 3,
            'timeout': 30,
            'user_agents': True,
            'max_pages': 10,
            'max_workers': 5
        },
        'database': {
            'url': 'sqlite:///data/products.db',
            'echo': False
        },
        'sources': {
            'amazon': {'enabled': True},
            'ebay': {'enabled': True},
            'walmart': {'enabled': False}
        },
        'export': {
            'formats': ['csv', 'json'],
            'output_dir': 'data_output'
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/scraper.log'
        }
    }
    
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    logger.info(f"Default configuration created at {config_path}") 