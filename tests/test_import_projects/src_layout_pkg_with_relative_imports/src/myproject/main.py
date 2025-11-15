"""
Main module for MyProject.

This module uses relative imports that should be converted to absolute imports
by pyuvstarter's automatic import fixing.
"""

from . import utils
from .utils import helper_function, another_helper
import sys

def main():
    """Main function that uses relative imports."""
    print("Running main function")

    # Use the imported functions
    result = helper_function()
    print(f"Helper result: {result}")

    processed = another_helper("test data")
    print(f"Processed result: {processed}")

    return "Main function completed"

if __name__ == "__main__":
    result = main()
    print(f"Result: {result}")