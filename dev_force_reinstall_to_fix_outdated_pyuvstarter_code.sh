#!/bin/bash
# dev_force_reinstall_to_fix_outdated_pyuvstarter_code.sh
#
# ═══════════════════════════════════════════════════════════════════════════
# FOR PYUVSTARTER DEVELOPERS ONLY - NOT FOR END USERS
# ═══════════════════════════════════════════════════════════════════════════
#
# This script reinstalls THE PYUVSTARTER TOOL ITSELF (this repository's code).
# It does NOT affect user projects or code that pyuvstarter processes.
#
# ═══════════════════════════════════════════════════════════════════════════
# WHEN TO USE THIS SCRIPT:
# ═══════════════════════════════════════════════════════════════════════════
#
# Use this when you modify PYUVSTARTER'S OWN SOURCE CODE (pyuvstarter.py in THIS repo)
# and your changes don't take effect when running the pyuvstarter command.
#
# ❌ DO NOT USE THIS FOR:
# - User projects that pyuvstarter processes
# - Fixing issues with Python code in projects you're managing with pyuvstarter
# - Normal pyuvstarter usage as an end user
# - Installing pyuvstarter for the first time
#
# ✅ USE THIS WHEN:
# - You modified pyuvstarter.py (THE TOOL'S source) and changes don't appear
# - You're developing/testing THE PYUVSTARTER TOOL ITSELF
# - After git pull/checkout on THE PYUVSTARTER REPOSITORY
# - Before running PYUVSTARTER'S OWN test suite (tests/test_*.py)
# - Diagnostic messages you added to pyuvstarter.py don't appear in logs
#
# ═══════════════════════════════════════════════════════════════════════════
# WHY THIS SCRIPT EXISTS (Critical for PyUVStarter Development):
# ═══════════════════════════════════════════════════════════════════════════
#
# UV aggressively caches packages for performance. This is great for users but
# problematic when developing THE PYUVSTARTER TOOL ITSELF because:
#
# 1. CACHED EDITABLE BUILDS of pyuvstarter persist in ~/.cache/uv/sdists-v9/editable/
# 2. TOOL INSTALLATIONS of pyuvstarter cache in ~/.local/share/uv/tools/pyuvstarter/
# 3. PYTHON BYTECODE of pyuvstarter.py caches in __pycache__/
# 4. VIRTUAL ENVIRONMENT has installed pyuvstarter package metadata
#
# Result: You modify pyuvstarter.py source code but `uv run pyuvstarter` executes
# the CACHED OLD VERSION of pyuvstarter.py!
#
# SYMPTOMS OF STALE PYUVSTARTER CACHE (How to Recognize Cached Old Code):
# - Changes to pyuvstarter.py source don't take effect when running the tool
# - Features you added to pyuvstarter.py don't appear in execution
# - Log files (pyuvstarter_setup_log.json) show different behavior than source code
# - Commands logged differ from what your modified source code should generate
# - Functions or code paths you added/modified don't execute
# - Pyuvstarter's own test suite behaves inconsistently across runs
#
# THIS SCRIPT ENSURES:
# - All cached versions are removed
# - Fresh build from current source code
# - Both `uv run pyuvstarter` and `pyuvstarter` command use latest code
#
# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION ORDER (Optimized for Clean Rebuild):
# ═══════════════════════════════════════════════════════════════════════════
#
# 1. Remove .venv (local virtual environment)
# 2. Remove __pycache__ (Python bytecode cache)
# 3. Clear UV cache for pyuvstarter (package-specific)
# 4. Prune UV cache (general cleanup)
# 5. Create fresh venv (foundation)
# 6. Sync dependencies (populate venv)
# 7. Install editable (for development/testing)
# 8. Install as tool (for command-line use)
#
# This order ensures we clean from most local to most global, then rebuild
# from foundation upward.
#
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on any error

# Parse optional Python version parameter (supports both --python flag and positional arg)
PYTHON_VERSION=""

if [[ "$1" == "--python" ]]; then
    # Flag-based usage: ./script.sh --python 3.14
    PYTHON_VERSION="${2:-}"
    if [ -z "$PYTHON_VERSION" ]; then
        echo "❌ ERROR: --python flag requires a version argument"
        echo "Usage: $0 [--python VERSION]"
        echo "Example: $0 --python 3.14"
        exit 1
    fi
elif [ -n "$1" ]; then
    # Backwards compatible positional usage: ./script.sh 3.14
    PYTHON_VERSION="$1"
fi

if [ -n "$PYTHON_VERSION" ]; then
    echo "🧹 Refreshing pyuvstarter installation with Python $PYTHON_VERSION"
    export UV_PYTHON="$PYTHON_VERSION"
else
    echo "🧹 Refreshing pyuvstarter installation (using default Python)"
fi
echo "============================================================"
echo ""

# Step 1: Remove virtual environment (highest-level local state)
echo "1️⃣  Removing .venv..."
if [ -d ".venv" ]; then
    # Try trash if available, otherwise rm
    if command -v trash &> /dev/null; then
        trash .venv
    else
        rm -rf .venv
    fi
    echo "  ✅ Removed .venv"
else
    echo "  ℹ️  No .venv to remove"
fi

# Step 2: Remove Python bytecode cache
echo ""
echo "2️⃣  Removing Python bytecode cache..."
# Remove all __pycache__ directories recursively (not just root)
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
# Remove any .pyc files
find . -name "*.pyc" -type f -delete 2>/dev/null || true
echo "  ✅ Removed __pycache__ directories and .pyc files"

# Step 3: Clear UV cache for pyuvstarter (package-specific)
echo ""
echo "3️⃣  Clearing UV cache for pyuvstarter..."
uv cache clean pyuvstarter --force || echo "  ℹ️  No pyuvstarter cache to clear"

# Step 4: Prune unused cache entries (general cleanup)
echo ""
echo "4️⃣  Pruning UV cache..."
uv cache prune --force

# Step 5: Create fresh virtual environment (foundation for rebuild)
echo ""
echo "5️⃣  Creating fresh virtual environment..."
if [ -n "$PYTHON_VERSION" ]; then
    uv venv --python "$PYTHON_VERSION"
    echo "  ✅ Created .venv with Python $PYTHON_VERSION"
else
    uv venv
    echo "  ✅ Created .venv"
fi

# Step 6: Sync dependencies
echo ""
echo "6️⃣  Syncing dependencies from lock file..."
uv sync
echo "  ✅ Synced dependencies"

# Step 7: Install pyuvstarter as editable package
echo ""
echo "7️⃣  Installing pyuvstarter as editable package (for 'uv run')..."
uv pip install --reinstall --no-cache -e .
echo "  ✅ Installed editable package"

# Step 8: Install pyuvstarter as UV tool
echo ""
echo "8️⃣  Installing pyuvstarter as UV tool (for direct command)..."
# Uninstall first if present
uv tool uninstall pyuvstarter 2>/dev/null || echo "  ℹ️  Tool not previously installed"
# Install fresh
if [ -n "$PYTHON_VERSION" ]; then
    uv tool install --force --reinstall --python "$PYTHON_VERSION" .
    echo "  ✅ Installed UV tool with Python $PYTHON_VERSION"
else
    uv tool install --force --reinstall .
    echo "  ✅ Installed UV tool"
fi

echo ""
echo "============================================================"
echo "✅ PyUVStarter refresh complete!"
echo "============================================================"
echo ""
echo "📋 Summary:"
echo "  ✅ Cleared all caches"
echo "  ✅ Fresh virtual environment created"
echo "  ✅ Editable install: uv run pyuvstarter"
echo "  ✅ Tool install: pyuvstarter (direct command)"
echo ""
echo "🧪 Verify installation:"
echo "  uv run pyuvstarter --version"
echo "  pyuvstarter --version"
echo ""
echo "🚀 Run tests:"
if [ -n "$PYTHON_VERSION" ]; then
    echo "  UV_PYTHON=$PYTHON_VERSION uv run tests/test_jupyter_pipeline.py"
    echo "  UV_PYTHON=$PYTHON_VERSION tests/run_all_tests.sh"
else
    echo "  uv run tests/test_jupyter_pipeline.py"
    echo "  tests/run_all_tests.sh"
fi
echo ""
echo "💡 Usage: $0 [--python VERSION | VERSION]"
echo "   Examples:"
echo "     $0 3.14           # Positional argument (backwards compatible)"
echo "     $0 --python 3.14  # Flag-based argument"
