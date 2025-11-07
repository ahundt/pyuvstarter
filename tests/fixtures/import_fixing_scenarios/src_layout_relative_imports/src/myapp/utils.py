"""
Utilities module with relative import patterns.
"""

# Relative imports within the same package
from .models import UserModel
from .config import get_config

# Standard library imports (should not be changed)
import json
import logging
from typing import Dict, List, Optional

# Complex relative import pattern
from . import main


class DataProcessor:
    """Data processing class with relative imports."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()

    def process_user_data(self, user_data: Dict) -> Optional[UserModel]:
        """Process user data and return UserModel instance."""
        try:
            user = UserModel.from_dict(user_data)
            return user
        except Exception as e:
            self.logger.error(f"Error processing user data: {e}")
            return None


def helper_function(data: str) -> str:
    """Helper function using relative imports."""
    processed_data = data.upper()
    main.main_function()  # This creates a circular dependency for testing
    return processed_data


# Relative import in function scope
def get_processor():
    """Factory function with relative import."""
    from .models import ProductModel
    return ProductProcessor()


class ProductProcessor:
    """Product processing class."""
    pass