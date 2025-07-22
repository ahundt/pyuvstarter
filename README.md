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


![pyuvstarter demo v0.2.0 Demo showing pyuvstarter automatically discovering and installing 20+ hidden dependencies from a legacy Python ML project, including imports from Jupyter notebooks, handling comments in requirements.txt, and creating a modern reproducible environment with pyproject.toml](https://github.com/user-attachments/assets/af8c45ff-c97b-4c95-a11f-c58024cfecec)


Watch `pyuvstarter` rescue a legacy ML project by automatically finding ALL dependencies (even those hidden in notebooks), fixing incorrect package names, and creating a modern reproducible environment - all in under 30 seconds.

## Is `pyuvstarter` for You?

`pyuvstarter` is designed to be a valuable assistant for any Python developer, whether you're building from scratch or upgrading an existing codebase.

*   **For Modernizing Existing Projects:** Do you have an old project with a messy `requirements.txt`? Run `pyuvstarter` in its directory. It handles real-world requirements files (inline comments, package extras like `requests[security]`), discovers every dependency in your code and notebooks, and builds a fresh environment managed by `pyproject.toml`.

*   **For Starting New Projects:** Get a new web app, CLI, or data analysis project off the ground instantly. `pyuvstarter` provides a clean slate with a `pyproject.toml`, a virtual environment, and all the necessary configurations, so you can start coding immediately.

*   **For Data Scientists & ML Engineers:** Stop wrestling with notebook-only `!pip install` cells. `pyuvstarter` detects these installations, adds them to a central `pyproject.toml`, and ensures your analysis environment is robust and truly reproducible for yourself, your team, and your production pipeline.

## The `pyuvstarter` Philosophy

`pyuvstarter` is opinionated to promote modern best practices:

1.  **`pyproject.toml` is the Single Source of Truth:** All dependencies and project metadata should live here. `pyuvstarter` helps you get everything into this file.
2.  **Environments Must Be Isolated:** Every project gets its own `.venv` directory.
3.  **Dependencies Should Be Explicit:** The script helps you find what you're *actually* using and add it to your project configuration.
4.  **Automation Should Be Transparent:** Every action `pyuvstarter` takes is logged to `pyuvstarter_setup_log.json` for full visibility.

### Why Not Just Use `uv` Directly?
You absolutely can! `uv` is a phenomenal low-level tool. `pyuvstarter` acts as a higher-level **orchestrator** that chains `uv` commands together with other best-practice tools like `pipreqs` and `ruff`. It automates the *workflow* of discovery, migration, and configuration that you would otherwise have to perform manually.

## What `pyuvstarter` Does For You: A Detailed Workflow

When you run `pyuvstarter` on a new or existing project directory, it performs a comprehensive setup sequence:

1.  **Establishes a Modern Foundation:** It checks for a `pyproject.toml` file. If one doesn't exist, `pyuvstarter` runs `uv init` to create it. If one does exist, it uses it as the foundation.

2.  **Creates an Isolated, High-Speed Environment:** It runs `uv venv` to create a local `.venv` directory.

3.  **Discovers Every Dependency, Everywhere:** `pyuvstarter` meticulously scans your project to find every package you need.
    *   **For `.py` files,** it uses [`pipreqs`](https://github.com/bndr/pipreqs) to analyze `import` statements.
    *   **For Jupyter Notebooks (`.ipynb`),** it uses a robust two-stage process:
        1.  **Primary Method:** It uses `jupyter nbconvert` to safely convert notebooks to Python scripts for the most accurate analysis.
        2.  **Fallback Method:** If `jupyter` isn't available, `pyuvstarter` parses the raw notebook file, using AST for `import` statements and regex to catch `!pip install` commands.

4.  **Manages and Installs Your Full Dependency Tree:**
    *   It intelligently migrates packages from a legacy `requirements.txt` file based on your chosen strategy.
    *   It adds all discovered dependencies to your `pyproject.toml` using `uv add`.
    *   It installs necessary notebook execution tools like `ipykernel` and `jupyter` if notebooks are present.
    *   Finally, it runs `uv sync` to install the complete, resolved set of packages into your `.venv` and creates a `uv.lock` file for perfect, byte-for-byte reproducibility.

5.  **Configures and Cleans Your Tooling:**
    *   It runs [`ruff`](https://docs.astral.sh/ruff/) to detect and warn you about unused imports.
    *   It creates or updates a comprehensive `.gitignore` file.
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

You can run `pyuvstarter` with the following options:

-   `pyuvstarter [project_dir]`
    Run setup in the specified `project_dir`. Defaults to the current directory.

-   `pyuvstarter --version`
    Print the installed version of `pyuvstarter` and exit.

-   `--dependency-migration {auto,all-requirements,only-imported,skip-requirements}`
    Strategy for handling an existing `requirements.txt` file.
    *   `'auto'` (default): Intelligently migrates `requirements.txt` entries only if they are actively imported, and adds all other imported packages.
    *   `'all-requirements'`: Migrates every single entry from `requirements.txt` as-is, and then adds any additional discovered imported packages.
    *   `'only-imported'`: Only migrates `requirements.txt` entries that are actively imported, and adds all other imported packages.
    *   `'skip-requirements'`: Ignores `requirements.txt` entirely and relies solely on discovering dependencies from `import` statements.

**Examples:**

```bash
# Run in the current directory
pyuvstarter

# Run in a specific directory
pyuvstarter /path/to/your/project

# Show version
pyuvstarter --version

# Migrate all requirements.txt entries, even if unused
pyuvstarter --dependency-migration all-requirements

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
*   **`pyuvstarter_setup_log.json`**: A detailed log of every action the script performed.

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

### Common Issues

*   If `uv` or other tools fail to install, check the console output for hints.
*   If `pipreqs` misidentifies a dependency, you can manually edit `pyproject.toml` and then run `uv sync` to add the correct package or `uv remove <incorrect-package>` to remove it.
*   **For notebook issues:** The script's most reliable detection method requires `jupyter`. If it's missing, `pyuvstarter` uses a fallback parser. For best results, install it via `uv pip install jupyter`.
*   Always check the `pyuvstarter_setup_log.json` file for detailed error messages.

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
- `tests/` - Integration tests for core functionality
- `create_demo.sh --unit-test` - Comprehensive test suite including notebook parsing
- `create_demo2.sh --unit-test` - Extended tests with edge cases

#### Run Tests Locally
```bash
# Run all integration tests
./tests/run_all_tests.sh

# Run specific tests
./tests/test_new_project.sh      # Empty project initialization
./tests/test_legacy_migration.sh  # Requirements.txt migration

# Run comprehensive test suites (recommended)
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

This project (`pyuvstarter`) is licensed under the Apache License, Version 2.0.

Copyright 2025 Andrew Hundt. Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0).

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.