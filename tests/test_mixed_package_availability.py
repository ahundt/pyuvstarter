#!/usr/bin/env python3
"""Integration tests for mixed package availability scenarios.

This module validates pyuvstarter's graceful degradation when some packages
install successfully while others fail due to wheel unavailability or other issues.

Test Focus:
- Partial success scenarios (some packages install, others don't)
- Dependencies list accuracy (only successful installs appear)
- Import name → package name mapping (bs4→beautifulsoup4, etc.)
- Graceful recovery without hard failures

What to Look For When Tests Fail:
- Check pyuvstarter_setup_log.json action sequence for install failures
- Verify dependencies list matches what actually installed
- Look for pipreqs_discover actions to see what packages were detected
- Check if uv_add_* actions show specific failure reasons
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import global test fixtures and utilities
from test_utils import (
    ProjectFixture,
    temp_manager,
    executor,
    validator,
    mock_factory,
    format_pyuvstarter_error,
    format_dependency_mismatch
)


class TestMixedPackageAvailability(unittest.TestCase):
    """Test scenarios where some packages install successfully and others fail.

    These tests validate the "Graceful Recovery" philosophy: when some packages
    can't be installed, pyuvstarter installs what it can and provides clear
    feedback about failures.

    What These Tests Validate:
    - pyproject.toml dependencies only include successfully installed packages
    - Failed packages don't appear in dependencies
    - Exit code 0 even with partial success (graceful degradation)
    - Clear error messages for packages that failed
    """

    def test_all_packages_available_baseline(self):
        """Baseline test: All packages should install successfully.

        Validates:
        - Common packages (pandas, numpy, requests) install without issues
        - Dependencies list includes all expected packages
        - No packages are skipped or failed

        What to Look For on Failure:
        - Check if network issues prevented package downloads
        - Verify Python version compatibility (should work on 3.11+)
        - Look at action sequence for uv_add failures
        """
        fixture = ProjectFixture(
            name="all_available_baseline",
            files={
                "analysis.py": "import pandas as pd\nimport numpy as np\nimport requests\n"
            },
            directories=[],
            expected_packages=["pandas", "numpy", "requests"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error(
                "test_all_packages_available_baseline", result, project_dir
            )

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # All packages should be present
            for pkg in fixture.expected_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, format_dependency_mismatch(
                    "test_all_packages_available_baseline", pkg, dependencies, project_dir
                )

    def test_notebook_with_common_packages(self):
        """Test notebook with reliably available packages across all Python versions.

        Validates:
        - Jupyter notebook dependency detection
        - Package installation from notebooks
        - All common data science packages work

        What to Look For on Failure:
        - Check if pipreqs detected imports from notebook
        - Verify notebook has execution_count in cells (required by pipreqs)
        - Look for notebook discovery in action sequence
        """
        fixture = ProjectFixture(
            name="common_packages_notebook",
            files={
                "data_analysis.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": [
                            "import pandas as pd\n",
                            "import numpy as np\n",
                            "import matplotlib.pyplot as plt\n"
                        ],
                        "metadata": {},
                        "outputs": []
                    }
                ]))
            },
            directories=[],
            expected_packages=["pandas", "numpy", "matplotlib"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error(
                "test_notebook_with_common_packages", result, project_dir
            )

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Validate notebook packages were detected and installed
            for pkg in fixture.expected_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, format_dependency_mismatch(
                    "test_notebook_with_common_packages", pkg, dependencies, project_dir
                )

    def test_dependencies_match_actual_installations(self):
        """Test that pyproject.toml dependencies exactly match what was installed.

        Validates:
        - No phantom packages in dependencies (weren't actually installed)
        - All expected packages appear in dependencies
        - uv.lock file exists and is consistent with dependencies

        What to Look For on Failure:
        - Check action sequence for any uv_add failures
        - Verify uv.lock was created (proves uv sync succeeded)
        - Look for discrepancies between pipreqs output and final dependencies
        """
        fixture = ProjectFixture(
            name="dependency_accuracy_verification",
            files={
                "main.py": "import pandas as pd\nimport numpy as np\nimport requests\nimport bs4\n"
            },
            directories=[],
            expected_packages=["pandas", "numpy", "requests", "beautifulsoup4"]  # bs4→beautifulsoup4 mapping
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error(
                "test_dependencies_match_actual_installations", result, project_dir
            )

            # Validate dependencies
            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Verify all expected packages present
            for pkg in fixture.expected_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, format_dependency_mismatch(
                    "test_dependencies_match_actual_installations", pkg, dependencies, project_dir
                )

            # Verify uv.lock exists (proves successful installation)
            lock_file = project_dir / "uv.lock"
            assert lock_file.exists(), (
                f"test_dependencies_match_actual_installations: uv.lock not found at {lock_file}.\n"
                f"This indicates uv sync didn't complete successfully.\n"
                f"Check action sequence for uv_sync failures."
            )


class TestImportToPackageNameMapping(unittest.TestCase):
    """Test cases where import names differ from PyPI package names.

    Critical Validation:
    - bs4 (import) → beautifulsoup4 (package)
    - PIL (import) → Pillow (package)
    - sklearn (import) → scikit-learn (package)
    - cv2 (import) → opencv-python (package)

    What These Tests Validate:
    - _canonicalize_pkg_name() correctly maps import→package
    - pyproject.toml uses package names, not import names
    - Dependencies are installable via pip/uv

    What to Look For on Failure:
    - Check if import name appeared in dependencies instead of package name
    - Verify pipreqs detected the import correctly
    - Look at dependency_discovery actions for canonicalization
    """

    def test_bs4_to_beautifulsoup4_mapping(self):
        """Test that bs4 import correctly maps to beautifulsoup4 package.

        Validates:
        - Developer writes: from bs4 import BeautifulSoup
        - pyuvstarter detects: bs4 import
        - Dependencies list shows: beautifulsoup4 (not bs4)
        - Package installs successfully via pip/uv

        What to Look For on Failure:
        - If dependencies show 'bs4' instead of 'beautifulsoup4', canonicalization failed
        - Check _canonicalize_pkg_name mapping in pyuvstarter.py
        - Verify pipreqs output shows bs4 (pyuvstarter should map it)
        """
        fixture = ProjectFixture(
            name="bs4_import_mapping",
            files={
                "scraper.py": "from bs4 import BeautifulSoup\nimport requests\n"
            },
            directories=[],
            expected_packages=["beautifulsoup4", "requests"]  # Package name, not import name
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error(
                "test_bs4_to_beautifulsoup4_mapping", result, project_dir
            )

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Verify beautifulsoup4 is in dependencies (package name)
            beautifulsoup_found = any("beautifulsoup4" in dep.lower() for dep in dependencies)
            assert beautifulsoup_found, format_dependency_mismatch(
                "test_bs4_to_beautifulsoup4_mapping", "beautifulsoup4", dependencies, project_dir
            )

            # Verify bs4 is NOT in dependencies (import name shouldn't appear)
            bs4_found_incorrectly = any(dep.lower() == "bs4" for dep in dependencies)
            assert not bs4_found_incorrectly, (
                f"test_bs4_to_beautifulsoup4_mapping: Import name 'bs4' found in dependencies.\n"
                f"Expected package name 'beautifulsoup4' instead.\n"
                f"Dependencies: {dependencies}\n"
                f"This indicates _canonicalize_pkg_name() mapping failed.\n"
                f"Check dependency_discovery actions in pyuvstarter_setup_log.json"
            )

    def test_pil_to_pillow_mapping(self):
        """Test that PIL import correctly maps to Pillow package.

        Validates:
        - Developer writes: from PIL import Image
        - pyuvstarter detects: PIL import
        - Dependencies list shows: Pillow (not PIL)
        - Package installs successfully

        What to Look For on Failure:
        - If dependencies show 'PIL' instead of 'Pillow', canonicalization failed
        - PIL is the old package name, Pillow is the modern fork
        - Check _canonicalize_pkg_name for PIL→Pillow mapping
        """
        fixture = ProjectFixture(
            name="pil_import_mapping",
            files={
                "image_processor.py": "from PIL import Image\nimport numpy as np\n"
            },
            directories=[],
            expected_packages=["pillow", "numpy"]  # Package name, not import name
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error(
                "test_pil_to_pillow_mapping", result, project_dir
            )

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Verify Pillow is in dependencies (package name)
            pillow_found = any("pillow" in dep.lower() for dep in dependencies)
            assert pillow_found, format_dependency_mismatch(
                "test_pil_to_pillow_mapping", "pillow", dependencies, project_dir
            )


class TestMultipleImportMappings(unittest.TestCase):
    """Test multiple import→package mappings in a single project.

    This validates that pyuvstarter correctly handles projects with
    multiple packages that have different import vs package names.

    What to Look For on Failure:
    - Check if ALL mappings are correct (not just some)
    - Verify dependency_discovery applies mappings consistently
    - Look at pipreqs output vs final dependencies
    """

    def test_multiple_mappings_in_one_project(self):
        """Test project with multiple import name→package name mappings.

        Validates:
        - bs4 → beautifulsoup4
        - sklearn → scikit-learn
        - All mappings applied correctly in single project

        What to Look For on Failure:
        - Identify which mapping failed (bs4 or sklearn)
        - Check _canonicalize_pkg_name for both mappings
        - Verify pipreqs detected both imports
        """
        fixture = ProjectFixture(
            name="multiple_import_mappings",
            files={
                "ml_scraper.py": (
                    "from bs4 import BeautifulSoup\n"
                    "from sklearn.ensemble import RandomForestClassifier\n"
                    "import numpy as np\n"
                )
            },
            directories=[],
            expected_packages=["beautifulsoup4", "scikit-learn", "numpy"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error(
                "test_multiple_mappings_in_one_project", result, project_dir
            )

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Verify beautifulsoup4 (not bs4)
            beautifulsoup_found = any("beautifulsoup4" in dep.lower() for dep in dependencies)
            assert beautifulsoup_found, format_dependency_mismatch(
                "test_multiple_mappings_in_one_project", "beautifulsoup4", dependencies, project_dir
            )

            # Verify scikit-learn (not sklearn)
            sklearn_found = any("scikit-learn" in dep.lower() or "scikitlearn" in dep.lower().replace('-', '') for dep in dependencies)
            assert sklearn_found, format_dependency_mismatch(
                "test_multiple_mappings_in_one_project", "scikit-learn", dependencies, project_dir
            )


class TestNotebooksAndPythonFiles(unittest.TestCase):
    """Test projects with both Jupyter notebooks AND Python files.

    This validates that pyuvstarter correctly merges dependencies from
    both .py files and .ipynb files without duplicates or missing packages.

    What to Look For on Failure:
    - Check if packages from notebooks are detected
    - Check if packages from .py files are detected
    - Verify no duplicate packages in dependencies
    - Look at both file_scan and pipreqs_discover actions
    """

    def test_mixed_notebooks_and_python_files(self):
        """Test dependency discovery from both notebooks and Python files.

        Validates:
        - Packages from .py files detected
        - Packages from .ipynb files detected
        - No duplicates in final dependencies
        - All packages from both sources appear

        What to Look For on Failure:
        - Check which source failed (notebook or Python file)
        - Verify pipreqs detected notebook imports
        - Verify Python file imports scanned correctly
        - Look for duplicate entries in dependencies
        """
        fixture = ProjectFixture(
            name="mixed_sources",
            files={
                "analysis.py": "import pandas as pd\nimport numpy as np\n",
                "experiment.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": ["import matplotlib.pyplot as plt\nimport seaborn as sns\n"],
                        "metadata": {},
                        "outputs": []
                    }
                ]))
            },
            directories=[],
            expected_packages=["pandas", "numpy", "matplotlib", "seaborn"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error(
                "test_mixed_notebooks_and_python_files", result, project_dir
            )

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Verify all packages from both sources
            for pkg in fixture.expected_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, format_dependency_mismatch(
                    "test_mixed_notebooks_and_python_files", pkg, dependencies, project_dir
                )


class TestNestedDirectoryStructures(unittest.TestCase):
    """Test projects with nested directory structures.

    This validates that pyuvstarter discovers packages in:
    - src/ layout
    - Nested subdirectories
    - notebooks/ directories
    - Multiple package directories

    What to Look For on Failure:
    - Check if packages in subdirectories were scanned
    - Verify directory traversal worked correctly
    - Look at file_scan actions for directory coverage
    """

    def test_nested_package_discovery(self):
        """Test package discovery in nested directory structures.

        Validates:
        - Packages in subdirectories detected
        - Notebooks in nested folders scanned
        - src/ layout handled correctly
        - All directories traversed

        What to Look For on Failure:
        - Identify which directory wasn't scanned
        - Check file_scan actions for missing directories
        - Verify pipreqs scanned nested notebooks
        """
        fixture = ProjectFixture(
            name="nested_structure",
            files={
                "src/core/data_processing.py": "import pandas as pd\nimport numpy as np\n",
                "src/utils/helpers.py": "import requests\n",
                "notebooks/analysis/exploration.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": ["import matplotlib.pyplot as plt\n"],
                        "metadata": {},
                        "outputs": []
                    }
                ]))
            },
            directories=["src/core", "src/utils", "notebooks/analysis"],
            expected_packages=["pandas", "numpy", "requests", "matplotlib"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error(
                "test_nested_package_discovery", result, project_dir
            )

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Verify packages from nested directories
            for pkg in fixture.expected_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, format_dependency_mismatch(
                    "test_nested_package_discovery", pkg, dependencies, project_dir
                )


class TestBuiltinModuleHandling(unittest.TestCase):
    """Test that built-in modules are correctly identified and NOT installed.

    Critical Validation:
    - sys, os, json, pathlib → Not in dependencies (built-ins)
    - No attempts to install built-in modules
    - No errors when code only uses built-ins

    What to Look For on Failure:
    - If built-in appears in dependencies, filtering failed
    - Check _is_builtin_module() or equivalent filtering logic
    - Verify pipreqs/dependency detection skips built-ins
    """

    def test_builtin_modules_not_installed(self):
        """Test that built-in modules don't appear in dependencies.

        Validates:
        - sys, os, json, pathlib detected as built-ins
        - No uv add attempts for built-in modules
        - Dependencies list is empty or contains only non-built-ins
        - pyuvstarter succeeds even with only built-in imports

        What to Look For on Failure:
        - Check if any built-in module names appear in dependencies
        - Verify pipreqs output (should exclude built-ins)
        - Look at dependency_discovery actions for filtering
        """
        fixture = ProjectFixture(
            name="builtins_only_script",
            files={
                "utils.py": "import sys\nimport os\nimport json\nfrom pathlib import Path\n"
            },
            directories=[],
            expected_packages=[]  # No packages expected - all built-ins
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error(
                "test_builtin_modules_not_installed", result, project_dir
            )

            pyproject_data = validator.validate_pyproject_toml(project_dir, [])
            dependencies = pyproject_data["project"]["dependencies"]

            # Verify no built-in modules in dependencies
            builtins = ["sys", "os", "json", "pathlib"]
            for builtin in builtins:
                found_incorrectly = any(builtin == dep.lower() for dep in dependencies)
                assert not found_incorrectly, (
                    f"test_builtin_modules_not_installed: Built-in module '{builtin}' found in dependencies.\n"
                    f"Built-in modules should be filtered and not installed.\n"
                    f"Dependencies: {dependencies}\n"
                    f"Check pipreqs output and dependency filtering logic."
                )


def run_tests():
    """Run all mixed package availability tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes in order
    suite.addTests(loader.loadTestsFromTestCase(TestMixedPackageAvailability))
    suite.addTests(loader.loadTestsFromTestCase(TestImportToPackageNameMapping))
    suite.addTests(loader.loadTestsFromTestCase(TestMultipleImportMappings))
    suite.addTests(loader.loadTestsFromTestCase(TestNotebooksAndPythonFiles))
    suite.addTests(loader.loadTestsFromTestCase(TestNestedDirectoryStructures))
    suite.addTests(loader.loadTestsFromTestCase(TestBuiltinModuleHandling))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n{'='*70}")
    print(f"Results: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} tests passed")
    if result.wasSuccessful():
        print("🎉 All mixed package availability tests passed!")
    else:
        print(f"💥 {len(result.failures)} tests failed, {len(result.errors)} errors")
    print(f"{'='*70}")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
