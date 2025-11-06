"""
Main module for legacy project with relative imports.

⚠️  IMPORTANT TEST NOTICE: This file MUST have relative imports that cause
ImportError when run as a script. This is INTENTIONAL - pyuvstarter should
convert these to absolute imports to fix script execution.

DO NOT FIX these relative imports manually! They are test cases for pyuvstarter's
automatic import fixing functionality. The file should fail when run with:
  python3 legacyproject/main.py  ❌ Should fail with ImportError

After pyuvstarter runs, it should work when run with:
  python3 legacyproject/main.py  ✅ Should succeed
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