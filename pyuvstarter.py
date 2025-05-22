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
"""

import os
import sys
import json
import shutil
import subprocess
import datetime
import platform
import importlib.util
from pathlib import Path

# --- Configuration Constants ---
VENV_NAME = ".venv"
PYPROJECT_TOML_NAME = "pyproject.toml"
GITIGNORE_NAME = ".gitignore"
LEGACY_REQUIREMENTS_TXT = "requirements.txt" # For migration
VSCODE_DIR_NAME = ".vscode"
SETTINGS_FILE_NAME = "settings.json"
JSON_LOG_FILE_NAME = "pyuvstarter_setup_log.json"

# --- JSON Logging Utilities ---
_log_data_global = {}

def _init_log():
    """Initializes the global log data structure."""
    global _log_data_global
    _log_data_global = {
        "script_name": Path(__file__).name,
        "start_time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "end_time_utc": None, "overall_status": "IN_PROGRESS",
        "platform_info": {"system": platform.system(), "release": platform.release(),
                          "version": platform.version(), "machine": platform.machine(),
                          "python_version_script_host": sys.version},
        "project_root": str(Path.cwd()), "actions": [],
        "final_summary": None, "errors_encountered_summary": []
    }
    _log_action("script_bootstrap", "INFO", f"Script execution initiated for project at {Path.cwd()}.")

def _log_action(action_name: str, status: str, message: str = "", details: dict = None):
    """Logs an action and prints to console."""
    global _log_data_global
    if "actions" not in _log_data_global: _log_data_global["actions"] = []
    entry = {"timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "action": action_name, "status": status.upper(),
             "message": message, "details": details or {}}
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
        if _log_data_global.get("final_summary"): _log_data_global["final_summary"] += next_steps_text
        else: _log_data_global["final_summary"] = f"Script Status: {_log_data_global['overall_status']}.{next_steps_text}"

    try:
        with open(log_file_path, "w", encoding="utf-8") as f: json.dump(_log_data_global, f, indent=4)
        print(f"INFO: Detailed execution log saved to '{log_file_path.name}'")
    except Exception as e:
        print(f"CRITICAL_ERROR: Failed to save JSON log to '{log_file_path.name}': {e}", file=sys.stderr)

# --- Core Helper Functions ---
def _run_command(command_list, action_log_name: str, work_dir=None, shell=False, capture_output=True, suppress_console_output_on_success=False):
    """
    Runs a shell command and logs its execution. Raises CalledProcessError on failure.
    Returns (stdout_str, stderr_str) if capture_output is True.
    If capture_output is False, stdout/stderr will be empty strings, and output streams to console.
    """
    if work_dir is None: work_dir = Path.cwd()
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
        print(f"ERROR: `uv` installation via Homebrew failed. See details above.\n       Try running `brew install uv` manually.", file=sys.stderr)
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
                print(f"ERROR: `curl` is not installed.\n       Please install `curl` (e.g., 'sudo apt install curl') and try again.", file=sys.stderr)
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
            print(f"WARN: `uv` command still not found after official script execution.\n      `uv` typically installs to $HOME/.local/bin or similar. Ensure this is in your PATH.", file=sys.stderr)
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
         _log_action(f"{action_name}_version_check", "ERROR", f"`uv --version` failed, though `uv` command seems to exist.", details={"exception": str(e)})
         print(f"WARN: `uv` command seems to exist, but 'uv --version' failed: {e}. Will attempt to ensure/reinstall.", file=sys.stderr)

    _log_action(action_name, "INFO", "`uv` not found or version check failed. Attempting installation.")
    print("INFO: `uv` not found in PATH or `uv --version` verification failed. Attempting installation...")

    installed_successfully = False; install_method_log = "None"
    if sys.platform == "darwin":
        if _command_exists("brew"):
            install_method_log = "Homebrew";
            if _install_uv_macos_brew(): installed_successfully = True
        if not installed_successfully:
            install_method_log = f"{install_method_log} -> Official Script (macOS)" if install_method_log != "None" else "Official Script (macOS)"
            if _install_uv_script(): installed_successfully = True
    elif sys.platform.startswith("linux") or sys.platform == "win32":
        install_method_log = "Official Script";
        if _install_uv_script(): installed_successfully = True
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
        print(f"INFO: '{PYPROJECT_TOML_NAME}' already exists.")
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
                    _log_action(f"{action_name}_remove_main_py", "ERROR", f"Failed to remove '{main_py_path.name}' created by `uv init`.", details={"exception": str(e)})
                    print(f"ERROR: Failed to remove '{main_py_path.name}': {e}. Please remove it manually if undesired.", file=sys.stderr)
            else: # Project was empty of .py files, so main.py from uv init is fine
                _log_action(f"{action_name}_keep_main_py", "INFO", f"`uv init` created '{main_py_path.name}' in an otherwise empty Python project. It will be kept.")
                print(f"INFO: `uv init` created '{main_py_path.name}'. Keeping it as standard for a new project.")
        return True

    except Exception: # Error logged by _run_command
        _log_action(action_name, "ERROR", f"Failed to initialize project with `uv init`. See command execution log.")
        print(f"ERROR: Failed to initialize project with `uv init`. See details above.\n       Manual `pyproject.toml` creation or `uv init` troubleshooting needed.", file=sys.stderr)
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
        print(f"INFO: '{GITIGNORE_NAME}' already exists. Will ensure venv and log file are ignored.")
        try:
            with open(gitignore_path, "r+", encoding="utf-8") as f:
                content = f.read()
                if content and not content.endswith("\n"): f.write("\n"); content += "\n"

                entries_to_add_with_comments = []
                for comment, patterns in essential_ignore_map.items():
                    all_patterns_present_for_group = True; temp_patterns_to_add_for_group = []
                    for pattern in patterns:
                        if not any(pattern.strip() == line.strip() for line in content.splitlines()):
                            all_patterns_present_for_group = False
                            temp_patterns_to_add_for_group.append(pattern)
                    if not all_patterns_present_for_group and temp_patterns_to_add_for_group:
                        comment_line = f"# {comment}"
                        if comment_line not in content: entries_to_add_with_comments.append(f"\n{comment_line}")
                        entries_to_add_with_comments.extend(temp_patterns_to_add_for_group)

                if entries_to_add_with_comments:
                    f.write("\n# Added/Ensured by pyuvstarter.py\n")
                    for entry in entries_to_add_with_comments: f.write(f"{entry}\n")
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
                f.write("\n".join(comprehensive_ignores)); f.write("\n")
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

    tomllib_module = None; tomllib_source = "None"
    if sys.version_info >= (3, 11):
        try: tomllib_module = importlib.import_module("tomllib"); tomllib_source = "tomllib (Python 3.11+ built-in)"
        except ImportError: pass
    if not tomllib_module:
        try: tomllib_module = importlib.import_module("toml"); tomllib_source = "toml (third-party package)"
        except ImportError:
            msg = "Cannot parse `pyproject.toml` to read existing dependencies: `tomllib` (Python 3.11+) or `toml` package not available in the environment running this script."
            _log_action(action_name, "WARN", msg + " Dependency checking against `pyproject.toml` will be skipped before `uv add` (this is okay as `uv add` is idempotent).")
            print(f"WARN: {msg} Script best run with Python 3.11+ or with 'toml' installed in its execution environment.", file=sys.stderr)
            return dependencies

    _log_action(action_name, "INFO", f"Attempting to parse '{pyproject_path.name}' for existing dependencies using {tomllib_source}.")
    try:
        with open(pyproject_path, "rb") as f: data = tomllib_module.load(f)
        project_data = data.get("project", {})
        for dep_section_key in ["dependencies", "optional-dependencies"]:
            deps_source = project_data.get(dep_section_key, [])
            items_to_parse = []
            if isinstance(deps_source, list): items_to_parse.extend(deps_source)
            elif isinstance(deps_source, dict):
                for group_list in deps_source.values():
                    if isinstance(group_list, list): items_to_parse.extend(group_list)
            for dep_str in items_to_parse:
                if isinstance(dep_str, str):
                    pkg_name = dep_str.split("[")[0].split("=")[0].split(">")[0].split("<")[0].split("!")[0].split("~")[0].strip()
                    if pkg_name: dependencies.add(pkg_name.lower())

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
                if not line or line.startswith("#") or line.startswith("-e"): continue
                if line: packages_specs.add(line)
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

    migrated_count = 0; failed_migrations = []; packages_actually_added_log = []
    for pkg_specifier in sorted(list(packages_from_req_txt_specs)):
        base_pkg_name = pkg_specifier.split("[")[0].split("=")[0].split(">")[0].split("<")[0].split("!")[0].split("~")[0].strip().lower()
        if base_pkg_name in declared_deps_before_migration:
            _log_action(f"{action_name}_skip_add", "INFO", f"Package '{base_pkg_name}' (from specifier '{pkg_specifier}') appears already declared. Skipping redundant `uv add` during migration.")
            continue
        try:
            _run_command(["uv", "add", pkg_specifier, "--python", str(venv_python_executable)], f"{action_name}_uv_add_'{base_pkg_name.replace('.', '_')}'")
            migrated_count += 1; packages_actually_added_log.append(pkg_specifier)
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
                if not line or line.startswith("#"): continue
                package_name = line.split("==")[0].split(">=")[0].split("<=")[0].split("!=")[0].split("~=")[0].strip()
                if package_name: packages.add(package_name.lower()); parsed_count +=1

        if parsed_count > 0:
            _log_action(action_name, "SUCCESS", f"Discovered {len(packages)} unique potential package name(s) via `pipreqs`: {', '.join(sorted(list(packages)))}.")
        elif not stdout.strip():
             _log_action(action_name, "INFO", "`pipreqs` (via `uvx`) produced no output. No import-based dependencies found or an issue running it (check command log).")
        else:
             _log_action(action_name, "INFO", "`pipreqs` (via `uvx`) ran but no parseable package names were found in its output.")
        return packages
    except subprocess.CalledProcessError:
        _log_action(action_name, "ERROR", "`uvx pipreqs` command failed. Cannot automatically discover dependencies. See command execution log for details.")
        print(f"ERROR: `uvx pipreqs` command failed. See details above.", file=sys.stderr)
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
    resolved_interpreter_path = str(venv_python_executable.resolve())
    settings_data["python.defaultInterpreterPath"] = resolved_interpreter_path
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
    _log_action(action_name, "SUCCESS", msg, details={"interpreter_path": resolved_interpreter_path})
    print(f"INFO: VS Code 'python.defaultInterpreterPath' set in '{settings_file_path.name}'\n      Path: {resolved_interpreter_path}\n      (Managed by pyuvstarter and uv)")

def _ensure_vscode_launch_json(project_root: Path, venv_python_executable: Path):
    """
    Ensure .vscode/launch.json exists and has a launch config for the currently active Python file using the venv Python.
    If launch.json is invalid JSON, back it up before overwriting. Only add a new config if needed, never remove user configs.
    The launch config is maximally integrated with uv: it uses the venv interpreter and is generic for any Python file.
    """
    action_name = "ensure_vscode_launch_json"
    vscode_dir = project_root / VSCODE_DIR_NAME
    launch_path = vscode_dir / "launch.json"
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
                "python": str(venv_python_executable.resolve()),
                "justMyCode": True,
                "internalConsoleOptions": "neverOpen",
                "env": {},
                "cwd": "${workspaceFolder}",
                "args": [],
                "description": "Runs the currently open Python file using the uv-managed virtual environment."
            }
        ]
    }
    backup_made = False
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
                print(f"INFO: Added launch config for current file to existing .vscode/launch.json.")
            else:
                _log_action(action_name, "INFO", "Launch config for current file and venv python already present in launch.json.")
                print(f"INFO: Launch config for current file and venv python already present in .vscode/launch.json.")
        except json.JSONDecodeError:
            # Backup invalid JSON before overwriting
            backup_path = launch_path.with_suffix(f".bak_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
            shutil.copy2(launch_path, backup_path)
            backup_made = True
            _log_action(action_name, "WARN", f"Existing '{launch_path.name}' is not valid JSON. Backed up before overwrite.", details={"backup": str(backup_path)})
            with open(launch_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
            _log_action(action_name, "SUCCESS", f"Created new launch.json for current file. (Backed up old file)")
            print(f"INFO: Created new .vscode/launch.json for current file. (Backed up old file)")
        except Exception as e:
            _log_action(action_name, "ERROR", f"Could not update existing launch.json: {e}")
            print(f"ERROR: Could not update .vscode/launch.json: {e}", file=sys.stderr)
    else:
        with open(launch_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        _log_action(action_name, "SUCCESS", "Created new launch.json for current file.")
        print(f"INFO: Created new .vscode/launch.json for current file.")

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

    venv_python_executable = None

    try:
        if not _ensure_uv_installed():
            raise SystemExit(f"Halting: `uv` could not be installed or verified. Check log and console output for details.")

        if not _ensure_project_initialized(project_root): # This now handles conditional main.py removal
            raise SystemExit(f"Halting: Project could not be initialized with '{PYPROJECT_TOML_NAME}'. Check log and console output.")

        _ensure_gitignore_exists(project_root, VENV_NAME)

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
            _log_action("migrate_legacy_requirements_txt_to_pyproject", "INFO", f"No '{LEGACY_REQUIREMENTS_TXT}' found, skipping migration step.")

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
                    if status == "WARN": print("WARN: Some newly discovered packages could not be added via `uv add`. Review logs and `uv` output.", file=sys.stderr)
                elif discovered_by_pipreqs:
                     _log_action(action_pipreqs_phase, "INFO", "All `pipreqs` discovered dependencies seem already declared in `pyproject.toml`.")
                     print("INFO: `pipreqs` found dependencies, but all seem covered by `pyproject.toml`.")
        else:
            _log_action(action_pipreqs_phase, "ERROR", "`pipreqs` tool setup failed. Skipping automatic import discovery.")
            print("WARN: `pipreqs` setup failed. Skipping automatic import discovery and addition of new dependencies.", file=sys.stderr)

        _configure_vscode_settings(project_root, venv_python_executable)
        _ensure_vscode_launch_json(project_root, venv_python_executable)

        _log_action("script_end", "SUCCESS", "Automated project setup script completed successfully.")
        print("\n--- Automated Project Setup Complete ---")
        print(f"Virtual Environment: {venv_path}")
        print(f"Primary Dependency File: {pyproject_file_path.name} (should be up-to-date)")
        print(f"Lock File: {project_root / 'uv.lock'} (should be up-to-date)")
        print(f"VS Code Configured: Check '{VSCODE_DIR_NAME}/{SETTINGS_FILE_NAME}'")
        print(f"Git Ignore File: '{GITIGNORE_NAME}' (created or checked)")
        print(f"Detailed Log: '{JSON_LOG_FILE_NAME}'")
        print("\nNext Steps:")
        print(f"- If VS Code is open with this project, reload the window (Ctrl+Shift+P > 'Developer: Reload Window').")
        print(f"- Activate the environment in your terminal: source {VENV_NAME}/bin/activate (Linux/macOS) or .\\{VENV_NAME}\\Scripts\\activate (Windows PowerShell)")
        print(f"- Review `pyproject.toml`, `uv.lock`, and '{GITIGNORE_NAME}', then test your project to ensure all dependencies are correctly captured and functional.")
        print(f"- Commit `pyproject.toml`, `uv.lock`, `{GITIGNORE_NAME}`, and your source files (including this script if desired) to version control.")

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
            if venv_python_executable: print(f"  - You might need to manually edit '{PYPROJECT_TOML_NAME}' and then run `uv sync --python {venv_python_executable}`.", file=sys.stderr)
            else: print(f"  - You might need to manually edit '{PYPROJECT_TOML_NAME}' and then run `uv sync` after ensuring the venv is correctly set up.", file=sys.stderr)
        elif "pipreqs" in cmd_str_lower:
             print("\nPIPReQS HINT: The 'pipreqs' command (run via 'uvx') failed.", file=sys.stderr)
             print("  - This could be due to syntax errors in your Python files that `pipreqs` cannot parse, an internal `pipreqs` issue, or `uvx` failing to execute `pipreqs`.", file=sys.stderr)
             print(f"  - Try running manually for debug: uvx pipreqs \"{project_root}\" --ignore \"{VENV_NAME}\" --debug", file=sys.stderr)
        elif "uv venv" in cmd_str_lower:
            print("\nVIRTUAL ENV HINT: `uv venv` command failed.", file=sys.stderr)
            print(f"  - Ensure `uv` is correctly installed and functional. Check `uv --version`.", file=sys.stderr)
            print(f"  - Check for issues like insufficient disk space or permissions in the project directory '{project_root}'.", file=sys.stderr)
        elif "uv tool install" in cmd_str_lower:
            print("\nUV TOOL INSTALL HINT: `uv tool install` (likely for pipreqs) failed.", file=sys.stderr)
            print(f"  - This could be due to network issues, `uv` problems, or the tool package ('pipreqs') not being found by `uv`.", file=sys.stderr)
            print(f"  - Try running `uv tool install pipreqs` manually in your terminal.", file=sys.stderr)
        elif "uv init" in cmd_str_lower:
            print("\nUV INIT HINT: `uv init` command failed.", file=sys.stderr)
            print(f"  - Ensure `uv` is correctly installed. Try running `uv init` manually in an empty directory to test.", file=sys.stderr)
            print(f"  - Check for permissions issues in the project directory '{project_root}'.", file=sys.stderr)
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
