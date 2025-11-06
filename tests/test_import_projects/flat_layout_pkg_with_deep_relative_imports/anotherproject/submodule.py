"""
Submodule with deep relative imports.

This module tests complex relative import patterns.
"""

from .subfolder import deep_function

def local_function():
    """Local function in submodule."""
    return "Local function result"

def complex_operation():
    """Function that uses deeply imported utilities."""
    result1 = deep_function()
    result2 = local_function()
    return f"Complex: {result1} + {result2}"