#!/usr/bin/env python3
"""
Automated Python Project Setup Script (v6.3 - Safer requirements.txt Handling)

Purpose:
This script automates the setup of a Python project environment using `uv`,
focusing on `pyproject.toml` for dependency management, and configures Visual
Studio Code. It operates without user prompts for a standard setup and creates
a detailed JSON log file of its actions, including recommended next steps.
It handles existing `requirements.txt` by migrating its dependencies to
`pyproject.toml` without automatically renaming/deleting the original file,
instead providing guidance to the user.

Key Actions:
1. Ensures `uv` is installed (platform-aware installation if missing).
2. Initializes a `uv` project (creates `pyproject.toml` if none exists) using `uv init`.
3. Creates a virtual environment (default: '.venv') using `uv venv`.
4. If 'requirements.txt' exists, its dependencies are added to `pyproject.toml`
   using `uv add` (if not already declared). The original 'requirements.txt' is NOT modified.
5. Installs all declared dependencies from `pyproject.toml` and `uv.lock` using `uv sync`.
6. Ensures `pipreqs` is available (installs via `uv tool install` if missing).
7. Scans project Python files using `pipreqs` (via `uvx`) to discover imported packages.
8. For newly discovered packages not already in `pyproject.toml`, automatically adds
   them using `uv add <package>`. This updates `pyproject.toml` and `uv.lock`.
9. Configures VS Code's 'python.defaultInterpreterPath' in '.vscode/settings.json'.
10. Logs all major actions, command executions, statuses, and errors to a
    'project_setup_log.json' file.

How to Use:
1. Prerequisites:
   - Python 3 (Python 3.11+ recommended for full `pyproject.toml` parsing via `tomllib`).
   - System tools for `uv` installation if `uv` is not yet installed:
     - macOS: Homebrew (https://brew.sh/) preferred, or `curl`.
     - Linux: `curl`.
     - Windows: PowerShell.
   - (Optional) An existing 'requirements.txt' file if migrating an old project.

2. Placement:
   - Save this script (e.g., 'bootstrap_project.py') in the root of your project.

3. Execution:
   - Open your terminal/command prompt.
   - Navigate to the project root.
   - Make executable (Linux/macOS): `chmod +x bootstrap_project.py`
   - Run: `./bootstrap_project.py` (or `python bootstrap_project.py`)

Outcome:
- A `pyproject.toml` will define project dependencies.
- A '.venv' directory will contain the Python virtual environment.
- A `uv.lock` file will ensure reproducible dependency resolution.
- Dependencies (migrated, declared, and discovered) will be installed.
- '.vscode/settings.json' will be configured.
- A 'project_setup_log.json' file will detail the script's execution.
- The script will print recommended next steps to the console, and these will
  also be included in the JSON log if the script completes without critical failure.
- An existing 'requirements.txt' will be left untouched, but its contents will be
  reflected in `pyproject.toml`. The user will be advised on managing it.

Notes:
- This script WILL automatically modify/create `pyproject.toml`, `uv.lock`, and
  install packages. Review the JSON log and project files after execution.
- `pipreqs` guesses dependencies from imports. While good, it's not infallible.
  Manually review `pyproject.toml` for correctness.
- If issues arise, check the script's terminal output and the detailed
  'project_setup_log.json' for error messages and hints.
"""

import os
import json
import subprocess
import sys
import shutil
from pathlib import Path
import datetime
import platform
import importlib.util # For tomllib check

# --- Configuration Constants ---
VENV_NAME = ".venv"
PYPROJECT_TOML_NAME = "pyproject.toml"
LEGACY_REQUIREMENTS_TXT = "requirements.txt" # For migration
VSCODE_DIR_NAME = ".vscode"
SETTINGS_FILE_NAME = "settings.json"
JSON_LOG_FILE_NAME = "project_setup_log.json"

# --- JSON Logging Utilities ---
_log_data_global = {} # Global dictionary to hold all log data

def _init_log():
    """Initializes the global log data structure."""
    global _log_data_global
    _log_data_global = {
        "script_name": Path(__file__).name,
        "start_time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "end_time_utc": None,
        "overall_status": "IN_PROGRESS",
        "platform_info": {
            "system": platform.system(), "release": platform.release(),
            "version": platform.version(), "machine": platform.machine(),
            "python_version_script_host": sys.version
        },
        "project_root": str(Path.cwd()),
        "actions": [],
        "final_summary": None,
        "errors_encountered_summary": []
    }
    _log_action("script_bootstrap", "INFO", f"Script execution initiated for project at {Path.cwd()}.")

def _log_action(action_name: str, status: str, message: str = "", details: dict = None):
    """Logs an action and prints to console."""
    global _log_data_global
    if "actions" not in _log_data_global: _log_data_global["actions"] = []

    entry = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": action_name, "status": status.upper(),
        "message": message, "details": details or {}
    }
    _log_data_global["actions"].append(entry)

    if status.upper() == "ERROR":
        if "errors_encountered_summary" not in _log_data_global: _log_data_global["errors_encountered_summary"] = []
        error_summary = f"Action: {action_name}, Message: {message}"
        if details and "exception" in details: error_summary += f", Exception: {details['exception']}"
        if details and "command" in details: error_summary += f", Command: {details['command']}"
        _log_data_global["errors_encountered_summary"].append(error_summary)

    console_prefix = status.upper()
    if console_prefix == "SUCCESS": console_prefix = "INFO"

    details_str = f" | Details: {json.dumps(details)}" if details and details != {} else ""
    print(f"{console_prefix}: ({action_name}) {message}{details_str}")

def _save_log(log_file_path: Path):
    """Saves the accumulated log data to a JSON file."""
    global _log_data_global
    _log_data_global["end_time_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    current_overall_status = _log_data_global.get("overall_status", "IN_PROGRESS")

    if current_overall_status == "IN_PROGRESS":
        if _log_data_global.get("errors_encountered_summary"):
            _log_data_global["overall_status"] = "COMPLETED_WITH_ERRORS"
            _log_data_global["final_summary"] = _log_data_global.get("final_summary", "Script completed, but some errors/warnings occurred. Check 'errors_encountered_summary' and 'actions' list in this log.")
        else:
            _log_data_global["overall_status"] = "SUCCESS"
            _log_data_global["final_summary"] = _log_data_global.get("final_summary", "Script completed successfully.")
    elif not _log_data_global.get("final_summary"):
         _log_data_global["final_summary"] = f"Script execution concluded. Status: {current_overall_status}"

    if _log_data_global["overall_status"] in ["SUCCESS", "COMPLETED_WITH_ERRORS"]:
        next_steps_text = (
            f"\n\nRecommended Next Steps (also printed to console):\n"
            f"1. If VS Code is open with this project, reload the window (Ctrl+Shift+P > 'Developer: Reload Window').\n"
            f"2. Activate the virtual environment in your terminal: source {VENV_NAME}/bin/activate (Linux/macOS) or .\\{VENV_NAME}\\Scripts\\activate (Windows PowerShell).\n"
            f"3. Review `{PYPROJECT_TOML_NAME}` and `uv.lock`, then test your project to ensure all dependencies are correctly captured and functional."
        )
        if _log_data_global.get("final_summary"):
            _log_data_global["final_summary"] += next_steps_text
        else:
            _log_data_global["final_summary"] = f"Script Status: {_log_data_global['overall_status']}.{next_steps_text}"

    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            json.dump(_log_data_global, f, indent=4)
        print(f"INFO: Detailed execution log saved to '{log_file_path.name}'")
    except Exception as e:
        print(f"CRITICAL_ERROR: Failed to save JSON log to '{log_file_path.name}': {e}", file=sys.stderr)

# --- Core Helper Functions ---

def _run_command(command_list, action_log_name: str, work_dir=None, shell=False, capture_output=True, suppress_console_output_on_success=False):
    if work_dir is None: work_dir = Path.cwd()
    cmd_str = ' '.join(command_list) if isinstance(command_list, list) else command_list
    print(f"EXEC: \"{cmd_str}\" in \"{work_dir}\" (Logged as action: {action_log_name})")

    log_details = {"command": cmd_str, "working_directory": str(work_dir), "shell_used": shell, "capture_output_setting": capture_output}

    try:
        process = subprocess.run(
            command_list, cwd=work_dir, capture_output=capture_output, text=True, shell=shell, check=True
        )
        stdout = process.stdout.strip() if process.stdout and capture_output else ""
        stderr = process.stderr.strip() if process.stderr and capture_output else ""

        log_details.update({"return_code": process.returncode,
                            "stdout": stdout if capture_output else "Output streamed directly to console.",
                            "stderr_info": stderr if capture_output else "Output streamed directly to console."})
        _log_action(action_log_name, "SUCCESS", f"Command executed successfully: {cmd_str}", details=log_details)

        if capture_output and not suppress_console_output_on_success:
            if stdout: print(f"  OUT: {stdout}")
            if stderr: print(f"  INF_STDERR: {stderr}", file=sys.stdout)
        return stdout, stderr
    except subprocess.CalledProcessError as e:
        log_details.update({"error_type": "CalledProcessError", "return_code": e.returncode,
                            "stdout": e.stdout.strip() if e.stdout and capture_output else ("Output streamed directly to console." if not capture_output else ""),
                            "stderr": e.stderr.strip() if e.stderr and capture_output else ("Output streamed directly to console." if not capture_output else ""),
                            "exception_message": str(e)})
        _log_action(action_log_name, "ERROR", f"Command failed: {cmd_str}", details=log_details)
        print(f"  CMD_ERROR: Command \"{cmd_str}\" failed with exit code {e.returncode}.", file=sys.stderr)
        if capture_output:
            if e.stdout: print(f"  FAIL_STDOUT:\n{e.stdout.strip()}", file=sys.stderr)
            if e.stderr: print(f"  FAIL_STDERR:\n{e.stderr.strip()}", file=sys.stderr)
        raise
    except FileNotFoundError as e:
        cmd_name = command_list[0] if isinstance(command_list, list) else command_list.split()[0]
        log_details.update({"error_type": "FileNotFoundError", "missing_command": cmd_name, "exception_message": str(e)})
        _log_action(action_log_name, "ERROR", f"Command not found: {cmd_name}", details=log_details)
        print(f"  CMD_ERROR: Command '{cmd_name}' not found. Is it installed and in PATH?", file=sys.stderr)
        raise
    except Exception as e:
        log_details.update({"error_type": "UnknownSubprocessException", "exception_message": str(e)})
        _log_action(action_log_name, "ERROR", f"Unexpected error executing command: {cmd_str}", details=log_details)
        print(f"  CMD_ERROR: An unexpected error occurred with command \"{cmd_str}\": {e}", file=sys.stderr)
        raise

def _command_exists(command_name):
    return shutil.which(command_name) is not None

# --- UV & Tool Installation ---

def _install_uv_macos_brew():
    action_name = "install_uv_macos_brew"
    _log_action(action_name, "INFO", "Attempting `uv` installation via Homebrew.")
    if not _command_exists("brew"):
        msg = "Homebrew (brew) not found. Cannot attempt `uv` installation via Homebrew."
        _log_action(action_name, "WARN", msg)
        print(f"WARN: {msg}\n      Please install Homebrew from https://brew.sh/ or allow installation via the official script.", file=sys.stderr)
        return False
    try:
        _run_command(["brew", "install", "uv"], f"{action_name}_exec", suppress_console_output_on_success=False)
        if _command_exists("uv"):
            _log_action(action_name, "SUCCESS", "`uv` installed/updated via Homebrew.")
            return True
        else:
            msg = "`brew install uv` seemed to complete, but `uv` command is still not found."
            _log_action(action_name, "ERROR", msg)
            print(f"ERROR: {msg}\n       Try running `brew doctor` or check Homebrew's output for errors.\n       Ensure Homebrew's bin directory (e.g., /opt/homebrew/bin or /usr/local/bin) is in your PATH.", file=sys.stderr)
            return False
    except Exception:
        _log_action(action_name, "ERROR", "`uv` installation via Homebrew failed (see command execution log for details).")
        print(f"ERROR: `uv` installation via Homebrew failed. See details above.", file=sys.stderr)
        print(f"       You can try running `brew install uv` manually in your terminal.", file=sys.stderr)
        return False

def _install_uv_script():
    action_name = "install_uv_official_script"
    _log_action(action_name, "INFO", "Attempting `uv` installation via official script.")
    command_str = ""
    try:
        if sys.platform == "win32":
            command_str = 'powershell -ExecutionPolicy ByPass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"'
            _run_command(command_str, f"{action_name}_exec_ps", shell=True, capture_output=False)
        else:
            if not _command_exists("curl"):
                msg = "`curl` is not installed. Cannot download `uv` installation script."
                _log_action(action_name, "ERROR", msg)
                print(f"ERROR: {msg}\n       Please install `curl` (e.g., 'sudo apt install curl') and try again.", file=sys.stderr)
                return False
            command_str = "curl -LsSf https://astral.sh/uv/install.sh | sh"
            _run_command(command_str, f"{action_name}_exec_curl", shell=True, capture_output=False)

        print("INFO: `uv` installation script execution finished. It usually adds `uv` to your PATH.")
        print("INFO: If `uv` is not found immediately, you might need to restart your terminal or source your shell profile.")
        if _command_exists("uv"):
            _log_action(action_name, "SUCCESS", "`uv` now available after script install.")
            return True
        else:
            msg = "`uv` command still not found after official script execution. PATH adjustment or shell restart may be needed."
            _log_action(action_name, "WARN", msg)
            print(f"WARN: {msg}\n      `uv` typically installs to $HOME/.local/bin or similar. Ensure this is in your PATH.", file=sys.stderr)
            return False
    except Exception:
        _log_action(action_name, "ERROR", f"Official `uv` installation script execution failed (command: {command_str}). See command execution log.")
        print(f"ERROR: Official `uv` installation script failed. See details above.", file=sys.stderr)
        print(f"       Try running the command manually in your terminal to diagnose:\n       {command_str}", file=sys.stderr)
        return False

def _ensure_uv_installed():
    action_name = "ensure_uv_installed_phase"
    _log_action(action_name, "INFO", "Starting `uv` availability check and installation if needed.")
    try:
        if _command_exists("uv"):
            version_out, _ = _run_command(["uv", "--version"], f"{action_name}_version_check", suppress_console_output_on_success=True)
            msg = f"`uv` is already installed. Version: {version_out}"
            _log_action(action_name, "SUCCESS", msg)
            print(f"INFO: {msg}")
            return True
    except Exception as e:
         _log_action(f"{action_name}_version_check", "ERROR", f"`uv --version` failed, though `uv` command seems to exist.", details={"exception": str(e)})
         print(f"WARN: `uv` command seems to exist, but 'uv --version' failed: {e}. Will attempt to ensure/reinstall.", file=sys.stderr)

    _log_action(action_name, "INFO", "`uv` not found or version check failed. Attempting installation.")
    print("INFO: `uv` not found in PATH or `uv --version` verification failed. Attempting installation...")

    installed_successfully = False
    install_method_log = "None"

    if sys.platform == "darwin":
        if _command_exists("brew"):
            install_method_log = "Homebrew"
            if _install_uv_macos_brew(): installed_successfully = True
        if not installed_successfully:
            install_method_log = f"{install_method_log} -> Official Script (macOS)" if install_method_log != "None" else "Official Script (macOS)"
            if _install_uv_script(): installed_successfully = True
    elif sys.platform.startswith("linux") or sys.platform == "win32":
        install_method_log = "Official Script"
        if _install_uv_script(): installed_successfully = True
    else:
        msg = f"Unsupported platform for automatic `uv` installation: {sys.platform}"
        _log_action(action_name, "ERROR", msg)
        print(f"ERROR: {msg}\n       Please install `uv` manually from https://astral.sh/uv", file=sys.stderr)
        return False

    if installed_successfully and _command_exists("uv"):
        try:
            version_out, _ = _run_command(["uv", "--version"], f"{action_name}_post_install_version_check", suppress_console_output_on_success=True)
            msg = f"`uv` successfully installed/ensured via {install_method_log}. Version: {version_out}"
            _log_action(action_name, "SUCCESS", msg)
            print(f"INFO: {msg}")
            return True
        except Exception as e:
            msg = f"`uv` reported as installed via {install_method_log}, but 'uv --version' still fails post-install."
            _log_action(action_name, "ERROR", msg, details={"exception": str(e)})
            print(f"ERROR: {msg} Exception: {e}\n       This might indicate an issue with the `uv` binary or its PATH setup after installation.", file=sys.stderr)
            return False
    else:
        msg = f"`uv` installation failed using method(s): {install_method_log}, or `uv` command is still not available."
        _log_action(action_name, "ERROR", msg)
        print(f"ERROR: {msg}\n       Please install `uv` manually from https://astral.sh/uv and ensure it's in your PATH.\n       You may need to restart your terminal or source your shell profile.", file=sys.stderr)
        return False

def _ensure_tool_available(tool_name, package_to_install_via_uv_tool):
    action_name = f"ensure_tool_{tool_name}"
    _log_action(action_name, "INFO", f"Ensuring CLI tool `{tool_name}` (package: `{package_to_install_via_uv_tool}`) is available for `uvx`.")
    try:
        _run_command(["uv", "tool", "install", package_to_install_via_uv_tool], f"{action_name}_uv_tool_install", suppress_console_output_on_success=True)
        msg = f"`{tool_name}` (package '{package_to_install_via_uv_tool}') install/check via `uv tool install` complete. Will be run via `uvx`."
        _log_action(action_name, "SUCCESS", msg)
        print(f"INFO: {msg}")
        return True
    except Exception:
        _log_action(action_name, "ERROR", f"Failed to ensure `{tool_name}` via `uv tool install`. See command execution log for details.")
        print(f"ERROR: Failed to ensure `{tool_name}` is available. Check details above.", file=sys.stderr)
        print(f"       If `uv` is working, try manually: `uv tool install {package_to_install_via_uv_tool}`", file=sys.stderr)
        return False

# --- Project and Dependency Handling ---

def _ensure_project_initialized(project_root: Path):
    action_name = "ensure_project_initialized_with_pyproject"
    pyproject_path = project_root / PYPROJECT_TOML_NAME
    if pyproject_path.exists():
        msg = f"'{PYPROJECT_TOML_NAME}' already exists at {project_root}."
        _log_action(action_name, "INFO", msg)
        print(f"INFO: {msg}")
        return True

    _log_action(action_name, "INFO", f"'{PYPROJECT_TOML_NAME}' not found. Initializing project with `uv init`...")
    print(f"INFO: '{PYPROJECT_TOML_NAME}' not found. Initializing project with `uv init`...")
    try:
        _run_command(["uv", "init"], f"{action_name}_uv_init")
        if pyproject_path.exists():
            msg = f"`uv init` completed. '{PYPROJECT_TOML_NAME}' created."
            _log_action(action_name, "SUCCESS", msg)
            print(f"INFO: {msg}")
            return True
        else:
            msg = f"`uv init` ran but '{PYPROJECT_TOML_NAME}' was not created. This is unexpected."
            _log_action(action_name, "ERROR", msg)
            print(f"ERROR: {msg}\n       Check `uv init` output above. Manual creation of `pyproject.toml` might be needed.", file=sys.stderr)
            return False
    except Exception:
        _log_action(action_name, "ERROR", f"Failed to initialize project with `uv init`. See command execution log for details.")
        print(f"ERROR: Failed to initialize project with `uv init`. See details above.", file=sys.stderr)
        print(f"       You might need to create a `pyproject.toml` manually or resolve issues with `uv init`.", file=sys.stderr)
        return False

def _get_declared_dependencies(pyproject_path: Path) -> set[str]:
    action_name = "get_declared_dependencies_from_pyproject"
    dependencies = set()
    if not pyproject_path.exists():
        _log_action(action_name, "WARN", f"'{pyproject_path.name}' not found when trying to read declared dependencies. Assuming none declared yet.")
        return dependencies

    tomllib_module = None
    tomllib_source = "None"
    if sys.version_info >= (3, 11):
        try: tomllib_module = importlib.import_module("tomllib"); tomllib_source = "tomllib (Python 3.11+ built-in)"
        except ImportError: pass
    if not tomllib_module:
        try: tomllib_module = importlib.import_module("toml"); tomllib_source = "toml (third-party package)"
        except ImportError:
            msg = "Cannot parse `pyproject.toml` to read existing dependencies: `tomllib` (Python 3.11+) or `toml` package not available in the environment running this script."
            _log_action(action_name, "WARN", msg + " Dependency checking against `pyproject.toml` will be skipped before `uv add` (this is okay as `uv add` is idempotent).")
            print(f"WARN: {msg} This script is best run with Python 3.11+ or with the 'toml' package installed in its execution environment.", file=sys.stderr)
            return dependencies

    _log_action(action_name, "INFO", f"Attempting to parse '{pyproject_path.name}' for existing dependencies using {tomllib_source}.")
    try:
        with open(pyproject_path, "rb") as f: data = tomllib_module.load(f)
        project_data = data.get("project", {})
        for dep_section_key in ["dependencies", "optional-dependencies"]:
            deps_source = project_data.get(dep_section_key, [])
            items_to_parse = []
            if isinstance(deps_source, list): # [project.dependencies]
                items_to_parse.extend(deps_source)
            elif isinstance(deps_source, dict): # [project.optional-dependencies]
                for group_list in deps_source.values():
                    if isinstance(group_list, list): items_to_parse.extend(group_list)

            for dep_str in items_to_parse:
                if isinstance(dep_str, str): # Ensure it's a string
                    pkg_name = dep_str.split("[")[0].split("=")[0].split(">")[0].split("<")[0].split("!")[0].split("~")[0].strip()
                    if pkg_name: dependencies.add(pkg_name.lower())

        _log_action(action_name, "SUCCESS", f"Parsed '{pyproject_path.name}'. Found {len(dependencies)} unique base dependency names declared.", details={"source": tomllib_source, "count": len(dependencies), "found_names": sorted(list(dependencies)) if dependencies else "None"})
        return dependencies
    except Exception as e:
        msg = f"Failed to parse '{pyproject_path.name}' using {tomllib_source} to get dependency list."
        _log_action(action_name, "ERROR", msg, details={"exception": str(e)})
        print(f"ERROR: {msg} Exception: {e}. Check its TOML syntax. The list of declared dependencies might be incomplete for subsequent checks.", file=sys.stderr)
        return dependencies

def _get_packages_from_legacy_req_txt(requirements_path: Path) -> set[str]:
    """Reads package specifiers from a legacy requirements.txt file."""
    action_name = "read_legacy_requirements_txt"
    packages_specs = set()
    if not requirements_path.exists():
        _log_action(action_name, "INFO", f"No legacy '{requirements_path.name}' found.")
        return packages_specs

    _log_action(action_name, "INFO", f"Reading legacy '{requirements_path.name}'.")
    try:
        with open(requirements_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-e"): continue
                if line: packages_specs.add(line)
        _log_action(action_name, "SUCCESS", f"Read {len(packages_specs)} package specifiers from '{requirements_path.name}'.")
    except Exception as e:
        msg = f"Could not read '{requirements_path.name}' for migration."
        _log_action(action_name, "ERROR", msg, details={"exception": str(e)})
        print(f"ERROR: {msg} Exception: {e}. Skipping migration of this file.", file=sys.stderr)
    return packages_specs


def _migrate_req_txt_to_pyproject(requirements_path: Path, venv_python_executable: Path, declared_deps_before_migration: set):
    action_name = "migrate_legacy_requirements_txt_to_pyproject"

    packages_from_req_txt_specs = _get_packages_from_legacy_req_txt(requirements_path)
    if not packages_from_req_txt_specs: # Either file didn't exist or was empty/unreadable
        _log_action(action_name, "INFO", "No packages from legacy requirements.txt to migrate.")
        return # Nothing to do

    _log_action(action_name, "INFO", f"Attempting to migrate {len(packages_from_req_txt_specs)} specifier(s) from '{requirements_path.name}' to `pyproject.toml` if not already declared.")
    print(f"INFO: Migrating packages from '{requirements_path.name}' to `pyproject.toml` (if new)...")

    migrated_count = 0
    failed_migrations = []
    packages_actually_added_log = []

    for pkg_specifier in sorted(list(packages_from_req_txt_specs)):
        base_pkg_name = pkg_specifier.split("[")[0].split("=")[0].split(">")[0].split("<")[0].split("!")[0].split("~")[0].strip().lower()

        if base_pkg_name in declared_deps_before_migration:
            _log_action(f"{action_name}_skip_add", "INFO", f"Package '{base_pkg_name}' (from specifier '{pkg_specifier}') appears already declared in `pyproject.toml`. Skipping redundant `uv add` during migration.")
            continue

        _log_action(f"{action_name}_attempt_add", "INFO", f"Attempting to `uv add \"{pkg_specifier}\"` from '{requirements_path.name}' to `pyproject.toml`.")
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

    # Advise user about the legacy requirements.txt, DO NOT RENAME AUTOMATICALLY
    if packages_from_req_txt_specs:
        advise_msg = (f"Dependencies from '{requirements_path.name}' have been processed and relevant ones added to `{PYPROJECT_TOML_NAME}`. "
                      f"The original '{requirements_path.name}' has NOT been modified by this script. "
                      f"It's recommended to use `{PYPROJECT_TOML_NAME}` as the primary source of dependencies going forward. "
                      f"You may want to manually archive, delete, or replace '{requirements_path.name}' with one generated from "
                      f"`pyproject.toml` (e.g., using `uv pip compile {PYPROJECT_TOML_NAME} -o {LEGACY_REQUIREMENTS_TXT}`) if it's needed for other tools.")
        _log_action(f"{action_name}_advise_user", "INFO", advise_msg)
        print(f"INFO: {advise_msg}")


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
                if not line or line.startswith("#"): continue
                package_name = line.split("==")[0].split(">=")[0].split("<=")[0].split("!=")[0].split("~=")[0].strip()
                if package_name:
                    packages.add(package_name.lower())
                    parsed_count +=1

        if parsed_count > 0:
            _log_action(action_name, "SUCCESS", f"Discovered {len(packages)} unique potential package name(s) via `pipreqs`: {', '.join(sorted(list(packages)))}.")
        elif not stdout.strip():
             _log_action(action_name, "INFO", "`pipreqs` (via `uvx`) produced no output. This might mean no import-based dependencies were found, or there was an issue running it (check command log).")
        else:
             _log_action(action_name, "INFO", "`pipreqs` (via `uvx`) ran but no parseable package names were found in its output.")
        return packages
    except subprocess.CalledProcessError:
        _log_action(action_name, "ERROR", "`uvx pipreqs` command failed. Cannot automatically discover dependencies. See command execution log for details.")
        print(f"ERROR: `uvx pipreqs` command failed. See details above.", file=sys.stderr)
        print(f"       This might be due to `pipreqs` internal errors, project scan issues, or `uvx` problems.", file=sys.stderr)
        print(f"       Consider running manually for debug: {' '.join(pipreqs_args)} --debug", file=sys.stderr)
    except Exception as e:
        _log_action(action_name, "ERROR", "An unexpected error occurred while running/processing `pipreqs`.", details={"exception": str(e)})
        print(f"ERROR: An unexpected error occurred while running/processing `pipreqs`: {e}", file=sys.stderr)
    return packages

def _configure_vscode_settings(project_root: Path, venv_python_executable: Path):
    action_name = "configure_vscode_settings"
    _log_action(action_name, "INFO", f"Configuring VS Code settings in '{VSCODE_DIR_NAME}'.")
    vscode_dir_path = project_root / VSCODE_DIR_NAME
    settings_file_path = vscode_dir_path / SETTINGS_FILE_NAME

    try:
        vscode_dir_path.mkdir(exist_ok=True)
        settings_data = {}
        if settings_file_path.exists():
            try:
                with open(settings_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip(): settings_data = json.loads(content)
            except json.JSONDecodeError:
                msg = f"Existing '{settings_file_path.name}' is not valid JSON. It will be overwritten with the interpreter path setting."
                _log_action(action_name, "WARN", msg)
                print(f"WARN: {msg}", file=sys.stderr)
            except Exception as e:
                msg = f"Could not read existing '{settings_file_path.name}': {e}. It may be overwritten."
                _log_action(action_name, "WARN", msg, details={"exception": str(e)})
                print(f"WARN: {msg}", file=sys.stderr)

        resolved_interpreter_path = str(venv_python_executable.resolve())
        settings_data["python.defaultInterpreterPath"] = resolved_interpreter_path

        with open(settings_file_path, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=4)

        msg = f"VS Code 'python.defaultInterpreterPath' set in '{settings_file_path.name}'."
        _log_action(action_name, "SUCCESS", msg, details={"interpreter_path": resolved_interpreter_path})
        print(f"INFO: {msg}\n      Interpreter Path: {resolved_interpreter_path}")
    except Exception as e:
        msg = f"Failed to configure VS Code settings in '{settings_file_path.name}'."
        _log_action(action_name, "ERROR", msg, details={"exception": str(e)})
        print(f"ERROR: {msg} Exception: {e}", file=sys.stderr)
        print(f"       Please check permissions for the '.vscode' directory and '{settings_file_path.name}'.", file=sys.stderr)
        print(f"       You may need to manually set the Python interpreter in VS Code. Recommended path:", file=sys.stderr)
        print(f"       {str(venv_python_executable.resolve())}", file=sys.stderr)

# --- Main Orchestration Function ---
def main():
    project_root = Path.cwd()
    log_file_path = project_root / JSON_LOG_FILE_NAME
    _init_log()

    pyproject_file_path = project_root / PYPROJECT_TOML_NAME
    legacy_req_path = project_root / LEGACY_REQUIREMENTS_TXT

    print(f"--- Starting Automated Python Project Setup ({_log_data_global['script_name']}) in: {project_root} ---")
    print(f"--- Using Virtual Environment Name: '{VENV_NAME}' ---")
    print(f"--- Primary Dependency File: '{PYPROJECT_TOML_NAME}' ---")
    print(f"--- JSON Log will be saved to: '{log_file_path.name}' ---")

    venv_python_executable = None # Define for broader scope, used in exception hints

    try:
        if not _ensure_uv_installed():
            raise SystemExit("Halting: `uv` could not be installed or verified. Check log and console output for details.")

        if not _ensure_project_initialized(project_root):
            raise SystemExit(f"Halting: Project could not be initialized with '{PYPROJECT_TOML_NAME}'. Check log and console output.")

        action_venv = "create_or_verify_venv"
        _log_action(action_venv, "INFO", f"Creating/ensuring virtual environment '{VENV_NAME}'.")
        _run_command(["uv", "venv", VENV_NAME], f"{action_venv}_uv_venv")
        venv_path = project_root / VENV_NAME
        venv_python_executable = venv_path / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")
        if not venv_python_executable.exists():
            msg = f"Virtual environment Python executable not found at '{venv_python_executable}' after `uv venv` command."
            _log_action(action_venv, "ERROR", msg)
            raise SystemExit(f"CRITICAL ERROR: {msg}\n       This indicates a problem with `uv venv` or an unexpected environment structure.")
        _log_action(action_venv, "SUCCESS", f"Virtual environment '{VENV_NAME}' ready. Interpreter: '{venv_python_executable}'.")
        print(f"INFO: Virtual environment '{VENV_NAME}' ready. Interpreter: '{venv_python_executable}'")

        declared_deps_before_migration = _get_declared_dependencies(pyproject_file_path)
        if legacy_req_path.exists():
            _migrate_req_txt_to_pyproject(legacy_req_path, venv_python_executable, declared_deps_before_migration)
        else:
            _log_action("migrate_legacy_requirements_txt", "INFO", f"No '{LEGACY_REQUIREMENTS_TXT}' found, skipping migration step.")

        action_sync = "uv_sync_dependencies"
        _log_action(action_sync, "INFO", "Syncing environment with `pyproject.toml` and `uv.lock` using `uv sync`.")
        print(f"\n--- Syncing all declared dependencies from '{PYPROJECT_TOML_NAME}' using `uv sync` ---")
        _run_command(["uv", "sync", "--python", str(venv_python_executable)], f"{action_sync}_exec")
        _log_action(action_sync, "SUCCESS", "Environment synced with `pyproject.toml` and `uv.lock`.")
        print(f"INFO: Environment synced with '{PYPROJECT_TOML_NAME}' and `uv.lock`.")

        action_pipreqs_phase = "pipreqs_discovery_and_add_phase"
        _log_action(action_pipreqs_phase, "INFO", "Starting dependency discovery with `pipreqs` to add to `pyproject.toml`.")
        print(f"\n--- Discovering additional project imports via `pipreqs` to add to '{PYPROJECT_TOML_NAME}' ---")

        if _ensure_tool_available("pipreqs", "pipreqs"):
            discovered_by_pipreqs = _get_packages_from_pipreqs(project_root, VENV_NAME)

            if discovered_by_pipreqs:
                current_declared_deps = _get_declared_dependencies(pyproject_file_path)
                genuinely_new_packages_to_add = discovered_by_pipreqs - current_declared_deps

                if genuinely_new_packages_to_add:
                    pkgs_added_count = 0
                    print(f"INFO: `pipreqs` discovered {len(genuinely_new_packages_to_add)} potential new package(s) not yet in `pyproject.toml` dependencies:")
                    for pkg_name in sorted(list(genuinely_new_packages_to_add)): print(f"         - {pkg_name}")
                    print(f"INFO: Automatically adding these {len(genuinely_new_packages_to_add)} package(s) to `pyproject.toml` using `uv add`...")

                    for pkg_to_add in sorted(list(genuinely_new_packages_to_add)):
                        try:
                            _run_command(["uv", "add", pkg_to_add, "--python", str(venv_python_executable)], f"{action_pipreqs_phase}_uv_add_{pkg_to_add.replace('-', '_').replace('.', '_')}")
                            pkgs_added_count +=1
                        except Exception:
                            print(f"ERROR: Failed to `uv add {pkg_to_add}`. Check log and `uv add` output above.", file=sys.stderr)

                    msg = f"Attempted to `uv add` {pkgs_added_count}/{len(genuinely_new_packages_to_add)} newly discovered packages to `pyproject.toml`."
                    status = "SUCCESS" if pkgs_added_count == len(genuinely_new_packages_to_add) else "WARN"
                    _log_action(action_pipreqs_phase, status, msg, details={"total_discovered_new": len(genuinely_new_packages_to_add), "successfully_added_count": pkgs_added_count})
                    print(f"{status.upper()}: {msg}")
                    if status == "WARN":
                         print("WARN: Some newly discovered packages could not be added via `uv add`. Review logs and `uv` output.", file=sys.stderr)
                elif discovered_by_pipreqs:
                     _log_action(action_pipreqs_phase, "INFO", "All `pipreqs` discovered dependencies seem already declared in `pyproject.toml`.")
                     print("INFO: `pipreqs` found dependencies, but all seem covered by `pyproject.toml`.")
        else:
            _log_action(action_pipreqs_phase, "ERROR", "`pipreqs` tool setup failed. Skipping automatic import discovery.")
            print("WARN: `pipreqs` setup failed. Skipping automatic import discovery and addition of new dependencies.", file=sys.stderr)

        _configure_vscode_settings(project_root, venv_python_executable)

        _log_action("script_end", "SUCCESS", "Automated project setup script completed successfully.")
        print("\n--- Automated Project Setup Complete ---")
        print(f"Virtual Environment: {venv_path}")
        print(f"Primary Dependency File: {pyproject_file_path.name} (should be up-to-date)")
        print(f"Lock File: {project_root / 'uv.lock'} (should be up-to-date)")
        print(f"VS Code Configured: Check '{VSCODE_DIR_NAME}/{SETTINGS_FILE_NAME}'")
        print(f"Detailed Log: '{JSON_LOG_FILE_NAME}'")
        print("\nNext Steps:")
        print(f"- If VS Code is open with this project, reload the window (Ctrl+Shift+P > 'Developer: Reload Window').")
        print(f"- Activate the environment in your terminal: source {VENV_NAME}/bin/activate (Linux/macOS) or .\\{VENV_NAME}\\Scripts\\activate (Windows PowerShell)")
        print(f"- Review `pyproject.toml` and `uv.lock`, then test your project to ensure all dependencies are correctly captured and functional.")

    except SystemExit as e:
        msg = f"Script halted by explicit exit: {e}"
        if _log_data_global.get("overall_status") == "IN_PROGRESS": _log_data_global["overall_status"] = "HALTED_BY_SCRIPT_LOGIC"
        _log_data_global["final_summary"] = _log_data_global.get("final_summary", msg)
        print(f"\nSCRIPT HALTED: {e}", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        failed_cmd_str = ' '.join(e.cmd) if isinstance(e.cmd, list) else str(e.cmd)
        msg = f"A critical command failed execution: {failed_cmd_str}"
        _log_data_global["final_summary"] = msg
        _log_data_global["overall_status"] = "CRITICAL_COMMAND_FAILED"
        print(f"\nCRITICAL ERROR: {msg}, halting script.", file=sys.stderr)
        print("  Details of the failed command should be visible in the output above and in the JSON log.", file=sys.stderr)

        cmd_str_lower = failed_cmd_str.lower()
        if "uv pip install" in cmd_str_lower or "uv add" in cmd_str_lower or "uv sync" in cmd_str_lower :
            print("\nINSTALLATION/SYNC HINT: A package operation with `uv` failed:", file=sys.stderr)
            print("  - Review `uv`'s error output (logged as FAIL_STDERR/FAIL_STDOUT for the command) for specific package names or reasons.", file=sys.stderr)
            print("  - Ensure the package name is correct and exists on PyPI (https://pypi.org) or your configured index.", file=sys.stderr)
            print("  - Some packages require system-level (non-Python) libraries to be installed first. Check the package's documentation.", file=sys.stderr)
            if venv_python_executable: # Check if it was defined
                 print(f"  - You might need to manually edit '{PYPROJECT_TOML_NAME}' and then run `uv sync --python {venv_python_executable}`.", file=sys.stderr)
            else:
                 print(f"  - You might need to manually edit '{PYPROJECT_TOML_NAME}' and then run `uv sync` after ensuring the venv is correctly set up.", file=sys.stderr)

        elif "pipreqs" in cmd_str_lower:
             print("\nPIPReQS HINT: The 'pipreqs' command (run via 'uvx') failed.", file=sys.stderr)
             print("  - This could be due to syntax errors in your Python files that `pipreqs` cannot parse, an internal `pipreqs` issue, or `uvx` failing to execute `pipreqs`.", file=sys.stderr)
             print(f"  - Try running manually for debug: uvx pipreqs \"{project_root}\" --ignore \"{VENV_NAME}\" --debug", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        cmd_name = e.filename if hasattr(e, 'filename') and e.filename else "An external command"
        msg = f"Required system command '{cmd_name}' was not found."
        _log_data_global["final_summary"] = msg
        _log_data_global["overall_status"] = "MISSING_SYSTEM_COMMAND"
        print(f"\nCRITICAL ERROR: {msg} Setup aborted.", file=sys.stderr)
        print(f"       Please install '{cmd_name}' or ensure it's in your system's PATH.", file=sys.stderr)
        if cmd_name == "brew": print("         For Homebrew on macOS, see https://brew.sh/", file=sys.stderr)
        if cmd_name == "curl": print("         For curl, see your OS package manager (e.g., 'sudo apt install curl' or 'sudo yum install curl').", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        msg = f"An unexpected critical error occurred: {e}"
        _log_action("unexpected_critical_error_main", "ERROR", msg, details={"exception_type": type(e).__name__, "exception_message": str(e), "traceback": tb_str.splitlines()})
        print(f"\nAN UNEXPECTED CRITICAL ERROR OCCURRED: {e}", file=sys.stderr)
        print(tb_str, file=sys.stderr)
        print("Setup aborted due to an unexpected error. Please review the traceback and the JSON log.", file=sys.stderr)
        _log_data_global["final_summary"] = msg
        _log_data_global["overall_status"] = "UNEXPECTED_ERROR"
        sys.exit(1)
    finally:
        if "start_time_utc" in _log_data_global:
            _save_log(log_file_path)

if __name__ == "__main__":
    main()
