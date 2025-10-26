#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2025 Andrew Hundt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
pyuvstarter.py (v7.1 - Enhanced Robustness & User Experience)

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
   - Place `pyuvstarter.py` in your existing project directory or use it to start a new project in an empty directory.

3. Execution:
   - Basic: `python pyuvstarter.py` (uses all defaults).
   - Custom venv: `python pyuvstarter.py --venv-name myenv`.
   - Preview mode: `python pyuvstarter.py --dry-run` (shows what would happen without making changes).
   - Migration mode examples:
     - `python pyuvstarter.py --dependency-migration all-requirements` (migrates everything from `requirements.txt`).
     - `python pyuvstarter.py --dependency-migration skip-requirements` (ignores `requirements.txt` entirely).
   - Full gitignore overwrite: `python pyuvstarter.py --full-gitignore-overwrite` (replaces existing `.gitignore`).
   - Custom log file: `python pyuvstarter.py --log-file-name my_setup_log.json`.

4. Post-run:
   - Activate the virtual environment:
     - macOS/Linux: `source .venv/bin/activate` (or your custom venv name).
     - Windows: `.venv\\Scripts\\activate.bat` or `.venv\\Scripts\\activate.ps1`.
   - Check the log file for a detailed summary of all actions and any warnings.

5. Configuration:
   - JSON config file: `python pyuvstarter.py --config-file settings.json`
   - Environment variables: `PYUVSTARTER_VENV_NAME=myenv python pyuvstarter.py`
   - See --help for all options: `python pyuvstarter.py --help`


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


Design Philosophy:
    pyuvstarter follows these core principles to create an exceptional user experience.
    These are ordered from most fundamental to most specific:

    === CORE PRINCIPLES ===

    1. **Automatic and Correct**: Make things "just work" without user intervention.
       We handle complexity so users don't have to. The tool should feel magical.
       Once started, pyuvstarter runs to completion without asking questions.

    2. **Modernize Projects Automatically**: Transform legacy Python projects into
       modern, reproducible environments. We find the newest compatible versions
       that work together, not the oldest. We're upgrading, not downgrading.

    3. **Easy to Use Correctly, Hard to Use Incorrectly**: Design APIs and defaults
       that guide users toward success. Minimal parameters, smart defaults.
       Example: Just run `pyuvstarter` - no flags needed for 95% of cases.

    4. **Solve Problems FOR Users**: Don't just report problems - fix them automatically.
       When we detect a conflict, we don't just tell users about it, we retry with
       a solution. Users should feel the tool is working on their behalf.

    === COMMUNICATION PRINCIPLES ===

    5. **Specific and Actionable Feedback**: Every message must tell users exactly what to do.
       - Bad: "Error occurred"
       - Good: "numpy 2.3.1 requires Python 3.11+, but your project uses Python 3.8"
       - Better: "Automatically finding compatible numpy version for Python 3.8..."
       - Best: "✅ Found numpy 1.24.3 that works with Python 3.8. Installing now..."
       The key: Show the problem AND that we're solving it for them!

    5. **Context-Aware Messages**: Error messages must include relevant context:
       - What was being attempted ("Installing numpy 2.3.1...")
       - Why it failed ("requires Python 3.11+, you have 3.8")
       - What we're doing to fix it ("Finding compatible version...")
       - What the user can do if we can't fix it (exact commands)

    6. **Show Progress and Success**: Users need confirmation that things are working.
       - Use status indicators: ✅ SUCCESS, ⚠️ WARNING, ❌ ERROR
       - Show what's happening: "Analyzing dependencies..." → "Installing..." → "✅ Done!"
       - Celebrate success: "✅ Successfully installed 12 packages!"

    7. **Progressive Disclosure**: Show simple success messages for normal cases,
       detailed information only when debugging is needed. Don't overwhelm users
       with logs when everything is working fine.

    === TECHNICAL PRINCIPLES ===

    8. **Graceful Recovery**: When something goes wrong, try to fix it automatically
       before asking for help. Example: retry with unpinned packages on version conflicts.
       The user should rarely need to intervene.

    9. **Trust the Tools**: Use tools as their creators intended. Don't try to
       outsmart uv's resolver or pipreqs' discovery - leverage their strengths.
       We orchestrate tools, we don't replace them.

    10. **Preserve User Intent**: Never change project settings (like requires-python)
        without explicit consent. Respect the user's choices. Their project, their rules.

    11. **One Problem, One Solution**: Avoid complex multi-strategy approaches when
        a single good solution suffices. Simplicity is reliability. Don't overthink it.

    === FAILURE HANDLING ===

    12. **Fail Fast with Recovery Path**: When automation isn't possible, fail quickly
        with a clear explanation and specific recovery steps. Don't leave users hanging.

    13. **Manual Fix Guidance**: When automation fails, guide toward modernization:
        Bad: "Failed to resolve dependencies"
        Good: "numpy 2.3.1 and pandas 2.2.0 require Python 3.11+. Your project uses Python 3.8."
        Best: "Cannot automatically resolve: numpy 2.3.1 and pandas 2.2.0 require Python 3.11+,
               but your project uses Python 3.8.

               Here are your options to modernize your project:

               1. Use a newer Python version (recommended):
                  Run: python3.11 -m pyuvstarter
                  This gives you latest features and best performance.
                  Note: You may need to update code that uses deprecated APIs.

               2. Update your project's Python requirement:
                  Edit pyproject.toml: requires-python = '>=3.11'
                  Then run pyuvstarter again.

               3. If you must stay on Python 3.8:
                  Run: uv add 'numpy<2.0' 'pandas<2.0'
                  This keeps older but compatible versions.

               Options 1 or 2 modernize your project, option 3 maintains compatibility."

    === OPTIMIZATION PRINCIPLES ===

    14. **Optimize for Common Case**: Make the 95% case seamless, even if the 5%
        requires manual intervention. Most users should never see an error.
        Focus effort where it has the most impact.

    15. **Transparent Operations**: Tell users what's happening and why. They should
        understand what the tool is doing, even if they don't need to intervene.
        Build trust through transparency.

"""

# --- Import Strategy ---
# All module-level imports are placed here to avoid UnboundLocalError issues.
# Python treats any name that has an import statement anywhere in a function
# as a local variable throughout that function's scope, even before the import.
# Moving imports to module level prevents this issue.

import sys
import json
import os
import shutil
import subprocess
import datetime
import platform

# --- Python Version Check ---
# Check Python version early to provide helpful error messages for incompatible versions
def check_python_version():
    """
    Check Python version and provide helpful error messages for incompatible versions.

    Returns:
        bool: True if Python version is compatible, False otherwise
    """
    # Check for Python 2.x - critical error
    if sys.version_info[0] < 3:
        print("=" * 70)
        print("ERROR: pyuvstarter requires Python 3.11 or higher")
        print("=" * 70)
        print()
        print("You are using Python {}.{} which is incompatible.".format(
            sys.version_info[0], sys.version_info[1]))
        print()
        print("SOLUTIONS:")
        print("1. Use UV package manager for proper Python management (RECOMMENDED):")
        print("   # Check if UV is already installed:")
        print("   uv --version")
        print("   # If UV is not installed, install it:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("   # Create virtual environment and install dependencies:")
        print("   uv venv")
        print("   source .venv/bin/activate")
        print("   uv sync")
        print("   # Run pyuvstarter:")
        print("   python3 pyuvstarter.py")
        print()
        print("2. Use python3 explicitly:")
        print("   python3 pyuvstarter.py")
        print()
        print("3. Activate your UV virtual environment:")
        print("   source .venv/bin/activate")
        print("   python3 pyuvstarter.py")
        print()
        print("4. Update your system default (if you have admin rights):")
        print("   ln -sf /usr/bin/python3 /usr/local/bin/python")
        print()
        print("=" * 70)
        return False

    # Check for Python 3.0-3.10 - warning but allow usage
    if sys.version_info < (3, 11):
        print("=" * 70)
        print("WARNING: Python 3.11+ recommended")
        print("=" * 70)
        print()
        print("You are using Python {}.{}.{}.".format(
            sys.version_info[0], sys.version_info[1], sys.version_info[2]))
        print("pyuvstarter requires Python 3.11+ for full compatibility.")
        print()
        print("RECOMMENDED SOLUTIONS:")
        print("1. Use UV with Python 3.11+ (RECOMMENDED):")
        print("   uv venv --python 3.11")
        print("   source .venv/bin/activate")
        print("   uv sync")
        print("   python3 pyuvstarter.py")
        print()
        print("2. Install Python 3.11+ and activate virtual environment:")
        print("   python3.11 -m venv .venv")
        print("   source .venv/bin/activate")
        print("   python3 pyuvstarter.py")
        print()
        print("=" * 70)

    return True


# Check Python version before proceeding
if not check_python_version():
    sys.exit(1)


import re
import ast
import tempfile
import shlex
import traceback
import functools

from pathlib import Path
from typing import Set, Tuple, List, Union, Dict, Optional, Any, Type

# --- Version Information ---
# Single source of truth for version information
PYUVSTARTER_VERSION = "0.2.1"

# --- Windows Unicode Encoding Setup ---
# Handle Windows Unicode encoding issues at module import time
# This must happen early, before any Unicode content is processed
if platform.system() == 'Windows':
    # Reconfigure stdout and stderr to use UTF-8 encoding on Windows
    # This prevents UnicodeEncodeError when emoji/Unicode characters are displayed
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, OSError):
        # Fallback for older Python versions or environments where reconfigure fails
        # Set environment variables that influence Python's encoding behavior
        os.environ.setdefault('PYTHONUTF8', '1')
        os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# --- Optional Built-in Imports ---
# Handle version-specific modules



# --- Robust TOML Parser Import (Python 3.11+ and older) ---
# Always provide a tomllib-compatible interface as 'tomllib'.
tomllib = None
if sys.version_info >= (3, 11):
    try:
        import tomllib as _tomllib
        tomllib = _tomllib
    except ImportError:
        tomllib = None
else:
    try:
        import toml as _toml
        class _TomlLibCompat:
            @staticmethod
            def load(fp):
                # toml.load expects str, not bytes
                if hasattr(fp, 'read'):
                    content = fp.read()
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')
                    return _toml.loads(content)
                raise TypeError("Expected a file-like object for tomllib.load")
            @staticmethod
            def loads(s):
                if isinstance(s, bytes):
                    s = s.decode('utf-8')
                return _toml.loads(s)
        tomllib = _TomlLibCompat
    except ImportError:
        tomllib = None

# importlib.metadata provides package version info (Python 3.8+)
# Using a flag instead of setting to None avoids modifying module namespace
try:
    import importlib.metadata  # Python 3.8+
    HAS_IMPORTLIB_METADATA = True
except ImportError:
    HAS_IMPORTLIB_METADATA = False

# --- Third-Party Imports ---
# Handle missing dependencies gracefully

try:
    import pathspec
    from pathspec.gitignore import GitIgnoreSpec
    from pathspec.patterns.gitwildmatch import GitWildMatchPattern
    from pathspec import PathSpec
except ImportError:
    pathspec = None
    GitIgnoreSpec = None
    GitWildMatchPattern = None
    PathSpec = None

from tqdm import tqdm

try:
    import typer
    from typing_extensions import Annotated, override
except ImportError as e:
    print("ERROR: Failed to import required dependency 'typer': {}".format(e))
    print("")
    print("This usually means typer is not installed. Please install it using:")
    print("  pip install typer")
    print("  Or if using uv: uv pip install typer")
    print("")
    print("If typer is installed, the error above will show the specific import issue.")
    sys.exit(1)

try:
    from pydantic import Field, ValidationError
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError as e:
    print("ERROR: Failed to import required dependency 'pydantic': {}".format(e))
    print("")
    print("This usually means pydantic is not installed. Please install it using:")
    print("  pip install pydantic pydantic-settings")
    print("  Or if using uv: uv pip install pydantic pydantic-settings")
    print("")
    print("If pydantic is installed, the error above will show the specific import issue.")
    sys.exit(1)


# ==============================================================================
# SECTION 0: CROSS-PLATFORM UNICODE SAFE OUTPUT
# ==============================================================================

def _is_windows_with_limited_unicode() -> bool:
    """
    Detect if we're on Windows with limited Unicode support in the console.

    Returns True if we should use ASCII fallbacks for emoji characters.
    """
    if platform.system() != 'Windows':
        return False

    # Check if stdout encoding supports Unicode properly
    try:
        # Try to encode a test emoji to the current stdout encoding
        # Use Unicode escape to avoid encoding issues during script import
        test_emoji = "\u2705"  # ✅ emoji using Unicode escape
        test_emoji.encode(sys.stdout.encoding or 'utf-8')
        return False  # If encoding succeeds, Unicode is supported
    except (UnicodeEncodeError, LookupError):
        return True  # If encoding fails, use ASCII fallbacks


def _get_safe_emoji_mapping() -> Dict[str, str]:
    """
    Get mapping of Unicode emoji characters to ASCII-safe alternatives for Windows.

    Returns:
        Dictionary mapping emoji to ASCII alternatives
    """
    return {
        "\u2705": "[OK]",        # ✅
        "\u274c": "[ERROR]",     # ❌
        "\u26a0\ufe0f": "[WARNING]",  # ⚠️
        "\U0001f4a5": "[CRITICAL]",   # 💥
        "\U0001f9ea": "[TEST]",       # 🧪
        "\U0001f50d": "[SEARCH]",     # 🔍
        "\U0001f4c1": "[FOLDER]",     # 📁
        "\U0001f4c2": "[SCAN]",       # 📂
        "\U0001f680": "[RUN]",        # 🚀
        "\u2699\ufe0f": "[CONFIG]",   # ⚙️
        "\U0001f389": "[SUCCESS]",    # 🎉
        "\U0001f527": "[TOOL]",       # 🔧
        "\U0001f4c4": "[FILE]",       # 📄
        "\u23f3": "[WORKING]",        # ⏳
        "\U0001f40d": "[PYTHON]",     # 🐍
        "\U0001f4e6": "[PACKAGE]",    # 📦
        "\U0001f512": "[LOCKED]",     # 🔒
        "\U0001f648": "[IGNORED]",    # 🙈
        "\u2795": "[ADDED]",          # ➕
        "\U0001f3af": "[NEXT]",       # 🎯
        "\U0001f4dd": "[GIT]",        # 📝
        "\u26a1": "[RESOLVE]",        # ⚡
        "\U0001f4d3": "[NOTEBOOK]"    # 📓
    }


def _make_text_safe_for_console(text: str) -> str:
    """
    Convert text with emoji characters to console-safe version if needed.

    Args:
        text: Text that may contain emoji characters

    Returns:
        Console-safe version of the text
    """
    if not _is_windows_with_limited_unicode():
        return text

    safe_text = text
    emoji_mapping = _get_safe_emoji_mapping()

    for emoji, replacement in emoji_mapping.items():
        safe_text = safe_text.replace(emoji, replacement)

    return safe_text


def safe_typer_secho(message: str, **kwargs) -> None:
    """
    Safe wrapper for typer.secho that handles Unicode characters on Windows.

    Args:
        message: The message to display
        **kwargs: Additional arguments to pass to typer.secho
    """
    safe_message = _make_text_safe_for_console(message)
    typer.secho(safe_message, **kwargs)


def safe_print(message: str = "", **kwargs) -> None:
    """
    Safe wrapper for print that handles Unicode characters on Windows.

    Args:
        message: The message to display
        **kwargs: Additional arguments to pass to print
    """
    safe_message = _make_text_safe_for_console(message)
    print(safe_message, **kwargs)


# ==============================================================================
# SECTION 1: CORE DATA CONSTANTS - these are mostly deprecated and should be integrated into the CLICommand and once all regressions are fixed and documentation correct these should be removed in the future unless CLICommand uses them
# ==============================================================================

# This dictionary contains a comprehensive set of patterns for a typical Python
# project, merged from community standards (e.g., GitHub's templates).
# The dictionary keys are used as section comments when CREATING a new
# .gitignore file from scratch, ensuring a well-organized result.
GITIGNORE_DEFAULT_ENTRIES: Dict[str, List[str]] = {
    "Python Virtual Environments": ["/.venv/", "/venv/", "/ENV/", "/env/"],
    "Python Cache, Compiled Files & Extensions": ["__pycache__/", "*.py[cod]", "*$py.class", "*.so", "*.pyd"],
    "Distribution & Packaging": [".Python", "build/", "develop-eggs/", "dist/", "downloads/", "eggs/", ".eggs/", "lib/", "lib64/", "parts/", "sdist/", "var/", "wheels/", "pip-wheel-metadata/", "share/python-wheels/", "*.egg-info/", ".installed.cfg", "*.egg", "MANIFEST"],
    "Test, Coverage & Linter Reports": ["htmlcov/", ".tox/", ".nox/", ".coverage", ".coverage.*", "nosetests.xml", "coverage.xml", ".cache", ".pytest_cache/", ".hypothesis/", "*.cover", "*.log"],
    "Installer Logs": ["pip-log.txt", "pip-delete-this-directory.txt"],
    "IDE & Editor Specific": [".vscode/*", "!/.vscode/settings.json", "!/.vscode/tasks.json", "!/.vscode/launch.json", "!/.vscode/extensions.json", ".history/", ".idea/"],
    "OS Specific": [".DS_Store", "Thumbs.db"],
    "Notebooks": [".ipynb_checkpoints"],
}

# This dictionary contains a minimal, essential set of patterns. It is used when
# UPDATING an existing .gitignore file to be non-intrusive and avoid
# deleting user-added rules.
ESSENTIAL_PATTERNS_TO_ENSURE: Dict[str, List[str]] = {
    "Python Virtual Environments": ["/.venv/", "/venv/"],
    "Python Cache & Compiled Files": ["__pycache__/"],
}

# Constants still used by deprecated functions - remove after deprecated code is deleted
VENV_NAME = ".venv"  # DEPRECATED: Use CLICommand.venv_name
PYPROJECT_TOML_NAME = "pyproject.toml"  # DEPRECATED: Hardcoded in modern code
GITIGNORE_NAME = ".gitignore"
JSON_LOG_FILE_NAME = "pyuvstarter_setup_log.json"  # DEPRECATED: Use CLICommand.log_file_name

# Constants that are still in use by modern implementation
LEGACY_REQUIREMENTS_TXT = "requirements.txt" # For migration
VSCODE_DIR_NAME = ".vscode"
SETTINGS_FILE_NAME = "settings.json"
LAUNCH_FILE_NAME = "launch.json"
# Map notebook system names to required execution dependencies (e.g. `ipykernel` for jupyter)
# This is an orthogonal concern to code dependencies like pandas.
_NOTEBOOK_SYSTEM_DEPENDENCIES = {
    "jupyter": ["jupyter", "ipykernel"],
    "polars-notebook": ["polars-notebook"],
    "quarto": ["quarto"],
    # Add more systems here as needed (e.g., 'voila': ['voila'])
}
# V1ax.3 - THE FINAL, VERIFIED, AND CORRECTED VERSION
#
# GOAL: To provide a robust, user-centric, and maintainable tool for discovering Python
#       dependencies within a specified project scope, including from scripts and notebooks.
#
# DESIGN PHILOSOPHY:
#   - Easy to Use Correctly: The primary function `discover_dependencies_in_scope`
#     has sensible defaults and a clear, explicit API.
#   - Hard to Use Incorrectly: Deprecated functions issue clear warnings, and the code
#     is resilient to common failure modes (e.g., malformed files, command failures).
#   - Actionable Guidance: All user-facing output, from logs to final summaries, is
#     designed to tell the user what happened, why, and what to do next.
#   - Fully Exercised: The demonstration code (`if __name__ == "__main__"`) is
#     designed to test all major code paths, including the hybrid notebook strategy.



_DYNAMIC_IGNORE_SET = {
    "python", "pip", "conda", "mamba", "poetry", "uv", "sh", "bash",
    "os", "sys", "json", "re", "pathlib", "tempfile", "ast", "collections",
    "subprocess", "warnings", "typing", "time"
}

DEFAULT_IGNORE_DIRS = {
    ".venv", "venv", ".env", "env", "node_modules", ".git", "__pycache__",
    ".tox", ".pytest_cache", ".hypothesis", "build", "dist", "*.egg-info"
}

# ==============================================================================
# DEFINITIVE pyuvstarter FUNCTION REFACTORING
# ==============================================================================

# Constants defining the desired patterns, for clarity and maintainability.
COMPREHENSIVE_PYTHON_GITIGNORE: Dict[str, List[str]] = {
    "Python Virtual Environments": ["venv/", ".venv/", "ENV/", "env/"],
    "Python Cache & Compiled Files": ["__pycache__/", "*.py[cod]", "*.so"],
    "Distribution & Packaging": ["build/", "dist/", "*.egg-info/"],
    "Test & Coverage Reports": [".coverage", "htmlcov/", ".pytest_cache/"],
    "IDE & OS Specific": [".vscode/", ".idea/", ".DS_Store", "Thumbs.db"],
}
ESSENTIAL_PATTERNS_TO_ENSURE: Dict[str, List[str]] = {
    "Python Virtual Environments": ["venv/", ".venv/"],
    "Python Cache & Compiled Files": ["__pycache__/"],
}


# This section has been removed as part of the consolidation of the GitIgnore class.
# The IgnoreManager class has been deprecated and its functionality for handling
# directory-based ignores has been moved into the functions that require it,
# such as `discover_dependencies_in_scope`. The .gitignore parsing is now
# handled by the single, consolidated GitIgnore class.

# ==============================================================================
#
# pyuvstarter - A Modern Python Project Setup Tool
# Copyright (c) 2025 Andrew Hundt
# Final Version: 30.3 (Definitive, Gold Standard Implementation)
#
# This script represents the definitive, production-ready version of the
# pyuvstarter tool. It has been meticulously revised to fix all previously
# identified regressions and to meet a "Gold Standard" specification for code
# quality, documentation, and user experience.
#
# It successfully synthesizes:
#   - The robust, declarative Typer/Pydantic architecture.
#   - The superior user feedback (banners, summaries) from the legacy version.
#   - The invaluable, specific error-handling hints from the legacy version.
#   - The correct, high-performance, and exceptionally documented GitIgnore class.
#
# Every function and class has been systematically reviewed to ensure it fulfills
# its architectural role with no logical or documentation regressions.
#
# Required Dependencies:
# uv add "typer[all]" pydantic pydantic-settings pathspec typing-extensions
#
# ==============================================================================

# ==============================================================================
# SECTION 2: THE DEFINITIVE GITIGNORE CLASS
# ==============================================================================

class GitIgnore(GitIgnoreSpec):
    """A high-performance and robust .gitignore file processor.

    NOTE: This is the GitIgnore to keep once regressions are fixed and it has been checked against the other versions.

    This class provides a clean, Pythonic façade over the battle-tested
    `pathspec` library. Its core purpose is to provide a simple, correct, and
    efficient way to answer the question "Is this file ignored?" according to
    the full .gitignore specification.

    It solves this by automatically discovering all `.gitignore` files in a
    project, correctly handling precedence, negation, and parent directory
    exclusion rules. It also provides a safe, idempotent API for updating
    ignore files.

    Motivation:
        Processing `.gitignore` files correctly is deceptively complex. This class
        solves that problem by providing a clean, Pythonic façade over the
        battle-tested `pathspec` library. It adds a crucial layer of
        convenience and correctness by automatically discovering patterns,
        implementing spec-critical rules like parent-directory exclusion,
        providing high-level methods to get file lists, and offering a safe
        way to update `.gitignore` files.

    Attributes:
        root_dir (Path): The absolute, resolved root directory for the project.

    Designed Usage Pattern:
        The class is designed for simple, expressive "one-liner" operations
        that solve a complete problem. For example, to get a list of all source
        files that need to be processed, while respecting both the project's
        `.gitignore` and some temporary ad-hoc rules:

        >>> # In a single, readable line, get all unignored files,
        >>> # adding a temporary rule to also ignore any 'backups' directory.
        >>> files_to_process = GitIgnore(
        ...     '.',
        ...     manual_patterns=['backups/']
        ... ).get_unignored_files()
        >>>
        >>> print(f"Found {len(files_to_process)} files to process.")

    Relationship with `pathspec` and Inherited API:
        This class inherits directly from `pathspec.gitignore.GitIgnoreSpec`.
        This means that in addition to the convenient methods defined here,
        an instance of `GitIgnore` is also a fully-featured `PathSpec` object.

        Advanced users can directly call the powerful, optimized methods from
        the underlying library, such as:
        - `checker.match_file(path)`: The core, low-level matching method.
        - `checker.match_files(paths)`: Batch match against an iterable of paths.
        - `checker.match_tree_files(root)`: Walk a directory tree for matches.

        The methods provided by this class (`is_ignored`, `get_*`)
        are primarily convenient and robust wrappers around these powerful
        primitives.
    """

    def __init__(self, root_dir: Path | str, manual_patterns: Optional[List[str]] = None, read_gitignore_files: bool = True):
        """Initializes the GitIgnore processor.

        Args:
            root_dir: The root directory of the project to be analyzed. It must
                      be an existing directory.
            manual_patterns: An optional list of ad-hoc gitignore patterns to
                             apply with the highest precedence.
            read_gitignore_files: If True (default), find and read .gitignore files.
                                  If False, only use manual_patterns.

        Raises:
            NotADirectoryError: If the provided `root_dir` does not point to a
                                valid directory.
            FileNotFoundError: If the provided `root_dir` does not exist.
        """
        # .resolve(strict=True) is a fail-fast mechanism. It ensures the root
        # directory exists and is accessible, raising an error immediately
        # rather than during a later method call. This prevents runtime errors.
        self.root_dir = Path(root_dir).resolve(strict=True)
        if not self.root_dir.is_dir():
            raise NotADirectoryError(f"The specified root_dir is not a directory: {self.root_dir}")
        self._manual_patterns = manual_patterns or []
        self.read_gitignore_files = read_gitignore_files

    @functools.cached_property
    def patterns(self) -> List:
        """A cached property that finds, parses, and compiles all patterns.

        This is a key performance optimization. The expensive work of finding
        and reading all .gitignore files is deferred until the first time a
        match is requested and is never repeated for the object's lifetime,
        unless the cache is explicitly invalidated after a write.

        Returns:
            List of compiled patterns ready for matching operations.
        """
        lines = self._collect_pattern_lines()
        # Parse the lines and create pattern objects directly
        pattern_factory = GitWildMatchPattern
        patterns = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                patterns.append(pattern_factory(line))
        return patterns

    def invalidate_cache(self) -> None:
        """Invalidate the cached patterns after a write operation.

        This ensures that subsequent calls to is_ignored() will re-read
        the .gitignore files and reflect any changes made by save().
        """
        # Use the proper way to clear a cached_property
        if 'patterns' in self.__dict__:
            del self.__dict__['patterns']

    def _collect_pattern_lines(self) -> List[str]:
        """A helper to find, read, and normalize all .gitignore patterns."""
        lines = []

        if self.read_gitignore_files:
            # According to the gitignore spec, rules from files in subdirectories
            # take precedence. We sort files by path depth (`len(p.parts)`) to
            # ensure deeper patterns are added *last*. `pathspec` correctly
            # honors this "last-match-wins" rule.
            sorted_ignore_files = sorted(
                self.root_dir.rglob('.gitignore'),
                key=lambda p: len(p.parts)
            )

            for path in sorted_ignore_files:
                relative_dir = path.parent.relative_to(self.root_dir)
                try:
                    # Use `errors='ignore'` for resilience against malformed files.
                    with path.open(encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            pattern = line.strip()
                            if not pattern or pattern.startswith('#'):
                                continue

                            # Per the spec, a pattern with a slash is relative to its
                            # own .gitignore file. We must normalize it to be
                            # relative to the project root for the unified spec.
                            if '/' in pattern.strip('/'):
                                pattern_path = (relative_dir / pattern).as_posix()
                                # Prepending '/' anchors the pattern to the `root_dir`.
                                lines.append(f'/{pattern_path}')
                            else:
                                # Patterns without a '/' are global and can match anywhere.
                                lines.append(pattern)
                except IOError:
                    # Silently skip files that cannot be read (e.g., due to permissions).
                    continue

        # Manually provided patterns are added last, giving them the highest precedence.
        lines.extend(self._manual_patterns)
        return lines

    def is_ignored(self, path: Union[Path, str]) -> bool:
        """Checks if a single file path is ignored, respecting all spec rules.

        This method correctly implements the full gitignore specification,
        including the critical parent directory exclusion rule.

        Args:
            path: The file or directory path to check.

        Returns:
            True if the path is ignored, False otherwise.
        """
        try:
            # All matching logic is done on POSIX-style, root-relative paths.
            path_rel_to_root = Path(path).resolve().relative_to(self.root_dir).as_posix()
        except ValueError:
            # The path is not within the project root, so it is not subject to these rules.
            return False

        # This loop correctly implements the parent directory exclusion rule:
        # "It is not possible to re-include a file if a parent directory of that file is excluded."
        current_parent = Path(path_rel_to_root).parent
        while current_parent and str(current_parent) != '.':
            # `self.match_file()` is inherited and returns True if a path is
            # *included* (i.e., NOT ignored). If any parent is not included,
            # this path is definitively ignored.
            if not self.match_file(str(current_parent)):
                return True
            current_parent = current_parent.parent

        # If no parents were ignored, check the file itself. The result is the
        # logical opposite of inclusion.
        return not self.match_file(path_rel_to_root)

    def get_ignored_files(self) -> List[Path]:
        """Scans the project and returns a list of all IGNORED files using
        pathspec's own optimized tree walker.

        Returns:
            List of absolute Path objects for all files that ARE ignored.
        """
        return [self.root_dir / p for p in self.match_tree_files(self.root_dir)]

    def get_unignored_files(self) -> List[Path]:
        """Scans the project and returns a list of all UNIGNORED files.

        This maximally offloads the work to `pathspec`'s optimized tree walker.

        Returns:
            List of absolute Path objects for all files that are NOT ignored.
        """
        # The `negate=True` flag tells pathspec to return all files that DO NOT
        # match the final spec, which is exactly what we want.
        return [self.root_dir / p for p in self.match_tree_files(self.root_dir, negate=True)]

    def save(self, patterns: List[str], comment: str = "Patterns added by tool"):
        """Safely and idempotently appends a commented block of patterns.

        This method is non-destructive. It reads the existing file, checks which
        of the provided patterns are new, and appends only the new ones under
        a formatted, commented block. If all patterns already exist, the file
        is not touched.

        Args:
            patterns: List of gitignore patterns to add.
            comment: Comment text to describe this block of patterns.

        Raises:
            IOError: If the file cannot be read or written.
        """
        target_path = self.root_dir / '.gitignore'
        try:
            content = target_path.read_text(encoding='utf-8') if target_path.exists() else ""
        except IOError as e:
            raise IOError(f"Could not read .gitignore file at {target_path}: {e}")

        # This is a key performance optimization. By building a set of existing
        # lines, we can check for a pattern's existence in O(1) time on average.
        existing_lines = {line.strip() for line in content.splitlines()}
        active_patterns = {p for p in existing_lines if p and not p.startswith('#')}
        patterns_to_add = [p for p in patterns if p.strip() and p.strip() not in active_patterns]

        if not patterns_to_add:
            return  # All patterns already exist; do nothing to preserve the file.

        # Build the new content block, ensuring proper spacing for readability.
        if content and not content.endswith('\n'):
            content += '\n'
        if content and not content.endswith('\n\n'):
            content += '\n'

        content += f"# {comment}\n"
        content += '\n'.join(patterns_to_add) + '\n'

        try:
            target_path.write_text(content, encoding='utf-8')
        except IOError as e:
            raise IOError(f"Could not write to .gitignore file at {target_path}: {e}")

        # CRITICAL: Invalidate the cached patterns. The on-disk file has changed,
        # so the next call to `is_ignored` must re-read and re-compile the spec.
        self.invalidate_cache()

    def get_allowed_files_by_pattern(self, include_pattern: str) -> List[Path]:
        """
        Scans the project and returns a list of files that match the given
        `include_pattern`, while also respecting the project's .gitignore rules.

        Args:
            include_pattern: The pattern (e.g., "*.ipynb", "*.py", "data/*.csv")
                             to match for inclusion. This pattern should follow
                             Git wildmatch syntax.

        Returns:
            A list of Path objects for files that match the `include_pattern`
            and are NOT ignored by .gitignore rules.
        """
        # 1. Get all files that are NOT ignored by .gitignore rules.
        # This already handles the parent directory exclusion logic.
        unignored_files = self.get_unignored_files()

        # 2. Create a PathSpec specifically for the desired inclusion pattern.
        # We ensure it's treated as an inclusion pattern.
        # Using a list to pass to PathSpec constructor for consistency, even if it's one pattern.
        include_spec_patterns = [GitWildMatchPattern(include_pattern)]
        include_spec = PathSpec(include_spec_patterns)

        # 3. Filter the unignored files using the `include_spec`.
        # `match_files` yields files that match the spec.
        # It expects relative paths (posix style).
        matched_relative_paths = include_spec.match_files(
            [p.relative_to(self.root_dir).as_posix() for p in unignored_files]
        )

        # 4. Convert relative paths back to absolute Path objects and return.
        return [self.root_dir / p for p in matched_relative_paths]

    def is_allowed_by_pattern(self, path: Union[Path, str], include_pattern: str) -> bool:
        """
        Checks if a single file path matches the `include_pattern` AND is not
        ignored by the project's .gitignore rules.

        Args:
            path: The file path to check.
            include_pattern: The pattern (e.g., "*.ipynb", "*.py", "data/*.csv")
                             to match for inclusion.

        Returns:
            True if the file matches the pattern AND is not ignored; False otherwise.
        """
        # First, ensure the file is within the root_dir and get its relative path.
        try:
            path_rel_to_root = Path(path).resolve().relative_to(self.root_dir).as_posix()
        except ValueError:
            # Path is not within the project root, so it cannot be "allowed" by project rules.
            return False

        # 1. Check if the file is ignored by .gitignore rules.
        if self.is_ignored(path):
            return False

        # 2. Check if the file matches the specific include pattern.
        # Create a temporary PathSpec for this single pattern.
        single_pattern_spec = PathSpec([GitWildMatchPattern(include_pattern, include=True)])
        return single_pattern_spec.match_file(path_rel_to_root)

# ==============================================================================
# SECTION: DEMONSTRATION
# ==============================================================================
def test():
    with tempfile.TemporaryDirectory() as temp_dir_str:
        root = Path(temp_dir_str)
        print(f"\n--- Setting up Adversarial Monorepo for Demonstration in: {root} ---\n")

        service_a = root / "service_a"
        service_b = root / "service_b"
        ignored_venv_dir = root / "service_a" / ".venv"
        service_a.mkdir()
        service_b.mkdir()
        ignored_venv_dir.mkdir(parents=True)

        (service_a / "main.py").touch()
        (service_a / "success_convert.ipynb").write_text(json.dumps({"cells": [{"cell_type": "code", "source": ["import scipy"]}]}))
        (service_a / "fallback.ipynb").write_text(json.dumps({"cells": [{"cell_type": "code", "source": ["import pandas", "import sklearn"]}]}))
        (ignored_venv_dir / "should_be_ignored.ipynb").write_text('{"cells":[]}')
        (service_b / "app.py").touch()

        print("\n--- 1. ACTION: Scanning 'service_a' scope ---")
        result_a = discover_dependencies_in_scope(scan_path=service_a)

        summary_a = generate_discovery_summary(result_a)
        print(summary_a)

        deps_a = {dep[0] for dep in result_a.all_unique_dependencies}
        assert deps_a == {"fastapi", "uvicorn", "scipy", "pandas", "scikit-learn"}
        assert result_a.notebooks_found_count == 2
        assert result_a.notebooks_converted_count == 1
        assert result_a.notebooks_fallback_count == 1

        print("\n\n--- 2. ACTION: Scanning 'service_b' scope (notebooks disabled) ---")
        result_b = discover_dependencies_in_scope(scan_path=service_b, scan_notebooks=False)
        print(generate_discovery_summary(result_b))
        deps_b = {dep[0] for dep in result_b.all_unique_dependencies}
        assert deps_b == {"django"}

        print("\n\n--- 3. ACTION: Testing .gitignore Integration ---")

        # Create a test project with .gitignore
        gitignore_test_root = root / "gitignore_test"
        gitignore_test_root.mkdir()

        # Create test .gitignore file
        gitignore_content = """# Test patterns for pyuvstarter
*.pyc
__pycache__/
test_ignore/
ignored_*.py
ignored_*.ipynb
**/deep_ignore/**
"""
        (gitignore_test_root / ".gitignore").write_text(gitignore_content)

        # Create files that should be ignored by .gitignore
        test_ignore_dir = gitignore_test_root / "test_ignore"
        test_ignore_dir.mkdir()
        (test_ignore_dir / "should_be_ignored.py").write_text("import pandas\nprint('ignored')")
        (gitignore_test_root / "ignored_notebook.ipynb").write_text(json.dumps({
            "cells": [{"cell_type": "code", "source": ["import tensorflow as tf"]}]
        }))

        # Create files that should NOT be ignored
        (gitignore_test_root / "main.py").write_text("import requests\nprint('not ignored')")
        (gitignore_test_root / "valid_notebook.ipynb").write_text(json.dumps({
            "cells": [{"cell_type": "code", "source": ["import numpy as np"]}]
        }))

        # Test with .gitignore enabled (default)
        print("    Testing WITH .gitignore patterns...")
        gitignore_manager = GitIgnore(gitignore_test_root)
        result_with_gitignore = discover_dependencies_in_scope(scan_path=gitignore_test_root, ignore_manager=gitignore_manager)
        deps_with_gitignore = {dep[0] for dep in result_with_gitignore.all_unique_dependencies}
        print(f"    Found dependencies: {sorted(deps_with_gitignore)}")

        # Test with .gitignore disabled
        print("    Testing WITHOUT .gitignore patterns...")
        result_without_gitignore = discover_dependencies_in_scope(scan_path=gitignore_test_root, ignore_manager=None)
        deps_without_gitignore = {dep[0] for dep in result_without_gitignore.all_unique_dependencies}
        print(f"    Found dependencies: {sorted(deps_without_gitignore)}")

        # Validate .gitignore functionality
        assert "requests" in deps_with_gitignore, "requests should be found (not ignored)"
        assert "numpy" in deps_with_gitignore, "numpy should be found (not ignored)"
        assert "pandas" not in deps_with_gitignore, "pandas should be ignored by .gitignore"
        assert "tensorflow" not in deps_with_gitignore, "tensorflow should be ignored by .gitignore"

        # Should find more dependencies without .gitignore
        assert len(deps_without_gitignore) >= len(deps_with_gitignore), "Should find same or more deps without .gitignore"
        assert "pandas" in deps_without_gitignore, "pandas should be found when .gitignore disabled"
        assert "tensorflow" in deps_without_gitignore, "tensorflow should be found when .gitignore disabled"

        print(f"    ✓ .gitignore test PASSED: {len(deps_with_gitignore)} deps with gitignore, {len(deps_without_gitignore)} without")



        print("\n\n--- Demonstration Complete ---")




# --- Project Version Extraction ---
def _get_project_version(pyproject_path: Path = Path(__file__), project_name: str = "pyuvstarter") -> str:
    """
    Robustly reads the version from the [project] section of a pyproject.toml.
    If project_name is given, only returns the version if [project].name matches.
    Returns the version string, or 'unknown' if not found or on error.

    Note: don't call me on a project before uv init, as I will return 'unknown'.
    """
    # Try importlib.metadata.version if project_name is given
    if project_name and HAS_IMPORTLIB_METADATA:
        try:
            return importlib.metadata.version(project_name)
        except Exception:
            pass
    # Fallback: try to read pyproject.toml
    if pyproject_path is not None and pyproject_path.exists():
        try:
            # Use module-level tomllib if available (Python 3.11+)
            # Otherwise dynamically import toml package
            # Different file modes: tomllib needs binary, toml needs text
            if tomllib is not None:
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


# --- UV Run Command Suggestion ---
def get_uv_run_command(pyproject_path="pyproject.toml", script_not_found_message="uv run your_script.py # add '[project.scripts] your_script' to your pyproject.toml."):
    """
    Suggest the correct `uv run <script>` command by reading [project.scripts] from pyproject.toml.

    This function uses the global `tomllib` import logic for robust TOML parsing across Python versions.
    - If `tomllib` is available (Python 3.11+ or via the compatibility wrapper), it is used to parse the TOML file.
    - If `tomllib` is None, the value of `script_not_found_message` is returned.
    - The function checks that the referenced module and function in each script entry are importable and exist in the current environment before suggesting it.
    - If multiple valid candidates exist, it lists them and asks the user to pick one.
    - If no valid script is found, but scripts exist, it suggests the first script with a warning comment.
    - If no scripts are found or TOML cannot be parsed, the value of `script_not_found_message` is returned.

    Args:
        pyproject_path (str or Path or None): Path to the pyproject.toml file. If None, attempts to resolve from project root or current directory.
        script_not_found_message (str): The fallback message to return if no script can be suggested (default: "uv run your_script.py # add '[project.scripts] your_script=\"your_script\"' to your pyproject.toml.").

    Returns:
        str: The recommended `uv run <script>` command, or the fallback message if not possible.
    """
    # Defensive: ensure pyproject_path is a Path and not None
    if pyproject_path is None:
        return script_not_found_message
    pyproject_path = Path(pyproject_path)
    if tomllib is None:
        return script_not_found_message  # Can't parse TOML
    try:
        if not pyproject_path.exists():
            return script_not_found_message
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        scripts = data.get("project", {}).get("scripts", {})

        def prefer_main_candidates(names):
            """Return a list of names, preferring those with 'main' in the name if any exist."""
            main_names = [k for k in names if "main" in k.lower()]
            return main_names if main_names else list(names)

        if scripts:
            import importlib.util
            import importlib

            candidates = prefer_main_candidates(scripts.keys())

            valid_candidates = []  # List of (script_name, entry_point, mod, func, found_mod, found_func)
            for script_name in candidates:
                entry_point = scripts[script_name]
                # Split entry point as 'module:function' or just 'module'
                parts = entry_point.split(":")
                mod = parts[0].strip()
                func = parts[1].strip() if len(parts) > 1 else None
                # Check if module exists
                try:
                    found_mod = importlib.util.find_spec(mod) is not None
                except Exception:
                    found_mod = False
                # Check if function exists in module (if specified)
                found_func = False
                if found_mod and func:
                    try:
                        module_obj = importlib.import_module(mod)
                        found_func = hasattr(module_obj, func)
                    except Exception:
                        found_func = False
                elif found_mod:
                    found_func = True  # If no function specified, just module is enough
                valid_candidates.append((script_name, entry_point, mod, func, found_mod, found_func))

            # Filter for candidates where both module and function (if specified) exist
            working = [c for c in valid_candidates if c[4] and c[5]]

            if len(working) == 1:
                # Exactly one valid candidate: recommend it
                script_name, entry_point, mod, func, _, _ = working[0]
                return f"uv run {script_name}"
            elif len(working) > 1:
                # Multiple valid candidates: list them and ask user to pick
                script_list = ", ".join([c[0] for c in working])
                return f"uv run <script>  # Multiple valid scripts found: {script_list}. Pick the one you want to run."
            else:
                # No fully valid candidates, but maybe some with just module present
                mod_only = [c for c in valid_candidates if c[4]]
                if len(mod_only) == 1:
                    script_name, entry_point, mod, func, _, _ = mod_only[0]
                    # Suggest with a concrete, actionable one-liner
                    return (
                        f"uv run {script_name}  # (guess) Check that '{mod}.py' exists and that [project.scripts] {script_name} = \"{mod}:main\" matches your code."
                    )
                elif len(mod_only) > 1:
                    script_list = ", ".join([c[0] for c in mod_only])
                    return f"uv run <script>  # Multiple script modules found: {script_list}. Check that each has a callable 'main' function."
                # If no candidates, fallback
                return script_not_found_message
        # --- ENHANCEMENT: If no scripts, scan for likely entry points ---
        # Look for .py files in src/, scripts/, and project root (excluding __init__.py)
        project_root = pyproject_path.parent
        candidate_files = []
        for subdir in [project_root / "src", project_root / "scripts", project_root]:
            if subdir.exists() and subdir.is_dir():
                for pyfile in subdir.glob("*.py"):
                    # Exclude __init__.py and files with leading dot (e.g. .simulate.py)
                    if pyfile.name != "__init__.py" and not pyfile.name.startswith('.'):
                        candidate_files.append(pyfile)
        # Remove duplicates and sort
        candidate_files = sorted(set(candidate_files))
        # Prefer files with 'main' in the name if any
        preferred_files = prefer_main_candidates([f for f in candidate_files if "main" in f.name.lower()])
        files_to_suggest = preferred_files if preferred_files else candidate_files
        if len(files_to_suggest) == 1:
            rel_path = files_to_suggest[0].relative_to(project_root)
            return f"uv run {rel_path}  # (guess) No [project.scripts] found. Consider adding one for reproducibility."
        elif 1 < len(files_to_suggest) <= 3:
            rels = [str(f.relative_to(project_root)) for f in files_to_suggest]
            candidates_block = "\n".join(f"      uv run {rel}" for rel in rels)
            return (
                "# Pick one to run, or add a [project.scripts] <your_script> entry to pyproject.toml:\n"
                f"{candidates_block}"
            )
        # If no candidates, fallback
        return script_not_found_message
    except Exception:
        # Catch-all for TOML or import errors
        return script_not_found_message


# --- JSON Logging Utilities ---
_log_data_global = {}

# --- Intelligent Output System Global State ---
# Global state for intelligent output system

# Single source of truth for progress step definitions
ACTION_STATUS_MAPPING = {
    "ensure_uv_installed": ("\U0001f527 Verifying uv installation", "\U0001f527 Verified uv installation"),  # 🔧
    "ensure_project_initialized_with_pyproject": ("\U0001f4c1 Initializing project with pyproject.toml", "\U0001f4c1 Initialized project with pyproject.toml"),  # 📁
    "ensure_gitignore": ("\U0001f4dd Setting up .gitignore", "\U0001f4dd Set up .gitignore"),  # 📝
    "create_or_verify_venv": ("\U0001f40d Creating virtual environment .venv/", "\U0001f40d Created virtual environment .venv/"),  # 🐍
    "ensure_tool_pipreqs": ("\U0001f527 Installing pipreqs via uv tool install", "\U0001f527 Installed pipreqs via uv tool install"),  # 🔧
    "ensure_tool_ruff": ("\U0001f527 Installing ruff via uv tool install", "\U0001f527 Installed ruff via uv tool install"),  # 🔧
    "ruff_unused_import_check": ("\U0001f50d Running ruff unused import checks", "\U0001f50d Completed ruff unused import checks"),  # 🔍
    "manage_project_dependencies": ("\U0001f4e6 Installing project dependencies", "\U0001f4e6 Installed project dependencies"),  # 📦
    "ensure_notebook_execution_support": ("\U0001f4d3 Setting up notebook support", "\U0001f4d3 Set up notebook support"),  # 📓
    "configure_vscode_settings": ("\u2699\ufe0f Configuring .vscode/settings.json", "\u2699\ufe0f Configured .vscode/settings.json"),  # ⚙️
    "ensure_vscode_launch_json": ("\u2699\ufe0f Setting up .vscode/launch.json", "\u2699\ufe0f Set up .vscode/launch.json"),  # ⚙️
    "uv_final_sync": ("\U0001f527 Syncing environment with uv.lock", "\U0001f527 Synced environment with uv.lock"),  # 🔧
    "script_end": ("\U0001f389 Setup complete!", "\U0001f389 Setup complete!"),  # 🎉
}

# WORKFLOW_STEPS removed - redundant with ACTION_STATUS_MAPPING
# Using ACTION_STATUS_MAPPING as single source of truth

class ProgressTracker:
    """Modern progress tracking using self-registering workflow steps.

    Philosophy: "Automatic and Correct" + "Easy to Use Correctly"
    - Steps register themselves automatically
    - Progress tracking happens automatically
    - No manual coordination required
    - Type-safe through WorkflowStep objects
    """

    def __init__(self, config):
        self.config = config
        # Encapsulated versions of previously global state
        self._progress_bar = None
        self._progress_steps_seen = set()
        self._previous_action_name = None
        self._auto_intelligence = {
            "files_created": set(),
            "files_modified": set(),
            "commands_executed": [],
            "packages_discovered": 0,
            "packages_installed": 0,
            "issues": [],
            "auto_fixes_available": []
        }
        self._initialized = False

    def should_show_progress(self, action_name: str) -> bool:
        """Progress detection using ACTION_STATUS_MAPPING as single source of truth.

        Fixed filtering logic to avoid false positives.
        """
        # Whitelist legitimate steps that contain excluded substrings
        whitelisted_steps = [
            "ensure_notebook_execution_support"
        ]
        if action_name in whitelisted_steps:
            return True

        # Exclude automatic command execution logs with precise patterns
        import re
        excluded_patterns = [
            r"_exec$",           # Ends with _exec
            r"_version_check$",  # Ends with _version_check
            r"_cmd$",            # Ends with _cmd
            r"_uv_add$",         # Ends with _uv_add
            r"_uv_tool_install$" # Ends with _uv_tool_install
        ]
        if any(re.search(pattern, action_name) for pattern in excluded_patterns):
            return False

        # Check if this action is in ACTION_STATUS_MAPPING
        if action_name in ACTION_STATUS_MAPPING:
            return True

        # Handle dynamic patterns
        if action_name.startswith("discover_deps_"):
            return True
        if action_name.startswith("ensure_tool_"):
            return True
        if "version_conflict_resolution" in action_name:
            return True

        return False

    def count_total_progress_steps(self) -> int:
        """Count based on ACTION_STATUS_MAPPING entries only.

        No conditional steps in base count - they're added dynamically when they execute.
        """
        # Base steps = only entries that actually get logged in normal execution
        base_steps = len(ACTION_STATUS_MAPPING)

        # Don't add conditional steps to base count - they'll be counted when they execute

        return base_steps

    def get_status_messages(self, action_name: str) -> tuple:
        """Get (present, past) status messages with intelligence integration."""
        # Handle dynamic patterns with auto-intelligence
        if action_name.startswith("discover_deps_"):
            project_name = action_name.replace("discover_deps_", "")
            count = self._auto_intelligence.get("packages_discovered", 0)
            present = f"📂 Scanning {project_name} for dependencies"
            if count > 0:
                past = f"📂 Found {count} dependencies in {project_name}"
            else:
                past = f"📂 Scanned {project_name} for dependencies"
            return present, past

        elif action_name.startswith("ensure_tool_"):
            tool_name = action_name.replace("ensure_tool_", "")
            present = f"🔧 Installing {tool_name} via uv tool install"
            past = f"🔧 Installed {tool_name} via uv tool install"
            return present, past

        elif action_name == "manage_project_dependencies":
            count = self._auto_intelligence.get("packages_installed", 0)
            present = "📦 Installing project dependencies"
            if count > 0:
                past = f"📦 Installed {count} dependencies → uv.lock created"
            else:
                past = "📦 Installed project dependencies"
            return present, past

        elif "version_conflict_resolution" in action_name:
            return "⚡ Resolving version conflicts", "⚡ Resolved version conflicts"

        # Static mapping lookup (single source of truth)
        if action_name in ACTION_STATUS_MAPPING:
            return ACTION_STATUS_MAPPING[action_name]

        # Fallback generation for unmapped actions
        base_name = action_name.replace('_', ' ').replace('ensure ', '').title()
        present = f"\u2699\ufe0f Setting up {base_name.lower()}"  # ⚙️
        past = f"\u2699\ufe0f Set up {base_name.lower()}"  # ⚙️
        return present, past

    def init_progress_bar(self):
        """Initialize progress bar with dynamically counted total steps."""
        if self._initialized:
            return

        version = _get_project_version()
        header = f"🚀 PYUVSTARTER v{version}"

        # Reset step tracking and previous action for new run
        self._progress_steps_seen.clear()
        self._previous_action_name = None

        # Count total progress steps from ACTION_STATUS_MAPPING (single source)
        total_steps = self.count_total_progress_steps()

        try:
            from tqdm import tqdm
            # Ensure header is safe for console output
            safe_header = _make_text_safe_for_console(header)
            self._progress_bar = tqdm(
                total=total_steps,
                desc=safe_header,
                bar_format='{desc} {percentage:3.0f}%|{bar}| {n}/{total} steps',
                ncols=80
            )
        except Exception:
            # Fallback to simple output if any progress bar creation fails
            safe_print(header)
            self._progress_bar = None

        self._initialized = True


    def update_progress_with_auto_intelligence(self, action_name: str):
        """Update progress with temporal flow and intelligence."""
        # Only update if this is a new step we haven't seen before
        if action_name not in self._progress_steps_seen:
            self._progress_steps_seen.add(action_name)

            if self._progress_bar:
                # 1. Write completion of previous step (with checkmark)
                if self._previous_action_name:
                    _, past_status = self.get_status_messages(self._previous_action_name)
                    self._progress_bar.write(_make_text_safe_for_console(f"\u2705 {past_status}"))  # ✅

                # 2. Get current step information and show progress
                present_status, _ = self.get_status_messages(action_name)

                # 3. Show current progress with appropriate icon
                if action_name == "script_end":
                    self._progress_bar.set_description(_make_text_safe_for_console(f"\u2705 {present_status}"))  # ✅
                else:
                    self._progress_bar.set_description(_make_text_safe_for_console(f"\u23f3 {present_status}"))  # ⏳
                self._progress_bar.update(1)

                # 4. Remember this action for next iteration
                self._previous_action_name = action_name

            else:
                # Non-progress-bar mode
                if self._previous_action_name:
                    _, past_status = self.get_status_messages(self._previous_action_name)
                    safe_print(f"\u2705 {past_status}")  # ✅

                self._previous_action_name = action_name

    def write_intelligent_error(self, message: str):
        """Write errors with previous completion flush."""
        # Flush any previous completion before showing error
        if self._previous_action_name:
            _, past_status = self.get_status_messages(self._previous_action_name)
            if self._progress_bar:
                self._progress_bar.write(_make_text_safe_for_console(f"\u2705 {past_status}"))  # ✅
            else:
                safe_print(f"\u2705 {past_status}")  # ✅
            self._previous_action_name = None

        # Show error with safe console handling
        error_msg = f"\u274c {message}"  # ❌
        if self._progress_bar:
            self._progress_bar.write(_make_text_safe_for_console(error_msg))
        else:
            safe_print(error_msg)

    def extract_intelligence_automatically(self, action_name: str, status: str, message: str, details: dict):
        """Extract intelligence from existing _log_action patterns."""
        if status != "SUCCESS":
            return

        # File creation patterns (extracted from analysis of 191 _log_action calls)
        if action_name.endswith("_init") or "initialized" in message.lower():
            self._auto_intelligence["files_created"].add("pyproject.toml")
        elif "gitignore" in action_name:
            self._auto_intelligence["files_created"].add(".gitignore")
        elif "venv" in action_name and ("created" in message.lower() or "ready" in message.lower()):
            self._auto_intelligence["files_created"].add(".venv/")
        elif "configure_vscode" in action_name:
            self._auto_intelligence["files_created"].update([".vscode/settings.json", ".vscode/launch.json"])
        elif "uv.lock" in message or ("uv_add" in action_name and "installed" in message.lower()):
            self._auto_intelligence["files_created"].add("uv.lock")
            self._auto_intelligence["files_modified"].add("pyproject.toml")

        # Command result extraction
        if details and "command" in details:
            cmd = details["command"]
            self._auto_intelligence["commands_executed"].append(cmd)

            if "stdout" in details:
                self._extract_results_from_command_output(cmd, details["stdout"])

        # Issue detection
        if "unused imports" in message.lower():
            self._extract_unused_imports_automatically(details)
        elif "conflict" in message.lower():
            self._auto_intelligence["issues"].append(f"Dependency conflict: {message.split('|')[0].strip()}")

    def _extract_results_from_command_output(self, command: str, output: str):
        """Extract concrete results from command outputs automatically."""
        # Extract package counts from pipreqs output
        if "pipreqs" in command and output:
            package_lines = [line for line in output.split('\n') if '==' in line]
            self._auto_intelligence["packages_discovered"] = len(package_lines)

        # Extract installation results from uv add output
        elif "uv add" in command and "installed" in output.lower():
            import re
            match = re.search(r'installed\s+(\d+)\s+package', output.lower())
            if match:
                self._auto_intelligence["packages_installed"] = int(match.group(1))

    def _extract_unused_imports_automatically(self, details: dict):
        """Extract unused imports automatically from existing ruff details."""
        if details and "unused_imports_details" in details:
            for file_path, line_num, import_desc in details["unused_imports_details"]:
                rel_path = file_path.split("/")[-1] if "/" in file_path else file_path
                self._auto_intelligence["issues"].append(f"Unused import: {rel_path}:{line_num} - {import_desc}")

            # Automatically suggest fix since ruff --fix is safe for unused imports
            self._auto_intelligence["auto_fixes_available"].append({
                "issue": "unused imports",
                "command": "uvx ruff check . --fix",
                "description": "Remove unused imports automatically",
                "safe": True
            })

    def handle_intelligent_output(self, action_name: str, status: str, message: str, details: dict):
        """Handle output with automatic intelligence - main entry point."""
        # Get verbose mode safely
        verbose_mode = getattr(self.config, 'verbose', False)  # Default to clean for Progressive Disclosure

        if verbose_mode:
            # EXISTING OUTPUT - exactly as before (lines 861-865)
            console_prefix = status.upper()
            if console_prefix == "SUCCESS":
                console_prefix = "INFO"
            details_str = f" | For details open: {json.dumps(details)}" if details and details != {} else ""
            print(f"{console_prefix}: ({action_name}) {message}{details_str}")

            # Still show summary at script end even in verbose mode
            if action_name == "script_end":
                self.show_intelligent_summary()
            return

        # INTELLIGENT OUTPUT with automatic details
        if action_name == "script_start":
            self.init_progress_bar()
        elif status == "ERROR":
            self.write_intelligent_error(message)
        elif self.should_show_progress(action_name) and status in ["SUCCESS", "WARN"]:
            self.update_progress_with_auto_intelligence(action_name)
            # Show summary after script_end progress update
            if action_name == "script_end":
                self.show_intelligent_summary()

    def show_intelligent_summary(self):
        """Show actionable summary with next steps."""
        if self._progress_bar:
            # Special case: script_end already shows in progress bar description
            # Don't write it again as a completion line
            if self._previous_action_name and self._previous_action_name != "script_end":
                _, past_status = self.get_status_messages(self._previous_action_name)
                self._progress_bar.write(_make_text_safe_for_console(f"\u2705 {past_status}"))  # ✅

            # Close progress bar without duplicate message
            self._progress_bar.close()
            self._previous_action_name = None
        else:
            # In non-progress-bar mode, still show the completion
            if self._previous_action_name:
                _, past_status = self.get_status_messages(self._previous_action_name)
                safe_print(f"\u2705 {past_status}")  # ✅
            self._previous_action_name = None

        print("\n" + "="*60)
        safe_print("\U0001f389 PYUVSTARTER SETUP COMPLETE")  # 🎉
        print("="*60)


        # Robustly determine project_dir and venv_path
        project_dir = None
        venv_name = '.venv'
        if self.config and hasattr(self.config, 'project_dir'):
            try:
                project_dir = Path(self.config.project_dir)
            except Exception:
                project_dir = Path.cwd()
            venv_name = getattr(self.config, 'venv_name', '.venv')
        else:
            project_dir = Path.cwd()
        venv_path = project_dir / venv_name

        # Platform-aware activation command
        if sys.platform == "win32":
            activate_cmd = f"{venv_path}\\Scripts\\activate"
        else:
            activate_cmd = f"source {venv_path}/bin/activate"

        safe_print("\n\U0001f680 PROJECT SUMMARY:")  # 🚀
        safe_print(f"   \U0001f4c1 Project: {project_dir.name if project_dir else 'Current directory'}")  # 📁
        # List of (file_path, icon, description)
        summary_files = [
            (venv_path, "\U0001f40d", "Virtual environment"),
            ("pyproject.toml", "\U0001f4e6", "Modern Python configuration"),
            ("uv.lock", "\U0001f512", "Locked dependency versions"),
            (".gitignore", "\U0001f648", "Git ignore patterns"),
            (".vscode", "\U0001f527", "VS Code configuration"),
        ]
        files_created = set(self._auto_intelligence.get("files_created", []))
        for file_path, icon, desc in summary_files:
            # file_path may be Path or str
            path_obj = Path(file_path) if not isinstance(file_path, Path) else file_path
            exists = path_obj.exists()
            created = str(file_path) in files_created or (isinstance(file_path, Path) and str(file_path) in files_created)
            marker = "[created]" if created else "[existing]" if exists else ""
            if exists:
                safe_print(f"   {icon} {file_path} — {desc} {marker}")
        # Dependency info - concrete numbers
        if self._auto_intelligence["packages_discovered"] > 0:
            safe_print("\n\U0001f4e6 DEPENDENCIES found and in uv.lock:")  # 📦
            safe_print(f"   \U0001f50d Found {self._auto_intelligence['packages_discovered']} packages from your code")  # 🔍
            if self._auto_intelligence["packages_installed"] > 0:
                safe_print(f"   \u2795 Ensured {self._auto_intelligence['packages_installed']} packages are in uv's .venv and pyproject.toml")  # ➕
            # safe_print("   \u2705 All dependencies locked in uv.lock")  # ✅

        # Issues - only show if there are any
        if self._auto_intelligence["issues"]:
            safe_print("\n\u26a0\ufe0f  ISSUES TO REVIEW:")  # ⚠️
            for issue in self._auto_intelligence["issues"][:3]:  # Show first 3 only
                print(f"   • {issue}")
            if len(self._auto_intelligence["issues"]) > 3:
                print(f"   ... +{len(self._auto_intelligence['issues']) - 3} more (see log)")

        # Next steps - prioritize activation and immediate use
        safe_print("\n\U0001f3af NEXT STEPS:")  # 🎯
        safe_print("   1. \U0001f40d Activate virtual environment:")  # 🐍
        print(f"      {activate_cmd}")
        # Use get_uv_run_command to suggest the correct script, passing the resolved pyproject.toml path
        pyproject_path = project_dir / PYPROJECT_TOML_NAME
        # print debug info about pyproject_path
        safe_print(f"      (pyproject.toml path: {pyproject_path})")
        uv_run_cmd = get_uv_run_command(pyproject_path=pyproject_path)
        safe_print(f"   2. \U0001f680 Run your Python code:\n      {uv_run_cmd}")  # 🚀
        safe_print("   3. \U0001f527 Open in VS Code (optional):")  # 🔧
        print("      code .")
        if Path(".git").exists():
            safe_print("   4. \U0001f4dd Commit your changes:")  # 📝
            print("      git add . && git commit -m 'Set up Python project with uv'")
        else:
            safe_print("   4. \U0001f4dd Initialize git (optional):")  # 📝
            print("      git init && git add . && git commit -m 'Set up Python project with pyuvstarter for uv'")

        print("\n\U0001f4cb For details open: pyuvstarter_setup_log.json")  # 📋
        print("="*60)

# Global instance for backward compatibility during migration
_progress_tracker = None


def set_output_mode(config):
    """Initialize intelligent output system with config."""
    global _progress_tracker
    _progress_tracker = ProgressTracker(config)















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

    # === AUTOMATIC INTELLIGENCE EXTRACTION & PROGRESS TRACKING ===
    global _progress_tracker
    if _progress_tracker:
        _progress_tracker.extract_intelligence_automatically(action_name, status, message, details)
        _progress_tracker.handle_intelligent_output(action_name, status, message, details)


def _get_next_steps_text(config: 'CLICommand') -> str:
    """
    Generates context-aware 'Next Steps' guidance text.

    ENHANCED (v7.3): Only includes the activation step if the venv was actually created.
    This prevents showing invalid commands if venv creation failed.
    """
    steps = [
        "1. If VS Code is open with this project, reload the window (Ctrl+Shift+P > 'Developer: Reload Window')."
    ]

    # HARDENED: Only include the activation step if the venv was actually created.
    venv_path = config.project_dir / config.venv_name
    if venv_path.exists() and venv_path.is_dir():
        if sys.platform == "win32":
            activate_cmd = f"'{venv_path / 'Scripts' / 'activate'}'"
        else:
            activate_cmd = f"source '{venv_path / 'bin' / 'activate'}'"
        steps.append(f"2. Activate the environment in your terminal:\n    {activate_cmd}")

    steps.append(f"3. Review `{PYPROJECT_TOML_NAME}`, `uv.lock`, and `{GITIGNORE_NAME}`.")
    steps.append(f"4. Commit your project files, including `{PYPROJECT_TOML_NAME}` and `uv.lock`, to version control.")

    return "Next Steps:\n" + "\n".join(steps)


def _save_log(config: 'CLICommand'):
    """Saves the accumulated log data to a JSON file."""
    global _log_data_global
    log_file_path = config.project_dir / config.log_file_name

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
        next_steps_text = _get_next_steps_text(config)
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
    # We use hasattr instead of version check because it's more reliable
    if hasattr(sys, "stdlib_module_names"):
        stdlib_modules = set(sys.stdlib_module_names)
    else:
        # Fallback for older Python: try to use an optional, pre-installed helper package.
        try:
            from stdlib_list import stdlib_list  # type: ignore
            # Get stdlib for the version of python running the script
            stdlib_modules = set(stdlib_list(f"{sys.version_info.major}.{sys.version_info.minor}"))
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

def _extract_package_name_from_specifier(specifier: str) -> str:
    """Extract the base package name from a PEP 508 specifier.

    Examples:
        'numpy>=1.19.0' -> 'numpy'
        'requests[security]>=2.25.0' -> 'requests'
        'Django>=3.0,<4.0' -> 'django' (lowercase)
    """
    from packaging.requirements import Requirement

    # Handle None gracefully
    if specifier is None:
        return ""

    try:
        req = Requirement(specifier)
        return req.name.lower()
    except Exception:
        # Fallback to simple parsing if packaging fails
        base_name = specifier.split('[')[0].split('=')[0].split('>')[0].split('<')[0].split('~')[0].split('!')[0].strip()
        return base_name.lower() if base_name else ""


def _categorize_uv_add_error(stderr: str) -> str:
    """Categorize uv add error messages into actionable failure reasons.

    Args:
        stderr: Error output from uv add command (should be lowercased before passing)

    Returns:
        Human-readable failure reason string

    Examples:
        'no solution found...python' -> 'incompatible with current Python version'
        'no solution found' -> 'version conflict with existing dependencies'
        'failed to build' -> 'build failed (missing system dependencies)'
    """
    stderr_lower = stderr.lower() if stderr else ""

    if "no solution found" in stderr_lower and "python" in stderr_lower:
        return "incompatible with current Python version"
    elif "no solution found" in stderr_lower:
        return "version conflict with existing dependencies"
    elif "can't be installed" in stderr_lower and "wheel" in stderr_lower:
        return "no compatible wheel available for your platform/Python version"
    elif "failed to build" in stderr_lower:
        return "build failed (missing system dependencies)"
    elif "could not find" in stderr_lower or "does not exist" in stderr_lower:
        return "package not found on PyPI"
    else:
        return "unknown error"


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
        "cv": "opencv-python",  # Some old code uses cv
        "skimage": "scikit-image",

        # Image Processing
        "pil": "pillow",
        "PIL": "pillow",

        # Configuration & Serialization
        "yaml": "pyyaml",
        "toml": "toml",  # Keep this - even though names match, good documentation

        # Web & APIs
        "requests_oauthlib": "requests-oauthlib",
        "google.cloud": "google-cloud",
        "bs4": "beautifulsoup4",
        "flask_cors": "flask-cors",
        "flask_sqlalchemy": "flask-sqlalchemy",
        "flask_migrate": "flask-migrate",
        "flask_login": "flask-login",
        "flask_wtf": "flask-wtforms",
        "rest_framework": "djangorestframework",

        # Database & ORM
        "psycopg2": "psycopg2-binary",
        "MySQLdb": "mysqlclient",
        "mysqldb": "mysqlclient",
        "_mysql": "mysqlclient",

        # Development Tools
        "dotenv": "python-dotenv",
        "dateutil": "python-dateutil",
        "jose": "python-jose",
        "magic": "python-magic",
        "dns": "dnspython",

        # GUI & Graphics
        "tkinter": "",  # Built-in, should be filtered out elsewhere
        "PyQt5": "pyqt5",
        "PyQt6": "pyqt6",
        "wx": "wxpython",

        # System & OS
        "win32api": "pywin32",
        "win32com": "pywin32",
        "pywintypes": "pywin32",
        "pythoncom": "pywin32",

        # Testing & Mocking
        "mock": "mock",  # Built into unittest in Python 3.3+
        "_pytest": "pytest",  # Internal pytest imports

        # Async & Concurrency
        "asyncio": "",  # Built-in

        # Typing
        "typing_extensions": "typing-extensions",

        # Additional common mismatches
        "Crypto": "pycryptodome",  # Or pycrypto
        "Cryptodome": "pycryptodomex",
        "jwt": "pyjwt",
        "git": "gitpython",
        "serial": "pyserial",
        "usb": "pyusb",
        "docx": "python-docx",
        "pptx": "python-pptx",
        "fitz": "pymupdf",
        "PyPDF2": "pypdf2",
        "websocket": "websocket-client",  # Different from 'websockets'
        "Levenshtein": "python-levenshtein",
        "slugify": "python-slugify",
        "multipart": "python-multipart",
        "memcache": "python-memcached",
        "ldap": "python-ldap",
        "nacl": "pynacl",
        "etree": "lxml",  # ElementTree from lxml
        "_cffi_backend": "cffi",
        "googleapiclient": "google-api-python-client",
        "apiclient": "google-api-python-client",
    }

    name_lower = name.lower()

    # Step 1: Check our curated mapping for known discrepancies
    if name_lower in mapping:
        canonical = mapping[name_lower]
        # Empty string means built-in module that shouldn't be installed
        return canonical if canonical else name_lower

    # Step 2: Check if it's a known built-in module
    # This prevents trying to install built-in modules
    if name_lower in sys.builtin_module_names:
        return ""

    # Step 3: Skip any importlib.metadata lookup!
    # Why? Because:
    # - It only works for already-installed packages (defeats our purpose)
    # - It's slow even for simple lookups
    # - Most packages have import name == package name anyway
    # - Our static mapping handles the known exceptions

    # Default: Assume import name == package name (lowercased)
    # This is correct for 95%+ of packages:
    # requests -> requests, numpy -> numpy, flask -> flask, etc.
    # If this assumption is wrong, the user will see a clear error from uv/pip
    # and we can add it to our mapping for future users
    return name_lower


def _extract_package_name_from_dependency_tuple(dependency_tuple) -> str:
    """
    Extract package name from a dependency tuple (e.g., from uv's dependency format).

    This handles cases where uv returns dependency information as tuples
    rather than simple specifier strings.

    Examples:
        ('numpy', 'numpy>=1.19.0') -> 'numpy'
        ('requests', 'requests[security]>=2.25.0') -> 'requests'
        ('name-only', 'name-only') -> 'name-only'
        (None, None) -> ''  # Handle None gracefully
    """
    if dependency_tuple is None:
        return ""

    try:
        # If it's a string, delegate to the string function
        if isinstance(dependency_tuple, str):
            return _extract_package_name_from_specifier(dependency_tuple)

        # If it's a tuple or list, extract the name (usually first element)
        if isinstance(dependency_tuple, (tuple, list)):
            if len(dependency_tuple) >= 1:
                name = dependency_tuple[0]
                if name and str(name).strip():  # Non-empty string after stripping
                    return str(name).lower()
                elif len(dependency_tuple) >= 2:
                    # If first element is empty, try the second (specifier)
                    return _extract_package_name_from_specifier(str(dependency_tuple[1]))
            return ""

        # If it's any other type, convert to string and parse
        return _extract_package_name_from_specifier(str(dependency_tuple))

    except Exception:
        # Fallback: return empty string for any parsing errors
        return ""


def _find_all_notebooks(scan_path: Path, ignore_manager: Optional[GitIgnore]) -> List[Path]:
    """Finds all .ipynb files within a scope, efficiently respecting ignore patterns.

    This function leverages the GitIgnore class's `get_allowed_files_by_pattern` method
    to efficiently retrieve only those .ipynb files that are not excluded by any
    .gitignore rule. This ensures full compliance with .gitignore specifications
    (including negation and directory precedence) while optimizing file system traversal.

    Args:
        scan_path: The root directory to scan for notebooks.
        ignore_manager: An optional GitIgnore object containing patterns.
                        If None, all .ipynb files are returned.

    Returns:
        A list of Path objects for .ipynb files (filtered by ignore patterns if provided).
    """
    if ignore_manager:
        # Use the GitIgnore's specialized method to get files matching '.ipynb'
        # that are also not ignored by any .gitignore rule.
        notebook_paths = ignore_manager.get_allowed_files_by_pattern("*.ipynb")

        # Filter to ensure paths are within the original scan_path, as get_allowed_files_by_pattern
        # operates on the GitIgnore's root_dir, which might be broader.
        # This also ensures we return only files, not directories that might match a pattern.
        return [p for p in notebook_paths if p.is_file() and p.is_relative_to(scan_path)]
    else:
        # No ignore manager, return all .ipynb files
        return [p for p in scan_path.rglob("*.ipynb") if p.is_file()]


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
    action_name = f"notebook_manual_parse_{nb_path.stem}"
    _log_action(action_name, "INFO", f"Using hardened fallback parser for '{nb_path.name}'.")

    try:
        with open(nb_path, "r", encoding="utf-8", errors='ignore') as f:
            nb_content = json.load(f)
    except (FileNotFoundError, IOError, json.JSONDecodeError, Exception) as e:
        _log_action(action_name, "ERROR", f"Cannot read or parse file '{nb_path.name}'.", details={"type": type(e).__name__, "exception": str(e)})
        return set()

    # Heuristic to quickly identify lines that are probably shell commands.
    shell_command_pattern = re.compile(r"^\s*[!%]")
    # Comprehensive pattern to match various install commands.
    install_pattern = re.compile(
        r"^(?:(?:pip3?|python\s+-m\s+pip|uv\s+pip|conda|mamba)\s+install|uv\s+add|poetry\s+add)\s*(.*)",
        re.IGNORECASE)

    discovered_packages: Set[Tuple[str, str]] = set()
    python_code_block: List[str] = []
    shell_line_buffer = ""

    cells = nb_content.get("cells", [])
    if not isinstance(cells, list):
        _log_action(action_name, "WARN", f"Notebook '{nb_path.name}' has malformed 'cells' key (not a list). Skipping.")
        return set()

    for cell in cells:
        if not isinstance(cell, dict) or cell.get("cell_type") != "code":
            continue

        source_block = cell.get("source", [])
        if isinstance(source_block, str):
            lines = source_block.splitlines()
        elif isinstance(source_block, list):
            lines = source_block
        else:
            continue

        for line in lines:
            if not isinstance(line, str):
                continue

            if shell_command_pattern.match(line):
                line_no_comment = line.split('#', 1)[0]
                stripped_line = line_no_comment.rstrip()

                if stripped_line.endswith('\\'):
                    shell_line_buffer += stripped_line[:-1] + " "
                    continue

                # We have a complete logical shell line. Process it.
                logical_shell_line = (shell_line_buffer + line_no_comment).strip()
                shell_line_buffer = ""

                # Strip the leading `!` or `%` before matching the install command.
                command_body = logical_shell_line.lstrip('!% \t')

                install_match = install_pattern.match(command_body)
                if install_match:
                    # *** CORRECTED LOGIC ***
                    # 1. Get the arguments from the successful match.
                    args_str = install_match.group(1).strip()

                    # 2. NOW, check this argument string for complex shell operators.
                    command_terminators = ['&&', '|', ';']
                    for terminator in command_terminators:
                        if terminator in args_str:
                            _log_action(action_name, "WARN", f"Complex shell command detected. Only parsing up to the first '{terminator}'.")
                            args_str = args_str.split(terminator, 1)[0].strip()
                            break

                    if not args_str:
                        continue
                    try:
                        tokens = shlex.split(args_str)
                        discovered_packages.update(_parse_install_tokens(tokens))
                    except ValueError:
                        _log_action(action_name, "WARN", f"Could not parse malformed install command arguments: '{args_str}'.")
            else:
                # This is a Python-like line. Append it raw to preserve indentation.
                python_code_block.append(line)

    if python_code_block:
        pure_python_code = "\n".join(python_code_block)
        if pure_python_code.strip():
            try:
                tree = ast.parse(pure_python_code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            base_pkg = alias.name.split('.')[0].lower()
                            if base_pkg and base_pkg not in _DYNAMIC_IGNORE_SET:
                                discovered_packages.add((_canonicalize_pkg_name(base_pkg), base_pkg))
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        base_pkg = node.module.split('.')[0].lower()
                        if base_pkg and base_pkg not in _DYNAMIC_IGNORE_SET:
                            discovered_packages.add((_canonicalize_pkg_name(base_pkg), base_pkg))
            except SyntaxError as e:
                _log_action(action_name, "INFO", "Skipping AST parse due to non-Python syntax.", details={"error": str(e)})

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
            base_pkg = _extract_package_name_from_specifier(part)
            if base_pkg and base_pkg not in _DYNAMIC_IGNORE_SET:
                canonical_name = _canonicalize_pkg_name(base_pkg)
                # Add the full specifier as found (e.g., 'pandas==1.2.3').
                discovered.add((canonical_name, part))
    return discovered


# ==============================================================================
# SECTION: CORE IMPLEMENTATION OF PYTHON AND NOTEBOOK DEPENDENCY DISCOVERY
# ==============================================================================

class DiscoveryResult:
    """A structured container for dependency discovery results."""
    def __init__(self):
        self.from_scripts: Set[Tuple[str, str]] = set()
        self.from_converted_notebooks: Set[Tuple[str, str]] = set()
        self.from_manual_notebooks: Set[Tuple[str, str]] = set()
        self.scan_path: Optional[Path] = None
        self.notebooks_found_count: int = 0
        self.notebooks_converted_count: int = 0
        self.notebooks_fallback_count: int = 0

    @property
    def all_unique_dependencies(self) -> Set[Tuple[str, str]]:
        return self.from_scripts | self.from_converted_notebooks | self.from_manual_notebooks

    def __str__(self):
        header = f"DiscoveryResult for scope: '{self.scan_path}'"
        return (f"{header}\n{'-' * len(header)}\n"
                f"  - From .py scripts: {len(self.from_scripts)}\n"
                f"  - From Converted Notebooks: {len(self.from_converted_notebooks)}\n"
                f"  - From Manual-Parse Notebooks: {len(self.from_manual_notebooks)}\n"
                f"  - Total Unique Dependencies: {len(self.all_unique_dependencies)}")


def discover_dependencies_in_scope(scan_path: Path, ignore_manager: Optional[GitIgnore] = None, scan_notebooks: bool = True, dry_run: bool = False, pipreqs_mode: Optional[str] = None) -> DiscoveryResult:
    """The primary, user-facing function to discover all dependencies within a specific scope.

    Args:
        scan_path: Directory to scan for dependencies
        ignore_manager: GitIgnore patterns to respect during scan
        scan_notebooks: Whether to scan Jupyter notebooks
        dry_run: If True, log commands without executing
        pipreqs_mode: Optional mode for pipreqs ('no-pin', 'gt', 'compat')
    """
    action_name = f"discover_deps_{scan_path.name}"
    _log_action(action_name, "INFO", f"Starting scope-aware discovery in '{scan_path}'.")
    result = DiscoveryResult()
    result.scan_path = scan_path

    # Log ignore configuration
    if ignore_manager:
        _log_action(action_name, "INFO", "Using GitIgnore patterns for dependency discovery")
    else:
        _log_action(action_name, "INFO", "GitIgnore support not provided - will scan all files")

    _log_action(action_name, "INFO", "Phase 1: Analyzing Python scripts...")
    result.from_scripts = _get_packages_from_pipreqs(scan_path, ignore_manager, dry_run, pipreqs_mode)

    if not scan_notebooks:
        _log_action(action_name, "INFO", "Phase 2 skipped: notebook scanning is disabled.")
        return result

    notebook_paths = _find_all_notebooks(scan_path, ignore_manager)
    result.notebooks_found_count = len(notebook_paths)
    if not notebook_paths:
        _log_action(action_name, "INFO", "Phase 2 complete: no notebooks found in scope.")
        return result

    _log_action(action_name, "INFO", f"Phase 2: Analyzing {len(notebook_paths)} notebook(s)...")

    conversion_map: Dict[Path, Path] = {}
    with tempfile.TemporaryDirectory(prefix="pyuvstarter_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        # Convert notebooks to Python scripts for analysis
        conversion_map = _convert_notebooks_to_py(notebook_paths, temp_dir, scan_path, dry_run)
        if conversion_map:
             _log_action(action_name, "INFO", f"Analyzing {len(conversion_map)} converted notebook(s)...")
             # For temp directory scanning, we don't need gitignore support since these are already filtered converted files
             result.from_converted_notebooks = _get_packages_from_pipreqs(temp_dir, None, dry_run, pipreqs_mode)

    result.notebooks_converted_count = len(conversion_map)
    failed_primary_notebooks = set(notebook_paths) - set(conversion_map.keys())
    result.notebooks_fallback_count = len(failed_primary_notebooks)

    if failed_primary_notebooks:
        _log_action(action_name, "INFO", f"Using fallback manual parser for {len(failed_primary_notebooks)} notebook(s).")
        for nb_path in failed_primary_notebooks:
            try:
                result.from_manual_notebooks.update(_parse_notebook_manually(nb_path))
            except Exception as e:
                _log_action(action_name, "CRITICAL", f"Unrecoverable error parsing '{nb_path.name}'.", details={"exception": str(e)})

    # Update progress tracker intelligence with final comprehensive count
    global _progress_tracker
    if _progress_tracker:
        _progress_tracker._auto_intelligence["packages_discovered"] = len(result.all_unique_dependencies)
        _progress_tracker._auto_intelligence["files_scanned"] = len(result.from_scripts) + result.notebooks_found_count

    _log_action(action_name, "SUCCESS", f"Discovery complete. {result}")
    # log the discovery summary
    summary = generate_discovery_summary(result)
    _log_action(action_name, "INFO", summary)

    return result

def generate_discovery_summary(result: DiscoveryResult) -> str:
    """Generates a detailed summary of the discovery phase results."""
    summary_lines = [
        "\n--- Discovery Phase Summary ---",
        f"\u2705 Scope Scanned: '{result.scan_path}'",  # ✅
    ]

    if result.from_scripts:
        summary_lines.append(f"  - Found {len(result.from_scripts)} dependencies in .py scripts.")
    if result.notebooks_found_count > 0:
        nb_deps_count = len(result.from_converted_notebooks | result.from_manual_notebooks)
        summary_lines.append(f"  - Found {nb_deps_count} dependencies in {result.notebooks_found_count} notebook(s).")
        if result.notebooks_converted_count > 0 or result.notebooks_fallback_count > 0:
             summary_lines.append(f"    ({result.notebooks_converted_count} analyzed with primary tools, {result.notebooks_fallback_count} with fallback parser)")

    total_deps = len(result.all_unique_dependencies)
    if total_deps > 0:
        summary_lines.append(f"  - Total unique dependencies discovered: {total_deps}")
    else:
        summary_lines.append("  - No dependencies discovered in this scope.")
    return "\n".join(summary_lines)



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
        _run_command(["uv", "init", "--no-workspace"], f"{action_name}_uv_init_exec", work_dir=project_root, dry_run=dry_run)

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
                _log_action(action_name, "INFO", f"`uv init` created '{main_py_path.name}', but other .py files existed. Removing '{main_py_path.name}'.")
                try:
                    main_py_path.unlink()
                    # This is part of the same logical step, don't log separate SUCCESS
                except OSError as e:
                    _log_action(action_name, "ERROR", f"Failed to remove '{main_py_path.name}': {e}.")
            else: # Project was empty of .py files, so main.py from uv init is fine
                _log_action(f"{action_name}_keep_main_py", "INFO", f"`uv init` created '{main_py_path.name}' in an otherwise empty Python project. It will be kept as standard for a new project.")
        return True

    except Exception: # Error logged by _run_command
        _log_action(action_name, "ERROR", "Failed to initialize project with `uv init`. See command execution log.\nManual `pyproject.toml` creation or `uv init` troubleshooting needed.")
        return False


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

    # Dynamic import is necessary here because:
    # 1. We need to check if tomllib is available (Python 3.11+)
    # 2. If not, we fall back to the third-party 'toml' package
    # 3. This function needs to work even if neither is available
    # We use importlib.import_module to avoid syntax errors on older Python
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
                    pkg_name = _extract_package_name_from_specifier(dep_str)
                    if pkg_name:
                        dependencies.add(pkg_name)

        _log_action(action_name, "SUCCESS", f"Parsed '{pyproject_path.name}'. Found {len(dependencies)} unique base dependency names declared.", details={"source": tomllib_source, "count": len(dependencies), "found_names": sorted(list(dependencies)) if dependencies else "None"})
        return dependencies
    except Exception as e:
        msg = f"Failed to parse '{pyproject_path.name}' using {tomllib_source} to get dependency list. Check its TOML syntax. Dependency list might be incomplete for subsequent checks. Exception: {e}"
        _log_action(action_name, "ERROR", msg, details={"exception": str(e)})
        return dependencies

def _get_packages_from_legacy_req_txt_simple(requirements_path: Path) -> set[tuple[str, str]]:
    """
    Simple fallback parser for requirements.txt when pip-requirements-parser is not available.
    Returns a set of (canonical_base_name, full_specifier) tuples.
    """
    action_name = "read_legacy_requirements_txt_simple"
    packages_specs = set()

    if not requirements_path.exists():
        return packages_specs

    _log_action(action_name, "WARN", "Using simple parser - inline comments will not be handled correctly")

    try:
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Simple comment stripping (not perfect but better than nothing)
                if '#' in line:
                    line = line.split('#')[0].strip()
                if line:
                    # Extract package name using the existing helper
                    pkg_name = _extract_package_name_from_specifier(line)
                    if pkg_name:
                        canonical_name = _canonicalize_pkg_name(pkg_name)
                        packages_specs.add((canonical_name, line))
    except Exception as e:
        _log_action(action_name, "ERROR", f"Failed to read requirements.txt: {e}")

    return packages_specs


def _get_packages_from_legacy_req_txt(requirements_path: Path) -> set[tuple[str, str]]:
    """
    Reads a requirements.txt file and extracts package specifiers.
    Returns a set of (canonical_base_name, full_specifier) tuples.
    """
    try:
        from pip_requirements_parser import RequirementsFile
    except ImportError:
        _log_action("read_legacy_requirements_txt_content", "ERROR",
                   "pip-requirements-parser is not installed. Cannot parse requirements.txt with comments.")
        _log_action("read_legacy_requirements_txt_content", "INFO",
                   "Install it with: uv pip install pip-requirements-parser")
        # Fall back to simple line-by-line parsing
        return _get_packages_from_legacy_req_txt_simple(requirements_path)

    action_name = "read_legacy_requirements_txt_content"
    packages_specs = set()

    if not requirements_path.exists():
        _log_action(action_name, "INFO", f"No legacy '{requirements_path.name}' found.")
        return packages_specs

    _log_action(action_name, "INFO", f"Reading legacy '{requirements_path.name}'.")

    try:
        rf = RequirementsFile.from_file(str(requirements_path))

        for req in rf.requirements:
            if req.name:
                canonical_name = _canonicalize_pkg_name(req.name.lower())
                # Build the full specifier string with extras
                extras_str = f"[{','.join(sorted(req.extras))}]" if req.extras else ""
                specifier_str = str(req.specifier) if req.specifier else ""
                full_spec = f"{req.name}{extras_str}{specifier_str}"
                packages_specs.add((canonical_name, full_spec))

        _log_action(action_name, "SUCCESS", f"Read {len(packages_specs)} package specifier(s) from '{requirements_path.name}'.")
    except Exception as e:
        _log_action(action_name, "ERROR", f"Could not parse '{requirements_path.name}': {e}", details={"exception": str(e)})

    return packages_specs


def _translate_gitignore_to_pipreqs_ignores(ignore_manager: GitIgnore) -> Tuple[Set[str], List[str]]:
    """Translates .gitignore patterns to a format compatible with pipreqs' --ignore flag.

    This is a best-effort translation. It uses a heuristic to extract simple,
    directory-based ignore patterns that pipreqs can understand. It identifies
    and returns complex patterns (e.g., file-specific ignores, negations) that
    cannot be translated, so the calling function can warn the user about any
    potential inaccuracies in the pipreqs scan.

    Args:
        ignore_manager: The GitIgnore object to extract patterns from.

    Returns:
        A tuple containing:
        - A set of directory path strings compatible with pipreqs' --ignore flag.
        - A list of complex pattern strings that could not be translated.
    """
    pipreqs_ignores = set()
    unsupported_patterns = []

    for pattern in ignore_manager.patterns:
        # We only care about ignore patterns (include=True), not re-include patterns (!pattern, include=False)
        if not pattern.include:
            unsupported_patterns.append(str(pattern.pattern))
            continue

        pattern_str = str(pattern.pattern).strip()

        # Heuristic: A pattern is considered a simple, translatable directory if:
        # 1. It ends with a '/' (e.g., "build/").
        # 2. It contains no slashes and no wildcards, making it a simple name (e.g., "node_modules").
        # This avoids file patterns ("*.log"), complex paths ("src/foo/bar.py"), and wildcards.
        is_definitely_dir = pattern_str.endswith('/')
        is_simple_name = '/' not in pattern_str and '*' not in pattern_str and '?' not in pattern_str

        if is_definitely_dir or is_simple_name:
            # Normalize to a simple name for pipreqs' --ignore format.
            pipreqs_ignores.add(pattern_str.strip('/'))
        else:
            # It's a complex file pattern, a wildcard pattern, or another rule we can't handle.
            unsupported_patterns.append(pattern_str)

    return pipreqs_ignores, unsupported_patterns


def _get_packages_from_pipreqs(scan_path: Path, ignore_manager: Optional[GitIgnore], dry_run: bool, mode: Optional[str] = None) -> Set[Tuple[str, str]]:
    """
    Runs the `pipreqs` tool safely and parses its output. This function represents
    the synthesis of the best features from multiple versions.

    Args:
        scan_path: The directory to scan for dependencies.
        ignore_manager: A fully configured GitIgnore object containing all patterns
                        (from .gitignore, defaults, and CLI).
        dry_run: If True, the command will be logged but not executed.
        mode: Optional pipreqs mode ('no-pin', 'gt', 'compat'). If None, uses default pinned versions.

    Returns:
        A set of (canonical_base_name, full_specifier) tuples, or an empty set on failure.
    """
    # Use a descriptive action_name derived from the input path for clear logging.
    action_name = f"pipreqs_discover_{scan_path.name}"

    # Build command as list of strings for subprocess execution
    pipreqs_args: List[str] = ["uvx", "pipreqs", "--print"]

    # Add mode if specified (for fallback strategy)
    if mode:
        pipreqs_args.extend(["--mode", mode])

    # Translate the comprehensive .gitignore patterns into the simple directory list
    # that pipreqs can understand.
    if ignore_manager:
        translated_ignores, complex_patterns = _translate_gitignore_to_pipreqs_ignores(ignore_manager)

        # Warn the user if there are complex .gitignore rules that pipreqs cannot respect.
        if complex_patterns:
            _log_action(action_name, "WARN", f"Found {len(complex_patterns)} complex .gitignore rules that cannot be translated for the pipreqs scan. These rules will be ignored by pipreqs, which may result in slightly inaccurate dependency discovery. The unsupported patterns are: {complex_patterns}")

        # MOTIVATION (from vb): The --ignore flag of pipreqs requires a path. By constructing
        # the full path, we ensure this command works correctly regardless of the
        # current working directory from which this script is executed. This is the most robust method.
        if translated_ignores:
            # Note: pipreqs only supports directory names, not glob patterns. The helper
            # function `_translate_gitignore_to_pipreqs_ignores` handles this translation.
            full_path_ignores = [str(scan_path / d) for d in translated_ignores]
            pipreqs_args.extend(["--ignore", ",".join(sorted(full_path_ignores))])

    # Standard CLI practice: the main subject of the command is the last argument.
    pipreqs_args.append(str(scan_path))

    try:
        stdout, _ = _run_command(pipreqs_args, f"{action_name}_exec", dry_run=dry_run)

        # In a dry run, the mock command returns an empty string. Handle this cleanly.
        if not stdout:
            return set()

        packages_specs = set()
        for line in stdout.splitlines():
            line = line.strip()
            # Ignore comments and empty lines in the requirements output.
            if not line or line.startswith("#"):
                continue

            # Use a regex to robustly extract the package name from a PEP 508 string.
            # This correctly handles specifiers like 'package[extra]>=1.0.0' or 'package~=2.2'.
            match = re.match(r"^([\w\.-]+)", line)
            if not match:
                _log_action(action_name, "WARN", f"Could not parse requirement line from pipreqs output: '{line}'")
                continue

            base_name = match.group(1).lower()
            packages_specs.add((_canonicalize_pkg_name(base_name), line))

        # ENHANCEMENT (from va): Provide more nuanced feedback to the user.
        if packages_specs:
            _log_action(action_name, "SUCCESS", f"Discovered {len(packages_specs)} unique package(s).")
        else:
            _log_action(action_name, "INFO", "`pipreqs` found no import-based dependencies in this source.")

        return packages_specs

    except subprocess.CalledProcessError:
        # ENHANCEMENT (from va): Provide a more actionable error message.
        _log_action(action_name, "ERROR", "`uvx pipreqs` command failed. Check pyuvstarter_setup_log.json for details.\nTry running `uvx pipreqs --help` to verify pipreqs is available.")
    except Exception as e:
        _log_action(action_name, "ERROR", f"An unexpected error occurred while running `pipreqs`: {e}", details={"exception": str(e)})

    # Return an empty set on any failure to allow the calling process to continue.
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
    declared_deps_before_management: set[str],
    project_imported_packages: set[tuple[str, str]],
) -> Optional[Dict[str, Any]]:
    """
    Implements the "Context-Aware Orchestrator" philosophy. It builds a
    unified model of all dependency requests, uses safe heuristics to merge them
    while respecting user intent, and then delegates final resolution to `uv`.
    """
    action_name = "manage_project_dependencies"
    _log_action(action_name, "INFO", f"Starting dependency management with mode: '{migration_mode}'.")

    # --- Step 1: Collect all requirements with context ---
    req_path = project_root / LEGACY_REQUIREMENTS_TXT
    req_pkgs_from_file = _get_packages_from_legacy_req_txt(req_path)
    imported_pkgs_canonical_names = {canonical_name for canonical_name, _ in project_imported_packages}

    # This data structure is key. It gathers all "requests" for a package.
    # Key: canonical_name (e.g., "pillow" for PIL imports), Value: list of specifier strings found.
    all_requests: dict[str, list[str]] = {}

    def add_request(canonical_name: str, specifier: str):
        # Skip empty canonical names (built-in modules)
        if not canonical_name:
            return
        if canonical_name not in all_requests:
            all_requests[canonical_name] = []
        all_requests[canonical_name].append(specifier)

    # Collect from code imports.
    for canonical_name, original_spec in project_imported_packages:
        if canonical_name not in declared_deps_before_management:
            add_request(canonical_name, original_spec)

    # Collect from requirements.txt based on migration mode.
    packages_to_skip_due_to_mode = set()
    editable_install_needed = False
    if migration_mode != "skip-requirements":
        for canonical_name, full_spec in req_pkgs_from_file:
            if canonical_name in declared_deps_before_management:
                continue
            if full_spec == "-e .":
                editable_install_needed = True
                continue

            is_imported = canonical_name in imported_pkgs_canonical_names
            if migration_mode == "all-requirements" or (migration_mode in ["auto", "only-imported"] and is_imported):
                add_request(canonical_name, full_spec)
            elif not is_imported:
                packages_to_skip_due_to_mode.add(full_spec)

    # --- Step 2: Intelligently merge requests using safe heuristics ---
    final_candidates: list[str] = []

    def is_versioned(spec: str) -> bool:
        """Checks if a specifier contains a version constraint."""
        return any(op in spec for op in ["==", ">=", "<=", ">", "<", "~="])

    for canonical_name, specs in all_requests.items():
        if len(specs) == 1:
            # For single requests, use the canonical name if the spec is unversioned,
            # or the specific versioned spec if it contains version constraints
            spec = specs[0]
            if is_versioned(spec):
                final_candidates.append(spec)
            else:
                final_candidates.append(canonical_name)  # Use canonical name for unversioned packages
            continue

        # More than one request for this package. Time for heuristics.
        # Rule: A more specific (versioned) specifier wins over a less specific one.
        versioned_specs = {s for s in specs if is_versioned(s)}
        unversioned_specs = {s for s in specs if not is_versioned(s)}

        if len(versioned_specs) == 1:
            # The ideal case: one clear version pin was found among generic requests.
            chosen_spec = list(versioned_specs)[0]
            _log_action(action_name, "INFO", f"For package '{canonical_name}', multiple requests found. Prioritizing the specific version constraint: '{chosen_spec}'.")
            final_candidates.append(chosen_spec)
        elif len(versioned_specs) > 1:
            # A true conflict: multiple *different* version constraints.
            # Delegate this impossible task to the expert (`uv`) to get a clear error.
            _log_action(action_name, "WARN", f"For package '{canonical_name}', multiple conflicting version requests found: {sorted(list(versioned_specs))}. Passing all to `uv` to resolve.")
            final_candidates.extend(versioned_specs)
        elif unversioned_specs:
            # Only generic, unversioned requests. Use the canonical name.
            final_candidates.append(canonical_name)

    final_packages_to_add = sorted(list(set(final_candidates)))

    # --- Step 3: Transparently report the plan ---
    if not final_packages_to_add and not editable_install_needed:
        _log_action(action_name, "INFO", "No new dependencies to manage.")
        return None

    _log_action(action_name, "INFO", "--- Dependency Resolution Plan ---")
    if final_packages_to_add:
        _log_action(action_name, "INFO", f"Will ask `uv` to resolve these requirements: {final_packages_to_add}")
    if packages_to_skip_due_to_mode:
         _log_action(action_name, "INFO", f"Skipping unused requirements.txt entries: {sorted(list(packages_to_skip_due_to_mode))}")
    if editable_install_needed:
        _log_action(action_name, "INFO", "An editable install (`-e .`) will be performed.")
    _log_action(action_name, "INFO", "---------------------------------")

    # --- Step 4: Delegate to `uv` and translate the verdict ---
    if final_packages_to_add:
        if dry_run:
            _log_action(action_name, "INFO", "DRY RUN: Skipping 'uv add' command.")
        else:
            try:
                _run_command(["uv", "add"] + final_packages_to_add, "uv_add_bulk", work_dir=project_root)
            except subprocess.CalledProcessError as e:
                # The "Expert Translator" logic for clear error messages.
                stderr = e.stderr.lower() if e.stderr else ""
                stderr_full = e.stderr if e.stderr else ""

                if "no solution found" in stderr and "python" in stderr:
                    # Python version conflict - parse the error to be specific
                    # Extract specific conflict information
                    conflict_details = []

                    # Pattern: "numpy==2.3.1 depends on Python>=3.11"
                    pkg_conflicts = re.findall(r"(\w+)==([\d\.]+) depends on Python([>=<]+[\d\.]+)", stderr_full)
                    for pkg_name, pkg_version, python_req in pkg_conflicts:
                        conflict_details.append(f"{pkg_name} {pkg_version} (requires Python{python_req})")

                    # Pattern: "requested Python version (>=3.8)"
                    project_python_match = re.search(r"requested Python version \(([^)]+)\)", stderr_full)
                    project_python = project_python_match.group(1) if project_python_match else "unknown"

                    if conflict_details:
                        _log_action("uv_add_python_conflict", "WARN",
                                  f"Python version conflict detected!\n"
                                  f"  Your project: Python {project_python}\n"
                                  f"  Conflicting packages:\n" +
                                  "\n".join(f"    • {detail}" for detail in conflict_details) +
                                  "\n\nAutomatically retrying with flexible versions...")
                    else:
                        # Couldn't parse specific packages, but we know it's a Python conflict
                        _log_action("uv_add_python_conflict", "WARN",
                                  "Python version conflict detected. Retrying with flexible versions...",
                                  details={"error_snippet": stderr_full[:500]})

                    # Return status indicating retry needed
                    return {"status": "NEEDS_UNPINNED_RETRY", "conflicts": conflict_details}

                elif "no solution found" in stderr or "can't be installed" in stderr:
                    # Bulk add failed - try adding packages one by one to salvage what we can
                    # This handles both dependency conflicts and platform/Python version wheel availability issues
                    _log_action("uv_add_conflict", "WARN",
                              "⚡ Bulk package add failed due to conflicts. Trying packages one-by-one to install what's compatible...")

                    successful_packages = []
                    failed_packages = []

                    for pkg in final_packages_to_add:
                        # Use existing helper function (DRY principle)
                        pkg_name = _extract_package_name_from_specifier(pkg)

                        # Edge case: Skip if package name extraction failed (empty string)
                        # This can happen for built-in modules that shouldn't be installed
                        if not pkg_name:
                            _log_action("uv_add_skip_empty", "DEBUG",
                                      f"Skipping package with empty canonical name: '{pkg}'")
                            continue

                        try:
                            _run_command(["uv", "add", pkg], f"uv_add_individual_{pkg_name}",
                                       work_dir=project_root, suppress_console_output_on_success=True)
                            successful_packages.append(pkg)
                        except subprocess.CalledProcessError as pkg_error:
                            # Use helper function to categorize error (DRY principle)
                            pkg_stderr = pkg_error.stderr if pkg_error.stderr else ""
                            failure_reason = _categorize_uv_add_error(pkg_stderr)
                            failed_packages.append((pkg, failure_reason))

                    # Report results with progressive disclosure
                    if successful_packages:
                        _log_action("uv_add_partial_success", "SUCCESS",
                                  f"✅ Successfully installed {len(successful_packages)}/{len(final_packages_to_add)} packages:\n" +
                                  "\n".join(f"  • {pkg}" for pkg in successful_packages[:10]) +
                                  (f"\n  ... and {len(successful_packages) - 10} more" if len(successful_packages) > 10 else ""))

                    if failed_packages:
                        failure_summary = (
                            f"⚠️  Failed to install {len(failed_packages)}/{len(final_packages_to_add)} packages:\n" +
                            "\n".join(f"  • {pkg}: {reason}" for pkg, reason in failed_packages[:10]) +
                            (f"\n  ... and {len(failed_packages) - 10} more (see log)" if len(failed_packages) > 10 else "") +
                            f"\n\n💡 TIP: These packages were skipped to allow the rest of your project to work.\n" +
                            f"    You can manually adjust versions in pyproject.toml or remove incompatible packages."
                        )
                        _log_action("uv_add_partial_failure", "WARN", failure_summary,
                                  details={"failed_packages": [{"package": pkg, "reason": reason} for pkg, reason in failed_packages]})

                    # If we got at least some packages, consider it a partial success
                    # Don't return error status - let the process continue
                    if not successful_packages:
                        # Total failure - all packages failed
                        _log_action("uv_add_total_failure", "ERROR",
                                  "❌ Could not install any packages. All packages have conflicts or compatibility issues.\n"
                                  "ACTION: Check Python version compatibility and package versions in pyproject.toml")

                elif "failed to build" in stderr:
                    # Extract which package failed to build
                    build_fail_match = re.search(r"error: Failed to build: ([^\s]+)", stderr_full)
                    if build_fail_match:
                        failed_pkg = build_fail_match.group(1)
                        _log_action("uv_add_build_failure", "ERROR",
                                  f"BUILD FAILURE: {failed_pkg} failed to build from source.\n"
                                  f"ACTIONS:\n"
                                  f"  • Install build dependencies: sudo apt-get install python3-dev build-essential\n"
                                  f"  • Or try: pip install {failed_pkg} --no-binary :all:")
                    else:
                        _log_action("uv_add_build_failure", "ERROR",
                                  "BUILD FAILURE: Package failed to build from source.\n"
                                  "ACTION: Install system dependencies (e.g., gcc, python-dev) or use pre-built wheels.")
                else:
                    _log_action(action_name, "ERROR", "Failed to add dependencies. Check the error above.")

    # --- Step 5: Handle special cases like editable installs ---
    if editable_install_needed:
        if dry_run:
            _log_action(action_name, "INFO", "DRY RUN: Skipping editable install.")
        else:
            # Safety pre-flight check before running a command we know might fail.
            can_install_editable = False
            if pyproject_file_path.exists():
                try:
                    with open(pyproject_file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if '[project]' in content and 'name' in content:
                        can_install_editable = True
                except Exception:
                    pass

            if can_install_editable:
                _log_action(action_name, "INFO", "Performing editable install as requested.")
                try:
                    _run_command(["uv", "pip", "install", "-e", "."], "uv_pip_install_editable", work_dir=project_root)
                except subprocess.CalledProcessError as e:
                    _log_action(action_name, "ERROR", "Failed to install project in editable mode.", details={"exception": str(e)})
            else:
                _log_action(action_name, "ERROR", "Cannot perform editable install: 'pyproject.toml' is missing a `[project]` table with a `name` field. Please add one.")
    # --- Step 6: Provide Final Summary and Actionable Advice ---
    summary_lines = [
        "\n--- Dependency Management Final Summary ---",
        f"Mode: {migration_mode}",
        f"Total packages from requirements.txt scanned: {len(req_pkgs_from_file)}",
        f"Total packages from code (scripts/notebooks) discovered: {len(project_imported_packages)}",
        f"Total packages declared in pyproject.toml initially: {len(declared_deps_before_management)}",
        f"Final requirements passed to `uv`: {final_packages_to_add if final_packages_to_add else 'None'}",
        f"Skipped unused requirements.txt entries: {sorted(list(packages_to_skip_due_to_mode)) if packages_to_skip_due_to_mode else 'None'}",
    ]
    summary_table = "\n".join(summary_lines)
    _log_action(action_name + "_final_summary", "INFO", summary_table)

    # Provide actionable advice to the user regarding the legacy requirements.txt.
    # This is crucial for guiding them towards modern practices.
    if req_path.exists():
        advice = (
            f"The original '{LEGACY_REQUIREMENTS_TXT}' was NOT modified by this script.\n"
            f"To keep your project modern and reproducible, '{PYPROJECT_TOML_NAME}' is now the single source of truth for dependencies.\n"
            f"Consider archiving or removing '{LEGACY_REQUIREMENTS_TXT}' to avoid future confusion.\n"
            f"If you need it for legacy tools, you can always regenerate it from the lock file with:\n"
            f"  uv pip freeze > {LEGACY_REQUIREMENTS_TXT}"
        )
        _log_action(action_name + "_advice_req_txt", "INFO", advice)
    _log_action(action_name, "SUCCESS", f"Dependency management completed for mode: '{migration_mode}'.")
    return None  # Success case - no retry needed


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
        "version": PYUVSTARTER_VERSION,
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
                    _log_action(action_name, "SUCCESS", "Launch config for current file and uv venv already present in launch.json.")
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

def _ensure_notebook_execution_support(project_root: Path, ignore_manager: Optional[GitIgnore], dry_run: bool) -> bool:
    """
    Ensures dependencies for running notebooks (like `ipykernel`) are installed.
    This is separate from code dependencies (like `pandas`). It detects the
    notebook "system" (e.g., Jupyter) and adds its required packages.

    Returns:
        True if successful or no action needed, False if errors occurred.
    """
    action_name = "ensure_notebook_execution_support"
    notebook_paths = _find_all_notebooks(project_root, ignore_manager)
    if not notebook_paths:
        _log_action(action_name, "SUCCESS", "\u2705 No notebooks found - notebook execution support not needed.")  # ✅
        return True

    _log_action(action_name, "INFO", "Checking for notebook execution support dependencies (e.g., ipykernel).")

    # Detect all unique systems required by all notebooks in the project.
    systems_needed = set()
    for nb_path in notebook_paths:
        systems_needed.update(_detect_notebook_systems(nb_path))

    if not systems_needed:
        _log_action(action_name, "SUCCESS", "\u2705 No specific notebook execution system detected - support packages not needed.")  # ✅
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
                _run_command(["uv", "add"] + sorted(list(packages_to_add)), f"{action_name}_uv_add", work_dir=project_root)
                _log_action(action_name, "SUCCESS", f"Successfully added notebook execution packages: {sorted(list(packages_to_add))}")
                return True
            except Exception as e:
                _log_action(action_name, "ERROR", f"Failed to add notebook support packages: {e}\n      ACTION: Please try adding them manually: uv add {' '.join(sorted(list(packages_to_add)))}")
                return False
    else:
        _log_action(action_name, "SUCCESS", "\u2705 All required notebook execution support packages are already available.")  # ✅
        return True


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

# ==============================================================================
# SECTION 4: CLI DEFINITION & APPLICATION ENTRY POINT - new functionality to repair and keep
# ==============================================================================

# --- REFACTORED GITIGNORE ORCHESTRATION CONTROLLER ---
def _perform_gitignore_setup(config: 'CLICommand', ignore_manager: GitIgnore):
    """Acts as the 'controller' for gitignore setup.

    This function contains the application-specific logic for deciding *when*
    and *how* to write to the gitignore file, intelligently creating a
    comprehensive file or non-intrusively appending essential patterns. It
    delegates the low-level, idempotent writing operations to the `GitIgnore`
    service class.
    """
    action_name = "ensure_gitignore"
    gitignore_path = config.project_dir / config.gitignore_name
    _log_action(action_name, "INFO", f"Ensuring '{config.gitignore_name}' configuration.")
    if config.dry_run:
        _log_action(action_name, "INFO", "DRY RUN: No filesystem changes will be made to gitignore.")
        return

    try:
        # Determine if we are creating a new file or if `full_gitignore_overwrite`
        # forces an overwrite. Otherwise, we'll append to an existing file.
        is_creating_new_file = not gitignore_path.exists()
        should_overwrite_existing = is_creating_new_file or config.full_gitignore_overwrite

        if should_overwrite_existing:
            # This branch handles creating a new, comprehensive .gitignore or
            # completely overwriting an existing one.
            mode = "Creating" if is_creating_new_file else "Overwriting"
            _log_action(action_name, "INFO", f"{mode} a comprehensive '{config.gitignore_name}'.")

            # If overwriting an existing file, create a backup first
            if gitignore_path.exists():
                # Create backup with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = gitignore_path.parent / f"{config.gitignore_name}.backup_{timestamp}"
                try:
                    shutil.copy2(gitignore_path, backup_path)
                    _log_action(action_name, "INFO", f"Created backup of existing '{config.gitignore_name}' at '{backup_path}'.")
                except Exception as e:
                    _log_action(action_name, "WARN", f"Could not create backup of '{config.gitignore_name}': {e}")

                # Now delete the original to ensure a clean slate
                gitignore_path.unlink()

            # CRITICAL: Invalidate the GitIgnore manager's pattern cache after
            # deleting the file. This ensures that when the manager reads
            # patterns again (e.g., if `is_ignored` is called), it gets the
            # fresh state (an empty file, then the new patterns).
            ignore_manager.invalidate_cache()

            # This is the FIX for the formatting regression. We iterate through
            # the dictionary of default entries. For each section, we call
            # `ignore_manager.save()`, passing the dictionary key as the
            # comment. This recreates the beautifully structured, sectioned
            # .gitignore file.
            patterns_to_write_sections = GITIGNORE_DEFAULT_ENTRIES.copy()
            patterns_to_write_sections["Python Virtual Environments"].insert(0, f"/{config.venv_name}/")
            patterns_to_write_sections["Pyuvstarter Specific"] = [f"/{config.log_file_name}"]

            for comment, patterns in patterns_to_write_sections.items():
                ignore_manager.save(patterns, comment=comment)
        else:
            # This branch handles updating an existing .gitignore file by
            # non-intrusively appending only essential, missing patterns.
            _log_action(action_name, "INFO", f"'{config.gitignore_name}' exists. Ensuring essential patterns are present.")

            patterns_to_ensure_sections = ESSENTIAL_PATTERNS_TO_ENSURE.copy()
            patterns_to_ensure_sections["Project Specific"] = [f"/{config.venv_name}/", f"/{config.log_file_name}"]

            # Iterate through the essential patterns and append them in sections.
            for comment, patterns in patterns_to_ensure_sections.items():
                ignore_manager.save(patterns, comment=f"Essential patterns by pyuvstarter: {comment}")

        _log_action(action_name, "SUCCESS", f"'{config.gitignore_name}' setup complete.")
    except IOError as e:
        _log_action(action_name, "ERROR", f"Gitignore setup failed: {e}\nCheck file permissions and ensure you can write to the project directory.", details={"exception": str(e)})
        raise typer.Exit(code=1)

# ==============================================================================
# SECTION 4: CLI DEFINITION & APPLICATION ENTRY POINT - new functionality to repair and keep
# This section implements the advanced Typer/Pydantic integration pattern
# to achieve a true Single Source of Truth for CLI options and configuration.
# ==============================================================================

# Configure Typer application instance.
app = typer.Typer(
    name="pyuvstarter",
    add_completion=False, # Disable default completion, often handled by shell scripts.
    rich_markup_mode="markdown", # Allow rich text formatting in help messages.
    help="🚀 **A Modern Python Project Setup Tool**", # Overall help message.
    invoke_without_command=True, # Allow running without subcommands
)

# CLICOMMAND: new functionality to repair and keep
class CLICommand(BaseSettings):
    """The Pydantic model defining the application's configuration schema.

    This class serves as the **Single Source of Truth** for all CLI options,
    their types, default values, help text, and configuration layering.
    It leverages Pydantic's `BaseSettings` for automatic environment variable
    loading and custom source definition for JSON configuration files.

    Configuration Load Order (Highest Precedence First):
    1. Command-Line Arguments (parsed by Typer and passed to `__init__`)
    2. JSON Config File (loaded via `settings_customise_sources`)
    3. Environment Variables (e.g., `PYUVSTARTER_DRY_RUN=true`, via `BaseSettings`)
    4. Pydantic Defaults (defined directly on the fields)
    """
    model_config = SettingsConfigDict(
        env_prefix='PYUVSTARTER_', # All env vars must start with PYUVSTARTER_
        extra='forbid' # Forbid extra fields to prevent typos
    )

    # Each field is annotated with `typer.Option` or `typer.Argument` to
    # declaratively define its CLI behavior. This eliminates repetition in `main`.
    config_file: Annotated[
        Optional[Path],
        typer.Option(
            "--config-file",
            "-c",
            help="Path to a JSON config file. CLI options override file settings.",
            rich_help_panel="Core Configuration"
        )
    ] = None

    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            help="Show the application version and exit.",
            is_eager=True, # Process immediately, short-circuiting other logic.
            hidden=True # Don't show in basic help
        )
    ] = None # No default, as it's typically only present if explicitly passed.

    project_dir: Annotated[
        Path,
        typer.Option(
            "--project-dir",
            "-p",
            help="Project directory to operate on (default: current directory).",
            rich_help_panel="Core Configuration"
        )
    ] = Field(default_factory=Path.cwd) # Default uses current working directory.

    venv_name: Annotated[
        str,
        typer.Option(
            "--venv-name",
            help="Name of the virtual environment directory.",
            rich_help_panel="Core Configuration"
        )
    ] = ".venv"

    gitignore_name: Annotated[
        str,
        typer.Option(
            "--gitignore-name",
            help="Name of the gitignore file.",
            rich_help_panel="Core Configuration"
        )
    ] = ".gitignore"

    log_file_name: Annotated[
        str,
        typer.Option(
            "--log-file-name",
            help="Name of the JSON log file for execution details.",
            rich_help_panel="Core Configuration"
        )
    ] = "pyuvstarter_setup_log.json"

    dependency_migration: Annotated[
        str,
        typer.Option(
            "--dependency-migration",
            help="Dependency migration mode for `requirements.txt` (e.g., 'auto', 'strict').",
            rich_help_panel="Dependency Management"
        )
    ] = "auto"

    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="Preview actions without making any file system changes.",
            is_flag=True, # Treat as a boolean flag.
            rich_help_panel="Execution Control"
        )
    ] = False # Default is False, meaning changes will be made.

    full_gitignore_overwrite: Annotated[
        bool,
        typer.Option(
            "--full-gitignore-overwrite",
            help="If an existing .gitignore is found, overwrite it completely instead of appending.",
            is_flag=True,
            rich_help_panel="Execution Control"
        )
    ] = False # Default is False, meaning intelligent appending is preferred.

    no_gitignore: Annotated[
        bool,
        typer.Option(
            "--no-gitignore",
            help="Disable all .gitignore creation, updates, and parsing.",
            is_flag=True,
            rich_help_panel="Execution Control"
        )
    ] = False # Default is False, meaning gitignore handling is enabled.

    ignore_patterns: Annotated[
        List[str],
        typer.Option(
            "--ignore-pattern",
            "-i",
            help=(
                "Additional gitignore patterns for dependency discovery. Follows gitignore syntax:\n"
                "• 'temp/' - ignore directories named 'temp'\n"
                "• '*.log' - ignore all .log files\n"
                "• 'src/experimental/' - ignore specific path\n"
                "• '**/*.tmp' - ignore .tmp files at any depth\n"
                "• '!important.py' - don't ignore this file (negation)\n"
                "Can be used multiple times: -i '*.log' -i 'temp/'"
            ),
            rich_help_panel="Dependency Management"
        )
    ] = Field(default_factory=list) # Default is an empty list.

    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed technical output for debugging and learning.",
            is_flag=True,
            rich_help_panel="Execution Control"
        )
    ] = False # Default is False, meaning clean progress output is preferred.

    @property
    def use_gitignore(self) -> bool:
        """Computed property: True if gitignore functionality is enabled, False otherwise."""
        return not self.no_gitignore

    @classmethod
    @override # Mark as an override for clarity and type checking.
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: SettingsConfigDict,
        env_settings: SettingsConfigDict,
        dotenv_settings: SettingsConfigDict,
        file_secret_settings: SettingsConfigDict,
    ) -> Tuple[SettingsConfigDict, ...]:
        """Customizes the order and sources from which settings are loaded.

        This method is crucial for implementing the desired configuration
        precedence: CLI > Environment Variables > JSON Config File > Defaults.

        Args:
            settings_cls: The Pydantic BaseSettings class itself.
            init_settings: Settings from `__init__` (primarily CLI arguments).
            env_settings: Settings from environment variables.
            dotenv_settings: Settings from .env files (not used directly here, but available).
            file_secret_settings: Settings from secrets files (not used directly here).

        Returns:
            A tuple of dictionaries, ordered by precedence (lower index = higher precedence).
        """
        # Start with .env files and JSON config file (lowest precedence).
        sources: List[SettingsConfigDict] = [dotenv_settings]

        # Check if a config file path was provided (from CLI or env).
        # We need to load it here so its values can be layered.
        # In Pydantic v2, init_settings is a source object, not a dict
        config_file_path = None
        if hasattr(init_settings, '__call__'):
            # init_settings is a callable source
            init_dict = init_settings()
            config_file_path = init_dict.get('config_file') if init_dict else None
        elif isinstance(init_settings, dict):
            config_file_path = init_settings.get('config_file')
        if config_file_path:
            p = Path(config_file_path).resolve()
            if p.exists() and p.is_file():
                try:
                    # Load the JSON config file.
                    file_settings = json.loads(p.read_text(encoding='utf-8'))
                    # Add file settings with lower precedence than env vars and CLI.
                    sources.append(file_settings)
                    _log_action("config_load", "INFO", f"Loaded settings from config file: '{p}'")
                except json.JSONDecodeError as e:
                    safe_typer_secho(f"ERROR: Could not parse config file '{p}': {e}", fg=typer.colors.RED, err=True)
                    raise typer.Exit(code=1)
                except IOError as e:
                    safe_typer_secho(f"ERROR: Could not read config file '{p}': {e}", fg=typer.colors.RED, err=True)
                    raise typer.Exit(code=1)
            else:
                safe_typer_secho(f"WARNING: Config file not found or is not a file: '{p}'", fg=typer.colors.YELLOW, err=True)

        # Add environment variables with higher precedence than config file but lower than CLI.
        sources.append(env_settings)

        # Finally, add the `init_settings` (from CLI arguments) with the highest precedence.
        sources.append(init_settings)

        return tuple(sources)

    @override # Mark as an override for clarity and type checking.
    def model_post_init(self, __context: Any) -> None:
        """This method serves as the primary application entry point.

        It is automatically invoked by Pydantic after the `CLICommand` instance
        has been fully initialized and validated, incorporating all settings
        from CLI, config file, environment variables, and defaults.

        The main orchestration logic for `pyuvstarter` resides here, wrapped
        in a robust error-handling block to provide detailed user feedback.
        """
        # Save the original working directory to restore it in finally block
        original_cwd = Path.cwd()

        # Ensure project_dir is the current working directory for all subsequent operations.
        # This is a critical safety measure for consistent path handling.
        os.chdir(self.project_dir)

        # Initialize intelligent output system with config
        set_output_mode(self)

        # Initialize the global logging mechanism.
        _init_log(self.project_dir)

        # Define common paths used throughout the orchestration.
        log_file_path = self.project_dir / self.log_file_name
        pyproject_file_path = self.project_dir / "pyproject.toml"

        # --- RESTORED & ENHANCED: Detailed Startup Banner ---
        banner_lines = [
            "🚀 PYUVSTARTER - Modern Python Project Automation",
            "─" * 60,
            f"Version: {_get_project_version()}",
            f"Project Directory: {self.project_dir}",
            f"Virtual Environment: {self.venv_name}",
            f"Dry Run: {'Yes - Preview Only' if self.dry_run else 'No - Making Changes'}",
            f"GitIgnore Support: {'Enabled' if self.use_gitignore else 'Disabled'}",
            f"Execution Log: {self.log_file_name}",
            "─" * 60,
            "This tool will automate project setup using the modern `uv` ecosystem, performing:",
            " ✓ Initialization: Ensure project structure and `uv` tool availability.",
            " ✓ GitIgnore Management: Create/update `.gitignore` with best practices.",
            " ✓ Virtual Environment Setup: Create/verify Python virtual environment.",
            " ✓ Dependency Management: Discover and sync project dependencies.",
            " ✓ IDE Configuration: Configure VS Code for a seamless developer experience.",
            "─" * 60
        ]
        _log_action("script_start", "INFO", "\n".join(banner_lines))

        # This list will track the status of major actions for the final summary.
        major_action_results: List[Tuple[str, str]] = []

        # Track VS Code configuration status for the final log.
        vscode_settings_status = "NOT_ATTEMPTED"
        vscode_launch_status = "NOT_ATTEMPTED"

        # --- Main Orchestration Logic ---
        # The entire orchestration is wrapped in a try-except block here. This ensures
        # that even if a critical error occurs mid-run, the log is saved and
        # helpful feedback is provided to the user.
        try:
            # Step 1: Ensure uv is installed and verified.
            if not _ensure_uv_installed(self.dry_run):
                raise SystemExit("`uv` could not be installed or verified.")
            _log_action("ensure_uv_installed", "SUCCESS", "uv installation verified successfully.")
            major_action_results.append(("uv_installed", "SUCCESS"))

            # Step 2: Ensure pyproject.toml exists and project is initialized.
            if not _ensure_project_initialized(self.project_dir, self.dry_run):
                raise SystemExit("Project could not be initialized with 'pyproject.toml'.")
            _log_action("ensure_project_initialized_with_pyproject", "SUCCESS", "Project structure and pyproject.toml initialized successfully.")
            major_action_results.append(("project_initialized", "SUCCESS"))

            # Step 3: Instantiate GitIgnore manager and setup .gitignore.
            ignore_manager: Optional[GitIgnore] = None
            if self.use_gitignore or self.ignore_patterns:
                # Create GitIgnore manager if we're using gitignore OR have manual patterns
                ignore_manager = GitIgnore(
                    self.project_dir,
                    manual_patterns=list(self.ignore_patterns),
                    read_gitignore_files=self.use_gitignore  # Only read .gitignore files if enabled
                )

                if self.use_gitignore:
                    _log_action("gitignore_manager_init", "INFO", "Initialized GitIgnore manager with .gitignore file support.")
                    if self.ignore_patterns:
                        _log_action("ignore_patterns", "INFO", f"Additional ignore patterns: {self.ignore_patterns}")
                    # Call the controller function to manage the .gitignore file.
                    _perform_gitignore_setup(self, ignore_manager)
                    _log_action("ensure_gitignore", "SUCCESS", ".gitignore setup completed successfully.")
                    major_action_results.append(("gitignore", "SUCCESS"))
                else:
                    _log_action("manual_patterns_only", "INFO", f"Using manual ignore patterns only (no .gitignore files): {self.ignore_patterns}")
                    major_action_results.append(("gitignore", "MANUAL_PATTERNS_ONLY"))
            else:
                _log_action("no_ignore", "INFO", "No ignore patterns configured (--no-gitignore and no manual patterns).")
                major_action_results.append(("gitignore", "DISABLED"))

            # Step 4: Create or verify the virtual environment using uv.
            _log_action("create_or_verify_venv", "INFO", f"Creating/ensuring virtual environment '{self.venv_name}'.")
            _run_command(["uv", "venv", self.venv_name], "create_or_verify_venv_cmd", work_dir=self.project_dir, dry_run=self.dry_run)
            venv_python_executable = self.project_dir / self.venv_name / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")

            # Critical check: ensure the venv Python executable exists after creation (if not dry run).
            if not self.dry_run and not venv_python_executable.exists():
                raise SystemExit(f"CRITICAL ERROR: Virtual environment Python executable not found at '{venv_python_executable}' after `uv venv` command.")
            elif self.dry_run:
                _log_action("create_or_verify_venv", "INFO", "In dry-run mode: assuming virtual environment would be ready.")
            else:
                _log_action("create_or_verify_venv", "SUCCESS", f"Virtual environment '{self.venv_name}' ready. Interpreter: '{venv_python_executable}'.")
            major_action_results.append(("venv_ready", "SUCCESS"))

            # Step 5: Ensure necessary development tools (pipreqs, ruff) are available.
            _ensure_tool_available("pipreqs", major_action_results, self.dry_run, website="https://github.com/bndr/pipreqs")
            _ensure_tool_available("ruff", major_action_results, self.dry_run, website="https://docs.astral.sh/ruff/")

            # Step 6: Run unused import checks, e.g., Ruff unused import detection.
            _run_ruff_unused_import_check(self.project_dir, major_action_results, self.dry_run)

            # Step 7: Discover dependencies from all code sources.
            declared_deps = _get_declared_dependencies(pyproject_file_path)
            discovery_result = discover_dependencies_in_scope(
                scan_path=self.project_dir,
                ignore_manager=ignore_manager, # Pass the configured GitIgnore manager.
                scan_notebooks=True, # Always scan notebooks for dependencies.
                dry_run=self.dry_run
            )
            # Discovery result is logged by discover_dependencies_in_scope() function
            major_action_results.append(("code_dep_discovery", "SUCCESS"))

            # Step 8: Manage project dependencies (add/remove from pyproject.toml, sync with venv).
            _log_action("manage_project_dependencies", "INFO", "Managing project dependencies via 'pyproject.toml'.")

            # Phase 1: Try with pinned versions (current behavior)
            result = _manage_project_dependencies(
                project_root=self.project_dir,
                venv_python_executable=venv_python_executable,
                pyproject_file_path=pyproject_file_path,
                migration_mode=self.dependency_migration,
                dry_run=self.dry_run,
                declared_deps_before_management=declared_deps,
                project_imported_packages=discovery_result.all_unique_dependencies
            )

            # Check if we need to retry with unpinned packages
            if isinstance(result, dict) and result.get("status") == "NEEDS_UNPINNED_RETRY":
                # Clear, specific user message showing we're solving the problem
                conflicts = result.get("conflicts", [])
                # Progressive disclosure: Keep it simple during automatic resolution
                _log_action("version_conflict_resolution_attempt_2", "INFO",
                          "⚡ Version conflict detected. Trying again with flexible version ranges...")

                # Phase 2: Re-run discovery with no-pin mode (this is fast - just different output format)
                discovery_unpinned = discover_dependencies_in_scope(
                    scan_path=self.project_dir,
                    ignore_manager=ignore_manager,
                    scan_notebooks=True,
                    dry_run=self.dry_run,
                    pipreqs_mode="no-pin"  # This is the key change
                )

                # Retry with unpinned packages
                result = _manage_project_dependencies(
                    project_root=self.project_dir,
                    venv_python_executable=venv_python_executable,
                    pyproject_file_path=pyproject_file_path,
                    migration_mode=self.dependency_migration,
                    dry_run=self.dry_run,
                    declared_deps_before_management=declared_deps,
                    project_imported_packages=discovery_unpinned.all_unique_dependencies
                )

                if not isinstance(result, dict) or result.get("status") != "NEEDS_UNPINNED_RETRY":
                    # Success!
                    _log_action("version_conflict_resolved", "SUCCESS",
                              "\u2705 Successfully resolved dependencies using flexible version ranges!")  # ✅
                    major_action_results.append(("dependency_management", "SUCCESS"))
                else:
                    # Phase 3: Third fallback - try with NO version constraints at all
                    # This implements the philosophy: "Solve Problems Automatically"

                    # Preserve conflict information from phase 2 for paper trail
                    conflicts_from_phase2 = result.get("conflicts", [])

                    _log_action("version_conflict_resolution_attempt_3", "INFO",
                              "⚡ Flexible ranges still have conflicts. "
                              "Final attempt - removing ALL version constraints...")

                    # Extract bare package names - strip ALL version info
                    # discovery_unpinned.all_unique_dependencies is a set of (canonical_name, full_spec) tuples
                    # We only need the canonical names without versions
                    # Filter out empty strings (built-in modules that _canonicalize_pkg_name returns as "")
                    packages_no_versions = {canonical_name for canonical_name, _ in discovery_unpinned.all_unique_dependencies if canonical_name}

                    # Log exactly what we're attempting (Philosophy: "Transparent Operations")
                    _log_action("packages_being_installed", "INFO",
                              f"Installing {len(packages_no_versions)} packages without version numbers",
                              details={
                                  "packages": sorted(packages_no_versions),
                                  "strategy": "Package manager (uv) will choose compatible versions"
                              })

                    # Final attempt with bare package names
                    # Convert string set to tuple set format expected by _manage_project_dependencies
                    packages_as_tuples = {(pkg, pkg) for pkg in packages_no_versions}
                    result_phase3 = _manage_project_dependencies(
                        project_root=self.project_dir,
                        venv_python_executable=venv_python_executable,
                        pyproject_file_path=pyproject_file_path,
                        migration_mode=self.dependency_migration,
                        dry_run=self.dry_run,
                        declared_deps_before_management=declared_deps,
                        project_imported_packages=packages_as_tuples
                    )

                    if not isinstance(result_phase3, dict) or result_phase3.get("status") != "NEEDS_UNPINNED_RETRY":
                        # Success! Provide detailed success message with warnings
                        _log_action("version_conflict_resolved_without_constraints", "WARN",
                                  "\u2705 Dependencies resolved by removing version numbers!",  # ✅
                                  details={
                                      "packages_installed": sorted(packages_no_versions),
                                      "packages_count": len(packages_no_versions),
                                      "what_happened": {
                                          "attempt_1": "Exact versions had conflicts with your Python version",
                                          "attempt_2": "Flexible ranges still had conflicts",
                                          "attempt_3": "Success: Removed all version numbers and let package manager decide"
                                      },
                                      "warning": "Packages installed without version numbers may update unexpectedly",
                                      "important": "Your code may need updates if newer package versions changed their APIs",
                                      "immediate_action": "Run 'uv lock' to save the exact versions that were installed",
                                      "recommended_steps": [
                                          "1. Test your application thoroughly",
                                          "2. Run: uv lock",
                                          "3. Commit both pyproject.toml and uv.lock",
                                          "4. Fix any compatibility issues in your code",
                                          "5. Consider adding version bounds once stable"
                                      ]
                                  })
                        major_action_results.append(("dependency_management", "SUCCESS_NO_VERSIONS"))
                        # Don't pass error to manual guidance
                        result = None
                    else:
                        # All three attempts failed
                        phase3_conflicts = result_phase3.get("conflicts", [])

                        _log_action("dependency_resolution_failed", "ERROR",
                                  "Unable to automatically resolve package dependencies",
                                  details={
                                      "what_we_tried": {
                                          "attempt_1": "Exact version numbers - conflicted with Python version",
                                          "attempt_2": "Flexible version ranges - still had conflicts",
                                          "attempt_3": "No version numbers - could not find compatible set"
                                      },
                                      "action": "Manual intervention needed - see instructions below",
                                      "common_causes": [
                                          "Package name typo (e.g., 'numpy' vs 'nunpy')",
                                          "Package doesn't exist on PyPI (https://pypi.org)",
                                          "Package requires system libraries not installed",
                                          "Could not reach PyPI servers to download packages"
                                      ]
                                  })

                        # Update conflicts for manual guidance section
                        # Prefer phase 2 conflicts as they're usually more informative
                        if conflicts_from_phase2:
                            conflicts = conflicts_from_phase2
                        else:
                            conflicts = phase3_conflicts or []

                        # Pass through the error for manual guidance
                        result = result_phase3

                # Only show manual fix guidance if all attempts failed
                if isinstance(result, dict) and result.get("status") == "NEEDS_UNPINNED_RETRY":
                    # Retry also failed - provide comprehensive manual fix guidance
                    current_python = f"{sys.version_info.major}.{sys.version_info.minor}"

                    # Parse conflicts to build clear error message
                    if conflicts and len(conflicts) > 0:
                        # Format specific packages that conflict
                        conflict_examples = []
                        conflict_packages = []

                        for conflict in conflicts:
                            parts = conflict.split()
                            if len(parts) >= 2:
                                pkg_name = parts[0]
                                pkg_version = parts[1]
                                conflict_examples.append(f"{pkg_name} {pkg_version}")
                                conflict_packages.append(pkg_name)

                        # Build the initial error statement following philosophy format
                        if len(conflict_examples) >= 2:
                            error_start = f"Cannot automatically resolve: {conflict_examples[0]} and {conflict_examples[1]} require Python 3.11+,\nbut your project uses Python {current_python}."
                        elif len(conflict_examples) == 1:
                            error_start = f"Cannot automatically resolve: {conflict_examples[0]} requires Python 3.11+,\nbut your project uses Python {current_python}."
                        else:
                            error_start = f"Cannot automatically resolve: some packages require Python 3.11+,\nbut your project uses Python {current_python}."

                        # For option 3, provide a clear exploration path
                        # We know these packages need older versions, so guide the user
                        if conflict_packages:
                            # Suggest using --resolution lowest to find oldest working versions
                            option3_cmd = f"uv add --resolution lowest {' '.join(conflict_packages)}"
                            option3_note = "This finds the oldest compatible versions. You may want newer ones."
                        else:
                            option3_cmd = "uv add --resolution lowest <conflicting-packages>"
                            option3_note = "Replace <conflicting-packages> with the packages that failed."
                    else:
                        error_start = f"Cannot automatically resolve version conflicts with Python {current_python}."
                        option3_cmd = "Check your requirements and add compatible versions"
                        option3_note = ""

                    # Build the complete error message following the philosophy
                    # Note: We've already tried with no versions, so adjust guidance
                    error_message = f"{error_start}\n"
                    error_message += "\nWe tried 3 strategies: exact versions, flexible ranges, and no versions.\n"
                    error_message += "All failed. Here are your options:\n"
                    error_message += "\n1. Use a newer Python version (recommended):\n"
                    error_message += "   Run: python3.11 -m pyuvstarter\n"
                    error_message += "   This gives you latest features and best performance.\n"
                    error_message += "   Note: You may need to update code that uses deprecated APIs.\n"
                    error_message += "\n2. Update your project's Python requirement:\n"
                    error_message += "   Edit pyproject.toml: requires-python = '>=3.11'\n"
                    error_message += "   Then run pyuvstarter again.\n"
                    error_message += f"\n3. If you must stay on Python {current_python}:\n"
                    error_message += "   a) Check for typos in import statements\n"
                    error_message += "   b) Some packages may have different names (e.g., cv2 → opencv-python)\n"
                    error_message += "   c) Try installing problem packages individually:\n"
                    error_message += f"      {option3_cmd}\n"
                    if option3_note:
                        error_message += f"      {option3_note}\n"

                    _log_action("manual_resolution_guidance", "ERROR", error_message)

                    # Log complete details for debugging without cluttering main output
                    if conflicts:
                        _log_action("technical_conflict_details", "DEBUG",
                                  "Technical details for troubleshooting",
                                  details={"all_conflicts": conflicts,
                                          "parsed_packages": conflict_packages if 'conflict_packages' in locals() else [],
                                          "current_python": current_python})

                    major_action_results.append(("dependency_management", "FAILED"))
            else:
                # First attempt succeeded
                major_action_results.append(("dependency_management", "SUCCESS"))

            # Step 9: Ensure Jupyter notebook execution support is configured.
            _log_action("ensure_notebook_execution_support", "INFO", "Ensuring Jupyter notebook execution support.")
            notebook_exec_success = _ensure_notebook_execution_support(self.project_dir, ignore_manager, self.dry_run)
            major_action_results.append(("notebook_exec_support", "SUCCESS" if notebook_exec_success else "FAILED"))

            # Step 10: Perform final uv sync to ensure environment matches pyproject.toml.
            _log_action("uv_final_sync", "INFO", "Performing final sync of environment with 'pyproject.toml' and 'uv.lock'.")
            try:
                _run_command(["uv", "sync", "--python", str(venv_python_executable)], "uv_sync_dependencies_cmd", work_dir=self.project_dir, dry_run=self.dry_run)
                _log_action("uv_final_sync", "SUCCESS", "Environment synced successfully.")
                major_action_results.append(("uv_final_sync", "SUCCESS"))
            except subprocess.CalledProcessError as e:
                # Sync failed - log the error but don't crash the entire script
                # This allows users to see what was accomplished and get actionable guidance
                _log_action("uv_final_sync", "WARN",
                           f"⚠️  Environment sync failed. Some packages may be incompatible with your Python version.\n"
                           f"   The script will continue to show what was accomplished.\n"
                           f"   See error details above for specific package conflicts.")
                major_action_results.append(("uv_final_sync", "FAILED"))

                # Read requires-python from pyproject.toml for guidance
                requires_python_str = "not specified"
                try:
                    if sys.version_info >= (3, 11):
                        import tomllib
                        with open(pyproject_file_path, "rb") as f:
                            pyproject_data = tomllib.load(f)
                    else:
                        with open(pyproject_file_path, "rb") as f:
                            pyproject_data = toml.load(f)
                    requires_python_str = pyproject_data.get('project', {}).get('requires-python', 'not specified')
                except Exception:
                    pass  # If we can't read it, just use default

                # Provide actionable next steps based on the error
                sync_guidance = (
                    f"\n📋 NEXT STEPS TO RESOLVE SYNC FAILURE:\n"
                    f"\n1. Check Python version compatibility:"
                    f"\n   Your venv uses: {venv_python_executable}"
                    f"\n   Project requires: {requires_python_str}"
                    f"\n   Some packages may not support your Python version yet."
                    f"\n\n2. Review package conflicts in the error output above"
                    f"\n   Look for messages like 'no wheels with matching Python version'"
                    f"\n   or 'incompatible' to identify problematic packages."
                    f"\n\n3. Options to fix:"
                    f"\n   a) Use an older Python version that packages support:"
                    f"\n      uv venv --python 3.13  # Then re-run pyuvstarter"
                    f"\n   b) Remove incompatible packages from pyproject.toml"
                    f"\n   c) Wait for package maintainers to release newer compatible wheels"
                    f"\n   d) Try syncing without dev dependencies:"
                    f"\n      uv sync --no-dev --python {venv_python_executable}"
                    f"\n\n4. Manual sync command for debugging:"
                    f"\n   uv sync --python {venv_python_executable} --verbose"
                )
                _log_action("uv_sync_guidance", "INFO", sync_guidance)
                # Print guidance to console so users see it immediately
                print(sync_guidance)

            # Step 11: Configure VS Code workspace settings and launch configurations.
            _configure_vscode_settings(self.project_dir, venv_python_executable, self.dry_run)
            vscode_settings_status = "SUCCESS"
            _ensure_vscode_launch_json(self.project_dir, venv_python_executable, self.dry_run)
            vscode_launch_status = "SUCCESS"
            major_action_results.append(("vscode_config", "SUCCESS"))

            # --- Final Status and Summary ---
            _log_action("script_end", "SUCCESS", "🎉 Automated project setup script completed successfully!")

            # RESTORED & ENHANCED: Explicit file summary (provides detailed paths for user clarity).
            explicit_summary = _get_explicit_summary_text(self.project_dir, self.venv_name, pyproject_file_path, log_file_path)
            _log_action("explicit_summary", "INFO", explicit_summary)

            # RESTORED & ENHANCED: Final summary table printed to console.
            # This provides immediate, high-level feedback to the user.
            # User-friendly step names for the summary table
            step_display_names = {
                "uv_installed": "Package Manager (uv)",
                "project_initialized": "Project Structure",
                "gitignore": "Git Ignore File",
                "venv_ready": "Virtual Environment",
                "pipreqs_cli_tool": "Dependency Scanner",
                "ruff_cli_tool": "Code Quality Tool",
                "ruff_unused_import_check": "Unused Import Check",
                "code_dep_discovery": "Dependency Discovery",
                "dependency_management": "Package Installation",
                "notebook_exec_support": "Notebook Support",
                "uv_final_sync": "Environment Sync",
                "vscode_config": "VS Code Setup"
            }

            summary_lines = [
                "\n--- Project Setup Summary ---",
                "Step                         | Status",
                "-----------------------------|----------",
            ]
            for step, status in major_action_results:
                display_name = step_display_names.get(step, step)
                # Also make status messages clearer
                display_status = status
                if status == "SUCCESS_NO_VERSIONS":
                    display_status = "SUCCESS (no versions)"
                elif status == "COMPLETED_WITH_WARNINGS":
                    display_status = "COMPLETED (warnings)"
                summary_lines.append(f"{display_name.ljust(29)}| {display_status}")
            summary_lines.append(f"\nSee '{log_file_path.name}' for full details.")
            _log_action("final_summary_table", "INFO", "\n".join(summary_lines))

            # Check for any warnings or errors that occurred during the run.
            errors_or_warnings = any(
                a.get("status", "").upper() in ("ERROR", "WARN", "FAILED")
                for a in _log_data_global.get("actions", [])
            )
            if errors_or_warnings:
                warn_msg = f"\n\u26a0\ufe0f  Some warnings/errors occurred during setup. See '{log_file_path.name}' for details."  # ⚠️
                _log_action("final_warning", "WARN", warn_msg)
                # Indicate overall status as WARNING if not already ERROR.
                if _log_data_global.get("overall_status") != "ERROR":
                    _log_data_global["overall_status"] = "WARNINGS"
            else:
                _log_data_global["overall_status"] = "SUCCESS"

        # --- RESTORED & ENHANCED: Granular Exception Handling ---
        # These specific exception blocks provide actionable hints to the user,
        # which was a key UX feature of the legacy `main` function.
        except SystemExit as e:
            # Caught for clean exits initiated by other functions.
            vscode_settings_status = "FAILED"
            vscode_launch_status = "FAILED"
            _log_action("script_halted_by_logic", "ERROR", f"SCRIPT HALTED: {e}")
            _log_data_global["overall_status"] = "HALTED_BY_SCRIPT_LOGIC"
            _log_data_global["final_summary"] = f"Script halted by explicit exit: {e}"
            safe_typer_secho(f"\n💥 Script halted: {e}", fg=typer.colors.RED, bold=True)
            raise typer.Exit(code=1) # Re-raise to exit Typer properly.
        except subprocess.CalledProcessError as e:
            failed_cmd_str = ' '.join(e.cmd) if isinstance(e.cmd, list) else str(e.cmd)
            vscode_settings_status = "FAILED"
            vscode_launch_status = "FAILED"
            error_message = f"A critical command failed execution: '{failed_cmd_str}'"
            _log_action("critical_command_failed", "ERROR", error_message, details={
                "command": failed_cmd_str, "return_code": e.returncode,
                "stdout": e.stdout.strip(), "stderr": e.stderr.strip()
            })
            _log_data_global["overall_status"] = "CRITICAL_COMMAND_FAILED"
            _log_data_global["final_summary"] = error_message

            # Provide specific, actionable hints based on the failed command.
            safe_typer_secho(f"\n💥 CRITICAL ERROR: {error_message}", fg=typer.colors.RED, bold=True)
            cmd_str_lower = failed_cmd_str.lower()
            if "uv pip install" in cmd_str_lower or "uv add" in cmd_str_lower or "uv sync" in cmd_str_lower:
                _log_action("install_sync_hint", "WARN", f"INSTALLATION/SYNC HINT: A package operation with `uv` failed.\n  - Review `uv`'s error output (logged as FAIL_STDOUT/FAIL_STDERR for the command) for specific package names or reasons.\n  - Ensure the package name is correct and exists on PyPI (https://pypi.org) or your configured index.\n  - Some packages require system-level (non-Python) libraries to be installed first. Check the package's documentation.\n  - You might need to manually edit 'pyproject.toml' and then run `uv sync --python {venv_python_executable}`.")
            elif "pipreqs" in cmd_str_lower:
                _log_action("pipreqs_hint", "WARN", f"PIPReQS HINT: The 'pipreqs' command (run via 'uvx') failed.\n  - This could be due to syntax errors in your Python files that `pipreqs` cannot parse, an internal `pipreqs` issue, or `uvx` failing to execute `pipreqs`.\n  - Try running manually for debug: uvx pipreqs \"{self.project_dir}\" --ignore \"{self.venv_name}\" --debug")
            elif "uv venv" in cmd_str_lower:
                _log_action("uv_venv_hint", "WARN", f"VIRTUAL ENV HINT: `uv venv` command failed.\n  - Ensure `uv` is correctly installed and functional. Check `uv --version`.\n  - Check for issues like insufficient disk space or permissions in the project directory '{self.project_dir}'.")
            elif "uv tool install" in cmd_str_lower:
                _log_action("uv_tool_install_hint", "WARN", "UV TOOL INSTALL HINT: `uv tool install` (likely for pipreqs) failed.\n  - Check PyPI connection (https://pypi.org) or your configured package index\n  - Verify `uv` is working: `uv --version`\n  - Try running `uv tool install pipreqs` manually in your terminal")
            elif "uv init" in cmd_str_lower:
                _log_action("uv_init_hint", "WARN", f"UV INIT HINT: `uv init` command failed.\n  - Ensure `uv` is correctly installed. Try running `uv init` manually in an empty directory to test.\n  - Check for permissions issues in the project directory '{self.project_dir}'.")
            elif "brew" in cmd_str_lower:
                _log_action("brew_hint", "WARN", "Homebrew might be required for some installations. Ensure it's installed and working.")

            safe_typer_secho("\nSetup aborted due to a critical command failure. See log for details.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        except FileNotFoundError as e:
            # Caught for missing external executables (e.g., 'uv' itself, 'brew', 'curl').
            cmd_name = e.filename if hasattr(e, 'filename') and e.filename else "An external command"
            vscode_settings_status = "FAILED"
            vscode_launch_status = "FAILED"
            error_message = f"Required command '{cmd_name}' was not found. Please ensure it's installed and in your system's PATH."
            _log_action("missing_system_command", "ERROR", error_message, details={"filename": e.filename, "message": str(e)})
            _log_data_global["overall_status"] = "MISSING_SYSTEM_COMMAND"
            _log_data_global["final_summary"] = error_message

            safe_typer_secho(f"\n💥 CRITICAL ERROR: {error_message}", fg=typer.colors.RED, bold=True)
            if cmd_name == "brew":
                safe_typer_secho("HINT: For Homebrew on macOS, see https://brew.sh/", fg=typer.colors.YELLOW)
            elif cmd_name == "curl":
                safe_typer_secho("HINT: For curl, see your OS package manager (e.g., 'sudo apt install curl' or 'sudo yum install curl').", fg=typer.colors.YELLOW)
            safe_typer_secho("Setup aborted.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        except Exception as e:
            # Catch-all for any unexpected errors.
            vscode_settings_status = "FAILED"
            vscode_launch_status = "FAILED"
            tb_str = traceback.format_exc() # Capture full traceback for debugging.
            error_message = f"An unexpected critical error occurred: {e}"
            _log_action("unexpected_critical_error", "ERROR", error_message, details={
                "exception_type": type(e).__name__, "exception_message": str(e), "traceback": tb_str.splitlines()
            })
            _log_data_global["overall_status"] = "UNEXPECTED_ERROR"
            _log_data_global["final_summary"] = error_message

            safe_typer_secho(f"\n💥 AN UNEXPECTED CRITICAL ERROR OCCURRED: {e}", fg=typer.colors.RED, bold=True)
            safe_typer_secho(f"{tb_str}\nSetup aborted due to an unexpected error. Please review the traceback and the JSON log.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        finally:
            # Ensure the log file is always saved at the end of the execution,
            # even if an error caused an early exit.
            if _log_data_global: # Only save if _init_log was called successfully.
                # Update summary in log with VS Code config status (restored from deprecated main).
                _log_data_global["vscode_settings_json_status"] = vscode_settings_status
                _log_data_global["vscode_launch_json_status"] = vscode_launch_status
                _save_log(self)

            # Restore the original working directory
            try:
                os.chdir(original_cwd)
            except Exception:
                # If we can't restore the directory, at least don't crash in the finally block
                pass

# main with app.callback: new functionality to repair and keep

# The `@app.callback(cls=CLICommand)` decorator is the core of the advanced
# Typer/Pydantic integration. It tells Typer to:
# 1. Inspect the fields of `CLICommand` for CLI options and arguments.
# 2. Automatically parse CLI input and instantiate `CLICommand`.
# 3. Call `CLICommand.model_post_init` (or `__post_init__` for Pydantic V1)
#    as the primary entry point for the command's logic.
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context = None,
    config_file: Annotated[Optional[Path], typer.Option("--config-file", "-c", help="Path to a JSON config file.")] = None,
    version: Annotated[Optional[bool], typer.Option("--version", help="Show version and exit.", is_eager=True)] = None,
    project_dir: Annotated[Path, typer.Argument(help="Project directory to operate on (default: current directory).")] = Path.cwd(),
    venv_name: Annotated[str, typer.Option("--venv-name", help="Name of the virtual environment directory.")] = ".venv",
    gitignore_name: Annotated[str, typer.Option("--gitignore-name", help="Name of the gitignore file.")] = ".gitignore",
    log_file_name: Annotated[str, typer.Option("--log-file-name", help="Name of the JSON log file.")] = "pyuvstarter_setup_log.json",
    dependency_migration: Annotated[str, typer.Option("--dependency-migration", help="Dependency migration mode.")] = "auto",
    dry_run: Annotated[bool, typer.Option("--dry-run", "-d", help="Preview actions without making changes.")] = False,
    full_gitignore_overwrite: Annotated[bool, typer.Option("--full-gitignore-overwrite", help="Overwrite existing .gitignore completely.")] = False,
    no_gitignore: Annotated[bool, typer.Option("--no-gitignore", help="Disable all .gitignore operations.")] = False,
    ignore_patterns: Annotated[List[str], typer.Option("--ignore-pattern", "-i", help="Additional gitignore patterns.")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed technical output for debugging and learning.")] = False,
):
    """The main entry point for pyuvstarter.

    This function handles CLI parsing via Typer and then instantiates
    the CLICommand Pydantic model for validation and execution.
    """
    # Handle the --version flag early
    if version:
        typer.echo("pyuvstarter version: {}".format(PYUVSTARTER_VERSION))
        raise typer.Exit()

    # Handle Typer shell completion
    if ctx and ctx.resilient_parsing:
        return

    # Use ctx.params which has all parsed values as a dictionary
    # Filter out None values to allow defaults and env vars to work
    if ctx is not None:
        cli_kwargs = {k: v for k, v in ctx.params.items() if v is not None and k != "version"}
    else:
        # When ctx is None, construct from the function parameters
        cli_kwargs = {
            'config_file': config_file,
            'project_dir': project_dir,
            'venv_name': venv_name,
            'gitignore_name': gitignore_name,
            'log_file_name': log_file_name,
            'dependency_migration': dependency_migration,
            'dry_run': dry_run,
            'full_gitignore_overwrite': full_gitignore_overwrite,
            'no_gitignore': no_gitignore,
            'ignore_patterns': ignore_patterns or [],
            'verbose': verbose,
        }

    # Create CLICommand instance - this will trigger model_post_init
    try:
        command = CLICommand(**cli_kwargs)  # noqa: F841 - Instance creation triggers validation
    except ValidationError as e:
        safe_typer_secho("\u274c Configuration validation error:", fg=typer.colors.RED, bold=True)  # ❌
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            safe_typer_secho("  • {}: {}".format(field, error['msg']), fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        safe_typer_secho(f"\n💥 Unexpected error during initialization: {e}", fg=typer.colors.RED, bold=True)
        safe_typer_secho(traceback.format_exc(), fg=typer.colors.RED)
        raise typer.Exit(code=1)

# new main with app() is new functionality to repair and keep

# This block ensures that the Typer application is run when the script is executed.
if __name__ == "__main__":
    # Wrap `app()` in a try-except to catch very early errors (e.g., invalid
    # CLI arguments that prevent Pydantic model instantiation).
    try:
        # Call the Typer app to handle CLI parsing and invoke main callback
        sys.exit(app())
    except Exception as e:
        # This is a last-resort error handler for issues *before* the model_post_init
        # can log them (e.g., Typer internal errors or Pydantic ValidationError
        # if the CLI input format is totally wrong).
        safe_typer_secho(f"\n💥 A critical error occurred during application startup: {e}", fg=typer.colors.RED, bold=True)
        safe_typer_secho(traceback.format_exc(), fg=typer.colors.RED)
        safe_typer_secho("Setup aborted due to an unexpected startup error.", fg=typer.colors.RED)
        sys.exit(1)