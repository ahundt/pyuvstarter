"""
Submodule with deep relative imports.

⚠️  IMPORTANT TEST NOTICE: This file MUST have deep relative imports that cause
ImportError when run as a script. This is INTENTIONAL - pyuvstarter should
convert these to absolute imports to fix script execution.

DO NOT FIX these relative imports manually! They are test cases for pyuvstarter's
automatic import fixing functionality. The file should fail when run with:
  python3 anotherproject/submodule.py  ❌ Should fail with ImportError

After pyuvstarter runs, it should work when run with:
  python3 anotherproject/submodule.py  ✅ Should succeed
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