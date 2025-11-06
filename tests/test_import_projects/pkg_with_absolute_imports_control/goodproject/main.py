"""
Main module using absolute imports.

This module should NOT be modified since it already uses absolute imports.
"""

from goodproject.helpers import get_system_info
import sys

def main():
    """Main function using absolute imports."""
    info = get_system_info()
    print(f"System info: {info}")
    return "Absolute imports working correctly"

if __name__ == "__main__":
    result = main()
    print(f"Result: {result}")