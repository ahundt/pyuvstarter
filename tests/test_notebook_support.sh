#!/bin/bash
# test_notebook_support.sh - Test notebook dependency discovery

set -e

echo "🧪 INTEGRATION TEST: Notebook support"
echo "====================================="
TEST_FAILED=0

# Create project with notebook
mkdir -p test_notebook_project
cd test_notebook_project
echo "📁 Created test directory: $(pwd)"

# Create a simple notebook file
echo "📝 Creating Jupyter notebook..."
cat > experiment.ipynb << 'NOTEBOOK_EOF'
{
  "cells": [
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "!pip install seaborn"
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python",
      "version": "3.11.0"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
NOTEBOOK_EOF
echo "  ✅ Created: experiment.ipynb"

# Run pyuvstarter
echo ""
echo "🚀 Running: pyuvstarter ."
pyuvstarter .

# Verify notebook dependencies were found
echo ""
echo "🔍 Verifying notebook dependency discovery:"
if test -f pyproject.toml; then echo "  ✅ pyproject.toml exists"; else echo "  ❌ pyproject.toml NOT FOUND"; ((TEST_FAILED++)); fi
if grep -q "pandas" pyproject.toml; then echo "  ✅ pandas found (from import)"; else echo "  ❌ pandas NOT FOUND"; ((TEST_FAILED++)); fi
if grep -q "matplotlib" pyproject.toml; then echo "  ✅ matplotlib found (from import)"; else echo "  ❌ matplotlib NOT FOUND"; ((TEST_FAILED++)); fi
if grep -q "seaborn" pyproject.toml; then echo "  ✅ seaborn found (from !pip install)"; else echo "  ❌ seaborn NOT FOUND"; ((TEST_FAILED++)); fi
if grep -q "ipykernel" pyproject.toml; then echo "  ✅ ipykernel found (notebook support)"; else echo "  ❌ ipykernel NOT FOUND"; ((TEST_FAILED++)); fi
echo ""
if [ $TEST_FAILED -eq 0 ]; then
  echo "✅ Notebook support test passed"
else
  echo "❌ Notebook support test FAILED ($TEST_FAILED checks failed)"
  exit $TEST_FAILED
fi