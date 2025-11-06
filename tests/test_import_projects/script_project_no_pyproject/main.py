"""
Main script for non-package project.

This script should NOT trigger import fixing since it's not a package project.
"""

import utils
from utils import script_helper

def main():
    """Main function."""
    print("Running non-package script")
    result = script_helper()
    print(f"Result: {result}")

if __name__ == "__main__":
    main()