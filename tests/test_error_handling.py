#!/usr/bin/env python3
"""
Tests for pyuvstarter error handling and recovery scenarios.

Tests various error conditions and how pyuvstarter handles them:
- Dependency conflicts and resolution attempts
- Malformed files (invalid JSON, broken requirements.txt)
- Network failures and connection issues
- Permission problems and read-only directories
- Missing tools and dependencies
- Invalid project structures
"""

import sys
import json
import tempfile
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_utils import (
    ProjectFixture, temp_manager, executor, validator, mock_factory
)

def test_dependency_conflict_handling():
    """Test handling of conflicting dependency versions."""

    fixture = ProjectFixture(
        name="dependency_conflict",
        files={
            "requirements.txt": """
# Conflicting versions
pandas==1.5.0
numpy>=1.20.0,<1.25.0
scikit-learn>=1.3.0  # May conflict with older numpy

# Additional conflicting dependencies
requests>=2.25.0
urllib3>=1.26.0,<2.0.0  # May conflict with requests
""",
            "main.py": """
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import requests
import urllib3

def main():
    return "All imports successful"
""",
        },
        directories=[],
        expected_packages=["pandas", "numpy", "scikit-learn", "requests", "urllib3"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dependency-migration", "auto", "--dry-run", "--verbose"]
        )

        # Should handle conflicts gracefully, either by:
        # 1. Resolving them automatically
        # 2. Providing clear error messages with solutions
        # 3. Falling back to compatible versions
        assert result.returncode == 0 or "conflict" in result.stderr.lower()

def test_malformed_requirements_file():
    """Test handling of malformed requirements.txt files."""

    fixture = ProjectFixture(
        name="malformed_requirements",
        files={
            "requirements.txt": """
# Valid entries
pandas==2.0.0
numpy>=1.20.0

# Malformed entries
invalid-package-without-version
requests>=2.25.0broken-syntax
scikit-learn>=1.0.0

# Comments without packages
# This is just a comment
!pip install some-package  # Invalid pip command

# Partially valid entries
beautifulsoup4 @ https://github.com/waylan/beautifulsoup/archive/refs/heads/master.zip

# Empty lines and whitespace


# More malformed entries
package>=version<invalid_format
another-package==1.0.0==2.0.0
""",
            "simple_script.py": """
import pandas as pd
import numpy as np
import requests  # May not be discovered due to malformed entry

def main():
    return pd.__version__, np.__version__
""",
        },
        directories=[],
        expected_packages=["pandas", "numpy"]  # Only valid packages
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dependency-migration", "auto", "--dry-run", "--verbose"]
        )

        # Should handle malformed entries gracefully
        assert result.returncode == 0 or "malformed" in result.stderr.lower() or "invalid" in result.stderr.lower()

def test_malformed_json_files():
    """Test handling of malformed JSON files in project."""

    fixture = ProjectFixture(
        name="malformed_json",
        files={
            "pyproject.toml": """
[project]
name = "test_project"
version = "1.0.0"
description = "Test project
# Unclosed string - should cause parsing error
dependencies = [
    "pandas>=1.5.0",
    "numpy>=1.20.0"
]
""",
            "invalid_config.json": '{"invalid": json content, "missing": quotes}',
            "main.py": """
import json
import pandas as pd
import numpy as np

def load_config():
    try:
        with open('invalid_config.json') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"fallback": "config"}

def main():
    config = load_config()
    return len(config)
""",
        },
        directories=[],
        expected_packages=["pandas", "numpy"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dry-run", "--verbose"]
        )

        # Should handle malformed JSON gracefully
        assert result.returncode == 0 or "invalid" in result.stderr.lower() or "malformed" in result.stderr.lower()

def test_permission_denied_scenarios():
    """Test handling of permission denied scenarios."""

    fixture = ProjectFixture(
        name="permission_test",
        files={
            "main.py": """
import sys
import os

def main():
    return "Permission test"
""",
            "requirements.txt": "requests"
        },
        directories=[],
        expected_packages=["requests"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        # Create a read-only file to simulate permission issues
        readonly_file = project_dir / "readonly.txt"
        readonly_file.write_text("This file is read-only")
        readonly_file.chmod(0o444)  # Read-only

        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dry-run", "--verbose"]
        )

        # Should handle permission issues gracefully
        assert result.returncode == 0 or "permission" in result.stderr.lower() or "denied" in result.stderr.lower()

def test_network_failure_simulation():
    """Test behavior when network operations fail."""

    fixture = ProjectFixture(
        name="network_failure_test",
        files={
            "requirements.txt": """
# These packages would require network access
nonexistent-package-12345==1.0.0
another-fake-package==2.0.0
pandas==2.0.0  # This one should work if available locally
""",
            "main.py": """
import sys

def main():
    return "Network failure test"
""",
        },
        directories=[],
        expected_packages=[]  # May not find any packages due to network issues
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dependency-migration", "auto", "--dry-run", "--verbose"]
        )

        # Should handle network failures gracefully
        assert result.returncode == 0 or "network" in result.stderr.lower() or "connection" in result.stderr.lower()

def test_invalid_project_structure():
    """Test handling of invalid or problematic project structures."""

    fixture = ProjectFixture(
        name="invalid_structure",
        files={
            # File with problematic name
            "main.py": """
import sys
import os

def main():
    return "Invalid structure test"
""",
            # Create files with problematic names
            "script with spaces.py": "print('Spaces in filename')",
            "file@with#special&chars.py": "print('Special characters')",
            "con.py": "import sys\nprint('Reserved name on Windows')",  # Reserved name on Windows
            "requirements.txt": "requests"
        },
        directories=[],
        expected_packages=["requests"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dry-run", "--verbose"]
        )

        # Should handle problematic filenames gracefully
        assert result.returncode == 0 or "invalid" in result.stderr.lower() or "filename" in result.stderr.lower()

def test_missing_dependencies():
    """Test handling when required tools are missing."""

    fixture = ProjectFixture(
        name="missing_deps_test",
        files={
            "main.py": """
import sys

def main():
    return "Missing dependencies test"
""",
            "requirements.txt": "this-package-does-not-exist==1.0.0\nanother-fake-package==2.0.0"
        },
        directories=[],
        expected_packages=[]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dependency-migration", "auto", "--dry-run", "--verbose"]
        )

        # Should handle missing packages gracefully
        assert result.returncode == 0 or "not found" in result.stderr.lower() or "missing" in result.stderr.lower()

def test_circular_imports():
    """Test handling of circular import situations."""

    fixture = ProjectFixture(
        name="circular_imports",
        files={
            "module_a.py": """
from module_b import function_b

def function_a():
    return "A"
""",
            "module_b.py": """
from module_a import function_a

def function_b():
    return "B"
""",
            "main.py": """
import module_a
import module_b

def main():
    return module_a.function_a(), module_b.function_b()
""",
            "requirements.txt": "requests"
        },
        directories=[],
        expected_packages=["requests"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dry-run", "--verbose"]
        )

        # Should detect circular imports but continue processing
        assert result.returncode == 0 or "circular" in result.stderr.lower()

def test_very_deep_directory_structure():
    """Test handling of very deep directory structures."""

    fixture = ProjectFixture(
        name="deep_structure",
        files={
            # Create a file in a very deep directory
            "level1/level2/level3/level4/level5/level6/level7/level8/level9/level10/deep_file.py": """
import sys
import os

def deep_function():
    return "Deep function called"
""",
            "main.py": """
import sys

def main():
    return "Deep structure test"
""",
            "requirements.txt": "requests"
        },
        directories=[
            "level1/level2/level3/level4/level5/level6/level7/level8/level9/level10"
        ],
        expected_packages=["requests"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dry-run", "--verbose"]
        )

        # Should handle deep directory structures
        assert result.returncode == 0 or "deep" in result.stderr.lower() or "path" in result.stderr.lower()

def test_extremely_large_file():
    """Test handling of extremely large files."""

    fixture = ProjectFixture(
        name="large_file_test",
        files={
            "main.py": """
import sys

def main():
    return "Large file test"
""",
            "requirements.txt": "requests",
            # Create a large file (simulated)
            "large_data.csv": "name,value\n" + ",".join(["data"] * 1000) + "\n"
        },
        directories=[],
        expected_packages=["requests"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        # Make the file larger
        large_file = project_dir / "large_data.csv"
        content = large_file.read_text()
        # Repeat content to make it larger
        large_file.write_text(content * 100)  # ~100KB file

        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dry-run", "--verbose"]
        )

        # Should handle large files without issues
        assert result.returncode == 0 or "large" in result.stderr.lower() or "memory" in result.stderr.lower()

def main():
    """Run all error handling tests."""

    tests = [
        ("dependency_conflict_handling", test_dependency_conflict_handling),
        ("malformed_requirements_file", test_malformed_requirements_file),
        ("malformed_json_files", test_malformed_json_files),
        ("permission_denied_scenarios", test_permission_denied_scenarios),
        ("network_failure_simulation", test_network_failure_simulation),
        ("invalid_project_structure", test_invalid_project_structure),
        ("missing_dependencies", test_missing_dependencies),
        ("circular_imports", test_circular_imports),
        ("very_deep_directory_structure", test_very_deep_directory_structure),
        ("extremely_large_file", test_extremely_large_file),
    ]

    passed = 0
    total = len(tests)

    print("🚀 Running PyUVStarter Error Handling Tests")
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
        print("🎉 All error handling tests passed!")
        return 0
    else:
        print(f"💥 {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())