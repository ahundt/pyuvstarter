"""
Main module for legacy project with relative imports.
"""

from . import data_processor
from .data_processor import process_data
import requests  # Will be in requirements.txt

def main():
    """Main function using legacy dependencies."""
    result = process_data("test data")
    response = requests.get("https://httpbin.org/get")
    return f"Processed: {result}, API Status: {response.status_code}"

if __name__ == "__main__":
    print(main())