"""
Models module with relative import patterns.
"""

# Relative imports
from .utils import DataProcessor
from .config import settings

# Standard library
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class UserModel:
    """User model with relative import dependencies."""
    name: str
    email: str = ""
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserModel':
        """Create instance from dictionary."""
        processor = DataProcessor()
        # Process data using relative import
        return cls(
            name=data.get('name', ''),
            email=data.get('email', '')
        )

    def save(self):
        """Save model using relative import."""
        config_value = settings.get('database_url', 'sqlite:///default.db')
        print(f"Saving user to {config_value}")


@dataclass
class ProductModel:
    """Product model."""
    name: str
    price: float
    description: str = ""

    def calculate_discount(self, discount_percent: float) -> float:
        """Calculate discounted price."""
        return self.price * (1 - discount_percent / 100)