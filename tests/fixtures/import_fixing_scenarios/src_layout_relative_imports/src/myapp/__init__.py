"""
MyApp package with relative import patterns for testing.
"""

__version__ = "1.0.0"

# These imports should be detected as needing fixing
from .main import main_function
from .utils import helper_function, DataProcessor
from .models import UserModel, ProductModel

__all__ = ["main_function", "helper_function", "DataProcessor", "UserModel", "ProductModel"]