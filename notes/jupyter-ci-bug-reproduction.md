# Jupyter Pipeline CI Test Failure - Root Cause Analysis

## Date
2025-11-11

## Issue Summary
Tests in `tests/test_jupyter_pipeline.py` and `tests/test_project_structure.py` were failing in GitHub Actions CI but passing locally.

## CI Failure Pattern
- **Ubuntu (all Python versions 3.11-3.14)**: FAILED
- **macOS 3.13**: FAILED
- **macOS 3.14**: FAILED
- **Windows (all versions)**: PASSED

## Error Messages
```
❌ TestJupyterNotebookPipeline.test_complex_notebook_with_various_imports FAILED:
   Expected package 'pandas' not found in dependencies: []

❌ TestJupyterNotebookPipeline.test_notebook_in_subdirectories FAILED:
   Expected package 'pandas' not found in dependencies: []
```

## Initial Hypothesis (INCORRECT)
Believed the issue was Python version mismatch in CI:
- CI workflow used `uv venv` without `--python` flag
- Suspected UV was creating venvs with wrong Python version
- Thought tests claimed "Python 3.14" but actually used Python 3.12

**Evidence for this**: CI logs showed Python 3.12 paths in error traces for jobs claiming to test Python 3.14

## Initial Fix Attempt (CAUSED REGRESSIONS)
1. Added `UV_PYTHON=3.14` environment variable to CI
2. Added `--python ${{ matrix.python-version }}` to all `uv venv` commands
3. **MISTAKE**: Modified test files to pass `--python` explicitly when `UV_PYTHON` set:
   - `tests/test_utils.py`: Added `--python` flag to `uv run` commands
   - `tests/test_import_fixing.py`: Added `--python` flag to `uv run` commands

## Reproduction of CI Bug Locally
```bash
# Normal execution - ALL TESTS PASS
$ python3 tests/test_jupyter_pipeline.py
Results: 12/12 tests passed
🎉 All Jupyter pipeline tests passed!

# With UV_PYTHON set - TESTS FAIL (reproduces CI bug!)
$ UV_PYTHON=3.14 python3 tests/test_jupyter_pipeline.py
Results: 9/12 tests passed
💥 3 tests failed!
❌ TestJupyterNotebookPipeline.test_complex_notebook_with_various_imports FAILED:
   Expected package 'pandas' not found in dependencies: []
```

**Key Finding**: Setting `UV_PYTHON` environment variable **caused** test failures that matched CI behavior!

## Root Cause Analysis

### Why UV_PYTHON Caused Failures
When `UV_PYTHON` is set AND `--python` flag is explicitly passed to `uv run`:
1. Creates conflict or unexpected behavior in UV's Python selection
2. Breaks pyuvstarter's dependency detection (returns empty dependencies)
3. Specifically affects Jupyter notebook dependency extraction

###Current Understanding
The CI failure is NOT primarily about Python version mismatch. The real issue appears to be:
1. **Test execution context**: How `uv run pyuvstarter` behaves in CI vs local
2. **Environment inheritance**: Subprocess environment handling in test framework
3. **UV behavior differences**: How UV resolves Python when multiple signals present

## Solution Approach

### What DIDN'T Work
- ❌ Adding `--python` to `uv run` commands in test files (caused regressions)
- ❌ Explicit Python version in subprocess calls (broke dependency detection)

### Current Approach (Defensive)
1. ✅ Set `UV_PYTHON=${{ matrix.python-version }}` at CI job level
2. ✅ Keep explicit `--python` on `uv venv`, `uv tool install` commands in CI
3. ✅ Let test files use `uv run` without explicit `--python` (env var inherited)
4. ✅ Add verification output to see actual Python versions in CI

### Key Insight
`UV_PYTHON` should work through environment inheritance to subprocesses. The tests copy `os.environ`, so UV_PYTHON is automatically available to all `uv` commands run by tests.

## Files Changed
- `.github/workflows/ci.yml`: Added UV_PYTHON env var + verification output
- `tests/test_utils.py`: NO CHANGES (reverted)
- `tests/test_import_fixing.py`: NO CHANGES (reverted)

## Testing Status
- ✅ Local tests pass without UV_PYTHON:  `uv run python tests/test_jupyter_pipeline.py` → 12/12 passed
- ❌ Local tests fail with UV_PYTHON: `UV_PYTHON=3.14 python3 tests/test_jupyter_pipeline.py` → 9/12 passed
- ❌ Using `uv run --python 3.14` triggers pydantic-core build errors (Python 3.14 too new, no wheels)
- ⏳ CI testing pending with new approach

## Critical Discovery: uv run Python Version Handling

### Test Execution Methods
```bash
# Method 1: Bare python3 (inconsistent)
$ python3 tests/test_jupyter_pipeline.py
Results: 11/12 tests passed  # ⚠️  Sometimes fails

# Method 2: uv run python (correct, consistent)
$ uv run python tests/test_jupyter_pipeline.py
Results: 12/12 tests passed  # ✅ Always works

# Method 3: uv run --python 3.14 (build errors on new Python)
$ uv run --python 3.14 python tests/test_jupyter_pipeline.py
ERROR: pydantic-core build failure  # ❌ Triggers source builds
```

### Root Cause: Test Execution Method
The real issue is **how tests are invoked**, not Python version mismatch:
- CI line 196 (old): `if python "$test_file"; then` after `source .venv/bin/activate`
- CI line 194 (new): `if uv run --python ${{ matrix.python-version }} python "$test_file"; then`

### Why This Matters
1. `uv run` creates an **isolated environment** with correct Python + dependencies
2. Bare `python` after venv activation uses **activated venv Python** (might be wrong version)
3. `UV_PYTHON` env var ensures ALL `uv` commands (including nested calls) use correct Python

## Solution Architecture

### Defense in Depth Strategy
1. **Job-level env var**: `UV_PYTHON=${{ matrix.python-version }}` (inherited by all subprocesses)
2. **Explicit --python on venv**: `uv venv --python ${{ matrix.python-version }}` (direct commands)
3. **Explicit --python on uv run**: `uv run --python ${{ matrix.python-version }} python` (test execution)
4. **Explicit --python on uv tool**: `uv tool install . --python ${{ matrix.python-version }}` (tool install)

### Fallback Behavior (Local Development)
When UV_PYTHON is not set:
- `uv venv` uses default Python from PATH
- `uv run` uses Python from project's venv or system default
- Still works, just uses developer's local Python version

## Open Questions
1. ⚠️  Will `--python 3.14` trigger build failures in CI for packages without Python 3.14 wheels?
2. Should we use `--python 3.11` as the "safest" version with most wheel availability?
3. Does the pydantic-core issue affect CI differently than local?

## Next Steps
1. Monitor for pydantic-core build failures in CI
2. If build failures occur, consider:
   - Using older Python version as baseline (3.11)
   - Pre-installing binary dependencies
   - Caching UV builds

## Commands for Local Reproduction
```bash
# Correct way - via uv run (always works)
uv run tests/test_jupyter_pipeline.py

# Incorrect way - bare python3 (inconsistent)
python3 tests/test_jupyter_pipeline.py

# Triggers pydantic build issue (Python 3.14)
uv run --python 3.14 tests/test_jupyter_pipeline.py

# Run full test suite
tests/run_all_tests.sh
```

---

## INVESTIGATION: Python-Version-Specific UV Tool Installation State Pollution

### Theory (Attempted Fix - See 2025-11-12 Update Below)

After deeper investigation, discovered the true root cause through timeline analysis:

#### Evidence from CI Logs

**First Test Run** (CI test loop at ~01:22-01:24):
- Method: `python "$test_file"` after `source .venv/bin/activate`
- Results: ✅ **ALL TESTS PASSED** on all platforms
```
ubuntu-latest 3.14: test_jupyter_pipeline.py → 12/12 passed at 01:23:39
macos-latest 3.13: test_jupyter_pipeline.py → 12/12 passed at 01:23:19
```

**Second Test Run** (run_all_tests.sh comprehensive suite at ~01:24-01:26):
- Method: `source .venv/bin/activate && python3 "tests/$test"`
- Results: ❌ **FAILURES** with `dependencies: []`
```
macos-latest 3.13 at 01:24:44: test_basic_notebook_discovery FAILED
macos-latest 3.14 at 01:26:30: test_complex_notebook_with_various_imports FAILED
                               test_notebook_in_subdirectories FAILED
```

#### The State Pollution Mechanism

UV tools are **Python-version-specific** and installed in `~/.local/share/uv/tools/`:

**First Run Sequence:**
1. Test activates venv → Python version X in PATH
2. Test runs `uv run pyuvstarter` inside temp project
3. pyuvstarter calls `uv tool install pipreqs` → installs pipreqs for Python X
4. pyuvstarter calls `uvx pipreqs --scan-notebooks ...` → uses pipreqs with Python X
5. pipreqs scans notebooks correctly → dependencies found ✅

**Second Run Sequence (State Polluted):**
1. Different test activates venv → Python version Y in PATH (different from X)
2. Test runs `uv run pyuvstarter` inside temp project
3. pyuvstarter calls `uv tool install pipreqs` → pipreqs already installed for Python X (idempotent, skips)
4. pyuvstarter calls `uvx pipreqs --scan-notebooks ...` → tries to use Python X's pipreqs with Python Y environment
5. **Python version mismatch** → pipreqs fails silently or returns empty results
6. No dependencies detected → `dependencies: []` ❌

#### Why Windows Passed

Windows test configuration only runs **one test loop** (lines 275-298), not two:
- No comprehensive run_all_tests.sh execution
- No opportunity for state pollution between runs
- Consistent Python environment throughout
- All tests pass ✅

### Complete Root Cause

The bug has **three contributing factors**:

1. **Sequential test runs with different Python versions** (first vs second run)
2. **UV tool installation is Python-version-specific** (tools installed for wrong Python)
3. **No UV_PYTHON propagation through the call chain**:
   ```
   CI → test script → uv run pyuvstarter → uv tool install → uvx pipreqs
   ```
   Without UV_PYTHON, each command independently discovers Python, causing mismatches.

### The Complete Fix

**Environment Variable** (CI + subprocesses):
```yaml
env:
  UV_PYTHON: ${{ matrix.python-version }}
```

**Test Execution** (CI + run_all_tests.sh):
```bash
# OLD (fragile - uses activated venv Python):
source .venv/bin/activate
python "$test_file"

# NEW (robust - uses UV_PYTHON):
uv run "$test_file"
```

**Application Code** (pyuvstarter.py - 6 locations):
```python
# OLD (no version specification):
["uv", "tool", "install", "pipreqs"]
["uvx", "pipreqs", "--print"]
["uvx", "ruff", "check"]

# NEW (respects UV_PYTHON):
cmd = ["uvx"]
if os.environ.get("UV_PYTHON"):
    cmd.extend(["--python", os.environ["UV_PYTHON"]])
cmd.extend(["pipreqs", "--print"])
```

### Locations Fixed in pyuvstarter.py

1. **Line 2051-2055**: `_ensure_tool_available()` - `uv tool install` with `--python`
2. **Line 2925-2929**: `_get_packages_from_pipreqs()` - `uvx pipreqs` with `--python`
3. **Line 3020-3031**: `_run_ruff_unused_import_check()` - `uvx ruff` analysis with `--python`
4. **Line 3134-3145**: `_run_ruff_unused_import_check()` - `uvx ruff` fix with `--python`
5. **Line 3894-3903**: `_detect_relative_import_issues()` - `uvx ruff` with `--python`
6. **Line 3978-3987**: `_fix_relative_imports()` - `uvx ruff` with `--python`

### Backward Compatibility

All changes use conditional logic:
```python
if os.environ.get("UV_PYTHON"):
    cmd.extend(["--python", os.environ["UV_PYTHON"]])
```

**Local development** (UV_PYTHON not set):
- ✅ Works normally with system/venv Python
- ✅ No breaking changes
- ✅ Maintains existing behavior

**CI environment** (UV_PYTHON set):
- ✅ All UV commands use consistent Python version
- ✅ No state pollution between test runs
- ✅ Tools installed for correct Python

### Verification

**Local Testing**:
```bash
$ tests/run_all_tests.sh
Results: 11/11 tests passed ✅

$ uv run tests/test_jupyter_pipeline.py
Results: 12/12 tests passed ✅
```

**Files Changed**:
- `.github/workflows/ci.yml`: 26 lines changed (add UV_PYTHON, remove venv activation, use uv run)
- `tests/run_all_tests.sh`: 3 lines changed (remove venv activation, use uv run)
- `pyuvstarter.py`: 48 lines changed (add UV_PYTHON support to 6 tool/uvx calls)

**Commit**: `87c24bd` - "ci.yml, run_all_tests.sh, pyuvstarter.py: fix Python version consistency across uv tool ecosystem"

### Why This Theory Was Proposed

- **First run passes**: Tools installed for active Python, everything matches
- **Second run fails**: Tools from first run (wrong Python) used in second run (different Python)
- **Windows always passes**: Only one test run, no state pollution opportunity
- **Local tests pass**: Single Python version throughout (3.14), no version conflicts
- **`dependencies: []`**: pipreqs/ruff tools fail silently with Python mismatch, return empty results

**Status**: This theory led to implementing `_build_uv_command_with_python()` helper (commits bba9aaf, dc7e4d0). However, 2025-11-12 investigation found this implementation actually **caused** the problem rather than fixing it. See update below.

---

## 2025-11-12 Investigation Update

### Previous Analysis Status: INCORRECT

**What Was Wrong:**
- Lines 166-315 claimed UV_PYTHON implementation with `_build_uv_command_with_python()` fixed the issue
- This was based on incorrect analysis
- The helper function adding `--python` flags actually **CAUSED** the corruption rather than fixing it

### Concrete Evidence from 2025-11-12 Investigation

**Reproduction with UV_PYTHON set** (local macOS):
```bash
$ UV_PYTHON=3.13 uv run tests/test_jupyter_pipeline.py
Results: 5/12 tests passed
💥 7 tests failed!
Error: Expected package 'pandas' not found in dependencies: []
```

**Tool corruption observed** (`~/.local/share/uv/tools/pipreqs`):
```bash
$ uv tool list
warning: Ignoring malformed tool `pipreqs` (run `uv tool uninstall pipreqs` to remove)
```

**After pipreqs reinstall WITHOUT UV_PYTHON**:
```bash
$ uv run tests/test_jupyter_pipeline.py
Results: 12/12 tests passed ✅
```

**UV Documentation** (https://docs.astral.sh/uv/reference/environment/):
> "UV_PYTHON: Equivalent to the `--python` command-line argument. The `--python` flag becomes optional when `UV_PYTHON` is set."

### Actual Fix Implemented (Commit 37743e6)

**Changed Files:**
- `pyuvstarter.py`: Removed `_build_uv_command_with_python()` function (lines 2040-2110, 70 lines deleted)
- `pyuvstarter.py`: Simplified `_ensure_tool_available()` to no-op (no `uv tool install`, line 2040-2064)
- `pyuvstarter.py`: Reverted 5 uvx call sites to plain commands (lines 2930, 3033, 3217, 3975, 4057)
- `pyuvstarter.py`: Updated progress messages (lines 1273-1274, 1379-1380)
- `dev_force_reinstall_to_fix_outdated_pyuvstarter_code.sh`: Added optional Python version parameter (40 lines added)

**Rationale:**
- `uvx` creates ephemeral environments automatically - no `uv tool install` needed
- `uvx` respects UV_PYTHON environment variable without explicit `--python` flags
- No persistent global state at `~/.local/share/uv/tools/` to corrupt
- Matches uv design: uvx for programmatic tool execution, uv tool install for user PATH tools

**Test Results After Fix:**
```bash
$ uv run tests/test_jupyter_pipeline.py
Results: 12/12 tests passed ✅

$ UV_PYTHON=3.11 uv run tests/test_jupyter_pipeline.py
Results: 12/12 tests passed ✅

$ UV_PYTHON=3.13 uv run tests/test_jupyter_pipeline.py
Results: 12/12 tests passed ✅
```

### Remaining Intermittent Failures (UNSOLVED)

**Observed Pattern** (non-deterministic):
- Tests pass when run in isolation: `python3 tests/test_jupyter_pipeline.py` → 12/12 ✅
- Tests fail intermittently in `./tests/run_all_tests.sh` → 10/11 or 11/12 ❌
- **Different tests fail on different runs** (not always same test)

**Failure Examples from run_all_tests.sh:**
```
Run 1: test_notebook_with_pip_install_commands FAILED
Run 2: test_notebook_systems_detection FAILED
Run 3: test_project_with_conflicting_structures FAILED
```

**Error Pattern:**
- Error messages often empty: `FAILED: ` (no details)
- Sometimes shows: `PyUVStarter failed: ` (no stderr captured)
- Exit code 1 but no stderr output

**Concrete Test Results:**
- `python3 tests/test_project_structure.py` → 11/11 PASS ✅
- `uv run tests/test_project_structure.py` → 10/11 PASS ❌ (test_project_with_conflicting_structures fails)
- Single test in isolation: `test_project_with_conflicting_structures()` → PASS ✅

### Low-Confidence Theories (Unverified)

**Theory 1: uv run environment isolation**
- Hypothesis: `uv run` creates different execution environment than bare `python3`
- Evidence: Same tests pass with python3, fail with uv run
- Confidence: LOW - single test runs don't establish pattern

**Theory 2: Shared singleton state** (test_utils.py:651):
```python
temp_manager = TempProjectManager()  # Global singleton
```
- Hypothesis: `temp_manager.temp_dirs` list accumulates across all test files
- Evidence: Failures only in jupyter_pipeline and project_structure (last 2 tests in suite)
- Confidence: LOW - cleanup logic exists in context manager

**Theory 3: pyuvstarter error handling**
- Hypothesis: SystemExit raises don't write to stderr, only to log JSON
- Evidence: pyuvstarter.py:4432,4438,4474 raise SystemExit without stderr output
- Confidence: LOW - improved logging added but not yet verified

**Theory 4: Race condition in temp directory cleanup**
- Hypothesis: Context manager cleanup has race condition under `uv run`
- Evidence: None concrete, purely speculative
- Confidence: VERY LOW

### Investigation Steps Taken (2025-11-12)

1. Added comprehensive error formatter to test assertions (test_utils.py:32-51, test_jupyter_pipeline.py)
2. Improved pyuvstarter stderr logging: added `err=True` to all safe_typer_secho error calls (pyuvstarter.py:4845,4860,4875,4887-4892,4906-4907)
3. Added explicit logging before SystemExit raises (pyuvstarter.py:4433-4435,4442-4444,4481-4483)
4. Confirmed global singleton usage: temp_manager, executor, validator (test_utils.py:651-654)

### Current Status

**Resolved:**
- ✅ UV_PYTHON tool corruption fixed (commit 37743e6)
- ✅ Tests pass reliably without state corruption when UV_PYTHON is set

**Unresolved:**
- ❌ Intermittent failures in run_all_tests.sh (different tests fail non-deterministically)
- ❌ Error messages not captured (empty stderr despite exit code 1)
- ❌ Failures specific to `uv run` execution vs bare `python3`

**Next Investigation Needed:**
- Capture actual error details from failed runs (improved logging deployed, awaiting failure reproduction)
- Determine exact mechanism causing uv run vs python3 difference
- Identify why different tests fail on different runs

---

## 2025-11-12 Investigation Update (Post-Enhancement)

### PR/Local Code Mismatch Discovery

**Critical Finding:**
- PR #1 HEAD: commit b149c18 (2025-11-12T01:21:49Z)
- Local HEAD: commit 2e1a18b (5 commits ahead)
- **Impact:** CI tests code WITHOUT commits 37743e6 (claimed fix), 2e1a18b (error diagnostics)

**CI Status (testing b149c18):**
- All Unix platforms (Ubuntu/macOS): FAILURE
- All Windows platforms: SUCCESS
- Pattern matches documentation (Unix-only failures)

### Local Test Results (10-Iteration Run on 2e1a18b)

**Test Command:** `./tests/run_all_tests.sh 10` (old external script)
**Environment:** macOS, local HEAD (2e1a18b), all "fix" commits included
**Results:** 6/10 FAILED (60% failure rate), 4/10 PASSED (40%)

**Failure Clustering Pattern:**
- Iterations 1-6: All failed consecutively
- Iterations 7-10: All passed consecutively
- **Suggests:** State accumulation, not random failures

**Root Causes Identified from stdout logs:**

1. **Virtual Environment Corruption:**
```
dyld: Library not loaded: @executable_path/../lib/libpython3.12.dylib
Reason: tried: '.../src_layout_pkg_with_relative_imports/.venv/lib/libpython3.12.dylib' (no such file)
SIGABRT (signal 6)
```
- Affects `src_layout_pkg_with_relative_imports` test projects
- Appears in ALL failed iterations

2. **Invalid Package Names:**
```
error: The current directory (`pyuvstarter_test_notebook_pip_commands_ajtix80_`) is not a valid package name
```
- `uv init` rejects underscore-suffixed test directory names (random suffix from mkdtemp)

### Enhancements Implemented (Commit TBD)

**1. Multi-Run Test Infrastructure (tests/run_all_tests.sh)**
- Added multi-run mode: `./tests/run_all_tests.sh 10` for debugging intermittent failures
- DRY refactoring: extracted `run_single_test()`, `add_xml_testcases()`, `exit_with_summary()`
- Added input validation and `--help` flag
- Enhanced JUnit XML with `<properties>` for GitHub Actions (iteration number, UV_PYTHON, GITHUB_RUN_ID)
- Shellcheck clean (0 warnings)

**2. Automatic Log Preservation (tests/test_utils.py:100-119)**
- Copies JSON logs before temp directory cleanup
- Unique filenames: `iteration_02_fixture_name_pyuvstarter_setup_log.json`
- Activated automatically via PYUVSTARTER_CURRENT_ITERATION env var
- Fail-safe: doesn't break tests if copy fails

**3. Comprehensive Tracing (pyuvstarter.py)**

**Enhanced JSON logs now include:**
- `invocation_context.command_line` - Full command that started pyuvstarter
- `invocation_context.cli_parameters` - All CLI flags (via Pydantic model_dump(mode="json"))
- `invocation_context.original_working_directory` - Where command was run
- `invocation_context.environment_variables` - UV_PYTHON, PYUVSTARTER_CURRENT_ITERATION, etc.

**Crash-Safe Logging Architecture:**
- DRY write function: `_write_log_to_disk()` with explicit flush() and fsync()
- Checkpoint saves: `_save_log(config, checkpoint=CHECKPOINT_SAVE)` at ALL 7 critical exit points
- Named constants: `CHECKPOINT_SAVE` (error mode) vs `FINAL_SAVE` (normal mode)
- Atexit fallback: Ultimate safety for unexpected termination
- Write frequency: 1x success path (efficient), 2x error path (comprehensive)

**Applied 2025 Best Practices:**
- Typer 0.20: `pretty_exceptions_show_locals=False` (security: no sensitive data in tracebacks)
- Pydantic 2.12: `model_dump(mode="json")` (JSON-safe serialization)

### Verification Status

**Test Infrastructure:**
- ✅ Multi-run mode working (verified with 2-iteration test)
- ✅ JSON logs preserved with unique names
- ✅ XML reports include environment properties
- ✅ All code DRY compliant and shellcheck clean

**Root Cause Investigation:**
- ⏳ 10-iteration test running with enhanced logging
- ⏳ Will verify invocation_context data in JSON logs
- ⏳ Will analyze failure patterns with complete tracing

**Outstanding Questions:**
- Why does libpython3.12.dylib go missing from venv?
- Why does clustering occur (6 consecutive failures, then 4 consecutive passes)?
- Are test directory names causing uv init failures systematically?
