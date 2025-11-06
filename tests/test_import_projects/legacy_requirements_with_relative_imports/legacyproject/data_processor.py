"""
Data processor module with relative imports.
"""

import pandas as pd  # Will be in requirements.txt
import numpy as np  # Will be in requirements.txt

def process_data(data):
    """Process data using legacy dependencies."""
    df = pd.DataFrame({"data": [data]})
    result = np.mean([1, 2, 3])
    return f"DataFrame shape: {df.shape}, NumPy result: {result}"