# pyuvstarter

**Tired of tedious Python project setup? `pyuvstarter` is here to streamline your workflow, whether you're starting a new project or modernizing an existing one!**

This script supercharges your Python project initialization by leveraging [`uv`](https://astral.sh/uv) – an extremely fast Python package manager from Astral. `pyuvstarter` automates the creation of a robust, modern Python environment, centered around `pyproject.toml` for dependency management. It's designed to get you coding faster by handling the foundational setup.

**Why should you care?**

* **Speed & Efficiency:** Launch new projects or update existing ones in seconds with `uv`'s blazing-fast environment creation and package operations.
* **Modern Standards:** Automatically sets up your project with `pyproject.toml` and `uv.lock` for reproducible and reliable dependency management, aligning with current Python best practices.
* **Smart Automation for New & Existing Projects with steps to avoid breaking them:**
    * For existing projects, it can migrate dependencies from legacy `requirements.txt` files into your `pyproject.toml`.
    * Scans your code for imports using [`pipreqs`](https://github.com/bndr/pipreqs) and automatically adds discovered dependencies to `pyproject.toml` via `uv add`.
    * Identifies unused imports using [`ruff`](https://docs.astral.sh/ruff/) to help you keep your dependency list clean and efficient.
    * Sets up a `.gitignore` file with sensible defaults.
    * Configures VS Code to use the new project environment.
* **Reproducibility & Auditing:** Generates a detailed JSON log (`pyuvstarter_setup_log.json`) of every action, making troubleshooting and understanding the setup process transparent.
* **Non-Interactive by Default:** Designed for a smooth, "standard run" experience without interrupting you with prompts.

In short, `pyuvstarter` handles the boilerplate, so you can focus on coding, whether it's a brand-new idea or an established codebase.

## Features

* **`uv` Integration:**
    * Ensures `uv` is installed on the system (with platform-aware installation attempts if missing).
    * Uses `uv init` to create or verify a `pyproject.toml` file.
    * Conditionally removes `main.py` if `uv init` creates it in a directory that already contained other Python files, respecting existing project structures.
    * Creates a virtual environment (default: `.venv`) using `uv venv`.
    * Manages dependencies through `pyproject.toml` using `uv add`.
    * Synchronizes the environment with `pyproject.toml` and `uv.lock` using `uv sync`.
    * Installs necessary CLI tools (like `pipreqs` and `ruff`) using `uv tool install`.
* **Dependency Management:**
    * Treats `pyproject.toml` as the primary source of truth for dependencies.
    * Migrates dependencies from an existing `requirements.txt` file (if present) into `pyproject.toml` using `uv add`. The original `requirements.txt` is left untouched, and the user is advised on its management.
    * Uses [`pipreqs`](https://github.com/bndr/pipreqs) (via `uvx`) to scan project source code for imported packages.
    * Automatically adds newly discovered, undeclared dependencies to `pyproject.toml` using `uv add`.
    *  [`ruff`](https://docs.astral.sh/ruff/) provides pre-flight unused import detection** (F401), warning users about potentially unneeded dependencies.
* **IDE & Version Control:**
    * Configures VS Code's Python interpreter path in `.vscode/settings.json` and `.vscode/launch.json`.
    * Ensures a `.gitignore` file exists with common Python, virtual environment, and OS-specific exclusions, also ignoring the script's own JSON log file.
* **Automation & Logging:**
    * Runs non-interactively, making sensible default choices.
    * Generates a detailed `pyuvstarter_setup_log.json` file for traceability and debugging.
    * Provides clear console output and includes "Next Steps" guidance in both console and the JSON log.

## How to Use `pyuvstarter`

### 1. Prerequisites for Running `pyuvstarter`

* **Python 3:** Preferably 3.8+ to run the `pyuvstarter.py` script. Python 3.11+ is recommended for the best experience with `pyproject.toml` parsing using the built-in `tomllib`.
* **`uv`:** `pyuvstarter` will attempt to install `uv` if it's not found on your system. This requires:
    * **macOS:** Homebrew (`brew`) is preferred, or `curl`.
    * **Linux:** `curl`.
    * **Windows:** PowerShell.
* **Git:** If you plan to install `pyuvstarter` itself from a Git repository (see below).

### 2. Installing `pyuvstarter` as a Command-Line Tool (Recommended)

Once this `pyuvstarter` project is available in a public Git repository (e.g., on GitHub), you can install it as a command-line tool using `uv` itself:

1.  **Ensure `uv` is installed on your system.** If not, `pyuvstarter` (when run for the first time on another project) can help install it, or you can install `uv` manually from [astral.sh](https://astral.sh/uv).
2.  **Install `pyuvstarter` using `uv tool install`:**
    ```bash
    uv tool install git+https://github.com/ahundt/pyuvstarter.git
    ```
    For this to work seamlessly and make `pyuvstarter` directly callable, the `pyproject.toml` file within the `pyuvstarter` project should define an entry point for the script, like:
    ```toml
    # In pyuvstarter's own pyproject.toml
    [project.scripts]
    pyuvstarter = "pyuvstarter:main"
    ```
3.  **Ensure `uv`'s tool binaries directory is in your PATH:**
    `uv tool install` places executables in a directory managed by `uv` (often `~/.local/bin` on Linux/macOS or a similar user-specific path). `uv` usually provides instructions to add this to your PATH if it's not already there. You can also run:
    ```bash
    uv tool update-shell
    ```
    Then, restart your terminal or source your shell configuration file (e.g., `.bashrc`, `.zshrc`).

After these steps, you should be able to run `pyuvstarter` from any directory.

**Alternative Installation (from a local clone):**

```bash
# 1. Clone the repository (if you haven't already)
git clone https://github.com/ahundt/pyuvstarter.git
cd pyuvstarter

# 2. Install pyuvstarter as a uv tool
uv tool install .

# 3. (Optional) Force reinstall if you want to overwrite an existing install
uv pip install .
```

**Uninstall pyuvstarter**

```bash
uv tool uninstall pyuvstarter
uv pip uninstall pyuvstarter
```

### 3. Running `pyuvstarter` to Set Up a Project

Once `pyuvstarter` is installed and available in your PATH:

1.  **Navigate to your target project's root directory** (this can be an empty directory for a new project or an existing project you want to set up with `uv`).
2.  **Run the command:**
    ```bash
    pyuvstarter
    ```

The script will then perform all its automated setup actions in that directory.

*(If you haven't installed `pyuvstarter` system-wide, you would place the `pyuvstarter.py` script directly into your target project's root directory, make it executable (`chmod +x pyuvstarter.py` on Linux/macOS), and run it with `./pyuvstarter.py` or `python3 pyuvstarter.py` from within that directory.)*

### Command-Line Arguments

You can run `pyuvstarter` with the following options:

- `pyuvstarter [project_dir]`
  Run setup in the specified `project_dir`. If omitted, uses the current directory.

- `pyuvstarter --version`
  Print the installed version of `pyuvstarter` and exit.

- `--dependency-migration {auto,all-requirements,only-imported,skip-requirements}`
  Strategy for handling `requirements.txt`.
    * `'auto'` (default): Intelligently migrates `requirements.txt` entries only if they are actively imported, and adds all other imported packages. Warns about unused `requirements.txt` entries.
    * `'all-requirements'`: Migrates every single entry from `requirements.txt` as-is, and then adds any additional discovered imported packages.
    * `'only-imported'`: Only migrates `requirements.txt` entries that are actively imported, and adds all other imported packages.
    * `'skip-requirements'`: Ignores `requirements.txt` entirely and relies solely on discovering dependencies from `import` statements.

- `--dry-run`
  Preview all actions without making any changes to the project's files or environment.

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

# Perform a dry-run to see what would happen
pyuvstarter --dry-run
```

## Expected Outcome After `pyuvstarter` Runs

* A `pyproject.toml` file will define your project's dependencies.
* A `.gitignore` file will be present.
* A `.venv/` directory will contain the Python virtual environment.
* A `uv.lock` file will ensure reproducible dependency installations.
* Dependencies (migrated, declared, and discovered) will be installed.
* `.vscode/settings.json` and `.vscode/launch.json` will be configured for vscode.
* A `pyuvstarter_setup_log.json` file will detail the script's operations.
* The console output (and the JSON log) will provide "Next Steps" guidance.

## Typical "Next Steps" After Running `pyuvstarter`

1.  **Reload VS Code:** If your project was already open in VS Code, reload the window (`Ctrl+Shift+P` or `Cmd+Shift+P`, then type "Developer: Reload Window").
2.  **Activate Virtual Environment:** In your terminal, activate the virtual environment:
    * Linux/macOS: `source .venv/bin/activate`
    * Windows (PowerShell): `.\.venv\Scripts\activate`
3.  **Review & Test:**
    * Examine `pyproject.toml` and `uv.lock`.
    * Review the generated `.gitignore`.
    * Test your project thoroughly.
4.  **Commit to Version Control:**
    * Commit `pyproject.toml`, `uv.lock`, `.gitignore`, and your project's source code.
    * If `pyuvstarter` itself is part of this project (not installed globally), commit it too.
    * **Do NOT commit** `.venv/` or `pyuvstarter_setup_log.json`.

## Troubleshooting

* If `uv` or `pipreqs`/`ruff` installation (done by `pyuvstarter`) fails, the script will provide error messages and hints.
* If `pipreqs` misidentifies dependencies, manually edit `pyproject.toml` and use `uv add <correct-package>` or `uv remove <incorrect-package>`, then `uv sync`.
* Always check `pyuvstarter_setup_log.json` for detailed error messages.

## License

This project (`pyuvstarter.py`) is licensed under the Apache License, Version 2.0.

Copyright 2025 Andrew Hundt Licensed under the Apache License, Version 2.0 (the "License");you may not use this file except in compliance with the License.You may obtain a copy of the License at[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS,WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.See the License for the specific language governing permissions and limitations under the License.
