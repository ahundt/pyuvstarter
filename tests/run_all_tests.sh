#!/bin/bash
# run_all_tests.sh - Run all integration tests

set -e

echo "🚀 PyUVStarter Integration Test Suite"
echo "===================================="
echo ""

# Save current directory
ORIGINAL_DIR=$(pwd)
TEST_DIR="$ORIGINAL_DIR/test_runs_$(date +%s)"

# Create a test directory
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

# Run all tests
TESTS=(
    "test_new_project.sh"
    "test_legacy_migration.sh" 
    "test_notebook_support.sh"
)

FAILED_TESTS=()

for test in "${TESTS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
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
echo "Total tests: ${#TESTS[@]}"
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