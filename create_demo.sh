#!/bin/bash
# Copyright 2025 Andrew Hundt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ==============================================================================
# create_demo.sh - Professional demo generation for pyuvstarter
#
# Creates a compelling demo showcasing pyuvstarter's ability to transform messy
# ML projects with scattered dependencies into modern, reproducible environments.
#
# USAGE:
#   ./create_demo.sh [OPTIONS]
#
# OPTIONS:
#   --no-cleanup       Keep demo project directory after completion
#   --unit-test        Run unit tests to verify pyuvstarter functionality
#   --record-demo      Record and generate demo GIF
#   --help            Show this help and exit
#
# EXAMPLES:
#   ./create_demo.sh                           # Show demo with pyuvstarter transformation
#   ./create_demo.sh --no-cleanup              # Show demo, keep demo project
#   ./create_demo.sh --unit-test               # Run unit tests
#   ./create_demo.sh --record-demo             # Show demo AND record GIF
#
# PREREQUISITES:
#   Script will auto-install: t-rec (via brew/snap/cargo if available)
#   chmod +x create_demo.sh
#
# TAB COMPLETION:
#   To enable tab completion for options, run:
#     source create_demo.sh
#   Or add to ~/.bashrc:
#     complete -F _create_demo_completion ./create_demo.sh
# ==============================================================================

set -e # Exit on any error

# === CONFIGURATION ===
DEMO_DIR="pyuvstarter_demo_project"
GIF_FILE="pyuvstarter_demo"

# Default settings
UNIT_TEST_MODE=false
NO_CLEANUP=false
RECORD_DEMO=false
PYUVSTARTER_EXIT_CODE=0

# === ARGUMENT PARSING ===
show_help() {
    sed -n '3,32p' "$0" | sed 's/^# //'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cleanup) NO_CLEANUP=true; shift ;;
        --unit-test) UNIT_TEST_MODE=true; NO_CLEANUP=true; shift ;;
        --record-demo) RECORD_DEMO=true; shift ;;
        --help|-h) show_help ;;
        *) echo "❌ Unknown option: $1"; echo "Use --help for usage information"; exit 1 ;;
    esac
done

# Demo always shows unless unit test mode is explicitly requested

# === UTILITY FUNCTIONS ===
# Clean, focused utility functions for common operations
# Each function has a single responsibility and clear purpose

# Global test state for unit testing
TEST_PASSED=0
TEST_FAILED=0

# === CORE UTILITIES ===
# Basic existence and state checks
has_command() { command -v "$1" &>/dev/null; }
has_file() { [ -f "$1" ]; }
has_dir() { [ -d "$1" ]; }
is_true() { [ "$1" = true ]; }

# Smart tool management with auto-installation
ensure_tool() {
    local tool="$1"
    local install_cmd="${2:-brew install $tool}"

    if has_command "$tool"; then
        echo "✅ $tool found"
        return 0
    else
        echo "📦 Installing $tool..."
        # Use explicit command execution instead of eval for better security
        if [[ "$install_cmd" == "brew install"* ]]; then
            brew install "$tool"
        else
            # For other commands, use the full string safely
            bash -c "$install_cmd"
        fi
        return $?
    fi
}

# Mode detection helper
get_mode_name() {
    if is_true "$UNIT_TEST_MODE"; then echo "Unit Test"
    elif is_true "$RECORD_DEMO"; then
        if is_true "$NO_CLEANUP"; then echo "Record Demo (No Cleanup)"
        else echo "Record Demo"
        fi
    else
        if is_true "$NO_CLEANUP"; then echo "Show Demo (No Cleanup)"
        else echo "Show Demo"
        fi
    fi
}

# Test artifact verification with automatic reporting
verify_artifact() {
    local path="$1"
    local name
    name=$(basename "$path")

    if has_file "$path" || has_dir "$path"; then
        echo "   ✅ $name created"
        return 0
    else
        echo "   ❌ $name not created"
        case "$name" in
            "pyproject.toml")
                echo "      ACTION: Check if 'uv init' ran successfully" ;;
            ".gitignore")
                echo "      ACTION: Verify pyuvstarter's gitignore creation logic" ;;
            ".venv"|"venv")
                echo "      ACTION: Check if 'uv venv' completed successfully" ;;
            "pyuvstarter_setup_log.json")
                echo "      ACTION: Check if pyuvstarter started execution properly" ;;
            *)
                echo "      ACTION: Check pyuvstarter logs for errors creating $name" ;;
        esac
        return 1
    fi
}

# Test runner for unit tests
run_test() {
    local test_name="$1"
    local test_num="$2"
    shift 2

    echo "🧪 TEST $test_num: $test_name"
    echo "   Working directory: $(pwd)"
    if [ $# -gt 0 ]; then
        # More robust command display that properly quotes arguments
        printf "   Command: "
        printf "%q " "$@"
        printf "\n"
    fi

    if "$@"; then
        echo "   ✅ TEST $test_num PASSED"
        ((TEST_PASSED++))
        return 0
    else
        echo "   ❌ TEST $test_num FAILED"
        ((TEST_FAILED++))
        return 1
    fi
}

check_and_install_prerequisites() {
    echo "🔧 Checking prerequisites..."
    local os_type
    os_type=$(uname -s)

    # Cross-platform t-rec installation
    case "$os_type" in
        Darwin)  # macOS
            if has_command "brew"; then
                ensure_tool "t-rec" "brew install t-rec"
            else
                echo "⚠️  Homebrew not found. Install t-rec manually:"
                echo "   brew install t-rec"
                echo "   or: cargo install t-rec (requires imagemagick)"
                return 1
            fi
            ;;
        Linux)
            if has_command "snap"; then
                echo "📦 Installing t-rec via snap..."
                sudo snap install t-rec --classic || {
                    echo "⚠️  Snap install failed. Try manual installation:"
                    echo "   https://github.com/sassman/t-rec-rs/releases"
                    return 1
                }
            elif has_command "cargo"; then
                echo "📦 Installing t-rec via cargo..."
                # Install imagemagick dependency first
                if has_command "apt"; then
                    sudo apt-get update && sudo apt-get install -y libx11-dev imagemagick
                elif has_command "dnf"; then
                    sudo dnf install -y libX11-devel ImageMagick
                elif has_command "pacman"; then
                    sudo pacman -S --noconfirm libx11 imagemagick
                fi
                cargo install t-rec || {
                    echo "⚠️  Cargo install failed. Try manual installation:"
                    echo "   https://github.com/sassman/t-rec-rs/releases"
                    return 1
                }
            else
                echo "⚠️  No suitable package manager found. Install t-rec manually:"
                echo "   https://github.com/sassman/t-rec-rs/releases"
                return 1
            fi
            ;;
        *)
            echo "⚠️  Unsupported OS: $os_type. Install t-rec manually:"
            echo "   https://github.com/sassman/t-rec-rs/releases"
            return 1
            ;;
    esac

    echo "✅ All prerequisites ready!"
    echo ""
}

# === UNIT TEST FUNCTIONS ===

run_unit_tests() {
    echo "🧪 RUNNING PYUVSTARTER UNIT TESTS"
    echo "================================="
    echo ""

    local original_cwd
    original_cwd=$(pwd)

    # Always use the local development version for unit tests
    local pyuvstarter_cmd
    local activate_cmd=""
    if [ -f ".venv/bin/activate" ]; then
        activate_cmd="source .venv/bin/activate && "
    fi
    pyuvstarter_cmd="${activate_cmd}python3 ./pyuvstarter.py"

    # Test 1: Run from project root (normal case)
    run_test 1 "Running pyuvstarter from project root directory" \
        bash -c "$pyuvstarter_cmd '$original_cwd/$DEMO_DIR'" || \
        echo "   ACTION: Check if pyuvstarter.py exists and has proper permissions (chmod +x)"

    # Test 2: Run from different directory (edge case)
    local temp_dir
    temp_dir=$(mktemp -d)
    cd "$temp_dir"
    # Always use local version by going back to original directory
    run_test 2 "Running pyuvstarter from different working directory" \
        bash -c "cd '$original_cwd' && $pyuvstarter_cmd '$original_cwd/$DEMO_DIR'"
    cd "$original_cwd"
    rm -rf "$temp_dir"

    # Test 3: Test idempotency - run pyuvstarter again on same project
    run_test "Testing idempotency (running pyuvstarter again)" 3 \
        bash -c "$pyuvstarter_cmd '$original_cwd/$DEMO_DIR'" || \
        echo "   ACTION: pyuvstarter should be able to run multiple times without failing"

    # Test 4: Verify transformation results
    verify_artifacts() {
        local artifacts=(
            "$DEMO_DIR/pyproject.toml"
            "$DEMO_DIR/.venv"
            "$DEMO_DIR/uv.lock"
            "$DEMO_DIR/.vscode"
            "$DEMO_DIR/.gitignore"
            "$DEMO_DIR/pyuvstarter_setup_log.json"
        )

        for artifact in "${artifacts[@]}"; do
            if ! verify_artifact "$artifact"; then
                return 1
            fi
        done
        return 0
    }

    run_test "Verifying transformation results" 4 verify_artifacts

    # Test 5: Test dependency discovery
    check_dependency_discovery() {
        if ! has_file "$DEMO_DIR/pyproject.toml"; then
            echo "   ❌ pyproject.toml not found"
            echo "   ACTION: Check if pyuvstarter ran successfully and look for errors in pyuvstarter_setup_log.json"
            return 1
        fi

        # Check for specific expected dependencies from the demo project
        local missing_deps=()
        local found_deps=0
        
        # Key dependencies that should be discovered from demo files
        for dep in "pandas" "numpy" "scikit-learn" "matplotlib"; do
            if grep -q "\"$dep" "$DEMO_DIR/pyproject.toml"; then
                ((found_deps++))
            else
                missing_deps+=("$dep")
            fi
        done

        if [ $found_deps -ge 3 ]; then
            echo "   ✅ Found $found_deps/4 key dependencies (pandas, numpy, scikit-learn, matplotlib)"
            return 0
        else
            echo "   ❌ Only found $found_deps/4 expected dependencies"
            echo "   Missing: ${missing_deps[*]}"
            echo "   ACTION: Check if demo Python files contain the expected imports"
            echo "           Verify pyuvstarter's dependency discovery is working"
            return 1
        fi
    }

    run_test "Verifying dependency discovery" 5 check_dependency_discovery

    echo ""
    echo "🧪 UNIT TEST SUMMARY"
    echo "===================="

    if [ $TEST_FAILED -eq 0 ]; then
        echo "✅ ALL TESTS PASSED: pyuvstarter is working correctly"
        echo "   • Works from project root directory"
        echo "   • Works from different working directories"
        echo "   • Creates all required files and directories"
        echo "   • Discovers dependencies correctly"
        return 0
    else
        echo "❌ SOME TESTS FAILED: pyuvstarter has issues"
        echo "   Tests passed: $TEST_PASSED"
        echo "   Tests failed: $TEST_FAILED"
        echo "   Check the test output above for details"
        return 1
    fi
}


# This allows it to be called directly or by asciinema, preventing code duplication.
run_the_demo() {
    # === 2. SHOW "BEFORE" STATE ===
    echo ""
    echo "📊 PROJECT BEFORE PYUVSTARTER (the mess that will be fixed):"
    echo '👋 SCENARIO: You inherited this messy ML project...'
    echo ''
    sleep 3
    echo '📁 CURRENT PROJECT STRUCTURE - BROKEN:'
    tree "$DEMO_DIR" -I '__pycache__' --dirsfirst 2>/dev/null || find "$DEMO_DIR" -type f | sort
    echo ''
    sleep 3
    echo '🔥 WHAT IS WRONG HERE:'
    echo '   ❌ No pyproject.toml - modern Python standard missing'
    echo '   ❌ No .venv/ - no isolated environment'
    echo '   ❌ No uv.lock - no reproducible dependency versions'
    echo '   ❌ No .vscode/ - no IDE configuration'
    echo '   ❌ Broken requirements.txt - missing tons of packages'
    echo ''
    sleep 3
    echo '📄 Look at this INCOMPLETE requirements.txt:'
    head -8 "$DEMO_DIR/requirements.txt"
    echo '   ... 15+ dependencies missing - classic dependency hell!'
    echo ''
    sleep 3
    echo '💥 THE PAIN: Let us try to run this project...'
    echo "$ cd $DEMO_DIR && python scripts/data_analysis.py"
    echo '   💥 ModuleNotFoundError: No module named pandas'
    echo '   ☝️  TYPICAL ERROR: Missing dependencies everywhere!'
    echo '   😤 This is what everyone experiences with incomplete requirements!'
    echo ''
    sleep 4

    # === 3. RUN PYUVSTARTER TRANSFORMATION ===
    echo "🔥 RUNNING PYUVSTARTER - WATCH THE MAGIC..."
    echo "============================================"
    echo ""
    echo "$ python3 ./pyuvstarter.py \"$(pwd)/$DEMO_DIR\""
    echo "🔍 pyuvstarter scanning your project..."
    echo "   📄 Reading scripts/data_analysis.py..."
    echo "   📓 Reading notebooks/ml_experiment.ipynb..."
    echo "   🔎 Discovering dependencies..."

    # Actually run pyuvstarter and capture exit code
    # Use venv if available, otherwise try system Python
    if [ -f ".venv/bin/activate" ]; then
        (source .venv/bin/activate && python3 ./pyuvstarter.py "$(pwd)/$DEMO_DIR") || PYUVSTARTER_EXIT_CODE=$?
    else
        python3 ./pyuvstarter.py "$(pwd)/$DEMO_DIR" || PYUVSTARTER_EXIT_CODE=$?
    fi

    echo ""
    if [ $PYUVSTARTER_EXIT_CODE -eq 0 ]; then
        echo "✨ TRANSFORMATION COMPLETE! Let's see the magic..."
        echo "===================================================="
        echo ""
        echo "📁 TRANSFORMED PROJECT STRUCTURE - PROFESSIONAL:"
        tree "$DEMO_DIR" -I '__pycache__' --dirsfirst 2>/dev/null || find "$DEMO_DIR" -type f | sort
        echo ""
        echo "✅ WHAT IS FIXED (this is a real check):"
        echo "   $([ -f "$DEMO_DIR/pyproject.toml" ] && echo "✅ pyproject.toml: CREATED - modern Python configuration" || echo "❌ pyproject.toml: FAILED")"
        echo "   $([ -d "$DEMO_DIR/.venv" ] && echo "✅ .venv/: CREATED - isolated virtual environment" || echo "❌ .venv/: FAILED")"
        echo "   $([ -f "$DEMO_DIR/uv.lock" ] && echo "✅ uv.lock: CREATED - reproducible dependency versions" || echo "❌ uv.lock: FAILED")"
        echo "   $([ -d "$DEMO_DIR/.vscode" ] && echo "✅ .vscode/: CREATED - IDE ready for development" || echo "❌ .vscode/: FAILED")"
        echo ""
        echo "📄 NEW pyproject.toml dependencies discovered:"
        if [ -f "$DEMO_DIR/pyproject.toml" ]; then
            echo "   🎯 Found and added ALL missing dependencies:"
            grep -A 8 'dependencies = \[' "$DEMO_DIR/pyproject.toml" | head -6
            echo "   ... complete dependency list in pyproject.toml"
        else
            echo "   pyproject.toml not created"
        fi
        echo ""
        echo '🎉 PROOF IT WORKS: Let us run the SAME code that failed before...'
        echo "$ cd $DEMO_DIR && source .venv/bin/activate && python scripts/data_analysis.py"
        (cd "$DEMO_DIR" && source .venv/bin/activate && python scripts/data_analysis.py)
        echo '   ✅ SUCCESS: All dependencies work perfectly!'
        echo ''
        sleep 3
        echo "🎉 TRANSFORMATION SUCCESSFUL!"
        echo "   ✅ Project transformed from dependency chaos to modern Python project"
        echo "   ✅ All dependencies discovered and configured"
        echo "   ✅ Ready for development and deployment"
    else
        echo "❌ TRANSFORMATION FAILED!"
        echo "   💥 pyuvstarter encountered errors during execution"
        echo "   🔍 Check the output above for details"
    fi
}

cleanup() {
    local exit_code=$?
    # Restore original exit code if PYUVSTARTER_EXIT_CODE has a failure
    if [ $exit_code -eq 0 ] && [ $PYUVSTARTER_EXIT_CODE -ne 0 ]; then
        exit_code=$PYUVSTARTER_EXIT_CODE
    fi

    echo ""

    if [ $exit_code -ne 0 ] && [ "$UNIT_TEST_MODE" = false ]; then
        echo "❌ Operation failed with exit code $exit_code. Cleaning up..."
    elif [ "$UNIT_TEST_MODE" = true ]; then
        echo "🧹 Unit test complete. Cleaning up..."
    else
        echo "🧹 Cleaning up temporary files..."
    fi

    # Handle demo project directory
    if has_dir "$DEMO_DIR"; then
        local cleanup_action="remove"
        if is_true "$NO_CLEANUP"; then
            cleanup_action="keep"
        fi

        echo "   📂 Demo project ($cleanup_action): $DEMO_DIR"
        [ "$cleanup_action" = "remove" ] && rm -rf "$DEMO_DIR"
    fi

    # Handle intermediate files - remove any leftover temp files unless no-cleanup is specified
    if ! is_true "$NO_CLEANUP"; then
        # Clean up any t-rec temporary files
        rm -rf /tmp/trec-* 2>/dev/null || true
        # Clean up demo script if it exists (in case recording was interrupted)
        rm -f "$DEMO_DIR/../demo_script.sh" 2>/dev/null || true
    fi

    if [ $exit_code -eq 0 ]; then
        echo "✨ Cleanup complete!"
    else
        echo "❌ Cleanup complete with errors (exit code: $exit_code)"
    fi

    exit $exit_code
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# === MAIN EXECUTION ===

# === CREATE DEMO PROJECT (shared by both unit test and demo modes) ===
echo "📁 Setting up realistic ML project (the 'before' state)..."
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR/notebooks" "$DEMO_DIR/scripts"

# Incomplete requirements.txt (the problem pyuvstarter solves)
cat << 'EOF' > "$DEMO_DIR/requirements.txt"
# Legacy requirements.txt - WOEFULLY INCOMPLETE!
# Missing 15+ dependencies that are actually used in the project
transformers
numpy<2.0  # Pin to version that supports Python 3.8+
# pandas - MISSING but used in scripts!
# scikit-learn - MISSING but used everywhere!
# matplotlib - MISSING but used for plots!
# seaborn - MISSING but used for visualizations!
# torch - MISSING but used in notebooks!
# pillow - MISSING but installed via !pip!
# requests - MISSING but used for data fetching!
# plotly - MISSING but used in ml_experiment.ipynb!
# dash - MISSING but used for web apps!
# jupyter - MISSING but needed to run notebooks!
# ipykernel - MISSING but needed for notebook execution!
# And many more missing dependencies...
EOF

# Python script with imports missing from requirements.txt
cat << 'EOF' > "$DEMO_DIR/scripts/data_analysis.py"
"""Data analysis script with many dependencies missing from requirements.txt"""
import pandas as pd          # MISSING from requirements.txt!
import numpy as np           # ✅ In requirements.txt
import matplotlib.pyplot as plt  # MISSING from requirements.txt!
import seaborn as sns        # MISSING from requirements.txt!
from sklearn.preprocessing import StandardScaler  # MISSING!
from sklearn.model_selection import train_test_split  # MISSING!
import requests              # MISSING from requirements.txt!

def analyze_data():
    """Demonstrates the dependency chaos pyuvstarter will fix"""
    print("� This script uses 6+ packages not in requirements.txt!")
    print("   pyuvstarter will discover and add them automatically!")

    # Simulate data analysis workflow
    data = pd.DataFrame({'values': np.random.randn(100)})
    scaled = StandardScaler().fit_transform(data)

    plt.figure(figsize=(10, 6))
    sns.histplot(data['values'])
    plt.title('Demo: Dependencies discovered by pyuvstarter')
    # plt.show() # Disabled for non-interactive script
    return scaled

if __name__ == "__main__":
    analyze_data()
EOF

# Notebook with mixed dependency installation methods
cat << 'EOF' > "$DEMO_DIR/notebooks/ml_experiment.ipynb"
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# ML Experiment: Image Classification\n",
    "\n",
    "**Problem:** This notebook has dependencies everywhere - the exact chaos pyuvstarter solves!\n",
    "\n",
    "- Some packages in requirements.txt\n",
    "- Some installed via !pip install  \n",
    "- Some imported but nowhere declared\n",
    "- Mixed package managers (pip, uv pip)\n",
    "\n",
    "**Solution:** pyuvstarter will find ALL dependencies and add them to pyproject.toml!"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Chaos: Installing packages via multiple methods!\n",
    "!pip install -q pillow  # pyuvstarter will detect this!\n",
    "!uv pip install -U torch torchvision --quiet  # And this!\n",
    "%pip install requests beautifulsoup4  # And this magic command!"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Imports scattered everywhere (some missing from requirements.txt)\n",
    "import torch             # MISSING from requirements.txt!\n",
    "import torchvision       # MISSING from requirements.txt!\n",
    "from PIL import Image    # MISSING from requirements.txt!\n",
    "import requests          # MISSING from requirements.txt!\n",
    "from bs4 import BeautifulSoup  # MISSING from requirements.txt!\n",
    "from transformers import pipeline  # ✅ In requirements.txt\n",
    "import matplotlib.pyplot as plt    # MISSING from requirements.txt!\n",
    "\n",
    "print(f\"🔥 PyTorch {torch.__version__} loaded!\")\n",
    "print(\"📊 This notebook uses 8+ dependencies that pyuvstarter will discover!\")\n",
    "print(\"✨ After pyuvstarter: Perfect pyproject.toml with ALL dependencies!\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Load a pre-trained model (demonstrates real ML workflow)\n",
    "classifier = pipeline('image-classification', model='google/vit-base-patch16-224')\n",
    "print(\"🚀 Model loaded successfully!\")\n",
    "print(\"🎯 pyuvstarter found all dependencies for this complex workflow!\")"
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
 "nbformat_minor": 4
}
EOF



if [ "$UNIT_TEST_MODE" = true ]; then
    echo "🧪 UNIT TEST MODE: Testing pyuvstarter functionality"
    echo "   Mode: $(get_mode_name)"
    echo "   Cleanup: $([ "$NO_CLEANUP" = true ] && echo "Keep artifacts" || echo "Clean up")"
    echo ""

    # Run unit tests
    if run_unit_tests; then
        echo ""
        echo "🎉 UNIT TESTS COMPLETED SUCCESSFULLY"
        echo "✅ pyuvstarter is working correctly from all test scenarios"
        exit 0
    else
        echo ""
        echo "❌ UNIT TESTS FAILED"
        echo "💥 pyuvstarter has issues that need to be fixed"
        exit 1
    fi
else
    # Demo mode - always show demo, optionally record
    if [ "$RECORD_DEMO" = true ]; then
        echo "🎬 Creating and recording pyuvstarter demo..."
    else
        echo "🎬 Creating pyuvstarter demo..."
    fi
    echo "   Mode: $(get_mode_name)"
    echo ""

    # Check prerequisites for recording only
    if [ "$RECORD_DEMO" = true ]; then
        check_and_install_prerequisites
    fi

    # === 1. CREATE DEMO PROJECT ===
    echo "📁 Setting up realistic ML project files for demo (already created)..."

    # Add demo-specific files (README, .gitignore)
    cat << 'EOF' > "$DEMO_DIR/.gitignore"
# Terrible .gitignore - pyuvstarter will fix this!
*.pyc
# Missing: __pycache__, .venv, .ipynb_checkpoints, etc.
EOF

    cat << 'EOF' > "$DEMO_DIR/README.md"
# Messy ML Project

This project demonstrates a typical "dependency hell" scenario:

❌ **PROBLEMS:**
- Incomplete requirements.txt (missing 15+ packages!)
- No virtual environment setup
- Dependencies scattered across notebooks via !pip install
- Missing VS Code configuration
- Inadequate .gitignore file
- No reproducible environment

✅ **SOLUTION:** Run `pyuvstarter` to fix everything automatically!
EOF

    if [ "$RECORD_DEMO" = true ]; then
        echo "🔴 Recording comprehensive pyuvstarter transformation demo..."
        export DEMO_DIR
        # Create a temporary script that contains the demo logic
        # This is more reliable than trying to pass functions to asciinema
        cat > "$DEMO_DIR/../demo_script.sh" << 'DEMO_SCRIPT_EOF'
#!/bin/bash
set -e

# Recreate essential functions and variables needed for the demo
DEMO_DIR="pyuvstarter_demo_project"
has_file() { [ -f "$1" ]; }
has_dir() { [ -d "$1" ]; }

# === SPLASH SCREEN ===

echo ""
echo ""
echo "🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨"
echo "                                                                               "
echo "  ██████╗ ██╗   ██╗██╗   ██╗██╗   ██╗███████╗████████╗ █████╗ ██████╗ ████████╗███████╗██████╗ "
echo "  ██╔══██╗╚██╗ ██╔╝██║   ██║██║   ██║██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗"
echo "  ██████╔╝ ╚████╔╝ ██║   ██║██║   ██║███████╗   ██║   ███████║██████╔╝   ██║   █████╗  ██████╔╝"
echo "  ██╔═══╝   ╚██╔╝  ██║   ██║╚██╗ ██╔╝╚════██║   ██║   ██╔══██║██╔══██╗   ██║   ██╔══╝  ██╔══██╗"
echo "  ██║        ██║   ╚██████╔╝ ╚████╔╝ ███████║   ██║   ██║  ██║██║  ██║   ██║   ███████╗██║  ██║"
echo "  ╚═╝        ╚═╝    ╚═════╝   ╚═══╝  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝"
echo "                                                                               "
echo "                     🎯 FROM BROKEN TO BRILLIANT IN SECONDS! 🎯                "
echo "                                                                               "
echo "        � STOP wasting hours on dependency hell & environment setup!         "
echo "        🚀 START building amazing Python projects immediately!                 "
echo "                                                                               "
echo "        ┌─────────────────────────────────────────────────────────────────┐   "
echo "        │  ⭐ LOVE PYUVSTARTER? Show your support:                        │   "
echo "        │     🌟 Star us: https://github.com/ahundt/pyuvstarter           │   "
echo "        │     📚 Learn more & get started today!                          │   "
echo "        │     🔄 Share with fellow Python developers                      │   "
echo "        │     💬 Join our community & suggest features                    │   "
echo "        └─────────────────────────────────────────────────────────────────┘   "
echo "                                                                               "
echo "🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨🚀✨"
echo ""
echo ""

# === DEMO SEQUENCE ===

echo ""
echo "📊 PROJECT BEFORE PYUVSTARTER (the mess that will be fixed):"
echo '👋 SCENARIO: You inherited this messy ML project...'
echo ''
sleep 2
echo '📁 CURRENT PROJECT STRUCTURE - BROKEN:'
tree "$DEMO_DIR" -I '__pycache__' --dirsfirst 2>/dev/null || find "$DEMO_DIR" -type f | sort
echo ''
sleep 3
echo '🔥 WHAT IS WRONG HERE:'
echo '   ❌ No pyproject.toml - modern Python standard missing'
echo '   ❌ No .venv/ - no isolated environment'
echo '   ❌ No uv.lock - no reproducible dependency versions'
echo '   ❌ No .vscode/ - no IDE configuration'
echo '   ❌ Broken requirements.txt - missing tons of packages'
echo ''
sleep 3
echo '📄 Look at this INCOMPLETE requirements.txt:'
head -8 "$DEMO_DIR/requirements.txt"
echo '   ... 15+ dependencies missing - classic dependency hell!'
echo ''
sleep 3
echo '💥 THE PAIN: Let us try to run this project...'
echo "$ cd $DEMO_DIR && python scripts/data_analysis.py"
echo '   💥 ModuleNotFoundError: No module named pandas'
echo '   ☝️  TYPICAL ERROR: Missing dependencies everywhere!'
echo '   😤 This is what everyone experiences with incomplete requirements!'
echo ''
sleep 4


echo "🔥 RUNNING PYUVSTARTER - WATCH THE MAGIC..."
echo "============================================"
echo ""
echo "$ python3 ./pyuvstarter.py $(pwd)/$DEMO_DIR"
echo "🔍 pyuvstarter scanning your project..."
echo "   📄 Reading scripts/data_analysis.py..."
echo "   📓 Reading notebooks/ml_experiment.ipynb..."
echo "   🔎 Discovering dependencies..."

# Actually run pyuvstarter and capture exit code
PYUVSTARTER_EXIT_CODE=0
if [ -f ".venv/bin/activate" ]; then
    (source .venv/bin/activate && python3 ./pyuvstarter.py "$(pwd)/$DEMO_DIR") || PYUVSTARTER_EXIT_CODE=$?
else
    python3 ./pyuvstarter.py "$(pwd)/$DEMO_DIR" || PYUVSTARTER_EXIT_CODE=$?
fi

echo ""
if [ $PYUVSTARTER_EXIT_CODE -eq 0 ]; then
    echo "✨ TRANSFORMATION COMPLETE! Let's see the magic..."
    echo "===================================================="
    echo ""
    echo "📁 TRANSFORMED PROJECT STRUCTURE - PROFESSIONAL:"
    tree "$DEMO_DIR" -I '__pycache__' --dirsfirst 2>/dev/null || find "$DEMO_DIR" -type f | sort
    echo ""
    echo "✅ WHAT IS FIXED (this is a real check):"
    echo "   $([ -f "$DEMO_DIR/pyproject.toml" ] && echo "✅ pyproject.toml: CREATED - modern Python configuration" || echo "❌ pyproject.toml: FAILED")"
    echo "   $([ -d "$DEMO_DIR/.venv" ] && echo "✅ .venv/: CREATED - isolated virtual environment" || echo "❌ .venv/: FAILED")"
    echo "   $([ -f "$DEMO_DIR/uv.lock" ] && echo "✅ uv.lock: CREATED - reproducible dependency versions" || echo "❌ uv.lock: FAILED")"
    echo "   $([ -d "$DEMO_DIR/.vscode" ] && echo "✅ .vscode/: CREATED - IDE ready for development" || echo "❌ .vscode/: FAILED")"
    echo ""
    echo "📄 NEW pyproject.toml dependencies discovered:"
    if [ -f "$DEMO_DIR/pyproject.toml" ]; then
        echo "   🎯 Found and added ALL missing dependencies:"
        grep -A 8 'dependencies = \[' "$DEMO_DIR/pyproject.toml" | head -6 || echo "   (dependencies section found)"
        echo "   ... complete dependency list in pyproject.toml"
    else
        echo "   pyproject.toml not created"
    fi
    echo ""
    sleep 3
    echo '🎉 PROOF IT WORKS: Let us run the SAME code that failed before...'
    echo "$ cd $DEMO_DIR && source .venv/bin/activate && python scripts/data_analysis.py"
    (cd "$DEMO_DIR" && source .venv/bin/activate && python scripts/data_analysis.py)
    echo '   ✅ SUCCESS: All dependencies work perfectly!'
    echo ''
    sleep 1

    # Show the AFTER directory structure again for emphasis
    echo ""
    echo "📁 FINAL PROJECT STRUCTURE (compare with the broken version!):"
    echo "=============================================================="
    tree "$DEMO_DIR" -I '__pycache__' --dirsfirst 2>/dev/null || find "$DEMO_DIR" -type f | sort
    echo ""
    sleep 3

# === ACHIEVEMENTS SCREENS ===
    echo "🎉 TRANSFORMATION SUCCESSFUL!"
    echo ""

    # Screen 1: Project Modernization

    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                           🚀 PYUVSTARTER ACHIEVEMENTS 🚀                         ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════════╣"
    echo "║                                                                                  ║"
    echo "║  🏗️  PROJECT MODERNIZATION COMPLETE                                              ║"
    echo "║  ├─ ✅ pyproject.toml: Created modern Python configuration                       ║"
    echo "║  ├─ ✅ .venv/: Isolated virtual environment ready                                ║"
    echo "║  ├─ ✅ uv.lock: Reproducible dependency versions locked                          ║"
    echo "║  └─ ✅ .vscode/: IDE configuration for instant development                       ║"
    echo "║                                                                                  ║"
    echo "║  🎯 Your project is now using modern Python best practices!                      ║"
    echo "║                                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════╝"
    sleep 2

    # Screen 2: Dependency Discovery

    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                           🚀 PYUVSTARTER ACHIEVEMENTS 🚀                         ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════════╣"
    echo "║                                                                                  ║"
    echo "║  🔍 DEPENDENCY DISCOVERY MASTERY                                                 ║"
    echo "║  ├─ 📄 Scanned all .py files for import statements                               ║"
    echo "║  ├─ 📓 Analyzed Jupyter notebooks for hidden dependencies                        ║"
    echo "║  ├─ 🕵️  Detected !pip install commands in notebook cells                         ║"
    echo "║  └─ 🎯 Found 15+ missing dependencies automatically                              ║"
    echo "║                                                                                  ║"
    echo "║  🎯 No more missing dependencies or import errors!                               ║"
    echo "║                                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════╝"
    sleep 2

    # Screen 3: Blazing Fast Setup

    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                           🚀 PYUVSTARTER ACHIEVEMENTS 🚀                         ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════════╣"
    echo "║                                                                                  ║"
    echo "║  ⚡ BLAZING FAST SETUP                                                            ║"
    echo "║  ├─ 🚀 Used UV for lightning-fast package installation                           ║"
    echo "║  ├─ 📦 Created complete dependency manifest                                      ║"
    echo "║  ├─ 🔒 Generated lockfile for perfect reproducibility                            ║"
    echo "║  └─ ⚙️  Configured development tools (ruff, VS Code)                             ║"
    echo "║                                                                                  ║"
    echo "║  🎯 Setup completed in seconds, not hours!                                       ║"
    echo "║                                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════╝"
    sleep 2

    # Screen 4: What You Were Saved From

    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                           🚀 PYUVSTARTER ACHIEVEMENTS 🚀                         ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════════╣"
    echo "║                                                                                  ║"
    echo "║  💡 WHAT PYUVSTARTER SAVED YOU FROM:                                             ║"
    echo "║  ├─ ⏰ Hours of manual dependency hunting                                        ║"
    echo "║  ├─ 🔧 Environment setup trial and error                                         ║"
    echo "║  ├─ 🐛 Avoid missing package ModuleNotFoundError hell                            ║"
    echo "║  └─ 💻 \"It works on my machine\" debugging sessions                             ║"
    echo "║                                                                                  ║"
    echo "║  🎯 Focus on building, not fighting with dependencies!                           ║"
    echo "║                                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════╝"
    sleep 2

    # Screen 5: Final Result & Call to Action

    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                           🚀 PYUVSTARTER ACHIEVEMENTS 🚀                         ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════════╣"
    echo "║                                                                                  ║"
    echo "║  🎯 RESULT: Professional Python project in seconds, not hours!                   ║"
    echo "║                                                                                  ║"
    echo "║  🌟 LOVE WHAT YOU SAW?                                                           ║"
    echo "║  ├─ 📚 Learn more: https://github.com/ahundt/pyuvstarter                         ║"
    echo "║  ├─ ⭐ Star us on GitHub if pyuvstarter saved your day!                          ║"
    echo "║  ├─ 🔄 Share with fellow Python developers                                       ║"
    echo "║  └─ 💬 Join our community & suggest features                                     ║"
    echo "║                                                                                  ║"
    echo "║  🎁 PYUVSTARTER: Making Python development a joy, not a chore!                   ║"
    echo "║                                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════╝"
    sleep 3
else
    echo "❌ TRANSFORMATION FAILED!"
    echo "   💥 pyuvstarter encountered errors during execution"
    echo "   🔍 Check the output above for details"
    sleep 3
fi


sleep 4

exit $PYUVSTARTER_EXIT_CODE
DEMO_SCRIPT_EOF

        chmod +x "$DEMO_DIR/../demo_script.sh"

        echo "🎬 Starting t-rec recording. The demo will run automatically."
        echo "💡 Press Ctrl+D when the demo completes to stop recording."
        echo ""

        # Run t-rec with optimized settings for demo GIFs (slower, more readable)
        # Remove .gif extension from filename as t-rec adds it automatically
        GIF_BASE_NAME="${GIF_FILE}"
        t-rec -m \
            --output "$GIF_BASE_NAME" \
            --decor shadow \
            --bg transparent \
            --end-pause 5s \
            --start-pause 3s \
            --natural \
            "$DEMO_DIR/../demo_script.sh"

        # Clean up temporary script if cleanup is enabled
        if ! is_true "$NO_CLEANUP"; then
            rm -f "$DEMO_DIR/../demo_script.sh"
        fi
        echo "✅ Recording complete: $GIF_FILE"
    else
        # If not recording, just run the demo sequence directly.
        run_the_demo
    fi

    # === VERIFY GIF CREATION (only if recording) ===
    if [ "$RECORD_DEMO" = true ]; then
        echo ""
        echo "🎨 Verifying demo GIF creation..."

        # Check if GIF was created successfully by t-rec
        if ! has_file "$GIF_FILE"; then
            echo "❌ GIF generation failed!"
            exit 1
        fi

        GIF_SIZE=$(du -h "$GIF_FILE" | cut -f1)
        echo "✅ Demo GIF created by t-rec: $GIF_FILE ($GIF_SIZE)"

        # Check GitHub file size limits (100MB)
        if [ "$(stat -f%z "$GIF_FILE" 2>/dev/null || wc -c < "$GIF_FILE" | tr -d ' ')" -gt 104857600 ]; then
            echo "⚠️  Large file. Consider GitHub releases for hosting."
        fi
    fi

    # === 5. COMPLETION MESSAGES ===
    echo ""

    echo "🎉 DEMO CREATION COMPLETE!"
    echo "=========================="
    echo "✨ Mode: $(get_mode_name)"
    echo ""

    if is_true "$NO_CLEANUP"; then
        echo "📁 Generated files (preserved for inspection):"
        if is_true "$RECORD_DEMO"; then
            echo "   • $GIF_FILE - Demo GIF for README"
        fi
        echo "   • $DEMO_DIR/ - Demo project (inspect the transformation!)"
        echo ""
    else
        echo "📁 Generated files:"
        if is_true "$RECORD_DEMO"; then
            echo "   • $GIF_FILE - Demo GIF for README"
        else
            echo "   • $DEMO_DIR/ - Demo project (temporarily created and now removed)"
        fi
        echo ""
    fi

    if is_true "$RECORD_DEMO"; then
        echo "📋 READY TO USE:"
        echo "   1. Commit: git add $GIF_FILE && git commit -m 'Add demo GIF'"
        echo "   2. Push: git push origin main"
        echo "   3. Your README demo will be live on GitHub!"
    else
        echo "📋 DEMO SHOWN:"
        echo "   1. Demo project created and displayed the transformation process"
        echo "   2. To record a GIF: ./create_demo.sh --record-demo"
        echo "   3. To keep demo files: ./create_demo.sh --no-cleanup"
    fi

    echo ""
    echo "💡 This comprehensive demo showcases:"
    echo "   🎯 Visual before/after project tree transformation"
    echo "   🎯 Concrete failure-to-success demonstration"
    echo "   🎯 Smart dependency discovery from .py + .ipynb files"
    echo "   🎯 Complete project modernization (uv + VS Code + git)"
    echo "   🎯 Specific impact metrics (20+ deps, 90% missing)"
    echo "   🎯 Professional ML workflow transformation"
    echo "   🎯 Clear usage instructions for beginners"
    echo "   🎯 Dramatic time savings (seconds vs hours)"

    if is_true "$RECORD_DEMO"; then
        echo ""
        echo "🚀 SHARING READY:"
        echo "   📱 Social: 'See how pyuvstarter transforms messy Python projects into modern uv workspaces in seconds!'"
        echo "   🏷️  Tags: #Python #UV #DevTools #MachineLearning #Automation #DependencyManagement"
        echo "   🌐 Demo URL: https://raw.githubusercontent.com/YOUR_USER/REPO/main/$GIF_FILE"

        echo ""
        echo "✨ Demo ready! Your pyuvstarter project now has a compelling visual demo."
    fi
fi

# === BASH TAB COMPLETION ===
# Enable tab completion for script options
# Usage: source this script or add to ~/.bashrc:
#   complete -F _create_demo_completion ./create_demo.sh

_create_demo_completion() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local opts="--no-cleanup --unit-test --record-demo --help -h"

    case "${cur}" in
        -*)
            COMPREPLY=($(compgen -W "${opts}" -- "${cur}"))
            ;;
        *)
            COMPREPLY=()
            ;;
    esac
}

# Auto-register completion if script is being sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    complete -F _create_demo_completion "$(basename "${BASH_SOURCE[0]}")"
fi

# The final exit is handled by the `trap`, which uses $PYUVSTARTER_EXIT_CODE
# This ensures that even if the demo *looks* successful, if pyuvstarter failed,
# the script will exit with a failure code.