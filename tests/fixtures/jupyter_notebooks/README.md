# Jupyter Notebook Fixtures

This directory contains Jupyter notebook fixtures for testing pyuvstarter's notebook discovery and dependency processing capabilities.

## Notebooks Included

### data_analysis_notebook.ipynb
A comprehensive notebook demonstrating various import patterns and scenarios:

**Import Categories:**
- **Data Science**: numpy, pandas, matplotlib, seaborn, scipy, sklearn
- **Web/API**: requests, aiohttp, urllib.parse, json
- **Visualization**: plotly, dash (via !pip install)
- **Async**: asyncio, aiohttp

**Discovery Scenarios:**
- Standard Python imports in code cells
- !pip install magic commands with various formats
- Conditional imports and function definitions
- Mixed cell types (code, markdown)
- Complex import patterns with aliases

## Expected Behavior

When pyuvstarter is run on projects containing these notebooks:

1. **Notebook Discovery**: Should find all .ipynb files in the project
2. **Dependency Extraction**: Should extract imports from both code cells and magic commands
3. **Dual Strategy Processing**:
   - **Primary**: Use `jupyter nbconvert --to python` + pipreqs analysis
   - **Fallback**: Direct JSON parsing with AST for imports, regex for !pip install
4. **Format Handling**: Should properly parse notebook JSON structure
5. **Cell Type Recognition**: Should distinguish between code and markdown cells
6. **Magic Command Parsing**: Should extract packages from !pip install commands

## Test Scenarios

Use these fixtures to test:
- Notebook file discovery and enumeration
- JSON parsing and structure validation
- AST-based import extraction from converted code
- Regex-based !pip install command parsing
- Dual-strategy processing (primary and fallback)
- Error handling for malformed notebooks
- Performance with multiple/large notebooks
- Encoding and special character handling

## Discovery Strategy Testing

### Primary Strategy (nbconvert + pipreqs)
```bash
jupyter nbconvert notebook.ipynb --to python --stdout
pipreqs --savepath requirements.txt /path/to/converted
```

### Fallback Strategy (JSON + AST + Regex)
- Parse notebook JSON directly
- Extract code from cell sources
- Use AST for Python import detection
- Use regex for !pip install magic commands

## Import Patterns Tested

1. **Standard imports**: `import numpy as np`
2. **From imports**: `from sklearn.linear_model import LinearRegression`
3. **Multiple imports**: `import pandas as pd, matplotlib.pyplot as plt`
4. **Conditional imports**: Try/except blocks
5. **Magic commands**: `!pip install plotly dash`
6. **Versioned installs**: `!pip install "scikit-learn>=1.0.0"`
7. **Upgrade commands**: `!pip install --upgrade seaborn`
8. **Function definitions**: Async functions and complex patterns

## Edge Cases Covered

- Malformed JSON structures
- Empty notebooks
- Notebooks with only markdown cells
- Complex magic command syntax
- Unicode and special characters
- Large notebook files
- Nested directory structures