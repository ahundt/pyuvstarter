#!/usr/bin/env python3
"""
Tests for pyuvstarter --prepare-pypi feature.

Tests that --prepare-pypi correctly generates PyPI publishing metadata:
- LICENSE file with correct template for each supported license type
- README.md template when missing
- pyproject.toml metadata fields (classifiers, keywords, authors, urls, license)
- .github/workflows/publish.yml with Trusted Publisher OIDC workflow
- Non-destructive behavior: existing files are not overwritten
- Idempotent re-runs: running twice produces same result
- Edge cases: unknown license types, missing pyproject.toml, dry-run mode
"""

import sys
import os
import textwrap
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_utils import (
    ProjectFixture, temp_manager, executor
)

# Helpers for reading TOML in tests
try:
    import tomllib
except ImportError:
    import toml as tomllib  # type: ignore[no-redef]


def _read_toml(path: Path) -> dict:
    """Read a TOML file, handling both tomllib and toml package APIs."""
    if hasattr(tomllib, "load") and "rb" in str(tomllib.load.__code__.co_varnames[:1]):
        # tomllib (stdlib) needs binary mode
        with open(path, "rb") as f:
            return tomllib.load(f)
    else:
        # toml package uses text mode
        import toml
        with open(path, "r", encoding="utf-8") as f:
            return toml.load(f)


# ── Fresh project: all files generated ──────────────────────────────


def test_prepare_pypi_generates_all_files():
    """--prepare-pypi on a fresh project should create LICENSE, README.md, publish.yml, and update pyproject.toml."""
    fixture = ProjectFixture(
        name="pypi_fresh",
        files={
            "main.py": "print('hello')\n",
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, (
            f"--prepare-pypi failed (exit={result.returncode}).\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # All expected files should exist
        assert (project_dir / "LICENSE").exists(), "LICENSE file should be created"
        assert (project_dir / "README.md").exists(), "README.md should be created"
        assert (project_dir / ".github" / "workflows" / "publish.yml").exists(), "publish.yml should be created"

        # pyproject.toml should have PyPI metadata
        data = _read_toml(project_dir / "pyproject.toml")
        project = data.get("project", {})
        assert "license" in project, "license field should be added"
        assert "classifiers" in project, "classifiers should be added"
        assert "keywords" in project, "keywords should be added"
        assert "authors" in project, "authors should be added"
        assert "readme" in project, "readme field should be added"


# ── Existing files are NOT overwritten ──────────────────────────────


def test_prepare_pypi_does_not_overwrite_existing_readme():
    """--prepare-pypi should skip README.md if it already exists."""
    original_readme = "# My Custom README\n\nDo not overwrite this.\n"
    fixture = ProjectFixture(
        name="pypi_existing_readme",
        files={
            "main.py": "print('hello')\n",
            "README.md": original_readme,
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        # README should be unchanged
        actual = (project_dir / "README.md").read_text(encoding="utf-8")
        assert actual == original_readme, "README.md should not be overwritten"


def test_prepare_pypi_does_not_overwrite_existing_license():
    """--prepare-pypi should skip LICENSE if it already exists."""
    original_license = "My custom license text\n"
    fixture = ProjectFixture(
        name="pypi_existing_license",
        files={
            "main.py": "print('hello')\n",
            "LICENSE": original_license,
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        actual = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert actual == original_license, "LICENSE should not be overwritten"


def test_prepare_pypi_does_not_overwrite_existing_publish_workflow():
    """--prepare-pypi should skip publish.yml if it already exists."""
    original_workflow = "name: My Custom Workflow\non: push\n"
    fixture = ProjectFixture(
        name="pypi_existing_workflow",
        files={
            "main.py": "print('hello')\n",
            ".github/workflows/publish.yml": original_workflow,
        },
        directories=[".github/workflows"],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        actual = (project_dir / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
        assert actual == original_workflow, "publish.yml should not be overwritten"


def test_prepare_pypi_does_not_overwrite_existing_toml_fields():
    """--prepare-pypi should not overwrite existing PyPI metadata fields in pyproject.toml."""
    fixture = ProjectFixture(
        name="pypi_existing_metadata",
        files={
            "main.py": "print('hello')\n",
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        # After pyuvstarter creates the initial pyproject.toml, manually add some fields
        # then re-run with --prepare-pypi to verify they're preserved
        result1 = executor.run_pyuvstarter(
            project_dir,
            args=["--verbose"],
        )
        assert result1.returncode == 0, f"Initial run failed: {result1.stderr}"

        # Now add a custom license to pyproject.toml
        import toml
        pyproject_path = project_dir / "pyproject.toml"
        data = _read_toml(pyproject_path)
        data.setdefault("project", {})["license"] = {"text": "Proprietary"}
        data["project"]["authors"] = [{"name": "Test Author", "email": "test@example.com"}]
        with open(pyproject_path, "w", encoding="utf-8") as f:
            toml.dump(data, f)

        # Run --prepare-pypi — should not overwrite license or authors
        result2 = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result2.returncode == 0, f"--prepare-pypi failed: {result2.stderr}"

        data2 = _read_toml(pyproject_path)
        project = data2.get("project", {})
        assert project.get("license") == {"text": "Proprietary"}, "license should not be overwritten"
        assert project["authors"][0]["name"] == "Test Author", "authors should not be overwritten"


# ── License type variants ───────────────────────────────────────────


def test_prepare_pypi_apache_license():
    """--prepare-pypi --license Apache-2.0 should generate Apache license text."""
    fixture = ProjectFixture(
        name="pypi_apache",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--license", "Apache-2.0", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert "Apache License" in license_text, "Should contain Apache license text"
        assert "Version 2.0" in license_text, "Should reference Apache 2.0"


def test_prepare_pypi_gpl_license():
    """--prepare-pypi --license GPL-3.0 should generate GPL license text."""
    fixture = ProjectFixture(
        name="pypi_gpl",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--license", "GPL-3.0", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert "GNU General Public License" in license_text, "Should contain GPL text"


def test_prepare_pypi_bsd_license():
    """--prepare-pypi --license BSD-3-Clause should generate BSD license text."""
    fixture = ProjectFixture(
        name="pypi_bsd",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--license", "BSD-3-Clause", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert "BSD 3-Clause" in license_text, "Should contain BSD 3-Clause text"


def test_prepare_pypi_mit_license_default():
    """--prepare-pypi with no --license should default to MIT."""
    fixture = ProjectFixture(
        name="pypi_mit_default",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert "MIT License" in license_text, "Default license should be MIT"


# ── Classifiers auto-generation ─────────────────────────────────────


def test_prepare_pypi_classifiers_from_python_version():
    """Classifiers should include Python version derived from requires-python."""
    fixture = ProjectFixture(
        name="pypi_classifiers",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        classifiers = data.get("project", {}).get("classifiers", [])

        # Should have base Python 3 classifier
        assert "Programming Language :: Python :: 3" in classifiers, "Should have Python 3 classifier"
        # Should have Development Status classifier
        assert any("Development Status" in c for c in classifiers), "Should have Development Status classifier"
        # Should have license classifier (MIT by default)
        assert any("MIT" in c for c in classifiers), "Should have MIT license classifier"


def test_prepare_pypi_license_classifier_matches_flag():
    """License classifier should match the --license flag."""
    fixture = ProjectFixture(
        name="pypi_license_classifier",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--license", "Apache-2.0", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        classifiers = data.get("project", {}).get("classifiers", [])
        assert any("Apache" in c for c in classifiers), f"Should have Apache classifier, got: {classifiers}"


# ── publish.yml content validation ──────────────────────────────────


def test_prepare_pypi_publish_workflow_content():
    """Generated publish.yml should have correct structure for Trusted Publisher OIDC."""
    fixture = ProjectFixture(
        name="pypi_workflow_content",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        workflow_text = (project_dir / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")

        # Must have tag trigger
        assert "tags:" in workflow_text, "Workflow should trigger on tags"
        assert "'v*'" in workflow_text, "Workflow should trigger on v* tags"

        # Must have id-token: write for OIDC
        assert "id-token: write" in workflow_text, "Workflow must request id-token: write for OIDC"

        # Must have pypi-publish action
        assert "pypa/gh-action-pypi-publish" in workflow_text, "Workflow must use pypi-publish action"

        # Must have version check step
        assert "TAG_VERSION" in workflow_text, "Workflow should verify tag matches package version"

        # Must have both testpypi and pypi jobs
        assert "testpypi" in workflow_text, "Workflow should publish to TestPyPI"
        assert "publish-pypi" in workflow_text, "Workflow should publish to PyPI"

        # Must have environment references
        assert "environment:" in workflow_text, "Workflow should use GitHub environments"


# ── Edge cases ──────────────────────────────────────────────────────


def test_prepare_pypi_unknown_license_type():
    """--prepare-pypi --license UNKNOWN should skip LICENSE but not crash."""
    fixture = ProjectFixture(
        name="pypi_unknown_license",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--license", "UNKNOWN-LICENSE", "--verbose"],
        )
        # Should not crash — may return 0 with a warning about unknown license
        # The other files should still be generated even if license fails
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        # LICENSE should NOT be created for unknown license
        assert not (project_dir / "LICENSE").exists(), "LICENSE should not be created for unknown license type"

        # But README and workflow should still be created
        assert (project_dir / "README.md").exists(), "README.md should still be created"
        assert (project_dir / ".github" / "workflows" / "publish.yml").exists(), "publish.yml should still be created"


def test_prepare_pypi_dry_run():
    """--prepare-pypi --dry-run should not create any files."""
    fixture = ProjectFixture(
        name="pypi_dry_run",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--dry-run", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        # In dry-run, LICENSE and publish.yml should NOT be created
        # (README.md might exist if pyuvstarter creates it in its non-pypi step)
        assert not (project_dir / "LICENSE").exists(), "LICENSE should not be created in dry-run"
        assert not (project_dir / ".github" / "workflows" / "publish.yml").exists(), "publish.yml should not be created in dry-run"


def test_prepare_pypi_idempotent():
    """Running --prepare-pypi twice should produce the same result."""
    fixture = ProjectFixture(
        name="pypi_idempotent",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        # First run
        result1 = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result1.returncode == 0, f"First run failed: {result1.stderr}"

        # Capture file contents after first run
        license1 = (project_dir / "LICENSE").read_text(encoding="utf-8")
        readme1 = (project_dir / "README.md").read_text(encoding="utf-8")
        workflow1 = (project_dir / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
        toml1 = _read_toml(project_dir / "pyproject.toml")

        # Second run
        result2 = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result2.returncode == 0, f"Second run failed: {result2.stderr}"

        # All files should be identical
        assert (project_dir / "LICENSE").read_text(encoding="utf-8") == license1, "LICENSE changed on re-run"
        assert (project_dir / "README.md").read_text(encoding="utf-8") == readme1, "README.md changed on re-run"
        assert (project_dir / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8") == workflow1, "publish.yml changed on re-run"

        # TOML metadata should be identical
        toml2 = _read_toml(project_dir / "pyproject.toml")
        assert toml2.get("project", {}).get("license") == toml1.get("project", {}).get("license"), "license changed on re-run"
        assert toml2.get("project", {}).get("classifiers") == toml1.get("project", {}).get("classifiers"), "classifiers changed on re-run"


def test_prepare_pypi_keywords_placeholder():
    """Keywords should be an empty list with a TODO comment for the user to fill in."""
    fixture = ProjectFixture(
        name="my_awesome_tool",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        # keywords should be an empty list (user fills in their own keywords)
        data = _read_toml(project_dir / "pyproject.toml")
        keywords = data.get("project", {}).get("keywords", None)
        assert keywords is not None, "keywords key should be present in [project]"
        assert isinstance(keywords, list), f"keywords must be a list, got: {type(keywords)}"
        assert keywords == [], (
            f"keywords should be empty list (user fills in their own), got: {keywords}"
        )
        # The raw file should contain a TODO comment so the user knows to fill it in
        raw = (project_dir / "pyproject.toml").read_text()
        assert "TODO" in raw and "keywords" in raw, (
            "pyproject.toml must contain a TODO comment on the keywords line"
        )


def test_prepare_pypi_urls_use_placeholder():
    """Generated URLs should use USERNAME placeholder since pyuvstarter has no git dependency."""
    fixture = ProjectFixture(
        name="pypi_urls",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        urls = data.get("project", {}).get("urls", {})
        assert "USERNAME" in urls.get("Homepage", ""), f"Homepage should have USERNAME placeholder, got: {urls}"
        assert "/issues" in urls.get("Issues", ""), f"Issues URL should end with /issues, got: {urls}"


def test_prepare_pypi_uv_build_succeeds():
    """After --prepare-pypi, `uv build` should succeed on the generated project."""
    fixture = ProjectFixture(
        name="pypi_build_check",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        # First set up the project with --prepare-pypi
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"--prepare-pypi failed: {result.stderr}"

        # Then try to build
        import subprocess
        build_result = subprocess.run(
            ["uv", "build"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert build_result.returncode == 0, (
            f"uv build failed after --prepare-pypi.\n"
            f"stdout: {build_result.stdout}\nstderr: {build_result.stderr}"
        )

        # dist/ directory should contain wheel and sdist
        dist_dir = project_dir / "dist"
        assert dist_dir.exists(), "dist/ directory should exist after uv build"
        dist_files = list(dist_dir.iterdir())
        assert len(dist_files) >= 2, f"Expected wheel + sdist, got: {[f.name for f in dist_files]}"


# ── Auto-detection and custom license ───────────────────────────────


def test_prepare_pypi_auto_detects_mit_license():
    """--license auto should detect MIT from an existing LICENSE file."""
    mit_text = """MIT License

Copyright (c) 2025 Test Author

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction.
"""
    fixture = ProjectFixture(
        name="pypi_auto_mit",
        files={
            "main.py": "print('hello')\n",
            "LICENSE": mit_text,
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],  # default is --license auto
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        license_val = data.get("project", {}).get("license", {})
        assert license_val.get("text") == "MIT", f"Should detect MIT license, got: {license_val}"

        # LICENSE file should NOT be overwritten
        actual = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert actual == mit_text, "Existing LICENSE should not be overwritten"


def test_prepare_pypi_auto_detects_apache_license():
    """--license auto should detect Apache-2.0 from an existing LICENSE file."""
    apache_text = """Apache License
Version 2.0, January 2004

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
"""
    fixture = ProjectFixture(
        name="pypi_auto_apache",
        files={
            "main.py": "print('hello')\n",
            "LICENSE": apache_text,
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        license_val = data.get("project", {}).get("license", {})
        assert license_val.get("text") == "Apache-2.0", f"Should detect Apache-2.0, got: {license_val}"


def test_prepare_pypi_auto_detects_license_md():
    """--license auto should detect license from LICENSE.md (not just LICENSE)."""
    bsd_text = """BSD 3-Clause License

Copyright (c) 2025, Test Author

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice.
2. Redistributions in binary form must reproduce the above copyright notice.
3. Neither the name of the copyright holder nor the names of its contributors.
"""
    fixture = ProjectFixture(
        name="pypi_auto_license_md",
        files={
            "main.py": "print('hello')\n",
            "LICENSE.md": bsd_text,
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        license_val = data.get("project", {}).get("license", {})
        assert license_val.get("text") == "BSD-3-Clause", f"Should detect BSD-3-Clause from LICENSE.md, got: {license_val}"


def test_prepare_pypi_custom_license_from_unrecognized_file():
    """--license auto should use 'custom' with file reference for unrecognized LICENSE content."""
    custom_text = """CUSTOM PROPRIETARY LICENSE

This software is proprietary. All rights reserved.
No part of this software may be reproduced without permission.
"""
    fixture = ProjectFixture(
        name="pypi_custom_license",
        files={
            "main.py": "print('hello')\n",
            "LICENSE": custom_text,
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        license_val = data.get("project", {}).get("license", {})
        # Custom license should use file reference, not text
        assert license_val.get("file") == "LICENSE", f"Custom license should use file reference, got: {license_val}"

        # LICENSE file should NOT be overwritten
        actual = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert actual == custom_text, "Custom LICENSE should not be overwritten"


def test_prepare_pypi_explicit_license_overrides_auto():
    """--license MIT should use MIT even if auto-detection would find something else."""
    apache_text = """Apache License Version 2.0"""
    fixture = ProjectFixture(
        name="pypi_explicit_override",
        files={
            "main.py": "print('hello')\n",
            "LICENSE": apache_text,
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--license", "MIT", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        license_val = data.get("project", {}).get("license", {})
        # Should use explicit MIT, not auto-detected Apache
        assert license_val.get("text") == "MIT", f"Explicit --license should override auto-detection, got: {license_val}"


def test_prepare_pypi_auto_no_license_file_defaults_mit():
    """--license auto with no LICENSE file should default to MIT."""
    fixture = ProjectFixture(
        name="pypi_auto_no_license",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        license_val = data.get("project", {}).get("license", {})
        assert license_val.get("text") == "MIT", f"No LICENSE file should default to MIT, got: {license_val}"

        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert "MIT License" in license_text, "Should generate MIT LICENSE file"


# ── Standalone --license (without --prepare-pypi) ───────────────────


def test_standalone_license_creates_file():
    """--license MIT (without --prepare-pypi) should create LICENSE file."""
    fixture = ProjectFixture(
        name="standalone_license",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--license", "MIT", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        assert (project_dir / "LICENSE").exists(), "LICENSE file should be created with standalone --license"
        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert "MIT License" in license_text, "LICENSE should contain MIT text"


def test_standalone_license_apache():
    """--license Apache-2.0 (without --prepare-pypi) should create Apache LICENSE."""
    fixture = ProjectFixture(
        name="standalone_apache",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--license", "Apache-2.0", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        assert (project_dir / "LICENSE").exists(), "LICENSE file should be created"
        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert "Apache License" in license_text, "LICENSE should contain Apache text"


def test_standalone_license_does_not_create_pypi_metadata():
    """--license MIT (without --prepare-pypi) should NOT create publish.yml or modify pyproject.toml metadata."""
    fixture = ProjectFixture(
        name="standalone_no_pypi",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--license", "MIT", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        # publish.yml should NOT be created
        assert not (project_dir / ".github" / "workflows" / "publish.yml").exists(), \
            "publish.yml should NOT be created without --prepare-pypi"


# ── Case-insensitive license file detection ─────────────────────────


def test_case_insensitive_license_detection():
    """Auto-detection should find 'License' (mixed case) files."""
    mit_text = "MIT License\n\nPermission is hereby granted, free of charge.\n"
    fixture = ProjectFixture(
        name="case_insensitive_license",
        files={
            "main.py": "print('hello')\n",
            "License": mit_text,  # Mixed case
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        license_val = data.get("project", {}).get("license", {})
        assert license_val.get("text") == "MIT", f"Should detect MIT from 'License' file, got: {license_val}"


def test_case_insensitive_license_txt():
    """Auto-detection should find 'license.txt' (lowercase) files."""
    gpl_text = "GNU General Public License\nVersion 3, 29 June 2007\n"
    fixture = ProjectFixture(
        name="case_insensitive_license_txt",
        files={
            "main.py": "print('hello')\n",
            "license.txt": gpl_text,
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        license_val = data.get("project", {}).get("license", {})
        assert license_val.get("text") == "GPL-3.0", f"Should detect GPL-3.0 from 'license.txt', got: {license_val}"


def test_apache_license_contains_canonical_text():
    """Generated Apache-2.0 LICENSE should contain key phrases from the canonical text at apache.org."""
    fixture = ProjectFixture(
        name="apache_canonical",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--license", "Apache-2.0", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        # Key phrases from the canonical Apache 2.0 text (https://www.apache.org/licenses/LICENSE-2.0.txt)
        assert "Version 2.0, January 2004" in license_text, "Should contain version header"
        assert "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION" in license_text, "Should contain terms header"
        assert "Grant of Copyright License" in license_text, "Should contain Section 2"
        assert "Grant of Patent License" in license_text, "Should contain Section 3"
        assert "Redistribution" in license_text, "Should contain Section 4"
        assert "Disclaimer of Warranty" in license_text, "Should contain Section 7"
        assert "Limitation of Liability" in license_text, "Should contain Section 8"
        assert "END OF TERMS AND CONDITIONS" in license_text, "Should contain end marker"
        assert "APPENDIX" in license_text, "Should contain the APPENDIX"


def test_mit_license_contains_canonical_text():
    """Generated MIT LICENSE should contain the canonical phrases from opensource.org."""
    fixture = ProjectFixture(
        name="mit_canonical",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--license", "MIT", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert "MIT License" in license_text, "Should have MIT header"
        assert "Permission is hereby granted, free of charge" in license_text, "Should have canonical grant"
        assert "THE SOFTWARE IS PROVIDED" in license_text, "Should have warranty disclaimer"
        assert "WITHOUT WARRANTY OF ANY KIND" in license_text, "Should disclaim warranties"


def test_bsd_license_contains_canonical_text():
    """Generated BSD-3-Clause LICENSE should contain canonical phrases from opensource.org."""
    fixture = ProjectFixture(
        name="bsd_canonical",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--license", "BSD-3-Clause", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert "BSD 3-Clause License" in license_text, "Should have BSD header"
        assert "Redistribution and use in source and binary forms" in license_text, "Should have redistribution clause"
        assert "Neither the name of the copyright holder" in license_text, "Should have clause 3"
        assert "THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS" in license_text, "Should have disclaimer"


def test_gpl_license_contains_canonical_text():
    """Generated GPL-3.0 LICENSE should contain the standard FSF notice and reference."""
    fixture = ProjectFixture(
        name="gpl_canonical",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--prepare-pypi", "--license", "GPL-3.0", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        license_text = (project_dir / "LICENSE").read_text(encoding="utf-8")
        assert "GNU General Public License" in license_text, "Should reference GPL"
        assert "either version 3 of the License" in license_text, "Should reference version 3"
        assert "https://www.gnu.org/licenses/" in license_text, "Should link to full GPL text"


def test_existing_license_not_overwritten_by_standalone():
    """--license MIT should not overwrite an existing license file (case-insensitive)."""
    original = "My Custom License\n"
    fixture = ProjectFixture(
        name="no_overwrite_case",
        files={
            "main.py": "print('hello')\n",
            "License.md": original,
        },
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--license", "MIT", "--verbose"],
        )
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        # Original file should be unchanged
        actual = (project_dir / "License.md").read_text(encoding="utf-8")
        assert actual == original, "Existing License.md should not be overwritten"

        # No new LICENSE file should be created either
        assert not (project_dir / "LICENSE").exists(), \
            "Should not create LICENSE when License.md already exists"


# ─── Gap 0: publish.yml test job ─────────────────────────────


def test_publish_yml_has_test_job_when_ci_exists():
    """Generated publish.yml should include test: job when ci.yml exists."""
    fixture = ProjectFixture(
        name="publish_test_job",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        # Create ci.yml so publish.yml will include test job
        ci_dir = project_dir / ".github" / "workflows"
        ci_dir.mkdir(parents=True, exist_ok=True)
        (ci_dir / "ci.yml").write_text("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")

        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        publish_yml = project_dir / ".github" / "workflows" / "publish.yml"
        assert publish_yml.exists(), "publish.yml should be created"
        content = publish_yml.read_text(encoding="utf-8")

        assert "test:" in content, "publish.yml should have a test: job"
        assert "uses: ./.github/workflows/ci.yml" in content, "test job should reference ci.yml"
        assert "needs: test" in content, "build job should depend on test job"
        assert "shell: bash" in content, "version check should have shell: bash for Windows compat"
        # Verify permissions block preventing startup_failure is present after uses: line
        ci_ref_idx = content.find("uses: ./.github/workflows/ci.yml")
        build_idx = content.find("build:", ci_ref_idx)
        between = content[ci_ref_idx:build_idx]
        assert "permissions:" in between, "permissions: block required after uses: line to prevent GitHub startup_failure"
        assert "checks: write" in between, "checks: write required for test reporter"
        assert "pull-requests: write" in between, "pull-requests: write required for test reporter"


def test_publish_yml_no_test_job_without_ci():
    """Generated publish.yml should omit test: job when ci.yml doesn't exist."""
    fixture = ProjectFixture(
        name="publish_no_ci",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        publish_yml = project_dir / ".github" / "workflows" / "publish.yml"
        assert publish_yml.exists(), "publish.yml should be created"
        content = publish_yml.read_text(encoding="utf-8")

        assert "test:" not in content, "publish.yml should NOT have test: job without ci.yml"
        assert "uses: ./.github/workflows/ci.yml" not in content
        assert "shell: bash" in content, "version check should still have shell: bash"


# ─── Gap 1: workflow_call injection ──────────────────────────


def test_workflow_call_injected_into_ci_yml():
    """When ci.yml exists without workflow_call, it should be injected."""
    fixture = ProjectFixture(
        name="wf_call_inject",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        # Create a ci.yml without workflow_call
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        ci_yml = workflows_dir / "ci.yml"
        ci_yml.write_text(
            "name: CI\n\non:\n  push:\n    branches: [main]\n  pull_request:\n    branches: [main]\n\n"
            "jobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n",
            encoding="utf-8",
        )

        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        content = ci_yml.read_text(encoding="utf-8")
        assert "workflow_call" in content, "workflow_call should be injected into ci.yml"
        assert "push:" in content, "push trigger should still be present"
        assert "pull_request:" in content, "pull_request trigger should still be present"


def test_workflow_call_already_present_skipped():
    """When ci.yml already has workflow_call, it should be skipped."""
    fixture = ProjectFixture(
        name="wf_call_skip",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        ci_yml = workflows_dir / "ci.yml"
        original = (
            "name: CI\n\non:\n  push:\n    branches: [main]\n  workflow_call:\n\n"
            "jobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        ci_yml.write_text(original, encoding="utf-8")

        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0

        content = ci_yml.read_text(encoding="utf-8")
        assert content.count("workflow_call") == 1, "Should not duplicate workflow_call"


def test_no_ci_yml_skipped():
    """When no ci.yml exists, injection should be skipped gracefully."""
    fixture = ProjectFixture(
        name="no_ci_yml",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"


# ─── Gap 2: Changelog URL ────────────────────────────────────


def test_changelog_url_in_fresh_project():
    """Fresh project should get Changelog URL in project.urls."""
    fixture = ProjectFixture(
        name="changelog_fresh",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        data = _read_toml(project_dir / "pyproject.toml")
        urls = data.get("project", {}).get("urls", {})
        assert "Changelog" in urls, "Changelog should be in project.urls"
        assert "/releases" in urls["Changelog"], "Changelog URL should point to /releases"


def test_changelog_added_to_existing_urls():
    """When urls exist but Changelog is missing, it should be added."""
    fixture = ProjectFixture(
        name="changelog_existing",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        # First run to create project with urls
        executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])

        # Remove Changelog from urls and re-run
        data = _read_toml(project_dir / "pyproject.toml")
        if "Changelog" in data.get("project", {}).get("urls", {}):
            del data["project"]["urls"]["Changelog"]
        import toml as _toml_writer
        with open(project_dir / "pyproject.toml", "w") as f:
            _toml_writer.dump(data, f)

        # Delete publish.yml so --prepare-pypi re-runs fully
        publish_yml = project_dir / ".github" / "workflows" / "publish.yml"
        if publish_yml.exists():
            publish_yml.unlink()

        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0

        data = _read_toml(project_dir / "pyproject.toml")
        assert "Changelog" in data["project"]["urls"], "Changelog should be re-added"


# ─── Gap 3: RELEASING.md ─────────────────────────────────────


def test_releasing_md_created_fresh():
    """Fresh project should get RELEASING.md."""
    fixture = ProjectFixture(
        name="releasing_fresh",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        releasing = project_dir / "RELEASING.md"
        assert releasing.exists(), "RELEASING.md should be created"
        content = releasing.read_text(encoding="utf-8")
        assert "PyPI" in content, "Should contain PyPI publishing section"
        assert "Trusted Publisher" in content or "testpypi" in content, "Should contain setup instructions"


def test_releasing_md_appended_when_exists_without_pypi():
    """Existing RELEASING.md without PyPI section should get it appended."""
    fixture = ProjectFixture(
        name="releasing_append",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        releasing = project_dir / "RELEASING.md"
        releasing.write_text("# Releasing\n\n## Version bump\n\n1. Bump version\n2. Tag\n3. Push\n", encoding="utf-8")

        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0

        content = releasing.read_text(encoding="utf-8")
        assert "Version bump" in content, "Original content should be preserved"
        assert "PyPI" in content, "PyPI section should be appended"


def test_releasing_md_skipped_when_pypi_exists():
    """RELEASING.md with existing PyPI content should not be modified."""
    fixture = ProjectFixture(
        name="releasing_skip",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        releasing = project_dir / "RELEASING.md"
        original = "# Releasing\n\n## PyPI Publishing\n\nAlready documented.\n"
        releasing.write_text(original, encoding="utf-8")

        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0

        content = releasing.read_text(encoding="utf-8")
        assert content == original, "RELEASING.md should not be modified when PyPI section exists"


# ─── Unit tests for detection helpers ──────────────────────────

import subprocess
import tempfile


def test_detect_github_owner_repo_ssh():
    """Detect owner/repo from SSH git remote URL."""
    from pyuvstarter import _detect_github_owner_repo
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        subprocess.run(["git", "init", str(root)], capture_output=True)
        subprocess.run(["git", "-C", str(root), "remote", "add", "origin",
                        "git@github.com:testuser/testrepo.git"], capture_output=True)
        owner, repo = _detect_github_owner_repo(root)
        assert owner == "testuser"
        assert repo == "testrepo"


def test_detect_github_owner_repo_https():
    """Detect owner/repo from HTTPS git remote URL."""
    from pyuvstarter import _detect_github_owner_repo
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        subprocess.run(["git", "init", str(root)], capture_output=True)
        subprocess.run(["git", "-C", str(root), "remote", "add", "origin",
                        "https://github.com/myorg/myproject.git"], capture_output=True)
        owner, repo = _detect_github_owner_repo(root)
        assert owner == "myorg"
        assert repo == "myproject"


def test_detect_github_owner_repo_no_remote():
    """Return (None, None) when no git remote exists."""
    from pyuvstarter import _detect_github_owner_repo
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        subprocess.run(["git", "init", str(root)], capture_output=True)
        owner, repo = _detect_github_owner_repo(root)
        assert owner is None
        assert repo is None


def test_detect_github_owner_repo_not_git_dir():
    """Return (None, None) when directory is not a git repo."""
    from pyuvstarter import _detect_github_owner_repo
    with tempfile.TemporaryDirectory() as td:
        owner, repo = _detect_github_owner_repo(Path(td))
        assert owner is None
        assert repo is None


def test_detect_default_branch_fallback():
    """Return 'main' when no remote HEAD is set."""
    from pyuvstarter import _detect_default_branch
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        subprocess.run(["git", "init", str(root)], capture_output=True)
        branch = _detect_default_branch(root)
        assert branch == "main"


def test_detect_build_backend_hatchling():
    """Hatchling backend should use uv build/publish (uv handles any PEP 517 backend)."""
    from pyuvstarter import _detect_build_backend
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text(
            '[build-system]\nbuild-backend = "hatchling.build"\n'
        )
        build_cmd, publish_cmd = _detect_build_backend(root)
        assert build_cmd == "uv build"
        assert publish_cmd == "uv publish"


def test_detect_build_backend_poetry():
    """Detect poetry build backend."""
    from pyuvstarter import _detect_build_backend
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text(
            '[build-system]\nbuild-backend = "poetry.core.masonry.api"\n'
        )
        build_cmd, publish_cmd = _detect_build_backend(root)
        assert build_cmd == "poetry build"
        assert publish_cmd == "poetry publish"


def test_detect_build_backend_setuptools():
    """Setuptools backend should use uv build/publish (uv handles any PEP 517 backend)."""
    from pyuvstarter import _detect_build_backend
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text(
            '[build-system]\nbuild-backend = "setuptools.build_meta"\n'
        )
        build_cmd, publish_cmd = _detect_build_backend(root)
        assert build_cmd == "uv build"
        assert publish_cmd == "uv publish"


def test_detect_build_backend_default_uv():
    """Default to uv when no build backend is specified."""
    from pyuvstarter import _detect_build_backend
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "test"\n')
        build_cmd, publish_cmd = _detect_build_backend(root)
        assert build_cmd == "uv build"
        assert publish_cmd == "uv publish"


def test_detect_build_backend_no_pyproject():
    """Default to uv when pyproject.toml doesn't exist."""
    from pyuvstarter import _detect_build_backend
    with tempfile.TemporaryDirectory() as td:
        build_cmd, publish_cmd = _detect_build_backend(Path(td))
        assert build_cmd == "uv build"
        assert publish_cmd == "uv publish"


def test_detect_python_version_from_requires_python():
    """Detect Python version from requires-python field."""
    from pyuvstarter import _detect_python_version
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text(
            '[project]\nname = "test"\nrequires-python = ">=3.10"\n'
        )
        version = _detect_python_version(root)
        assert version == "3.10"


def test_detect_python_version_complex_specifier():
    """Detect Python version from complex requires-python like >=3.11,<4."""
    from pyuvstarter import _detect_python_version
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text(
            '[project]\nname = "test"\nrequires-python = ">=3.11,<4"\n'
        )
        version = _detect_python_version(root)
        assert version == "3.11"


def test_detect_python_version_fallback():
    """Fallback to 3.12 when requires-python is not set."""
    from pyuvstarter import _detect_python_version
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "test"\n')
        version = _detect_python_version(root)
        assert version == "3.12"


# ─── GitIgnore is_ignored consistency tests ──────────────────────


def test_gitignore_is_ignored_correct_semantics():
    """is_ignored should return True for files matching gitignore patterns."""
    from pyuvstarter import GitIgnore
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".gitignore").write_text("*.pyc\n__pycache__/\n")
        (root / "hello.py").write_text("x\n")
        (root / "hello.pyc").write_text("x\n")
        (root / ".gitignore").resolve()  # ensure exists

        gi = GitIgnore(root)
        assert not gi.is_ignored(root / "hello.py"), "hello.py should NOT be ignored"
        assert gi.is_ignored(root / "hello.pyc"), "hello.pyc SHOULD be ignored"
        assert not gi.is_ignored(root / ".gitignore"), ".gitignore should NOT be ignored"


def test_gitignore_is_ignored_consistent_with_get_methods():
    """is_ignored results must be consistent with get_unignored/ignored_files."""
    from pyuvstarter import GitIgnore
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".gitignore").write_text("*.log\nbuild/\n")
        (root / "app.py").write_text("x\n")
        (root / "debug.log").write_text("x\n")

        gi = GitIgnore(root)
        for f in gi.get_unignored_files():
            assert not gi.is_ignored(f), f"is_ignored inconsistent for unignored {f.name}"
        for f in gi.get_ignored_files():
            assert gi.is_ignored(f), f"is_ignored inconsistent for ignored {f.name}"


def test_gitignore_super_init_no_crash():
    """GitIgnore should not crash with newer pathspec versions (super().__init__ fix)."""
    from pyuvstarter import GitIgnore
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".gitignore").write_text("*.tmp\n")
        (root / "test.py").write_text("x\n")
        (root / "test.tmp").write_text("x\n")

        gi = GitIgnore(root)
        # These methods use inherited pathspec methods that need proper init
        assert isinstance(gi.match_file("test.tmp"), bool)
        assert isinstance(list(gi.match_tree_files(root)), list)
        unignored = gi.get_unignored_files()
        assert any(f.name == "test.py" for f in unignored)


# ─── RELEASING.md adaptive build commands ──────────────────────


def test_releasing_md_uses_detected_build_backend():
    """RELEASING.md should use detected build commands via _create_releasing_doc."""
    from pyuvstarter import _create_releasing_doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text(
            '[project]\nname = "test_backend"\nversion = "0.1.0"\n'
            '\n[build-system]\nbuild-backend = "hatchling.build"\nrequires = ["hatchling"]\n'
        )
        result = _create_releasing_doc(root, dry_run=False, build_cmd="uv build", publish_cmd="uv publish")
        assert result is True
        releasing = root / "RELEASING.md"
        assert releasing.exists()
        content = releasing.read_text()
        assert "uv build" in content, "Should use uv build"
        assert "uv publish" in content, "Should use uv publish"


def test_publish_yml_uses_detected_python_version():
    """publish.yml should use detected Python version from requires-python."""
    fixture = ProjectFixture(
        name="publish_pyver",
        files={
            "main.py": "print('hello')\n",
            "pyproject.toml": '[project]\nname = "publish_pyver"\nversion = "0.1.0"\nrequires-python = ">=3.10"\n',
        },
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        publish_yml = project_dir / ".github" / "workflows" / "publish.yml"
        assert publish_yml.exists()
        yml_content = publish_yml.read_text()
        assert "3.10" in yml_content, "Should use detected Python 3.10"
        assert "3.13" not in yml_content, "Should NOT hardcode 3.13"


def test_releasing_md_uses_detected_owner():
    """RELEASING.md should use detected git owner, not USERNAME placeholder."""
    fixture = ProjectFixture(
        name="releasing_owner",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )
    with temp_manager.create_temp_project(fixture) as project_dir:
        # Set up git remote
        subprocess.run(["git", "init", str(project_dir)], capture_output=True)
        subprocess.run(["git", "-C", str(project_dir), "remote", "add", "origin",
                        "git@github.com:testowner/releasing_owner.git"], capture_output=True)

        result = executor.run_pyuvstarter(project_dir, args=["--prepare-pypi", "--verbose"])
        assert result.returncode == 0, f"exit={result.returncode}\nstderr: {result.stderr}"

        releasing = project_dir / "RELEASING.md"
        assert releasing.exists()
        content = releasing.read_text()
        assert "testowner" in content, "Should use detected owner"
        assert "USERNAME" not in content, "Should NOT have USERNAME placeholder"


# ── Format-preserving TOML insertion tests ─────────────────────────


def test_add_pypi_toml_metadata_preserves_formatting():
    """_add_pypi_toml_metadata should not reformat existing pyproject.toml content."""
    from pyuvstarter import _add_pypi_toml_metadata

    fixture = ProjectFixture(
        name="toml_format_preserve",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        # Write a carefully formatted pyproject.toml with comments and multi-line arrays
        original_content = textwrap.dedent("""\
            [build-system]
            requires = ["hatchling"]
            build-backend = "hatchling.build"

            [project]
            name = "test-project"
            version = "0.1.0"
            description = "A test project"
            readme = "README.md"
            requires-python = ">=3.12"
            license = {text = "MIT"}
            authors = [
                {name = "Test Author", email = "test@example.com"}
            ]
            keywords = ["test", "project"]
            classifiers = [
                "Development Status :: 3 - Alpha",
                "Intended Audience :: Developers",
            ]
            # This is an important comment
            dependencies = [
                "click>=8.0",
                "rich>=13.0",
            ]

            [project.urls]
            Homepage = "https://github.com/test/test-project"
            Repository = "https://github.com/test/test-project"
            Issues = "https://github.com/test/test-project/issues"

            [tool.ruff]
            line-length = 120
            # Keep this comment too
            target-version = "py312"
        """)
        pyproject_path = project_dir / "pyproject.toml"
        pyproject_path.write_text(original_content, encoding="utf-8")

        # Run _add_pypi_toml_metadata — should only add Changelog URL
        result = _add_pypi_toml_metadata(project_dir, "MIT", dry_run=False, owner="testowner")
        assert result is True

        modified = pyproject_path.read_text(encoding="utf-8")

        # Comments must be preserved
        assert "# This is an important comment" in modified
        assert "# Keep this comment too" in modified

        # Multi-line arrays must NOT be collapsed to single lines
        assert '    "click>=8.0",' in modified
        assert '    "rich>=13.0",' in modified

        # Inline tables must be preserved
        assert '{text = "MIT"}' in modified

        # Section order must be preserved (build-system before project before tool)
        build_pos = modified.index("[build-system]")
        project_pos = modified.index("[project]")
        ruff_pos = modified.index("[tool.ruff]")
        assert build_pos < project_pos < ruff_pos

        # The only addition should be the Changelog URL
        assert 'Changelog = "https://github.com/testowner/test-project/releases"' in modified


def test_add_pypi_toml_metadata_adds_missing_fields():
    """_add_pypi_toml_metadata should insert missing fields without disrupting existing content."""
    from pyuvstarter import _add_pypi_toml_metadata

    fixture = ProjectFixture(
        name="toml_add_fields",
        files={"main.py": "print('hello')\n"},
        directories=[],
        expected_packages=[],
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        # Minimal pyproject.toml — missing most PyPI fields
        original = textwrap.dedent("""\
            [build-system]
            requires = ["hatchling"]
            build-backend = "hatchling.build"

            [project]
            name = "my-tool"
            version = "0.1.0"
            # keep this comment
            dependencies = ["click"]
        """)
        pyproject_path = project_dir / "pyproject.toml"
        pyproject_path.write_text(original, encoding="utf-8")

        result = _add_pypi_toml_metadata(project_dir, "Apache-2.0", dry_run=False, owner="jdoe")
        assert result is True

        modified = pyproject_path.read_text(encoding="utf-8")

        # Comment preserved
        assert "# keep this comment" in modified

        # Missing fields were added
        assert 'readme = "README.md"' in modified
        assert "Apache-2.0" in modified
        assert "authors" in modified
        assert "classifiers" in modified
        assert "keywords" in modified

        # URLs section created with all 4 keys
        assert "[project.urls]" in modified
        assert 'Homepage = "https://github.com/jdoe/my-tool"' in modified
        assert 'Changelog = "https://github.com/jdoe/my-tool/releases"' in modified

        # Original content still present
        assert 'dependencies = ["click"]' in modified


def test_find_toml_section_range():
    """_find_toml_section_range should correctly identify section boundaries."""
    from pyuvstarter import _find_toml_section_range

    lines = [
        "[build-system]\n",
        'requires = ["hatchling"]\n',
        "\n",
        "[project]\n",
        'name = "test"\n',
        'version = "0.1.0"\n',
        "\n",
        "[project.urls]\n",
        'Homepage = "https://example.com"\n',
        "\n",
        "[tool.ruff]\n",
        "line-length = 120\n",
    ]

    # [project] section includes sub-tables like [project.urls], so it spans 3-8
    start, end = _find_toml_section_range(lines, "[project]")
    assert start == 3
    assert end == 9  # after Homepage line (includes [project.urls] sub-table)

    # [project.urls] section: lines 7-8, insert at 9
    start, end = _find_toml_section_range(lines, "[project.urls]")
    assert start == 7
    assert end == 9

    # Non-existent section
    start, end = _find_toml_section_range(lines, "[missing]")
    assert start == -1
    assert end == -1


# ── Step 1d: flit backend uses uv ──────────────────────────────────────────────


def test_detect_build_backend_flit_uses_uv():
    """Flit backend should also use uv build/publish."""
    from pyuvstarter import _detect_build_backend
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text(
            '[build-system]\nbuild-backend = "flit_core.buildapi"\n'
        )
        build_cmd, publish_cmd = _detect_build_backend(root)
        assert build_cmd == "uv build"
        assert publish_cmd == "uv publish"


# ── Step 3: publish.yml uses python3, not uv run python ───────────────────────


def test_publish_yml_uses_uv_run_no_project():
    """publish.yml version check should use 'uv run --no-project python' to avoid dependency resolution."""
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".github" / "workflows").mkdir(parents=True)
        result = _create_publish_workflow(root, dry_run=False)
        assert result is True
        content = (root / ".github" / "workflows" / "publish.yml").read_text()
        assert "uv run --no-project python -c" in content, "Should use uv run --no-project python"
        # Must NOT use bare 'uv run python' (would trigger dependency resolution)
        assert "uv run python -c" not in content.replace("uv run --no-project python -c", ""), "Should NOT use bare uv run python"


# ── Step 5: publish.yml update capability ──────────────────────────────────────


def test_publish_yml_updates_hatch_to_uv():
    """Re-running should update publish.yml from hatch build to uv build."""
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        old_content = "name: Publish\njobs:\n  build:\n    steps:\n      - run: hatch build\n"
        (wf_dir / "publish.yml").write_text(old_content)
        result = _create_publish_workflow(root, dry_run=False, build_cmd="uv build")
        assert result is True
        new_content = (wf_dir / "publish.yml").read_text()
        assert "uv build" in new_content, "Should have uv build after update"
        assert "hatch build" not in new_content, "Should NOT have hatch build after update"


def test_publish_yml_skip_if_already_correct():
    """If publish.yml already uses uv build, skip without changes."""
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        correct_content = "name: Publish\njobs:\n  build:\n    steps:\n      - run: uv build\n"
        (wf_dir / "publish.yml").write_text(correct_content)
        result = _create_publish_workflow(root, dry_run=False, build_cmd="uv build")
        assert result is True
        assert (wf_dir / "publish.yml").read_text() == correct_content, "Should not modify correct file"


def test_publish_yml_respects_dry_run_on_update():
    """Dry run should not modify existing publish.yml even if outdated."""
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        old_content = "name: Publish\njobs:\n  build:\n    steps:\n      - run: hatch build\n"
        (wf_dir / "publish.yml").write_text(old_content)
        result = _create_publish_workflow(root, dry_run=True, build_cmd="uv build")
        assert result is True
        assert (wf_dir / "publish.yml").read_text() == old_content, "Dry run should not modify"


# ── Step 7: RELEASING.md update capability ─────────────────────────────────────


def test_releasing_md_updates_hatch_to_uv():
    """Re-running should update RELEASING.md from hatch to uv commands."""
    from pyuvstarter import _create_releasing_doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "myproj"\nversion = "0.1.0"\n')
        releasing = root / "RELEASING.md"
        releasing.write_text("# Releasing\n\n## PyPI Publishing\nhatch build\nhatch publish\n")
        result = _create_releasing_doc(root, dry_run=False, build_cmd="uv build", publish_cmd="uv publish")
        assert result is True
        content = releasing.read_text()
        assert "uv build" in content
        assert "uv publish" in content
        assert "hatch build" not in content
        assert "hatch publish" not in content


def test_releasing_md_skip_if_already_uv():
    """RELEASING.md with uv commands should not be modified."""
    from pyuvstarter import _create_releasing_doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "myproj"\nversion = "0.1.0"\n')
        releasing = root / "RELEASING.md"
        original = "# Releasing\n\n## PyPI Publishing\nuv build\nuv publish\n"
        releasing.write_text(original)
        result = _create_releasing_doc(root, dry_run=False, build_cmd="uv build", publish_cmd="uv publish")
        assert result is True
        assert releasing.read_text() == original, "Should not modify"


def test_releasing_md_respects_dry_run_on_update():
    """Dry run should not modify existing RELEASING.md even if outdated."""
    from pyuvstarter import _create_releasing_doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "myproj"\nversion = "0.1.0"\n')
        releasing = root / "RELEASING.md"
        old_content = "# Releasing\n\n## PyPI Publishing\nhatch build\nhatch publish\n"
        releasing.write_text(old_content)
        result = _create_releasing_doc(root, dry_run=True, build_cmd="uv build", publish_cmd="uv publish")
        assert result is True
        assert releasing.read_text() == old_content, "Dry run should not modify"


# ── Step 9: PyPI project name normalization ────────────────────────────────────


def test_releasing_md_normalizes_project_name():
    """RELEASING.md should show PyPI-normalized project name (underscores -> hyphens)."""
    from pyuvstarter import _create_releasing_doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "my_cool_tool"\nversion = "0.1.0"\n')
        result = _create_releasing_doc(root, dry_run=False, owner="testowner")
        assert result is True
        content = (root / "RELEASING.md").read_text()
        assert "my-cool-tool" in content, "Should show PyPI-normalized name"


# ── Edge case tests ────────────────────────────────────────────────────────────


def test_detect_build_backend_pdm_uses_uv():
    """Unknown backend (pdm) should fall through to uv build/publish."""
    from pyuvstarter import _detect_build_backend
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text(
            '[build-system]\nbuild-backend = "pdm.backend"\n'
        )
        build_cmd, publish_cmd = _detect_build_backend(root)
        assert build_cmd == "uv build"
        assert publish_cmd == "uv publish"


def test_releasing_md_updates_pip_to_uv_pip():
    """RELEASING.md TestPyPI verification should use uv pip install."""
    from pyuvstarter import _create_releasing_doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "myproj"\nversion = "0.1.0"\n')
        result = _create_releasing_doc(root, dry_run=False, owner="testowner")
        assert result is True
        content = (root / "RELEASING.md").read_text()
        assert "uv pip install" in content, "Should use uv pip install for TestPyPI verification"
        # Should NOT have bare 'pip install' (without 'uv' prefix)
        for line in content.split("\n"):
            if "pip install" in line:
                assert "uv pip install" in line, f"Bare pip install found: {line}"


def test_publish_yml_setuptools_also_triggers_update():
    """publish.yml with 'python -m build' should also be detected as outdated."""
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        old_content = "name: Publish\njobs:\n  build:\n    steps:\n      - run: python -m build\n"
        (wf_dir / "publish.yml").write_text(old_content)
        result = _create_publish_workflow(root, dry_run=False, build_cmd="uv build")
        assert result is True
        new_content = (wf_dir / "publish.yml").read_text()
        assert "uv build" in new_content, "Should have uv build after update"
        assert "python -m build" not in new_content, "Should NOT have python -m build"


def test_publish_yml_flit_also_triggers_update():
    """publish.yml with 'flit build' should also be detected as outdated."""
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        old_content = "name: Publish\njobs:\n  build:\n    steps:\n      - run: flit build\n"
        (wf_dir / "publish.yml").write_text(old_content)
        result = _create_publish_workflow(root, dry_run=False, build_cmd="uv build")
        assert result is True
        new_content = (wf_dir / "publish.yml").read_text()
        assert "uv build" in new_content
        assert "flit build" not in new_content


def test_releasing_md_normalizes_dots_and_mixed_case():
    """PyPI normalizes dots, mixed case: My.Cool.Tool -> my-cool-tool."""
    from pyuvstarter import _create_releasing_doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "My.Cool.Tool"\nversion = "0.1.0"\n')
        result = _create_releasing_doc(root, dry_run=False, owner="testowner")
        assert result is True
        content = (root / "RELEASING.md").read_text()
        assert "my-cool-tool" in content, "Should normalize dots, mixed case to hyphens-lowercase"


def test_releasing_md_already_normalized_name_unchanged():
    """Already-normalized project name should pass through unchanged."""
    from pyuvstarter import _create_releasing_doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "my-project"\nversion = "0.1.0"\n')
        result = _create_releasing_doc(root, dry_run=False, owner="testowner")
        assert result is True
        content = (root / "RELEASING.md").read_text()
        assert "my-project" in content


def test_releasing_md_consecutive_separators():
    """Consecutive underscores/dots normalize to single hyphen (PEP 503)."""
    from pyuvstarter import _create_releasing_doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "my__tool"\nversion = "0.1.0"\n')
        result = _create_releasing_doc(root, dry_run=False, owner="testowner")
        assert result is True
        content = (root / "RELEASING.md").read_text()
        assert "my-tool" in content, "Consecutive underscores should normalize to single hyphen"
        assert "my--tool" not in content, "Should NOT have double hyphens"


def test_releasing_md_updates_twine_to_uv():
    """RELEASING.md with 'twine upload dist/*' should be updated to 'uv publish'."""
    from pyuvstarter import _create_releasing_doc
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "myproj"\nversion = "0.1.0"\n')
        releasing = root / "RELEASING.md"
        releasing.write_text("# Releasing\n\n## PyPI Publishing\npython -m build\ntwine upload dist/*\n")
        result = _create_releasing_doc(root, dry_run=False, build_cmd="uv build", publish_cmd="uv publish")
        assert result is True
        content = releasing.read_text()
        assert "uv build" in content
        assert "uv publish" in content
        assert "python -m build" not in content
        assert "twine upload" not in content


def test_publish_yml_test_job_has_permissions_block():
    """Generated publish.yml test job must have permissions block (prevents startup_failure).

    Without permissions on the test: job that calls ci.yml via workflow_call,
    GitHub fails the entire workflow at launch with startup_failure.
    Reference: ~/.claude/ai_session_tools/.github/workflows/publish.yml:17-21
    """
    import tempfile
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yml").write_text(
            "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        result = _create_publish_workflow(root, dry_run=False)
        assert result is True
        content = (wf_dir / "publish.yml").read_text()
        assert "uses: ./.github/workflows/ci.yml" in content
        # permissions block must appear AFTER the uses: line and BEFORE build:
        ci_ref_idx = content.find("uses: ./.github/workflows/ci.yml")
        build_idx = content.find("build:", ci_ref_idx)
        between = content[ci_ref_idx:build_idx]
        assert "permissions:" in between, (
            "permissions: block must appear between test: uses: line and build: job"
        )
        assert "checks: write" in between
        assert "pull-requests: write" in between


def test_publish_yml_updates_missing_permissions_block():
    """Re-running should add permissions block to existing publish.yml that lacks it (startup_failure fix)."""
    import tempfile
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        # Simulate old publish.yml without permissions block (ci.yml must exist for test: job to appear)
        (wf_dir / "ci.yml").write_text(
            "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        old_content = (
            "name: Publish\njobs:\n"
            "  test:\n    uses: ./.github/workflows/ci.yml\n"
            "  build:\n    needs: test\n    steps:\n      - run: uv build\n"
        )
        (wf_dir / "publish.yml").write_text(old_content)
        result = _create_publish_workflow(root, dry_run=False)
        assert result is True
        new_content = (wf_dir / "publish.yml").read_text()
        ci_ref_idx = new_content.find("uses: ./.github/workflows/ci.yml")
        build_idx = new_content.find("build:", ci_ref_idx)
        between = new_content[ci_ref_idx:build_idx]
        assert "permissions:" in between, "permissions block should be added on update"


# ─── CI filename detection ────────────────────────────────────────────────────


def test_detect_ci_workflow_name_returns_ci_yml_first():
    """ci.yml takes priority over test.yml when both exist."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        (wf_dir / "ci.yml").write_text("on: push\n")
        (wf_dir / "test.yml").write_text("on: push\n")
        assert _detect_ci_workflow_name(wf_dir) == "ci.yml"


def test_detect_ci_workflow_name_falls_back_to_test_yml():
    """Falls back to test.yml when ci.yml is absent."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        (wf_dir / "test.yml").write_text("on: push\n")
        assert _detect_ci_workflow_name(wf_dir) == "test.yml"


def test_detect_ci_workflow_name_returns_none_when_absent():
    """Returns None when no known CI workflow file exists."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        assert _detect_ci_workflow_name(Path(td)) is None


def test_publish_yml_references_detected_ci_filename():
    """publish.yml test: job references test.yml when that is the CI file (not hardcoded ci.yml)."""
    import tempfile
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "test.yml").write_text(
            "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        result = _create_publish_workflow(root, dry_run=False)
        assert result is True
        content = (wf_dir / "publish.yml").read_text()
        assert "uses: ./.github/workflows/test.yml" in content, \
            "publish.yml must reference test.yml when that is the detected CI workflow"
        assert "uses: ./.github/workflows/ci.yml" not in content, \
            "publish.yml must NOT hardcode ci.yml when the CI file is test.yml"


def test_add_workflow_call_trigger_injects_into_test_yml():
    """workflow_call trigger is injected into test.yml when that is the detected CI workflow."""
    import tempfile
    from pyuvstarter import _add_workflow_call_trigger
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "test.yml").write_text(
            "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        result = _add_workflow_call_trigger(root, dry_run=False)
        assert result is True
        content = (wf_dir / "test.yml").read_text()
        assert "workflow_call" in content, \
            "workflow_call trigger should be injected into test.yml, not ci.yml"


def test_publish_yml_permissions_detection_not_fooled_by_build_docs_job():
    """Permissions detection uses regex job-boundary, not split('build:') which breaks on 'build-docs:'."""
    import tempfile
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yml").write_text(
            "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        # Simulate old publish.yml where 'build-docs:' appears before 'build:'
        # Old split("build:")[0] approach would split at 'build-docs:' and find nothing → no update
        old_content = (
            "name: Publish\njobs:\n"
            "  test:\n    uses: ./.github/workflows/ci.yml\n"
            "  build-docs:\n    needs: test\n"
            "  build:\n    needs: test\n    steps:\n      - run: uv build\n"
        )
        (wf_dir / "publish.yml").write_text(old_content)
        result = _create_publish_workflow(root, dry_run=False)
        assert result is True
        new_content = (wf_dir / "publish.yml").read_text()
        ci_ref_idx = new_content.find("uses: ./.github/workflows/ci.yml")
        next_build_idx = new_content.find("\n  build", ci_ref_idx)
        between = new_content[ci_ref_idx:next_build_idx]
        assert "permissions:" in between, \
            "Regex-based job-boundary detection must correctly regenerate permissions block"


def test_detect_ci_workflow_name_falls_back_to_workflow_yml():
    """Falls back to workflow.yml when no higher-priority CI file exists (GitHub UI default name)."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        (wf_dir / "workflow.yml").write_text("on: push\n")
        assert _detect_ci_workflow_name(wf_dir) == "workflow.yml"


def test_detect_ci_workflow_name_falls_back_to_python_yml():
    """Falls back to python.yml (GitHub's Python starter workflow template name)."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        (wf_dir / "python.yml").write_text("on: push\n")
        assert _detect_ci_workflow_name(wf_dir) == "python.yml"


def test_publish_yml_references_workflow_yml_when_detected():
    """publish.yml test: job references workflow.yml when that is the only CI file found."""
    import tempfile
    from pyuvstarter import _create_publish_workflow
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        wf_dir = root / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "workflow.yml").write_text(
            "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        result = _create_publish_workflow(root, dry_run=False)
        assert result is True
        content = (wf_dir / "publish.yml").read_text()
        assert "uses: ./.github/workflows/workflow.yml" in content, \
            "publish.yml must reference workflow.yml when that is the detected CI workflow"
        assert "uses: ./.github/workflows/ci.yml" not in content, \
            "publish.yml must NOT hardcode ci.yml when the CI file is workflow.yml"


# ─── _is_publish_workflow detection ───────────────────────────────────────────


def test_is_publish_workflow_detects_pypa_action():
    """Tier 1: pypa/gh-action-pypi-publish is the definitive publish workflow tell."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("      - uses: pypa/gh-action-pypi-publish@release/v1\n") is True


def test_is_publish_workflow_detects_pypa_action_sha_pinned():
    """Tier 1: SHA-pinned pypa action is also detected (substring match)."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow(
        "      - uses: pypa/gh-action-pypi-publish@ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e # release/v1\n"
    ) is True


def test_is_publish_workflow_detects_pypi_environment_single_value():
    """Tier 2a: environment: pypi (single-value) is a strong publish tell."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("    environment: pypi\n") is True
    assert _is_publish_workflow("    environment: testpypi\n") is True


def test_is_publish_workflow_detects_pypi_environment_with_inline_comment():
    """Tier 2a: environment: pypi # comment (inline comment) still matches."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("    environment: pypi # OIDC trusted publisher\n") is True
    assert _is_publish_workflow("    environment: testpypi # test only\n") is True


def test_is_publish_workflow_does_not_match_pypi_staging():
    """Tier 2a: environment: pypi-staging must NOT match (partial name)."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("    environment: pypi-staging\n") is False


def test_is_publish_workflow_detects_dict_form_environment():
    """Tier 2b: environment:\\n  name: pypi (dict form) is detected."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("    environment:\n      name: pypi\n") is True
    assert _is_publish_workflow("    environment:\n      name: testpypi\n") is True


def test_is_publish_workflow_dict_form_does_not_match_job_display_name():
    """Tier 2b: 'name: pypi tests' (job display name) must NOT match (EOL anchor)."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("    name: pypi tests and checks\n") is False


def test_is_publish_workflow_detects_twine_upload_in_run_step():
    """Tier 3: run: step with twine upload is a publish tell."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("      - run: twine upload dist/*\n") is True


def test_is_publish_workflow_detects_python_m_twine_upload():
    """Tier 3: run: python -m twine upload is also detected."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("      - run: python -m twine upload dist/*\n") is True


def test_is_publish_workflow_twine_in_comment_does_not_match():
    """Tier 3: twine in a comment line (no run: prefix) must NOT match."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("        # TODO: twine upload dist/*\n") is False


def test_is_publish_workflow_detects_uv_publish_in_run_step():
    """Tier 3: run: uv publish is a publish tell."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("      - run: uv publish\n") is True
    assert _is_publish_workflow("      - run: uv publish --index-url https://test.pypi.org/\n") is True


def test_is_publish_workflow_uv_publish_in_comment_does_not_match():
    """Tier 3: uv publish in a comment must NOT match."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("        # Alternative: uv publish --dry-run\n") is False


def test_is_publish_workflow_uv_build_does_not_match():
    """'uv build' alone is NOT a publish tell (only uv publish triggers detection)."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("      - run: uv build\n") is False


def test_is_publish_workflow_returns_false_for_ci_content():
    """Normal CI workflow content must return False."""
    from pyuvstarter import _is_publish_workflow
    ci_content = (
        "on:\n  push:\n  pull_request:\n"
        "jobs:\n  test:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - run: pytest\n"
    )
    assert _is_publish_workflow(ci_content) is False


def test_is_publish_workflow_empty_content_returns_false():
    """Empty file content returns False."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("") is False


def test_detect_ci_workflow_name_skips_publish_workflow_named_build():
    """build.yml containing pypa/gh-action-pypi-publish must be skipped; test.yml is returned."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        # build.yml is a publish workflow (contains pypi action)
        (wf_dir / "build.yml").write_text(
            "on:\n  push:\n    tags: ['v*']\n"
            "jobs:\n  publish:\n"
            "    steps:\n      - uses: pypa/gh-action-pypi-publish@release/v1\n"
        )
        # test.yml is the real CI workflow
        (wf_dir / "test.yml").write_text(
            "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        result = _detect_ci_workflow_name(wf_dir)
        assert result == "test.yml", (
            f"build.yml containing pypa/gh-action-pypi-publish must be skipped; "
            f"test.yml should be returned as CI workflow, got: {result!r}"
        )


def test_detect_ci_workflow_name_skips_workflow_with_uv_publish():
    """workflow.yml containing 'run: uv publish' is skipped; ci.yml is returned."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        (wf_dir / "workflow.yml").write_text(
            "on:\n  push:\n    tags: ['v*']\n"
            "jobs:\n  release:\n    steps:\n      - run: uv publish\n"
        )
        (wf_dir / "ci.yml").write_text(
            "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        result = _detect_ci_workflow_name(wf_dir)
        assert result == "ci.yml", (
            f"workflow.yml with uv publish must be skipped; ci.yml should be returned, got: {result!r}"
        )


# ─── DRY RUN log uses detected CI filename (C5) ───────────────────────────────


def test_add_workflow_call_trigger_dry_run_does_not_modify_file(tmp_path):
    """DRY RUN must not modify the CI file — only reports what would happen."""
    from pyuvstarter import _add_workflow_call_trigger
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    original = "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
    (wf_dir / "test.yml").write_text(original)
    result = _add_workflow_call_trigger(tmp_path, dry_run=True)
    assert result is True
    assert (wf_dir / "test.yml").read_text() == original, \
        "DRY RUN must not modify any files"


def test_add_workflow_call_trigger_dry_run_log_uses_ci_filename(tmp_path):
    """DRY RUN log must reference the detected CI filename, not hardcoded 'ci.yml'."""
    from unittest.mock import patch
    from pyuvstarter import _add_workflow_call_trigger
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "test.yml").write_text(
        "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
    )
    with patch("pyuvstarter._log_action") as mock_log:
        _add_workflow_call_trigger(tmp_path, dry_run=True)
        dry_run_calls = [c for c in mock_log.call_args_list if "DRY RUN" in str(c)]
        assert dry_run_calls, "Expected at least one DRY RUN _log_action call"
        dry_run_msg = str(dry_run_calls[0])
        assert "test.yml" in dry_run_msg, \
            f"DRY RUN log must use ci_filename='test.yml', got: {dry_run_msg}"
        assert "ci.yml" not in dry_run_msg, \
            f"DRY RUN log must not hardcode 'ci.yml', got: {dry_run_msg}"


# ─── _is_publish_workflow: additional Tier 3 variants ─────────────────────────


def test_is_publish_workflow_detects_python3_m_twine_upload():
    """Tier 3: python3 -m twine upload is detected (whole-word 'twine' and 'upload' present)."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("      - run: python3 -m twine upload dist/*\n") is True


def test_is_publish_workflow_detects_uv_run_twine_upload():
    """Tier 3: uv run twine upload is detected (whole-word 'twine' and 'upload' present)."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("      - run: uv run twine upload dist/*\n") is True


def test_is_publish_workflow_detects_twine_upload_with_flags():
    """Tier 3: twine upload with extra flags is detected."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("      - run: twine upload --skip-existing dist/*\n") is True
    assert _is_publish_workflow(
        "      - run: twine upload --repository testpypi dist/*.whl\n"
    ) is True


def test_is_publish_workflow_twine_check_does_not_match():
    """Tier 3: 'run: twine check' is NOT a publish tell (no 'upload' word)."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("      - run: twine check dist/*\n") is False


def test_is_publish_workflow_detects_compound_uv_build_and_publish():
    """Tier 3: compound command 'uv build && uv publish' on one run: line is detected."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("      - run: uv build && uv publish\n") is True


def test_is_publish_workflow_multiline_run_block_not_caught_by_tier3():
    """Tier 3 limitation: multi-line run: | block with twine on next line is NOT detected.

    This is the documented design trade-off: scoping to the run: line avoids
    comment false-positives. Such workflows are still caught by Tier 1 (pypa action)
    or Tier 2 (environment: pypi) if present.
    """
    from pyuvstarter import _is_publish_workflow
    multiline_run_content = (
        "jobs:\n  publish:\n    steps:\n"
        "      - name: Upload to PyPI\n"
        "        run: |\n"
        "          twine upload dist/*\n"
    )
    # Tier 3 does NOT catch multi-line run blocks — this is expected behavior.
    # (The workflow would still be caught by Tier 1 or Tier 2 in a real publish workflow.)
    assert _is_publish_workflow(multiline_run_content) is False


def test_is_publish_workflow_multiline_run_caught_by_tier1():
    """When multi-line run: block is the only Tier-3 tell, Tier 1 must catch it."""
    from pyuvstarter import _is_publish_workflow
    content = (
        "jobs:\n  publish:\n    steps:\n"
        "      - name: Upload to PyPI\n"
        "        run: |\n"
        "          twine upload dist/*\n"
        "      - uses: pypa/gh-action-pypi-publish@release/v1\n"
    )
    assert _is_publish_workflow(content) is True


def test_is_publish_workflow_uv_publish_with_env_vars():
    """Tier 3: uv publish with env var prefix on same run: line is detected."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow(
        "      - run: UV_PUBLISH_TOKEN=${{ secrets.PYPI_TOKEN }} uv publish\n"
    ) is True


def test_is_publish_workflow_complete_realistic_publish_yaml():
    """Full realistic publish workflow YAML must be detected (all tiers present)."""
    from pyuvstarter import _is_publish_workflow
    content = (
        "name: Publish to PyPI\n"
        "on:\n  push:\n    tags: ['v*']\n"
        "jobs:\n"
        "  publish:\n"
        "    runs-on: ubuntu-latest\n"
        "    permissions:\n"
        "      id-token: write\n"
        "    environment: pypi\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: astral-sh/setup-uv@v4\n"
        "      - run: uv build\n"
        "      - uses: pypa/gh-action-pypi-publish@release/v1\n"
    )
    assert _is_publish_workflow(content) is True


def test_is_publish_workflow_complete_realistic_ci_yaml():
    """Full realistic CI workflow YAML must NOT be detected as a publish workflow."""
    from pyuvstarter import _is_publish_workflow
    content = (
        "name: CI\n"
        "on:\n  push:\n  pull_request:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - name: Install deps\n"
        "        run: pip install pytest\n"
        "      - name: Run tests\n"
        "        run: pytest tests/ -v\n"
        "      - name: Build docs\n"
        "        run: uv build --wheel\n"
    )
    assert _is_publish_workflow(content) is False


def test_is_publish_workflow_tier2a_crlf_line_endings():
    """Tier 2a: environment: pypi with CRLF line endings (Windows-created files) is detected."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("    environment: pypi\r\n") is True
    assert _is_publish_workflow("    environment: testpypi\r\n") is True


def test_is_publish_workflow_tier2b_crlf_line_endings():
    """Tier 2b: name: pypi dict-form with CRLF line endings is detected."""
    from pyuvstarter import _is_publish_workflow
    assert _is_publish_workflow("    environment:\r\n      name: pypi\r\n") is True


def test_is_publish_workflow_pypi_in_workflow_name_does_not_match():
    """Workflow name mentioning 'pypi' in a job display name must NOT trigger Tier 2b."""
    from pyuvstarter import _is_publish_workflow
    # "name: Run pypi tests" — job display name, not environment name
    assert _is_publish_workflow("    name: Run pypi tests\n") is False
    # "name: pypi-tests" — partial match guard (EOL anchor)
    assert _is_publish_workflow("    name: pypi-tests\n") is False


# ─── _detect_ci_workflow_name: additional candidate and edge case tests ────────


def test_detect_ci_workflow_name_falls_back_to_tests_yml():
    """Falls back to tests.yml (plural) when no higher-priority file exists."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        (wf_dir / "tests.yml").write_text("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
        assert _detect_ci_workflow_name(wf_dir) == "tests.yml"


def test_detect_ci_workflow_name_falls_back_to_python_app_yml():
    """Falls back to python-app.yml (GitHub Python Application starter template)."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        (wf_dir / "python-app.yml").write_text("on:\n  push:\njobs:\n  build:\n    runs-on: ubuntu-latest\n")
        assert _detect_ci_workflow_name(wf_dir) == "python-app.yml"


def test_detect_ci_workflow_name_falls_back_to_python_package_yml():
    """Falls back to python-package.yml (GitHub Python Package starter template)."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        # python-package.yml template may include a publish step — must confirm it
        # is NOT detected as a publish workflow when it lacks publish tells
        (wf_dir / "python-package.yml").write_text(
            "on:\n  push:\njobs:\n  build:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - run: pip install pytest\n      - run: pytest\n"
        )
        assert _detect_ci_workflow_name(wf_dir) == "python-package.yml"


def test_detect_ci_workflow_name_falls_back_to_ci_yaml():
    """Falls back to ci.yaml (.yaml extension) when no .yml variants exist."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        (wf_dir / "ci.yaml").write_text("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
        assert _detect_ci_workflow_name(wf_dir) == "ci.yaml"


def test_detect_ci_workflow_name_yml_takes_priority_over_yaml():
    """ci.yml takes priority over ci.yaml when both exist."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        (wf_dir / "ci.yml").write_text("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
        (wf_dir / "ci.yaml").write_text("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
        assert _detect_ci_workflow_name(wf_dir) == "ci.yml"


def test_detect_ci_workflow_name_all_candidates_are_publish_workflows():
    """When every matching candidate file is a publish workflow, returns None."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        publish_content = (
            "on:\n  push:\n    tags: ['v*']\n"
            "jobs:\n  publish:\n    steps:\n"
            "      - uses: pypa/gh-action-pypi-publish@release/v1\n"
        )
        # Only ci.yml and test.yml exist, both are publish workflows
        (wf_dir / "ci.yml").write_text(publish_content)
        (wf_dir / "test.yml").write_text(publish_content)
        result = _detect_ci_workflow_name(wf_dir)
        assert result is None, (
            f"All candidates are publish workflows; must return None, got: {result!r}"
        )


def test_detect_ci_workflow_name_ci_yml_is_publish_falls_back_to_test_yml():
    """ci.yml is a publish workflow → skipped; test.yml is the CI workflow → returned."""
    import tempfile
    from pyuvstarter import _detect_ci_workflow_name
    with tempfile.TemporaryDirectory() as td:
        wf_dir = Path(td)
        (wf_dir / "ci.yml").write_text(
            "on:\n  push:\n    tags: ['v*']\n"
            "jobs:\n  publish:\n    environment: pypi\n"
            "    steps:\n      - uses: pypa/gh-action-pypi-publish@release/v1\n"
        )
        (wf_dir / "test.yml").write_text(
            "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        result = _detect_ci_workflow_name(wf_dir)
        assert result == "test.yml", (
            f"ci.yml is a publish workflow and must be skipped; "
            f"test.yml should be returned, got: {result!r}"
        )


def test_detect_ci_workflow_name_nonexistent_directory_returns_none():
    """When the workflow directory does not exist, returns None without error."""
    from pyuvstarter import _detect_ci_workflow_name
    result = _detect_ci_workflow_name(Path("/tmp/nonexistent_wfdir_pyuvstarter_test"))
    assert result is None


def test_detect_ci_workflow_name_skips_unreadable_file(tmp_path):
    """OSError on read (unreadable file) is silently skipped; next candidate is tried."""
    from unittest.mock import patch, mock_open
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    # ci.yml exists but is "unreadable" (OSError on read); test.yml is readable CI
    (wf_dir / "ci.yml").write_text("on: push\n")
    (wf_dir / "test.yml").write_text("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")

    original_read_text = Path.read_text

    def mock_read(self, *args, **kwargs):
        if self.name == "ci.yml":
            raise OSError("Permission denied")
        return original_read_text(self, *args, **kwargs)

    with patch.object(Path, "read_text", mock_read):
        result = _detect_ci_workflow_name(wf_dir)

    assert result == "test.yml", (
        f"Unreadable ci.yml must be skipped; test.yml should be returned, got: {result!r}"
    )


# ─── _add_workflow_call_trigger: edge cases ────────────────────────────────────


def test_add_workflow_call_trigger_skips_when_already_present(tmp_path):
    """workflow_call already in CI file → returns True, file unchanged."""
    from pyuvstarter import _add_workflow_call_trigger
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    already_has = (
        "on:\n  push:\n  workflow_call:  # Allow publish.yml to reuse this workflow\n"
        "jobs:\n  test:\n    runs-on: ubuntu-latest\n"
    )
    (wf_dir / "ci.yml").write_text(already_has)
    result = _add_workflow_call_trigger(tmp_path, dry_run=False)
    assert result is True
    assert (wf_dir / "ci.yml").read_text() == already_has, \
        "File must be unchanged when workflow_call already present"


def test_add_workflow_call_trigger_warns_when_no_on_block(tmp_path):
    """CI file without an 'on:' block → returns True with WARN, file unchanged."""
    from unittest.mock import patch
    from pyuvstarter import _add_workflow_call_trigger
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    no_on_block = "jobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest\n"
    (wf_dir / "ci.yml").write_text(no_on_block)
    with patch("pyuvstarter._log_action") as mock_log:
        result = _add_workflow_call_trigger(tmp_path, dry_run=False)
        warn_calls = [c for c in mock_log.call_args_list if "WARN" in str(c)]
        assert warn_calls, "Expected a WARN log when 'on:' block is missing"
    assert result is True
    assert (wf_dir / "ci.yml").read_text() == no_on_block, \
        "File must be unchanged when 'on:' block is missing"


def test_add_workflow_call_trigger_warns_on_compact_on_format(tmp_path):
    """Compact 'on: push' format → returns True with WARN, file unchanged."""
    from unittest.mock import patch
    from pyuvstarter import _add_workflow_call_trigger
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    compact_on = "on: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
    (wf_dir / "ci.yml").write_text(compact_on)
    with patch("pyuvstarter._log_action") as mock_log:
        result = _add_workflow_call_trigger(tmp_path, dry_run=False)
        warn_calls = [c for c in mock_log.call_args_list if "WARN" in str(c)]
        assert warn_calls, "Expected a WARN log for compact 'on: push' format"
    assert result is True
    assert (wf_dir / "ci.yml").read_text() == compact_on, \
        "File must be unchanged for compact on: format"


def test_add_workflow_call_trigger_handles_quoted_on_block(tmp_path):
    """'\"on\":' (double-quoted form) is handled correctly — workflow_call is injected."""
    from pyuvstarter import _add_workflow_call_trigger
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    quoted_on = '"on":\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n'
    (wf_dir / "ci.yml").write_text(quoted_on)
    result = _add_workflow_call_trigger(tmp_path, dry_run=False)
    assert result is True
    content = (wf_dir / "ci.yml").read_text()
    assert "workflow_call" in content, \
        "workflow_call must be injected into workflow with double-quoted 'on': form"


def test_add_workflow_call_trigger_returns_true_when_no_ci_found(tmp_path):
    """No CI workflow found → returns True (graceful no-op), no error."""
    from pyuvstarter import _add_workflow_call_trigger
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    # No CI workflow files, only a publish.yml (not in candidates)
    (wf_dir / "publish.yml").write_text("on:\n  push:\n    tags: ['v*']\n")
    result = _add_workflow_call_trigger(tmp_path, dry_run=False)
    assert result is True


# ─── _create_publish_workflow: SHA pins and structural checks ──────────────────


def test_publish_yml_contains_sha_pinned_actions(tmp_path):
    """Generated publish.yml uses SHA-pinned action refs, not mutable tags."""
    from pyuvstarter import _create_publish_workflow
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "ci.yml").write_text("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
    result = _create_publish_workflow(tmp_path, dry_run=False)
    assert result is True
    content = (wf_dir / "publish.yml").read_text()
    # Verify each expected SHA pin is present (not mutable tags like @v4)
    assert "actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5" in content, \
        "actions/checkout must use SHA pin, not @v4"
    assert "astral-sh/setup-uv@5a095e7a2014a4212f075830d4f7277575a9d098" in content, \
        "astral-sh/setup-uv must use SHA pin, not @v7"
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in content, \
        "actions/upload-artifact must use SHA pin, not @v4"
    assert "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in content, \
        "actions/download-artifact must use SHA pin, not @v4"
    assert "pypa/gh-action-pypi-publish@ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e" in content, \
        "pypa/gh-action-pypi-publish must use SHA pin, not @release/v1"
    # Verify mutable tags are NOT present as standalone references
    assert "actions/checkout@v4" not in content
    assert "astral-sh/setup-uv@v7" not in content
    assert "actions/upload-artifact@v4" not in content
    assert "actions/download-artifact@v4" not in content
    assert "pypa/gh-action-pypi-publish@release/v1" not in content


def test_publish_yml_structural_validity_with_ci(tmp_path):
    """Generated publish.yml has all required top-level sections (with CI workflow)."""
    from pyuvstarter import _create_publish_workflow
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "ci.yml").write_text("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
    _create_publish_workflow(tmp_path, dry_run=False)
    content = (wf_dir / "publish.yml").read_text()
    # Top-level YAML structure checks (no external parser required)
    assert content.startswith("# Publish to PyPI"), "Must start with header comment"
    assert "\nname: Publish to PyPI\n" in content, "Must have name: key"
    assert "\non:\n" in content, "Must have on: trigger block"
    assert "\njobs:\n" in content, "Must have jobs: block"
    assert "\n  build:\n" in content, "Must have build: job"
    assert "\n  publish-testpypi:\n" in content, "Must have publish-testpypi: job"
    assert "\n  publish-pypi:\n" in content, "Must have publish-pypi: job"
    assert "\n  test:\n" in content, "Must have test: job when CI exists"
    # Verify no mismatched braces or obvious template errors (f-string interpolation check)
    assert "${" not in content or "GITHUB_REF" in content, \
        "Only expected ${GITHUB_REF} template var; no other unresolved f-string placeholders"


def test_publish_yml_structural_validity_without_ci(tmp_path):
    """Generated publish.yml (no CI) has required sections, omits test: job."""
    from pyuvstarter import _create_publish_workflow
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    # No CI workflow files at all
    _create_publish_workflow(tmp_path, dry_run=False)
    content = (wf_dir / "publish.yml").read_text()
    assert "\njobs:\n" in content, "Must have jobs: block"
    assert "\n  build:\n" in content, "Must have build: job"
    assert "\n  publish-testpypi:\n" in content, "Must have publish-testpypi: job"
    assert "\n  publish-pypi:\n" in content, "Must have publish-pypi: job"
    # No test: job when CI does not exist
    assert "uses: ./.github/workflows/" not in content, \
        "Must NOT have a uses: CI reference when no CI workflow exists"


def test_publish_yml_valid_yaml_with_pyyaml(tmp_path):
    """Generated publish.yml is parseable by PyYAML when available (skips if not installed)."""
    yaml = pytest.importorskip("yaml", reason="pyyaml not installed; structural checks cover this")
    from pyuvstarter import _create_publish_workflow
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "ci.yml").write_text("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
    _create_publish_workflow(tmp_path, dry_run=False)
    content = (wf_dir / "publish.yml").read_text()
    parsed = yaml.safe_load(content)
    assert parsed is not None and "jobs" in parsed


def test_publish_yml_uses_custom_python_version(tmp_path):
    """Generated publish.yml contains the specified python_version."""
    from pyuvstarter import _create_publish_workflow
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    _create_publish_workflow(tmp_path, dry_run=False, python_version="3.11")
    content = (wf_dir / "publish.yml").read_text()
    assert "python-version: '3.11'" in content, \
        "Generated publish.yml must embed the requested python_version"
    assert "python-version: '3.12'" not in content


def test_publish_yml_uses_custom_build_cmd(tmp_path):
    """Generated publish.yml contains the specified build_cmd."""
    from pyuvstarter import _create_publish_workflow
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    _create_publish_workflow(tmp_path, dry_run=False, build_cmd="hatch build")
    content = (wf_dir / "publish.yml").read_text()
    assert "run: hatch build" in content, \
        "Generated publish.yml must embed the requested build_cmd"


# ---------------------------------------------------------------------------
# M6: No spurious ci.yml warning when test.yml is the CI workflow
# ---------------------------------------------------------------------------

def test_prepare_pypi_no_spurious_ci_warning_with_test_yml(tmp_path):
    """_prepare_pypi_metadata must NOT warn 'no ci.yml' when test.yml is the CI workflow."""
    import sys
    import importlib
    from unittest.mock import patch, call
    import pyuvstarter

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myproj"\nversion = "0.1.0"\n'
    )
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    # test.yml is the CI workflow (no ci.yml present)
    (wf_dir / "test.yml").write_text(
        "name: CI\non:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps: []\n"
    )

    logged_calls = []

    original_log = pyuvstarter._log_action

    def capturing_log(action, status, msg, *args, **kwargs):
        logged_calls.append((action, status, msg))
        return original_log(action, status, msg, *args, **kwargs)

    with patch.object(pyuvstarter, "_log_action", side_effect=capturing_log):
        pyuvstarter._prepare_pypi_metadata(tmp_path, "MIT", dry_run=False)

    spurious = [
        (a, s, m) for (a, s, m) in logged_calls
        if s == "WARN" and "no ci" in m.lower() and "ci.yml" in m.lower()
    ]
    assert not spurious, (
        "Must NOT warn about missing ci.yml when test.yml exists as CI workflow. "
        f"Got spurious WARN calls: {spurious}"
    )


# ---------------------------------------------------------------------------
# M7: Tier 2b _is_publish_workflow top-level name: pypi false-positive
# ---------------------------------------------------------------------------

def test_is_publish_workflow_top_level_workflow_name_pypi_does_not_match():
    """Workflow named 'name: pypi' at column 0 must NOT be classified as publish workflow."""
    from pyuvstarter import _is_publish_workflow
    # Top-level workflow name at column 0 — must NOT trigger Tier 2b
    content = "name: pypi\non:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
    assert _is_publish_workflow(content) is False, (
        "A workflow whose top-level name is 'pypi' must not be classified as a publish workflow"
    )


def test_is_publish_workflow_indented_environment_name_pypi_matches():
    """Indented 'name: pypi' (environment dict form, ≥2 spaces) must still be detected."""
    from pyuvstarter import _is_publish_workflow
    # 6-space indentation — environment dict form inside a job step
    content = "jobs:\n  publish:\n    environment:\n      name: pypi\n"
    assert _is_publish_workflow(content) is True, (
        "Indented 'name: pypi' (environment dict form) must be classified as a publish workflow"
    )


def test_is_publish_workflow_two_space_indented_name_pypi_matches():
    """Two-space indented 'name: pypi' must be classified as a publish workflow."""
    from pyuvstarter import _is_publish_workflow
    content = "  name: pypi\n"
    assert _is_publish_workflow(content) is True, (
        "Two-space indented 'name: pypi' must trigger Tier 2b detection"
    )


# ---------------------------------------------------------------------------
# M8: PEP 639 license-files — must not insert duplicate license key
# ---------------------------------------------------------------------------

def test_add_pypi_toml_metadata_skips_license_when_license_files_present(tmp_path):
    """If license-files is already present, must not also insert license key."""
    from pyuvstarter import _add_pypi_toml_metadata
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myproj"\nversion = "0.1.0"\nlicense-files = ["LICENSE"]\n'
    )
    result = _add_pypi_toml_metadata(tmp_path, "MIT", dry_run=False)
    assert result is True
    content = (tmp_path / "pyproject.toml").read_text()
    assert "license-files" in content
    # Must NOT also insert a redundant license = {text = "MIT"}
    assert 'license = {text' not in content, (
        "Must not insert duplicate license field when license-files already present"
    )


# ---------------------------------------------------------------------------
# M9: Poetry format — graceful WARN, no crash, return True
# ---------------------------------------------------------------------------

def test_add_pypi_toml_metadata_handles_poetry_format_gracefully(tmp_path):
    """Poetry [tool.poetry] format should log WARN and return True (not crash)."""
    import pyuvstarter
    from unittest.mock import patch

    (tmp_path / "pyproject.toml").write_text(
        '[tool.poetry]\nname = "myproj"\nversion = "0.1.0"\n'
        '[build-system]\nrequires = ["poetry-core"]\nbuild-backend = "poetry.core.masonry.api"\n'
    )

    logged_calls = []
    original_log = pyuvstarter._log_action

    def capturing_log(action, status, msg, *args, **kwargs):
        logged_calls.append((action, status, msg))
        return original_log(action, status, msg, *args, **kwargs)

    with patch.object(pyuvstarter, "_log_action", side_effect=capturing_log):
        result = pyuvstarter._add_pypi_toml_metadata(tmp_path, "MIT", dry_run=False)

    assert result is True, "Poetry format should not cause failure — must return True"
    warn_calls = [(a, s, m) for (a, s, m) in logged_calls if s == "WARN"]
    assert warn_calls, "Should log at least one WARN about unsupported format"
    assert any("poetry" in m.lower() for (a, s, m) in warn_calls), (
        "WARN message must mention 'poetry' to be actionable"
    )


# ---------------------------------------------------------------------------
# M10: New .yaml extension candidates in _detect_ci_workflow_name
# ---------------------------------------------------------------------------

def _make_ci_wf_dir(tmp_path, filename):
    """Helper: create a workflow dir with a single non-publish CI workflow file."""
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / filename).write_text(
        "name: CI\non:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
    )
    return wf_dir


def test_detect_ci_workflow_name_falls_back_to_tests_yaml(tmp_path):
    """`tests.yaml` is detected as a CI workflow."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "tests.yaml")
    assert _detect_ci_workflow_name(wf_dir) == "tests.yaml"


def test_detect_ci_workflow_name_falls_back_to_build_yaml(tmp_path):
    """`build.yaml` is detected as a CI workflow."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "build.yaml")
    assert _detect_ci_workflow_name(wf_dir) == "build.yaml"


def test_detect_ci_workflow_name_falls_back_to_main_yaml(tmp_path):
    """`main.yaml` is detected as a CI workflow."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "main.yaml")
    assert _detect_ci_workflow_name(wf_dir) == "main.yaml"


def test_detect_ci_workflow_name_falls_back_to_workflows_yaml(tmp_path):
    """`workflows.yaml` is detected as a CI workflow."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "workflows.yaml")
    assert _detect_ci_workflow_name(wf_dir) == "workflows.yaml"


def test_detect_ci_workflow_name_falls_back_to_python_yaml(tmp_path):
    """`python.yaml` is detected as a CI workflow."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "python.yaml")
    assert _detect_ci_workflow_name(wf_dir) == "python.yaml"


def test_detect_ci_workflow_name_falls_back_to_python_app_yaml(tmp_path):
    """`python-app.yaml` is detected as a CI workflow."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "python-app.yaml")
    assert _detect_ci_workflow_name(wf_dir) == "python-app.yaml"


def test_detect_ci_workflow_name_falls_back_to_python_package_yaml(tmp_path):
    """`python-package.yaml` is detected as a CI workflow."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "python-package.yaml")
    assert _detect_ci_workflow_name(wf_dir) == "python-package.yaml"


# ---------------------------------------------------------------------------
# Missing candidate tests: main.yml, workflows.yml, test.yaml, workflow.yaml
# ---------------------------------------------------------------------------

def test_detect_ci_workflow_name_falls_back_to_main_yml(tmp_path):
    """`main.yml` is detected as a CI workflow (position 5 in priority order)."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "main.yml")
    assert _detect_ci_workflow_name(wf_dir) == "main.yml"


def test_detect_ci_workflow_name_falls_back_to_workflows_yml(tmp_path):
    """`workflows.yml` is detected as a CI workflow (position 7 in priority order)."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "workflows.yml")
    assert _detect_ci_workflow_name(wf_dir) == "workflows.yml"


def test_detect_ci_workflow_name_falls_back_to_test_yaml(tmp_path):
    """`test.yaml` is detected as a CI workflow (.yaml extension of test.yml)."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "test.yaml")
    assert _detect_ci_workflow_name(wf_dir) == "test.yaml"


def test_detect_ci_workflow_name_falls_back_to_workflow_yaml(tmp_path):
    """`workflow.yaml` is detected as a CI workflow (.yaml extension of workflow.yml)."""
    from pyuvstarter import _detect_ci_workflow_name
    wf_dir = _make_ci_wf_dir(tmp_path, "workflow.yaml")
    assert _detect_ci_workflow_name(wf_dir) == "workflow.yaml"


# ---------------------------------------------------------------------------
# P1: tqdm disable=not _is_tty + dynamic_ncols tests
# ---------------------------------------------------------------------------

def test_tqdm_disabled_when_stderr_not_tty():
    """init_progress_bar must disable tqdm when stderr is not a TTY (AST-based check)."""
    import ast
    import re

    source = open("pyuvstarter.py").read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "init_progress_bar":
            func_src = ast.get_source_segment(source, node)
            assert func_src is not None, "Could not extract init_progress_bar source"
            assert "isatty" in func_src, \
                "init_progress_bar must check sys.stderr.isatty() to detect non-TTY environments"
            assert "disable" in func_src, \
                "init_progress_bar must pass disable= to tqdm to suppress output when not a TTY"
            assert re.search(r'disable\s*=\s*not\s+', func_src), \
                "disable must be set to 'not <tty_check>' so piped/AI contexts get zero tqdm output"
            return
    raise AssertionError("init_progress_bar not found in pyuvstarter.py")


def test_tqdm_has_dynamic_ncols_not_hardcoded_ncols():
    """ProgressTracker.init_progress_bar must use dynamic_ncols=True, not ncols=<int>."""
    import ast
    # Read the source and check the tqdm call in init_progress_bar
    source = open("pyuvstarter.py").read()
    # The tqdm constructor call should have dynamic_ncols and NOT ncols=<number>
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "init_progress_bar":
            func_source = ast.get_source_segment(source, node)
            assert "dynamic_ncols=True" in func_source, (
                "init_progress_bar must use dynamic_ncols=True"
            )
            # Should not have hardcoded ncols= assignment
            import re
            assert not re.search(r'\bncols\s*=\s*\d+', func_source), (
                "init_progress_bar must not hardcode ncols=<integer>"
            )
            return
    raise AssertionError("init_progress_bar function not found in pyuvstarter.py")


def test_tqdm_disabled_when_no_color_set():
    """ProgressTracker.init_progress_bar must create tqdm with disable=True when NO_COLOR is set."""
    import ast
    source = open("pyuvstarter.py").read()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == "init_progress_bar":
            func_source = ast.get_source_segment(source, node)
            # Must check NO_COLOR env var to determine disable
            assert "NO_COLOR" in func_source, (
                "init_progress_bar must check NO_COLOR environment variable"
            )
            assert "isatty" in func_source, (
                "init_progress_bar must check sys.stderr.isatty()"
            )
            assert "disable" in func_source, (
                "init_progress_bar must pass disable= to tqdm"
            )
            return
    raise AssertionError("init_progress_bar function not found in pyuvstarter.py")


# ---------------------------------------------------------------------------
# P5: Non-GitHub remote detection tests
# ---------------------------------------------------------------------------

def test_detect_github_owner_repo_github_ssh_url(tmp_path):
    """SSH git@github.com:owner/repo.git must return (owner, repo)."""
    from unittest.mock import patch, MagicMock
    import pyuvstarter

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "git@github.com:myowner/myrepo.git\n"

    with patch("subprocess.run", return_value=mock_result):
        owner, repo = pyuvstarter._detect_github_owner_repo(tmp_path)

    assert owner == "myowner", f"Expected 'myowner', got {owner!r}"
    assert repo == "myrepo", f"Expected 'myrepo', got {repo!r}"


def test_detect_github_owner_repo_github_https_url(tmp_path):
    """HTTPS https://github.com/owner/repo.git must return (owner, repo)."""
    from unittest.mock import patch, MagicMock
    import pyuvstarter

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://github.com/myowner/myrepo.git\n"

    with patch("subprocess.run", return_value=mock_result):
        owner, repo = pyuvstarter._detect_github_owner_repo(tmp_path)

    assert owner == "myowner", f"Expected 'myowner', got {owner!r}"
    assert repo == "myrepo", f"Expected 'myrepo', got {repo!r}"


def test_detect_github_owner_repo_non_github_returns_none(tmp_path):
    """Non-GitHub remote (GitLab, Gitea, etc.) must return (None, None) and log WARN."""
    from unittest.mock import patch, MagicMock
    import pyuvstarter

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "git@gitlab.com:myorg/myproject.git\n"

    logged_calls = []
    original_log = pyuvstarter._log_action

    def capturing_log(action, status, msg, *args, **kwargs):
        logged_calls.append((action, status, msg))
        return original_log(action, status, msg, *args, **kwargs)

    with patch("subprocess.run", return_value=mock_result), \
         patch.object(pyuvstarter, "_log_action", side_effect=capturing_log):
        owner, repo = pyuvstarter._detect_github_owner_repo(tmp_path)

    assert owner is None, f"Non-GitHub remote must return None owner, got {owner!r}"
    assert repo is None, f"Non-GitHub remote must return None repo, got {repo!r}"
    warn_calls = [(a, s, m) for (a, s, m) in logged_calls if s == "WARN"]
    assert warn_calls, "Must log a WARN for non-GitHub remote"
    assert any("github" in m.lower() for (a, s, m) in warn_calls), (
        "WARN message must mention 'github' to be actionable"
    )


def test_detect_github_owner_repo_bitbucket_returns_none(tmp_path):
    """Bitbucket remote must return (None, None)."""
    from unittest.mock import patch, MagicMock
    import pyuvstarter

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://bitbucket.org/myorg/myrepo.git\n"

    with patch("subprocess.run", return_value=mock_result), \
         patch.object(pyuvstarter, "_log_action"):
        owner, repo = pyuvstarter._detect_github_owner_repo(tmp_path)

    assert owner is None and repo is None, (
        f"Bitbucket remote must return (None, None), got ({owner!r}, {repo!r})"
    )


# ---------------------------------------------------------------------------
# P7: Generated classifiers include Development Status TODO comment
# ---------------------------------------------------------------------------

def test_generated_classifiers_include_development_status_todo_comment(tmp_path):
    """--prepare-pypi must add a TODO comment before classifiers in pyproject.toml."""
    from pyuvstarter import _add_pypi_toml_metadata

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myproj"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n'
    )
    result = _add_pypi_toml_metadata(tmp_path, "MIT", dry_run=False)
    assert result is True

    raw = (tmp_path / "pyproject.toml").read_text()
    assert "TODO" in raw, "pyproject.toml must contain a TODO comment for Development Status"
    assert "Development Status" in raw, "pyproject.toml must contain Development Status classifier"
    # The TODO comment should appear before the classifiers key
    todo_idx = raw.index("TODO")
    classifiers_idx = raw.index("classifiers")
    assert todo_idx < classifiers_idx, (
        "TODO comment must appear before the classifiers key"
    )
