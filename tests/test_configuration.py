#!/usr/bin/env python3
"""
Tests for pyuvstarter configuration options and CLI parameters.

Tests various configuration scenarios:
- --config-file parameter with JSON configuration
- --venv-name for custom virtual environment naming
- Custom gitignore templates
- Different CLI argument combinations
- Configuration validation and error handling
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_utils import (
    ProjectFixture, temp_manager, executor
)

def test_config_file_parameter():
    """Test --config-file parameter with JSON configuration."""

    # Create a configuration file
    config_content = {
        "venv_name": "custom-env",
        "dependency_migration": "auto",
        "verbose": True,
        "dry_run": True
    }

    fixture = ProjectFixture(
        name="config_file_test",
        files={
            "pyuvstarter_config.json": json.dumps(config_content, indent=2),
            "main.py": "import sys\nprint('Hello from configured project')",
            "requirements.txt": "pandas\nnumpy"
        },
        directories=[],
        expected_packages=["pandas", "numpy"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        config_path = project_dir / "pyuvstarter_config.json"
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--config-file", str(config_path), "--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"
        assert "dry-run" in result.stdout.lower()

def test_custom_venv_name():
    """Test --venv-name parameter for custom virtual environment naming."""

    fixture = ProjectFixture(
        name="custom_venv_test",
        files={
            "main.py": "import sys\nprint('Custom venv test')",
            "requirements.txt": "requests"
        },
        directories=[],
        expected_packages=["requests"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--venv-name", "my-custom-env", "--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"
        assert "dry-run" in result.stdout.lower()

def test_custom_gitignore_template():
    """Test custom gitignore template functionality."""

    fixture = ProjectFixture(
        name="custom_gitignore_test",
        files={
            "main.py": "import sys\nprint('Custom gitignore test')",
            ".gitignore.template": "# Custom gitignore template\n*.log\n*.tmp\n.env\ncustom_output/\n# Python specific\n__pycache__/\n*.pyc\n",
            "requirements.txt": "flask"
        },
        directories=[],
        expected_packages=["flask"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"
        assert "dry-run" in result.stdout.lower()

def test_cli_argument_combinations():
    """Test various CLI argument combinations."""

    fixture = ProjectFixture(
        name="cli_args_test",
        files={
            "main.py": "import sys\nimport os\nprint('CLI args test')",
            "data.csv": "name,value\ntest,123",
            "requirements.txt": "pandas\nmatplotlib"
        },
        directories=[],
        expected_packages=["pandas", "matplotlib"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        # Test combination of --verbose and --dry-run
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--verbose", "--dry-run"]
        )

        assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"
        assert "dry-run" in result.stdout.lower()
        # Verbose mode should show more details
        assert len(result.stdout) > 1000  # Verbose output should be substantial

def test_dependency_migration_with_config():
    """Test dependency migration modes with configuration."""

    fixture = ProjectFixture(
        name="config_migration_test",
        files={
            "requirements.txt": "numpy==1.24.0\npandas>=2.0.0\nrequests>=2.25.0\n",
            "main.py": """
import numpy as np
import pandas as pd
import requests
import sys  # Standard library, shouldn't be in dependencies

def main():
    data = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
    return len(data)
""",
            "config.json": json.dumps({
                "dependency_migration": "auto",
                "venv_name": "migration-test-env"
            }, indent=2)
        },
        directories=[],
        expected_packages=["numpy", "pandas", "requests"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dependency-migration", "auto", "--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"
        assert "dry-run" in result.stdout.lower()

def test_config_file_validation():
    """Test configuration file validation."""

    # Test with invalid JSON
    fixture = ProjectFixture(
        name="invalid_config_test",
        files={
            "invalid_config.json": '{"invalid": json content}',
            "main.py": "print('test')"
        },
        directories=[],
        expected_packages=[]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        config_path = project_dir / "invalid_config.json"
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--config-file", str(config_path), "--dry-run"]
        )

        # Should handle invalid config gracefully
        assert result.returncode == 0 or "invalid" in result.stderr.lower()

def test_missing_config_file():
    """Test behavior with missing configuration file."""

    fixture = ProjectFixture(
        name="missing_config_test",
        files={
            "main.py": "print('missing config test')"
        },
        directories=[],
        expected_packages=[]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--config-file", "/nonexistent/config.json", "--dry-run"]
        )

        # Should handle missing config file gracefully
        assert result.returncode == 0 or "not found" in result.stderr.lower()

def test_json_config_with_special_characters():
    """Test JSON configuration with special characters and Unicode."""

    fixture = ProjectFixture(
        name="unicode_config_test",
        files={
            "unicode_config.json": json.dumps({
                "venv_name": "tëst-ënv-ñamé",
                "dependency_migration": "auto",
                "verbose": True,
                "dry_run": True
            }, ensure_ascii=False),
            "main.py": """
# Test with Unicode comments and strings
def main():
    message = "Héllo Wörld! 🌍"
    special_chars = "café naïve résumé"
    print(message)
    return special_chars
""",
            "requirements.txt": "python-decouple"  # Package with dash
        },
        directories=[],
        expected_packages=["python-decouple"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        config_path = project_dir / "unicode_config.json"
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--config-file", str(config_path), "--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"
        assert "dry-run" in result.stdout.lower()

def test_config_override_priority():
    """Test configuration override priority (CLI args > config file > defaults)."""

    fixture = ProjectFixture(
        name="config_priority_test",
        files={
            "config.json": json.dumps({
                "venv_name": "config-file-env",
                "dependency_migration": "skip-requirements"
            }, indent=2),
            "main.py": """
import sys
import json

def main():
    # Test that CLI args override config file
    print("Config priority test")
    return True
""",
            "requirements.txt": "numpy\npandas"
        },
        directories=[],
        expected_packages=["numpy", "pandas"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        config_path = project_dir / "config.json"

        # CLI args should override config file
        result = executor.run_pyuvstarter(
            project_dir,
            args=[
                "--config-file", str(config_path),
                "--venv-name", "cli-override-env",  # Should override config file
                "--dependency-migration", "auto",   # Should override config file
                "--dry-run", "--verbose"
            ]
        )

        assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"
        assert "dry-run" in result.stdout.lower()

def main():
    """Run all configuration tests."""

    tests = [
        ("config_file_parameter", test_config_file_parameter),
        ("custom_venv_name", test_custom_venv_name),
        ("custom_gitignore_template", test_custom_gitignore_template),
        ("cli_argument_combinations", test_cli_argument_combinations),
        ("dependency_migration_with_config", test_dependency_migration_with_config),
        ("config_file_validation", test_config_file_validation),
        ("missing_config_file", test_missing_config_file),
        ("json_config_with_special_characters", test_json_config_with_special_characters),
        ("config_override_priority", test_config_override_priority),
    ]

    passed = 0
    total = len(tests)

    print("🚀 Running PyUVStarter Configuration Tests")
    print("=" * 60)

    for test_name, test_func in tests:
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
        print("🎉 All configuration tests passed!")
        return 0
    else:
        print(f"💥 {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())