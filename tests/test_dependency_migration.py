#!/usr/bin/env python3
"""
Tests for pyuvstarter dependency migration strategies.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_utils import (
    ProjectFixture, temp_manager, executor
)

def test_basic_dependency_migration():
    """Test basic dependency migration functionality."""

    fixture = ProjectFixture(
        name="basic_test",
        files={
            "requirements.txt": "pandas==2.0.0\nnumpy>=1.20.0\n",
            "main.py": """import pandas as pd
import numpy as np

def main():
    return pd.__version__, np.__version__
"""
        },
        directories=[],
        expected_packages=["pandas", "numpy"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dependency-migration=auto", "--dry-run"]
        )

        assert result.returncode == 0
        assert "dry-run" in result.stdout.lower()

def main():
    """Run all tests."""

    print("🧪 Running dependency migration tests...")

    try:
        test_basic_dependency_migration()
        print("✅ Basic dependency migration test PASSED")
        return 0
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())