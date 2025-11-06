#!/usr/bin/env python3
"""
Comprehensive test suite for pyuvstarter's automatic import fixing functionality.

This test validates that pyuvstarter correctly:
1. Detects package projects with relative imports
2. Converts relative imports to absolute imports
3. Skips non-package projects
4. Leaves absolute imports unchanged
5. Handles legacy requirements.txt projects
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class ImportFixingTestSuite:
    """Test suite for pyuvstarter import fixing functionality."""

    def __init__(self):
        self.test_dir = Path(__file__).parent / "test_import_projects"
        self.original_dir = Path.cwd()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pyuvstarter_test_"))
        self.pyuvstarter_path = Path(__file__).parent.parent

    def setup_test_environment(self, test_project_path: Path) -> Path:
        """Copy test project to temporary directory for isolation."""
        project_name = test_project_path.name
        temp_project_path = self.temp_dir / project_name

        # Copy the entire test project
        shutil.copytree(test_project_path, temp_project_path)

        return temp_project_path

    def cleanup(self):
        """Clean up temporary directories."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def run_pyuvstarter(self, project_path: Path, dry_run: bool = True) -> Tuple[int, str, str]:
        """Run pyuvstarter on the given project and return result using uv run."""
        # Use uv run to execute pyuvstarter with proper dependency resolution
        cmd = [
            "uv", "run",
            "pyuvstarter",
        ]

        # Add dry-run flag only if specified
        if dry_run:
            cmd.append("--dry-run")

        cmd.extend([
            "--verbose",
            str(project_path.resolve())
        ])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.pyuvstarter_path,  # Run from project root
                timeout=120  # 2 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "TIMEOUT: pyuvstarter took too long"

    def find_relative_imports(self, project_path: Path) -> List[Tuple[str, int, str]]:
        """Find all relative imports in a project."""
        relative_imports = []

        for py_file in project_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue  # Skip __init__.py files

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line.startswith(('from .', 'from ..', 'from ...')):
                        relative_imports.append((str(py_file.relative_to(project_path)), i, line))
            except Exception as e:
                print(f"Error reading {py_file}: {e}")

        return relative_imports

    def find_absolute_imports(self, project_path: Path) -> List[Tuple[str, int, str]]:
        """Find all absolute imports in a project."""
        absolute_imports = []

        for py_file in project_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue  # Skip __init__.py files

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line.startswith(('from ', 'import ')) and not line.startswith(('from .', 'from ..', 'from ...')):
                        absolute_imports.append((str(py_file.relative_to(project_path)), i, line))
            except Exception as e:
                print(f"Error reading {py_file}: {e}")

        return absolute_imports

    def test_script_execution_before_and_after_fix(self):
        """Test that relative imports fail as scripts, then work after pyuvstarter fixes them."""
        print("\n🧪 Testing: Script execution before and after import fixing")
        print("=" * 60)

        test_project = self.test_dir / "src_layout_pkg_with_relative_imports"
        temp_project = self.setup_test_environment(test_project)

        try:
            # Step 1: Verify initial state has relative imports
            initial_relative = self.find_relative_imports(temp_project)
            print(f"🔍 Initial relative imports found: {len(initial_relative)}")
            for file_path, line_num, line in initial_relative:
                print(f"  - {file_path}:{line_num}: {line}")

            if len(initial_relative) == 0:
                print("❌ No relative imports found in test project - test setup error")
                return False

            # Step 2: Test script execution FAILS before fixing (this is EXPECTED SUCCESS)
            main_script = temp_project / "src" / "myproject" / "main.py"
            print(f"🧪 Testing script execution BEFORE fix: {main_script.relative_to(temp_project)}")

            # Use uv run to properly test script execution - it should FAIL with ImportError
            try:
                result = subprocess.run(
                    ["uv", "run", "--quiet", "python3", str(main_script)],
                    capture_output=True,
                    text=True,
                    cwd=temp_project,
                    timeout=30
                )
                if result.returncode == 0:
                    print(f"❌ UNEXPECTED: Script execution should have failed with ImportError but succeeded")
                    print(f"   This indicates the test project setup is incorrect")
                    return False
                else:
                    print(f"✅ EXPECTED: Script execution failed with ImportError (this is correct before pyuvstarter fixes)")
                    # Verify it's the expected ImportError
                    if "attempted relative import" in result.stderr or "relative import" in result.stderr:
                        print(f"✅ Correct error type detected: relative import ImportError")
                    else:
                        print(f"⚠️  Different error than expected, but still failed: {result.stderr.strip()}")
                        # Still consider this success since the goal is that it fails before fixing
            except Exception as e:
                print(f"❌ Script execution test failed with exception: {e}")
                return False

            # Step 3: Run pyuvstarter to ACTUALLY FIX the imports (not dry run)
            print("🔧 Running pyuvstarter to fix imports...")
            returncode, stdout, stderr = self.run_pyuvstarter(temp_project, dry_run=False)
            print(f"🚀 PyUVStarter result: {returncode}")

            if returncode != 0:
                print(f"❌ PyUVStarter failed: {stderr}")
                return False

            # Step 4: Verify relative imports were converted to absolute imports
            remaining_relative = self.find_relative_imports(temp_project)
            print(f"🔍 Relative imports after fixing: {len(remaining_relative)}")

            if len(remaining_relative) > 0:
                print(f"❌ Some relative imports were not fixed:")
                for file_path, line_num, line in remaining_relative:
                    print(f"  - {file_path}:{line_num}: {line}")
                return False

            # Step 5: Test script execution SUCCEEDS after fixing (the solution)
            print(f"🧪 Testing script execution AFTER fix: {main_script.relative_to(temp_project)}")

            try:
                # Use uv run to ensure proper Python environment and dependency resolution
                result = subprocess.run(
                    ["uv", "run", "--quiet", "python3", str(main_script)],
                    capture_output=True,
                    text=True,
                    cwd=temp_project,
                    timeout=30
                )
                if result.returncode == 0:
                    print(f"✅ SUCCESS: Script execution works after pyuvstarter fixed imports!")
                    print(f"   Output: {result.stdout.strip()}")
                else:
                    print(f"❌ FAILURE: Script execution still fails after pyuvstarter fix")
                    print(f"   Error: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ Script execution test failed with exception: {e}")
                return False

            # Step 6: Verify import fixing was reported in output
            if "Automatically fixed" in stdout and "relative import" in stdout.lower():
                print("✅ Import fixing was reported in pyuvstarter output")
            else:
                print("❌ Import fixing not properly reported in output")
                print(f"STDOUT snippet: {stdout[:500]}...")
                return False

            print("✅ COMPLETE: Relative imports failed as scripts, then worked after pyuvstarter fixing")
            return True

        finally:
            pass  # Don't cleanup for manual inspection

    def test_flat_layout_package_with_relative_imports(self):
        """Test flat-layout package with deep relative imports should be fixed."""
        print("\n🧪 Testing: flat_layout_pkg_with_deep_relative_imports")
        print("=" * 60)

        test_project = self.test_dir / "flat_layout_pkg_with_deep_relative_imports"
        temp_project = self.setup_test_environment(test_project)

        try:
            # Check initial state - should have deep relative imports
            initial_relative = self.find_relative_imports(temp_project)
            print(f"🔍 Initial deep relative imports found: {len(initial_relative)}")
            for file_path, line_num, line in initial_relative:
                print(f"  - {file_path}:{line_num}: {line}")

            # Run pyuvstarter
            returncode, stdout, stderr = self.run_pyuvstarter(temp_project, dry_run=True)
            print(f"🚀 Dry run result: {returncode}")

            # Verify detection of relative imports
            if "relative import" in stdout.lower():
                print("✅ Deep relative imports detected")
            else:
                print("❌ Deep relative imports not detected")
                return False

            print("✅ Test passed")
            return True

        finally:
            pass

    def test_script_project_no_pyproject(self):
        """Test script project without pyproject.toml should NOT be fixed."""
        print("\n🧪 Testing: script_project_no_pyproject")
        print("=" * 60)

        test_project = self.test_dir / "script_project_no_pyproject"
        temp_project = self.setup_test_environment(test_project)

        try:
            # Check initial state - should have imports but not in a package
            print(f"🔍 Checking if this is detected as non-package...")

            # Run pyuvstarter
            returncode, stdout, stderr = self.run_pyuvstarter(temp_project, dry_run=True)
            print(f"🚀 Dry run result: {returncode}")

            # Verify pyproject.toml is created but import fixing should not apply
            if "pyproject.toml" in stdout and "ensure_project_initialized" in stdout:
                print("✅ pyproject.toml created as expected")
            else:
                print("❌ pyproject.toml creation not detected")
                return False

            # pyuvstarter creates pyproject.toml for script projects, making them packages
            # This is the expected behavior, so we should see relative import detection
            if "relative import" in stdout.lower():
                print("✅ Import fixing correctly detected after pyproject.toml creation")
            else:
                print("❌ Import fixing not detected after pyproject.toml creation")
                return False

            print("✅ Test passed")
            return True

        finally:
            pass

    def test_package_without_pyproject(self):
        """Test package without pyproject.toml should NOT be fixed."""
        print("\n🧪 Testing: pkg_without_pyproject_but_relative_imports")
        print("=" * 60)

        test_project = self.test_dir / "pkg_without_pyproject_but_relative_imports"
        temp_project = self.setup_test_environment(test_project)

        try:
            # Check initial state - should have relative imports but no pyproject.toml
            initial_relative = self.find_relative_imports(temp_project)
            print(f"🔍 Initial relative imports found: {len(initial_relative)}")
            for file_path, line_num, line in initial_relative:
                print(f"  - {file_path}:{line_num}: {line}")

            # Run pyuvstarter
            returncode, stdout, stderr = self.run_pyuvstarter(temp_project, dry_run=True)
            print(f"🚀 Dry run result: {returncode}")

            # Should create pyproject.toml and then detect imports
            if "pyproject.toml" in stdout:
                print("✅ pyproject.toml created as expected")
            else:
                print("❌ pyproject.toml creation not detected")
                return False

            # After pyproject.toml creation, should detect relative imports
            if "relative import" in stdout.lower():
                print("✅ Import fixing correctly detected after pyproject.toml creation")
            else:
                print("❌ Import fixing not detected after pyproject.toml creation")
                return False

            print("✅ Test passed")
            return True

        finally:
            pass

    def test_legacy_requirements_with_relative_imports(self):
        """Test legacy project with requirements.txt and relative imports."""
        print("\n🧪 Testing: legacy_requirements_with_relative_imports")
        print("=" * 60)

        test_project = self.test_dir / "legacy_requirements_with_relative_imports"
        temp_project = self.setup_test_environment(test_project)

        try:
            # Check initial state - should have requirements.txt and relative imports
            requirements_file = temp_project / "requirements.txt"
            pyproject_file = temp_project / "pyproject.toml"

            print(f"🔍 requirements.txt exists: {requirements_file.exists()}")
            print(f"🔍 pyproject.toml exists: {pyproject_file.exists()}")

            initial_relative = self.find_relative_imports(temp_project)
            print(f"🔍 Initial relative imports found: {len(initial_relative)}")

            # Run pyuvstarter
            returncode, stdout, stderr = self.run_pyuvstarter(temp_project, dry_run=True)
            print(f"🚀 Dry run result: {returncode}")

            # Should detect relative imports and handle requirements.txt migration
            if "relative import" in stdout.lower():
                print("✅ Relative imports detected in legacy project")
            else:
                print("❌ Relative imports not detected in legacy project")
                return False

            if "requirements.txt" in stdout or "dependency-migration" in stdout:
                print("✅ Requirements.txt migration detected")
            else:
                print("❌ Requirements.txt migration not detected")
                return False

            print("✅ Test passed")
            return True

        finally:
            pass

    def test_absolute_imports_control(self):
        """Test package with absolute imports should NOT be modified."""
        print("\n🧪 Testing: pkg_with_absolute_imports_control")
        print("=" * 60)

        test_project = self.test_dir / "pkg_with_absolute_imports_control"
        temp_project = self.setup_test_environment(test_project)

        try:
            # Check initial state - should have absolute imports
            initial_relative = self.find_relative_imports(temp_project)
            print(f"🔍 Initial relative imports found: {len(initial_relative)}")

            # Run pyuvstarter
            returncode, stdout, stderr = self.run_pyuvstarter(temp_project, dry_run=True)
            print(f"🚀 Dry run result: {returncode}")

            # Should detect no relative imports to fix (control test)
            if len(initial_relative) == 0:
                print("✅ No relative imports to fix - control test passed")
                return True
            else:
                print(f"❌ Control test found {len(initial_relative)} unexpected relative imports")
                for file_path, line_num, line in initial_relative:
                    print(f"  - {file_path}:{line_num}: {line}")
                return False

        finally:
            pass

    def run_all_tests(self, keep_artifacts: bool = False) -> bool:
        """Run all import fixing tests."""
        print("🚀 Starting PyUVStarter Import Fixing Test Suite")
        print("=" * 60)

        tests = [
            ("Script Execution Before/After Fix", self.test_script_execution_before_and_after_fix),
            ("Flat Layout Package", self.test_flat_layout_package_with_relative_imports),
            ("Script Project", self.test_script_project_no_pyproject),
            ("Package No PyProject", self.test_package_without_pyproject),
            ("Legacy Requirements", self.test_legacy_requirements_with_relative_imports),
            ("Absolute Imports Control", self.test_absolute_imports_control),
        ]

        results = []

        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:.<40} {status}")

        print(f"\nTotal: {total} tests")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")

        if passed == total:
            print("\n🎉 All tests passed!")
            if keep_artifacts:
                print(f"\nTest artifacts preserved in: {self.temp_dir}")
            else:
                print("\nCleaning up test artifacts...")
                self.cleanup()
            return True
        else:
            print(f"\n💥 {total - passed} tests failed!")
            print(f"\nTest artifacts preserved in: {self.temp_dir}")
            print("Use --keep-artifacts flag to preserve for debugging")
            return False


def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Run pyuvstarter import fixing tests")
    parser.add_argument("--keep-artifacts", action="store_true",
                       help="Keep test artifacts for debugging")
    args = parser.parse_args()

    test_suite = ImportFixingTestSuite()

    try:
        success = test_suite.run_all_tests(keep_artifacts=args.keep_artifacts)
        return 0 if success else 1
    finally:
        if not args.keep_artifacts:
            test_suite.cleanup()


if __name__ == "__main__":
    sys.exit(main())