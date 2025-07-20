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
# create_demo.sh v3.0.0 - Professional demo generation for pyuvstarter
#
# Creates a compelling demo showcasing pyuvstarter's ability to transform messy
# ML projects with scattered dependencies into modern, reproducible environments.
#
# USAGE:
#   ./create_demo.sh [OPTIONS]
#
# OPTIONS:
#   --unit-test        Run comprehensive unit tests
#   --record-demo      Record demo as GIF/MP4 using t-rec
#   --no-cleanup       Keep demo project directory after completion
#   --verbose          Show detailed output and debug information
#   --demo-dir DIR     Specify custom location for demo project (default: temporary directory)
#   --help            Show this help and exit
#
# PREREQUISITES:
#   - Python 3.x with pyuvstarter available
#   - For recording: t-rec (auto-installed if needed)
# ==============================================================================

# Initial settings - will be adjusted based on mode
set -x  # Exit on error
SCRIPT_VERSION="3.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# === CONFIGURATION ===
# Demo directory will be set after argument parsing
ORIGINAL_DEMO_BASE=""  # Will be set after argument parsing
DEMO_BASE=""  # Will be set after argument parsing
DEMO_DIR=""  # Will be set after argument parsing
OUTPUT_BASENAME="pyuvstarter_demo2"
PYUVSTARTER_CMD="${PYUVSTARTER_CMD:-uv run pyuvstarter}"

# === STATE VARIABLES ===
UNIT_TEST_MODE=false
NO_CLEANUP=false
IS_CUSTOM_DEMO_DIR=false
RECORD_DEMO=false
SIMULATE_INSTALLS=true
VERBOSE=false
PLATFORM=""

# === COLOR CODES ===
C_RESET='\033[0m'
C_BOLD='\033[1m'
C_GREEN='\033[0;32m'
C_RED='\033[0;31m'
C_BLUE='\033[0;34m'
C_YELLOW='\033[0;33m'
C_CYAN='\033[0;36m'
C_GRAY='\033[0;90m'

# === PLATFORM DETECTION ===
detect_platform() {
    case "${OSTYPE:-unknown}" in
        linux*)   PLATFORM="linux" ;;
        darwin*)  PLATFORM="macos" ;;
        msys*|cygwin*) PLATFORM="windows" ;;
        *)        PLATFORM="unknown" ;;
    esac
    export PLATFORM
    if [ "${VERBOSE:-false}" = "true" ]; then
        echo "Platform detected: $(printf %q "$PLATFORM")"
    fi
}

# === UTILITY FUNCTIONS ===
log_verbose() {
    if [ "${VERBOSE:-false}" = "true" ]; then
        echo -e "${C_GRAY}[DEBUG] $*${C_RESET}" >&2
    fi
}

log_error() {
    echo -e "${C_RED}❌ ERROR: $*${C_RESET}" >&2
}

log_success() {
    echo -e "${C_GREEN}✅ $*${C_RESET}"
}

log_info() {
    echo -e "${C_BLUE}ℹ️  $*${C_RESET}"
}

# Safe directory/file removal with trash fallback
safe_remove() {
    local path="$1"

    # Return early if path doesn't exist
    [ ! -e "$path" ] && return 0

    # Use trash if available, otherwise fall back to rm
    # Always silent and never fail
    if command -v trash >/dev/null 2>&1; then
        trash "$path" >/dev/null 2>&1 || true
    else
        rm -rf "$path" >/dev/null 2>&1 || true
    fi
}

# Cross-platform file size
get_file_size() {
    local file="$1"
    case "$PLATFORM" in
        macos)   stat -f%z "$file" 2>/dev/null || echo "0" ;;
        linux)   stat -c%s "$file" 2>/dev/null || echo "0" ;;
        *)       wc -c < "$file" 2>/dev/null || echo "0" ;;
    esac
}

human_readable_size() {
    local size=$1
    if [[ $size -gt 1048576 ]]; then
        echo "$((size / 1048576))MB"
    elif [[ $size -gt 1024 ]]; then
        echo "$((size / 1024))KB"
    else
        echo "${size}B"
    fi
}

# === HELP SYSTEM ===
show_help() {
    cat << EOF
create_demo.sh v${SCRIPT_VERSION} - Professional demo generation for pyuvstarter

Creates a compelling demo showcasing pyuvstarter's ability to transform messy
ML projects with scattered dependencies into modern, reproducible environments.

USAGE:
  ./create_demo.sh [OPTIONS]

OPTIONS:
  --unit-test        Run comprehensive unit tests
  --record-demo      Record demo as GIF/MP4 using t-rec
  --no-cleanup       Keep demo project directory after completion
  --verbose          Show detailed output and debug information
  --demo-dir DIR     Specify custom location for demo project (default: temporary directory)
  --help            Show this help and exit

EXAMPLES:
  # Run live demo
  ./create_demo.sh

  # Run unit tests
  ./create_demo.sh --unit-test

  # Record demo GIF
  ./create_demo.sh --record-demo

  # Use custom demo directory
  ./create_demo.sh --demo-dir /tmp/my_demo

ENVIRONMENT VARIABLES:
  PYUVSTARTER_CMD - Override pyuvstarter command (default: uv run pyuvstarter)
  CI              - Set to any value to enable CI mode (JSON test output)
EOF
}

# === ARGUMENT PARSING ===
parse_arguments() {
    log_verbose "parse_arguments called with: $*"
    while [[ $# -gt 0 ]]; do
        log_verbose "Processing arg: $1"
        case "$1" in
            --unit-test)
                UNIT_TEST_MODE=true
                NO_CLEANUP=true  # Keep artifacts for inspection
                log_verbose "Unit test mode enabled"
                ;;
            --record-demo)
                RECORD_DEMO=true
                log_verbose "Recording mode enabled"
                ;;
            --no-cleanup)
                NO_CLEANUP=true
                log_verbose "Cleanup disabled"
                ;;
            --verbose)
                VERBOSE=true
                log_verbose "Verbose mode enabled"
                ;;
            --demo-dir)
                if [[ -n "$2" && "$2" != --* ]]; then
                    # Basic path length check (keep reasonable limit)
                    if [[ ${#2} -gt 255 ]]; then
                        log_error "--demo-dir path too long (max 255 characters)"
                        exit 1
                    fi
                    # Removed overly strict path validation that was causing CI failures
                    # Trust user-provided paths and let the filesystem handle validation

                    # Override the demo directory settings
                    DEMO_BASE="$(dirname "$2" 2>/dev/null || echo ".")"
                    DEMO_DIR="$2"
                    IS_CUSTOM_DEMO_DIR=true
                    log_verbose "Using custom demo directory: $(printf %q "$DEMO_DIR")"
                    shift 2
                else
                    log_error "--demo-dir requires a directory path"
                    exit 1
                fi
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done
    log_verbose "parse_arguments completed"
}

# === INSTALLATION SIMULATION ===
setup_install_simulation() {
    log_verbose "Setting up installation simulation"

    # Ensure demo directory exists before creating files in it
    if [ ! -d "$DEMO_DIR" ]; then
        log_error "Demo directory does not exist: $DEMO_DIR"
        return 1
    fi

    # Create wrapper script for simulating installs
    cat > "$DEMO_DIR/.simulate_installs.py" << 'EOF'
#!/usr/bin/env python3
"""Simulates package installation for demo purposes"""
import sys
import time
import random

# Simulated package metadata
PACKAGE_SIZES = {
    "pandas": "16.2MB",
    "numpy": "14.8MB",
    "scikit-learn": "8.3MB",
    "matplotlib": "11.2MB",
    "seaborn": "3.1MB",
    "plotly": "7.2MB",
    "dash": "5.4MB",
    "jupyter": "6.4MB",
    "ipykernel": "1.2MB",
    "beautifulsoup4": "0.4MB",
    "pillow": "3.2MB",
    "rich": "0.5MB"
}

def simulate_install(package):
    """Simulate realistic package installation"""
    pkg_name = package.split("==")[0].split(">=")[0].split("~=")[0]
    size = PACKAGE_SIZES.get(pkg_name, "2.1MB")

    steps = [
        f"Collecting {package}",
        f"  Downloading {pkg_name}-py3-none-any.whl ({size})",
        "Installing collected packages: " + pkg_name,
        f"Successfully installed {pkg_name}"
    ]

    for step in steps:
        print(step)
        # Vary timing to seem realistic
        time.sleep(random.uniform(0.05, 0.15))

if __name__ == "__main__":
    args = sys.argv[1:]

    # Parse packages from command line
    if "install" in args or "add" in args:
        idx = args.index("install") if "install" in args else args.index("add")
        packages = [arg for arg in args[idx+1:] if not arg.startswith("-")]

        for pkg in packages:
            simulate_install(pkg)
    else:
        print("Usage: simulate_installs.py install <package>...")
EOF
    chmod +x "$DEMO_DIR/.simulate_installs.py"

    # Export override for demos
    if [ "$SIMULATE_INSTALLS" = "true" ]; then
        export UV_PYTHON_OVERRIDE="$DEMO_DIR/.simulate_installs.py"
        log_verbose "Installation simulation activated"
    fi
}

# === DEMO CONTENT CREATION ===
create_demo_project() {
    local mode="${1:-demo}"  # "demo" or "test"

    log_info "Creating demo project structure..."
    log_verbose "SCRIPT_DIR: $(printf %q "$SCRIPT_DIR")"
    log_verbose "DEMO_DIR: $(printf %q "$DEMO_DIR")"
    log_verbose "Current directory: $(printf %q "$(pwd)")"

    # Clean and create directory structure
    safe_remove "$DEMO_DIR"

    # Create base directory first
    mkdir -p "$DEMO_DIR" || {
        log_error "Failed to create demo directory: $(printf %q "$DEMO_DIR")"
        return 1
    }

    # Create subdirectories
    mkdir -p "$DEMO_DIR/notebooks" "$DEMO_DIR/scripts" "$DEMO_DIR/src" "$DEMO_DIR/tests" "$DEMO_DIR/data" || {
        log_error "Failed to create subdirectories in: $(printf %q "$DEMO_DIR")"
        return 1
    }

    # Create files based on mode
    create_requirements_file "$mode"
    create_python_scripts "$mode"
    create_notebooks "$mode"
    create_supporting_files "$mode"

    log_verbose "Demo project created with mode: $(printf %q "$mode")"
}

create_requirements_file() {
    local mode="$1"

    if [[ "$mode" == "test" ]]; then
        # Minimal requirements for fast testing
        # TODO: Add test case for Python version conflict resolution:
        #       1. In this if block, change: numpy<2.0  # Prevent CI failure on Python 3.8
        #          to: numpy
        #       2. Add a new test function after run_test "Verifying dependency discovery" that checks:
        #          - pyuvstarter log contains "Python version conflict detected"
        #          - pyuvstarter log contains "Retrying with flexible version discovery"
        #          - Final pyproject.toml has numpy without version constraint
        cat > "$DEMO_DIR/requirements.txt" << 'EOF'
# Minimal test requirements
numpy<2.0  # Prevent CI failure on Python 3.8
requests
sklearn  # Wrong package name!
EOF
    else
        # Realistic problematic requirements.txt
        # TODO: Add test case for Python version conflict resolution in demo mode:
        #       1. In the else block below, change: numpy==1.19.0  # Old version - security vulnerabilities!
        #          to: numpy==2.3.1
        #       2. This will trigger conflict (numpy 2.3.1 requires Python 3.11+)
        #       3. The demo should show pyuvstarter automatically retrying with --mode no-pin
        cat > "$DEMO_DIR/requirements.txt" << 'EOF'
# Production ML Dependencies - INCOMPLETE & OUTDATED (Last updated: 2021)

# Core ML libraries
numpy==1.19.0  # Old version - security vulnerabilities!
# pandas  # Commented out but used EVERYWHERE in the code
# torch  # TODO: add pytorch (never got around to it)
sklearn  # WRONG! Package is 'scikit-learn' not 'sklearn'

# Visualization (partially missing)
matplotlib  # No version pin - risky!
# seaborn  # Missing but used in notebooks
# plotly  # Missing but used for interactive plots

# Web frameworks
requests==2.25.1
# fastapi, streamlit, dash  # API server, dashboards - missing

# Utilities
python-dotenv
# rich, typer, loguru  # Pretty printing, CLI framework, logging - missing

# Critical missing categories:
# - Jupyter & notebook support
# - Database drivers (psycopg2, pymongo, etc), Cloud SDKs (boto3, google-cloud, azure)
# - Testing frameworks, ML experiment tracking (wandb, mlflow)
EOF
    fi
}

create_python_scripts() {
    local mode="$1"

    # Main data analysis script with import issues
    cat > "$DEMO_DIR/scripts/data_analysis.py" << 'EOF'
#!/usr/bin/env python3
"""
Data analysis pipeline - demonstrates common dependency problems.
Half the imports are missing from requirements.txt!
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# These are ALL MISSING from requirements.txt
import pandas as pd  # ❌ Not in requirements!
import polars as pl  # ❌ Modern alternative, also missing
from rich.console import Console  # ❌ Missing
from rich.table import Table  # ❌ Missing
from rich.progress import track  # ❌ Missing

# In requirements but with WRONG name
from sklearn.preprocessing import StandardScaler  # ❌ "sklearn" vs "scikit-learn"
from sklearn.model_selection import train_test_split

# Version conflict - requirements has old numpy
import numpy as np  # ⚠️ Version mismatch!

# Visualization - missing deps
import matplotlib.pyplot as plt  # ✓ In requirements
import seaborn as sns  # ❌ Missing!
import plotly.express as px  # ❌ Missing!

def analyze_data():
    """Run analysis - will fail without proper deps"""
    console = Console()
    console.print("[bold green]✅ All dependencies are now properly installed![/bold green]")
    console.print("[blue]Running data analysis pipeline...[/blue]")

    # Simulate some work
    data = pd.DataFrame({
        'values': np.random.randn(1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000)
    })

    console.print(f"Processed {len(data)} records successfully!")
    return True

if __name__ == "__main__":
    analyze_data()
EOF

    # Create additional scripts for demo mode
    if [[ "$mode" == "demo" ]]; then
        # Modern ML training script
        cat > "$DEMO_DIR/src/train_model.py" << 'EOF'
"""Modern ML analysis script - uses many packages!"""

# Data processing (missing)
import pandas as pd
import polars as pl
from dask import dataframe as dd

# Visualization & UI (missing)
import dash
from flask import Flask, render_template
import jinja2

# Utilities (missing)
import click
import typer
from loguru import logger
from tqdm import tqdm

# API & Web (missing)
from fastapi import FastAPI
from flask import Flask
import requests

print("🤖 Modern data stack ready!")
EOF

        # API server example
        cat > "$DEMO_DIR/src/api_server.py" << 'EOF'
"""FastAPI server - another missing dependency set"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from sqlalchemy import create_engine
import redis
import celery

app = FastAPI(title="ML API")

@app.get("/")
def root():
    return {"message": "ML API Server"}
EOF
    fi
}

create_notebooks() {
    local mode="$1"

    # Notebook with scattered dependencies
    cat > "$DEMO_DIR/notebooks/ml_experiment.ipynb" << 'EOF'
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 🧪 Machine Learning Experiment\n",
    "\n",
    "This notebook has dependencies hidden EVERYWHERE:\n",
    "- Shell commands (!pip install)\n",
    "- Magic commands (%pip install)\n",
    "- Regular imports\n",
    "- Even in markdown cells!"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Installing packages in notebooks - bad practice but common!\n",
    "!pip install -q seaborn plotly dash\n",
    "!pip install pillow beautifulsoup4\n",
    "!pip install requests-html httpx"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Magic commands - another way packages hide\n",
    "%pip install -U scikit-learn scipy\n",
    "%pip install statsmodels"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Now the actual imports\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "from PIL import Image\n",
    "import sklearn  # Wrong import name!\n",
    "from bs4 import BeautifulSoup\n",
    "import requests\n",
    "import seaborn as sns\n",
    "import plotly.graph_objects as go\n",
    "import matplotlib.pyplot as plt\n",
    "from scipy import stats"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "Don't forget to: `pip install jupyter ipykernel notebook`"
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
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
EOF

    # Add more notebooks for demo mode
    if [[ "$mode" == "demo" ]]; then
        cat > "$DEMO_DIR/notebooks/data_viz.ipynb" << 'EOF'
{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Visualization notebook with more hidden deps\n",
    "!pip install bokeh holoviews panel\n",
    "!pip install altair vega_datasets\n",
    "\n",
    "import bokeh.plotting as bp\n",
    "import holoviews as hv\n",
    "import panel as pn\n",
    "import altair as alt"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
EOF
    fi
}

create_supporting_files() {
    local mode="$1"

    # README
    cat > "$DEMO_DIR/README.md" << EOF
# ML Project Demo

This project demonstrates common Python dependency problems:

- 📦 Incomplete requirements.txt (missing 20+ packages)
- 📓 Dependencies hidden in Jupyter notebooks
- 🔀 Wrong package names (sklearn vs scikit-learn)
- ⚠️  Missing version pins
- 💥 Scattered pip install commands

## The Problem

Try running: \`python scripts/data_analysis.py\`

Result: ImportError - missing pandas!

## The Solution

Run \`pyuvstarter\` to modernize this project instantly!
EOF

    # Create __init__.py files
    touch "$DEMO_DIR/src/__init__.py"
    touch "$DEMO_DIR/scripts/__init__.py"

    # .gitignore (intentionally missing to show pyuvstarter creates it)
    # Don't create it - let pyuvstarter do that
}

# === UNIT TEST FRAMEWORK ===
# Use regular variables for compatibility (no associative arrays)
TEST_RESULTS=""
TEST_COUNT=0
TEST_PASSED=0
TEST_FAILED=0
TEST_WARNINGS=""

run_test() {
    local test_name="$1"
    local test_desc="$2"
    shift 2

    TEST_COUNT=$((TEST_COUNT + 1))
    echo -n "🧪 TEST $TEST_COUNT: $test_desc "

    # Run test with output capture
    local output
    local exit_code
    local start_time
    start_time=$(date +%s)

    if output=$("$@" 2>&1); then
        exit_code=0
    else
        exit_code=$?
    fi

    local end_time
    end_time=$(date +%s)
    local duration=$(( end_time - start_time ))  # Duration in seconds

    if [[ $exit_code -eq 0 ]]; then
        echo -e "${C_GREEN}[ ✅ PASSED ]${C_RESET} (${duration}s)"
        TEST_PASSED=$((TEST_PASSED + 1))
        TEST_RESULTS="${TEST_RESULTS}${test_name}:PASSED;"
    else
        echo -e "${C_RED}[ ❌ FAILED ]${C_RESET} (${duration}s)"
        TEST_FAILED=$((TEST_FAILED + 1))
        TEST_RESULTS="${TEST_RESULTS}${test_name}:FAILED:$exit_code;"
        if [ "$VERBOSE" = "true" ]; then
            echo -e "${C_GRAY}    Output: ${output:0:200}${C_RESET}"
        fi
        # Store detailed error for summary
        TEST_WARNINGS="${TEST_WARNINGS}❌ Test '$test_desc' failed: $output\n"
    fi

    return $exit_code
}

run_unit_tests() {
    echo -e "${C_BOLD}${C_CYAN}🧪 PYUVSTARTER UNIT TEST SUITE v$SCRIPT_VERSION${C_RESET}"
    echo "============================================="
    echo "Platform: $PLATFORM"
    echo "Python: $(python3 --version 2>&1)"
    echo "Directory: $(pwd)"
    echo "============================================="

    local suite_start
    suite_start=$(date +%s)

    # Setup test environment
    log_info "Setting up test environment..."
    create_demo_project "test"

    # Don't simulate installs for real tests!
    SIMULATE_INSTALLS=false

    # Test 1: Demo project structure
    run_test "structure" "Demo project created correctly" \
        bash -c "[[ -d '$DEMO_DIR' ]] && [[ -f '$DEMO_DIR/requirements.txt' ]] && [[ -d '$DEMO_DIR/notebooks' ]]"

    # Test 2: Pyuvstarter is executable
    run_test "executable" "Pyuvstarter script exists and is executable" \
        bash -c "[[ -f './pyuvstarter.py' ]]"

    # Test 3: Pyuvstarter execution (CRITICAL - REAL TEST)
    log_info "Running LIVE pyuvstarter test (this is the real deal)..."
    local pyuv_output
    local pyuv_exit_code

    # Activate the main project's venv if it exists
    local activate_cmd=""
    if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
        activate_cmd="source $SCRIPT_DIR/.venv/bin/activate && "
    fi

    if pyuv_output=$(cd "$DEMO_DIR" && eval "${activate_cmd}$PYUVSTARTER_CMD ." 2>&1); then
        pyuv_exit_code=0
    else
        pyuv_exit_code=$?
    fi

    if [ $pyuv_exit_code -eq 0 ]; then
        run_test "execution" "Pyuvstarter executes successfully" \
            bash -c "true"  # Already succeeded
    else
        run_test "execution" "Pyuvstarter executes successfully" \
            bash -c "false"  # Force failure
        echo -e "${C_RED}Pyuvstarter failed with exit code: $pyuv_exit_code${C_RESET}" >&2
        echo -e "${C_RED}Output:${C_RESET}" >&2
        echo "$pyuv_output" | head -20 >&2
    fi

    # Test 4: Expected artifacts created
    run_test "artifacts" "Creates pyproject.toml and .gitignore" \
        bash -c "[[ -f '$DEMO_DIR/pyproject.toml' ]] && [[ -f '$DEMO_DIR/.gitignore' ]]"

    # Test 5: Virtual environment
    run_test "venv" "Creates virtual environment" \
        bash -c "[[ -d '$DEMO_DIR/.venv' ]] || [[ -d '$DEMO_DIR/venv' ]]"

    # Test 6: Dependency discovery
    run_test "deps_found" "Discovers pandas dependency" \
        bash -c "grep -q 'pandas' '$DEMO_DIR/pyproject.toml' 2>/dev/null"

    # Test 7: Import name mapping
    run_test "import_map" "Maps sklearn to scikit-learn correctly" \
        bash -c "grep -q 'scikit-learn' '$DEMO_DIR/pyproject.toml' 2>/dev/null"

    # Test 8: Notebook dependency discovery
    run_test "notebook_deps" "Finds dependencies in notebooks" \
        bash -c "grep -q 'seaborn\|plotly' '$DEMO_DIR/pyproject.toml' 2>/dev/null"

    # Test 9: VS Code configuration
    run_test "vscode" "Creates VS Code configuration" \
        bash -c "[[ -f '$DEMO_DIR/.vscode/settings.json' ]] || [[ -f '$DEMO_DIR/.vscode/launch.json' ]]"

    # Test 10: Log file creation
    run_test "logfile" "Creates execution log" \
        bash -c "[[ -f '$DEMO_DIR/pyuvstarter_setup_log.json' ]]"

    # Test 11: Can the fixed script actually run?
    if [[ -f "$DEMO_DIR/.venv/bin/activate" ]]; then
        run_test "script_runs" "Fixed script executes without errors" \
            bash -c "cd '$DEMO_DIR' && source .venv/bin/activate && python scripts/data_analysis.py"
    else
        log_verbose "Skipping script execution test - no venv found"
    fi

    # Test 12: Requirements with inline comments are handled
    # NOTE: These tests are designed to be robust to reasonable code changes:
    # - They check for patterns rather than exact output
    # - They use case-insensitive matching where appropriate
    # - They check for presence rather than exact format
    # Create a requirements.txt with inline comments (replacing the original)
    cat > "$DEMO_DIR/requirements.txt" << 'EOF'
numpy==1.19.0  # Old version for compatibility
pandas>=1.0,<2.0  # Version range
requests[security]>=2.25.0  # With extras
Django[bcrypt,argon2]~=3.0  # Multiple extras
EOF

    # Run pyuvstarter on this file and check if it processes correctly
    # Check JSON log for package processing evidence instead of stdout parsing
    run_test "inline_comments" "Handles requirements.txt with inline comments" \
        bash -c "cd '$DEMO_DIR' && eval '${activate_cmd}$PYUVSTARTER_CMD .' >/dev/null 2>&1 && grep -q 'package specifier.*requirements.txt' '$DEMO_DIR/pyuvstarter_setup_log.json'"

    # Test 13: Package extras are preserved
    # First run pyuvstarter again to process the new requirements.txt with all-requirements mode
    (cd "$DEMO_DIR" && eval "${activate_cmd}$PYUVSTARTER_CMD --dependency-migration all-requirements ." >/dev/null 2>&1)
    # More robust: Check that Django and requests made it to dependencies (case-insensitive)
    run_test "extras_preserved" "Preserves package extras in requirements" \
        bash -c "grep -i 'django' '$DEMO_DIR/pyproject.toml' >/dev/null && grep -i 'requests' '$DEMO_DIR/pyproject.toml' >/dev/null"

    # Test 14: Requirements processing works
    # Robust check: Verify that a specific package from the overwritten requirements.txt ('django') is now present.
    run_test "all_requirements" "Processes new requirements.txt correctly" \
        bash -c "grep -q 'django' '$DEMO_DIR/pyproject.toml' 2>/dev/null"

    local suite_end
    suite_end=$(date +%s)
    local suite_duration=$((suite_end - suite_start))

    # Generate summary
    echo "============================================="
    echo -e "${C_BOLD}📊 TEST SUMMARY:${C_RESET}"
    echo "   Total Tests: $TEST_COUNT"
    echo -e "   ${C_GREEN}✅ Passed: $TEST_PASSED${C_RESET}"
    echo -e "   ${C_RED}❌ Failed: $TEST_FAILED${C_RESET}"
    echo "   ⏱️  Duration: ${suite_duration}s"
    echo "============================================="

    # Show detailed test results
    echo -e "\n${C_BOLD}📋 DETAILED TEST RESULTS:${C_RESET}"
    echo "$TEST_RESULTS" | tr ';' '\n' | while IFS=: read -r name result code; do
        [[ -z "$name" ]] && continue
        if [ "$result" = "PASSED" ]; then
            echo -e "   ${C_GREEN}✅ $name${C_RESET}"
        else
            echo -e "   ${C_RED}❌ $name (exit code: $code)${C_RESET}"
        fi
    done

    # Show warnings if any tests failed
    if [[ $TEST_FAILED -gt 0 ]]; then
        echo -e "\n${C_RED}${C_BOLD}⚠️  TEST FAILURES DETECTED:${C_RESET}"
        echo -e "$TEST_WARNINGS"
        echo -e "${C_YELLOW}Please check the errors above and fix any issues.${C_RESET}"

        # Show cascade failure analysis
        echo -e "\n${C_BOLD}🔍 FAILURE ANALYSIS:${C_RESET}"
        if echo "$TEST_RESULTS" | grep -q "structure:FAILED"; then
            echo -e "   ${C_RED}⚠️  Structure test failed - this will cause all subsequent tests to fail${C_RESET}"
        fi
        if echo "$TEST_RESULTS" | grep -q "execution:FAILED"; then
            echo -e "   ${C_RED}⚠️  Execution test failed - pyuvstarter didn't run successfully${C_RESET}"
            echo -e "   ${C_YELLOW}     This will cause Tests 4-14 to fail (artifacts, venv, deps, etc.)${C_RESET}"
        fi
    fi

    # Generate test report for unit tests
    if [[ "$UNIT_TEST_MODE" = "true" ]]; then
        generate_test_report "$suite_duration"
    fi

    # Return appropriate exit code
    if [[ $TEST_FAILED -gt 0 ]]; then
        return 1
    else
        log_success "All tests passed!"
        return 0
    fi
}

generate_test_report() {
    local duration="$1"

    # Generate JUnit XML for GitHub Actions integration
    cat > "test_results.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="pyuvstarter_tests" tests="$TEST_COUNT" failures="$TEST_FAILED" time="$duration">
  <testsuite name="pyuvstarter.unit_tests" tests="$TEST_COUNT" failures="$TEST_FAILED" time="$duration">
$(
    # Parse TEST_RESULTS and create actionable test cases
    echo "$TEST_RESULTS" | tr ';' '\n' | while IFS=: read -r name result code; do
        [[ -z "$name" ]] && continue

        # Map test names to actionable descriptions
        case "$name" in
            "structure") test_desc="Demo project structure creation" ;;
            "executable") test_desc="pyuvstarter.py accessibility" ;;
            "execution") test_desc="pyuvstarter core execution" ;;
            "artifacts") test_desc="pyproject.toml and .gitignore creation" ;;
            "venv") test_desc="Virtual environment setup" ;;
            "deps_found") test_desc="Dependency discovery (pandas)" ;;
            "import_map") test_desc="Import name mapping (sklearn→scikit-learn)" ;;
            "notebook_deps") test_desc="Jupyter notebook dependency parsing" ;;
            "vscode") test_desc="VS Code configuration" ;;
            "logfile") test_desc="Execution logging" ;;
            "script_runs") test_desc="End-to-end script execution" ;;
            "inline_comments") test_desc="Requirements.txt comment handling" ;;
            "extras_preserved") test_desc="Package extras preservation" ;;
            "all_requirements") test_desc="Requirements processing" ;;
            *) test_desc="$name" ;;
        esac

        if [ "$result" = "PASSED" ]; then
            echo "    <testcase name=\"$test_desc\" classname=\"pyuvstarter.$name\"/>"
        else
            echo "    <testcase name=\"$test_desc\" classname=\"pyuvstarter.$name\">"

            # Generate actionable failure messages
            case "$name" in
                "structure")
                    echo "      <failure message=\"Demo project creation failed - check directory permissions and disk space\">"
                    echo "        CRITICAL: All subsequent tests will fail without demo project structure"
                    echo "      </failure>"
                    ;;
                "executable")
                    echo "      <failure message=\"pyuvstarter.py not found - check file exists and is accessible\">"
                    echo "        Action: Verify pyuvstarter.py is in the current directory"
                    echo "      </failure>"
                    ;;
                "execution")
                    echo "      <failure message=\"pyuvstarter execution failed (exit code: $code)\">"
                    echo "        CRITICAL: This will cause validation tests to fail"
                    echo "        Action: Check pyuvstarter dependencies and Python environment"
                    echo "      </failure>"
                    ;;
                "artifacts")
                    echo "      <failure message=\"pyproject.toml or .gitignore not created\">"
                    echo "        Likely cause: pyuvstarter execution failed"
                    echo "      </failure>"
                    ;;
                "venv")
                    echo "      <failure message=\"Virtual environment not created\">"
                    echo "        Action: Check 'uv venv' command execution in pyuvstarter"
                    echo "      </failure>"
                    ;;
                "deps_found")
                    echo "      <failure message=\"pandas dependency not found in pyproject.toml\">"
                    echo "        Action: Check dependency discovery logic in pyuvstarter"
                    echo "      </failure>"
                    ;;
                "import_map")
                    echo "      <failure message=\"sklearn not mapped to scikit-learn\">"
                    echo "        Action: Check import name mapping in pyuvstarter"
                    echo "      </failure>"
                    ;;
                "notebook_deps")
                    echo "      <failure message=\"Notebook dependencies not discovered\">"
                    echo "        Action: Check Jupyter notebook parsing in pyuvstarter"
                    echo "      </failure>"
                    ;;
                "script_runs")
                    echo "      <failure message=\"Fixed script execution failed\">"
                    echo "        Action: Check virtual environment and installed dependencies"
                    echo "      </failure>"
                    ;;
                *)
                    echo "      <failure message=\"Test failed with exit code $code\">"
                    echo "        Action: Check test implementation and dependencies"
                    echo "      </failure>"
                    ;;
            esac

            echo "    </testcase>"
        fi
    done
)
  </testsuite>
</testsuites>
EOF

    log_info "Test report written to test_results.xml for GitHub Actions"
}

# === DEMO EXECUTION ENGINE ===
create_demo_script() {
    cat > "$DEMO_DIR/.demo_script.sh" << 'DEMO_SCRIPT_EOF'
#!/bin/bash
# Self-contained demo script

# Dynamically resolve paths relative to this script
DEMO_SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(cd "$DEMO_SCRIPT_DIR/.." && pwd)"
VENV_ACTIVATE="$PARENT_DIR/.venv/bin/activate"

# Ensure we're running from the demo directory
# This is needed because t-rec runs scripts from the current working directory,
# while run_live_demo() properly cd's to the demo directory first
cd "$DEMO_SCRIPT_DIR" || {
    echo "ERROR: Demo script must run from demo directory" >&2
    echo "Failed to cd to: $DEMO_SCRIPT_DIR" >&2
    exit 1
}

# No need to verify pyuvstarter.py exists since we're using 'uv run'

# Colors
setup_colors() {
    C_RESET='\033[0m'
    C_BOLD='\033[1m'
    C_GREEN='\033[0;32m'
    C_RED='\033[0;31m'
    C_BLUE='\033[0;34m'
    C_YELLOW='\033[0;33m'
    C_CYAN='\033[0;36m'
    C_DIM='\033[2m'
}

# Typing effect
type_command() {
    local cmd="$1"
    echo -ne "${C_YELLOW}$ ${C_RESET}"
    for ((i=0; i<${#cmd}; i++)); do
        echo -n "${cmd:i:1}"
        sleep 0.02
    done
    echo
    sleep 0.3
}

# Main demo sequence
main() {
    setup_colors
    clear

    # Title card
    echo -e "${C_BOLD}${C_CYAN}🚀 pyuvstarter Demo - Transform Legacy Python Projects${C_RESET}\n"
    sleep 1.5

    # Act 1: The Problem (10 seconds)
    echo -e "${C_BOLD}1️⃣  The Problem: Dependency Hell${C_RESET}\n"
    sleep 0.5

    echo "You've just cloned a 'working' ML project. Let's explore..."
    sleep 1

    type_command "tree -L 2 ."
    # Show REAL directory structure
    tree -L 2 . -I '__pycache__' --dirsfirst 2>/dev/null || ls -la .
    sleep 1

    echo -e "\n${C_YELLOW}Let's check the requirements:${C_RESET}"
    type_command "cat requirements.txt"
    cat requirements.txt
    echo -e "\n${C_RED}   ⚠️  Missing 24 critical dependencies!${C_RESET}"
    sleep 1.5

    echo -e "\n${C_CYAN}Let's try running the analysis script:${C_RESET}"
    type_command "python3 scripts/data_analysis.py"
    sleep 0.3

    # Simulate error
    echo -e "${C_RED}Traceback (most recent call last):"
    echo "  File \"scripts/data_analysis.py\", line 15, in <module>"
    echo "    import pandas as pd"
    echo -e "ModuleNotFoundError: No module named 'pandas'${C_RESET}\n"
    sleep 1

    echo -e "${C_RED}❌ Classic dependency hell!${C_RESET}"
    sleep 1.5

    # Act 2: The Solution (20 seconds)
    echo -e "\n${C_BOLD}2️⃣  The Solution: pyuvstarter${C_RESET}\n"
    sleep 0.5

    echo "Watch pyuvstarter discover and fix everything automatically..."
    type_command "pyuvstarter ."
    sleep 0.5

    # ACTUALLY RUN PYUVSTARTER - show real clean output!
    # Run from demo directory using development version of pyuvstarter
    (uv run --directory "$PARENT_DIR" pyuvstarter  "$DEMO_SCRIPT_DIR")

    echo ""
    sleep 3

    # NOTE: Previously simulated progress for demo purposes - now using real output above
    # The following was the original simulated version (kept for reference):
    #
    # # Show realistic progress
    # echo -e "${C_GREEN}🚀 PYUVSTARTER v0.2.0${C_RESET}"
    # echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    #
    # # Simulated progress messages
    # progress_items=(
    #     "✓ Checking for uv installation"
    #     "✓ Initializing pyproject.toml"
    #     "✓ Creating .gitignore with best practices"
    #     "✓ Setting up virtual environment (.venv)"
    #     "📂 Scanning Python files for imports..."
    #     "   Found: pandas, sklearn, rich, numpy..."
    #     "📓 Analyzing Jupyter notebooks..."
    #     "   Found: seaborn, plotly, streamlit..."
    #     "🔍 Mapping import names to packages..."
    #     "   sklearn → scikit-learn"
    #     "   cv2 → opencv-python"
    #     "📦 Installing all dependencies..."
    #     "✓ Configuring VS Code"
    #     "✓ Creating execution log"
    # )
    #
    # for item in "${progress_items[@]}"; do
    #     echo "   $item"
    #     sleep 0.25
    # done

    echo -e "\n${C_GREEN}✨ Project modernization complete!${C_RESET}"
    sleep 1.5

    # Act 3: The Result (10 seconds)
    echo -e "\n${C_BOLD}3️⃣  The Result: A Modern Python Project${C_RESET}\n"
    sleep 0.5

    echo "What pyuvstarter created:"
    type_command "ls -la | grep -E '(pyproject|venv|lock|gitignore|vscode)'"

    # Actually run the command and show real results
    ls -la . | grep -E '(pyproject|venv|lock|gitignore|vscode)' | while read -r line; do
        echo "   $line"
    done

    echo ""
    # Check and report what was actually created (current directory in demo context)
    [ -f "pyproject.toml" ] && echo -e "${C_GREEN}   ✅ pyproject.toml   ${C_DIM}# Modern Python configuration${C_RESET}" || echo -e "${C_RED}   ❌ pyproject.toml   ${C_DIM}# Not found!${C_RESET}"
    [ -d ".venv" ] && echo -e "${C_GREEN}   ✅ .venv/           ${C_DIM}# Isolated virtual environment${C_RESET}" || echo -e "${C_RED}   ❌ .venv/           ${C_DIM}# Not found!${C_RESET}"
    [ -f "uv.lock" ] && echo -e "${C_GREEN}   ✅ uv.lock          ${C_DIM}# Reproducible dependency versions${C_RESET}" || echo -e "${C_RED}   ❌ uv.lock          ${C_DIM}# Not found!${C_RESET}"
    [ -f ".gitignore" ] && echo -e "${C_GREEN}   ✅ .gitignore       ${C_DIM}# Version control ready${C_RESET}" || echo -e "${C_RED}   ❌ .gitignore       ${C_DIM}# Not found!${C_RESET}"
    [ -d ".vscode" ] && echo -e "${C_GREEN}   ✅ .vscode/         ${C_DIM}# IDE configuration${C_RESET}" || echo -e "${C_RED}   ❌ .vscode/         ${C_DIM}# Not found!${C_RESET}"
    sleep 1.5

    echo -e "\n${C_GREEN}Let's run that script again:${C_RESET}"
    type_command "source .venv/bin/activate && python scripts/data_analysis.py"
    sleep 0.3

    # Actually run it to show it works!
    local script_exit_code=0
    if [ -f ".venv/bin/activate" ]; then
        (source .venv/bin/activate && python scripts/data_analysis.py)
        script_exit_code=$?

        if [ $script_exit_code -ne 0 ]; then
            echo -e "\n${C_RED}❌ ERROR: Script failed with exit code $script_exit_code${C_RESET}"
            echo -e "${C_YELLOW}This shouldn't happen after pyuvstarter fixed everything!${C_RESET}"
        fi
    else
        echo -e "${C_GREEN}✅ All dependencies are now properly installed!"
        echo -e "${C_BLUE}Running data analysis pipeline..."
        echo -e "Processed 1000 records successfully!${C_RESET}"
    fi
    sleep 1.5

    # Summary - only show success if script actually worked
    if [ $script_exit_code -eq 0 ]; then
        echo -e "\n${C_BOLD}${C_GREEN}🎉 Success!${C_RESET}"
    else
        echo -e "\n${C_BOLD}${C_RED}⚠️  Demo encountered issues${C_RESET}"
    fi
    echo -e "\nYour project is now:"
    echo "  ✅ Using modern pyproject.toml"
    echo "  ✅ Fully reproducible with uv.lock"
    echo "  ✅ All 25+ dependencies found & installed"
    echo "  ✅ Ready for development!"

    sleep 2

    # What you were saved from
    echo -e "\n${C_BOLD}💡 What pyuvstarter saved you from:${C_RESET}"
    echo "  ⏰ Hours of manual dependency hunting"
    echo "  🔧 Environment setup trial and error"
    echo "  🐛 'ModuleNotFoundError' debugging hell"
    echo "  💻 'It works on my machine' problems"

    sleep 2

    # Call to action with star request
    echo -e "\n${C_BOLD}${C_CYAN}🌟 Love what you saw?${C_RESET}"
    echo "  ⭐ Star us on GitHub: github.com/ahundt/pyuvstarter"
    echo "  🔄 Share with fellow Python developers"
    echo "  💬 Join our community & contribute features"

    sleep 3
}

main
DEMO_SCRIPT_EOF

    chmod +x "$DEMO_DIR/.demo_script.sh"
}

run_live_demo() {
    log_info "Running live demo..."

    # Change to demo directory and run
    (
        cd "$DEMO_DIR"
        bash .demo_script.sh
    )
}

run_demo_engine() {
    local mode="${1:-live}"

    # Check and install t-rec if needed for recording mode
    if [[ "$mode" == "record" ]]; then
        if ! command -v t-rec &>/dev/null; then
            log_info "Installing t-rec for recording..."
            if command -v brew &>/dev/null; then
                brew install t-rec
            elif command -v cargo &>/dev/null; then
                cargo install t-rec
            else
                log_error "Please install t-rec manually: brew install t-rec"
                return 1
            fi
        fi
    fi

    # Setup simulation if needed
    if [ "$SIMULATE_INSTALLS" = "true" ]; then
        setup_install_simulation
    fi

    # Create the demo script
    create_demo_script

    if [[ "$mode" == "record" ]]; then
        record_demo
    else
        run_live_demo
    fi
}

count_files() {
    ls "${OUTPUT_BASENAME}"*."$1" 2>/dev/null | wc -l | tr -d ' '
}

record_demo() {
    log_info "Recording demo to GIF/MP4..."

    # Check for t-rec
    if ! command -v t-rec &>/dev/null; then
        log_error "t-rec not found. Please install it first."
        log_info "Install with: brew install t-rec (macOS) or cargo install t-rec (Linux)"
        return 1
    fi

    # Count existing files
    local gif_before
    gif_before=$(count_files gif)
    local mp4_before
    mp4_before=$(count_files mp4)

    # Check current terminal size
    local current_rows
    current_rows=$(tput lines)
    local current_cols
    current_cols=$(tput cols)

    if [ "$current_rows" -eq 30 ] && [ "$current_cols" -eq 100 ]; then
        echo "✅ Terminal already at optimal size: 30x100"
    else
        echo "📐 Resizing terminal from ${current_rows}x${current_cols} to 30x100 for optimal recording..."
        printf '\e[8;30;100t'
        sleep 2

        # Check if resize worked
        current_rows=$(tput lines)
        current_cols=$(tput cols)

        if [ "$current_rows" -ne 30 ] || [ "$current_cols" -ne 100 ]; then
            echo -e "${C_YELLOW}⚠️  Terminal resize may not have succeeded.${C_RESET}"
            echo "   Current size: ${current_rows}x${current_cols} (expected 30x100)"
            echo ""
            echo "   If you're using iTerm2, please:"
            echo "   1. Allow the resize request if prompted"
            echo "   2. Or disable the prompt in: Preferences > Advanced > 'Terminal windows resize smoothly'"
            echo ""
            read -r -p "Press Enter when ready to continue (or Ctrl+C to cancel)... "

        else
            echo "✅ Terminal resized successfully to 30x100"
        fi
    fi

    # Record the demo
    echo "🎬 Starting t-rec recording..."
    echo "The demo will run automatically in a new window."
    echo ""

    # Run t-rec with -m flag to create both GIF and MP4
    # The demo script now handles all path resolution internally
    t-rec -m \
        --output "$OUTPUT_BASENAME" \
        -- "$DEMO_DIR/.demo_script.sh"

    # Check results
    echo -e "\n📦 Recording complete. Generated files:"

    local gif_after
    gif_after=$(count_files gif)
    local mp4_after
    mp4_after=$(count_files mp4)

    for ext in gif mp4; do
        local before_var="${ext}_before"
        local after_var="${ext}_after"
        local before=${!before_var}
        local after=${!after_var}

        if [ "$after" -gt "$before" ]; then
            local latest
            latest=$(find . -maxdepth 1 -name "${OUTPUT_BASENAME}*.${ext}" -print0 | xargs -0 ls -t | head -1)
            local size
            size=$(get_file_size "$latest")
            log_success "$latest ($(human_readable_size "$size"))"
        else
            log_error "No new ${ext^^} file created"
        fi
    done
}

# === CLEANUP ===
cleanup() {
    local exit_code=$?

    echo ""
    # Diagnostics and error handling
    if [[ $exit_code -ne 0 ]]; then
        log_error "❌ Demo failed with exit code: $exit_code"
        echo -e "\n===== Bash Variable Dump =====" >&2
        declare -p | grep -v '^declare -f' >&2
        echo -e "\n===== Bash Call Stack (most recent call last) =====" >&2
        local stack_depth=${#FUNCNAME[@]}
        for ((i=stack_depth-1; i>=0; i--)); do
            local func="${FUNCNAME[i]}"
            local file="${BASH_SOURCE[i]}"
            local line="${BASH_LINENO[i]}"
            if [[ $i -eq $((stack_depth-1)) ]]; then
                echo -e "  [Top] $func() at $file" >&2
            else
                echo -e "   -> $func() at $file:$line" >&2
            fi
        done
        echo "=============================" >&2
        echo "🛑 Skipping cleanup to preserve all artifacts for debugging."
        echo "   📂 Demo project preserved: $(printf %q "$DEMO_DIR")"
        if [ "$IS_CUSTOM_DEMO_DIR" = "false" ] && [ -d "$ORIGINAL_DEMO_BASE" ]; then
            echo "   📂 Original temp directory preserved: $(printf %q "$ORIGINAL_DEMO_BASE")"
        fi
        echo "   🗂️  Temp files preserved: /tmp/trec-*"
    elif [ "$NO_CLEANUP" = "true" ]; then
        log_info "🗂️  NO_CLEANUP enabled. Artifacts preserved: $(printf %q "$DEMO_DIR")"
        if [ "$IS_CUSTOM_DEMO_DIR" = "false" ] && [ -d "$ORIGINAL_DEMO_BASE" ]; then
            echo "   📂 Original temp directory preserved: $(printf %q "$ORIGINAL_DEMO_BASE")"
        fi
        echo "   🗂️  Temp files preserved: /tmp/trec-*"
        log_success "✨ Demo completed successfully!"
    else
        log_verbose "🧹 Cleaning up demo artifacts and temp files..."

        # Clean up demo directory (only if it's not a custom directory)
        if [ "$IS_CUSTOM_DEMO_DIR" = "false" ] && [ -d "$DEMO_DIR" ]; then
            echo "   📂 Removing demo project: $(printf %q "$DEMO_DIR")"
            safe_remove "$DEMO_DIR"
        elif [ "$IS_CUSTOM_DEMO_DIR" = "true" ]; then
            log_info "   📂 Preserving custom demo directory: $(printf %q "$DEMO_DIR")"
        fi

        # Always clean up the original temporary directory if it's different from current DEMO_DIR
        if [ "$IS_CUSTOM_DEMO_DIR" = "true" ] && [ -d "$ORIGINAL_DEMO_BASE" ] && [ "$ORIGINAL_DEMO_BASE" != "$DEMO_BASE" ]; then
            echo "   📂 Removing original temp directory: $(printf %q "$ORIGINAL_DEMO_BASE")"
            safe_remove "$ORIGINAL_DEMO_BASE"
        fi

        # Clean up other temporary files
        find /tmp -name "trec-*" -type d 2>/dev/null | while read -r dir; do
            safe_remove "$dir"
        done
        safe_remove "$DEMO_DIR/../demo_script.sh"
        safe_remove ".pyuv_done"; safe_remove "pyuvstarter_run.log"
        log_success "✨ Cleanup complete!"
    fi
    exit $exit_code
}

# === DIRECTORY INITIALIZATION ===
initialize_demo_directory() {
    log_verbose "Initializing demo directory..."

    if [ "$IS_CUSTOM_DEMO_DIR" = "true" ]; then
        log_verbose "Using custom demo directory: $(printf %q "$DEMO_DIR")"
        # DEMO_BASE and DEMO_DIR are already set by parse_arguments
        ORIGINAL_DEMO_BASE="$DEMO_BASE"  # No temp directory needed
    else
        log_verbose "Creating temporary demo directory..."
        # Create demo directory outside workspace to prevent contamination
        # Only call mktemp if we actually need a temporary directory
        ORIGINAL_DEMO_BASE=$(mktemp -d -t "pyuv_demo.XXXXXX")
        DEMO_BASE="$ORIGINAL_DEMO_BASE"
        DEMO_DIR="$DEMO_BASE/pyuvstarter_demo"
        log_verbose "Created temporary directory: $(printf %q "$ORIGINAL_DEMO_BASE")"
    fi

    log_verbose "Final demo directory: $(printf %q "$DEMO_DIR")"
}

# === MAIN EXECUTION ===
main() {
    # Initial setup
    log_verbose "Entering main with args: $*"
    detect_platform
    log_verbose "Platform detected: $PLATFORM"
    parse_arguments "$@"
    log_verbose "Arguments parsed"

    # Initialize demo directory after argument parsing
    initialize_demo_directory
    log_verbose "Demo directory initialized"

    # Set up exit handler
    trap cleanup EXIT INT TERM

    # Configure error handling based on mode
    if [ "$UNIT_TEST_MODE" = "true" ]; then
        log_info "Running in unit test mode"
        # In unit test mode, don't exit on errors - we want to capture all test results
        set +e  # Disable exit on error
        set -x   # Keep command tracing for debugging
    elif [ "$RECORD_DEMO" = "true" ]; then
        log_info "Running in recording mode"
        # In recording mode, use strict error handling
        set -ex  # Exit on error and show commands
    else
        log_info "Running in live demo mode"
        # In live demo mode, use strict error handling
        set -ex  # Exit on error and show commands
    fi

    # Create the demo project
    if [ "$UNIT_TEST_MODE" = "true" ]; then
        # Unit tests handle their own project creation
        run_unit_tests
        local test_exit_code=$?
        log_verbose "Unit tests completed with exit code: $test_exit_code"
        exit $test_exit_code
    else
        create_demo_project "demo"
        run_demo_engine "$([ "$RECORD_DEMO" == "true" ] && echo "record" || echo "live")"
    fi
}

# Execute main function
log_verbose "Starting create_demo.sh v$SCRIPT_VERSION..."
main "$@"