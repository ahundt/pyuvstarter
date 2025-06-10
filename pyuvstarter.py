#!/usr/bin/env python3
"""
pyuvstarter.py (v6.6 - Conditional main.py removal)

Copyright (c) 2025 Andrew Hundt

Purpose:
This script automates the setup of a Python project environment using `uv`,
focusing on `pyproject.toml` for dependency management, configures Visual
Studio Code, and prepares the project for version control by ensuring a
`.gitignore` file is present. It operates without user prompts for a standard
setup and creates a detailed JSON log file of its actions. It uses `uv init`
to create `pyproject.toml` if missing, and conditionally removes `main.py`
if `uv init` creates it in a directory that already contained other Python files.

Key Actions:
1. Ensures `uv` is installed (platform-aware installation if missing).
2. Ensures a `pyproject.toml` file exists, running `uv init` if necessary.
   If `uv init` creates `main.py` in a pre-existing Python project, `main.py` is removed.
3. Ensures a `.gitignore` file exists with common Python/venv exclusions.
4. Creates a virtual environment (default: '.venv') using `uv venv`.
5. Migrates dependencies from an existing 'requirements.txt' (if present and not
   already in `pyproject.toml`) by adding them to `pyproject.toml` using `uv add`.
   The original 'requirements.txt' is NOT modified; user is advised.
6. Installs all declared dependencies from `pyproject.toml` and `uv.lock` using `uv sync`.
7. Ensures `pipreqs` is available (installs via `uv tool install` if missing).
8. Scans project Python files using `pipreqs` (via `uvx`) to discover imported packages.
9. For newly discovered packages not already in `pyproject.toml`, automatically adds
   them using `uv add <package>`. This updates `pyproject.toml` and `uv.lock`.
10. Configures VS Code's 'python.defaultInterpreterPath' in '.vscode/settings.json'.
11. Logs all major actions, command executions, statuses, and errors to a
    'pyuvstarter_setup_log.json' file.

How to Use:
1. Prerequisites:
   - Python 3 (Python 3.11+ recommended for full `pyproject.toml` parsing via `tomllib`).
   - System tools for `uv` installation if `uv` is not yet installed:
     - macOS: Homebrew (https://brew.sh/) preferred, or `curl`.
     - Linux: `curl`.
     - Windows: PowerShell.
   - (Optional) An existing 'requirements.txt' file if migrating an old project.

2. Placement:
   - Save this script as 'pyuvstarter.py' (or your preferred name) in the
     root directory of your new or existing Python project.

3. Execution:
   - Open your terminal or command prompt.
   - Navigate to the project root (the directory containing this script).
   - Make executable (Linux/macOS): `chmod +x pyuvstarter.py`
   - Run: `./pyuvstarter.py` (or `python3 pyuvstarter.py`)

Outcome:
- A `pyproject.toml` will define project dependencies.
- A `.gitignore` file will be present.
- A '.venv' directory will contain the Python virtual environment.
- A `uv.lock` file will ensure reproducible dependency resolution.
- Dependencies (migrated, declared, and discovered) will be installed.
- '.vscode/settings.json' will be configured.
- A 'pyuvstarter_setup_log.json' file will detail the script's execution.
- The script will print recommended next steps to the console, and these will
  also be included in the JSON log if the script completes without critical failure.
- you should source the virtual environment in your terminal:
    - `source .venv/bin/activate` (Linux/macOS)
    - `.venv\\Scripts\\activate` (Windows PowerShell)

Committing to Git:
- After running, you should typically commit:
  - `pyuvstarter.py` (this script itself if it's part of the project)
  - `pyproject.toml`
  - `uv.lock`
  - `.gitignore`
  - Your actual project source code.
  - `.vscode/settings.json` (optional, if you want to share VS Code settings).
- Do NOT commit the `.venv/` directory or the `pyuvstarter_setup_log.json` file
  (this script adds them to `.gitignore`).


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
import shutil
import subprocess
import importlib
import datetime
import platform
import argparse

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

# --- Argument Parsing ---
def parse_args():
    parser = argparse.ArgumentParser(
        description="Automate Python project setup with uv, VS Code config, and dependency management."
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
        help="Dependency migration mode: 'auto' (default, smart), 'all-requirements' (migrate all requirements.txt), 'only-imported' (only migrate actually imported), 'skip-requirements' (ignore requirements.txt)."
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

# --- Modular requirements.txt migration supporting new modes ---
def migrate_requirements_modular(
    project_root,
    venv_python_executable,
    pyproject_file_path,
    migration_mode,
    dry_run,
    declared_deps_before_migration
):
    """
    Migrate requirements.txt to pyproject.toml in a robust, user-friendly, and modern way.
    Supports multiple migration modes and dry-run. All user-facing actions are logged and printed.
    """
    req_path = project_root / LEGACY_REQUIREMENTS_TXT
    if not req_path.exists():
        _log_action("migrate_modern_requirements", "INFO", f"No '{LEGACY_REQUIREMENTS_TXT}' found, skipping modular migration step.")
        return
    with open(req_path, "r", encoding="utf-8") as f:
        req_lines = [line.strip() for line in f if line.strip() and not line.startswith("#") and not line.startswith("-e")]
    imported_pkgs = set()
    if migration_mode in ("auto", "only-imported"):
        try:
            pipreqs_args = ["uvx", "pipreqs", "--print", "--ignore", VENV_NAME, str(project_root)]
            stdout, _ = _run_command(pipreqs_args, "pipreqs_discover_imports", suppress_console_output_on_success=True)
            for line in stdout.splitlines():
                pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("!=")[0].split("~=")[0].strip().lower()
                if pkg:
                    imported_pkgs.add(pkg)
        except Exception:
            _log_action("migrate_modern_requirements", "WARN", "Could not run pipreqs for import-based discovery. Proceeding without it.")
    req_pkgs = set()
    for line in req_lines:
        base = line.split("[")[0].split("=")[0].split(">=")[0].split("<=")[0].split("!=")[0].split("~=")[0].strip().lower()
        req_pkgs.add((base, line))
    to_add = []
    skipped = []
    for base, spec in req_pkgs:
        if base in declared_deps_before_migration:
            skipped.append((base, spec, "already in pyproject.toml"))
            continue
        if migration_mode == "all-requirements":
            to_add.append((base, spec))
        elif migration_mode == "skip-requirements":
            skipped.append((base, spec, "mode=skip-requirements"))
        elif migration_mode == "only-imported":
            if base in imported_pkgs:
                to_add.append((base, spec))
            else:
                skipped.append((base, spec, "not imported"))
        elif migration_mode == "auto":
            if base in imported_pkgs:
                to_add.append((base, spec))
            else:
                skipped.append((base, spec, "not imported (auto mode)"))
    # Dry run output
    if dry_run:
        msg = ("\n--- DRY RUN: Dependency Migration (modular) ---\n"
               f"Would add: {[spec for base, spec in to_add]}\n"
               f"Would skip: {[f'{spec} ({reason})' for base, spec, reason in skipped]}")
        print(msg)
        _log_action("migrate_modern_requirements_dry_run", "INFO", msg)
        return
    # Actually add dependencies
    for base, spec in to_add:
        try:
            _run_command(["uv", "add", spec, "--python", str(venv_python_executable)], f"uv_add_{base}")
            msg = f"Added dependency '{spec}' to pyproject.toml."
            _log_action("migrate_modern_requirements_add", "SUCCESS", msg, details={"package": spec})
        except Exception:
            msg = f"Failed to add '{spec}' via uv add."
            _log_action("migrate_modern_requirements_add", "ERROR", msg, details={"package": spec})
    if to_add or skipped:
        # Print and log a summary table for transparency
        summary_lines = [
            "\n--- Dependency Migration Summary ---",
            f"Mode: {migration_mode}",
            f"Dry Run: {dry_run}",
            f"Added:   {[spec for base, spec in to_add] if to_add else 'None'}",
            f"Skipped: {[f'{spec} ({reason})' for base, spec, reason in skipped] if skipped else 'None'}",
        ]
        summary_table = "\n".join(summary_lines)
        _log_action("migrate_modern_requirements_summary_table", "INFO", summary_table)

    msg = (f"IMPORTANT: The original '{LEGACY_REQUIREMENTS_TXT}' was not modified. "
           "Consider archiving or regenerating it if needed.")
    _log_action("migrate_modern_requirements_final_advice", "INFO", msg)

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
        "final_summary": None, "errors_encountered_summary": []
    }
    _log_action("script_bootstrap", "INFO", f"Script execution initiated for project at {project_root}.")


def _log_action(action_name: str, status: str, message: str = "", details: dict = None):
    """Logs an action and prints to console."""
    global _log_data_global
    if "actions" not in _log_data_global:
        _log_data_global["actions"] = []
    entry = {"timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "action": action_name, "status": status.upper(),
             "message": message, "details": details or {}}
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
        console_prefix = "INFO"

    details_str = f" | Details: {json.dumps(details)}" if details and details != {} else ""
    # FIXED malformed f-string below
    print(f"{console_prefix}: ({action_name}) {message}{details_str}")


def _get_next_steps_text():
    return (
        "Next Steps:\n"
        "1. If VS Code is open with this project, reload the window (Ctrl+Shift+P > 'Developer: Reload Window').\n"
        f"2. Activate the environment in your terminal:\n    {'./' + VENV_NAME + '/bin/activate' if sys.platform != 'win32' else '.\\\\' + VENV_NAME + '\\\\Scripts\\\\activate'}\n"
        f"3. Review `{PYPROJECT_TOML_NAME}`, `uv.lock`, and '{GITIGNORE_NAME}', then test your project to ensure all dependencies are correctly captured and functional.\n"
        f"4. Commit `{PYPROJECT_TOML_NAME}`, `uv.lock`, `{GITIGNORE_NAME}`, and your source files (including this script if desired) to version control."
    )


def _save_log(log_file_path: Path):
    """Saves the accumulated log data to a JSON file."""
    global _log_data_global
    _log_data_global["end_time_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    current_overall_status = _log_data_global.get("overall_status", "IN_PROGRESS")

    if current_overall_status == "IN_PROGRESS":
        if _log_data_global.get("errors_encountered_summary"):
            _log_data_global["overall_status"] = "COMPLETED_WITH_ERRORS"
            if "final_summary" in _log_data_global:
                _log_data_global["final_summary"] += "Script completed, but some errors/warnings occurred. Check 'errors_encountered_summary' and 'actions' list in this log."
            else:
                _log_data_global["final_summary"] = "Script completed, but some errors/warnings occurred. Check 'errors_encountered_summary' and 'actions' list in this log."
        else:
            _log_data_global["overall_status"] = "SUCCESS"
            if "final_summary" in _log_data_global:
                _log_data_global["final_summary"] += "Script completed successfully."
            else:
                _log_data_global["final_summary"] = "Script completed successfully."
    elif not _log_data_global.get("final_summary"):
        _log_data_global["final_summary"] = f"Script execution concluded. Status: {current_overall_status}"

    if _log_data_global["overall_status"] in ["SUCCESS", "COMPLETED_WITH_ERRORS"]:
        next_steps_text = _get_next_steps_text()
        if _log_data_global.get("final_summary"):
            _log_data_global["final_summary"] += next_steps_text
        else:
            _log_data_global["final_summary"] = f"Script Status: {_log_data_global['overall_status']}.{next_steps_text}"

    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            json.dump(_log_data_global, f, indent=2)
        _log_action("save_log", "SUCCESS", f"Detailed execution log saved to '{log_file_path.name}'")
    except Exception as e:
        _log_action("save_log", "ERROR", f"Failed to save JSON log to '{log_file_path.name}': {e}")

# --- Core Helper Functions ---
def _run_command(command_list, action_log_name: str, work_dir=None, shell=False, capture_output=True, suppress_console_output_on_success=False):
    """
    Runs a shell command and logs its execution. Raises CalledProcessError on failure.
    Returns (stdout_str, stderr_str) if capture_output is True.
    If capture_output is False, stdout/stderr will be empty strings, and output streams to console.
    """
    if work_dir is None:
        work_dir = Path.cwd()
    cmd_str = ' '.join(command_list) if isinstance(command_list, list) else command_list
    print(f"EXEC: \"{cmd_str}\" in \"{work_dir}\" (Logged as action: {action_log_name})")

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
                print(f"  OUT: {stdout}")
            if stderr:
                print(f"  INF_STDERR: {stderr}", file=sys.stdout)
        return stdout, stderr
    except subprocess.CalledProcessError as e:
        log_details.update({"error_type": "CalledProcessError", "return_code": e.returncode,
                            "stdout": e.stdout.strip() if e.stdout and capture_output else ("Output streamed directly to console." if not capture_output else ""),
                            "stderr": e.stderr.strip() if e.stderr and capture_output else ("Output streamed directly to console." if not capture_output else ""),
                            "exception_message": str(e)})
        _log_action(action_log_name, "ERROR", f"Command failed: {cmd_str}", details=log_details)
        print(f"  CMD_ERROR: Command \"{cmd_str}\" failed with exit code {e.returncode}.", file=sys.stderr)
        if capture_output:
            if e.stdout:
                print(f"  FAIL_STDOUT:\n{e.stdout.strip()}", file=sys.stderr)
            if e.stderr:
                print(f"  FAIL_STDERR:\n{e.stderr.strip()}", file=sys.stderr)
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
def _install_uv_macos_brew():
    """Attempts to install `uv` on macOS using Homebrew."""
    action_name = "install_uv_macos_brew"
    _log_action(action_name, "INFO", "Attempting `uv` installation via Homebrew.")
    if not _command_exists("brew"):
        _log_action(action_name, "WARN", "Homebrew (brew) not found.")
        print(f"WARN: Homebrew (brew) not found. Cannot attempt `uv` installation via Homebrew.\n      Please install Homebrew from https://brew.sh/ or allow installation via the official script.", file=sys.stderr)
        return False
    try:
        _run_command(["brew", "install", "uv"], f"{action_name}_exec", suppress_console_output_on_success=False)
        if _command_exists("uv"):
            _log_action(action_name, "SUCCESS", "`uv` installed/updated via Homebrew.")
            return True
        else:
            _log_action(action_name, "ERROR", "`brew install uv` seemed complete, but `uv` command is still not found.")
            print(f"ERROR: `brew install uv` seemed to complete, but `uv` command is still not found.\n       Try running `brew doctor` or check Homebrew's output.\n       Ensure Homebrew's bin directory is in your PATH.", file=sys.stderr)
            return False
    except Exception:
        _log_action(action_name, "ERROR", "`uv` installation via Homebrew failed. See command execution log.")
        print("ERROR: `uv` installation via Homebrew failed. See details above.\n       Try running `brew install uv` manually.", file=sys.stderr)
        return False

def _install_uv_script():
    """Installs `uv` using the official OS-specific scripts (curl or PowerShell)."""
    action_name = "install_uv_official_script"
    _log_action(action_name, "INFO", "Attempting `uv` installation via official script.")
    command_str = ""
    try:
        if sys.platform == "win32":
            command_str = 'powershell -ExecutionPolicy ByPass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"'
            _run_command(command_str, f"{action_name}_exec_ps", shell=True, capture_output=False)
        else:
            if not _command_exists("curl"):
                _log_action(action_name, "ERROR", "`curl` is not installed. Cannot download `uv` installation script.")
                print("ERROR: `curl` is not installed.\n       Please install `curl` (e.g., 'sudo apt install curl') and try again.", file=sys.stderr)
                return False
            command_str = "curl -LsSf https://astral.sh/uv/install.sh | sh"
            _run_command(command_str, f"{action_name}_exec_curl", shell=True, capture_output=False)

        print("INFO: `uv` installation script execution finished. It usually adds `uv` to your PATH.")
        print("INFO: If `uv` is not found immediately, you might need to restart your terminal or source your shell profile.")
        if _command_exists("uv"):
            _log_action(action_name, "SUCCESS", "`uv` now available after script install.")
            return True
        else:
            _log_action(action_name, "WARN", "`uv` command still not found after script install. PATH adjustment or shell restart may be needed.")
            print("WARN: `uv` command still not found after official script execution.\n      `uv` typically installs to $HOME/.local/bin or similar. Ensure this is in your PATH.", file=sys.stderr)
            return False
    except Exception:
        _log_action(action_name, "ERROR", f"Official `uv` installation script execution failed. Command: {command_str}. See command execution log.")
        print(f"ERROR: Official `uv` installation script failed. See details above.\n       Try running manually: {command_str}", file=sys.stderr)
        return False

def _ensure_uv_installed():
    """Ensures `uv` is installed, attempting platform-specific methods if necessary."""
    action_name = "ensure_uv_installed_phase"
    _log_action(action_name, "INFO", "Starting `uv` availability check and installation if needed.")
    try:
        if _command_exists("uv"):
            version_out, _ = _run_command(["uv", "--version"], f"{action_name}_version_check", suppress_console_output_on_success=True)
            _log_action(action_name, "SUCCESS", f"`uv` is already installed. Version: {version_out}")
            print(f"INFO: `uv` is already installed. Version: {version_out}")
            return True
    except Exception as e:
         _log_action(f"{action_name}_version_check", "ERROR", "`uv --version` failed, though `uv` command seems to exist.", details={"exception": str(e)})
         print(f"WARN: `uv` command seems to exist, but 'uv --version' failed: {e}. Will attempt to ensure/reinstall.", file=sys.stderr)

    _log_action(action_name, "INFO", "`uv` not found or version check failed. Attempting installation.")
    print("INFO: `uv` not found in PATH or `uv --version` verification failed. Attempting installation...")

    installed_successfully = False
    install_method_log = "None"
    if sys.platform == "darwin":
        if _command_exists("brew"):
            install_method_log = "Homebrew"
            if _install_uv_macos_brew():
                installed_successfully = True
        if not installed_successfully:
            install_method_log = f"{install_method_log} -> Official Script (macOS)" if install_method_log != "None" else "Official Script (macOS)"
            if _install_uv_script():
                installed_successfully = True
    elif sys.platform.startswith("linux") or sys.platform == "win32":
        install_method_log = "Official Script"
        if _install_uv_script():
            installed_successfully = True
    else:
        _log_action(action_name, "ERROR", f"Unsupported platform for automatic `uv` installation: {sys.platform}")
        print(f"ERROR: Unsupported platform for automatic `uv` installation: {sys.platform}\n       Please install `uv` manually from https://astral.sh/uv", file=sys.stderr)
        return False

    if installed_successfully and _command_exists("uv"):
        try:
            version_out, _ = _run_command(["uv", "--version"], f"{action_name}_post_install_version_check", suppress_console_output_on_success=True)
            _log_action(action_name, "SUCCESS", f"`uv` successfully installed/ensured via {install_method_log}. Version: {version_out}")
            print(f"INFO: `uv` successfully installed/ensured. Version: {version_out}")
            return True
        except Exception as e:
            _log_action(action_name, "ERROR", f"`uv` reported installed via {install_method_log}, but 'uv --version' still fails post-install.", details={"exception": str(e)})
            print(f"ERROR: `uv --version` still fails post-install: {e}\n       This might indicate an issue with the `uv` binary or its PATH setup.", file=sys.stderr)
            return False
    else:
        _log_action(action_name, "ERROR", f"`uv` installation failed using method(s): {install_method_log}, or command still not available.")
        print(f"ERROR: `uv` installation failed or `uv` command is still not available after attempts.\n       Please install `uv` manually from https://astral.sh/uv and ensure it's in your PATH.\n       You may need to restart your terminal or source your shell profile.", file=sys.stderr)
        return False

def _ensure_tool_available(tool_name, package_to_install_via_uv_tool):
    """Ensures a CLI tool is installed via `uv tool install` for use with `uvx`."""
    action_name = f"ensure_tool_{tool_name}"
    _log_action(action_name, "INFO", f"Ensuring CLI tool `{tool_name}` (package: `{package_to_install_via_uv_tool}`) is available for `uvx`.")
    try:
        _run_command(["uv", "tool", "install", package_to_install_via_uv_tool], f"{action_name}_uv_tool_install", suppress_console_output_on_success=True)
        _log_action(action_name, "SUCCESS", f"`{tool_name}` (package '{package_to_install_via_uv_tool}') install/check via `uv tool install` complete.")
        print(f"INFO: `{tool_name}` will be run via `uvx`. For direct terminal use, ensure `uv`'s tool directory is in PATH (try `uv tool update-shell`).")
        return True
    except Exception:
        _log_action(action_name, "ERROR", f"Failed to ensure `{tool_name}` via `uv tool install`. See command execution log.")
        print(f"ERROR: Failed to ensure `{tool_name}` is available. Check details above.\n       If `uv` is working, try manually: `uv tool install {package_to_install_via_uv_tool}`", file=sys.stderr)
        return False

# --- Project and Dependency Handling ---

def _ensure_project_initialized(project_root: Path):
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

    _log_action(action_name, "INFO", f"'{PYPROJECT_TOML_NAME}' not found. Will run `uv init`.")
    print(f"INFO: '{PYPROJECT_TOML_NAME}' not found. Running `uv init`...")

    # Check for existing Python files before running uv init
    existing_py_files = list(project_root.rglob("*.py"))
    # Exclude this script itself if it's in the project root
    # script_path_in_project = project_root / Path(__file__).name
    # if script_path_in_project in existing_py_files:
    #     existing_py_files.remove(script_path_in_project)

    project_had_py_files_before_init = bool(existing_py_files)
    main_py_existed_before_init = main_py_path.exists()

    try:
        _run_command(["uv", "init"], f"{action_name}_uv_init_exec")
        if not pyproject_path.exists():
            _log_action(action_name, "ERROR", f"`uv init` ran but '{PYPROJECT_TOML_NAME}' was not created. This is unexpected.")
            print(f"ERROR: `uv init` ran but '{PYPROJECT_TOML_NAME}' was not created.\n       Check `uv init` output. Manual creation of `pyproject.toml` might be needed.", file=sys.stderr)
            return False

        _log_action(action_name, "SUCCESS", f"`uv init` completed. '{PYPROJECT_TOML_NAME}' created/updated.")
        print(f"INFO: `uv init` completed. '{PYPROJECT_TOML_NAME}' is present.")

        # Conditional removal of main.py created by `uv init`
        main_py_exists_after_init = main_py_path.exists()
        if main_py_exists_after_init and not main_py_existed_before_init: # `uv init` created main.py
            if project_had_py_files_before_init: # And there were other .py files
                _log_action(f"{action_name}_remove_main_py", "INFO", f"`uv init` created '{main_py_path.name}', but other .py files existed. Removing '{main_py_path.name}'.")
                print(f"INFO: `uv init` created '{main_py_path.name}'. Removing it as other Python files already exist in the project.")
                try:
                    main_py_path.unlink()
                    _log_action(f"{action_name}_remove_main_py", "SUCCESS", f"Successfully removed '{main_py_path.name}' created by `uv init`.")
                except OSError as e:
                    _log_action(f"{action_name}_remove_main_py", "ERROR", f"Failed to remove '{main_py_path.name}': {e}")
                    print(f"ERROR: Failed to remove '{main_py_path.name}': {e}", file=sys.stderr)
            else: # Project was empty of .py files, so main.py from uv init is fine
                _log_action(f"{action_name}_keep_main_py", "INFO", f"`uv init` created '{main_py_path.name}' in an otherwise empty Python project. It will be kept.")
                print(f"INFO: `uv init` created '{main_py_path.name}'. Keeping it as standard for a new project.")
        return True

    except Exception: # Error logged by _run_command
        _log_action(action_name, "ERROR", "Failed to initialize project with `uv init`. See command execution log.")
        print("ERROR: Failed to initialize project with `uv init`. See details above.\n       Manual `pyproject.toml` creation or `uv init` troubleshooting needed.", file=sys.stderr)
        return False


def _ensure_gitignore_exists(project_root: Path, venv_name: str):
    """Ensures a .gitignore file exists and contains essential Python/venv ignores."""
    action_name = "ensure_gitignore"
    gitignore_path = project_root / GITIGNORE_NAME
    _log_action(action_name, "INFO", f"Checking for '{GITIGNORE_NAME}' file.")

    essential_ignore_map = {
        "Python Virtual Environments": [f"{venv_name}/", "venv/", "ENV/", "env/", "*/.venv/", "*/venv/"],
        "Python Cache & Compiled Files": ["__pycache__/", "*.py[cod]", "*$py.class"],
        "Log file from this script": [JSON_LOG_FILE_NAME],
        "OS-specific": [".DS_Store", "Thumbs.db"]
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
                    print(f"INFO: Appended essential entries to '{GITIGNORE_NAME}'.")
                else:
                    _log_action(action_name, "INFO", f"Existing '{GITIGNORE_NAME}' seems to cover essential exclusions for venv and log file.")
        except Exception as e:
            _log_action(action_name, "WARN", f"Could not read/update existing '{GITIGNORE_NAME}'. Manual check advised.", details={"exception": str(e)})
            print(f"WARN: Could not check/update existing '{GITIGNORE_NAME}': {e}. Please verify it manually includes at least '{VENV_NAME}/' and '{JSON_LOG_FILE_NAME}'.", file=sys.stderr)
    else:
        _log_action(action_name, "INFO", f"'{GITIGNORE_NAME}' not found. Creating a default one.")
        print(f"INFO: '{GITIGNORE_NAME}' not found. Creating a default one.")
        try:
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write("# Auto-generated by pyuvstarter.py\n")
                f.write("\n".join(comprehensive_ignores))
                f.write("\n")
            _log_action(action_name, "SUCCESS", f"Default '{GITIGNORE_NAME}' created.")
            print(f"INFO: Default '{GITIGNORE_NAME}' created.")
        except Exception as e:
            _log_action(action_name, "ERROR", f"Failed to create '{GITIGNORE_NAME}'.", details={"exception": str(e)})
            print(f"ERROR: Failed to create '{GITIGNORE_NAME}': {e}. Please create it manually with standard Python ignores.", file=sys.stderr)


def _get_declared_dependencies(pyproject_path: Path) -> set[str]:
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
            msg = "Cannot parse `pyproject.toml` to read existing dependencies: `tomllib` (Python 3.11+) or `toml` package not available in the environment running this script."
            _log_action(action_name, "WARN", msg + " Dependency checking against `pyproject.toml` will be skipped before `uv add` (this is okay as `uv add` is idempotent).")
            print(f"WARN: {msg} Script best run with Python 3.11+ or with 'toml' installed in its execution environment.", file=sys.stderr)
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
        msg = f"Failed to parse '{pyproject_path.name}' using {tomllib_source} to get dependency list."
        _log_action(action_name, "ERROR", msg, details={"exception": str(e)})
        print(f"ERROR: {msg} Exception: {e}. Check its TOML syntax. Dependency list might be incomplete for subsequent checks.", file=sys.stderr)
        return dependencies

def _get_packages_from_legacy_req_txt(requirements_path: Path) -> set[str]:
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
                if not line or line.startswith("#") or line.startswith("-e"):
                    continue
                if line:
                    packages_specs.add(line)
        _log_action(action_name, "SUCCESS", f"Read {len(packages_specs)} package specifiers from '{requirements_path.name}'.")
    except Exception as e:
        _log_action(action_name, "ERROR", f"Could not read '{requirements_path.name}' for migration.", details={"exception": str(e)})
        print(f"ERROR: Could not read '{requirements_path.name}': {e}. Skipping migration.", file=sys.stderr)
    return packages_specs

def _migrate_req_txt_to_pyproject(requirements_path: Path, venv_python_executable: Path, declared_deps_before_migration: set):
    action_name = "migrate_legacy_requirements_txt_to_pyproject"
    packages_from_req_txt_specs = _get_packages_from_legacy_req_txt(requirements_path)
    if not packages_from_req_txt_specs:
        _log_action(action_name, "INFO", "No packages from legacy requirements.txt to migrate.")
        return

    _log_action(action_name, "INFO", f"Attempting to migrate {len(packages_from_req_txt_specs)} specifier(s) from '{requirements_path.name}' to `pyproject.toml` if not already declared.")
    print(f"INFO: Migrating packages from '{requirements_path.name}' to `pyproject.toml` (if new)...")

    migrated_count = 0
    failed_migrations = []
    packages_actually_added_log = []
    for pkg_specifier in sorted(list(packages_from_req_txt_specs)):
        base_pkg_name = pkg_specifier.split("[")[0].split("=")[0].split(">")[0].split("<")[0].split("!")[0].split("~")[0].strip().lower()
        if base_pkg_name in declared_deps_before_migration:
            _log_action(f"{action_name}_skip_add", "INFO", f"Package '{base_pkg_name}' (from specifier '{pkg_specifier}') appears already declared. Skipping redundant `uv add` during migration.")
            continue
        try:
            _run_command(["uv", "add", pkg_specifier, "--python", str(venv_python_executable)], f"{action_name}_uv_add_'{base_pkg_name.replace('.', '_')}'")
            migrated_count += 1
            packages_actually_added_log.append(pkg_specifier)
        except Exception:
            print(f"ERROR: Failed to `uv add \"{pkg_specifier}\"` from '{requirements_path.name}'. Check `uv add` output above.", file=sys.stderr)
            failed_migrations.append(pkg_specifier)

    summary_msg = f"Migration from '{requirements_path.name}': {migrated_count} package specifier(s) processed for addition to `pyproject.toml`."
    summary_details = {"total_from_req_txt": len(packages_from_req_txt_specs), "attempted_uv_add_count": migrated_count, "added_specifiers": packages_actually_added_log}
    if failed_migrations:
        summary_msg += f" {len(failed_migrations)} package specifier(s) failed to be added via `uv add`."
        summary_details["failed_migrations"] = failed_migrations
        _log_action(action_name, "WARN", summary_msg, details=summary_details)
        print(f"WARN: {summary_msg}", file=sys.stderr)
    else:
        status = "SUCCESS" if migrated_count > 0 or not packages_from_req_txt_specs else "INFO"
        _log_action(action_name, status, summary_msg, details=summary_details)
        print(f"INFO: {summary_msg}")

    if packages_from_req_txt_specs:
        advise_msg = (f"Dependencies from '{requirements_path.name}' have been processed. "
                      f"The original '{requirements_path.name}' HAS NOT been modified by this script. "
                      f"It's recommended to use `{PYPROJECT_TOML_NAME}` as the primary source of dependencies. "
                      f"You may want to manually archive or delete '{requirements_path.name}', or replace it "
                      f"with one generated from `pyproject.toml` (e.g., using `uv pip compile {PYPROJECT_TOML_NAME} -o {LEGACY_REQUIREMENTS_TXT}`) "
                      f"if it's still needed for other tools or workflows.")
        _log_action(f"{action_name}_advise_user_req_txt", "INFO", advise_msg)
        print(f"IMPORTANT_ADVICE: {advise_msg}")


def _get_packages_from_pipreqs(project_root: Path, venv_name_to_ignore: str) -> set[str]:
    action_name = "pipreqs_discover_imports"
    _log_action(action_name, "INFO", f"Scanning project imports with `pipreqs` (via `uvx`), ignoring '{venv_name_to_ignore}'.")
    packages = set()
    pipreqs_args = ["uvx", "pipreqs", "--print", "--ignore", venv_name_to_ignore, str(project_root)]
    try:
        stdout, _ = _run_command(pipreqs_args, f"{action_name}_exec", suppress_console_output_on_success=True)
        parsed_count = 0
        if stdout:
            for line in stdout.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                package_name = line.split("==")[0].split(">=")[0].split("<=")[0].split("!=")[0].split("~=")[0].strip()
                if package_name:
                    packages.add(package_name.lower())
                    parsed_count += 1

        if parsed_count > 0:
            _log_action(action_name, "SUCCESS", f"Discovered {len(packages)} unique potential package name(s) via `pipreqs`: {', '.join(sorted(list(packages)))}.")
        elif not stdout.strip():
             _log_action(action_name, "INFO", "`pipreqs` (via `uvx`) produced no output. No import-based dependencies found or an issue running it (check command log).")
        else:
             _log_action(action_name, "INFO", "`pipreqs` (via `uvx`) ran but no parseable package names were found in its output.")
        return packages
    except subprocess.CalledProcessError:
        _log_action(action_name, "ERROR", "`uvx pipreqs` command failed. Cannot automatically discover dependencies. See command execution log for details.")
        print("ERROR: `uvx pipreqs` command failed. See details above.", file=sys.stderr)
        print(f"       Hints: This might be due to syntax errors in your Python files that `pipreqs` cannot parse, or `uvx` failing to run `pipreqs`.\n       Consider running manually for debug: {' '.join(pipreqs_args)} --debug", file=sys.stderr)
    except Exception as e:
        _log_action(action_name, "ERROR", "An unexpected error occurred while running/processing `pipreqs`.", details={"exception": str(e)})
        print(f"ERROR: An unexpected error occurred while running/processing `pipreqs`: {e}", file=sys.stderr)
    return packages

def _configure_vscode_settings(project_root: Path, venv_python_executable: Path):
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
    if settings_file_path.exists():
        try:
            with open(settings_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    settings_data = json.loads(content)
        except json.JSONDecodeError:
            # Backup invalid JSON before overwriting
            backup_path = settings_file_path.with_suffix(f".bak_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
            shutil.copy2(settings_file_path, backup_path)
            backup_made = True
            _log_action(action_name, "WARN", f"Existing '{settings_file_path.name}' is not valid JSON. Backed up before overwrite.", details={"backup": str(backup_path)})
            settings_data = {}
        except Exception as e:
            _log_action(action_name, "WARN", f"Could not read existing '{settings_file_path.name}': {e}. It may be overwritten.", details={"exception": str(e)})
            settings_data = {}
    interpreter_path = str(venv_python_executable)
    settings_data["python.defaultInterpreterPath"] = interpreter_path
    # Add a comment for uv integration (not valid JSON, but VS Code ignores comments in settings.json)
    # So we prepend a comment line if not present
    comment_line = "// This interpreter path is managed by pyuvstarter and uv (https://astral.sh/uv)"
    try:
        with open(settings_file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
    except Exception:
        first_line = ""
    with open(settings_file_path, 'w', encoding='utf-8') as f:
        if not first_line.strip().startswith("// This interpreter path is managed by pyuvstarter"):
            f.write(comment_line + "\n")
        json.dump(settings_data, f, indent=4)
    msg = f"VS Code 'python.defaultInterpreterPath' set.{' (Backed up old file)' if backup_made else ''}"
    _log_action(action_name, "SUCCESS", msg, details={"interpreter_path": interpreter_path})
    print(f"INFO: VS Code 'python.defaultInterpreterPath' set in '{settings_file_path.name}'\n      Path: {interpreter_path}\n      (Managed by pyuvstarter and uv)")

def _ensure_vscode_launch_json(project_root: Path, venv_python_executable: Path):
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
    default_config = {
        "version": "0.2.0",
        "configurations": [
            {
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
        ]
    }
    try:
        if launch_path.exists():
            try:
                with open(launch_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                configs = data.get("configurations", [])
                # Check if a config for ${file} and the venv python already exists
                already_present = any(
                    c.get("type") == "python" and c.get("program") == "${file}" and c.get("python") == str(venv_python_executable.resolve())
                    for c in configs
                )
                if not already_present:
                    configs.append(default_config["configurations"][0])
                    data["configurations"] = configs
                    with open(launch_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                    _log_action(action_name, "SUCCESS", "Added launch config for current file to existing launch.json.")
                else:
                    _log_action(action_name, "INFO", "Launch config for current file and venv python already present in launch.json.")
            except json.JSONDecodeError:
                backup_path = launch_path.with_suffix(f".bak_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
                shutil.copy2(launch_path, backup_path)
                _log_action(action_name, "WARN", f"Existing '{launch_path.name}' is not valid JSON. Backed up before overwrite.", details={"backup": str(backup_path)})
                with open(launch_path, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=4)
                _log_action(action_name, "SUCCESS", "Created new launch.json for current file. (Backed up old file)")
            except Exception as e:
                _log_action(action_name, "ERROR", f"Could not update existing launch.json: {e}")
        else:
            with open(launch_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
            _log_action(action_name, "SUCCESS", "Created new launch.json for current file.")
    except Exception as e:
        _log_action(action_name, "ERROR", f"Failed to create or update launch.json: {e}")

def detect_unused_imports(project_root: Path):
    """
    Runs ruff to detect unused imports (F401) in the project.
    Returns a list of (file, lineno, description) for each unused import, or None if ruff is not available.
    """
    action_name = "detect_unused_imports_ruff"
    if not _command_exists("ruff"):
        _log_action(action_name, "WARN", "ruff is not installed. Skipping unused import detection.")
        return None
    try:
        result = subprocess.run([
            "ruff", str(project_root), "--select", "F401", "--format", "json"
        ], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        unused = []
        if output:
            try:
                issues = json.loads(output)
                for issue in issues:
                    if issue.get("code") == "F401":
                        unused.append((issue.get("filename"), issue.get("location", {}).get("row"), issue.get("message")))
            except Exception as e:
                _log_action(action_name, "ERROR", "Failed to parse ruff output.", details={"exception": str(e)})
                print("ERROR: Failed to parse ruff output for unused imports.")
                return None
        _log_action(action_name, "SUCCESS", f"Ruff unused import detection complete. Found {len(unused)} unused imports.")
        return unused
    except subprocess.CalledProcessError as e:
        _log_action(action_name, "ERROR", "ruff command failed.", details={"exception": str(e)})
        print("ERROR: ruff command failed. See details above.")
        return None
    except Exception as e:
        _log_action(action_name, "ERROR", "Unexpected error running ruff.", details={"exception": str(e)})
        print("ERROR: Unexpected error running ruff.")
        return None

# --- Main Orchestration Function ---
def main():
    args = parse_args()
    if getattr(args, "version", False):
        version = _get_project_version(Path(__file__).parent / "pyproject.toml", "pyuvstarter")
        _log_action("show_version", "INFO", f"pyuvstarter version: {version}")
        sys.exit(0)
    project_root = Path(args.project_dir).expanduser().resolve()
    log_file_path = project_root / JSON_LOG_FILE_NAME
    _init_log(project_root)

    pyproject_file_path = project_root / PYPROJECT_TOML_NAME
    legacy_req_path = project_root / LEGACY_REQUIREMENTS_TXT

    _log_action("script_start", "INFO", f"--- Starting Automated Python Project Setup ({_log_data_global['script_name']}) in: {project_root} ---\n--- Using Virtual Environment Name: '{VENV_NAME}' ---\n--- Primary Dependency File: '{PYPROJECT_TOML_NAME}' ---\n--- JSON Log will be saved to: '{log_file_path.name}' ---")

    venv_python_executable = None
    settings_json_status = "NOT_ATTEMPTED"
    launch_json_status = "NOT_ATTEMPTED"
    major_action_results = []

    try:
        if not _ensure_uv_installed():
            _log_action("ensure_uv_installed", "ERROR", "Halting: `uv` could not be installed or verified. Check log and console output for details.")
            raise SystemExit("Halting: `uv` could not be installed or verified. Check log and console output for details.")
        major_action_results.append(("uv_installed", "SUCCESS"))

        if not _ensure_project_initialized(project_root):
            _log_action("ensure_project_initialized", "ERROR", f"Halting: Project could not be initialized with '{PYPROJECT_TOML_NAME}'. Check log and console output.")
            raise SystemExit(f"Halting: Project could not be initialized with '{PYPROJECT_TOML_NAME}'. Check log and console output.")
        major_action_results.append(("project_initialized", "SUCCESS"))

        _ensure_gitignore_exists(project_root, VENV_NAME)
        major_action_results.append(("gitignore", "SUCCESS"))

        action_venv = "create_or_verify_venv"
        _log_action(action_venv, "INFO", f"Creating/ensuring virtual environment '{VENV_NAME}'.")
        _run_command(["uv", "venv", VENV_NAME], f"{action_venv}_uv_venv")
        venv_path = project_root / VENV_NAME
        venv_python_executable = venv_path / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")
        _log_action(action_venv, "INFO", f"Virtual environment '{VENV_NAME}' created/verified. venv_path:'{venv_path}' Python executable: '{venv_python_executable}'. Project venv Python resolved to absolute path: '{venv_python_executable.resolve()}' venv path: '{venv_path}'.")

        if not venv_python_executable.exists():
            msg = f"Virtual environment Python executable not found at '{venv_python_executable}' after `uv venv` command."
            _log_action(action_venv, "ERROR", msg)
            raise SystemExit(f"CRITICAL ERROR: {msg}\n       This indicates a problem with `uv venv` or an unexpected environment structure.")
        _log_action(action_venv, "SUCCESS", f"Virtual environment '{VENV_NAME}' ready. Interpreter: '{venv_python_executable}'.")
        major_action_results.append(("venv_ready", "SUCCESS"))

        declared_deps_before_migration = _get_declared_dependencies(pyproject_file_path)
        # --- New: Modular requirements.txt migration with CLI modes/dry-run ---
        if legacy_req_path.exists():
            migrate_requirements_modular(
                project_root=project_root,
                venv_python_executable=venv_python_executable,
                pyproject_file_path=pyproject_file_path,
                migration_mode=args.dependency_migration,
                dry_run=args.dry_run,
                declared_deps_before_migration=declared_deps_before_migration
            )
            major_action_results.append(("requirements_migration", "SUCCESS"))
        else:
            _log_action("migrate_legacy_requirements_txt_to_pyproject", "INFO", f"No '{LEGACY_REQUIREMENTS_TXT}' found, skipping migration step.")
            major_action_results.append(("requirements_migration", "SKIPPED"))

        # --- Legacy: Sync environment ---
        action_sync = "uv_sync_dependencies"
        _log_action(action_sync, "INFO", "Syncing environment with `pyproject.toml` and `uv.lock` using `uv sync`.")
        _run_command(["uv", "sync", "--python", str(venv_python_executable)], f"{action_sync}_exec")
        _log_action(action_sync, "SUCCESS", "Environment synced with `pyproject.toml` and `uv.lock`.")
        major_action_results.append(("uv_sync", "SUCCESS"))

        # --- Legacy: pipreqs discovery and add ---
        action_pipreqs_phase = "pipreqs_discovery_and_add_phase"
        _log_action(action_pipreqs_phase, "INFO", "Starting dependency discovery with `pipreqs` to add to `pyproject.toml`.")

        if _ensure_tool_available("pipreqs", "pipreqs"):
            discovered_by_pipreqs = _get_packages_from_pipreqs(project_root, VENV_NAME)
            if discovered_by_pipreqs:
                current_declared_deps = _get_declared_dependencies(pyproject_file_path)
                genuinely_new_packages_to_add = discovered_by_pipreqs - current_declared_deps
                if genuinely_new_packages_to_add:
                    pkgs_added_count = 0
                    _log_action(action_pipreqs_phase, "INFO", f"`pipreqs` discovered {len(genuinely_new_packages_to_add)} potential new package(s) not yet in `pyproject.toml` dependencies: {[pkg for pkg in sorted(list(genuinely_new_packages_to_add))]}")
                    _log_action(action_pipreqs_phase, "INFO", f"Automatically adding these {len(genuinely_new_packages_to_add)} package(s) to `pyproject.toml` using `uv add`...")
                    for pkg_to_add in sorted(list(genuinely_new_packages_to_add)):
                        try:
                            _run_command(["uv", "add", pkg_to_add, "--python", str(venv_python_executable)], f"uv_add_{pkg_to_add.replace('-', '_').replace('.', '_')}")
                            pkgs_added_count +=1
                        except Exception:
                            _log_action(action_pipreqs_phase, "ERROR", f"Failed to `uv add {pkg_to_add}`. Check log and `uv add` output above.")
                    msg = f"Attempted to `uv add` {pkgs_added_count}/{len(genuinely_new_packages_to_add)} newly discovered packages to `pyproject.toml`."
                    status = "SUCCESS" if pkgs_added_count == len(genuinely_new_packages_to_add) else "WARN"
                    _log_action(action_pipreqs_phase, status, msg, details={"total_discovered_new": len(genuinely_new_packages_to_add), "successfully_added_count": pkgs_added_count})
                    if status == "WARN":
                        _log_action(action_pipreqs_phase, "WARN", "Some newly discovered packages could not be added via `uv add`. Review logs and `uv` output.")
                elif discovered_by_pipreqs:
                    _log_action(action_pipreqs_phase, "INFO", "All `pipreqs` discovered dependencies seem already declared in `pyproject.toml`.")
        else:
            _log_action(action_pipreqs_phase, "ERROR", "`pipreqs` tool setup failed. Skipping automatic import discovery.")
        major_action_results.append(("pipreqs_discovery", "SUCCESS"))

        # --- New: Ruff unused import detection ---
        unused_imports = detect_unused_imports(project_root)
        if unused_imports is not None:
            if unused_imports:
                msg = ("Ruff detected unused imports (F401):\n" +
                       "\n".join([f"  {file}:{lineno} {desc}" for file, lineno, desc in unused_imports]) +
                       "\nConsider removing these unused imports for a cleaner project.")
                _log_action("ruff_unused_imports", "WARN", msg, details={"unused_imports": unused_imports})
            else:
                msg = "No unused imports detected by ruff (F401)."
                _log_action("ruff_unused_imports", "INFO", msg)
        else:
            msg = "Ruff could not be run for unused import detection."
            _log_action("ruff_unused_imports", "WARN", msg)
        major_action_results.append(("ruff_unused_imports", "SUCCESS"))

        # --- VS Code config ---
        _configure_vscode_settings(project_root, venv_python_executable)
        settings_json_status = "SUCCESS"
        _ensure_vscode_launch_json(project_root, venv_python_executable)
        launch_json_status = "SUCCESS"
        major_action_results.append(("vscode_config", "SUCCESS"))

        _log_action("script_end", "SUCCESS", "Automated project setup script completed successfully.")

        # --- Final summary table ---
        summary_lines = [
            "\n--- Final Setup Summary ---",
            "Step                        | Status",
            "-----------------------------|--------",
        ]
        for step, status in major_action_results:
            summary_lines.append(f"{step.ljust(28)}| {status}")
        summary_lines.append(f"\nSee '{JSON_LOG_FILE_NAME}' for full details.")
        summary_table = "\n".join(summary_lines)
        _log_action("final_summary_table", "INFO", summary_table)

        # --- Next steps ---
        next_steps = _get_next_steps_text()
        _log_action("explicit_next_steps", "INFO", next_steps)
        print("\n" + next_steps)

        # If any errors or warnings, print/log a final warning
        errors_or_warnings = any(
            a.get("status", "").upper() in ("ERROR", "WARN")
            for a in _log_data_global.get("actions", [])
        )
        if errors_or_warnings:
            warn_msg = f"\n⚠️  Some warnings/errors occurred. See '{log_file_path.name}' for details."
            _log_action("final_warning", "WARN", warn_msg)
            print(warn_msg)

        # Print and log explicit summary and next steps
        explicit_summary = _get_explicit_summary_text(project_root, VENV_NAME, pyproject_file_path, log_file_path)
        _log_action("explicit_summary", "INFO", explicit_summary)
        print(explicit_summary)

    except SystemExit as e:
        msg = f"Script halted by explicit exit: {e}"
        settings_json_status = "FAILED"
        launch_json_status = "FAILED"
        if _log_data_global.get("overall_status") == "IN_PROGRESS":
            _log_data_global["overall_status"] = "HALTED_BY_SCRIPT_LOGIC"
        _log_data_global["final_summary"] = _log_data_global.get("final_summary", msg)
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
            _log_action("install_sync_hint", "WARN", "INSTALLATION/SYNC HINT: A package operation with `uv` failed.\n  - Review `uv`'s error output (logged as FAIL_STDERR/FAIL_STDOUT for the command) for specific package names or reasons.\n  - Ensure the package name is correct and exists on PyPI (https://pypi.org) or your configured index.\n  - Some packages require system-level (non-Python) libraries to be installed first. Check the package's documentation.\n  - You might need to manually edit '{PYPROJECT_TOML_NAME}' and then run `uv sync --python {venv_python_executable}`.")
        elif "pipreqs" in cmd_str_lower:
            _log_action("pipreqs_hint", "WARN", "PIPReQS HINT: The 'pipreqs' command (run via 'uvx') failed.\n  - This could be due to syntax errors in your Python files that `pipreqs` cannot parse, an internal `pipreqs` issue, or `uvx` failing to execute `pipreqs`.\n  - Try running manually for debug: uvx pipreqs \"{project_root}\" --ignore \"{VENV_NAME}\" --debug")
        elif "uv venv" in cmd_str_lower:
            _log_action("uv_venv_hint", "WARN", "VIRTUAL ENV HINT: `uv venv` command failed.\n  - Ensure `uv` is correctly installed and functional. Check `uv --version`.\n  - Check for issues like insufficient disk space or permissions in the project directory '{project_root}'.")
        elif "uv tool install" in cmd_str_lower:
            _log_action("uv_tool_install_hint", "WARN", "UV TOOL INSTALL HINT: `uv tool install` (likely for pipreqs) failed.\n  - This could be due to network issues, `uv` problems, or the tool package ('pipreqs') not being found by `uv`.\n  - Try running `uv tool install pipreqs` manually in your terminal.")
        elif "uv init" in cmd_str_lower:
            _log_action("uv_init_hint", "WARN", "UV INIT HINT: `uv init` command failed.\n  - Ensure `uv` is correctly installed. Try running `uv init` manually in an empty directory to test.\n  - Check for permissions issues in the project directory '{project_root}'.")
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
        if "start_time_utc" in _log_data_global:
            _log_data_global["vscode_settings_json_status"] = settings_json_status
            _log_data_global["vscode_launch_json_status"] = launch_json_status
            _save_log(log_file_path)

def _get_explicit_summary_text(project_root: Path, venv_name: str, pyproject_file_path: Path, log_file_path: Path):
    """
    Returns a legacy-style explicit summary of all key files and paths for user clarity.
    """
    vscode_settings = project_root / VSCODE_DIR_NAME / SETTINGS_FILE_NAME
    vscode_launch = project_root / VSCODE_DIR_NAME / LAUNCH_FILE_NAME
    summary_lines = [
        "\n--- Project Setup Summary ---",
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
