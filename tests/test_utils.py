#!/usr/bin/env python3
"""
Shared testing utilities for pyuvstarter comprehensive test suite.

Provides reusable infrastructure for:
- Temporary directory management with automatic cleanup
- Project fixture creation for various scenarios
- Validation helpers for pyuvstarter output and behavior
- Mock factories for external dependencies
- Cross-platform compatibility utilities

These utilities are designed to ENHANCE existing tests without breaking them.
Existing test patterns are preserved and can optionally use these utilities.
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
import stat
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Add parent directory to path for pyuvstarter imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def _read_log_data(project_dir: Path) -> Optional[Dict[str, Any]]:
    """Read pyuvstarter JSON log safely, returning None on any error.

    Returns:
        Dict with log data if successful, None if file doesn't exist or can't be read.
        On error, prints diagnostic message to help debug log reading issues.
    """
    log_file = project_dir / "pyuvstarter_setup_log.json"
    if not log_file.exists():
        # Not an error - log may not exist for some test scenarios
        return None
    try:
        with open(log_file, 'r') as f:
            data = json.load(f)
            # Validate basic structure
            if not isinstance(data, dict):
                print(f"WARNING: Log file exists but is not a dict: {log_file}")
                return None
            return data
    except json.JSONDecodeError as e:
        print(f"WARNING: Log file has invalid JSON: {log_file}: {e}")
        return None
    except Exception as e:
        print(f"WARNING: Could not read log file: {log_file}: {e}")
        return None

def _add_project_file_listing(error_parts: List[str], project_dir: Path) -> None:
    """Add project file count and names to error_parts list (in-place)."""
    try:
        py_files = list(project_dir.glob("**/*.py"))
        ipynb_files = list(project_dir.glob("**/*.ipynb"))
        error_parts.append(f"Project files: {len(py_files)} .py files, {len(ipynb_files)} .ipynb files")
        if ipynb_files:
            error_parts.append(f"Notebook files: {[f.name for f in ipynb_files]}")
    except Exception:
        pass

def _add_log_actions(error_parts: List[str], project_dir: Path, action_filter: str = None, max_actions: int = 5) -> None:
    """Add JSON log action diagnostics to error_parts list (in-place).

    Never fails silently - always provides diagnostic information about what's available.
    If specific action not found, shows what actions ARE available for debugging.
    """
    log_data = _read_log_data(project_dir)
    if not log_data:
        error_parts.append("LOG DIAGNOSTIC: pyuvstarter_setup_log.json not found or unreadable")
        return

    actions = log_data.get("actions")
    if not actions:
        error_parts.append(f"LOG DIAGNOSTIC: JSON log has no 'actions' key. Available keys: {list(log_data.keys())}")
        return

    if not isinstance(actions, list):
        error_parts.append(f"LOG DIAGNOSTIC: 'actions' is not a list, it's a {type(actions).__name__}")
        return

    if len(actions) == 0:
        error_parts.append("LOG DIAGNOSTIC: 'actions' list is empty")
        return

    # ALWAYS show action sequence for debugging test failures
    error_parts.append(f"\n═══ ACTION SEQUENCE ({len(actions)} total) ═══")
    for i, action in enumerate(actions[-40:], start=max(1, len(actions) - 39)):  # Show last 40 actions
        if isinstance(action, dict):
            action_name = action.get("action", "UNKNOWN")
            status = action.get("status", "UNKNOWN")
            error_parts.append(f"  {i:3}. {action_name:55} [{status}]")
    error_parts.append("═" * 70)

    if action_filter:
        # Find specific action type (e.g., "pipreqs_discover")
        # Prioritize __exec actions (subprocess calls) which have command details
        filtered = [a for a in actions if isinstance(a, dict) and action_filter in a.get("action", "")]

        if not filtered:
            # Filter found nothing - provide diagnostic information
            available_actions = [a.get("action", "NO_ACTION_KEY") for a in actions if isinstance(a, dict)]
            unique_actions = sorted(set(available_actions))
            error_parts.append(f"LOG DIAGNOSTIC: No actions matching filter '{action_filter}'")
            error_parts.append(f"Available action types ({len(unique_actions)}): {unique_actions[:20]}")
            # Fallback: show last few actions for context
            error_parts.append(f"Last {min(3, len(actions))} actions for context:")
            for action in actions[-3:]:
                if isinstance(action, dict):
                    error_parts.append(f"  - {action.get('action', 'unknown')}: {action.get('status', 'unknown')}")
            return

        # Prefer actions with non-empty details (usually __exec subprocess actions)
        actions_with_details = [a for a in filtered if a.get("details") and len(a.get("details", {})) > 0]
        last_action = actions_with_details[-1] if actions_with_details else filtered[-1]

        # Always show what we found
        if actions_with_details:
            error_parts.append(f"Found {len(filtered)} matching actions, {len(actions_with_details)} with details")

        error_parts.append(f"{action_filter} action: {last_action.get('action', 'unknown')}")
        error_parts.append(f"Status: {last_action.get('status', 'unknown')}")
        if last_action.get("message"):
            error_parts.append(f"Message: {last_action['message']}")
        if "details" in last_action and last_action["details"]:
            error_parts.append(f"Details: {json.dumps(last_action['details'], indent=2)}")
        else:
            error_parts.append("Details: (none available for this action)")
    else:
        # Get last N actions for general context
        last_actions = actions[-max_actions:] if len(actions) > max_actions else actions
        error_parts.append(f"Last {len(last_actions)} actions: {json.dumps(last_actions, indent=2)}")

def format_pyuvstarter_error(test_name: str, result, project_dir: Path) -> str:
    """Format comprehensive error message for pyuvstarter execution failures.

    For timeout errors (returncode -1), stderr already contains full diagnostic info,
    so it's returned directly. For other errors, shows last 300 chars of output.
    """
    # Check if this is already a formatted timeout error (stderr starts with "TIMEOUT")
    if result.returncode == -1 and result.stderr and result.stderr.startswith("TIMEOUT"):
        # Timeout errors already have full diagnostics in stderr, return directly
        return f"{test_name}: PyUVStarter failed (exit code {result.returncode})\n{result.stderr}"

    # For other errors, show truncated output (backward compatible)
    error_parts = [
        f"{test_name}: PyUVStarter failed (exit code {result.returncode})",
        f"Stdout (last 300 chars): {result.stdout[-300:] if result.stdout else 'EMPTY'}",
        f"Stderr (last 300 chars): {result.stderr[-300:] if result.stderr else 'EMPTY'}"
    ]
    _add_log_actions(error_parts, project_dir)
    return "\n".join(error_parts)

def format_dependency_mismatch(test_name: str, expected_pkg: str, dependencies: list, project_dir: Path) -> str:
    """Format comprehensive error message when expected package not found in dependencies."""
    error_parts = [
        f"{test_name}: Expected package '{expected_pkg}' not found in dependencies: {dependencies}"
    ]
    _add_log_actions(error_parts, project_dir, action_filter="pipreqs_discover")
    _add_project_file_listing(error_parts, project_dir)
    return "\n".join(error_parts)

@dataclass
class ProjectFixture:
    """Represents a test project structure with files and metadata."""
    name: str
    files: Dict[str, str]  # filepath -> content
    directories: List[str]  # directory paths
    expected_packages: List[str]  # packages that should be discovered
    is_package: bool = True
    has_notebooks: bool = False
    has_relative_imports: bool = False
    expected_error: Optional[str] = None  # For error scenario tests

class TempProjectManager:
    """Manages temporary project directories with automatic cleanup.

    This provides an enhanced alternative to manual tempfile management
    used in existing tests, but doesn't replace existing functionality.
    """

    def __init__(self):
        self.temp_dirs = []
        self.original_dir = Path.cwd()

    @contextmanager
    def create_temp_project(self, fixture: ProjectFixture):
        """Create temporary project directory from fixture with automatic cleanup.

        This provides an enhanced version of the setup_test_environment method
        used in existing ImportFixingTestSuite, but is fully backward compatible.
        """
        # Create temp directory with valid package name for uv init
        # Use suffix to ensure directory name always ends with alphanumeric (PEP 508 requirement)
        # Pattern: pyuvstarter_test_fixture_name_randomchars_test (readable and valid)
        temp_dir = Path(tempfile.mkdtemp(prefix=f"pyuvstarter_test_{fixture.name}_", suffix="_test"))
        self.temp_dirs.append(temp_dir)

        try:
            # Create directory structure
            for directory in fixture.directories:
                dir_path = temp_dir / directory
                dir_path.mkdir(parents=True, exist_ok=True)

            # Create files with content
            for filepath, content in fixture.files.items():
                file_path = temp_dir / filepath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding='utf-8')

            yield temp_dir

        finally:
            # Preserve logs before cleanup if in multi-run/debugging mode
            iteration = os.environ.get('PYUVSTARTER_CURRENT_ITERATION')
            if iteration and iteration != '0':
                # Find and preserve pyuvstarter log files before cleanup
                log_files = list(temp_dir.glob('*pyuvstarter*log*.json'))
                if log_files:
                    # Copy to project root with iteration-specific names
                    project_root = Path(__file__).parent.parent
                    for log_file in log_files:
                        dest_name = f"iteration_{iteration.zfill(2)}_{fixture.name}_{log_file.name}"
                        try:
                            shutil.copy2(log_file, project_root / dest_name)
                        except Exception:
                            pass  # Don't fail tests if log preservation fails

            self._cleanup_dir(temp_dir)
            if temp_dir in self.temp_dirs:
                self.temp_dirs.remove(temp_dir)

    def setup_test_environment_enhanced(self, test_project_path: Path) -> Path:
        """Enhanced version of setup_test_environment that returns ProjectFixture.

        This method is compatible with existing test patterns but provides
        additional functionality for fixture-based testing.
        """
        project_name = test_project_path.name
        # Create temp directory with valid package name (suffix ensures alphanumeric ending)
        temp_project_path = self.temp_dirs[0] / project_name if self.temp_dirs else Path(tempfile.mkdtemp(prefix="pyuvstarter_test_", suffix="_test"))

        if not self.temp_dirs:
            self.temp_dirs.append(temp_project_path)

        # Copy the entire test project (preserve existing behavior)
        if test_project_path.exists():
            if temp_project_path.exists():
                shutil.rmtree(temp_project_path)
            shutil.copytree(test_project_path, temp_project_path)

        return temp_project_path

    def _cleanup_dir(self, path: Path):
        """Recursively clean up directory with permission handling.

        Enhanced cleanup that handles Windows permission issues better
        than basic shutil.rmtree.
        """
        if not path.exists():
            return

        # Handle Windows permission issues
        if os.name == 'nt':
            def change_permissions(action):
                for root, dirs, files in os.walk(path):
                    for name in files + dirs:
                        full_path = os.path.join(root, name)
                        try:
                            os.chmod(full_path, action)
                        except OSError:
                            pass

            # Try to make files writable
            change_permissions(stat.S_IWRITE)

        try:
            shutil.rmtree(path)
        except (OSError, PermissionError):
            # Final cleanup attempt
            import time
            time.sleep(0.1)
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)

    def cleanup_all(self):
        """Clean up all managed temporary directories."""
        for temp_dir in self.temp_dirs[:]:
            self._cleanup_dir(temp_dir)
        self.temp_dirs.clear()

    def __del__(self):
        """Cleanup on object destruction."""
        self.cleanup_all()

class PyuvstarterCommandExecutor:
    """Standardized pyuvstarter command execution with output capture.

    This provides an enhanced version of the run_pyuvstarter method
    used in existing tests, with additional error handling and flexibility.
    """

    def __init__(self, pyuvstarter_path: Optional[Path] = None):
        if pyuvstarter_path is None:
            pyuvstarter_path = Path(__file__).parent.parent / "pyuvstarter.py"
        self.pyuvstarter_path = pyuvstarter_path

    def run_pyuvstarter(
        self,
        project_dir: Path,
        args: List[str] = None,
        timeout: int = None,
        capture_output: bool = True,
        env: Dict[str, str] = None,
        dry_run: bool = False,
        verbose: bool = True
    ) -> subprocess.CompletedProcess:
        """Run pyuvstarter command with standardized parameters.

        Enhanced version of run_pyuvstarter from ImportFixingTestSuite
        with additional options and better error handling.

        Timeout defaults to PYUVSTARTER_TEST_TIMEOUT env var or 240 seconds.
        """
        if args is None:
            args = []

        # Allow timeout to be overridden via environment variable
        if timeout is None:
            timeout = int(os.environ.get("PYUVSTARTER_TEST_TIMEOUT", "240"))

        cmd = [
            "uv", "run",
            "pyuvstarter",
        ]

        # Add dry-run flag only if specified
        if dry_run:
            cmd.append("--dry-run")

        # Add verbose flag
        if verbose:
            cmd.append("--verbose")

        # Add additional arguments
        cmd.extend(args)

        # Add project directory
        cmd.append(str(project_dir.resolve()))

        # Set up environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Ensure uv is available
        process_env["PATH"] = self._ensure_uv_in_path(process_env.get("PATH", ""))

        try:
            return subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                cwd=project_dir.resolve(),  # Run from test project directory to avoid contamination
                timeout=timeout,
                env=process_env
            )
        except subprocess.TimeoutExpired as e:
            # Capture complete diagnostic information for timeout
            cmd_str = " ".join(cmd)

            # Collect all relevant environment variables for reproduction
            env_vars = {
                "UV_PYTHON": process_env.get("UV_PYTHON", "not set"),
                "PYUVSTARTER_TEST_PYTHON": process_env.get("PYUVSTARTER_TEST_PYTHON", "not set"),
                "PYUVSTARTER_TEST_OS": process_env.get("PYUVSTARTER_TEST_OS", "not set"),
                "PATH": process_env.get("PATH", "not set")[:200] + "..." if len(process_env.get("PATH", "")) > 200 else process_env.get("PATH", "not set"),
            }

            # Decode output from bytes if necessary to avoid b'...' representation
            stdout_str = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode('utf-8', errors='replace') if e.stdout else "")
            stderr_str = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode('utf-8', errors='replace') if e.stderr else "")

            # Detect common timeout causes from output
            timeout_indicators = []
            combined_output = (stdout_str + "\n" + stderr_str).lower()

            if "no compatible wheel" in combined_output or "no matching distribution" in combined_output:
                timeout_indicators.append("⚠️  WHEEL UNAVAILABILITY: Package may be building from source (very slow)")
            if "building wheel" in combined_output or "running setup.py" in combined_output:
                timeout_indicators.append("⚠️  BUILDING FROM SOURCE: Compiling package instead of using pre-built wheel")
            if "network" in combined_output or "connection" in combined_output or "timeout" in combined_output:
                timeout_indicators.append("⚠️  NETWORK ISSUE: Connection problems detected")
            if "error:" in combined_output and ("rust" in combined_output or "cargo" in combined_output):
                timeout_indicators.append("⚠️  RUST COMPILATION: Package requires Rust compiler (can be very slow)")
            if "downloading" in combined_output or "resolving" in combined_output:
                timeout_indicators.append("⚠️  PACKAGE DOWNLOAD: May be downloading large ML packages (~GB)")

            # Show more context (last 1000 chars) and format for readability
            stdout_display = stdout_str[-1000:] if stdout_str else "No stdout"
            stderr_display = stderr_str[-1000:] if stderr_str else "No stderr"

            error_parts = [
                f"\n{'='*70}",
                f"⏱️  TEST TIMEOUT: Process exceeded {timeout}s limit",
                f"{'='*70}",
            ]

            # Add detected timeout indicators first (most actionable info)
            if timeout_indicators:
                error_parts.append("\n🔍 DETECTED TIMEOUT CAUSES:")
                for indicator in timeout_indicators:
                    error_parts.append(f"   {indicator}")
                error_parts.append("\n💡 SUGGESTED ACTIONS:")
                if any("WHEEL" in ind or "SOURCE" in ind or "RUST" in ind for ind in timeout_indicators):
                    error_parts.append("   • Use packages with pre-built wheels for your Python version")
                    error_parts.append("   • Check package availability: https://pypi.org/<package>/")
                    error_parts.append("   • For CI: Install build dependencies or use different Python version")
                if any("NETWORK" in ind for ind in timeout_indicators):
                    error_parts.append("   • Check internet connection and PyPI status")
                    error_parts.append("   • Try again with better network or use package mirror")
                if any("DOWNLOAD" in ind for ind in timeout_indicators):
                    error_parts.append("   • Large ML packages can take 5-20min on slow connections")
                    error_parts.append("   • Consider increasing timeout or using smaller test packages")
                error_parts.append("")

            error_parts.extend([
                f"\n📋 REPRODUCTION DETAILS:",
                f"   Working directory: {project_dir.resolve()}",
                f"\n   Command (copy-paste):",
                f"   {cmd_str}",
                f"\n   Command (exact args for debugging):",
                f"   {cmd}",
                f"\n   Environment:",
            ])
            for k, v in env_vars.items():
                error_parts.append(f"      {k}={v}")
            error_parts.extend([
                f"\n📤 OUTPUT (last 1000 chars of stdout):",
                f"{'-'*70}",
                stdout_display,
                f"{'-'*70}",
                f"\n📤 ERRORS (last 1000 chars of stderr):",
                f"{'-'*70}",
                stderr_display,
                f"{'-'*70}",
            ])
            # Add recent log actions to identify what was executing when timeout occurred
            _add_log_actions(error_parts, project_dir, max_actions=5)

            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-1,
                stdout=stdout_str,
                stderr="\n".join(error_parts)
            )

    def run_pyuvstarter_legacy_compatible(
        self,
        project_path: Path,
        dry_run: bool = False
    ) -> Tuple[int, str, str]:
        """Legacy-compatible method matching existing ImportFixingTestSuite signature.

        This method maintains exact compatibility with existing test patterns
        while providing enhanced error handling under the hood.
        """
        result = self.run_pyuvstarter(
            project_dir=project_path,
            dry_run=dry_run,
            timeout=120  # Preserve existing timeout
        )

        return result.returncode, result.stdout, result.stderr

    def _ensure_uv_in_path(self, current_path: str) -> str:
        """Ensure uv is available in PATH."""
        # Try common uv installation paths
        common_paths = [
            os.path.expanduser("~/.cargo/bin"),
            os.path.expanduser("~/.local/bin"),
            "/usr/local/bin",
        ]

        path_dirs = current_path.split(os.pathsep) if current_path else []

        for uv_path in common_paths:
            if uv_path not in path_dirs and os.path.exists(uv_path):
                path_dirs.append(uv_path)

        return os.pathsep.join(path_dirs)

class OutputValidator:
    """Validates pyuvstarter output and created files.

    Provides enhanced validation methods that complement existing
    test assertions without replacing them.
    """

    @staticmethod
    def validate_log_file(project_dir: Path, log_filename: str = "pyuvstarter_setup_log.json") -> Dict[str, Any]:
        """Load and validate pyuvstarter setup log file."""
        log_path = project_dir / log_filename

        if not log_path.exists():
            raise AssertionError(f"Expected log file not found: {log_path}")

        try:
            log_content = log_path.read_text(encoding='utf-8')
            log_data = json.loads(log_content)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise AssertionError(f"Invalid log file format: {e}")

        # Validate required fields
        required_fields = ["actions", "project_dir", "start_time"]
        for field in required_fields:
            if field not in log_data:
                raise AssertionError(f"Missing required field in log: {field}")

        return log_data

    @staticmethod
    def _map_import_to_package_names(import_name: str) -> List[str]:
        """Map import names to possible package names.

        Uses the same comprehensive mapping as pyuvstarter for consistency.
        This mapping is extracted from pyuvstarter's _canonicalize_pkg_name function.
        """
        # Comprehensive mapping from pyuvstarter
        mapping = {
            # Machine Learning & Data Science
            "sklearn": "scikit-learn",
            "cv2": "opencv-python",
            "cv": "opencv-python",
            "skimage": "scikit-image",

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
            "tkinter": "",  # Built-in
            "PyQt5": "pyqt5",
            "PyQt6": "pyqt6",
            "wx": "wxpython",

            # System & OS
            "win32api": "pywin32",
            "win32com": "pywin32",
            "pywintypes": "pywin32",
            "pythoncom": "pywin32",

            # Testing & Mocking
            "mock": "mock",
            "_pytest": "pytest",

            # Async & Concurrency
            "asyncio": "",  # Built-in

            # Typing
            "typing_extensions": "typing-extensions",

            # Additional common mismatches
            "Crypto": "pycryptodome",
            "Cryptodome": "pycryptodomex",
            "jwt": "pyjwt",
            "git": "gitpython",
            "serial": "pyserial",
            "usb": "pyusb",
            "docx": "python-docx",
            "pptx": "python-pptx",
            "fitz": "pymupdf",
            "PyPDF2": "pypdf2",
            "websocket": "websocket-client",
            "Levenshtein": "python-levenshtein",
            "slugify": "python-slugify",
            "multipart": "python-multipart",
            "memcache": "python-memcached",
            "ldap": "python-ldap",
            "nacl": "pynacl",
            "etree": "lxml",
            "_cffi_backend": "cffi",
            "googleapiclient": "google-api-python-client",
            "apiclient": "google-api-python-client",
        }

        # Additional common package mappings for testing
        additional_mappings = {
            'sklearn.ensemble': 'scikit-learn',
            'sklearn.model_selection': 'scikit-learn',
            'sklearn.svm': 'scikit-learn',
            'matplotlib.pyplot': 'matplotlib',
            'ipywidgets': 'ipywidgets',
            'ipykernel': 'ipykernel',
            'notebook': 'notebook',
            'jupyter': 'jupyter',
            'torch': 'torch',
            'transformers': 'transformers',
            'torchvision': 'torchvision',
            'accelerate': 'accelerate',
            'datasets': 'datasets',
            'tensorflow': 'tensorflow',
            'scipy': 'scipy',
            'seaborn': 'seaborn',
            'plotly': 'plotly',
            'dash': 'dash',
            'requests': 'requests',
            'flask': 'flask',
            'numpy': 'numpy',
            'pandas': 'pandas',
        }

        # Combine mappings
        mapping.update(additional_mappings)

        name_lower = import_name.lower()

        # Check for exact mappings
        if name_lower in mapping:
            canonical = mapping[name_lower]
            if canonical:  # Skip empty strings (built-ins)
                return [canonical]
            else:
                return []  # Built-in module

        # Check base import name
        base_import = import_name.split('.')[0].lower()
        if base_import in mapping:
            canonical = mapping[base_import]
            if canonical:
                return [canonical]
            else:
                return []

        # Default: return original import name
        return [import_name.lower()]

    @staticmethod
    def validate_pyproject_toml(project_dir: Path, expected_packages: List[str] = None) -> Dict[str, Any]:
        """Validate pyproject.toml content and dependencies.

        Enhanced validation that can be used alongside existing test checks.
        """
        try:
            import tomllib
        except ImportError:
            # Fallback for older Python versions
            try:
                import tomli as tomllib
            except ImportError:
                raise ImportError("tomllib or tomli required for TOML parsing")

        pyproject_path = project_dir / "pyproject.toml"

        if not pyproject_path.exists():
            raise AssertionError("pyproject.toml not created")

        try:
            with open(pyproject_path, 'rb') as f:
                pyproject_data = tomllib.load(f)
        except Exception as e:
            raise AssertionError(f"Invalid pyproject.toml format: {e}")

        # Validate project metadata
        if "project" not in pyproject_data:
            raise AssertionError("Missing [project] section in pyproject.toml")

        project = pyproject_data["project"]
        if "dependencies" not in project:
            project["dependencies"] = []

        # Check expected packages if provided
        if expected_packages:
            deps = [dep.split('[')[0].split('=')[0].split('>')[0].split('<')[0].strip()
                    for dep in project["dependencies"]]

            for expected_pkg in expected_packages:
                # Get possible package names for this import
                possible_package_names = OutputValidator._map_import_to_package_names(expected_pkg)

                found = False
                for possible_pkg in possible_package_names:
                    canonical_possible = possible_pkg.lower().replace('-', '_').replace('.', '')
                    for dep in deps:
                        canonical_dep = dep.lower().replace('-', '_').replace('.', '')
                        if canonical_possible in canonical_dep or canonical_dep in canonical_possible:
                            found = True
                            break
                    if found:
                        break

                if not found:
                    raise AssertionError(format_dependency_mismatch("validate_pyproject_toml", expected_pkg, deps, project_dir))

        return pyproject_data

    @staticmethod
    def validate_vscode_config(project_dir: Path, venv_path: Path):
        """Validate VS Code configuration files."""
        vscode_dir = project_dir / ".vscode"

        if not vscode_dir.exists():
            # VS Code config is optional, so don't raise error
            return

        # Check settings.json
        settings_path = vscode_dir / "settings.json"
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text(encoding='utf-8'))
                if "python.defaultInterpreterPath" not in settings:
                    raise AssertionError("Python interpreter path not configured in VS Code settings")

                actual_path = settings["python.defaultInterpreterPath"]

                # Validate path ends with correct Python executable for platform
                expected_suffix = "python.exe" if os.name == 'nt' else "python"
                if not actual_path.endswith(expected_suffix):
                    raise AssertionError(
                        f"Python interpreter path should end with '{expected_suffix}', got: {actual_path}"
                    )

            except json.JSONDecodeError as e:
                raise AssertionError(f"Invalid VS Code settings.json: {e}")

        # Check launch.json
        launch_path = vscode_dir / "launch.json"
        if launch_path.exists():
            try:
                launch_config = json.loads(launch_path.read_text(encoding='utf-8'))
                if "configurations" not in launch_config:
                    raise AssertionError("No configurations found in launch.json")

                # Validate at least one Python configuration exists
                python_configs = [
                    config for config in launch_config["configurations"]
                    if config.get("type") == "python"
                ]
                if not python_configs:
                    raise AssertionError("No Python debug configuration found")

            except json.JSONDecodeError as e:
                raise AssertionError(f"Invalid VS Code launch.json: {e}")

class MockFactory:
    """Factory for creating mock objects and test data.

    Provides reusable mock creation for consistent testing scenarios.
    """

    @staticmethod
    def create_mock_uv_response(package_name: str, version: str = "1.0.0") -> Dict[str, Any]:
        """Create mock uv package installation response."""
        return {
            "package": package_name,
            "version": version,
            "installed": True,
            "dependencies": []
        }

    @staticmethod
    def create_mock_notebook_json(cells: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create mock Jupyter notebook JSON structure.

        Creates realistic notebook JSON for testing notebook parsing
        without requiring actual Jupyter installation.
        """
        if cells is None:
            cells = [
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "source": ["import pandas as pd\nimport numpy as np\n!pip install matplotlib"],
                    "metadata": {},
                    "outputs": []
                }
            ]
        else:
            # Ensure all code cells have execution_count field (required by nbformat)
            execution_counter = 1
            for cell in cells:
                if cell.get("cell_type") == "code":
                    if "execution_count" not in cell:
                        cell["execution_count"] = execution_counter
                        execution_counter += 1
                    elif cell["execution_count"] is None:
                        cell["execution_count"] = execution_counter
                        execution_counter += 1

        return {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.9.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }

    @staticmethod
    def create_requirements_txt_content(packages: List[str], comments: bool = True) -> str:
        """Create requirements.txt content with optional comments."""
        lines = []
        for pkg in packages:
            if comments:
                lines.append(f"# Package: {pkg}")
            lines.append(pkg)
            if comments:
                lines.append("# Additional comment")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def create_basic_project_fixture(name: str, packages: List[str] = None) -> ProjectFixture:
        """Create a basic project fixture for common testing scenarios."""
        if packages is None:
            packages = ["pandas", "numpy"]

        imports = "\n".join([f"import {pkg}" for pkg in packages])

        return ProjectFixture(
            name=name,
            files={
                "main.py": f"""
{imports}

def main():
    print("Hello from {name}")
    return True

if __name__ == "__main__":
    main()
""",
                "requirements.txt": MockFactory.create_requirements_txt_content(packages)
            },
            directories=[],
            expected_packages=packages,
            is_package=True
        )

# Global instances for easy access (backward compatible)
temp_manager = TempProjectManager()
executor = PyuvstarterCommandExecutor()
validator = OutputValidator()
mock_factory = MockFactory()

# Backward compatibility functions
def setup_test_environment_compatible(test_project_path: Path, temp_dir: Path = None) -> Path:
    """Backward compatible setup_test_environment function.

    Provides drop-in compatibility for existing test code while
    offering enhanced functionality.
    """
    if temp_dir is None:
        # Create temp directory with valid package name (suffix ensures alphanumeric ending)
        temp_dir = Path(tempfile.mkdtemp(prefix="pyuvstarter_test_", suffix="_test"))

    project_name = test_project_path.name
    temp_project_path = temp_dir / project_name

    # Copy the entire test project
    if test_project_path.exists():
        if temp_project_path.exists():
            shutil.rmtree(temp_project_path)
        shutil.copytree(test_project_path, temp_project_path)

    return temp_project_path

def run_pyuvstarter_compatible(project_path: Path, dry_run: bool = False, pyuvstarter_path: Path = None) -> Tuple[int, str, str]:
    """Backward compatible run_pyuvstarter function.

    Provides exact compatibility with existing test signatures.
    """
    if pyuvstarter_path is None:
        pyuvstarter_path = Path(__file__).parent.parent / "pyuvstarter.py"

    compat_executor = PyuvstarterCommandExecutor(pyuvstarter_path)
    return compat_executor.run_pyuvstarter_legacy_compatible(project_path, dry_run)