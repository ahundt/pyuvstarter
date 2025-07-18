#!/bin/bash
# test_legacy_migration.sh - Test legacy project migration

set -e

echo "🧪 INTEGRATION TEST: Legacy project migration"
echo "============================================="
TEST_FAILED=0

# Create a legacy project with requirements.txt
mkdir -p test_legacy_project
cd test_legacy_project
echo "📁 Created test directory: $(pwd)"
echo "📝 Creating legacy project files..."
echo "# Legacy ML project" > README.md
echo "pandas==2.0.0" > requirements.txt
echo "numpy>=1.20" >> requirements.txt
echo "import pandas as pd" > analysis.py
echo "import numpy as np" >> analysis.py
echo "  ✅ Created: README.md, requirements.txt, analysis.py"

# Run pyuvstarter
echo ""
echo "🚀 Running: pyuvstarter --dependency-migration auto ."
pyuvstarter --dependency-migration auto .

# Verify migration
echo ""
echo "🔍 Verifying migration results:"
if test -f pyproject.toml; then echo "  ✅ pyproject.toml exists"; else echo "  ❌ pyproject.toml NOT FOUND"; ((TEST_FAILED++)); fi
if grep -q "pandas" pyproject.toml; then echo "  ✅ pandas found in pyproject.toml"; else echo "  ❌ pandas NOT FOUND in pyproject.toml"; ((TEST_FAILED++)); fi
if grep -q "numpy" pyproject.toml; then echo "  ✅ numpy found in pyproject.toml"; else echo "  ❌ numpy NOT FOUND in pyproject.toml"; ((TEST_FAILED++)); fi
echo ""
if [ $TEST_FAILED -eq 0 ]; then
  echo "✅ Legacy project migration test passed"
else
  echo "❌ Legacy project migration test FAILED ($TEST_FAILED checks failed)"
  exit $TEST_FAILED
fi