#!/usr/bin/env python3
"""
pyuvstarter.py (v7.0 - Enhanced Robustness & User Experience)

Copyright (c) 2025 Andrew Hundt

Purpose:
    Automates Python project and environment setup using `uv`, focusing on modern, reproducible, and user-friendly workflows.
    - Sets up `pyproject.toml` for dependency management.
    - Configures Visual Studio Code for the project.
    - Prepares the project for version control with a robust `.gitignore`.
    - Manages legacy `requirements.txt` dependencies and discovers new ones with robust configuration options.
    - **Detects dependencies in both Python scripts (`.py`) and Jupyter Notebooks (`.ipynb`).**
    - Ensures required CLI tools (e.g., pipreqs, ruff) are available via `uv tool install`.
    - Detects unused imports to advise on a cleaner dependency graph.
    - Logs all actions, errors, and next steps to a detailed JSON log.

Key Actions:
1. Ensures `uv` is installed (platform-aware, automatic installation if missing).
2. Ensures a `pyproject.toml` file exists, running `uv init` if necessary.
   - If `uv init` creates `main.py` in a project with existing Python files, `main.py` is removed.
3. Ensures a `.gitignore` file exists with common Python/venv/log exclusions.
4. Creates a virtual environment (default: '.venv') using `uv venv`.
5. Ensures necessary CLI tools (`pipreqs`, `ruff`) are installed via `uv tool install`.
6. Performs a pre-flight check for unused imports using `ruff` and warns the user.
7. Discovers packages imported in project source code:
   - **For `.py` files:** Uses `pipreqs` to find imports.
   - **For `.ipynb` files:** Uses a primary strategy of converting notebooks to Python scripts and analyzing with `pipreqs`. If that fails (e.g., `jupyter` not found), it uses a robust fallback strategy of parsing notebook JSON with `ast` (for imports) and `regex` (for `!pip install` commands).
8. Intelligently manages dependencies:
   - Reads existing dependencies from `pyproject.toml`.
   - Processes `requirements.txt` (if present) and all discovered dependencies based on the `--dependency-migration` mode:
     - `auto` (default): Migrates `requirements.txt` entries only if they are actively imported, and adds all other imported packages. Warns about unused `requirements.txt` entries.
     - `all-requirements`: Migrates all entries from `requirements.txt` and then adds any additional discovered imported packages.
     - `only-imported`: Explicitly migrates only `requirements.txt` entries that are actively imported, and adds all other imported packages.
     - `skip-requirements`: Ignores `requirements.txt` and only considers packages discovered from imports.
   - Adds newly identified dependencies to `pyproject.toml` using `uv add`.
9. **Ensures Notebook Execution Support:** If notebooks are found, it detects the required execution system (e.g., Jupyter) and installs necessary support packages like `ipykernel` if they aren't already declared.
10. Installs/syncs all declared dependencies from `pyproject.toml` and `uv.lock` using `uv sync`.
11. Configures VS Code's 'python.defaultInterpreterPath' and adds a generic launch configuration in '.vscode/settings.json' and 'launch.json'.
12. Logs all major actions, command executions, statuses, errors, and user guidance to 'pyuvstarter_setup_log.json' and prints them to the console.
13. Halts with clear, actionable error messages if a critical step fails (e.g., missing tool, venv creation failure).

How to Use:
1. Prerequisites:
   - Python 3 (Python 3.11+ recommended for full `pyproject.toml` parsing via `tomllib`).
   - System tools for `uv` installation if `uv` is not yet installed:
     - macOS: Homebrew (https://brew.sh/) preferred, or `curl`.
     - Linux: `curl`.
     - Windows: PowerShell.
   - (Optional) An existing 'requirements.txt' file if migrating an old project.

2. Placement:
   - Save this script as 'pyuvstarter.py' (or your preferred name) in the root directory of your new or existing Python project.

3. Execution:
   - Open your terminal or command prompt.
   - Navigate to the project root (the directory containing this script).
   - Make executable (Linux/macOS): `chmod +x pyuvstarter.py`
   - Run: `./pyuvstarter.py` (or `python3 pyuvstarter.py`)
   - Use `--help` to see additional options like `--dependency-migration` and `--dry-run`.

Outcome:
- A `pyproject.toml` will define project dependencies.
- A `.gitignore` file will be present.
- A '.venv' directory will contain the Python virtual environment.
- A `uv.lock` file will ensure reproducible dependency resolution.
- Dependencies (migrated, declared, and discovered from scripts and notebooks) will be installed.
- '.vscode/settings.json' and 'launch.json' will be configured for the venv interpreter.
- A 'pyuvstarter_setup_log.json' file will detail the script's execution, actions, errors, and next steps.
- The script will print recommended next steps to the console and include them in the JSON log if the script completes without critical failure.
- If a critical error occurs, the script will halt and print/log clear, actionable guidance.
- After pyuvstarter runs you should source the virtual environment in your terminal:
    - `source .venv/bin/activate` (Linux/macOS)
    - `.venv\\Scripts\\activate` (Windows PowerShell)
- Finally, commit to version control:

Committing to Git:
- After running, you should typically commit:
  - `pyuvstarter.py` (this script itself if it's part of the project)
  - `pyproject.toml`
  - `uv.lock`
  - `.gitignore`
  - Your actual project source code.
  - `.vscode/settings.json` and `.vscode/launch.json` (optional, if you want to share VS Code settings).
- Do NOT commit the `.venv/` directory or the `pyuvstarter_setup_log.json` file (this script adds them to `.gitignore`).


Installing and uninstalling pyuvstarter:

install pyuvstarter:
uv tool install .

Force reinstall (sorta works):

uv pip install --force-reinstall .


Uninstall pyuvstarter:

(hacky way to clear out pyuvstarter on mac when testing uv tool install . which is partly broken has problems like not removing the .venv and highlighting the name of the tool after uninstall):

uv tool uninstall pyuvstarter
uv pip uninstall pyuvstarter
find ~/.local/share/uv/tools ~/.cache/uv ~/.local/lib ~/.pyenv .venv -iname 'pyuvstarter*' -delete
"""

import sys
import json
import os
import shutil
import subprocess
import importlib
import datetime
import platform
import argparse
import re
import ast
import tempfile
import shlex

from pathlib import Path

# --- Configuration Constants ---
VENV_NAME = ".venv"
PYPROJECT_TOML_NAME = "pyproject.toml"
GITIGNORE_NAME = ".gitignore"
LEGACY_REQUIREMENTS_TXT = "requirements.txt" # For migration
VSCODE_DIR_NAME = ".vscode"
SETTINGS_FILE_NAME = "settings.json"
LAUNCH_FILE_NAME = "launch.json"
JSON_LOG_FILE_NAME = "pyuvstarter_setup_log.json"
# Map notebook system names to required execution dependencies (e.g. `ipykernel` for jupyter)
# This is an orthogonal concern to code dependencies like pandas.
_NOTEBOOK_SYSTEM_DEPENDENCIES = {
    "jupyter": ["jupyter", "ipykernel"],
    "polars-notebook": ["polars-notebook"],
    "quarto": ["quarto"],
    # Add more systems here as needed (e.g., 'voila': ['voila'])
}

# --- Argument Parsing ---
def parse_args():
    parser = argparse.ArgumentParser(
        description="Automate Python project setup with uv, VS Code config, and dependency management for scripts and notebooks."
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory to operate on (default: current directory)"
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Show pyuvstarter version and exit"
    )
    parser.add_argument(
        "--dependency-migration",
        choices=["auto", "all-requirements", "only-imported", "skip-requirements"],
        default="auto",
        help="Dependency migration mode: 'auto' (default, intelligent), 'all-requirements' (migrate all requirements.txt and discover imports), 'only-imported' (only migrate imported entries from requirements.txt, and discover other imports), 'skip-requirements' (ignore requirements.txt, rely only on imports)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without making changes."
    )
    return parser.parse_args()

# --- Project Version Extraction ---
def _get_project_version(pyproject_path: Path = Path(__file__), project_name: str = "pyuvstarter") -> str:
    """
    Robustly reads the version from the [project] section of a pyproject.toml.
    If project_name is given, only returns the version if [project].name matches.
    Returns the version string, or 'unknown' if not found or on error.

    Note: don't call me on a project before uv init, as I will return 'unknown'.
    """
    # Try importlib.metadata.version if project_name is given
    if project_name:
        try:
            import importlib.metadata
            return importlib.metadata.version(project_name)
        except Exception:
            pass
    # Fallback: try to read pyproject.toml
    if pyproject_path is not None and pyproject_path.exists():
        try:
            if sys.version_info >= (3, 11):
                import tomllib
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
            else:
                import toml
                with open(pyproject_path, "r", encoding="utf-8") as f:
                    data = toml.load(f)
            project = data.get("project", {})
            if project_name and project.get("name") != project_name:
                return "unknown"
            return project.get("version", "unknown")
        except Exception as e:
            _log_action("get_project_version", "ERROR", f"Failed to read version from '{pyproject_path.name}'", details={"exception": str(e)})
    return "unknown"

# --- JSON Logging Utilities ---
_log_data_global = {}

def _init_log(project_root: Path):
    """Initializes the global log data structure."""
    global _log_data_global
    pyproject_path = project_root / PYPROJECT_TOML_NAME
    project_version = _get_project_version(pyproject_path)
    _log_data_global = {
        "script_name": Path(__file__).name,
        "pyuvstarter_version": _get_project_version(Path(__file__).parent / "pyproject.toml", "pyuvstarter"),
        "project_version": project_version,
        "start_time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "end_time_utc": None, "overall_status": "IN_PROGRESS",
        "platform_info": {"system": platform.system(), "release": platform.release(),
                          "version": platform.version(), "machine": platform.machine(),
                          "python_version_script_host": sys.version},
        "project_root": str(project_root), "actions": [],
        "final_summary": "", "errors_encountered_summary": []
    }
    _log_action("script_bootstrap", "INFO", f"Script execution initiated for project at {project_root}.")


def _log_action(action_name: str, status: str, message: str = "", details: dict = None):
    """
    Logs a single, user-meaningful event to both the console and the structured JSON log, especially when the program takes action to change the system / project or encounters a significant condition.

    Purpose & Philosophy:
    - _log_action is the ONLY approved way to communicate actions, errors, and next steps to users and to the log in pyuvstarter.
    - It enforces a one-event, one-call discipline: every important event (success, warning, error, or user guidance) must be logged ONCE, with all relevant info.
    - This prevents log spam, double-logging, and user confusion, and ensures the JSON log is a faithful, machine-parseable record of what happened.

    Status Usage:
    - **INFO:** Routine progress, context, or non-critical information. No user action required.
    - **SUCCESS:** A key step completed as intended. No user action required unless you provide explicit next steps.
    - **WARN:** Something unexpected happened, but the script can continue. User may want to check or fix something. Provide next steps if user intervention is recommended.
    - **ERROR:** A critical failure. The script cannot proceed, or user intervention is required. Always provide clear, step-by-step next steps if the user can resolve the issue.

    When to Provide Next Steps:
    - Only include next steps if the user must take action to recover, fix, or continue.
    - If the script can handle the issue automatically, do NOT tell the user to do anything.
    - If next steps are needed, be specific and step-by-step (e.g., “Run this command: ...”, “Edit this file: ...”).
    - Avoid vague or generic advice (“Try again”, “Contact support”) unless there is no other option.

    Examples:
        # Good: (clear status, actionable next steps)
        _log_action('venv_create', 'SUCCESS', 'Virtual environment created at .venv. Next steps: Activate it with "source .venv/bin/activate".')

        _log_action('install_uv', 'ERROR', 'Failed to install uv. Next steps: Run "brew install uv" in your terminal, then re-run this script.', details={'exception': str(e)})

        # Bad: (split event, vague next steps, or unnecessary instruction)
        _log_action('venv_create', 'SUCCESS', 'Virtual environment created at .venv.')
        _log_action('venv_create', 'INFO', 'You may want to activate it.')  # Too vague, not actionable

        _log_action('install_uv', 'ERROR', 'Failed to install uv. Try something else.')  # Not specific

    Quick Reference:
    | Status   | Meaning                | User Action Needed? | Next Steps?         |
    |----------|------------------------|---------------------|---------------------|
    | INFO     | Routine info/progress  | No                  | Rarely              |
    | SUCCESS  | Step completed         | No (unless noted)   | Sometimes           |
    | WARN     | Unexpected, recoverable| Maybe               | If user can help    |
    | ERROR    | Critical failure       | Yes                 | Always, if possible |

    Parameters:
    - action_name: Short identifier for the event (e.g. 'install_uv').
    - status: 'INFO', 'SUCCESS', 'WARN', or 'ERROR'.
    - message: User-facing and/or technical message. Include next steps if needed.
    - details: Optional dict for structured, technical info.

    Always print to console and log to JSON. Never split a single event across multiple calls.
    """
    global _log_data_global
    if "actions" not in _log_data_global:
        _log_data_global["actions"] = []
    entry = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": action_name,
        "status": status.upper(),
        "message": message,
        "details": details or {},
    }
    _log_data_global["actions"].append(entry)

    if status.upper() == "ERROR":
        if "errors_encountered_summary" not in _log_data_global:
            _log_data_global["errors_encountered_summary"] = []
        error_summary = f"Action: {action_name}, Message: {message}"
        if details and "exception" in details:
            error_summary += f", Exception: {details['exception']}"
        if details and "command" in details:
            error_summary += f", Command: {details['command']}"
        _log_data_global["errors_encountered_summary"].append(error_summary)

    console_prefix = status.upper()
    if console_prefix == "SUCCESS":
        console_prefix = "INFO" # Success messages are often displayed as INFO on console
    details_str = f" | Details: {json.dumps(details)}" if details and details != {} else ""
    print(f"{console_prefix}: ({action_name}) {message}{details_str}")


def _get_next_steps_text(project_root: Path) -> str:
    """
    Generates context-aware 'Next Steps' guidance text.

    ENHANCED (v7.3): Only includes the activation step if the venv was actually created.
    This prevents showing invalid commands if venv creation failed.
    """
    steps = [
        "1. If VS Code is open with this project, reload the window (Ctrl+Shift+P > 'Developer: Reload Window')."
    ]

    # HARDENED: Only include the activation step if the venv was actually created.
    venv_path = project_root / VENV_NAME
    if venv_path.exists() and venv_path.is_dir():
        if sys.platform == "win32":
            activate_cmd = f"'{venv_path / 'Scripts' / 'activate'}'"
        else:
            activate_cmd = f"source '{venv_path / 'bin' / 'activate'}'"
        steps.append(f"2. Activate the environment in your terminal:\n    {activate_cmd}")

    steps.append(f"3. Review `{PYPROJECT_TOML_NAME}`, `uv.lock`, and `{GITIGNORE_NAME}`.")
    steps.append(f"4. Commit your project files, including `{PYPROJECT_TOML_NAME}` and `uv.lock`, to version control.")

    return "Next Steps:\n" + "\n".join(steps)


def _save_log(log_file_path: Path, project_root: Path):
    """Saves the accumulated log data to a JSON file."""
    global _log_data_global
    _log_data_global["end_time_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    current_overall_status = _log_data_global.get("overall_status", "IN_PROGRESS")

    if current_overall_status == "IN_PROGRESS":
        if _log_data_global.get("errors_encountered_summary"):
            _log_data_global["overall_status"] = "COMPLETED_WITH_ERRORS"
            _log_data_global["final_summary"] = _log_data_global.get("final_summary", "") + "Script completed, but some errors/warnings occurred. Check 'errors_encountered_summary' and 'actions' list in this log."
        else:
            _log_data_global["overall_status"] = "SUCCESS"
            _log_data_global["final_summary"] = _log_data_global.get("final_summary", "") + "Script completed successfully."
    elif not _log_data_global.get("final_summary"):
        _log_data_global["final_summary"] = f"Script execution concluded. Status: {current_overall_status}"

    # Always add next steps if the script made progress
    if _log_data_global["overall_status"] in ["SUCCESS", "COMPLETED_WITH_ERRORS", "HALTED_BY_SCRIPT_LOGIC"]:
        next_steps_text = _get_next_steps_text(project_root)
        # Ensure there's a newline before appending next steps if there's already a summary
        if _log_data_global.get("final_summary"):
            _log_data_global["final_summary"] += "\n\n" + next_steps_text
        else:
            _log_data_global["final_summary"] = next_steps_text


    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            json.dump(_log_data_global, f, indent=2)
        _log_action("save_log", "SUCCESS", f"Detailed execution log saved to '{log_file_path.name}'")
    except Exception as e:
        _log_action("save_log", "ERROR", f"Failed to save JSON log to '{log_file_path.name}': {e}")

# --- Core Helper Functions ---
def _run_command(command_list: list[str], action_log_name: str, work_dir: Path = None, shell: bool = False, capture_output: bool = True, suppress_console_output_on_success: bool = False, dry_run: bool = False):
    """
    Runs a shell command and logs its execution. Raises CalledProcessError on failure.
    Returns (stdout_str, stderr_str) if capture_output is True.
    If capture_output is False, stdout/stderr will be empty strings, and output streams to console.
    If dry_run is True, logs the command but does not execute it.

    Note: Since the main() function changes the CWD to project_root, work_dir defaults to
    the project root directory, making command execution safe and consistent.
    """
    if work_dir is None:
        work_dir = Path.cwd()  # This is now the project_root directory
    cmd_str = ' '.join(command_list) if isinstance(command_list, list) else command_list

    if dry_run:
        _log_action(action_log_name, "INFO", f"DRY RUN: Would execute: \"{cmd_str}\" in \"{work_dir}\" (Logged as action: {action_log_name})")
        return "", "" # Simulate successful empty output for dry run

    _log_action(action_log_name, "INFO", f"EXEC: \"{cmd_str}\" in \"{work_dir}\" (Logged as action: {action_log_name})")

    log_details = {"command": cmd_str, "working_directory": str(work_dir), "shell_used": shell, "capture_output_setting": capture_output}

    try:
        process = subprocess.run(command_list, cwd=work_dir, capture_output=capture_output, text=True, shell=shell, check=True)
        stdout = process.stdout.strip() if process.stdout and capture_output else ""
        stderr = process.stderr.strip() if process.stderr and capture_output else ""
        log_details.update({"return_code": process.returncode,
                            "stdout": stdout if capture_output else "Output streamed directly to console.",
                            "stderr_info": stderr if capture_output else "Output streamed directly to console."})
        _log_action(action_log_name, "SUCCESS", f"Command executed successfully: {cmd_str}", details=log_details)
        if capture_output and not suppress_console_output_on_success:
            if stdout:
                _log_action(action_log_name, "INFO", f"  OUT: {stdout}")
            if stderr:
                _log_action(action_log_name, "INFO", f"  INF_STDERR: {stderr}")
        return stdout, stderr
    except subprocess.CalledProcessError as e:
        log_details.update({"error_type": "CalledProcessError", "return_code": e.returncode,
                            "stdout": e.stdout.strip() if e.stdout and capture_output else ("Output streamed directly to console." if not capture_output else ""),
                            "stderr": e.stderr.strip() if e.stderr and capture_output else ("Output streamed directly to console." if not capture_output else ""),
                            "exception_message": str(e)})
        _log_action(action_log_name, "ERROR", f"  CMD_ERROR: Command failed: \"{cmd_str}\" failed with exit code {e.returncode}.", details=log_details)
        if capture_output:
            if e.stdout:
                _log_action(action_log_name, "ERROR", f"  FAIL_STDOUT:\n{e.stdout.strip()}")
            if e.stderr:
                _log_action(action_log_name, "ERROR", f"  FAIL_STDERR:\n{e.stderr.strip()}")
        raise
    except FileNotFoundError as e:
        cmd_name = command_list[0] if isinstance(command_list, list) else command_list.split()[0]
        log_details.update({"error_type": "FileNotFoundError", "missing_command": cmd_name, "exception_message": str(e)})
        _log_action(action_log_name, "ERROR", f"Command not found: {cmd_name}", details=log_details)
        raise
    except Exception as e:
        log_details.update({"error_type": "UnknownSubprocessException", "exception_message": str(e)})
        _log_action(action_log_name, "ERROR", f"Unexpected error executing command: {cmd_str}", details=log_details)
        raise

def _command_exists(command_name):
    """Checks if a command-line tool is available in the system's PATH."""
    return shutil.which(command_name) is not None

# --- UV & Tool Installation ---
def _install_uv_brew(dry_run: bool):
    """Attempts to install `uv` using Homebrew (available on macOS, Linux, and WSL)."""
    action_name = "install_uv_brew"
    _log_action(action_name, "INFO", "Attempting `uv` installation via Homebrew.")
    if not _command_exists("brew"):
        _log_action(action_name, "ERROR", "Homebrew (brew) not found. Cannot attempt `uv` installation via Homebrew.\n      Please install Homebrew from https://brew.sh/ or allow installation via the official script.")
        return False
    try:
        _run_command(["brew", "install", "uv"], f"{action_name}_exec", suppress_console_output_on_success=False, dry_run=dry_run)
        if dry_run: # In dry run, assume uv is installed for the check to pass
            _log_action(action_name, "INFO", "Assuming `uv` would be installed/updated via Homebrew in dry-run mode.")
            return True
        if _command_exists("uv"):
            _log_action(action_name, "SUCCESS", "`uv` installed/updated via Homebrew.")
            return True
        else:
            _log_action(action_name, "ERROR", "`brew install uv` seemed complete, but `uv` command is still not found.\nTry running `brew doctor` or check Homebrew's output.\n       Ensure Homebrew's bin directory is in your PATH.")
            return False
    except Exception:
        _log_action(action_name, "ERROR", "`uv` installation via Homebrew failed. See command execution log.\nTry running `brew install uv` manually.")
        return False

def _install_uv_script(dry_run: bool):
    """Installs `uv` using the official OS-specific scripts (curl or PowerShell)."""
    action_name = "install_uv_official_script"
    _log_action(action_name, "INFO", "Attempting `uv` installation via official script.")
    command_str = ""
    try:
        if sys.platform == "win32":
            command_str = 'powershell -ExecutionPolicy ByPass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"'
            _run_command(command_str, f"{action_name}_exec_ps", shell=True, capture_output=False, dry_run=dry_run)
        else:
            if not _command_exists("curl"):
                _log_action(action_name, "ERROR", "`curl` is not installed. Cannot download `uv` installation script.\nInstall `curl` (e.g., 'sudo apt install curl') and try again.")
                return False
            command_str = "curl -LsSf https://astral.sh/uv/install.sh | sh"
            _run_command(command_str, f"{action_name}_exec_curl", shell=True, capture_output=False, dry_run=dry_run)

        if dry_run: # In dry run, assume uv is installed for the check to pass
            _log_action(action_name, "INFO", "Assuming `uv` installation script would execute and uv would be available in dry-run mode.")
            return True
        _log_action(action_name, "SUCCESS", "`uv` installation script executed. It usually adds `uv` to your PATH.\nIf `uv` is not found immediately, you might need to restart your terminal or source your shell profile.")
        if _command_exists("uv"):
            _log_action(action_name, "SUCCESS", "`uv` now available after script install.")
            return True
        else:
            _log_action(action_name, "WARN", "`uv` command still not found after script install. PATH adjustment or shell restart may be needed.\n`uv` typically installs to $HOME/.local/bin or similar. Ensure this is in your PATH.")
            return False
    except Exception:
        _log_action(action_name, "ERROR", f"Official `uv` installation script execution failed. Command: {command_str}. See command execution log.\nTry running manually: {command_str}")
        return False

def _ensure_uv_installed(dry_run: bool):
    """
    Ensures `uv` is installed using a robust, multi-stage verification process.

    4-Stage Process (from v7.3 battle-tested logic):
    1. uv --version pre-check
    2. Platform-aware installation attempt
    3. _command_exists post-check
    4. uv --version final verification

    This handles the common gotcha where installers succeed but PATH isn't updated.
    """
    action_name = "ensure_uv_installed"
    _log_action(action_name, "INFO", "Starting `uv` availability check and installation if needed.")

    # Stage 1: Pre-check with version verification
    if _command_exists("uv"):
        try:
            version_out, _ = _run_command(["uv", "--version"], f"{action_name}_version_check", suppress_console_output_on_success=True, dry_run=dry_run)
            if not dry_run:
                _log_action(action_name, "SUCCESS", f"`uv` is already installed. Version: {version_out}")
            return True
        except Exception as e:
            _log_action(f"{action_name}_version_check", "WARN", "`uv --version` failed, though `uv` command seems to exist. Will attempt to reinstall.", details={"exception": str(e)})

    _log_action(action_name, "INFO", "`uv` not found or version check failed. Attempting installation.")

    # Stage 2: Platform-aware installation
    installed_successfully = False
    methods = []
    # Try Homebrew first if available (works on macOS, Linux, and WSL)
    if _command_exists("brew"):
        methods.append("Homebrew")
        if _install_uv_brew(dry_run):
            installed_successfully = True

    if not installed_successfully:
        methods.append("Official Script")
        if _install_uv_script(dry_run):
            installed_successfully = True

    if installed_successfully:
        if dry_run:
            _log_action(action_name, "SUCCESS", f"DRY RUN: `uv` assumed successfully installed via {' -> '.join(methods)}.")
            return True

        # Stage 3: Post-install command existence check
        if _command_exists("uv"):
            try:
                # Stage 4: Final version verification
                version_out, _ = _run_command(["uv", "--version"], f"{action_name}_post_install_version_check")
                _log_action(action_name, "SUCCESS", f"`uv` successfully installed/ensured via {' -> '.join(methods)}. Version: {version_out}")
                return True
            except Exception:
                _log_action(action_name, "ERROR", "Installation successful, but 'uv --version' still fails.\n      ACTION: This may indicate a problem with the `uv` binary or PATH. Please restart your terminal.")
                return False
        else:
            _log_action(action_name, "ERROR", f"Installation via {' -> '.join(methods)} seemed to complete, but `uv` command is still not available.\n      ACTION: Please restart your terminal or manually add the installation directory (e.g., ~/.local/bin) to your PATH.")
            return False
    else:
        _log_action(action_name, "ERROR", f"All automatic `uv` installation attempts failed (methods tried: {' -> '.join(methods)}).\n      ACTION: Please install `uv` manually from https://astral.sh/uv.")
        return False

def _ensure_tool_available(tool_name: str, major_action_results: list, dry_run: bool, website: str = None):
    """
    Ensures a CLI tool is installed via `uv tool install` for use with `uvx`.
    Optionally provide a website for user guidance. Handles all error logging internally.
    Updates major_action_results for each tool.
    """
    action_name = f"ensure_tool_{tool_name}"
    package_to_install = tool_name # Often the package name is the same as the tool name
    _log_action(action_name, "INFO", f"Ensuring CLI tool `{tool_name}` (package: `{package_to_install}`) is available for `uvx`.")
    try:
        # uv tool install is idempotent and safer to just run (or dry-run)
        _run_command(["uv", "tool", "install", package_to_install], f"{action_name}_uv_tool_install", suppress_console_output_on_success=True, dry_run=dry_run)
        _log_action(action_name, "SUCCESS", f"`{tool_name}` (package '{package_to_install}') install/check via `uv tool install` complete.\nFor direct terminal use, ensure `uv`'s tool directory is in PATH (try `uv tool update-shell`).")
        major_action_results.append((f"{tool_name}_cli_tool", "SUCCESS"))
        return True
    except Exception:
        website_msg = f"\nSee documentation or troubleshooting at: {website}" if website else ""
        _log_action(
            action_name,
            "ERROR",
            f"Failed to ensure `{tool_name}` via `uv tool install`.\nTry running: uv tool install {package_to_install}{website_msg}"
        )
        major_action_results.append((f"{tool_name}_cli_tool", "FAILED"))
        return False


######################################################################
# NOTEBOOK DEPENDENCY DETECTION (CONSOLIDATED)
#
# This section contains the new, consolidated logic for discovering
# dependencies from all source files, including Jupyter Notebooks.
######################################################################

def _get_dynamic_ignore_set():
    """
    Dynamically generate a set of standard library and built-in names to ignore for dependency detection.
    This is critical for not treating 'sys' or 'os' as a PyPI dependency.
    It uses sys.stdlib_module_names (Python 3.10+) or falls back to the `stdlib-list` package if available.
    """
    stdlib_modules = set()
    # Best case: Python 3.10+ has this built-in.
    if hasattr(sys, "stdlib_module_names"):
        stdlib_modules = set(sys.stdlib_module_names)
    else:
        # Fallback for older Python: try to use an optional, pre-installed helper package.
        try:
            from stdlib_list import stdlib_list  # type: ignore
            import sys as _sys
            # Get stdlib for the version of python running the script
            stdlib_modules = set(stdlib_list(f"{_sys.version_info.major}.{_sys.version_info.minor}"))
        except ImportError:
            # If neither is available, the set will be smaller, which is a minor degradation.
            # We still filter builtins, which is better than nothing.
            _log_action("get_stdlib", "WARN", "Could not determine Python's standard library list. 'stdlib-list' package not found and not on Python 3.10+. Standard library modules might be incorrectly identified as dependencies.")
            stdlib_modules = set()
    # Also include built-in names.
    builtin_names = set(dir(__builtins__))
    # The final set is the union of both, lowercased for case-insensitive comparison.
    return {name.lower() for name in stdlib_modules | builtin_names}

# Initialize the ignore set once at script startup for efficiency.
_DYNAMIC_IGNORE_SET = _get_dynamic_ignore_set()

def _canonicalize_pkg_name(name: str) -> str:
    """
    Canonicalize package import names to their PyPI package names for consistency.
    This is crucial because `import` names often differ from installable package names.
    (e.g., you `import sklearn` but `uv add scikit-learn`).

    Comprehensive mapping of common import-to-package name discrepancies.
    """
    mapping = {
        # Machine Learning & Data Science
        "sklearn": "scikit-learn",
        "cv2": "opencv-python",

        # Image Processing
        "pil": "pillow",
        "PIL": "pillow",

        # Configuration & Serialization
        "yaml": "pyyaml",
        "toml": "toml",

        # Web & APIs
        "requests_oauthlib": "requests-oauthlib",
        "google.cloud": "google-cloud",
        "bs4": "beautifulsoup4",

        # Database & ORM
        "psycopg2": "psycopg2-binary",
        "MySQLdb": "mysqlclient",

        # Development Tools
        "dotenv": "python-dotenv",
        "dateutil": "python-dateutil",

        # GUI & Graphics
        "tkinter": "",  # Built-in, should be filtered out elsewhere

        # System & OS
        "win32api": "pywin32",
        "win32com": "pywin32",

        # Testing & Mocking
        "mock": "mock",  # Built into unittest in Python 3.3+

        # Async & Concurrency
        "asyncio": "",  # Built-in

        # Typing
        "typing_extensions": "typing-extensions",
    }

    canonical = mapping.get(name.lower(), name.lower())
    # Handle empty string mappings (built-in modules that shouldn't be installed)
    return canonical if canonical else name.lower()

def _find_all_notebooks(project_root: Path) -> list[Path]:
    """Recursively finds all .ipynb files in the project, ignoring the venv directory."""
    return [p for p in project_root.rglob("*.ipynb") if VENV_NAME not in p.parts]

def _convert_notebooks_to_py(notebook_paths: list[Path], temp_dir: Path, project_root: Path, dry_run: bool) -> dict[Path, Path]:
    """
    Converts notebooks to .py scripts, returning a map of original to converted paths for precise failure tracking.

    This function's return type is critical for the deterministic fallback logic. By returning a dictionary,
    it allows the calling function to know exactly which notebooks were processed successfully.

    Args:
        notebook_paths: A list of Path objects for the notebooks to convert.
        temp_dir: The temporary directory to store the converted Python scripts.
        dry_run: If True, simulates the action without running commands.

    Returns:
        A dictionary mapping the original notebook Path to its successful temporary script Path.
    """
    successful_conversions: dict[Path, Path] = {}
    # This tool-based method can only run if `jupyter` is available.
    if not _command_exists("jupyter"):
        _log_action("nbconvert_check", "WARN", "'jupyter' command not found. Cannot convert notebooks to scripts for tool-based dependency analysis. Will use fallback manual parsing.")
        return successful_conversions

    for nb_path in notebook_paths:
        # Create a corresponding python file path in the temp directory.
        py_path = temp_dir / (nb_path.stem + ".py")
        if dry_run:
            _log_action("nbconvert_dry_run", "INFO", f"DRY RUN: Would convert {nb_path.name} to a temporary script for analysis.")
            successful_conversions[nb_path] = py_path
            continue
        try:
            # Execute the conversion.
            _run_command([
                "jupyter", "nbconvert", "--to", "script", str(nb_path),
                "--output", py_path.stem, # nbconvert adds the extension
                "--output-dir", str(temp_dir)
            ], f"nbconvert_{nb_path.stem}", suppress_console_output_on_success=True)
            if py_path.exists():
                successful_conversions[nb_path] = py_path
        except subprocess.CalledProcessError as e:
            # If a single notebook fails to convert, log it and continue with others.
            _log_action("nbconvert_error", "WARN", f"Failed to convert notebook '{nb_path.name}'. It may be corrupt or have invalid syntax. It will be parsed manually as a fallback.", details={"notebook": str(nb_path), "exception": str(e)})
        except Exception as e:
            # Catch any other unexpected errors during conversion
            _log_action("nbconvert_error", "WARN", f"Unexpected error converting notebook '{nb_path.name}': {e}. It will be parsed manually as a fallback.", details={"notebook": str(nb_path), "exception": str(e)})
    return successful_conversions

def _parse_notebook_manually(nb_path: Path) -> set[tuple[str, str]]:
    """
    Fallback dependency discovery: Parses a notebook file's JSON directly.
    It uses the Abstract Syntax Tree (AST) for reliable `import` parsing and
    regular expressions for finding shell/magic install commands (e.g., `!pip install`).
    Returns a set of (canonical_base_name, full_specifier) tuples.
    """
    action_name = f"notebook_fallback_parse_{nb_path.stem}"
    _log_action(action_name, "INFO", f"Using fallback parser for '{nb_path.name}'.")
    discovered_packages = set()

    try:
        with open(nb_path, "r", encoding="utf-8") as f:
            nb_content = json.load(f)
    except FileNotFoundError:
        _log_action(action_name, "ERROR", f"Notebook file not found at path '{nb_path}'. Skipping dependency discovery.")
        return set()
    except IOError as e:
        _log_action(action_name, "ERROR", f"Could not read notebook file '{nb_path.name}' due to an I/O error. Check file permissions.", details={"exception": str(e)})
        return set()
    except json.JSONDecodeError as e:
        _log_action(action_name, "ERROR", f"Notebook file '{nb_path.name}' is not valid JSON. It may be corrupted.", details={"exception": str(e)})
        return set()
    except Exception as e:
        _log_action(action_name, "ERROR", f"Unexpected error reading notebook '{nb_path.name}': {e}", details={"exception": str(e)})
        return set()

    # Gather all source code from every code cell into a single block.
    all_code_source = "\n".join(
        "".join(cell.get("source", []))
        for cell in nb_content.get("cells", [])
        if cell.get("cell_type") == "code"
    )

    # 1. AST-based parsing for `import` and `from ... import` statements. This is very reliable.
    try:
        tree = ast.parse(all_code_source)
        for node in ast.walk(tree):
            module_name = None
            if isinstance(node, ast.Import):
                module_name = node.names[0].name
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_name = node.module

            if module_name:
                # Get the top-level package (e.g., 'pandas' from 'pandas.DataFrame').
                base_pkg = module_name.split('.')[0].lower()
                # Filter out standard library modules.
                if base_pkg not in _DYNAMIC_IGNORE_SET:
                    # Canonicalize the name (e.g., sklearn -> scikit-learn).
                    canonical_name = _canonicalize_pkg_name(base_pkg)
                    # For imports, the specifier is just the package name itself.
                    discovered_packages.add((canonical_name, canonical_name))
    except SyntaxError as e:
        _log_action(action_name, "WARN", f"Could not parse Python code in '{nb_path.name}' due to a syntax error. Import detection may be incomplete. Error: {e}")

    # 2. Streamlined regex-based parsing for shell/magic install commands (v7.3 improvement)
    # Single consolidated pattern for better maintainability
    install_pattern = re.compile(
        r"^[!%]\s*(?:(?:pip3?|python\s+-m\s+pip|uv\s+pip|conda|mamba)\s+install|uv\s+add|poetry\s+add)\s+(.+)",
        re.IGNORECASE
    )

    for line in all_code_source.splitlines():
        line = line.split('#', 1)[0].strip() # Remove comments and whitespace.
        if not line:
            continue

        match = install_pattern.match(line)
        if match:
            args_str = match.group(1).strip()
            # Use shlex.split() for proper handling of quoted arguments (v7.3 improvement)
            try:
                tokens = shlex.split(args_str)
                # Use the helper function for clean separation of concerns
                discovered_packages.update(_parse_install_tokens(tokens))
            except ValueError as e:
                _log_action(action_name, "WARN", f"Could not shlex-parse arguments in line: '{line}'. Error: {e}.")
                continue

    return discovered_packages

def _parse_install_tokens(tokens: list[str]) -> set[tuple[str, str]]:
    """
    Parses a list of tokens from a package installation command.

    This helper function separates the concern of parsing tokens from finding the
    install command line itself. It is designed to be robust and handle various
    package specification formats.

    Args:
        tokens: A list of strings, typically from shlex.split().

    Returns:
        A set of (canonical_base_name, full_specifier) tuples found in the tokens.
    """
    discovered: set[tuple[str, str]] = set()
    for part in tokens:
        if not part:
            continue
        # Skip flags like -U, --user, etc.
        if part.startswith('-'):
            if part in ('-r', '--requirement'):
                # Log a warning but don't halt processing
                _log_action("parse_install_tokens", "WARN", f"Unsupported '-r' flag found in install command and ignored: '{part}'")
            continue
        # A basic filter for valid-looking package names/specifiers.
        if re.match(r"^[\w\-\.]+(?:\[.*\])?(?:[=<>!~]=?.*)?$", part):
            base_pkg = part.split('[')[0].split('=')[0].split('>')[0].split('<')[0].split('~')[0].split('!')[0].strip().lower()
            if base_pkg not in _DYNAMIC_IGNORE_SET:
                canonical_name = _canonicalize_pkg_name(base_pkg)
                # Add the full specifier as found (e.g., 'pandas==1.2.3').
                discovered.add((canonical_name, part))
    return discovered

def _discover_all_code_dependencies(project_root: Path, venv_name: str, dry_run: bool) -> set[tuple[str, str]]:
    """
    Facade function to discover all dependencies using a hybrid strategy:
    1. Analyzes .py files with pipreqs.
    2. Attempts to convert .ipynb files and analyze with pipreqs (Primary).
    3. For any notebooks that fail conversion, it uses a robust manual parser (Fallback).
    """
    action_name = "discover_all_code_dependencies"
    _log_action(action_name, "INFO", "Starting comprehensive dependency discovery from all sources.")
    all_discovered_deps = set()

    # Phase 1: Analyze Python scripts
    _log_action(action_name, "INFO", "Phase 1: Analyzing Python scripts (.py files)...")
    script_deps = _get_packages_from_pipreqs(project_root, venv_name, dry_run, source_type="Python scripts")
    all_discovered_deps.update(script_deps)
    _log_action(action_name, "INFO", f"Found {len(script_deps)} dependencies in .py files.")

    # Phase 2: Hybrid Notebook Analysis
    notebook_paths = _find_all_notebooks(project_root)
    if not notebook_paths:
        _log_action(action_name, "SUCCESS", "Dependency discovery complete. No notebooks found.")
        return all_discovered_deps

    _log_action(action_name, "INFO", f"Phase 2: Analyzing {len(notebook_paths)} Jupyter notebook(s)...")

    successfully_converted_notebooks = set()
    with tempfile.TemporaryDirectory(prefix="pyuvstarter_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        # Primary Strategy: Try to convert and analyze with tools
        conversion_map = _convert_notebooks_to_py(notebook_paths, temp_dir, project_root, dry_run)

        if conversion_map:
            converted_script_deps = _get_packages_from_pipreqs(temp_dir, "", dry_run, source_type="converted notebooks", work_dir=temp_dir)
            all_discovered_deps.update(converted_script_deps)
            successfully_converted_notebooks = set(conversion_map.keys())
            _log_action(action_name, "INFO", f"Successfully analyzed {len(successfully_converted_notebooks)} notebook(s) using the primary tool-based method.")

    # Fallback Strategy: Manually parse any notebooks that failed conversion
    failed_notebooks = set(notebook_paths) - successfully_converted_notebooks
    if failed_notebooks:
        _log_action(action_name, "INFO", f"Using fallback parser for {len(failed_notebooks)} notebook(s) that could not be converted.")
        for nb_path in failed_notebooks:
            manual_deps = _parse_notebook_manually(nb_path) # Assumes the robust version of this function exists
            all_discovered_deps.update(manual_deps)

    _log_action(action_name, "SUCCESS", f"Dependency discovery complete. Found {len(all_discovered_deps)} unique dependencies from all sources.")
    return all_discovered_deps

# --- Project and Dependency Handling ---

def _ensure_project_initialized(project_root: Path, dry_run: bool):
    """
    Ensures a pyproject.toml exists. If not, runs `uv init` and then checks
    if `main.py` should be removed.
    """
    action_name = "ensure_project_initialized_with_pyproject"
    pyproject_path = project_root / PYPROJECT_TOML_NAME
    main_py_path = project_root / "main.py"

    if pyproject_path.exists():
        _log_action(action_name, "INFO", f"'{PYPROJECT_TOML_NAME}' already exists at {project_root}.")
        return True

    _log_action(action_name, "INFO", f"'{PYPROJECT_TOML_NAME}' not found. Running `uv init`...")

    # Check for existing Python files before running uv init
    existing_py_files = list(project_root.rglob("*.py"))
    # Exclude this script itself if it's in the project root
    # script_path_in_project = project_root / Path(__file__).name
    # if script_path_in_project in existing_py_files:
    #     existing_py_files.remove(script_path_in_project)

    project_had_py_files_before_init = bool(existing_py_files)
    main_py_existed_before_init = main_py_path.exists()

    try:
        _run_command(["uv", "init"], f"{action_name}_uv_init_exec", dry_run=dry_run)

        if dry_run:
            _log_action(action_name, "INFO", f"In dry-run mode: Assuming `uv init` would create/update '{PYPROJECT_TOML_NAME}'.")
            return True # In dry-run, assume success to continue simulation

        if not pyproject_path.exists():
            _log_action(action_name, "ERROR", f"`uv init` ran but '{PYPROJECT_TOML_NAME}' was not created. This is unexpected.\nCheck `uv init` output. Manual creation of `pyproject.toml` might be needed.")
            return False

        _log_action(action_name, "SUCCESS", f"`uv init` completed. '{PYPROJECT_TOML_NAME}' created/updated.")

        # Conditional removal of main.py created by `uv init`
        main_py_exists_after_init = main_py_path.exists()
        if main_py_exists_after_init and not main_py_existed_before_init: # `uv init` created main.py
            if project_had_py_files_before_init: # And there were other .py files
                _log_action(f"{action_name}_remove_main_py", "INFO", f"`uv init` created '{main_py_path.name}', but other .py files existed. Removing '{main_py_path.name}'.")
                try:
                    main_py_path.unlink()
                    _log_action(f"{action_name}_remove_main_py", "SUCCESS", f"Successfully removed '{main_py_path.name}' created by `uv init`.")
                except OSError as e:
                    _log_action(f"{action_name}_remove_main_py", "ERROR", f"Failed to remove '{main_py_path.name}': {e}.")
            else: # Project was empty of .py files, so main.py from uv init is fine
                _log_action(f"{action_name}_keep_main_py", "INFO", f"`uv init` created '{main_py_path.name}' in an otherwise empty Python project. It will be kept as standard for a new project.")
        return True

    except Exception: # Error logged by _run_command
        _log_action(action_name, "ERROR", "Failed to initialize project with `uv init`. See command execution log.\nManual `pyproject.toml` creation or `uv init` troubleshooting needed.")
        return False


def _ensure_gitignore_exists(project_root: Path, venv_name: str, dry_run: bool):
    """Ensures a .gitignore file exists and contains essential Python/venv ignores."""
    action_name = "ensure_gitignore"
    gitignore_path = project_root / GITIGNORE_NAME
    _log_action(action_name, "INFO", f"Checking for '{GITIGNORE_NAME}' file.")

    essential_ignore_map = {
        "Python Virtual Environments": [f"{venv_name}/", "venv/", "ENV/", "env/", "*/.venv/", "*/venv/"],
        "Python Cache & Compiled Files": ["__pycache__/", "*.py[cod]", "*$py.class"],
        "Log file from this script": [JSON_LOG_FILE_NAME],
        "OS-specific": [".DS_Store", "Thumbs.db"],
        "Jupyter Notebook": [".ipynb_checkpoints"],
    }
    comprehensive_ignores = [
        "# Python Virtual Environments", f"{venv_name}/", "venv/", "ENV/", "env/", "*/.venv/", "*/venv/",
        "\n# Python Cache & Compiled Files", "__pycache__/", "*.py[cod]", "*$py.class",
        "\n# Compiled C extensions", "*.so", "*.pyd",
        "\n# Distribution / packaging", ".Python", "build/", "develop-eggs/", "dist/", "downloads/",
        "eggs/", ".eggs/", "lib/", "lib64/", "parts/", "sdist/", "var/", "wheels/",
        "pip-wheel-metadata/", "share/python-wheels/", "*.egg-info/", ".installed.cfg", "*.egg", "MANIFEST",
        "\n# Installer logs", "pip-log.txt", "pip-delete-this-directory.txt",
        "\n# Unit test / coverage reports", "htmlcov/", ".tox/", ".nox/", ".coverage", ".coverage.*",
        ".cache", "nosetests.xml", "coverage.xml", "*.cover", "*.log", ".hypothesis/", ".pytest_cache/",
        "\n# Jupyter Notebook", ".ipynb_checkpoints",
        "\n# VS Code (allow user-committed settings)", ".vscode/*",
        "!.vscode/settings.json", "!.vscode/tasks.json", "!.vscode/launch.json", "!.vscode/extensions.json",
        ".history/",
        "\n# Log file from this script", JSON_LOG_FILE_NAME,
        "\n# OS-specific", ".DS_Store", "Thumbs.db"
    ]

    if dry_run:
        _log_action(action_name, "INFO", f"DRY RUN: Would create or update '{GITIGNORE_NAME}' with essential Python/venv ignores.")
        return

    if gitignore_path.exists():
        _log_action(action_name, "INFO", f"'{GITIGNORE_NAME}' already exists. Checking for essential entries.")
        try:
            with open(gitignore_path, "r+", encoding="utf-8") as f:
                content = f.read()
                if content and not content.endswith("\n"):
                    f.write("\n")
                    content += "\n"

                entries_to_add_with_comments = []
                for comment, patterns in essential_ignore_map.items():
                    all_patterns_present_for_group = True
                    temp_patterns_to_add_for_group = []
                    for pattern in patterns:
                        if not any(pattern.strip() == line.strip() for line in content.splitlines()):
                            all_patterns_present_for_group = False
                            temp_patterns_to_add_for_group.append(pattern)
                    if not all_patterns_present_for_group and temp_patterns_to_add_for_group:
                        comment_line = f"# {comment}"
                        if comment_line not in content:
                            entries_to_add_with_comments.append(f"\n{comment_line}")
                        entries_to_add_with_comments.extend(temp_patterns_to_add_for_group)

                if entries_to_add_with_comments:
                    f.write("\n# Added/Ensured by pyuvstarter.py\n")
                    for entry in entries_to_add_with_comments:
                        f.write(f"{entry}\n")
                    _log_action(action_name, "SUCCESS", f"Appended essential missing entries to existing '{GITIGNORE_NAME}'.", details={"appended": entries_to_add_with_comments})
                else:
                    _log_action(action_name, "INFO", f"Existing '{GITIGNORE_NAME}' seems to cover essential exclusions for venv and log file.")
        except Exception as e:
            _log_action(action_name, "WARN", f"Could not read/update existing '{GITIGNORE_NAME}'. Manual check advised. Exception: {e}.", details={"exception": str(e)})
    else:
        _log_action(action_name, "INFO", f"'{GITIGNORE_NAME}' not found. Creating a default one.")
        try:
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write("# Auto-generated by pyuvstarter.py\n")
                f.write("\n".join(comprehensive_ignores))
                f.write("\n")
            _log_action(action_name, "SUCCESS", f"Default '{GITIGNORE_NAME}' created.")
        except Exception as e:
            _log_action(action_name, "ERROR", f"Failed to create '{GITIGNORE_NAME}'. Exception: {e}. Please create it manually with standard Python ignores.", details={"exception": str(e)})


def _get_declared_dependencies(pyproject_path: Path) -> set[str]:
    """
    Parses pyproject.toml to get a set of base package names declared under
    [project.dependencies] and [project.optional-dependencies].
    Returns a set of lowercase base package names.
    """
    action_name = "get_declared_dependencies_from_pyproject"
    dependencies = set()
    if not pyproject_path.exists():
        _log_action(action_name, "WARN", f"'{pyproject_path.name}' not found when trying to read declared dependencies. Assuming none declared yet.")
        return dependencies

    tomllib_module = None
    tomllib_source = "None"
    if sys.version_info >= (3, 11):
        try:
            tomllib_module = importlib.import_module("tomllib")
            tomllib_source = "tomllib (Python 3.11+ built-in)"
        except ImportError:
            pass
    if not tomllib_module:
        try:
            tomllib_module = importlib.import_module("toml")
            tomllib_source = "toml (third-party package)"
        except ImportError:
            msg = "Cannot parse `pyproject.toml` to read existing dependencies: `tomllib` (Python 3.11+) or `toml` package not available in the environment running this script. Dependency checking against `pyproject.toml` might be incomplete."
            _log_action(action_name, "WARN", msg + " Script best run with Python 3.11+ or with 'toml' installed in its execution environment.")
            return dependencies

    _log_action(action_name, "INFO", f"Attempting to parse '{pyproject_path.name}' for existing dependencies using {tomllib_source}.")
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib_module.load(f)
        project_data = data.get("project", {})
        for dep_section_key in ["dependencies", "optional-dependencies"]:
            deps_source = project_data.get(dep_section_key, [])
            items_to_parse = []
            if isinstance(deps_source, list):
                items_to_parse.extend(deps_source)
            elif isinstance(deps_source, dict):
                for group_list in deps_source.values():
                    if isinstance(group_list, list):
                        items_to_parse.extend(group_list)
            for dep_str in items_to_parse:
                if isinstance(dep_str, str):
                    pkg_name = dep_str.split("[")[0].split("=")[0].split(">")[0].split("<")[0].split("!")[0].split("~")[0].strip()
                    if pkg_name:
                        dependencies.add(pkg_name.lower())

        _log_action(action_name, "SUCCESS", f"Parsed '{pyproject_path.name}'. Found {len(dependencies)} unique base dependency names declared.", details={"source": tomllib_source, "count": len(dependencies), "found_names": sorted(list(dependencies)) if dependencies else "None"})
        return dependencies
    except Exception as e:
        msg = f"Failed to parse '{pyproject_path.name}' using {tomllib_source} to get dependency list. Check its TOML syntax. Dependency list might be incomplete for subsequent checks. Exception: {e}"
        _log_action(action_name, "ERROR", msg, details={"exception": str(e)})
        return dependencies

def _get_packages_from_legacy_req_txt(requirements_path: Path) -> set[tuple[str, str]]:
    """
    Reads a requirements.txt file and extracts package specifiers.
    Returns a set of (base_package_name, full_specifier) tuples.
    """
    action_name = "read_legacy_requirements_txt_content"
    packages_specs = set()
    if not requirements_path.exists():
        _log_action(action_name, "INFO", f"No legacy '{requirements_path.name}' found.")
        return packages_specs

    _log_action(action_name, "INFO", f"Reading legacy '{requirements_path.name}'.")
    try:
        with open(requirements_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-e"): # Skip comments and editable installs
                    continue
                # Extract base package name from specifier for comparison
                base_pkg_name = line.split("[")[0].split("=")[0].split(">")[0].split("<")[0].split("!")[0].split("~")[0].strip().lower()
                if base_pkg_name:
                    packages_specs.add((base_pkg_name, line))
        _log_action(action_name, "SUCCESS", f"Read {len(packages_specs)} package specifier(s) from '{requirements_path.name}'.")
    except Exception as e:
        _log_action(action_name, "ERROR", f"Could not read '{requirements_path.name}' for migration. Exception: {e}. Skipping migration.", details={"exception": str(e)})
    return packages_specs

def _get_packages_from_pipreqs(path_to_scan: Path, venv_name_to_ignore: str, dry_run: bool, source_type: str, work_dir: Path = None) -> set[tuple[str, str]]:
    """
    Reusable utility to run `pipreqs` via `uvx` on a specific path.
    This is used for both the main project and for converted notebooks in a temp dir.

    Returns a set of (canonical_base_name, full_specifier) tuples.
    """
    action_name = f"pipreqs_discover_imports_in_{source_type.replace(' ', '_')}"
    _log_action(action_name, "INFO", f"Scanning {source_type} for imports with `pipreqs` (via `uvx`) in '{path_to_scan}'.")
    packages_specs = set()
    # If a venv name is provided, ignore it. For temp dirs, this will be empty.
    pipreqs_args = ["uvx", "pipreqs", "--print", str(path_to_scan)]
    if venv_name_to_ignore:
        pipreqs_args.extend(["--ignore", venv_name_to_ignore])

    try:
        stdout, _ = _run_command(pipreqs_args, f"{action_name}_exec", work_dir=work_dir, suppress_console_output_on_success=True, dry_run=dry_run)

        if dry_run:
            _log_action(action_name, "INFO", f"DRY RUN: Assuming `pipreqs` would scan {source_type}. No actual imports found.")
            return set()

        parsed_count = 0
        if stdout:
            for line in stdout.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # pipreqs --print gives specifiers like 'package==1.2.3'
                base_name = line.split("==")[0].strip().lower()
                canonical_name = _canonicalize_pkg_name(base_name)
                packages_specs.add((canonical_name, line))
                parsed_count += 1

        if parsed_count > 0:
            _log_action(action_name, "SUCCESS", f"Discovered {len(packages_specs)} unique package specifier(s) in {source_type}.")
        else:
             _log_action(action_name, "INFO", f"`pipreqs` found no import-based dependencies in {source_type}.")
        return packages_specs
    except subprocess.CalledProcessError:
        _log_action(action_name, "ERROR", f"`uvx pipreqs` command failed for {source_type}. Cannot automatically discover dependencies. Check command logs.")
    except Exception as e:
        _log_action(action_name, "ERROR", f"An unexpected error occurred while running `pipreqs` for {source_type}: {e}", details={"exception": str(e)})
    return set()

def _run_ruff_unused_import_check(project_root: Path, major_action_results: list, dry_run: bool):
    """
    Runs ruff via uvx to detect unused imports (F401) and logs warnings if found.

    This function uses the correct argument order and format for `uvx ruff check`:
    - The `=` syntax (e.g., --select=F401) is used to create unambiguous option-value pairs.
    - All ruff options are placed after a `--` separator to pass them to ruff.
    - The target directory (project_root) is placed last.

    Example of the correct CLI invocation:
        uvx ruff check -- --select=F401 --exit-zero --format=json /path/to/project

    Args:
        project_root (Path): The root directory of the project to check.
        major_action_results (list): List to append action results for summary.
        dry_run (bool): If True, simulates the check without executing.

    Returns:
        None. Logs results and warnings as appropriate.
    """
    action_name = "ruff_unused_import_check"
    _log_action(action_name, "INFO", "Running ruff to check for unused imports (F401).")

    try:
        # CORRECTED Ruff CLI arguments using the robust '=' syntax.
        ruff_args = [
            "uvx",
            "ruff",
            # 1. Use the global '--config' option to set the output format.
            #    The value must be a valid TOML key-value pair string.
            # 2. The subcommand comes next.
            "check",
            "--output-format=json",  # Use --output-format instead of --format for clarity
            # 3. Options for the subcommand follow.
            "--select=F401",
            "--exit-zero",
            # 4. The positional path argument is last.
            str(project_root),
        ]
        result_stdout, _ = _run_command(
            ruff_args,
            f"{action_name}_exec",
            suppress_console_output_on_success=True,
            dry_run=dry_run
        )
        # print the stdout for debugging purposes
        if result_stdout:
            _log_action(action_name, "DEBUG", f"Ruff output:\n{result_stdout.strip()}")

        if dry_run:
            _log_action(action_name, "INFO", "DRY RUN: Assuming `ruff` would check for unused imports. No actual check performed.")
            return

        unused = []
        if result_stdout:
            try:
                # CORRECTED LOGIC: --output-format=json returns a single JSON array for all issues.
                # We parse the entire stdout string at once.
                issues = json.loads(result_stdout)

                for issue in issues:
                    # Now, 'issue' will be a dictionary as expected
                    if issue.get("code") == "F401":
                        filename = issue.get("filename")
                        line_no = issue.get("location", {}).get("row")
                        message = issue.get("message")
                        # Try to get path relative to project_root, fallback to full path
                        display_path = filename
                        try:
                            display_path = Path(filename).relative_to(project_root).as_posix()
                        except ValueError:
                            pass
                        unused.append((display_path, line_no, message))
            except json.JSONDecodeError as e:
                _log_action(
                    action_name,
                    "ERROR",
                    "Failed to parse ruff output (invalid JSON).",
                    details={"exception": str(e), "ruff_raw_output": result_stdout}
                )
                major_action_results.append((action_name, "FAILED_PARSE_OUTPUT"))
                return
            except Exception as e:
                _log_action(
                    action_name,
                    "ERROR",
                    "Failed to process ruff output for unused imports.",
                    details={"exception": str(e)}
                )
                major_action_results.append((action_name, "FAILED_PROCESS_OUTPUT"))
                return

        if unused:
            msg = (
                "Ruff detected unused imports (F401). These may lead to unnecessary dependencies or code cruft:\n" +
                "\n".join([f"  - {f}:{lineno}: {desc}" for f, lineno, desc in unused]) +
                "\nConsider removing these unused imports for a cleaner project and more accurate dependency analysis. "
                "You can typically auto-fix them by running `uvx ruff check . --fix`."
            )
            _log_action(
                action_name,
                "WARN",
                msg,
                details={"unused_imports_count": len(unused), "unused_imports_details": unused}
            )
            major_action_results.append((action_name, "COMPLETED_WITH_WARNINGS"))
        else:
            _log_action(action_name, "SUCCESS", "No unused imports (F401) detected by ruff. Great job!")
            major_action_results.append((action_name, "SUCCESS"))

    except subprocess.CalledProcessError as e:
        _log_action(
            action_name,
            "ERROR",
            "uvx ruff command failed.",
            details={"exception": str(e), "stdout": e.stdout, "stderr": e.stderr}
        )
        major_action_results.append((action_name, "FAILED_CMD_ERROR"))
    except Exception as e:
        _log_action(
            action_name,
            "ERROR",
            "An unexpected error occurred while running/processing ruff.",
            details={"exception": str(e)}
        )
        major_action_results.append((action_name, "FAILED_UNEXPECTED_ERROR"))

def _manage_project_dependencies(
    project_root: Path,
    venv_python_executable: Path,
    pyproject_file_path: Path,
    migration_mode: str,
    dry_run: bool,
    declared_deps_before_management: set[str], # set of base package names from pyproject.toml
    project_imported_packages: set[tuple[str, str]], # set of (base_name, spec) from all sources
):
    """
    Manages project dependencies by migrating from requirements.txt, adding imports,
    and syncing with pyproject.toml based on the configured migration_mode.
    This function centralizes all dependency management logic.
    """
    action_name = "manage_project_dependencies"
    _log_action(action_name, "INFO", f"Starting dependency management with mode: '{migration_mode}', dry-run: {dry_run}.")

    req_path = project_root / LEGACY_REQUIREMENTS_TXT
    req_pkgs_from_file = _get_packages_from_legacy_req_txt(req_path) # set of (base_name, spec)

    # Convert imported_packages to a set of base names for quick lookups
    imported_pkgs_base_names = {base for base, _ in project_imported_packages}

    # Data structures to build up the plan
    packages_to_add_candidate: set[tuple[str, str]] = set() # (base_name, full_specifier)
    packages_to_skip_due_to_mode: set[tuple[str, str]] = set() # (base_name, full_specifier) -- for reasons like 'not imported'
    packages_already_in_pyproject: set[tuple[str, str]] = set() # (base_name, full_specifier)

    # Helper to check if a package (base_name) is already declared in pyproject.toml
    # and adds it to the packages_already_in_pyproject set for detailed logging
    def _check_and_mark_declared(base_name: str, full_spec: str) -> bool:
        if base_name in declared_deps_before_management:
            packages_already_in_pyproject.add((base_name, full_spec))
            return True
        return False

    # --- Determine packages to add based on migration mode ---

    if migration_mode == "skip-requirements":
        _log_action(action_name, "INFO", f"Migration mode set to '{migration_mode}'. Ignoring '{LEGACY_REQUIREMENTS_TXT}'.")
        for base, spec in project_imported_packages:
            if not _check_and_mark_declared(base, spec):
                packages_to_add_candidate.add((base, spec))

    elif migration_mode in ("auto", "only-imported"):
        _log_action(action_name, "INFO", f"Migration mode set to '{migration_mode}'. Will migrate requirements.txt entries only if imported, and add all other imported packages.")

        # 1. Process packages from requirements.txt: prioritize those that are imported
        for base, spec in req_pkgs_from_file:
            if _check_and_mark_declared(base, spec):
                continue # Already declared in pyproject, no need to process further for addition

            if base in imported_pkgs_base_names:
                packages_to_add_candidate.add((base, spec))
            else:
                # Mark as unused from requirements.txt because it's not imported
                packages_to_skip_due_to_mode.add((base, spec))

        # 2. Process packages from project imports: add any that are not already declared or slated for addition
        # This covers imports not found in requirements.txt
        for base, spec in project_imported_packages:
            if not _check_and_mark_declared(base, spec) and (base, spec) not in packages_to_add_candidate:
                packages_to_add_candidate.add((base, spec))

    elif migration_mode == "all-requirements":
        _log_action(action_name, "INFO", f"Migration mode set to '{migration_mode}'. Will add all dependencies from '{LEGACY_REQUIREMENTS_TXT}' and then all imported packages.")

        # 1. Process packages from requirements.txt first
        for base, spec in req_pkgs_from_file:
            if not _check_and_mark_declared(base, spec):
                packages_to_add_candidate.add((base, spec))

        # 2. Process packages from project imports. Add any that are not already declared in pyproject.toml
        # AND not already added from requirements.txt in this run.
        currently_added_base_names = {base for base, _ in packages_to_add_candidate}
        for base, spec in project_imported_packages:
            if not _check_and_mark_declared(base, spec) and base not in currently_added_base_names:
                packages_to_add_candidate.add((base, spec))

    else:
        _log_action(action_name, "ERROR", f"Invalid dependency migration mode: {migration_mode}. No dependencies will be added/managed.")
        return

    # Final sorted list for consistent logging and action
    final_packages_to_add: list[tuple[str, str]] = sorted(list(packages_to_add_candidate), key=lambda x: x[0])
    all_skipped_info_for_log: list[tuple[str, str, str]] = [] # (base_name, spec, reason)

    # Collect all skipped packages with their reasons
    for base, spec in packages_already_in_pyproject:
        all_skipped_info_for_log.append((base, spec, "already in pyproject.toml"))
    for base, spec in packages_to_skip_due_to_mode:
        all_skipped_info_for_log.append((base, spec, "not imported (unused from requirements.txt)"))
    all_skipped_info_for_log = sorted(all_skipped_info_for_log, key=lambda x: x[0])

    # --- Dry run output ---
    if dry_run:
        msg = (
            "\n--- DRY RUN: Dependency Management Summary ---\n"
            f"Mode: {migration_mode}\n"
            f"Would add: {[spec for base, spec in final_packages_to_add] if final_packages_to_add else 'None'}\n"
            f"Would skip: {[f'{spec} ({reason})' for base, spec, reason in all_skipped_info_for_log] if all_skipped_info_for_log else 'None'}\n"
            "This was a dry run. No changes were made.\nTo perform the dependency management, re-run without the --dry-run flag."
        )
        _log_action(action_name + "_dry_run", "INFO", msg)
        return

    # --- Actually add dependencies with robust hybrid strategy ---
    successfully_added_specs = []
    failed_to_add_specs = []

    if final_packages_to_add:
        packages_to_add_specs_only = [spec for _, spec in final_packages_to_add]
        _log_action(action_name, "INFO", f"Attempting to add {len(packages_to_add_specs_only)} new package(s) to '{PYPROJECT_TOML_NAME}'.")

        try:
            # Stage 1: Try bulk add for efficiency (v7.3 hybrid strategy)
            _log_action(action_name, "INFO", "Attempting a fast bulk-add operation...")
            _run_command(["uv", "add"] + packages_to_add_specs_only, "uv_add_bulk")
            successfully_added_specs.extend(packages_to_add_specs_only)
        except Exception:
            # Stage 2: Individual fallback for robustness
            _log_action(action_name, "WARN", "Bulk 'uv add' failed. Falling back to adding packages individually for robustness.")
            for base, spec in final_packages_to_add:
                try:
                    _run_command(["uv", "add", spec], f"uv_add_individual_{base}")
                    successfully_added_specs.append(spec)
                except Exception:
                    failed_to_add_specs.append(spec)
    else:
        _log_action(action_name, "INFO", "No new dependencies identified for addition based on mode and existing declarations.")

    if successfully_added_specs:
        _log_action(action_name, "SUCCESS", f"Successfully added {len(successfully_added_specs)} packages.", details={"packages": successfully_added_specs})
    if failed_to_add_specs:
        _log_action(action_name, "ERROR", f"Failed to add {len(failed_to_add_specs)} packages.", details={"failed_packages": failed_to_add_specs})

    # --- Final Summary and Advice ---
    summary_lines = [
        "\n--- Dependency Management Final Summary ---",
        f"Mode: {migration_mode}",
        f"Total packages from requirements.txt scanned: {len(req_pkgs_from_file)}",
        f"Total packages from code (scripts/notebooks) discovered: {len(project_imported_packages)}",
        f"Total packages declared in pyproject.toml initially: {len(declared_deps_before_management)}",
        f"Packages Added to {PYPROJECT_TOML_NAME}: {successfully_added_specs if successfully_added_specs else 'None'}",
        f"Packages Skipped: {[f'{spec} ({reason})' for base, spec, reason in all_skipped_info_for_log] if all_skipped_info_for_log else 'None'}",
        f"Packages Failed to Add: {failed_to_add_specs if failed_to_add_specs else 'None'}",
    ]
    summary_table = "\n".join(summary_lines)
    _log_action(action_name + "_final_summary", "INFO", summary_table)

    # Actionable advice
    if failed_to_add_specs:
        advice = (
            f"Some dependencies could not be added to '{PYPROJECT_TOML_NAME}'.\n"
            f"Please review the errors above and try adding them manually, e.g.:\n  uv add <package>\n"
            f"You may also need to check for typos or unsupported specifiers.\n"
        )
        _log_action(action_name + "_advice_failed", "WARN", advice, details={"failed": failed_to_add_specs})

    # Always give advice on requirements.txt if it exists
    if req_path.exists():
        if successfully_added_specs or failed_to_add_specs:
            advice = (
                f"The original '{LEGACY_REQUIREMENTS_TXT}' was NOT modified by this script.\n"
                f"To keep your project modern and reproducible, '{PYPROJECT_TOML_NAME}' is now the primary source of truth.\n"
                f"If you need '{LEGACY_REQUIREMENTS_TXT}' for other tools (e.g., legacy CI/CD), regenerate it with:\n"
                f"  uv pip compile {PYPROJECT_TOML_NAME} -o {LEGACY_REQUIREMENTS_TXT}"
            )
            _log_action(action_name + "_advice_req_txt", "INFO", advice)
        elif not final_packages_to_add and all_skipped_info_for_log: # reqs.txt exists, but nothing new was added
            advice = (
                f"No new dependencies were added from '{LEGACY_REQUIREMENTS_TXT}' as they were either already declared or not applicable to the '{migration_mode}' mode.\n"
                f"Consider archiving or deleting '{LEGACY_REQUIREMENTS_TXT}' to avoid confusion.\n"
                f"If you wish to regenerate it from '{PYPROJECT_TOML_NAME}' for legacy tools, run:\n"
                f"  uv pip compile {PYPROJECT_TOML_NAME} -o {LEGACY_REQUIREMENTS_TXT}"
            )
            _log_action(action_name + "_advice_nothing_added_from_req", "INFO", advice)
    else:
        _log_action(action_name, "INFO", f"No '{LEGACY_REQUIREMENTS_TXT}' found in the project root. No migration from legacy requirements was attempted.")

    _log_action(action_name, "SUCCESS", f"Dependency management completed for mode: '{migration_mode}'.")


def _configure_vscode_settings(project_root: Path, venv_python_executable: Path, dry_run: bool):
    """
    Ensure .vscode/settings.json exists and sets python.defaultInterpreterPath to the venv Python.
    If settings.json is invalid JSON, back it up before overwriting. Only update the interpreter path, preserve other settings.
    Adds a comment to clarify uv integration.
    """
    action_name = "configure_vscode_settings"
    _log_action(action_name, "INFO", f"Configuring VS Code settings in '{VSCODE_DIR_NAME}'.")
    vscode_dir_path = project_root / VSCODE_DIR_NAME
    settings_file_path = vscode_dir_path / SETTINGS_FILE_NAME
    vscode_dir_path.mkdir(exist_ok=True)
    settings_data = {}
    backup_made = False

    if dry_run:
        _log_action(action_name, "INFO", f"DRY RUN: Would set 'python.defaultInterpreterPath' to '{venv_python_executable}' in '{settings_file_path.name}'. No actual file changes made.")
        return

    if settings_file_path.exists():
        try:
            with open(settings_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    settings_data = json.loads(content) # Attempt to parse existing content
        except json.JSONDecodeError:
            # Backup invalid JSON before overwriting
            backup_path = settings_file_path.with_suffix(f".bak_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
            shutil.copy2(settings_file_path, backup_path)
            backup_made = True
            _log_action(action_name, "WARN", f"Existing '{settings_file_path.name}' is not valid JSON. Backed up before overwrite.", details={"backup": str(backup_path)})
            settings_data = {} # Start with empty settings if original was invalid
        except Exception as e:
            _log_action(action_name, "WARN", f"Could not read existing '{settings_file_path.name}': {e}. It may be overwritten.", details={"exception": str(e)})
            settings_data = {} # Start with empty settings if error reading


    interpreter_path = str(venv_python_executable)
    settings_data["python.defaultInterpreterPath"] = interpreter_path

    # Construct the final content: comment + JSON string
    comment_line = "// This interpreter path is managed by pyuvstarter and uv (https://astral.sh/uv)"
    json_content_str = json.dumps(settings_data, indent=4)

    final_file_content = json_content_str
    # Check if the comment is already the first line, to avoid duplicating it
    current_first_line_exists = False
    if settings_file_path.exists():
        try:
            with open(settings_file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith("// This interpreter path is managed by pyuvstarter"):
                    current_first_line_exists = True
        except Exception:
            # If reading fails, assume no relevant first line exists or is readable
            pass

    if not current_first_line_exists:
        final_file_content = comment_line + "\n" + json_content_str

    with open(settings_file_path, 'w', encoding='utf-8') as f:
        f.write(final_file_content)

    msg = f"VS Code 'python.defaultInterpreterPath' set.{' (Backed up old file)' if backup_made else ''}\n      Path: {interpreter_path}\n      (Managed by pyuvstarter and uv)"
    _log_action(action_name, "SUCCESS", msg, details={"interpreter_path": interpreter_path})

def _ensure_vscode_launch_json(project_root: Path, venv_python_executable: Path, dry_run: bool):
    """
    Ensure .vscode/launch.json exists and has a launch config for the currently active Python file using the venv Python.
    If launch.json is invalid JSON, back it up before overwriting. Only add a new config if needed, never remove user configs.
    The launch config is maximally integrated with uv: it uses the venv interpreter and is generic for any Python file.
    """
    action_name = "ensure_vscode_launch_json"
    _log_action(action_name, "INFO", f"Ensuring VS Code launch.json exists in '{VSCODE_DIR_NAME}'.")
    vscode_dir = project_root / VSCODE_DIR_NAME
    launch_path = vscode_dir / LAUNCH_FILE_NAME
    vscode_dir.mkdir(exist_ok=True)
    # Use ${file} so the user can run any Python file they have open in the editor
    default_config_entry = {
        "name": "Python: Run Current File (uv venv)",
        "type": "python",
        "request": "launch",
        "program": "${file}",
        "console": "integratedTerminal",
        "python": str(venv_python_executable),
        "justMyCode": True,
        "internalConsoleOptions": "neverOpen",
        # "env": {},  # Removed to let VS Code inherit the environment, including venv activation
        "cwd": "${workspaceFolder}",
        "args": [],
        "description": "Runs the currently open Python file using the uv-managed virtual environment."
    }
    default_file_content = {
        "version": "0.2.0",
        "configurations": [default_config_entry]
    }

    if dry_run:
        _log_action(action_name, "INFO", f"DRY RUN: Would ensure launch configuration for '{venv_python_executable}' in '{launch_path.name}'. No actual file changes made.")
        return

    try:
        if launch_path.exists():
            try:
                with open(launch_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                configs = data.get("configurations", [])

                # v7.3 Bug Fix: Check both name AND python interpreter path to prevent stale configurations
                # Note: venv_python_executable might be relative to project_root, but VS Code usually resolves it
                # For robustness, comparing against both original string and resolved path.
                venv_python_executable_str = str(venv_python_executable)
                venv_python_executable_resolved_str = str(venv_python_executable.resolve())

                already_present = any(
                    c.get("type") == "python" and
                    c.get("name") == default_config_entry["name"] and
                    (c.get("python") == venv_python_executable_str or c.get("python") == venv_python_executable_resolved_str)
                    for c in configs
                )

                if not already_present:
                    configs.append(default_config_entry)
                    data["configurations"] = configs
                    with open(launch_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                    _log_action(action_name, "SUCCESS", "Added launch config for current file to existing launch.json.")
                else:
                    _log_action(action_name, "INFO", "Launch config for current file and uv venv already present in launch.json.")
            except json.JSONDecodeError:
                backup_path = launch_path.with_suffix(f".bak_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
                shutil.copy2(launch_path, backup_path)
                _log_action(action_name, "WARN", f"Existing '{launch_path.name}' is not valid JSON. Backed up before overwrite.", details={"backup": str(backup_path)})
                with open(launch_path, "w", encoding="utf-8") as f:
                    json.dump(default_file_content, f, indent=4)
                _log_action(action_name, "SUCCESS", "Created new launch.json for current file. (Backed up old file)")
            except Exception as e:
                _log_action(action_name, "ERROR", f"Could not update existing launch.json: {e}")
        else:
            with open(launch_path, "w", encoding="utf-8") as f:
                json.dump(default_file_content, f, indent=4)
            _log_action(action_name, "SUCCESS", "Created new launch.json for current file.")
    except Exception as e:
        _log_action(action_name, "ERROR", f"Failed to create or update launch.json: {e}")

def _detect_notebook_systems(nb_path: Path) -> set[str]:
    """
    Detects which notebook execution systems are referenced in a notebook's metadata.

    This enhanced version inspects multiple keys within the notebook's JSON structure
    to provide more accurate runtime detection. It is designed to be easily extensible.

    Args:
        nb_path: The Path object for the notebook to inspect.

    Returns:
        A set of identified system names (e.g., {'jupyter', 'quarto'}).
    """
    systems = set()
    try:
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        # The metadata block is the primary source of truth for environment info.
        meta = nb.get("metadata", {})
        if not meta:
            return systems # No metadata, nothing to detect.

        # --- Detection Logic for Different Systems ---

        # 1. Jupyter: The presence of 'kernelspec' is the strongest indicator.
        #    'language_info' is also a common key in Jupyter-generated notebooks.
        if "kernelspec" in meta or "language_info" in meta:
            systems.add("jupyter")

        # 2. Quarto: Quarto notebooks explicitly add a 'quarto' key to the metadata.
        if "quarto" in meta:
            systems.add("quarto")
            # Quarto often runs on a Jupyter kernel, so we can infer Jupyter support is also needed.
            systems.add("jupyter")

        # 3. Google Colab: Colab notebooks include a 'colab' dictionary in their metadata.
        if "colab" in meta:
            # Colab is a Jupyter-compatible environment, so it requires Jupyter dependencies.
            systems.add("jupyter")

        # 4. VS Code: VS Code's notebook editor may add its own metadata.
        if "vscode" in meta:
             # VS Code also uses Jupyter kernels.
             systems.add("jupyter")

        # Scan code cells for magics or imports that imply a system.
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code":
                for line in cell.get("source", []):
                    line_lower = line.strip().lower()
                    if "import polars_notebook" in line_lower:
                        systems.add("polars-notebook")
                    # Any common magic command often implies a jupyter-like environment.
                    if line_lower.startswith("%") and any(x in line_lower for x in ["matplotlib", "pip", "sql"]):
                        systems.add("jupyter")

    except (json.JSONDecodeError, IOError) as e:
        _log_action("notebook_system_detect", "WARN", f"Could not inspect metadata in '{nb_path.name}' due to a file read or JSON parse error.", details={"exception": str(e)})

    return systems

def _ensure_notebook_execution_support(project_root: Path, dry_run: bool) -> bool:
    """
    Ensures dependencies for running notebooks (like `ipykernel`) are installed.
    This is separate from code dependencies (like `pandas`). It detects the
    notebook "system" (e.g., Jupyter) and adds its required packages.

    Returns:
        True if successful or no action needed, False if errors occurred.
    """
    action_name = "ensure_notebook_execution_support"
    notebook_paths = _find_all_notebooks(project_root)
    if not notebook_paths:
        # No notebooks, nothing to do.
        return True

    _log_action(action_name, "INFO", "Checking for notebook execution support dependencies (e.g., ipykernel).")

    # Detect all unique systems required by all notebooks in the project.
    systems_needed = set()
    for nb_path in notebook_paths:
        systems_needed.update(_detect_notebook_systems(nb_path))

    if not systems_needed:
        _log_action(action_name, "INFO", "No specific notebook execution system (like Jupyter) was detected. Skipping support package installation.")
        return True

    _log_action(action_name, "INFO", f"Detected required notebook systems: {sorted(list(systems_needed))}.")

    # Get dependencies already declared in pyproject.toml.
    pyproject_path = project_root / PYPROJECT_TOML_NAME
    declared_deps = _get_declared_dependencies(pyproject_path)

    # Determine which required support packages are missing.
    packages_to_add = set()
    for system in systems_needed:
        for pkg in _NOTEBOOK_SYSTEM_DEPENDENCIES.get(system, []):
            if pkg.lower() not in declared_deps:
                packages_to_add.add(pkg)

    if packages_to_add:
        _log_action(action_name, "INFO", f"Adding missing notebook execution packages: {sorted(list(packages_to_add))}")
        if dry_run:
            _log_action(action_name, "INFO", f"DRY RUN: Would add notebook execution packages: {sorted(list(packages_to_add))}")
            return True
        else:
            try:
                # Use a single `uv add` command for efficiency.
                _run_command(["uv", "add"] + sorted(list(packages_to_add)), f"{action_name}_uv_add")
                _log_action(action_name, "SUCCESS", f"Successfully added notebook execution packages: {sorted(list(packages_to_add))}")
                return True
            except Exception as e:
                _log_action(action_name, "ERROR", f"Failed to add notebook support packages: {e}\n      ACTION: Please try adding them manually: uv add {' '.join(sorted(list(packages_to_add)))}")
                return False
    else:
        _log_action(action_name, "INFO", "All required notebook execution support packages are already declared in pyproject.toml.")
        return True

######################################################################
# MAIN ORCHESTRATION FUNCTION
######################################################################
def main():
    args = parse_args()
    if getattr(args, "version", False):
        version = _get_project_version(Path(__file__).parent / "pyproject.toml", "pyuvstarter")
        _log_action("show_version", "INFO", f"pyuvstarter version: {version}")
        sys.exit(0)
    project_root = Path(args.project_dir).expanduser().resolve()

    # Change to project root directory for consistent, safe operation
    # This ensures all file operations and commands work relative to the project root
    original_cwd = Path.cwd()
    if original_cwd != project_root:
        _log_action("change_directory", "INFO", f"Changing working directory from {original_cwd} to {project_root}")
        os.chdir(project_root)

    log_file_path = project_root / JSON_LOG_FILE_NAME
    _init_log(project_root)

    pyproject_file_path = project_root / PYPROJECT_TOML_NAME

    # Enhanced startup banner with clear information
    banner_lines = [
        "🚀 PYUVSTARTER - Modern Python Project Automation",
        f"Version: {_log_data_global.get('pyuvstarter_version', 'unknown')}",
        f"Project Directory: {project_root}",
        f"Virtual Environment: {VENV_NAME}",
        f"Dependency File: {PYPROJECT_TOML_NAME}",
        f"Migration Mode: {args.dependency_migration}",
        f"Dry Run: {'Yes - Preview Only' if args.dry_run else 'No - Making Changes'}",
        f"Execution Log: {log_file_path.name}",
        "─" * 60,
        "This tool will automate your Python project setup using the modern uv ecosystem.",
        "✓ Discover dependencies from .py files and Jupyter notebooks",
        "✓ Configure VS Code with proper interpreter and launch configs",
        "✓ Set up comprehensive .gitignore and project structure",
        "✓ Perform code quality checks and provide actionable guidance",
        "─" * 60
    ]

    startup_banner = "\n".join(banner_lines)
    _log_action("script_start", "INFO", startup_banner)

    venv_python_executable = None
    settings_json_status = "NOT_ATTEMPTED"
    launch_json_status = "NOT_ATTEMPTED"
    major_action_results = [] # To populate the final summary table

    try:
        # 1. Ensure uv is installed
        if not _ensure_uv_installed(args.dry_run):
            _log_action("ensure_uv_installed", "ERROR", "Halting: `uv` could not be installed or verified. Check log and console output for details.")
            raise SystemExit("Halting: `uv` could not be installed or verified. Check log and console output for details.")
        major_action_results.append(("uv_installed", "SUCCESS"))

        # 2. Ensure pyproject.toml exists and remove main.py if conditional
        if not _ensure_project_initialized(project_root, args.dry_run):
            _log_action("ensure_project_initialized", "ERROR", f"Halting: Project could not be initialized with '{PYPROJECT_TOML_NAME}'. Check log and console output.")
            raise SystemExit(f"Halting: Project could not be initialized with '{PYPROJECT_TOML_NAME}'. Check log and console output.")
        major_action_results.append(("project_initialized", "SUCCESS"))

        # 3. Ensure .gitignore exists
        _ensure_gitignore_exists(project_root, VENV_NAME, args.dry_run)
        major_action_results.append(("gitignore", "SUCCESS"))

        # 4. Create/verify virtual environment
        action_venv = "create_or_verify_venv"
        _log_action(action_venv, "INFO", f"Creating/ensuring virtual environment '{VENV_NAME}'.")
        _run_command(["uv", "venv", VENV_NAME], f"{action_venv}_uv_venv", dry_run=args.dry_run)

        venv_path = project_root / VENV_NAME
        venv_python_executable = venv_path / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")

        # In dry-run, we assume the venv path for subsequent steps, no actual existence check
        if not args.dry_run and not venv_python_executable.exists():
            msg = f"Virtual environment Python executable not found at '{venv_python_executable}' after `uv venv` command."
            _log_action(action_venv, "ERROR", msg)
            raise SystemExit(f"CRITICAL ERROR: {msg}\n       This indicates a problem with `uv venv` or an unexpected environment structure.")
        elif args.dry_run:
            _log_action(action_venv, "INFO", f"In dry-run mode: assuming virtual environment '{VENV_NAME}' would be ready and Python executable at '{venv_python_executable}'.")
        else:
            _log_action(action_venv, "SUCCESS", f"Virtual environment '{VENV_NAME}' ready. Interpreter: '{venv_python_executable}'.")
        major_action_results.append(("venv_ready", "SUCCESS"))

        # 5. Ensure tools for dependency discovery and linting are available via uv tool install
        _ensure_tool_available("pipreqs", major_action_results, args.dry_run, website="https://github.com/bndr/pipreqs")
        _ensure_tool_available("ruff", major_action_results, args.dry_run, website="https://docs.astral.sh/ruff/")

        # 6. Pre-flight: Ruff unused import detection
        # Run in dry-run mode too, as it provides valuable info without side-effects.
        _run_ruff_unused_import_check(project_root, major_action_results, args.dry_run)

        # 7. Consolidated Dependency Discovery from all sources
        declared_deps_before_management = _get_declared_dependencies(pyproject_file_path)
        all_discovered_packages = _discover_all_code_dependencies(project_root, VENV_NAME, args.dry_run)
        major_action_results.append(("code_dep_discovery", "SUCCESS"))

        # 8. Centralized Dependency Management (using all discovered packages)
        _manage_project_dependencies(
            project_root=project_root,
            venv_python_executable=venv_python_executable,
            pyproject_file_path=pyproject_file_path,
            migration_mode=args.dependency_migration,
            dry_run=args.dry_run,
            declared_deps_before_management=declared_deps_before_management,
            project_imported_packages=all_discovered_packages
        )
        major_action_results.append(("dependency_management", "SUCCESS"))

        # 9. Notebook Execution Support (Orthogonal Concern)
        # This runs after dependency management to ensure support packages are also added.
        notebook_exec_success = _ensure_notebook_execution_support(project_root, args.dry_run)
        if notebook_exec_success:
            major_action_results.append(("notebook_exec_support", "SUCCESS"))
        else:
            major_action_results.append(("notebook_exec_support", "FAILED"))

        # 10. Final Sync environment (after all potential `uv add` calls)
        action_sync = "uv_sync_dependencies"
        _log_action(action_sync, "INFO", "Performing final sync of environment with `pyproject.toml` and `uv.lock` using `uv sync`.")
        _run_command(["uv", "sync", "--python", str(venv_python_executable)], f"{action_sync}_exec", dry_run=args.dry_run)
        _log_action(action_sync, "SUCCESS", "Environment synced with `pyproject.toml` and `uv.lock`.")
        major_action_results.append(("uv_final_sync", "SUCCESS"))

        # 11. VS Code config
        _configure_vscode_settings(project_root, venv_python_executable, args.dry_run)
        settings_json_status = "SUCCESS"
        _ensure_vscode_launch_json(project_root, venv_python_executable, args.dry_run)
        launch_json_status = "SUCCESS"
        major_action_results.append(("vscode_config", "SUCCESS"))

        _log_action("script_end", "SUCCESS", "🎉 Automated project setup script completed successfully!")

        # --- File summary table ---
        explicit_summary = _get_explicit_summary_text(project_root, VENV_NAME, pyproject_file_path, log_file_path)
        _log_action("explicit_summary", "INFO", explicit_summary)

        # --- Project summary table ---
        summary_lines = [
            "\n--- Project Setup Summary ---",
            "Step                        | Status",
            "-----------------------------|--------",
        ]
        for step, status in major_action_results:
            summary_lines.append(f"{step.ljust(28)}| {status}")
        summary_lines.append(f"\nSee '{JSON_LOG_FILE_NAME}' for full details.")
        summary_table = "\n".join(summary_lines)
        _log_action("final_summary_table", "INFO", summary_table)

        # If any errors or warnings, print/log a final warning
        errors_or_warnings = any(
            a.get("status", "").upper() in ("ERROR", "WARN")
            for a in _log_data_global.get("actions", [])
        )
        if errors_or_warnings:
            warn_msg = f"\n⚠️  Some warnings/errors occurred during setup. See '{log_file_path.name}' for details."
            _log_action("final_warning", "WARN", warn_msg)

    except SystemExit as e:
        msg = f"Script halted by explicit exit: {e}"
        settings_json_status = "FAILED"
        launch_json_status = "FAILED"
        if _log_data_global.get("overall_status") == "IN_PROGRESS":
            _log_data_global["overall_status"] = "HALTED_BY_SCRIPT_LOGIC"
        _log_data_global["final_summary"] = _log_data_global.get("final_summary", "") + msg
        _log_action("script_halted", "ERROR", f"\nSCRIPT HALTED: {e}")
    except subprocess.CalledProcessError as e:
        failed_cmd_str = ' '.join(e.cmd) if isinstance(e.cmd, list) else str(e.cmd)
        msg = f"A critical command failed execution: {failed_cmd_str}"
        settings_json_status = "FAILED"
        launch_json_status = "FAILED"
        _log_data_global["final_summary"] = msg
        _log_data_global["overall_status"] = "CRITICAL_COMMAND_FAILED"
        _log_action("critical_command_failed", "ERROR", f"\nCRITICAL ERROR: {msg}, halting script.\n  Details of the failed command should be visible in the output above and in the JSON log.")
        cmd_str_lower = failed_cmd_str.lower()
        if "uv pip install" in cmd_str_lower or "uv add" in cmd_str_lower or "uv sync" in cmd_str_lower:
            _log_action("install_sync_hint", "WARN", "INSTALLATION/SYNC HINT: A package operation with `uv` failed.\n  - Review `uv`'s error output (logged as FAIL_STDOUT/FAIL_STDERR for the command) for specific package names or reasons.\n  - Ensure the package name is correct and exists on PyPI (https://pypi.org) or your configured index.\n  - Some packages require system-level (non-Python) libraries to be installed first. Check the package's documentation.\n  - You might need to manually edit '{PYPROJECT_TOML_NAME}' and then run `uv sync --python {venv_python_executable}`.")
        elif "pipreqs" in cmd_str_lower:
            _log_action("pipreqs_hint", "WARN", "PIPReQS HINT: The 'pipreqs' command (run via 'uvx') failed.\n  - This could be due to syntax errors in your Python files that `pipreqs` cannot parse, an internal `pipreqs` issue, or `uvx` failing to execute `pipreqs`.\n  - Try running manually for debug: uvx pipreqs \"{project_root}\" --ignore \"{VENV_NAME}\" --debug")
        elif "uv venv" in cmd_str_lower:
            _log_action("uv_venv_hint", "WARN", "VIRTUAL ENV HINT: `uv venv` command failed.\n  - Ensure `uv` is correctly installed and functional. Check `uv --version`.\n  - Check for issues like insufficient disk space or permissions in the project directory '{project_root}'.")
        elif "uv tool install" in cmd_str_lower:
            _log_action("uv_tool_install_hint", "WARN", "UV TOOL INSTALL HINT: `uv tool install` (likely for pipreqs) failed.\n  - This could be due to network issues, `uv` problems, or the tool package ('pipreqs') not being found by `uv`.\n  - Try running `uv tool install pipreqs` manually in your terminal.")
        elif "uv init" in cmd_str_lower:
            _log_action("uv_init_hint", "WARN", "UV INIT HINT: `uv init` command failed.\n  - Ensure `uv` is correctly installed. Try running `uv init` manually in an empty directory to test.\n   - Check for permissions issues in the project directory '{project_root}'.")
        elif "brew" in cmd_str_lower:
            _log_action("brew_hint", "WARN", "Homebrew might be required for some installations. Ensure it's installed and working.")
        sys.exit(1)
    except FileNotFoundError as e:
        cmd_name = e.filename if hasattr(e, 'filename') and e.filename else "An external command"
        settings_json_status = "FAILED"
        launch_json_status = "FAILED"
        msg = f"Required system command '{cmd_name}' was not found."
        _log_data_global["final_summary"] = msg
        _log_data_global["overall_status"] = "MISSING_SYSTEM_COMMAND"
        _log_action("missing_system_command", "ERROR", f"\nCRITICAL ERROR: {msg} Setup aborted.\n       Please install '{cmd_name}' or ensure it's in your system's PATH.")
        if cmd_name == "brew":
            _log_action("brew_hint", "WARN", "For Homebrew on macOS, see https://brew.sh/")
        if cmd_name == "curl":
            _log_action("curl_hint", "WARN", "For curl, see your OS package manager (e.g., 'sudo apt install curl' or 'sudo yum install curl').")
        sys.exit(1)
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        settings_json_status = "FAILED"
        launch_json_status = "FAILED"
        msg = f"An unexpected critical error occurred: {e}"
        _log_action("unexpected_critical_error_main", "ERROR", msg, details={"exception_type": type(e).__name__, "exception_message": str(e), "traceback": tb_str.splitlines()})
        _log_action("unexpected_critical_error_main_print", "ERROR", f"\nAN UNEXPECTED CRITICAL ERROR OCCURRED: {e}\n{tb_str}\nSetup aborted due to an unexpected error. Please review the traceback and the JSON log.")
        _log_data_global["final_summary"] = msg
        _log_data_global["overall_status"] = "UNEXPECTED_ERROR"
        sys.exit(1)
    finally:
        # Update summary in log with VS Code config status
        if "start_time_utc" in _log_data_global: # Only save if _init_log was called successfully
            _log_data_global["vscode_settings_json_status"] = settings_json_status
            _log_data_global["vscode_launch_json_status"] = launch_json_status
            _save_log(log_file_path, project_root)

def _get_explicit_summary_text(project_root: Path, venv_name: str, pyproject_file_path: Path, log_file_path: Path):
    """
    Returns a legacy-style explicit summary of all key files and paths for user clarity.
    """
    vscode_settings = project_root / VSCODE_DIR_NAME / SETTINGS_FILE_NAME
    vscode_launch = project_root / VSCODE_DIR_NAME / LAUNCH_FILE_NAME
    summary_lines = [
        "\n--- Project Setup Files Summary ---",
        f"Project root:           {project_root}",
        f"Virtual environment:    {project_root / venv_name}",
        f"Dependency file:        {pyproject_file_path}",
        f"Lock file:              {project_root / 'uv.lock'}",
        f"VS Code settings:       {vscode_settings}",
        f"VS Code launch config:  {vscode_launch}",
        f"Git ignore file:        {project_root / GITIGNORE_NAME}",
        f"Setup log:              {log_file_path}",
    ]
    return "\n".join(summary_lines)

if __name__ == "__main__":
    main()
