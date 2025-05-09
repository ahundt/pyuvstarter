# pyuvstarter.py

`pyuvstarter.py` is a Python script designed to automate the setup of a modern Python project environment. It leverages `uv` (an extremely fast Python package installer and resolver) as its core engine, focuses on `pyproject.toml` for dependency management, configures Visual Studio Code for the project, and prepares the project for version control by ensuring a sensible `.gitignore` file is present.

The script operates in a non-interactive "standard run" mode, making decisions automatically to streamline the setup process. It also generates a detailed JSON log (`pyuvstarter_setup_log.json`) of all actions performed, which is invaluable for troubleshooting and auditing.

## Features

* **`uv` Integration:**
    * Ensures `uv` is installed on the system (with platform-aware installation attempts if missing).
    * Uses `uv init` to create or verify a `pyproject.toml` file.
    * Conditionally removes `main.py` if `uv init` creates it in a directory that already contained other Python files, respecting existing project structures.
    * Creates a virtual environment (default: `.venv`) using `uv venv`.
    * Manages dependencies through `pyproject.toml` using `uv add`.
    * Synchronizes the environment with `pyproject.toml` and `uv.lock` using `uv sync`.
    * Installs necessary CLI tools (like `pipreqs`) using `uv tool install`.
* **Dependency Management:**
    * Treats `pyproject.toml` as the primary source of truth for dependencies.
    * Migrates dependencies from an existing `requirements.txt` file (if present) into `pyproject.toml` using `uv add`. The original `requirements.txt` is left untouched, and the user is advised on its management.
    * Uses `pipreqs` (via `uvx`) to scan project source code for imported packages.
    * Automatically adds newly discovered, undeclared dependencies to `pyproject.toml` using `uv add`.
* **IDE & Version Control:**
    * Configures VS Code's Python interpreter path in `.vscode/settings.json`.
    * Ensures a `.gitignore` file exists with common Python, virtual environment, and OS-specific exclusions, also ignoring the script's own JSON log file.
* **Automation & Logging:**
    * Runs non-interactively, making sensible default choices.
    * Generates a detailed `pyuvstarter_setup_log.json` file for traceability and debugging.
    * Provides clear console output and includes "Next Steps" guidance in both console and the JSON log.

## How to Use

1.  **Prerequisites:**
    * Python 3 installed (Python 3.11+ is recommended for the best experience with `pyproject.toml` parsing using the built-in `tomllib`).
    * System tools for `uv` installation if `uv` is not already installed:
        * **macOS:** Homebrew (`brew`) is preferred for `uv` installation. If Homebrew is not available, `curl` will be used.
        * **Linux:** `curl` is required.
        * **Windows:** PowerShell is required.
    * (Optional) An existing `requirements.txt` file if you are migrating an older project.

2.  **Placement:**
    * Save the `pyuvstarter.py` script in the root directory of your new or existing Python project.

3.  **Execution:**
    * Open your terminal or command prompt.
    * Navigate to the project root directory (where `pyuvstarter.py` is located).
    * **On Linux/macOS, make the script executable (one-time setup):**
        ```bash
        chmod +x pyuvstarter.py
        ```
    * **Run the script:**
        ```bash
        ./pyuvstarter.py
        ```
        Alternatively, on any OS, you can run it with:
        ```bash
        python3 pyuvstarter.py
        ```
        (Use `python` instead of `python3` if that's how your Python 3 interpreter is aliased).

## Expected Outcome

After the script runs successfully:

* A `pyproject.toml` file will be present and will define your project's dependencies.
* A `.gitignore` file will be present, configured with useful defaults.
* A `.venv/` directory (or your chosen name) will contain the isolated Python virtual environment.
* A `uv.lock` file will exist, ensuring reproducible dependency installations.
* All declared and discovered dependencies will be installed in the virtual environment.
* If you have VS Code, `.vscode/settings.json` will be configured to use the new virtual environment's interpreter.
* A `pyuvstarter_setup_log.json` file will provide a detailed record of the script's operations.
* The console output (and the JSON log) will provide "Next Steps" guidance.

## Typical "Next Steps" After Running

1.  **Reload VS Code:** If your project was already open in VS Code, reload the window (`Ctrl+Shift+P` or `Cmd+Shift+P`, then type "Developer: Reload Window") for changes to take full effect.
2.  **Activate Virtual Environment:** In your terminal, activate the virtual environment:
    * Linux/macOS: `source .venv/bin/activate`
    * Windows (PowerShell): `.\.venv\Scripts\activate`
3.  **Review & Test:**
    * Examine `pyproject.toml` and `uv.lock` to ensure dependencies are correctly listed.
    * Review the generated `.gitignore`.
    * Test your project thoroughly to confirm everything works as expected with the new environment.
4.  **Commit to Version Control:**
    * Commit `pyproject.toml`, `uv.lock`, `.gitignore`, your project's source code, and `pyuvstarter.py` itself (if you want it versioned with the project).
    * **Do NOT commit** the `.venv/` directory or the `pyuvstarter_setup_log.json` file (they are included in the default `.gitignore`).

## Troubleshooting

* If `uv` or `pipreqs` installation fails, the script will provide error messages and hints. You might need to install system prerequisites like `curl` or Homebrew manually.
* If `pipreqs` fails to discover a dependency or maps an import name incorrectly, you may need to manually add the correct package to `pyproject.toml` using `uv add <package-name>`.
* Always check the `pyuvstarter_setup_log.json` file for detailed error messages and the sequence of operations if the script doesn't behave as expected.

## License

This project (`pyuvstarter.py`) is licensed under the Apache License, Version 2.0.

Copyright 2025 Andrew Hundt Licensed under the Apache License, Version 2.0 (the "License");you may not use this file except in compliance with the License.You may obtain a copy of the License at[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS,WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.See the License for the specific language governing permissions and limitations under the License.
