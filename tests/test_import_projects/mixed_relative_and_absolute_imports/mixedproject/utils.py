"""
Utils module with relative imports (should be converted).
"""

from .config import get_config
import sys

def mixed_function():
    """Function that uses both relative and absolute imports."""
    config = get_config()
    return f"Mixed function with config: {config} on Python {sys.version}"