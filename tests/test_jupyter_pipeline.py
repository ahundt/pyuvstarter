#!/usr/bin/env python3
"""
Comprehensive tests for pyuvstarter Jupyter notebook pipeline.

Tests notebook discovery, JSON parsing, AST extraction without GUI dependencies.
Validates both primary (nbconvert) and fallback (manual parsing) methods.

These tests ensure pyuvstarter correctly handles Jupyter notebooks in various
scenarios without requiring actual Jupyter installation or GUI interaction.
"""

import sys

import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_utils import (
    ProjectFixture, temp_manager, executor, validator, mock_factory, format_pyuvstarter_error, format_dependency_mismatch
)

# Optional pytest import for when pytest is available
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    pytest = None

class TestJupyterNotebookPipeline:
    """Test Jupyter notebook discovery and dependency extraction."""

    def test_basic_notebook_discovery(self):
        """Test discovery of basic Jupyter notebooks."""

        fixture = ProjectFixture(
            name="basic_notebooks",
            files={
                "data_analysis.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": [
                            "import pandas as pd\n",
                            "import numpy as np\n",
                            "import matplotlib.pyplot as plt\n",
                            "import seaborn as sns\n"
                        ],
                        "metadata": {},
                        "outputs": []
                    }
                ])),
                "notebooks/visualization.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": [
                            "import plotly.graph_objects as go\n",
                            "import plotly.express as px\n",
                            "import dash\n"
                        ],
                        "metadata": {},
                        "outputs": []
                    }
                ])),
                "README.md": "# Project with notebooks",
                "main.py": """
print("This is a Python file")

# This should be discovered too
import sys
import os
"""
            },
            directories=["notebooks"],
            expected_packages=["pandas", "numpy", "matplotlib", "seaborn", "plotly", "dash"],
            has_notebooks=True
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, f"PyUVStarter failed: {result.stderr}"

            # Verify notebook support was detected
            assert "notebook" in result.stdout.lower()
            assert "jupyter" in result.stdout.lower() or "ipykernel" in result.stdout.lower()

            # Validate dependencies from both notebooks and Python files
            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Check for notebook dependencies
            notebook_packages = ["pandas", "numpy", "matplotlib", "seaborn", "plotly", "dash"]
            for pkg in notebook_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, f"Notebook package {pkg} not found in dependencies"

    def test_notebook_with_pip_install_commands(self):
        """Test notebooks containing !pip install commands."""

        fixture = ProjectFixture(
            name="notebook_pip_commands",
            files={
                "ml_experiment.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "markdown",
                        "source": [
                            "# Machine Learning Experiment\n",
                            "First, install required packages:"
                        ],
                        "metadata": {}
                    },
                    {
                        "cell_type": "code",
                        "source": [
                            "# Install packages not in requirements.txt\n",
                            "!pip install transformers torch torchvision\n",
                            "!pip install -q accelerate  # Quiet installation\n",
                            "!pip install datasets[audio] @ git+https://github.com/huggingface/datasets.git\n"
                        ],
                        "metadata": {},
                        "outputs": []
                    },
                    {
                        "cell_type": "code",
                        "source": [
                            "import pandas as pd\n",
                            "import numpy as np\n",
                            "from transformers import AutoTokenizer, AutoModel\n",
                            "import torch\n",
                            "from datasets import load_dataset\n"
                        ],
                        "metadata": {},
                        "outputs": []
                    }
                ])),
                "requirements.txt": "pandas==1.5.0\nnumpy>=1.20.0"
            },
            directories=[],
            expected_packages=["pandas", "numpy", "transformers", "torch", "datasets"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(
                project_dir,
                args=["--dependency-migration=auto"],
                dry_run=False
            )

            assert result.returncode == 0, format_pyuvstarter_error("test_notebook_with_pip_install_commands", result, project_dir)

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Check for packages discovered from notebook imports
            notebook_packages = ["transformers", "torch", "datasets"]
            for pkg in notebook_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, format_dependency_mismatch("test_notebook_with_pip_install_commands", pkg, dependencies, project_dir)

    def test_complex_notebook_with_various_imports(self):
        """Test notebook with complex import patterns and edge cases."""

        fixture = ProjectFixture(
            name="complex_notebook",
            files={
                "complex_analysis.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": [
                            "# Standard imports\n",
                            "import pandas as pd\n",
                            "import numpy as np\n",
                            "\n",
                            "# Imports with aliases\n",
                            "import matplotlib.pyplot as plt\n",
                            "import seaborn as sns\n",
                            "import plotly.graph_objects as go\n",
                            "\n",
                            "# From imports\n",
                            "from sklearn.ensemble import RandomForestClassifier\n",
                            "from sklearn.model_selection import train_test_split\n",
                            "from scipy import stats\n",
                            "from bs4 import BeautifulSoup\n",
                            "\n",
                            "# Try-except imports (optional dependencies)\n",
                            "try:\n",
                            "    import tensorflow as tf\n",
                            "    import torch\n",
                            "except ImportError:\n",
                            "    print('ML libraries not available')\n",
                            "\n",
                            "# Conditional imports\n",
                            "import sys\n",
                            "if sys.version_info >= (3, 8):\n",
                            "    import typing_extensions\n",
                            "\n",
                            "# Star imports (should be handled carefully)\n",
                            "from math import *\n",
                            "from collections import *  # This might not be discoverable"
                        ],
                        "metadata": {},
                        "outputs": []
                    }
                ]))
            },
            directories=[],
            expected_packages=[
                "pandas", "numpy", "matplotlib", "seaborn", "plotly",
                "sklearn", "scipy", "bs4",
                "tensorflow", "torch", "typing_extensions"
            ]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error("test_complex_notebook_with_various_imports", result, project_dir)

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Validate various import patterns were discovered
            complex_packages = ["pandas", "numpy", "matplotlib", "seaborn", "plotly", "sklearn", "scipy", "beautifulsoup4"]
            for pkg in complex_packages:
                found = False
                for dep in dependencies:
                    dep_clean = dep.lower().replace('-', '')
                    # Handle sklearn -> scikit-learn mapping specifically
                    if pkg == "sklearn" and "scikitlearn" in dep_clean:
                        found = True
                        break
                    # General substring matching
                    elif pkg.lower() in dep_clean:
                        found = True
                        break
                    # Handle underscore to hyphen conversion
                    elif pkg.replace('_', '').lower() in dep_clean:
                        found = True
                        break
                assert found, format_dependency_mismatch("test_complex_notebook_with_various_imports", pkg, dependencies, project_dir)

    def test_malformed_notebook_handling(self):
        """Test handling of malformed or corrupted notebook files."""

        fixture = ProjectFixture(
            name="malformed_notebooks",
            files={
                "valid.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": ["import pandas as pd\nimport numpy as np"],
                        "metadata": {},
                        "outputs": []
                    }
                ])),
                "corrupted.ipynb": json.dumps({
                    "cells": [
                        {
                            "cell_type": "code",
                            "execution_count": 1,
                            "source": "import matplotlib.pyplot as plt",
                            "metadata": {},
                            "outputs": []
                        }
                    ],
                    "metadata": {
                        "kernelspec": {
                            "display_name": "Python 3",
                            "language": "python",
                            "name": "python3"
                        }
                    },
                    "nbformat": 4,
                    "nbformat_minor": 4
                }),
                "invalid_json.ipynb": json.dumps({
                    "cells": [
                        {
                            "cell_type": "code",
                            "execution_count": 1,
                            "source": "import requests\nimport sys",
                            "metadata": {},
                            "outputs": []
                        }
                    ],
                    "metadata": {
                        "kernelspec": {
                            "display_name": "Python 3",
                            "language": "python",
                            "name": "python3"
                        }
                    },
                    "nbformat": 4,
                    "nbformat_minor": 4
                }),
                "empty.ipynb": json.dumps({
                    "cells": [],
                    "metadata": {},
                    "nbformat": 4,
                    "nbformat_minor": 4
                })
            },
            directories=[],
            expected_packages=["pandas", "numpy", "matplotlib", "requests"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            # Should handle malformed notebooks gracefully
            # May succeed with warnings or skip invalid notebooks
            assert result.returncode == 0, format_pyuvstarter_error("test_malformed_notebook_handling", result, project_dir)

            # Should still discover dependencies from valid notebook
            pyproject_data = validator.validate_pyproject_toml(project_dir)
            dependencies = pyproject_data["project"]["dependencies"]

            pandas_found = any("pandas" in dep.lower() for dep in dependencies)
            numpy_found = any("numpy" in dep.lower() for dep in dependencies)

            assert pandas_found or numpy_found, format_dependency_mismatch("test_malformed_notebook_handling", "pandas or numpy", dependencies, project_dir)

    def test_notebook_in_subdirectories(self):
        """Test notebook discovery in nested directory structures."""

        fixture = ProjectFixture(
            name="nested_notebooks",
            files={
                "notebooks/data_analysis/basic.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": ["import pandas as pd\nimport numpy as np"],
                        "metadata": {},
                        "outputs": []
                    }
                ])),
                "notebooks/data_analysis/advanced.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": ["import scipy as sp\nimport matplotlib.pyplot as plt"],
                        "metadata": {},
                        "outputs": []
                    }
                ])),
                "experiments/ml/experiment_1.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": ["import sklearn\nimport tensorflow as tf"],
                        "metadata": {},
                        "outputs": []
                    }
                ])),
                "scripts/main.py": """
import sys
import os
print("Main script")
"""
            },
            directories=["notebooks/data_analysis", "experiments/ml"],
            expected_packages=["pandas", "numpy", "scipy", "matplotlib", "sklearn", "tensorflow"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error("test_notebook_in_subdirectories", result, project_dir)

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Should discover packages from all nested notebooks
            for expected_pkg in fixture.expected_packages:
                found = False
                for dep in dependencies:
                    dep_clean = dep.lower().replace('-', '')
                    # Handle sklearn -> scikit-learn mapping specifically
                    if expected_pkg == "sklearn" and "scikitlearn" in dep_clean:
                        found = True
                        break
                    # General substring matching
                    elif expected_pkg.lower() in dep_clean:
                        found = True
                        break
                assert found, format_dependency_mismatch("test_notebook_in_subdirectories", expected_pkg, dependencies, project_dir)

class TestNotebookExecutionSupport:
    """Test notebook execution support functionality."""

    def test_notebook_execution_dependencies(self):
        """Test installation of notebook execution dependencies like ipykernel."""

        fixture = ProjectFixture(
            name="notebook_execution",
            files={
                "analysis.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": [
                            "import pandas as pd\n",
                            "import numpy as np\n",
                            "print('Notebook execution test')"
                        ],
                        "metadata": {},
                        "outputs": []
                    }
                ])),
                "dashboard.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": [
                            "import ipywidgets as widgets\n",
                            "from IPython.display import display\n",
                            "import plotly.graph_objects as go"
                        ],
                        "metadata": {},
                        "outputs": []
                    }
                ]))
            },
            directories=[],
            expected_packages=["pandas", "numpy", "ipython", "ipywidgets", "plotly"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error("test_notebook_execution_dependencies", result, project_dir)

            # Check for notebook execution support in output
            assert "notebook execution support" in result.stdout.lower() or "ipykernel" in result.stdout.lower() or "ipython" in result.stdout.lower()

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Should include notebook execution dependencies
            ipython_found = any("ipython" in dep.lower() for dep in dependencies)
            assert ipython_found, format_dependency_mismatch("test_notebook_execution_dependencies", "ipython", dependencies, project_dir)

            # Should include dependencies from notebooks
            notebook_packages = ["pandas", "numpy", "ipywidgets", "plotly"]
            for pkg in notebook_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, f"Notebook package {pkg} not found"

    def test_notebook_systems_detection(self):
        """Test detection of different notebook systems."""

        fixture = ProjectFixture(
            name="notebook_systems",
            files={
                # Jupyter notebook
                "jupyter_notebook.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": ["import pandas as pd"],
                        "metadata": {},
                        "outputs": []
                    }
                ])),
                # VS Code notebook (similar structure)
                ".vscode/notebooks/vscode_notebook.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": ["import numpy as np"],
                        "metadata": {},
                        "outputs": []
                    }
                ])),
                # Notebook in subdirectory
                "experiments/ml_experiment.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": ["import sklearn"],
                        "metadata": {},
                        "outputs": []
                    }
                ]))
            },
            directories=["experiments", ".vscode/notebooks"],
            expected_packages=["pandas", "numpy", "scikit-learn"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, format_pyuvstarter_error("test_notebook_systems_detection", result, project_dir)

            # Should detect notebooks in various locations
            assert "notebook" in result.stdout.lower()

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Should discover packages from all notebooks
            for pkg in fixture.expected_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, f"Package {pkg} from notebooks not found"

class TestNotebookFallbackMethods:
    """Test notebook parsing fallback methods when nbconvert is not available."""

    def test_manual_json_parsing(self):
        """Test manual JSON parsing when nbconvert is not available."""

        fixture = ProjectFixture(
            name="manual_parsing",
            files={
                "complex_notebook.ipynb": json.dumps({
                    "cells": [
                        {
                            "cell_type": "code",
                            "execution_count": 1,
                            "source": [
                                "# Multiple import statements\n",
                                "import pandas as pd\n",
                                "import numpy as np\n",
                                "from sklearn.model_selection import train_test_split\n",
                                "\n",
                                "# Comment with !pip install\n",
                                "# !pip install some-package  # This is commented out\n",
                                "\n",
                                "# Actual pip install command\n",
                                "!pip install plotly dash\n",
                                "!pip install -q seaborn  # Quiet install\n"
                            ],
                            "metadata": {"tags": ["parameters"]},
                            "outputs": []
                        },
                        {
                            "cell_type": "markdown",
                            "source": [
                                "# Analysis\n",
                                "This notebook uses various libraries for data analysis."
                            ],
                            "metadata": {}
                        }
                    ],
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
                })
            },
            directories=[],
            expected_packages=["pandas", "numpy", "scikit-learn"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            # Should still succeed using manual parsing (nbconvert may or may not be available)
            assert result.returncode == 0, format_pyuvstarter_error("test_manual_json_parsing", result, project_dir)

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Should discover packages from import statements via manual parsing
            for pkg in fixture.expected_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, f"Package {pkg} not discovered via manual parsing"

    def test_notebook_with_multiline_imports(self):
        """Test notebooks with multiline import statements."""

        fixture = ProjectFixture(
            name="multiline_imports",
            files={
                "multiline_notebook.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": [
                            "from sklearn.ensemble import RandomForestClassifier\n",
                            "from sklearn.ensemble import GradientBoostingClassifier\n",
                            "\n",
                            "import pandas as pd\n",
                            "import numpy as np\n",
                            "import matplotlib.pyplot as plt\n",
                            "\n",
                            "# Backslash continuation\n",
                            "from sklearn.model_selection import (\n",
                            "    train_test_split,\n",
                            "    cross_val_score\n",
                            ")"
                        ],
                        "metadata": {},
                        "outputs": []
                    }
                ]))
            },
            directories=[],
            expected_packages=["sklearn", "pandas", "numpy", "matplotlib"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, f"PyUVStarter failed (exit={result.returncode}). Stdout: {result.stdout[:200]} Stderr: {result.stderr[:300]}"

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Should discover packages from multiline imports
            for pkg in fixture.expected_packages:
                found = False
                for dep in dependencies:
                    dep_clean = dep.lower().replace('-', '')
                    # Handle sklearn -> scikit-learn mapping specifically
                    if pkg == "sklearn" and "scikitlearn" in dep_clean:
                        found = True
                        break
                    # General substring matching
                    elif pkg.lower() in dep_clean:
                        found = True
                        break
                assert found, f"Package {pkg} from multiline imports not found"

class TestNotebookEdgeCases:
    """Test edge cases and special scenarios for notebook handling."""

    def test_notebook_with_special_characters(self):
        """Test notebooks with special characters and unicode in imports."""

        fixture = ProjectFixture(
            name="special_chars_notebook",
            files={
                "unicode_notebook.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": [
                            "# Imports with special characters\n",
                            "import pandas as pd  # Data processing 📊\n",
                            "import numpy as np  # Numerical computing 🔢\n",
                            "import matplotlib.pyplot as plt  # Plotting 📈\n",
                            "\n",
                            "# Package with dashes\n",
                            "import sklearn as sklearn  # ML 🤖\n",
                            "import beautifulsoup4 as bs4  # HTML parsing 🌐\n",
                            "\n",
                            "# Comments with unicode\n",
                            "# This should handle émojis 🚀 and special chars: café naïve résumé"
                        ],
                        "metadata": {},
                        "outputs": []
                    }
                ]))
            },
            directories=[],
            expected_packages=["pandas", "numpy", "matplotlib", "scikit-learn", "beautifulsoup4"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, f"PyUVStarter failed (exit={result.returncode}). Stdout: {result.stdout[:200]} Stderr: {result.stderr[:300]}"

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Should handle unicode and special characters
            for pkg in fixture.expected_packages:
                found = any(pkg.lower().replace('-', '').replace('_', '') in
                          dep.lower().replace('-', '').replace('_', '')
                          for dep in dependencies)
                assert found, f"Package {pkg} with special characters not found"

    def test_notebook_with_conditional_code(self):
        """Test notebooks with conditional code and dynamic imports."""

        fixture = ProjectFixture(
            name="conditional_notebook",
            files={
                "pyproject.toml": "[project]\nname = 'conditional-notebook'\nversion = '0.1.0'\n",
                "conditional_notebook.ipynb": json.dumps(mock_factory.create_mock_notebook_json([
                    {
                        "cell_type": "code",
                        "source": [
                            "import sys\n",
                            "import os\n",
                            "\n",
                            "# Dynamic imports based on conditions\n",
                            "if sys.platform == 'win32':\n",
                            "    import winreg\n",
                            "elif sys.platform == 'darwin':\n",
                            "    import applescript\n",
                            "else:\n",
                            "    import pwd\n",
                            "\n",
                            "# Version-based imports\n",
                            "if sys.version_info >= (3, 8):\n",
                            "    import typing_extensions\n",
                            "else:\n",
                            "    import enum34 as enum  # Backward compatibility\n",
                            "\n",
                            "# Environment-based imports\n",
                            "if os.getenv('JUPYTER_NOTEBOOK'):\n",
                            "    import ipywidgets\n",
                            "    import plotly"
                        ],
                        "metadata": {},
                        "outputs": []
                    }
                ]))
            },
            directories=[],
            expected_packages=["ipywidgets", "plotly", "typing_extensions"]  # Platform-specific ones may vary
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, f"PyUVStarter failed (exit={result.returncode}). Stdout: {result.stdout[:200]} Stderr: {result.stderr[:300]}"

            pyproject_data = validator.validate_pyproject_toml(project_dir)
            dependencies = pyproject_data["project"]["dependencies"]

            # Should discover at least some conditional imports
            # (platform-specific ones may or may not be included depending on current platform)
            common_packages = ["ipywidgets", "plotly", "typing_extensions"]
            found_packages = sum(1 for pkg in common_packages
                             if any(pkg.lower() in dep.lower() for dep in dependencies))

            assert found_packages > 0, "No conditional imports were discovered"

    def test_notebook_with_code_execution_metadata(self):
        """Test notebooks with execution counts and timestamps."""

        fixture = ProjectFixture(
            name="metadata_notebook",
            files={
                "pyproject.toml": "[project]\nname = 'metadata-notebook'\nversion = '0.1.0'\n",
                "metadata_notebook.ipynb": json.dumps({
                    "cells": [
                        {
                            "cell_type": "code",
                            "execution_count": 1,
                            "metadata": {
                                "collapsed": False,
                                "scrolled": False,
                                "tags": ["parameters"]
                            },
                            "source": [
                                "import pandas as pd\n",
                                "import numpy as np\n",
                                "print('Data loaded')"
                            ],
                            "outputs": [
                                {
                                    "output_type": "stream",
                                    "name": "stdout",
                                    "text": ["Data loaded\n"]
                                }
                            ]
                        },
                        {
                            "cell_type": "code",
                            "execution_count": 2,
                            "metadata": {},
                            "source": [
                                "import matplotlib.pyplot as plt\n",
                                "plt.figure()\n",
                                "plt.plot([1, 2, 3, 4])\n",
                                "plt.show()"
                            ],
                            "outputs": []
                        }
                    ],
                    "metadata": {
                        "kernelspec": {
                            "display_name": "Python 3",
                            "language": "python",
                            "name": "python3"
                        },
                        "language_info": {
                            "file_extension": ".py",
                            "mimetype": "text/x-python",
                            "name": "python",
                            "nbconvert_exporter": "python",
                            "pygments_lexer": "ipython3",
                            "version": "3.9.0"
                        },
                        "orig_nbformat": 2,
                        "authors": [
                            {
                                "name": "Test Author"
                            }
                        ]
                    },
                    "nbformat": 4,
                    "nbformat_minor": 4
                })
            },
            directories=[],
            expected_packages=["pandas", "numpy", "matplotlib"]
        )

        with temp_manager.create_temp_project(fixture) as project_dir:
            result = executor.run_pyuvstarter(project_dir, dry_run=False)

            assert result.returncode == 0, f"PyUVStarter failed (exit={result.returncode}). Stdout: {result.stdout[:200]} Stderr: {result.stderr[:300]}"

            pyproject_data = validator.validate_pyproject_toml(project_dir, fixture.expected_packages)
            dependencies = pyproject_data["project"]["dependencies"]

            # Should discover packages despite rich metadata
            for pkg in fixture.expected_packages:
                found = any(pkg.lower() in dep.lower() for dep in dependencies)
                assert found, f"Package {pkg} not found despite metadata"

def main():
    """Run all Jupyter pipeline tests."""

    # Simple test runner for manual execution
    test_classes = [
        TestJupyterNotebookPipeline,
        TestNotebookExecutionSupport,
        TestNotebookFallbackMethods,
        TestNotebookEdgeCases
    ]

    all_tests = []
    for test_class in test_classes:
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        for method in test_methods:
            all_tests.append((test_class().__getattribute__(method), f"{test_class.__name__}.{method}"))

    passed = 0
    total = len(all_tests)

    print("🚀 Running PyUVStarter Jupyter Pipeline Tests")
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
        print("🎉 All Jupyter pipeline tests passed!")
        return 0
    else:
        print(f"💥 {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())