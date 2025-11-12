# PyUVStarter Development Guide

**FOR PYUVSTARTER DEVELOPERS ONLY**

This guide is for developers modifying the pyuvstarter tool itself (pyuvstarter.py source code in THIS repository). If you're a user looking to use pyuvstarter for your Python projects, see README.md instead.

---

## Development Environment Setup

When developing THE PYUVSTARTER TOOL ITSELF, you need both an editable install (for `uv run pyuvstarter`) and a tool install (for direct `pyuvstarter` command).

### Quick Setup
```bash
uv venv
uv sync
uv pip install -e .
uv tool install .
```

---

## ⚠️ Important: UV Cache and Code Freshness

### Problem: Cached Pyuvstarter Tool Code Can Execute After You Modify Source

**Symptom**: You modify `pyuvstarter.py` (THE TOOL'S source code in this repository) but when you run `uv run pyuvstarter` or the `pyuvstarter` command, the OLD CACHED version of the tool still executes instead of your new code.

**Root Cause**: UV caches built versions of THE PYUVSTARTER TOOL in multiple locations:
- `~/.cache/uv/sdists-v9/editable/` - Cached editable builds
- `~/.cache/uv/archive-v0/` - Cached package metadata
- `~/.cache/uv/builds-v0/` - Build artifacts
- `.venv/lib/python*/site-packages/` - Installed package
- `__pycache__/` - Python bytecode cache
- `~/.local/share/uv/tools/pyuvstarter/` - Tool installation

**When This Happens** (during pyuvstarter tool development):
- After modifying pyuvstarter.py (THE TOOL'S source code)
- After git operations (checkout, pull, commit) on THE PYUVSTARTER REPOSITORY
- Features YOU ADDED to pyuvstarter.py don't execute when you run the tool
- Log files show different commands/behavior than your modified source code should produce
- Functions or code paths you modified don't execute
- Pyuvstarter's own tests behave inconsistently across runs

### Solution: Complete Cache Refresh

**Option 1: Use the force reinstall script (recommended)**
```bash
./dev_force_reinstall_to_fix_outdated_pyuvstarter_code.sh
```

**Option 2: Manual steps**
```bash
# 1. Clear UV cache for pyuvstarter
uv cache clean pyuvstarter --force

# 2. Prune unused UV cache entries
uv cache prune --force

# 3. Remove virtual environment
rm -rf .venv
# or: trash .venv  (if trash-cli installed)

# 4. Remove Python bytecode cache
rm -rf __pycache__
find . -name "*.pyc" -delete

# 5. Create fresh virtual environment
uv venv

# 6. Sync dependencies from lock file
uv sync

# 7. Install as editable package (for 'uv run pyuvstarter')
uv pip install --reinstall --no-cache -e .

# 8. Install as UV tool (for direct 'pyuvstarter' command)
uv tool uninstall pyuvstarter || true
uv tool install --force --reinstall .
```

### Verification

After refresh, verify new code is running:

```bash
# Test editable install
uv run pyuvstarter --version

# Test tool install
pyuvstarter --version

# Check for new features (example: UV_PYTHON diagnostics)
cd /tmp && mkdir test_fresh && cd test_fresh
echo "import pandas" > test.py
UV_PYTHON=3.12 uv run pyuvstarter --dry-run .

# Check log file for diagnostic messages
grep "with Python 3.12" pyuvstarter_setup_log.json
# Should find: "Ensuring CLI tool ... with Python 3.12"
# Should find: "Running pipreqs with explicit Python 3.12"
```

### Quick Cache Status Check

```bash
# Check if pyuvstarter is in UV cache
uv cache dir  # Shows cache location
ls ~/.cache/uv/sdists-v9/editable/ | grep pyuvstarter

# Check tool installation
uv tool list | grep pyuvstarter

# Check editable install
uv pip list | grep pyuvstarter
```

---

## Testing Pyuvstarter Itself

**Note**: These are tests FOR THE PYUVSTARTER TOOL, not tests of user projects.

### Run All Tests
```bash
# Full comprehensive test suite for pyuvstarter tool
tests/run_all_tests.sh

# Individual pyuvstarter tool test files
uv run tests/test_jupyter_pipeline.py
uv run tests/test_project_structure.py
```

### Test with Specific Python Version
```bash
# Set UV_PYTHON to test version consistency
UV_PYTHON=3.11 uv run tests/test_jupyter_pipeline.py

# Check logs show correct Python version
cd /tmp && mkdir test_py311 && cd test_py311
echo "import pandas" > test.py
UV_PYTHON=3.11 uv run pyuvstarter .
grep "with Python 3.11" pyuvstarter_setup_log.json
```

---

## Common Development Tasks

### After Code Changes
Always force reinstall:
```bash
./dev_force_reinstall_to_fix_outdated_pyuvstarter_code.sh
```

### After Git Operations
```bash
git pull origin main
./dev_force_reinstall_to_fix_outdated_pyuvstarter_code.sh
```

### Before Running Tests
```bash
./dev_force_reinstall_to_fix_outdated_pyuvstarter_code.sh
tests/run_all_tests.sh
```

---

## CI and UV_PYTHON Environment Variable

### How UV_PYTHON Works

The `UV_PYTHON` environment variable ensures consistent Python versions across:
- `uv venv` - Virtual environment creation
- `uv tool install` - Tool installation
- `uvx` - Tool execution
- `uv run` - Script execution

**CI Usage** (`.github/workflows/ci.yml`):
```yaml
env:
  UV_PYTHON: ${{ matrix.python-version }}
```

**Local Testing**:
```bash
UV_PYTHON=3.12 uv run pyuvstarter <dir>
```

### Why This Matters

UV tools (pipreqs, ruff) are Python-version-specific. When installed for Python 3.12, they can't be used correctly with Python 3.14. The UV_PYTHON variable ensures:
1. Tools are installed for the correct Python version
2. Tools are executed with the same Python version
3. No state pollution between sequential test runs with different Python versions

See `notes/jupyter-ci-bug-reproduction.md` for detailed root cause analysis.

---

## Troubleshooting

### "Old code still running after changes"
**Solution**: Run `./dev_force_reinstall_to_fix_outdated_pyuvstarter_code.sh`

### "Tests pass directly but fail in run_all_tests.sh"
**Possible causes**:
1. UV tool cache from previous run with different Python
2. Bytecode cache (__pycache__)
3. Stale .venv

**Solution**: Refresh installation, run tests again

### "Dependencies not detected in Jupyter notebooks"
**Check**:
1. Is UV_PYTHON set correctly?
2. Are diagnostic messages in pyuvstarter_setup_log.json?
3. Do commands show `--python X.Y` flags?
4. Did pipreqs/ruff tools install successfully?

**Solution**:
```bash
./dev_force_reinstall_to_fix_outdated_pyuvstarter_code.sh
UV_PYTHON=3.12 uv run pyuvstarter <test_dir>
# Check log file for diagnostics
```

### "import pyuvstarter finds wrong version"
**Check which file Python loads**:
```bash
uv run python -c "import pyuvstarter; print(pyuvstarter.__file__)"
# Should be: /path/to/pyuvstarter/pyuvstarter.py
```

**If wrong path**: Run `./dev_force_reinstall_to_fix_outdated_pyuvstarter_code.sh`

---

## Development Best Practices

1. **Always reinstall after code changes**: `./dev_force_reinstall_to_fix_outdated_pyuvstarter_code.sh`
2. **Run tests with UV_PYTHON set**: `UV_PYTHON=3.12 tests/run_all_tests.sh`
3. **Check logs for diagnostics**: Look for "with Python X.Y" messages
4. **Verify commands have --python**: Check pyuvstarter_setup_log.json
5. **Test both install methods**:
   - Editable: `uv run pyuvstarter`
   - Tool: `pyuvstarter` (direct command)
