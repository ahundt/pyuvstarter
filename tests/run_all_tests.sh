#!/bin/bash
# run_all_tests.sh - Run all integration tests
#
# Usage:
#   ./run_all_tests.sh [iterations] [output_dir]
#
# Arguments:
#   iterations  - Number of times to run the test suite (default: 1 for backward compatibility)
#   output_dir  - Directory to save multi-run results (default: ./test_run_outputs)
#
# Multi-Run Mode:
#   When iterations > 1, enables multi-run mode for debugging intermittent test failures.
#   This mode:
#   - Runs test suite multiple times sequentially
#   - Saves each iteration's logs to separate numbered directories
#   - Uses unique log file names per iteration (via --log-file-name parameter)
#   - Preserves all JSON logs and XML reports for analysis
#   - Generates summary showing which tests failed in which iterations
#   - Useful for identifying non-deterministic failures and failure patterns
#
# Examples:
#   ./run_all_tests.sh              # Run once (normal mode, backward compatible)
#   ./run_all_tests.sh 10           # Debug mode: run 10 iterations, saves all logs
#   ./run_all_tests.sh 10 /tmp/results  # Custom output directory for multi-run logs

set -e

# Parse command-line arguments
ITERATIONS="${1:-1}"
MULTI_RUN_OUTPUT_DIR="${2:-./test_run_outputs}"
PYTHON_VERSION="${3:-}"  # Optional Python version (e.g., "3.14")
CURRENT_ITERATION="${PYUVSTARTER_CURRENT_ITERATION:-0}"  # Used internally for multi-run

# Input validation: Show help if requested or invalid input
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    cat << 'HELP_EOF'
🚀 PyUVStarter Integration Test Suite

Usage:
  ./run_all_tests.sh [iterations] [output_dir] [python_version]

Arguments:
  iterations      - Number of times to run test suite (default: 1)
  output_dir      - Directory for multi-run logs (default: ./test_run_outputs)
  python_version  - Optional Python version to use (e.g., "3.14", "3.12")
                    If provided, sets UV_PYTHON environment variable

Examples:
  ./run_all_tests.sh              # Run once (normal mode, uses default Python)
  ./run_all_tests.sh 10           # Run 10 times to debug intermittent failures
  ./run_all_tests.sh 10 /tmp/logs # Run 10 times, save logs to custom directory
  ./run_all_tests.sh 1 ./logs 3.14 # Run once with Python 3.14
  ./run_all_tests.sh 5 ./logs 3.12 # Run 5 times with Python 3.12

Multi-Run Mode:
  Automatically activates when iterations > 1. Useful for debugging non-deterministic
  test failures by running the suite multiple times and preserving all logs.

Python Version Control:
  Set python_version to test against a specific Python version. This sets UV_PYTHON
  before running tests, ensuring all tests use the specified version.
HELP_EOF
    exit 0
fi

# Set UV_PYTHON if a Python version was specified
if [ -n "$PYTHON_VERSION" ]; then
    export UV_PYTHON="$PYTHON_VERSION"
    echo "📌 Python version override: UV_PYTHON=$UV_PYTHON"
fi

# Validate iterations is a positive integer
if ! [[ "$ITERATIONS" =~ ^[0-9]+$ ]] || [ "$ITERATIONS" -lt 1 ]; then
    echo "❌ ERROR: iterations must be a positive integer (got: '$1')" >&2
    echo "Usage: ./run_all_tests.sh [iterations] [output_dir]" >&2
    echo "Run './run_all_tests.sh --help' for more information" >&2
    exit 1
fi

# Determine if this is multi-run mode (only when iterations > 1 AND not already in a sub-run)
if [ "$ITERATIONS" -gt 1 ] && [ "$CURRENT_ITERATION" -eq 0 ]; then
    MULTI_RUN_MODE=true
else
    MULTI_RUN_MODE=false
fi

echo "🚀 PyUVStarter Integration Test Suite"
echo "===================================="
if [ "$MULTI_RUN_MODE" = true ]; then
    echo "🔄 Multi-run mode: $ITERATIONS iterations (for debugging intermittent failures)"
    echo "📁 Output directory: $MULTI_RUN_OUTPUT_DIR"
fi
echo ""

# Save current directory
ORIGINAL_DIR=$(pwd)

# Shared function: Run a single test with timing and result tracking
run_single_test() {
    local test_name=$1
    local test_command=$2

    # Declare and assign separately per shellcheck SC2155
    local test_start
    test_start=$(date +%s.%N 2>/dev/null || date +%s)

    if eval "$test_command"; then
        local test_end
        local test_duration
        test_end=$(date +%s.%N 2>/dev/null || date +%s)
        test_duration=$(echo "$test_end - $test_start" | bc 2>/dev/null || echo "0")
        echo "✅ $test_name PASSED"
        TEST_RESULTS+=("$test_name:PASSED:$test_duration")
        return 0
    else
        local test_end
        local test_duration
        test_end=$(date +%s.%N 2>/dev/null || date +%s)
        test_duration=$(echo "$test_end - $test_start" | bc 2>/dev/null || echo "0")
        echo "❌ $test_name FAILED"
        FAILED_TESTS+=("$test_name")
        TEST_RESULTS+=("$test_name:FAILED:$test_duration")
        return 1
    fi
}

# Shared function: Display summary and exit with appropriate code
exit_with_summary() {
    local pass_count=$1
    local total_count=$2
    local fail_count=$((total_count - pass_count))

    echo ""
    echo "📈 Final Results: $pass_count/$total_count passed, $fail_count/$total_count failed"
    echo "🏁 Completed at $(date)"

    if [ $fail_count -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# If multi-run mode, orchestrate multiple test runs with log retention
if [ "$MULTI_RUN_MODE" = true ]; then
    mkdir -p "$MULTI_RUN_OUTPUT_DIR"
    echo "Starting $ITERATIONS test iterations at $(date)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    MULTI_RUN_RESULTS=()

    for i in $(seq 1 "$ITERATIONS"); do
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🧪 Test Iteration $i/$ITERATIONS started at $(date)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        ITERATION_DIR="$MULTI_RUN_OUTPUT_DIR/iteration_$(printf '%02d' "$i")"
        mkdir -p "$ITERATION_DIR"

        # Export iteration number for this run
        export PYUVSTARTER_CURRENT_ITERATION="$i"

        # Note: Log file naming handled by default behavior in single-run mode
        # Each test creates its own log in project directory with standard name

        # Run test suite, capturing output
        if "$0" 1 "$MULTI_RUN_OUTPUT_DIR" > "$ITERATION_DIR/stdout.log" 2> "$ITERATION_DIR/stderr.log"; then
            echo "✅ Iteration $i: ALL TESTS PASSED"
            MULTI_RUN_RESULTS+=("$i:PASS")
        else
            echo "❌ Iteration $i: SOME TESTS FAILED"
            MULTI_RUN_RESULTS+=("$i:FAIL")
        fi

        # Copy XML and JSON logs with iteration-specific names
        if [ -f "$ORIGINAL_DIR/test_results_comprehensive.xml" ]; then
            cp "$ORIGINAL_DIR/test_results_comprehensive.xml" "$ITERATION_DIR/" 2>/dev/null || true
        fi

        # Search for pyuvstarter JSON logs in project root matching THIS iteration only
        ITER_PREFIX="iteration_$(printf '%02d' "$i")_"
        find "$ORIGINAL_DIR" -maxdepth 1 -name "${ITER_PREFIX}*pyuvstarter*log*.json" -type f 2>/dev/null | while read -r logfile; do
            if [ -f "$logfile" ]; then
                cp "$logfile" "$ITERATION_DIR/" 2>/dev/null || true
            fi
        done

        # Cleanup old iteration logs from project root to prevent accumulation
        find "$ORIGINAL_DIR" -maxdepth 1 -name "${ITER_PREFIX}*pyuvstarter*log*.json" -type f -delete 2>/dev/null || true

        echo "💾 Iteration $i output saved to: $ITERATION_DIR"
        echo ""
    done

    # Generate multi-run summary
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Multi-Run Test Summary"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    pass_count=0
    fail_count=0

    for result in "${MULTI_RUN_RESULTS[@]}"; do
        IFS=':' read -r iter_num status <<< "$result"
        if [ "$status" = "PASS" ]; then
            ((pass_count++))
            echo "✅ Iteration $iter_num: PASSED"
        else
            ((fail_count++))
            echo "❌ Iteration $iter_num: FAILED"

            # Show which specific tests failed
            iter_dir="$MULTI_RUN_OUTPUT_DIR/iteration_$(printf '%02d' "$iter_num")"
            if [ -f "$iter_dir/stdout.log" ]; then
                echo "   Failed tests:"
                grep -E "❌.*FAILED" "$iter_dir/stdout.log" 2>/dev/null | sed 's/^/   - /' | head -5 || true
            fi
        fi
    done

    echo "📁 All iteration logs saved in: $MULTI_RUN_OUTPUT_DIR"
    exit_with_summary $pass_count "$ITERATIONS"
fi

# Normal single-run mode continues below (backward compatible)

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

    # Use uv run to execute test file (respects UV_PYTHON if set)
    run_single_test "$test" "(cd '$ORIGINAL_DIR' && uv run 'tests/$test')"

    echo ""
done

echo "🚀 Running Integration Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run shell-based integration tests
cd "$TEST_DIR"
for test in "${INTEGRATION_TESTS[@]}"; do
    echo "Running: $test"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    run_single_test "$test" "bash '$ORIGINAL_DIR/tests/$test'"

    echo ""
    # Clean up between tests
    cd "$TEST_DIR"
    rm -rf test_*
done

# Calculate total duration
SUITE_END_TIME=$(date +%s.%N 2>/dev/null || date +%s)
TOTAL_DURATION=$(echo "$SUITE_END_TIME - $SUITE_START_TIME" | bc 2>/dev/null || echo "0")

# Shared function: Add test results to XML file by file extension filter
add_xml_testcases() {
    local xml_file=$1
    local extension=$2  # e.g., ".py" or ".sh"
    local failure_type=$3  # e.g., "AssertionError" or "TestFailure"

    for result in "${TEST_RESULTS[@]}"; do
        IFS=':' read -r name status duration <<< "$result"

        # Only include tests matching the extension
        if [[ "$name" == test_*$extension ]]; then
            # Extract test name without extension
            local test_name="${name%"$extension"}"
            local classname="pyuvstarter.tests.$test_name"

            if [ "$status" = "PASSED" ]; then
                echo "    <testcase name=\"$test_name\" classname=\"$classname\" time=\"$duration\"/>" >> "$xml_file"
            else
                # For failures, add tracing context (iteration number, environment, log references)
                local iteration_info=""
                if [ -n "$PYUVSTARTER_CURRENT_ITERATION" ] && [ "$PYUVSTARTER_CURRENT_ITERATION" != "0" ]; then
                    iteration_info="Iteration: ${PYUVSTARTER_CURRENT_ITERATION}\n"
                fi

                local env_info=""
                if [ -n "$UV_PYTHON" ]; then
                    env_info="UV_PYTHON: ${UV_PYTHON}\n"
                fi

                cat >> "$xml_file" << XML_EOF
    <testcase name="$test_name" classname="$classname" time="$duration">
      <failure message="Test failed - see logs for details" type="$failure_type">
${iteration_info}${env_info}Test suite: $name
Check logs: stdout.log, stderr.log, and iteration_*_${test_name}_pyuvstarter_setup_log.json files
      </failure>
    </testcase>
XML_EOF
            fi
        fi
    done
}

# Generate JUnit XML for GitHub Actions
generate_junit_xml() {
    local xml_file="$ORIGINAL_DIR/test_results_comprehensive.xml"
    local total_tests=$((${#PYTHON_TESTS[@]} + ${#INTEGRATION_TESTS[@]}))
    local failed_count=${#FAILED_TESTS[@]}

    # Build testsuite name suffix from environment (os, python version)
    local name_suffix=""
    if [ -n "$PYUVSTARTER_TEST_OS" ] || [ -n "$PYUVSTARTER_TEST_PYTHON" ]; then
        local os_part="${PYUVSTARTER_TEST_OS:-unknown}"
        local py_part="${PYUVSTARTER_TEST_PYTHON:-unknown}"
        name_suffix=" ($os_part, py$py_part)"
    fi

    cat > "$xml_file" << 'XML_EOF'
<?xml version="1.0" encoding="UTF-8"?>
XML_EOF

    # Add testsuites opening tag with optional properties for tracing
    cat >> "$xml_file" << XML_EOF
<testsuites name="pyuvstarter_comprehensive_tests${name_suffix}" tests="$total_tests" failures="$failed_count" time="$TOTAL_DURATION">
XML_EOF

    # Add properties element for environment context (JUnit XML standard)
    if [ -n "$PYUVSTARTER_CURRENT_ITERATION" ] || [ -n "$UV_PYTHON" ] || [ -n "$GITHUB_RUN_ID" ] || [ -n "$PYUVSTARTER_TEST_OS" ] || [ -n "$PYUVSTARTER_TEST_PYTHON" ]; then
        cat >> "$xml_file" << 'XML_EOF'
  <properties>
XML_EOF
        if [ -n "$PYUVSTARTER_CURRENT_ITERATION" ] && [ "$PYUVSTARTER_CURRENT_ITERATION" != "0" ]; then
            cat >> "$xml_file" << XML_EOF
    <property name="test.iteration" value="$PYUVSTARTER_CURRENT_ITERATION"/>
XML_EOF
        fi
        if [ -n "$UV_PYTHON" ]; then
            cat >> "$xml_file" << XML_EOF
    <property name="env.UV_PYTHON" value="$UV_PYTHON"/>
XML_EOF
        fi
        if [ -n "$PYUVSTARTER_TEST_OS" ]; then
            cat >> "$xml_file" << XML_EOF
    <property name="test.os" value="$PYUVSTARTER_TEST_OS"/>
XML_EOF
        fi
        if [ -n "$PYUVSTARTER_TEST_PYTHON" ]; then
            cat >> "$xml_file" << XML_EOF
    <property name="test.python_version" value="$PYUVSTARTER_TEST_PYTHON"/>
XML_EOF
        fi
        if [ -n "$GITHUB_RUN_ID" ]; then
            cat >> "$xml_file" << XML_EOF
    <property name="ci.github_run_id" value="$GITHUB_RUN_ID"/>
XML_EOF
        fi
        cat >> "$xml_file" << 'XML_EOF'
  </properties>
XML_EOF
    fi

    cat >> "$xml_file" << XML_EOF
  <testsuite name="pyuvstarter.python_unit_tests${name_suffix}" tests="${#PYTHON_TESTS[@]}" failures="0" time="0">
XML_EOF

    # Add Python test results
    add_xml_testcases "$xml_file" ".py" "AssertionError"

    # Close Python test suite, open integration test suite
    cat >> "$xml_file" << XML_EOF
  </testsuite>
  <testsuite name="pyuvstarter.integration_tests${name_suffix}" tests="${#INTEGRATION_TESTS[@]}" failures="0" time="0">
XML_EOF

    # Add integration test results
    add_xml_testcases "$xml_file" ".sh" "TestFailure"

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
else
    echo ""
    echo "❌ Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo ""
    echo "Test artifacts preserved in: $TEST_DIR"
fi

# Use shared exit function
PASSED_TESTS=$((TOTAL_TESTS - ${#FAILED_TESTS[@]}))
exit_with_summary $PASSED_TESTS $TOTAL_TESTS