#!/bin/bash
# test_new_project.sh - Test new project creation

set -e

echo "🧪 INTEGRATION TEST: New project creation"
echo "========================================="
TEST_FAILED=0

mkdir -p test_new_project
cd test_new_project
echo "📁 Created test directory: $(pwd)"
echo "🚀 Running: pyuvstarter ."
pyuvstarter .
echo ""
echo "🔍 Verifying generated files:"
if test -f pyproject.toml; then echo "  ✅ pyproject.toml exists"; else echo "  ❌ pyproject.toml NOT FOUND"; ((TEST_FAILED++)); fi
if test -f .gitignore; then echo "  ✅ .gitignore exists"; else echo "  ❌ .gitignore NOT FOUND"; ((TEST_FAILED++)); fi
if test -d .venv; then echo "  ✅ .venv/ directory exists"; else echo "  ❌ .venv/ directory NOT FOUND"; ((TEST_FAILED++)); fi
if test -f uv.lock; then echo "  ✅ uv.lock exists"; else echo "  ❌ uv.lock NOT FOUND"; ((TEST_FAILED++)); fi
echo ""
if [ $TEST_FAILED -eq 0 ]; then
  echo "✅ New project test passed"
else
  echo "❌ New project test FAILED ($TEST_FAILED checks failed)"
  exit $TEST_FAILED
fi