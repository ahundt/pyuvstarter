#!/bin/bash
# run_all_tests.sh - Run all integration tests

set -e

echo "🚀 PyUVStarter Integration Test Suite"
echo "===================================="
echo ""

# Save current directory
ORIGINAL_DIR=$(pwd)

# Create a test directory outside the pyuvstarter workspace (cross-platform)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    TEST_DIR="$ORIGINAL_DIR/test_runs_$(date +%s)_$$"
else
    # Unix-like systems (Linux, macOS)
    TEST_DIR="/tmp/pyuvstarter_test_$$"
fi
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "Test directory: $TEST_DIR"
echo ""

# Make sure pyuvstarter is available
if ! command -v pyuvstarter >/dev/null 2>&1; then
    echo "❌ pyuvstarter not found in PATH"
    echo "Please install it first: uv tool install ."
    exit 1
fi

# Run shell-based integration tests
INTEGRATION_TESTS=(
    "test_new_project.sh"
    "test_legacy_migration.sh"
)

# Run Python unit tests
PYTHON_TESTS=(
    "test_extraction_fix.py"
    "test_import_fixing.py"
    "test_dependency_migration.py"
    "test_jupyter_pipeline.py"
    "test_project_structure.py"
    "test_utils.py"
    "test_configuration.py"
    "test_cross_platform.py"
    "test_error_handling.py"
)

FAILED_TESTS=()

echo ""
echo "🧪 Running Python Unit Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run Python unit tests first (don't need temp directory)
cd "$ORIGINAL_DIR"
for test in "${PYTHON_TESTS[@]}"; do
    echo "Running: $test"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if source "$ORIGINAL_DIR/.venv/bin/activate" && python3 "tests/$test"; then
        echo "✅ $test PASSED"
    else
        echo "❌ $test FAILED"
        FAILED_TESTS+=("$test")
    fi

    echo ""
done

echo "🚀 Running Integration Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run shell-based integration tests
cd "$TEST_DIR"
for test in "${INTEGRATION_TESTS[@]}"; do
    echo "Running: $test"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if bash "$ORIGINAL_DIR/tests/$test"; then
        echo "✅ $test PASSED"
    else
        echo "❌ $test FAILED"
        FAILED_TESTS+=("$test")
    fi

    echo ""
    # Clean up between tests
    cd "$TEST_DIR"
    rm -rf test_*
done

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOTAL_TESTS=$((${#PYTHON_TESTS[@]} + ${#INTEGRATION_TESTS[@]}))
echo "Total tests: $TOTAL_TESTS"
echo "  - Python unit tests: ${#PYTHON_TESTS[@]}"
echo "  - Integration tests: ${#INTEGRATION_TESTS[@]}"
echo "Failed tests: ${#FAILED_TESTS[@]}"

if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    # Clean up test directory
    cd "$ORIGINAL_DIR"
    rm -rf "$TEST_DIR"
    exit 0
else
    echo ""
    echo "❌ Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
    echo "Test artifacts preserved in: $TEST_DIR"
    exit 1
fi