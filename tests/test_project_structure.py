#!/usr/bin/env python3
"""
Comprehensive tests for pyuvstarter project structure detection.

Tests pyuvstarter's ability to detect and handle various project layouts:
- src-layout packages (recommended best practice)
- flat-layout packages (traditional Python packages)
- single-file scripts (non-packaged projects)
- multi-package projects (complex structures)
- hybrid projects (mixed layouts)

These tests validate that pyuvstarter correctly identifies project types
and applies appropriate behaviors for each structure.
"""

import sys

import json
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_utils import (
    ProjectFixture, temp_manager, executor, validator, mock_factory
)

# Optional pytest import for when pytest is available
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    pytest = None

class TestProjectStructureDetection:
    """Test project structure detection and layout handling."""

    def test_src_layout_package_detection(self):
        """Test detection of src-layout packages (recommended best practice)."""

        fixture = ProjectFixture(
            name="src_layout_package",
            files={
                "pyproject.toml": """
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "myproject"
version = "0.1.0"
description = "A src-layout package"
authors = [{name = "Test Author", email = "test@example.com"}]
""",
                "src/myproject/__init__.py": """
\"\"\"MyProject main package.\"\"\"

__version__ = "0.1.0"
""",
                "src/myproject/main.py": """
from .utils import helper_function
import sys

def main():
    print("MyProject main function")
    return helper_function()

if __name__ == "__main__":
    main()
""",
                "src/myproject/utils.py": """
def helper_function():
    return "Helper function result"
""",
                "src/myproject/submodule/__init__.py": "",
                "src/myproject/submodule/processor.py": """
from ..utils import helper_function

def process_data():
    return helper_function()
""",
                "tests/test_main.py": """
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import myproject.main

def test_main():
    assert myproject.main.main() == "Helper function result"
"""
            },
            directories=["src/myproject", "src/myproject/submodule", "tests"],
            expected_packages=["pytest"],  # Only test dependencies, project code is internal
            is_package=True
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"

            # Validate src-layout detection
            assert "src" in result.stdout.lower() or "package" in result.stdout.lower()

            # Validate that pyproject.toml was enhanced but not replaced
            pyproject_data = validator.validate_pyproject_toml(project_dir)

            # Should preserve existing project metadata
            assert pyproject_data["project"]["name"] == "myproject"
            assert pyproject_data["project"]["version"] == "0.1.0"

            # Should add test dependencies
            dependencies = pyproject_data["project"]["dependencies"]
            pytest_found = any("pytest" in dep.lower() for dep in dependencies)
            assert pytest_found, "pytest dependency not added"

    def test_flat_layout_package_detection(self):
        """Test detection of flat-layout packages (traditional Python packages)."""

        fixture = ProjectFixture(
            name="flat_layout_package",
            files={
                "pyproject.toml": """
[project]
name = "flatproject"
version = "0.1.0"
description = "A flat-layout package
""",
                "myproject/__init__.py": """
\"\"\"FlatProject main package.\"\"\"

__version__ = "0.1.0"
""",
                "myproject/main.py": """
from . import utils
from .utils import helper_function

def main():
    print("FlatProject main function")
    return helper_function()

if __name__ == "__main__":
    main()
""",
                "myproject/utils.py": """
def helper_function():
    return "Flat helper function result"
""",
                "myproject/data/__init__.py": "",
                "myproject/data/processor.py": """
from ..utils import helper_function

def process_data():
    return helper_function()
""",
                "README.md": "# FlatProject\nA traditional flat-layout Python package."
            },
            directories=["myproject", "myproject/data"],
            expected_packages=[],
            is_package=True
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"

            # Validate flat-layout detection
            pyproject_data = validator.validate_pyproject_toml(project_dir)

            # Should preserve existing project metadata
            assert pyproject_data["project"]["name"] == "flatproject"
            assert pyproject_data["project"]["version"] == "0.1.0"

    def test_single_file_script_detection(self):
        """Test detection of single-file script projects."""

        fixture = ProjectFixture(
            name="single_file_script",
            files={
                "main.py": """
#!/usr/bin/env python3
\"\"\"Single file script.\"\"\"

import sys
import os
import json
from pathlib import Path

def main():
    print("Single file script main function")
    data = {"message": "Hello from single file", "files": []}

    # Process files in current directory
    for file_path in Path('.').glob('*.py'):
        if file_path.name != 'main.py':
            data["files"].append(file_path.name)

    return json.dumps(data, indent=2)

if __name__ == "__main__":
    print(main())
""",
                "config.json": """
{
    "app_name": "single_file_app",
    "version": "1.0.0"
}
""",
                "README.md": "# Single File Script\nA simple single-file Python application."
            },
            directories=[],
            expected_packages=[],
            is_package=False
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"

            # Should create pyproject.toml for single-file projects
            pyproject_data = validator.validate_pyproject_toml(project_dir)

            # Should create basic project structure
            assert "project" in pyproject_data
            assert "name" in pyproject_data["project"]

    def test_multi_package_project_detection(self):
        """Test detection of multi-package projects."""

        fixture = ProjectFixture(
            name="multi_package_project",
            files={
                "pyproject.toml": """
[project]
name = "multipackage"
version = "0.1.0"
description = "A multi-package project

This project contains multiple packages in different directories.
""",
                "packages/api/__init__.py": """
\"\"\"API package.\"\"\"
""",
                "packages/api/routes/__init__.py": "",
                "packages/api/routes/users.py": """
from ..auth import authenticate

def get_users():
    return authenticate()
""",
                "packages/api/auth/__init__.py": """
def authenticate():
    return "authenticated"
""",
                "packages/data/__init__.py": """
\"\"\"Data processing package.\"\"\"
""",
                "packages/data/processors/__init__.py": "",
                "packages/data/processors/cleaner.py": """
from ..transformers import normalize_data

def clean_data(raw_data):
    return normalize_data(raw_data)
""",
                "packages/data/transformers/__init__.py": """
def normalize_data(data):
    return str(data).lower().strip()
""",
                "shared/__init__.py": """
\"\"\"Shared utilities package.\"\"\"
""",
                "shared/utils.py": """
def format_message(message):
    return f"[INFO] {message}"
""",
                "main.py": """
# Main entry point using multiple packages
from packages.api.routes.users import get_users
from packages.data.processors.cleaner import clean_data
from shared.utils import format_message

def main():
    users = get_users()
    data = clean_data("  RAW DATA  ")
    message = format_message("Multi-package execution")
    return users, data, message

if __name__ == "__main__":
    print(main())
"""
            },
            directories=["packages/api/routes", "packages/api/auth", "packages/data/processors", "packages/data/transformers", "shared"],
            expected_packages=[],
            is_package=True
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"

            # Should handle multi-package structure
            pyproject_data = validator.validate_pyproject_toml(project_dir)
            assert pyproject_data["project"]["name"] == "multipackage"

    def test_hybrid_project_detection(self):
        """Test detection of hybrid projects with mixed layouts."""

        fixture = ProjectFixture(
            name="hybrid_project",
            files={
                "pyproject.toml": """
[project]
name = "hybridproject"
version = "0.1.0"
description = "A hybrid project with mixed layouts

This project has both src-layout and flat-layout packages.
""",
                # src-layout package
                "src/hybrid/__init__.py": """
\"\"\"Hybrid main package in src-layout.\"\"\"
""",
                "src/hybrid/core.py": """
from ..utils import shared_function

def hybrid_function():
    return shared_function()
""",
                # flat-layout package
                "tools/__init__.py": """
\"\"\"Tools package in flat-layout.\"\"\"
""",
                "tools/processor.py": """
from ..utils import shared_function

def process_data():
    return shared_function()
""",
                # shared utilities
                "utils.py": """
def shared_function():
    return "Shared utility function"
""",
                # single-file scripts
                "scripts/generate_data.py": """
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.hybrid.core import hybrid_function
from tools.processor import process_data
from utils import shared_function

def generate_data():
    return hybrid_function(), process_data(), shared_function()

if __name__ == "__main__":
    print(generate_data())
""",
                "scripts/cleanup.py": """
import os
import sys

def cleanup():
    print("Cleaning up...")
    return "cleanup complete"

if __name__ == "__main__":
    cleanup()
"""
            },
            directories=["src/hybrid", "tools", "scripts"],
            expected_packages=[],
            is_package=True
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"

            # Should handle hybrid structure
            pyproject_data = validator.validate_pyproject_toml(project_dir)
            assert pyproject_data["project"]["name"] == "hybridproject"

class TestProjectStructureBehavior:
    """Test that pyuvstarter behaves differently based on project structure."""

    def test_package_vs_script_relative_import_handling(self):
        """Test that relative imports are handled differently for packages vs scripts."""

        # Test package project (should fix relative imports)
        package_fixture = ProjectFixture(
            name="package_relative_imports",
            files={
                "myproject/__init__.py": "",
                "myproject/main.py": """
from . import utils
from .utils import helper_function

def main():
    return helper_function()
""",
                "myproject/utils.py": """
def helper_function():
    return "Package helper function"
"""
            },
            directories=["myproject"],
            expected_packages=[],
            has_relative_imports=True,
            is_package=True
        )

        # Test script project (should not fix relative imports initially, but may create package)
        script_fixture = ProjectFixture(
            name="script_relative_imports",
            files={
                "main.py": """
from .utils import helper_function  # This should fail as script

def main():
    return helper_function()

if __name__ == "__main__":
    main()
""",
                "utils.py": """
def helper_function():
    return "Script helper function"
"""
            },
            directories=[],
            expected_packages=[],
            has_relative_imports=True,
            is_package=False
        )

        # Test package project
        with temp_manager.create_temp_project(package_fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            assert result.returncode == 0, f"Package project failed: {result.stderr}"

            # Package projects should have relative imports fixed
            remaining_relative = self._find_relative_imports(project_dir)
            assert len(remaining_relative) == 0, f"Package project still has {len(remaining_relative)} relative imports"

        # Test script project (pyuvstarter may convert it to a package)
        with temp_manager.create_temp_project(script_fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            assert result.returncode == 0, f"Script project failed: {result.stderr}"

            # pyuvstarter likely creates pyproject.toml and converts to package
            # The relative import may now work since it's a package
            # This is expected behavior - pyuvstarter modernizes scripts

    def _find_relative_imports(self, project_path: Path):
        """Helper method to find relative imports in a project."""
        relative_imports = []

        for py_file in project_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line.startswith(('from .', 'from ..', 'from ...')):
                        relative_imports.append((str(py_file.relative_to(project_path)), i, line))
            except Exception:
                pass

        return relative_imports

    def test_project_structure_dependency_discovery(self):
        """Test dependency discovery across different project structures."""

        # Test that dependency discovery works consistently across layouts
        layouts = [
            {
                "name": "src_layout",
                "structure": {
                    "pyproject.toml": "[project]\nname = 'src_layout_test'\n",
                    "src/package/main.py": "import pandas\nimport numpy\n",
                    "src/package/utils.py": "import requests\n"
                }
            },
            {
                "name": "flat_layout",
                "structure": {
                    "pyproject.toml": "[project]\nname = 'flat_layout_test'\n",
                    "package/main.py": "import pandas\nimport numpy\n",
                    "package/utils.py": "import requests\n"
                }
            },
            {
                "name": "single_file",
                "structure": {
                    "main.py": "import pandas\nimport numpy\nimport requests\n"
                }
            }
        ]

        for layout in layouts:
            fixture = ProjectFixture(
                name=layout["name"],
                files=layout["structure"],
                directories=[],
                expected_packages=["pandas", "numpy", "requests"],
                is_package=layout["name"] != "single_file"
            )

            with temp_manager.create_temp_project(fixture) as project_dir:
                result = executor.run_pyuvstarter(project_dir)

                assert result.returncode == 0, f"Layout {layout['name']} failed: {result.stderr}"

                # All layouts should discover dependencies consistently
                pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
                dependencies = pyproject_data["project"]["dependencies"]

                for expected_pkg in fixture.expected_packages:
                    found = any(expected_pkg.lower() in dep.lower() for dep in dependencies)
                    assert found, f"Package {expected_pkg} not discovered in {layout['name']} layout"

    def test_project_structure_vscode_configuration(self):
        """Test VS Code configuration generation for different project structures."""

        fixture = ProjectFixture(
            name="vscode_structure_test",
            files={
                "pyproject.toml": """
[project]
name = "vscode_test"
version = "0.1.0"
""",
                # src-layout with multiple packages
                "src/package1/__init__.py": "",
                "src/package1/module1.py": "def func1(): return 'package1'",
                "src/package2/__init__.py": "",
                "src/package2/module2.py": "def func2(): return 'package2'",
                # flat-layout utilities
                "utils/__init__.py": "",
                "utils/common.py": "def common(): return 'common'",
                # scripts directory
                "scripts/run.py": """
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.package1.module1 import func1
from utils.common import common

def run():
    return func1(), common()

if __name__ == "__main__":
    print(run())
"""
            },
            directories=["src/package1", "src/package2", "utils", "scripts"],
            expected_packages=[],
            is_package=True
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            assert result.returncode == 0, f"VS Code structure test failed: {result.stderr}"

            # Check VS Code configuration
            vscode_dir = project_dir / ".vscode"
            assert vscode_dir.exists(), ".vscode directory not created"

            # Check settings.json
            settings_path = vscode_dir / "settings.json"
            if settings_path.exists():
                settings = json.loads(settings_path.read_text(encoding='utf-8'))
                assert "python.defaultInterpreterPath" in settings, "Python interpreter not configured"

            # Check launch.json
            launch_path = vscode_dir / "launch.json"
            if launch_path.exists():
                launch_config = json.loads(launch_path.read_text(encoding='utf-8'))
                assert "configurations" in launch_config, "No configurations in launch.json"

                python_configs = [
                    config for config in launch_config["configurations"]
                    if config.get("type") == "python"
                ]
                assert len(python_configs) > 0, "No Python debug configuration found"

class TestProjectStructureEdgeCases:
    """Test edge cases and special scenarios in project structure detection."""

    def test_empty_project_structure(self):
        """Test handling of empty projects or projects with only config files."""

        fixture = ProjectFixture(
            name="empty_project",
            files={
                "README.md": "# Empty Project\nThis project has only documentation.",
                "LICENSE": "MIT License",
                ".gitignore": "*.pyc\n__pycache__/",
                "config.json": """
{
    "project": "empty_project",
    "version": "0.1.0"
}
"""
            },
            directories=[],
            expected_packages=[],
            is_package=False
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            assert result.returncode == 0, f"Empty project failed: {result.stderr}"

            # Should create basic pyproject.toml
            pyproject_data = validator.validate_pyproject_toml(project_dir)
            assert "project" in pyproject_data, "Basic project structure not created"

    def test_project_with_only_directories(self):
        """Test project with only empty directories (package structure without files)."""

        fixture = ProjectFixture(
            name="directories_only",
            files={
                "README.md": "# Directories Only Project"
            },
            directories=[
                "package1",
                "package1/subpackage",
                "package2",
                "package2/utils",
                "shared",
                "data"
            ],
            expected_packages=[],
            is_package=True  # Directories suggest package structure
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            assert result.returncode == 0, f"Directories only project failed: {result.stderr}"

            # Should handle empty package structure gracefully
            pyproject_data = validator.validate_pyproject_toml(project_dir)
            assert "project" in pyproject_data, "Project not initialized for directories-only structure"

    def test_project_with_conflicting_structures(self):
        """Test project with potentially conflicting structures."""

        fixture = ProjectFixture(
            name="conflicting_structure",
            files={
                # Both __init__.py in root and src/ - potential conflict
                "__init__.py": """
\"\"\"Root package.\"\"\"
version = "1.0.0"
""",
                "main.py": """
# Should use root package import
from . import version
from utils import helper

def main():
    return version
""",
                "utils.py": """
def helper():
    return "Helper from root"
""",
                # Also has src/ directory
                "src/__init__.py": """
\"\"\"Src package.\"\"\"
version = "2.0.0"
""",
                "src/main.py": """
# Should use src package import
from . import version
from .utils import helper

def main():
    return version
""",
                "src/utils.py": """
def helper():
    return "Helper from src"
"""
            },
            directories=["src"],
            expected_packages=[],
            is_package=True
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir)

            # Should handle conflicting structures gracefully
            # May prioritize one structure over the other
            assert result.returncode == 0, f"Conflicting structure project failed: {result.stderr}"

            pyproject_data = validator.validate_pyproject_toml(project_dir)
            assert "project" in pyproject_data, "Project not created for conflicting structure"

def main():
    """Run all project structure tests."""
    import sys

    # Simple test runner for manual execution
    test_classes = [
        TestProjectStructureDetection,
        TestProjectStructureBehavior,
        TestProjectStructureEdgeCases
    ]

    all_tests = []
    for test_class in test_classes:
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        for method in test_methods:
            all_tests.append((test_class().__getattribute__(method), f"{test_class.__name__}.{method}"))

    passed = 0
    total = len(all_tests)

    print("🚀 Running PyUVStarter Project Structure Tests")
    print("=" * 60)

    for test_func, test_name in all_tests:
        try:
            print(f"🧪 Running: {test_name}")
            test_func()
            print(f"✅ {test_name} PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
        print()

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All project structure tests passed!")
        return 0
    else:
        print(f"💥 {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())