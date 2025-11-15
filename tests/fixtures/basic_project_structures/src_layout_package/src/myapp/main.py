"""
Main module for MyApp package.
"""

from . import utils
from .utils import helper_function

def main():
    """Main entry point for the application."""
    print("MyApp main function called")
    result = helper_function()
    return f"Main result: {result}"

def get_version():
    """Get the package version."""
    from . import __version__
    return __version__