"""
Configuration module with relative imports.
"""

# Relative imports
from . import utils

# Standard library
import os
from typing import Dict, Any


def get_config() -> Dict[str, Any]:
    """Get configuration with relative import usage."""
    config = {
        'debug': os.getenv('DEBUG', 'false').lower() == 'true',
        'database_url': os.getenv('DATABASE_URL', 'sqlite:///app.db'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }

    # Use relative import
    processor = utils.DataProcessor()
    config['processor_available'] = processor is not None

    return config


# Global settings instance
settings = get_config()