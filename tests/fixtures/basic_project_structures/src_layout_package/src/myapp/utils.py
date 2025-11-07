"""
Utility functions for MyApp package.
"""

def helper_function():
    """A helper function for demonstration."""
    return "Helper function result from MyApp"

def process_data(data):
    """Process some data."""
    if isinstance(data, str):
        return data.upper()
    return str(data)

def format_message(message: str, prefix: str = "INFO") -> str:
    """Format a message with prefix."""
    return f"[{prefix}] {message}"