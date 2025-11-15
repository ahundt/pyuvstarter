"""
Main module without pyproject.toml but with relative imports.

This should NOT be fixed since there's no pyproject.toml to define the package.
"""

from . import utils

def main():
    """Main function that should not be modified."""
    return utils.get_value()

if __name__ == "__main__":
    print(main())