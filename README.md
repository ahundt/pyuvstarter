# pyuvstarter

<!--
README Badges: These provide at-a-glance project health.
The "Build Status" and "License" badges will work once you push the `ci.yml` and `LICENSE` files to GitHub.
The PyPI-related badges are commented out until you publish the package.
-->
<!-- GitHub Actions CI: This badge requires a workflow file at .github/workflows/ci.yml -->
[![Build Status](https://img.shields.io/github/actions/workflow/status/ahundt/pyuvstarter/ci.yml?style=flat-square)](https://github.com/ahundt/pyuvstarter/actions)
<!-- GitHub License: This badge reads your LICENSE file directly from the repository. -->
[![License](https://img.shields.io/github/license/ahundt/pyuvstarter?style=flat-square)](https://github.com/ahundt/pyuvstarter/blob/main/LICENSE)
<!--
The following badges will only work after you publish your package to PyPI.
To enable them, publish your package and then remove the comment markers.
[![PyPI version](https://img.shields.io/pypi/v/pyuvstarter.svg?style=flat-square)](https://pypi.python.org/pypi/pyuvstarter)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyuvstarter.svg?style=flat-square)](https://pypi.python.org/pypi/pyuvstarter)
-->

**From Zero to a Reproducible Python Project in Seconds.**

Stop fighting with broken environments, outdated `requirements.txt` files, and the "it works on my machine" curse. `pyuvstarter` is an opinionated script that automates the creation of a robust, modern, and production-ready Python project foundation using [`uv`](https://astral.sh/uv), the blazing-fast package manager from Astral.

Whether you are starting a new application or modernizing a years-old codebase, `pyuvstarter` handles the tedious boilerplate of project setup, so you can start writing code that matters.

## Quick Look


![pyuvstarter demo v0.3.0 Demo showing pyuvstarter automatically discovering and installing 20+ hidden dependencies from a legacy Python ML project, including imports from Jupyter notebooks, handling comments in requirements.txt, and creating a modern reproducible environment with pyproject.toml](https://github.com/user-attachments/assets/af8c45ff-c97b-4c95-a11f-c58024cfecec)


Watch `pyuvstarter` rescue a legacy ML project by discovering dependencies from `.py` files and Jupyter notebooks (including those from `!pip install` cells), fixing incorrect package names, and creating a modern reproducible environment - all in under 30 seconds.

## Is `pyuvstarter` for You?

`pyuvstarter` is designed to be a valuable assistant for any Python developer, whether you're building from scratch or upgrading an existing codebase.

*   **For Modernizing Existing Projects:** Do you have an old project with a messy `requirements.txt`? Run `pyuvstarter` in its directory. It handles real-world requirements files (inline comments, package extras like `requests[security]`), discovers dependencies in your code and notebooks, and builds a fresh environment managed by `pyproject.toml`.

*   **For Starting New Projects:** Get a new web app, CLI, or data analysis project off the ground instantly. `pyuvstarter` provides a clean slate with a `pyproject.toml`, a virtual environment, and all the necessary configurations, so you can start coding immediately.

*   **For Data Scientists & ML Engineers:** Stop wrestling with notebook-only `!pip install` cells. `pyuvstarter` detects these installations, adds them to a central `pyproject.toml`, and helps make your analysis environment more robust and reproducible for yourself, your team, and your production pipeline.

## The `pyuvstarter` Philosophy

`pyuvstarter` is opinionated to promote modern best practices:

1.  **`pyproject.toml` is the Single Source of Truth:** All dependencies and project metadata should live here. `pyuvstarter` helps you get everything into this file.
2.  **Environments Must Be Isolated:** Every project gets its own `.venv` directory.
3.  **Dependencies Should Be Explicit:** The script helps you find what you're *actually* using and add it to your project configuration.
4.  **Automation Should Be Transparent:** Every action `pyuvstarter` takes is logged to `pyuvstarter_setup_log.json` for full visibility.

### Why Not Just Use `uv` Directly?
You absolutely can! `uv` is a powerful low-level tool. `pyuvstarter` acts as a higher-level **orchestrator** that chains `uv` commands together with other best-practice tools like `pipreqs` and `ruff`. It automates the *workflow* of discovery, migration, and configuration that you would otherwise have to perform manually.

## What `pyuvstarter` Does For You: A Detailed Workflow

When you run `pyuvstarter` on a new or existing project directory, it performs this setup sequence:

1.  **Establishes a Modern Foundation:** It checks for a `pyproject.toml` file. If one doesn't exist, `pyuvstarter` runs `uv init` to create it. If one does exist, it uses it as the foundation.

2.  **Creates an Isolated, High-Speed Environment:** It runs `uv venv` to create a local `.venv` directory.

3.  **Discovers Dependencies:** `pyuvstarter` scans your project to find imported packages.
    *   **For `.py` files,** it uses [`pipreqs`](https://github.com/bndr/pipreqs) to analyze `import` statements.
    *   **For Jupyter Notebooks (`.ipynb`),** it uses a two-stage process:
        1.  **Primary Method:** Uses `jupyter nbconvert` to convert notebooks to Python scripts for analysis.
        2.  **Fallback Method:** If `jupyter` isn't available, parses the raw notebook file using AST for `import` statements and regex for `!pip install` commands.

4.  **Manages and Installs Your Full Dependency Tree:**
    *   It migrates packages from a legacy `requirements.txt` file based on your chosen strategy.
    *   It adds all discovered dependencies to your `pyproject.toml` using `uv add`.
    *   It installs necessary notebook execution tools like `ipykernel` and `jupyter` if notebooks are present.
    *   Finally, it runs `uv sync` to install the complete, resolved set of packages into your `.venv` and creates a `uv.lock` file for byte-for-byte reproducibility.

5.  **Configures and Cleans Your Tooling:**
    *   It runs [`ruff`](https://docs.astral.sh/ruff/) to detect and warn you about unused imports.
    *   It creates or updates `.gitignore` with common Python project patterns.
    *   It configures VS Code by creating or updating `.vscode/settings.json` and `.vscode/launch.json`.

## How to Use `pyuvstarter`

### 1. Prerequisites

*   **Python 3:** Requires 3.11 or newer.
*   **`uv`:** The script will attempt to install `uv` if it's not found. This requires:
    *   **macOS:** Homebrew (`brew`) is preferred, or `curl`.
    *   **Linux:** `curl`.
    *   **Windows:** PowerShell.
*   **Git:** Required to install `pyuvstarter` from its repository.

### 2. Quick Try (No Installation)

Want to try `pyuvstarter` without installing? Use [`uvx`](https://docs.astral.sh/uv/guides/tools/#running-tools) to run it directly:

```bash
# Run pyuvstarter directly from GitHub
uvx --from git+https://github.com/ahundt/pyuvstarter.git pyuvstarter
```

This downloads and runs `pyuvstarter` in an isolated environment without permanently installing it.

### 3. Installation

For regular use, we recommend installing `pyuvstarter` as a command-line tool via `uv`.

#### Option 1: As a Command-Line Tool (Recommended)

1.  **Ensure `uv` is installed.** If not, you can install it from [astral.sh](https://astral.sh/uv).

2.  **Install the tool.** Before running, check the project's GitHub page for the latest version tag to ensure you're installing a stable release.
    ```bash
    # Replace vX.Y.Z with the latest stable version tag from the repository
    uv tool install git+https://github.com/ahundt/pyuvstarter.git@vX.Y.Z
    ```

3.  **Ensure `uv`'s tool directory is in your `PATH`**. If the `pyuvstarter` command isn't found, run `uv tool update-shell`, then restart your terminal.

#### Option 2: From a Local Clone
```bash
# 1. Clone the repository (if you haven't already)
git clone https://github.com/ahundt/pyuvstarter.git
cd pyuvstarter

# 2. Install pyuvstarter as a uv tool
uv tool install .

# 3. (Optional) Force reinstall if you want to overwrite an existing install
uv tool install . --force
```

#### Uninstalling
```bash
uv tool uninstall pyuvstarter
uv pip uninstall pyuvstarter
```

### 4. Running `pyuvstarter`

*   **If installed as a tool:** Navigate to your project's root directory and run:
    ```bash
    pyuvstarter
    ```
*   **If running from a local clone:** Navigate to the cloned pyuvstarter directory and run:
    ```bash
    uv run pyuvstarter
    ```

### Command-Line Arguments

#### Basic Usage

```bash
pyuvstarter [project_dir] [options]
```

#### Core Options

-   `project_dir`
    Project directory to operate on. Defaults to current directory if not specified.

-   `--version`
    Show installed version and exit.

-   `--verbose, -v`
    Show detailed technical output for debugging and learning.

#### Dependency Management

-   `--dependency-migration {auto,all-requirements,only-imported,skip-requirements}`
    Strategy for handling existing `requirements.txt` files:
    *   `'auto'` (default): Migrates `requirements.txt` entries only if actively imported, plus all discovered imports
    *   `'all-requirements'`: Migrates every `requirements.txt` entry, plus discovered imports
    *   `'only-imported'`: Migrates only `requirements.txt` entries that are imported, plus discovered imports
    *   `'skip-requirements'`: Ignores `requirements.txt`, uses only discovered imports

#### Customization Options

-   `--venv-name <name>`
    Name of virtual environment directory (default: `.venv`)

-   `--log-file-name <name>`
    Name of JSON log file (default: `pyuvstarter_setup_log.json`)

-   `--config-file <path>, -c <path>`
    Path to JSON configuration file with option presets

#### Gitignore Control

-   `--no-gitignore`
    Disable all `.gitignore` operations

-   `--full-gitignore-overwrite`
    Replace existing `.gitignore` completely instead of merging

-   `--gitignore-name <name>`
    Name of gitignore file (default: `.gitignore`)

-   `--ignore-pattern <pattern>, -i <pattern>`
    Additional gitignore patterns to add (can be specified multiple times)

#### Examples

```bash
# Run in current directory (most common)
pyuvstarter

# Run in specific directory
pyuvstarter /path/to/your/project

# Show detailed output for debugging
pyuvstarter --verbose

# Migrate all requirements.txt entries, even if unused
pyuvstarter --dependency-migration all-requirements

# Custom virtual environment name
pyuvstarter --venv-name my_venv

# Add custom patterns to .gitignore
pyuvstarter --ignore-pattern "*.tmp" --ignore-pattern "cache/"

# Completely replace existing .gitignore
pyuvstarter --full-gitignore-overwrite
```

## Expected Outcome: A Ready-to-Use Development Environment

After `pyuvstarter` finishes, your project is not just configured—it's ready for immediate development.

### Your New Capabilities
*   **Open the project in VS Code** and see that it automatically detects and uses the new `.venv/` Python interpreter.
*   **Get intelligent code completion, linting, and formatting** from `ruff` and other Python extensions, because the environment is set up correctly.
*   **Run and debug your code immediately.** You can open a Python file and use the default `F5` key (or the "Run and Debug" panel) to execute it.
*   **Activate and use the terminal** (`source .venv/bin/activate`) for any additional commands.
*   **Trust your dependency list**, as `pyproject.toml` will accurately reflect the packages your project actually uses.

### Created & Modified Files
The script achieves this by creating or modifying the following files in your project directory:
*   **`pyproject.toml`**: The central configuration file for your project's dependencies.
*   **`.venv/`**: The directory containing your isolated Python virtual environment.
*   **`uv.lock`**: The lock file that guarantees reproducible installations.
*   **`.gitignore`**: A file configured to ignore the virtual environment, logs, and other common artifacts.
*   **`.vscode/settings.json`**: Configures VS Code to use the correct Python interpreter.
*   **`.vscode/launch.json`**: Provides a default debug configuration.
*   **`pyuvstarter_setup_log.json`**: A detailed log of all actions the script performed.

## Typical Next Steps After Running `pyuvstarter`

1.  **Reload VS Code:** If the project was already open, reload the window (`Ctrl+Shift+P` > "Developer: Reload Window").
2.  **Activate Virtual Environment:**
    *   **Linux/macOS:** `source .venv/bin/activate`
    *   **Windows (PowerShell):** `.\.venv\Scripts\activate`
3.  **Review & Test:** Examine `pyproject.toml` and run your application or tests.
4.  **Commit to Version Control:** Commit `pyproject.toml`, `uv.lock`, `.gitignore`, and your source code. **Do NOT commit `.venv/`**.

## Contributing
Contributions are welcome! Please feel free to open an issue to report a bug or suggest a feature, or open a pull request to propose a change. See the project's issue tracker for ideas.

## Troubleshooting

### Error Handling Behavior

**Critical Failures (script stops):**
- `uv` installation fails → Install `uv` manually from [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)
- `pyproject.toml` creation fails → Check write permissions, resolve conflicts
- Virtual environment creation fails → Run `uv venv` manually for diagnostic output
- File permission errors → Adjust with `chmod` or use directory you control

**Partial Success (script continues):**
- Some packages fail → Installs successful packages; check `pyuvstarter_setup_log.json` → `failed_packages` for reasons
- Dependency discovery issues → Skips unparseable files; manually add missing packages with `uv add <package>`
- Notebook parsing failures → Skips corrupt notebooks; fix format or add dependencies manually
- Import fixing failures → Reports issues; manually fix complex relative imports

**Check diagnostic log:**
```bash
# View errors
cat pyuvstarter_setup_log.json | grep -A 5 '"status": "ERROR"'

# Check overall status: SUCCESS | COMPLETED_WITH_ERRORS | CRITICAL_FAILURE
grep '"overall_status"' pyuvstarter_setup_log.json
```

**Common package failure reasons:**
- "no Python 3.14 wheel" → Package not yet compatible; use older Python version
- "version conflict" → Adjust version constraints in `pyproject.toml`
- "package not found" → Verify package name spelling on PyPI

### Common Issues

*   If `uv` or other tools fail to install, check the console output for hints.
*   If `pipreqs` misidentifies a dependency, manually edit `pyproject.toml` and run `uv sync` to apply changes, or use `uv remove <incorrect-package>` to remove it.
*   **For notebook issues:** The most reliable detection requires `jupyter`. If missing, `pyuvstarter` uses a fallback parser that may miss some dependencies. Install with `uv pip install jupyter` for best results.
*   Always check the `pyuvstarter_setup_log.json` file for detailed error messages and specific failure reasons.

### Running pyuvstarter in Different Contexts

**Issue:** "command not found: pyuvstarter" or pyuvstarter creates files in the wrong directory.

**Background:** `pyuvstarter` can be run in several ways, each with different implications for where it's available and which directory it operates on:

1. **As a globally installed tool (Recommended)**
   ```bash
   # Install globally
   uv tool install git+https://github.com/ahundt/pyuvstarter.git
   # Run in any directory
   pyuvstarter .
   ```

2. **Using uvx (Quick try without installation)**
   ```bash
   # Run directly without installing
   uvx --from git+https://github.com/ahundt/pyuvstarter.git pyuvstarter .
   ```

3. **From within the pyuvstarter project directory**
   ```bash
   # If you've cloned pyuvstarter
   cd /path/to/pyuvstarter
   uv run pyuvstarter /path/to/your/project
   ```

**Important:** When using `uv run --directory <dir>`, be aware that this changes the working directory before executing the command. For example:
- `uv run --directory .. pyuvstarter` runs pyuvstarter with the parent directory as the working directory
- `uv run --directory .. pyuvstarter .` still operates on the parent directory (not the original directory)
- To specify the target directory explicitly: `uv run --directory .. pyuvstarter "$(pwd)"`

**Solution:** For most use cases, install pyuvstarter as a global tool (option 1) or use uvx (option 2) to avoid directory context issues.

## Developer Notes

### Prerequisites

Before running tests, ensure pyuvstarter is installed:
```bash
# Install pyuvstarter as a global tool
uv tool install .

# Verify installation
which pyuvstarter
```

### Running Tests

#### Test Structure

**Python Test Suite** (`tests/*.py`):
- `test_configuration.py` - Configuration management and CLI arguments
- `test_cross_platform.py` - Cross-platform compatibility (Windows, macOS, Linux)
- `test_dependency_migration.py` - Requirements.txt migration strategies
- `test_error_handling.py` - Error detection and graceful degradation
- `test_extraction_fix.py` - Package name extraction and canonicalization
- `test_import_fixing.py` - Import statement detection and relative import handling
- `test_jupyter_pipeline.py` - Jupyter notebook dependency discovery
- `test_mixed_package_availability.py` - Package availability edge cases
- `test_project_structure.py` - Flat vs src-layout project structure detection
- `test_utils.py` - Core utility functions and helpers
- `test_wheel_unavailability.py` - Python 3.14+ wheel unavailability handling

**Shell Test Scripts** (`tests/*.sh`):
- `run_all_tests.sh` - Main test runner for all integration tests
- `test_new_project.sh` - Empty project initialization
- `test_legacy_migration.sh` - Requirements.txt migration

**Comprehensive Test Suites**:
- `create_demo.sh --unit-test` - Comprehensive test suite including notebook parsing
- `create_demo2.sh --unit-test` - Extended tests with edge cases

#### Run Tests Locally

```bash
# Run Python test suite (pytest)
./tests/run_all_tests.sh

# Run specific Python test modules
python -m pytest tests/test_jupyter_pipeline.py -v
python -m pytest tests/test_import_fixing.py -v
python -m pytest tests/test_wheel_unavailability.py -v

# Run shell-based integration tests
./tests/test_new_project.sh
./tests/test_legacy_migration.sh

# Run comprehensive test suites (recommended for full validation)
./create_demo.sh --unit-test
./create_demo2.sh --unit-test
```

### CI Validation

Check workflow syntax before pushing:
```bash
# Install actionlint
brew install actionlint          # macOS/Linux with Homebrew
# Other platforms: https://github.com/rhysd/actionlint

# Validate workflows
actionlint                       # Basic check
actionlint -shellcheck          # With shell script validation
```

### Debugging Failed Tests

1. **Check logs**: Look for `pyuvstarter_setup_log.json` in the test directory
2. **Run verbose**: Set `PYUVSTARTER_LOG_LEVEL=DEBUG` before running tests
3. **Test isolation**: Tests create temporary directories to avoid conflicts
4. **Common issues**:
   - Missing dependencies: Run `uv sync` in the project root
   - Tool not found: Ensure `~/.local/bin` is in your PATH

## License

This project (`pyuvstarter`) is licensed under the Apache License, Version 2.0 and Copyright 2025 Andrew Hundt.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use pyuvstarter` except in compliance with the License. You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0).

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.