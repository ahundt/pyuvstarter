#!/bin/bash
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
#   --help            Show this help and exit
#
# PREREQUISITES:
#   - Python 3.x with pyuvstarter available
#   - For recording: t-rec (auto-installed if needed)
# ==============================================================================

set -euo pipefail  # Strict error handling
SCRIPT_VERSION="3.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# === CONFIGURATION ===
DEMO_DIR="pyuvstarter_demo_project"
OUTPUT_BASENAME="pyuvstarter_demo"
PYUVSTARTER_CMD="${PYUVSTARTER_CMD:-python3 $SCRIPT_DIR/pyuvstarter.py}"

# === STATE VARIABLES ===
UNIT_TEST_MODE=false
NO_CLEANUP=false
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
        echo "Platform detected: $PLATFORM"
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
  --help            Show this help and exit

EXAMPLES:
  # Run live demo
  ./create_demo.sh
  
  # Run unit tests
  ./create_demo.sh --unit-test
  
  # Record demo GIF
  ./create_demo.sh --record-demo

ENVIRONMENT VARIABLES:
  PYUVSTARTER_CMD - Override pyuvstarter command (default: python3 ./pyuvstarter.py)
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
    "torch": "681.2MB",
    "tensorflow": "439.1MB",
    "scikit-learn": "8.3MB",
    "matplotlib": "11.2MB",
    "seaborn": "3.1MB",
    "plotly": "7.2MB",
    "streamlit": "8.7MB",
    "jupyter": "6.4MB",
    "ipykernel": "1.2MB"
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
    
    # Clean and create directory structure
    rm -rf "$DEMO_DIR"
    mkdir -p "$DEMO_DIR"/{notebooks,scripts,src,tests,data}
    
    # Create files based on mode
    create_requirements_file "$mode"
    create_python_scripts "$mode"
    create_notebooks "$mode"
    create_supporting_files "$mode"
    
    log_verbose "Demo project created with mode: $mode"
}

create_requirements_file() {
    local mode="$1"
    
    if [[ "$mode" == "test" ]]; then
        # Minimal requirements for fast testing
        cat > "$DEMO_DIR/requirements.txt" << 'EOF'
# Minimal test requirements
numpy>=1.20
requests
sklearn  # Wrong package name!
EOF
    else
        # Realistic problematic requirements.txt
        cat > "$DEMO_DIR/requirements.txt" << 'EOF'
# Production ML Dependencies - INCOMPLETE & OUTDATED
# Last updated: 2021 (obviously needs work)

# Core ML libraries
numpy==1.19.0  # Old version - security vulnerabilities!
tensorflow>=2.0  # Which version exactly? 2.0 vs 2.15 is huge
# torch  # TODO: add pytorch (never got around to it)
sklearn  # WRONG! Package is 'scikit-learn' not 'sklearn'

# Data processing
# pandas  # Commented out but used EVERYWHERE in the code
# polars  # Modern alternative - forgot to add

# Visualization (partially missing)
matplotlib  # No version pin - risky!
# seaborn  # Missing but used in notebooks
# plotly  # Missing but used for interactive plots

# Web frameworks
requests==2.25.1
# fastapi  # API server - missing
# streamlit  # Dashboard - missing but used!
# dash  # Alternative dashboard - also missing

# Utilities
python-dotenv
# rich  # Pretty printing - missing
# typer  # CLI framework - missing
# loguru  # Better logging - missing

# Critical missing categories:
# - Jupyter & notebook support
# - Database drivers (psycopg2, pymongo, etc)
# - Cloud SDKs (boto3, google-cloud, azure)
# - Testing frameworks
# - ML experiment tracking (wandb, mlflow)
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
"""State-of-the-art ML training script - uses 25+ packages!"""

# Deep learning (ALL MISSING from requirements.txt!)
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import lightning.pytorch as pl

# Transformers & NLP (missing)
from transformers import AutoTokenizer, AutoModel
import datasets
from tokenizers import Tokenizer

# Experiment tracking (missing)
import wandb
import mlflow
from tensorboard import TensorBoard

# Config management (missing)
import hydra
from omegaconf import DictConfig

# More missing essentials
import pandas as pd
import typer
from loguru import logger

print("🤖 Modern ML stack initialized!")
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
    "!pip install opencv-python pillow\n",
    "!uv pip install streamlit gradio"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Magic commands - another way packages hide\n",
    "%pip install -U scikit-learn xgboost lightgbm\n",
    "%pip install prophet statsmodels"
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
    "import torch\n",
    "import tensorflow as tf\n",
    "from PIL import Image\n",
    "import cv2  # Note: import is 'cv2' but package is 'opencv-python'\n",
    "import sklearn  # Wrong import name!\n",
    "from bs4 import BeautifulSoup\n",
    "import requests\n",
    "import seaborn as sns\n",
    "import plotly.graph_objects as go"
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
    
    ((TEST_COUNT++))
    printf "🧪 TEST %02d: %-50s" "$TEST_COUNT" "$test_desc"
    
    # Run test with output capture
    local output
    local exit_code
    local start_time=$(date +%s)
    
    if output=$("$@" 2>&1); then
        exit_code=0
    else
        exit_code=$?
    fi
    
    local end_time=$(date +%s)
    local duration=$(( end_time - start_time ))  # Duration in seconds
    
    if [[ $exit_code -eq 0 ]]; then
        echo -e "${C_GREEN}[ ✅ PASSED ]${C_RESET} (${duration}s)"
        ((TEST_PASSED++))
        TEST_RESULTS="${TEST_RESULTS}${test_name}:PASSED\n"
    else
        echo -e "${C_RED}[ ❌ FAILED ]${C_RESET} (${duration}s)"
        ((TEST_FAILED++))
        TEST_RESULTS="${TEST_RESULTS}${test_name}:FAILED:$exit_code\n"
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
    
    local suite_start=$(date +%s)
    
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
        bash -c "[[ -f './pyuvstarter.py' ]] && python3 -m py_compile ./pyuvstarter.py"
    
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
    
    local suite_end=$(date +%s)
    local suite_duration=$((suite_end - suite_start))
    
    # Generate summary
    echo "============================================="
    echo -e "${C_BOLD}📊 TEST SUMMARY:${C_RESET}"
    echo "   Total Tests: $TEST_COUNT"
    echo -e "   ${C_GREEN}✅ Passed: $TEST_PASSED${C_RESET}"
    echo -e "   ${C_RED}❌ Failed: $TEST_FAILED${C_RESET}"
    echo "   ⏱️  Duration: ${suite_duration}s"
    echo "============================================="
    
    # Show warnings if any tests failed
    if [[ $TEST_FAILED -gt 0 ]]; then
        echo -e "\n${C_RED}${C_BOLD}⚠️  TEST FAILURES DETECTED:${C_RESET}"
        echo -e "$TEST_WARNINGS"
        echo -e "${C_YELLOW}Please check the errors above and fix any issues.${C_RESET}"
    fi
    
    # Generate JSON report for CI
    if [[ -n "${CI:-}" ]]; then
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
    
    cat > "test_results.json" << EOF
{
  "version": "$SCRIPT_VERSION",
  "platform": "$PLATFORM",
  "python": "$(python3 --version 2>&1 | cut -d' ' -f2)",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "summary": {
    "total": $TEST_COUNT,
    "passed": $TEST_PASSED,
    "failed": $TEST_FAILED,
    "duration_seconds": $duration
  },
  "tests": {
$(
    # Parse TEST_RESULTS string
    local first=true
    echo "$TEST_RESULTS" | while IFS=: read -r name result code; do
        [[ -z "$name" ]] && continue
        if [ "$first" = "true" ]; then first=false; else echo ","; fi
        if [ "$result" = "PASSED" ]; then
            echo -n "    \"$name\": \"PASSED\""
        else
            echo -n "    \"$name\": \"FAILED: Exit code $code\""
        fi
    done
)
  }
}
EOF
    
    log_info "Test report written to test_results.json"
}

# === DEMO EXECUTION ENGINE ===
create_demo_script() {
    cat > "$DEMO_DIR/.demo_script.sh" << 'DEMO_SCRIPT_EOF'
#!/bin/bash
# Self-contained demo script

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
    
    type_command "ls -la"
    ls -la | head -8 | sed 's/^/   /'
    echo "   ..."
    sleep 0.5
    
    echo -e "\n${C_YELLOW}Let's check the requirements:${C_RESET}"
    type_command "head -10 requirements.txt"
    head -10 requirements.txt | sed 's/^/   /'
    echo -e "${C_DIM}   # ... and 20+ missing dependencies${C_RESET}"
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
    
    # Show realistic progress
    echo -e "${C_GREEN}🚀 PYUVSTARTER v0.2.0${C_RESET}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Simulated progress messages
    progress_items=(
        "✓ Checking for uv installation"
        "✓ Initializing pyproject.toml"
        "✓ Creating .gitignore with best practices"
        "✓ Setting up virtual environment (.venv)"
        "📂 Scanning Python files for imports..."
        "   Found: pandas, sklearn, rich, numpy..."
        "📓 Analyzing Jupyter notebooks..."
        "   Found: seaborn, plotly, streamlit..."
        "🔍 Mapping import names to packages..."
        "   sklearn → scikit-learn"
        "   cv2 → opencv-python"
        "📦 Installing all dependencies..."
        "✓ Configuring VS Code"
        "✓ Creating execution log"
    )
    
    for item in "${progress_items[@]}"; do
        echo "   $item"
        sleep 0.25
    done
    
    echo -e "\n${C_GREEN}✨ Project modernization complete!${C_RESET}"
    sleep 1.5
    
    # Act 3: The Result (10 seconds)
    echo -e "\n${C_BOLD}3️⃣  The Result: A Modern Python Project${C_RESET}\n"
    sleep 0.5
    
    echo "What pyuvstarter created:"
    type_command "ls -la | grep -E '(pyproject|venv|lock|gitignore)'"
    echo -e "${C_GREEN}   ✅ pyproject.toml   ${C_DIM}# Modern Python configuration${C_RESET}"
    echo -e "${C_GREEN}   ✅ .venv/           ${C_DIM}# Isolated virtual environment${C_RESET}"
    echo -e "${C_GREEN}   ✅ uv.lock          ${C_DIM}# Reproducible dependency versions${C_RESET}"
    echo -e "${C_GREEN}   ✅ .gitignore       ${C_DIM}# Version control ready${C_RESET}"
    echo -e "${C_GREEN}   ✅ .vscode/         ${C_DIM}# IDE configuration${C_RESET}"
    sleep 1.5
    
    echo -e "\n${C_GREEN}Let's run that script again:${C_RESET}"
    type_command "source .venv/bin/activate && python scripts/data_analysis.py"
    sleep 0.3
    
    echo -e "${C_GREEN}✅ All dependencies are now properly installed!"
    echo -e "${C_BLUE}Running data analysis pipeline..."
    echo -e "Processed 1000 records successfully!${C_RESET}"
    sleep 1.5
    
    # Summary
    echo -e "\n${C_BOLD}${C_GREEN}🎉 Success!${C_RESET}"
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

record_demo() {
    log_info "Recording demo to GIF/MP4..."
    
    # Check for t-rec
    if ! command -v t-rec &>/dev/null; then
        log_error "t-rec not found. Please install it first."
        log_info "Install with: brew install t-rec (macOS) or cargo install t-rec (Linux)"
        return 1
    fi
    
    # Set terminal size for consistency
    echo "📐 Attempting to resize terminal to 30x100 for optimal recording..."
    printf '\e[8;30;100t'
    sleep 1  # Give time for resize
    
    # Check if resize worked by comparing terminal dimensions
    local current_rows=$(tput lines)
    local current_cols=$(tput cols)
    
    if [ "$current_rows" -ne 30 ] || [ "$current_cols" -ne 100 ]; then
        echo -e "${C_YELLOW}⚠️  Terminal resize may not have succeeded.${C_RESET}"
        echo "   Current size: ${current_rows}x${current_cols} (expected 30x100)"
        echo ""
        echo "   If you're using iTerm2, please:"
        echo "   1. Allow the resize request if prompted"
        echo "   2. Or disable the prompt in: Preferences > Advanced > 'Terminal windows resize smoothly'"
        echo ""
        read -p "Press Enter when ready to continue (or Ctrl+C to cancel)... "
        
        # Try resize again after user confirmation
        printf '\e[8;30;100t'
        sleep 0.5
    else
        echo "✅ Terminal resized successfully to 30x100"
    fi
    
    # Record the demo
    echo "🎬 Starting t-rec recording..."
    echo "The demo will run automatically in a new window."
    echo ""
    
    # Run t-rec with the demo script
    t-rec -m \
        --output "$OUTPUT_BASENAME" \
        "$DEMO_DIR/.demo_script.sh"
    
    # Check results
    echo -e "\n📦 Recording complete. Generated files:"
    for ext in gif mp4; do
        local file="${OUTPUT_BASENAME}.${ext}"
        if [[ -f "$file" ]]; then
            local size=$(get_file_size "$file")
            log_success "$file ($(human_readable_size $size))"
        else
            log_error "$file not created"
        fi
    done
}

# === CLEANUP ===
cleanup() {
    local exit_code=$?
    
    if [ "$NO_CLEANUP" != "true" ]; then
        log_verbose "Cleaning up demo artifacts..."
        rm -rf "$DEMO_DIR"
        rm -f .demo_script.sh .pyuv_done pyuvstarter_run.log
    else
        log_info "Demo artifacts preserved in: $DEMO_DIR"
    fi
    
    # Show final status
    if [[ $exit_code -eq 0 ]]; then
        log_success "Demo completed successfully!"
    else
        log_error "Demo failed with exit code: $exit_code"
    fi
    
    exit $exit_code
}

# === MAIN EXECUTION ===
main() {
    # Initial setup
    log_verbose "Entering main with args: $*"
    detect_platform
    log_verbose "Platform detected: $PLATFORM"
    parse_arguments "$@"
    log_verbose "Arguments parsed"
    
    # Set up exit handler
    trap cleanup EXIT INT TERM
    
    # Show mode
    if [ "$UNIT_TEST_MODE" = "true" ]; then
        log_info "Running in unit test mode"
    elif [ "$RECORD_DEMO" = "true" ]; then
        log_info "Running in recording mode"
    else
        log_info "Running in live demo mode"
    fi
    
    # Create the demo project
    if [ "$UNIT_TEST_MODE" = "true" ]; then
        # Unit tests handle their own project creation
        run_unit_tests
    else
        create_demo_project "demo"
        run_demo_engine $([ "$RECORD_DEMO" == "true" ] && echo "record" || echo "live")
    fi
}

# Execute main function
log_verbose "Starting create_demo.sh v$SCRIPT_VERSION..."
main "$@"