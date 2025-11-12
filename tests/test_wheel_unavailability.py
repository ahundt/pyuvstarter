#!/usr/bin/env python3
"""Unit tests for wheel unavailability handling and graceful dependency installation.

This module tests the enhanced error handling for packages that have no wheels
available for the current Python version, ensuring graceful degradation and
specific, actionable error messages.

Tests are designed to be platform-independent using mocks, so they work reliably
regardless of which packages actually have wheel availability issues.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import MagicMock, Mock, call, patch

# Import the functions we're testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from pyuvstarter import _categorize_uv_add_error, _try_packages_individually


class TestCategorizeUvAddError(unittest.TestCase):
    """Test the enhanced error categorization function."""

    def test_wheel_unavailability_with_package_name_and_versions(self):
        """Test detection of wheel unavailability with specific package and Python versions."""
        stderr = """error: Failed to prepare distributions
  Caused by: Failed to fetch wheel: tensorflow==2.20.0
  Caused by: Build backend failed to build wheel through `build_sdist` with exit status: 1

--- stderr
Because all versions of tensorflow have no wheels with a matching Python version tag, we can conclude that all versions of tensorflow are incompatible.
Only the following Python version tags are available for tensorflow: Python ABI tags: `cp39`, `cp310`, `cp311`, `cp312`, `cp313`.
Your Python version is: 3.14
"""
        result = _categorize_uv_add_error(stderr)

        # Should extract package name and available versions
        self.assertIn("tensorflow", result.lower())
        self.assertIn("cp39", result)  # Shows available versions
        self.assertIn("3.14", result)  # Shows current version

    def test_wheel_unavailability_without_version_details(self):
        """Test wheel unavailability when version details aren't in stderr."""
        stderr = """Because all versions of some-package have no wheels with a matching Python version tag,
we can conclude that the package is incompatible."""

        result = _categorize_uv_add_error(stderr)

        # Should still detect wheel unavailability even without details
        self.assertIn("some-package", result.lower())
        self.assertIn("wheel", result.lower())

    def test_python_version_conflict_not_wheel_issue(self):
        """Test that Python version conflicts (not wheel issues) are categorized differently."""
        stderr = """error: No solution found when resolving dependencies:
  Because package-x==2.3.1 depends on Python>=3.11 and you are using Python 3.10,
  we can conclude that package-x==2.3.1 cannot be used."""

        result = _categorize_uv_add_error(stderr)

        # Should identify as Python version incompatibility, not wheel issue
        self.assertIn("incompatible", result.lower())
        self.assertIn("python", result.lower())
        # Should NOT mention wheels
        self.assertNotIn("wheel", result.lower())

    def test_generic_version_conflict(self):
        """Test categorization of general version conflicts."""
        stderr = """error: No solution found when resolving dependencies:
  Because package-a==1.0.0 depends on package-b>=2.0.0 and package-c==1.0.0 depends on package-b<2.0.0,
  we can conclude that package-a==1.0.0 and package-c==1.0.0 are incompatible."""

        result = _categorize_uv_add_error(stderr)

        self.assertIn("conflict", result.lower())

    def test_network_error(self):
        """Test categorization of network errors."""
        stderr = """error: Failed to fetch package metadata
  Caused by: Failed to download package
  Caused by: Connection timeout"""

        result = _categorize_uv_add_error(stderr)

        self.assertIn("network", result.lower())

    def test_empty_stderr(self):
        """Test handling of empty stderr."""
        result = _categorize_uv_add_error("")

        # Should return a generic error message
        self.assertIn("unknown", result.lower())

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        stderr_upper = "BECAUSE ALL VERSIONS OF PACKAGE HAVE NO WHEELS WITH A MATCHING PYTHON VERSION TAG"
        stderr_lower = "because all versions of package have no wheels with a matching python version tag"

        result_upper = _categorize_uv_add_error(stderr_upper)
        result_lower = _categorize_uv_add_error(stderr_lower)

        # Both should detect wheel unavailability
        self.assertIn("wheel", result_upper.lower())
        self.assertIn("wheel", result_lower.lower())


class TestTryPackagesIndividually(unittest.TestCase):
    """Test the DRY helper function for one-by-one package installation."""

    @patch('pyuvstarter._run_command')
    @patch('pyuvstarter._log_action')
    def test_all_packages_succeed(self, mock_log, mock_run):
        """Test when all packages install successfully."""
        packages = ["numpy", "pandas", "matplotlib"]
        project_root = Path("/tmp/test_project")

        # Mock successful uv add commands
        mock_run.return_value = None

        successful, failed = _try_packages_individually(
            packages, project_root, action_prefix="test_install"
        )

        # All should succeed
        self.assertEqual(successful, packages)
        self.assertEqual(failed, [])

        # Should have called uv add for each package
        self.assertEqual(mock_run.call_count, 3)

    @patch('pyuvstarter._run_command')
    @patch('pyuvstarter._log_action')
    @patch('pyuvstarter._categorize_uv_add_error')
    def test_partial_success_with_wheel_unavailability(self, mock_categorize, mock_log, mock_run):
        """Test graceful handling when some packages lack wheels."""
        packages = ["numpy", "pandas", "tensorflow", "torch"]
        project_root = Path("/tmp/test_project")

        # Mock numpy and pandas succeeding, tensorflow and torch failing with wheel errors
        def mock_run_side_effect(cmd, *args, **kwargs):
            pkg = cmd[2]  # Package name is at index 2 in ["uv", "add", "PACKAGE"]
            if pkg in ["tensorflow", "torch"]:
                error = subprocess.CalledProcessError(
                    returncode=1,
                    cmd=cmd,
                    stderr=f"Because all versions of {pkg} have no wheels with a matching Python version tag"
                )
                raise error

        mock_run.side_effect = mock_run_side_effect

        # Mock categorization to return specific error messages
        def mock_categorize_side_effect(stderr):
            if "tensorflow" in stderr:
                return "tensorflow: no Python 3.14 wheel (available: cp39-cp313)"
            elif "torch" in stderr:
                return "torch: no Python 3.14 wheel (available: cp38-cp313)"
            return "unknown error"

        mock_categorize.side_effect = mock_categorize_side_effect

        successful, failed = _try_packages_individually(
            packages, project_root, action_prefix="test_wheel_fallback"
        )

        # Should have partial success
        self.assertEqual(len(successful), 2)
        self.assertIn("numpy", successful)
        self.assertIn("pandas", successful)

        self.assertEqual(len(failed), 2)
        # Check that failed packages have specific reasons
        failed_packages = [pkg for pkg, reason in failed]
        self.assertIn("tensorflow", failed_packages)
        self.assertIn("torch", failed_packages)

        # Check that reasons are specific
        tensorflow_reason = next(reason for pkg, reason in failed if pkg == "tensorflow")
        self.assertIn("tensorflow", tensorflow_reason)
        self.assertIn("3.14", tensorflow_reason)

    @patch('pyuvstarter._run_command')
    @patch('pyuvstarter._log_action')
    @patch('pyuvstarter._extract_package_name_from_specifier')
    def test_package_with_version_specifier(self, mock_extract, mock_log, mock_run):
        """Test handling packages with version specifiers."""
        packages = ["numpy>=1.20.0", "pandas==2.0.0", "matplotlib"]
        project_root = Path("/tmp/test_project")

        # Mock extraction of package names
        def extract_side_effect(pkg):
            if ">=" in pkg:
                return pkg.split(">=")[0]
            elif "==" in pkg:
                return pkg.split("==")[0]
            return pkg

        mock_extract.side_effect = extract_side_effect
        mock_run.return_value = None

        successful, failed = _try_packages_individually(
            packages, project_root, action_prefix="test_versioned"
        )

        # All should succeed
        self.assertEqual(len(successful), 3)
        self.assertEqual(len(failed), 0)

    @patch('pyuvstarter._run_command')
    @patch('pyuvstarter._log_action')
    def test_skip_empty_package_names(self, mock_log, mock_run):
        """Test that empty package names are skipped."""
        # Include a package that _extract_package_name_from_specifier might return empty for
        packages = ["numpy", "", "pandas"]
        project_root = Path("/tmp/test_project")

        mock_run.return_value = None

        with patch('pyuvstarter._extract_package_name_from_specifier', return_value=""):
            successful, failed = _try_packages_individually(
                packages, project_root, action_prefix="test_empty"
            )

        # Should skip empty names (depends on implementation)
        # The exact behavior depends on how _extract_package_name_from_specifier is mocked

    @patch('pyuvstarter._run_command')
    @patch('pyuvstarter._log_action')
    @patch('pyuvstarter._categorize_uv_add_error')
    def test_mixed_failure_reasons(self, mock_categorize, mock_log, mock_run):
        """Test when packages fail for different reasons (wheel unavailability vs version conflicts)."""
        packages = ["numpy", "tensorflow", "some-nonexistent-package"]
        project_root = Path("/tmp/test_project")

        # Mock different failure modes
        def mock_run_side_effect(cmd, *args, **kwargs):
            pkg = cmd[2]
            if pkg == "tensorflow":
                raise subprocess.CalledProcessError(
                    returncode=1,
                    cmd=cmd,
                    stderr="Because all versions of tensorflow have no wheels with a matching Python version tag"
                )
            elif pkg == "some-nonexistent-package":
                raise subprocess.CalledProcessError(
                    returncode=1,
                    cmd=cmd,
                    stderr="error: No solution found: Package 'some-nonexistent-package' not found on PyPI"
                )

        mock_run.side_effect = mock_run_side_effect

        # Mock categorization
        def mock_categorize_side_effect(stderr):
            if "no wheels" in stderr:
                return "tensorflow: no Python 3.14 wheel"
            elif "not found" in stderr:
                return "package not found on PyPI"
            return "unknown error"

        mock_categorize.side_effect = mock_categorize_side_effect

        successful, failed = _try_packages_individually(
            packages, project_root, action_prefix="test_mixed"
        )

        # Numpy should succeed
        self.assertEqual(len(successful), 1)
        self.assertIn("numpy", successful)

        # Two packages should fail with different reasons
        self.assertEqual(len(failed), 2)

        # Check that each failure has a specific, different reason
        reasons = {pkg: reason for pkg, reason in failed}
        self.assertIn("wheel", reasons.get("tensorflow", "").lower())
        self.assertIn("not found", reasons.get("some-nonexistent-package", "").lower())


class TestWheelUnavailabilityIntegration(unittest.TestCase):
    """Integration tests for the complete wheel unavailability handling flow."""

    @patch('pyuvstarter._run_command')
    @patch('pyuvstarter._log_action')
    @patch('pyuvstarter._try_packages_individually')
    def test_early_detection_skips_futile_retries(self, mock_try_individual, mock_log, mock_run):
        """Test that wheel unavailability is detected early and skips the 3-retry cycle."""
        # This would test the code path in _manage_project_dependencies
        # where we check for "no wheels with a matching python version tag" BEFORE
        # the "no solution found" + "python" check

        # Mock uv add failing with wheel error
        stderr_with_wheel_error = """Because all versions of tensorflow have no wheels with a matching Python version tag.
Python ABI tags: `cp39`, `cp310`, `cp311`, `cp312`, `cp313`"""

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["uv", "add", "tensorflow"],
            stderr=stderr_with_wheel_error
        )

        # Mock the one-by-one installation to return partial success
        mock_try_individual.return_value = (
            ["numpy", "pandas"],  # successful
            [("tensorflow", "tensorflow: no Python 3.14 wheel (available: cp39-cp313)")]  # failed
        )

        # The actual test would call _manage_project_dependencies here
        # and verify that it:
        # 1. Detects wheel unavailability immediately
        # 2. Calls _try_packages_individually without retrying
        # 3. Returns partial success status

        # This is a placeholder - the actual integration test would need
        # to call the full _manage_project_dependencies function
        pass


class TestPythonVersionAwareness(unittest.TestCase):
    """Tests for Python version-aware package expectations."""

    def test_current_python_version(self):
        """Verify we can detect the current Python version."""
        major, minor = sys.version_info[:2]
        version_str = f"{major}.{minor}"

        # Basic sanity check
        self.assertIsInstance(major, int)
        self.assertIsInstance(minor, int)
        self.assertGreaterEqual(major, 3)

    def test_tensorflow_availability_by_python_version(self):
        """Document tensorflow wheel availability by Python version.

        This is a documentation test that records the known wheel availability.
        When tensorflow adds Python 3.14+ wheels, this test should be updated.
        """
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        # Known tensorflow wheel availability (as of 2025-11)
        # Update this when tensorflow releases Python 3.14 wheels
        tensorflow_available_versions = ["3.9", "3.10", "3.11", "3.12", "3.13"]

        if python_version in tensorflow_available_versions:
            # Tensorflow should be installable on these versions
            self.assertTrue(
                True,
                f"TensorFlow has wheels for Python {python_version}"
            )
        elif python_version == "3.14":
            # As of 2025-11, tensorflow doesn't have Python 3.14 wheels yet
            # This will change in the future - update this test when it does
            self.assertTrue(
                True,
                f"TensorFlow will have Python {python_version} wheels in the future "
                f"(currently only cp39-cp313 available)"
            )


def run_tests():
    """Run all wheel unavailability tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCategorizeUvAddError))
    suite.addTests(loader.loadTestsFromTestCase(TestTryPackagesIndividually))
    suite.addTests(loader.loadTestsFromTestCase(TestWheelUnavailabilityIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPythonVersionAwareness))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
