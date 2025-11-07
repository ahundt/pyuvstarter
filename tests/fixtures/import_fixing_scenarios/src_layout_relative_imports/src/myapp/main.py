"""
Main module with relative imports that need fixing.
"""

# Relative imports that should be detected by Ruff TID252
from . import utils
from .models import UserModel
from .utils import DataProcessor, helper_function

# Mixed relative and absolute imports
import os
import sys
from .config import settings
from datetime import datetime


def main_function():
    """Main function using relative imports."""
    processor = DataProcessor()
    user = UserModel(name="Test User")

    result = helper_function("test data")
    config_value = settings.get('debug', False)

    print(f"Main function executed: {result}, Config: {config_value}")
    return True


if __name__ == "__main__":
    main_function()