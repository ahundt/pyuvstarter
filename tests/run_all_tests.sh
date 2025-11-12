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
TEST_RESULTS=()  # Store results as "name:status:duration"
SUITE_START_TIME=$(date +%s.%N 2>/dev/null || date +%s)

echo ""
echo "🧪 Running Python Unit Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run Python unit tests first (don't need temp directory)
cd "$ORIGINAL_DIR"
for test in "${PYTHON_TESTS[@]}"; do
    echo "Running: $test"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    test_start=$(date +%s.%N 2>/dev/null || date +%s)
    if source "$ORIGINAL_DIR/.venv/bin/activate" && python3 "tests/$test"; then
        test_end=$(date +%s.%N 2>/dev/null || date +%s)
        test_duration=$(echo "$test_end - $test_start" | bc 2>/dev/null || echo "0")
        echo "✅ $test PASSED"
        TEST_RESULTS+=("$test:PASSED:$test_duration")
    else
        test_end=$(date +%s.%N 2>/dev/null || date +%s)
        test_duration=$(echo "$test_end - $test_start" | bc 2>/dev/null || echo "0")
        echo "❌ $test FAILED"
        FAILED_TESTS+=("$test")
        TEST_RESULTS+=("$test:FAILED:$test_duration")
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

    test_start=$(date +%s.%N 2>/dev/null || date +%s)
    if bash "$ORIGINAL_DIR/tests/$test"; then
        test_end=$(date +%s.%N 2>/dev/null || date +%s)
        test_duration=$(echo "$test_end - $test_start" | bc 2>/dev/null || echo "0")
        echo "✅ $test PASSED"
        TEST_RESULTS+=("$test:PASSED:$test_duration")
    else
        test_end=$(date +%s.%N 2>/dev/null || date +%s)
        test_duration=$(echo "$test_end - $test_start" | bc 2>/dev/null || echo "0")
        echo "❌ $test FAILED"
        FAILED_TESTS+=("$test")
        TEST_RESULTS+=("$test:FAILED:$test_duration")
    fi

    echo ""
    # Clean up between tests
    cd "$TEST_DIR"
    rm -rf test_*
done

# Calculate total duration
SUITE_END_TIME=$(date +%s.%N 2>/dev/null || date +%s)
TOTAL_DURATION=$(echo "$SUITE_END_TIME - $SUITE_START_TIME" | bc 2>/dev/null || echo "0")

# Generate JUnit XML for GitHub Actions
generate_junit_xml() {
    local xml_file="$ORIGINAL_DIR/test_results_comprehensive.xml"
    local total_tests=$((${#PYTHON_TESTS[@]} + ${#INTEGRATION_TESTS[@]}))
    local failed_count=${#FAILED_TESTS[@]}

    cat > "$xml_file" << 'XML_EOF'
<?xml version="1.0" encoding="UTF-8"?>
XML_EOF

    # Add testsuites opening tag
    cat >> "$xml_file" << XML_EOF
<testsuites name="pyuvstarter_comprehensive_tests" tests="$total_tests" failures="$failed_count" time="$TOTAL_DURATION">
  <testsuite name="pyuvstarter.python_unit_tests" tests="${#PYTHON_TESTS[@]}" failures="0" time="0">
XML_EOF

    # Add Python test results
    for result in "${TEST_RESULTS[@]}"; do
        IFS=':' read -r name status duration <<< "$result"

        # Only include Python tests in this suite
        if [[ "$name" == test_*.py ]]; then
            # Extract test name without .py extension
            local test_name="${name%.py}"
            local classname="pyuvstarter.tests.$test_name"

            if [ "$status" = "PASSED" ]; then
                echo "    <testcase name=\"$test_name\" classname=\"$classname\" time=\"$duration\"/>" >> "$xml_file"
            else
                cat >> "$xml_file" << XML_EOF
    <testcase name="$test_name" classname="$classname" time="$duration">
      <failure message="Test failed - see logs for details" type="AssertionError">
        Test suite $name failed. Check CI logs for detailed output.
      </failure>
    </testcase>
XML_EOF
            fi
        fi
    done

    # Close Python test suite, open integration test suite
    cat >> "$xml_file" << XML_EOF
  </testsuite>
  <testsuite name="pyuvstarter.integration_tests" tests="${#INTEGRATION_TESTS[@]}" failures="0" time="0">
XML_EOF

    # Add integration test results
    for result in "${TEST_RESULTS[@]}"; do
        IFS=':' read -r name status duration <<< "$result"

        # Only include integration tests (.sh files) in this suite
        if [[ "$name" == test_*.sh ]]; then
            # Extract test name without .sh extension
            local test_name="${name%.sh}"
            local classname="pyuvstarter.tests.$test_name"

            if [ "$status" = "PASSED" ]; then
                echo "    <testcase name=\"$test_name\" classname=\"$classname\" time=\"$duration\"/>" >> "$xml_file"
            else
                cat >> "$xml_file" << XML_EOF
    <testcase name="$test_name" classname="$classname" time="$duration">
      <failure message="Integration test failed - see logs for details" type="TestFailure">
        Integration test $name failed. Check CI logs for detailed output.
      </failure>
    </testcase>
XML_EOF
            fi
        fi
    done

    # Close testsuite and testsuites tags
    cat >> "$xml_file" << 'XML_EOF'
  </testsuite>
</testsuites>
XML_EOF

    echo "📊 Generated JUnit XML: $xml_file"
}

# Generate the JUnit XML report
generate_junit_xml

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