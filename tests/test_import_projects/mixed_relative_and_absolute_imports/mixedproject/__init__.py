"""
MixedProject - Tests mixed relative and absolute imports.

Some modules use relative imports (should be fixed), others use absolute imports (should stay).
"""

from .utils import mixed_function

__version__ = "0.5.0"
__all__ = ["mixed_function"]