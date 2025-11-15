#!/usr/bin/env python3
"""
Simple Python project fixture.

This is a basic single-file Python project that should be modernized
by pyuvstarter into a proper package structure.
"""

import sys
import os
from pathlib import Path

def main():
    """Main entry point for the simple Python project."""
    print("Hello from simple Python project!")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {Path.cwd()}")

    # Basic functionality
    data = {"name": "Simple Project", "version": "1.0.0"}
    print(f"Project data: {data}")

    return data

def helper_function():
    """Helper function for demonstrating module structure."""
    return "Helper function called"

def process_data(input_data):
    """Process some data."""
    if isinstance(input_data, dict):
        return {k.upper(): v.upper() for k, v in input_data.items()}
    return str(input_data).upper()

if __name__ == "__main__":
    result = main()
    print(f"Result: {result}")