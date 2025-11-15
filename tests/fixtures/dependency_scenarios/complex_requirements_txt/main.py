"""
Complex Python project with diverse dependencies for testing pyuvstarter.
This script imports from various dependency categories to test discovery.
"""

import requests
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import pytest
import django
from flask import Flask
import sqlalchemy
from aiohttp import ClientSession

# Conditional imports based on availability
try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

try:
    import sklearn
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

def main():
    """Main function demonstrating various library usage."""
    # HTTP requests
    response = requests.get("https://httpbin.org/get")

    # Data processing
    data = np.random.randn(100, 5)
    df = pd.DataFrame(data, columns=['A', 'B', 'C', 'D', 'E'])

    # Statistical analysis
    correlation = df.corr()

    # Web app
    app = Flask(__name__)

    # Database setup
    engine = sqlalchemy.create_engine('sqlite:///test.db')

    # Async HTTP
    async def fetch_data():
        async with ClientSession() as session:
            async with session.get('https://api.example.com') as response:
                return await response.json()

    print("Complex dependencies test completed successfully!")
    return True

if __name__ == "__main__":
    main()