"""
Helper functions using absolute imports.
"""

import os
import sys

def get_system_info():
    """Get system information using absolute imports."""
    return f"Python: {sys.version}, Platform: {os.name}"