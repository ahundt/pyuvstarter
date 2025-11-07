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
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from unittest.mock import Mock, patch

# Add parent directory to path for pyuvstarter imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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
        temp_dir = Path(tempfile.mkdtemp(prefix=f"pyuvstarter_test_{fixture.name}_"))
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
            self._cleanup_dir(temp_dir)
            if temp_dir in self.temp_dirs:
                self.temp_dirs.remove(temp_dir)

    def setup_test_environment_enhanced(self, test_project_path: Path) -> Path:
        """Enhanced version of setup_test_environment that returns ProjectFixture.

        This method is compatible with existing test patterns but provides
        additional functionality for fixture-based testing.
        """
        project_name = test_project_path.name
        temp_project_path = self.temp_dirs[0] / project_name if self.temp_dirs else Path(tempfile.mkdtemp(prefix="pyuvstarter_test_"))

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
        timeout: int = 120,
        capture_output: bool = True,
        env: Dict[str, str] = None,
        dry_run: bool = True,
        verbose: bool = True
    ) -> subprocess.CompletedProcess:
        """Run pyuvstarter command with standardized parameters.

        Enhanced version of run_pyuvstarter from ImportFixingTestSuite
        with additional options and better error handling.
        """
        if args is None:
            args = []

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

        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=self.pyuvstarter_path.parent,  # Run from project root (preserve existing behavior)
            timeout=timeout,
            env=process_env
        )

    def run_pyuvstarter_legacy_compatible(
        self,
        project_path: Path,
        dry_run: bool = True
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
                canonical_expected = expected_pkg.lower().replace('-', '_').replace('.', '')
                found = any(
                    canonical_expected in dep.lower().replace('-', '_').replace('.', '')
                    for dep in deps
                )
                if not found:
                    raise AssertionError(f"Expected package '{expected_pkg}' not found in dependencies: {deps}")

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

                expected_path = str(venv_path / "bin" / "python")
                if os.name == 'nt':  # Windows
                    expected_path = str(venv_path / "Scripts" / "python.exe")

                actual_path = settings["python.defaultInterpreterPath"]
                if not actual_path.endswith("python") and not actual_path.endswith("python.exe"):
                    raise AssertionError(f"Invalid Python interpreter path: {actual_path}")

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
                    "source": ["import pandas as pd\nimport numpy as np\n!pip install matplotlib"],
                    "metadata": {},
                    "outputs": []
                }
            ]

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
        temp_dir = Path(tempfile.mkdtemp(prefix="pyuvstarter_test_"))

    project_name = test_project_path.name
    temp_project_path = temp_dir / project_name

    # Copy the entire test project
    if test_project_path.exists():
        if temp_project_path.exists():
            shutil.rmtree(temp_project_path)
        shutil.copytree(test_project_path, temp_project_path)

    return temp_project_path

def run_pyuvstarter_compatible(project_path: Path, dry_run: bool = True, pyuvstarter_path: Path = None) -> Tuple[int, str, str]:
    """Backward compatible run_pyuvstarter function.

    Provides exact compatibility with existing test signatures.
    """
    if pyuvstarter_path is None:
        pyuvstarter_path = Path(__file__).parent.parent / "pyuvstarter.py"

    compat_executor = PyuvstarterCommandExecutor(pyuvstarter_path)
    return compat_executor.run_pyuvstarter_legacy_compatible(project_path, dry_run)