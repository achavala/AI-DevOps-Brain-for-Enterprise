"""
Configuration loader for AI DevOps Brain
Supports local and AWS environments
"""

import yaml
import os
from pathlib import Path


def load_config(profile='local'):
    """
    Load configuration based on profile
    
    Args:
        profile: Configuration profile ('local' or 'aws-dev')
    
    Returns:
        dict: Configuration dictionary
    """
    # Check environment variable first
    env_profile = os.getenv('APP_PROFILE', profile)
    
    # Determine config path
    config_dir = Path(__file__).parent
    config_path = config_dir / f'{env_profile}.yaml'
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables if present
    config = _apply_env_overrides(config)
    
    return config


def _apply_env_overrides(config):
    """Apply environment variable overrides to config"""
    # Database overrides
    if os.getenv('DB_HOST'):
        config['database']['host'] = os.getenv('DB_HOST')
    if os.getenv('DB_PORT'):
        config['database']['port'] = int(os.getenv('DB_PORT'))
    
    # Redis overrides
    if os.getenv('REDIS_HOST'):
        config['redis']['host'] = os.getenv('REDIS_HOST')
    
    # Kafka overrides
    if os.getenv('KAFKA_BROKERS'):
        config['kafka']['brokers'] = os.getenv('KAFKA_BROKERS')
    
    return config


def get_config():
    """Get current configuration based on APP_PROFILE"""
    profile = os.getenv('APP_PROFILE', 'local')
    return load_config(profile)

