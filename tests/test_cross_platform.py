#!/usr/bin/env python3
"""
Tests for pyuvstarter cross-platform compatibility and Unicode handling.

Tests various platform-specific and internationalization scenarios:
- Unicode filenames and directory names
- Emoji in comments and strings
- Windows path handling
- Different text encodings
- Platform-specific package dependencies
- International characters in package names
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_utils import (
    ProjectFixture, temp_manager, executor
)

def test_unicode_filenames():
    """Test handling of Unicode filenames and directory names."""

    unicode_names = [
        "cafe_data_processor.py",  # ASCII filename with Unicode content
        "naive_script.py",  # ASCII filename with Unicode content
        "resume_generator.py",  # ASCII filename with Unicode content
        "chinese_data_processor.py",  # ASCII filename with Chinese content
        "cyrillic_analyzer.py",  # ASCII filename with Cyrillic content
        "arabic_analyzer.py"  # ASCII filename with Arabic content
    ]

    files = {}
    for name in unicode_names:
        files[name] = f"""
# File with Unicode name: {name}
import sys
import os

def main():
    print("Unicode filename test")
    return "Success from {name}"
"""

    fixture = ProjectFixture(
        name="unicode_filenames_test",
        files=files,
        directories=[],
        expected_packages=[]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed with Unicode filenames: {result.stderr}"

def test_unicode_directory_names():
    """Test handling of Unicode directory names."""

    fixture = ProjectFixture(
        name="unicode_directories_test",
        files={
            "café/main.py": """
import sys
def main():
    return "Unicode directory test"
""",
            "naïve/module.py": """
def helper():
    return "Helper from Unicode directory"
""",
            "数据/处理器.py": """
# Chinese directory name
def process_data():
    return "Processing data"
""",
            "анализ/скрипт.py": """
# Cyrillic directory name
def analyze():
    return "Analysis complete"
""",
            "main.py": """
import sys
from café.main import main as cafe_main
from naïve.module import helper
from 数据.处理器 import process_data
from анализ.скрипт import analyze

def main():
    return cafe_main(), helper(), process_data(), analyze()
""",
            "requirements.txt": "requests"
        },
        directories=["café", "naïve", "数据", "анализ"],
        expected_packages=["requests"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed with Unicode directories: {result.stderr}"

def test_emoji_in_code():
    """Test handling of emoji in code comments and strings."""

    fixture = ProjectFixture(
        name="emoji_test",
        files={
            "main.py": """
#!/usr/bin/env python3
# 🚀 Python project with emoji support 🎉
# 📊 Data processing script 📈

import sys
import os

def main():
    # 🌟 Welcome message with emoji
    print("Hello World! 🌍")

    # 🐍 Python emoji
    python_facts = [
        "Python is awesome! 🐍",
        "Data science 📊",
        "Machine learning 🤖",
        "Web development 🌐"
    ]

    # 💰 Money emoji for finance
    budget = {
        "income": "💵 $1000",
        "expenses": "💸 $500",
        "savings": "🏦 $500"
    }

    # 🎯 Progress tracking
    progress = "🔵🔵🔵⚪⚪"  # 60% complete

    return {
        "message": "Emoji test successful! ✅",
        "progress": progress,
        "facts": python_facts,
        "budget": budget
    }

if __name__ == "__main__":
    result = main()
    print(f"Result: {result}")
""",
            "data.py": """
# 📈 Data processing with emoji 📊

import pandas as pd
import numpy as np

def analyze_data():
    # 🎯 Target: analyze user engagement
    metrics = {
        "users": "👥 1000",
        "engagement": "📈 85%",
        "satisfaction": "😊 4.5/5"
    }

    return metrics

def create_visualization():
    # 🎨 Create beautiful plots
    colors = ["🔴", "🟢", "🔵", "🟡", "🟣"]
    return colors
""",
            "requirements.txt": """
pandas>=1.5.0 📊
numpy>=1.20.0 🔢
matplotlib>=3.5.0 📈
seaborn>=0.11.0 🎨
"""
        },
        directories=[],
        expected_packages=["pandas", "numpy", "matplotlib", "seaborn"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dependency-migration", "auto", "--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed with emoji: {result.stderr}"

def test_different_text_encodings():
    """Test handling of different text encodings."""

    fixture = ProjectFixture(
        name="encoding_test",
        files={
            "main.py": """
# -*- coding: utf-8 -*-
import sys

def main():
    # Test different Unicode characters
    messages = [
        "Hello World",  # English
        "Bonjour le monde",  # French
        "Hola Mundo",  # Spanish
        "Привет мир",  # Russian
        "你好世界",  # Chinese
                "مرحبا بالعالم",  # Arabic
                "こんにちは世界",  # Japanese
                "한국어",  # Korean
                "🌍🌎🌏",  # Earth emoji
            ]

    for message in messages:
        print(message)

    return len(messages)
""",
            "german.py": """
# -*- coding: iso-8859-1 -*-
# German special characters
def german_text():
    return "Müller, Müller, Müller: German text with umlauts äöüß"
""",
            "french.py": """
# -*- coding: latin-1 -*-
# French special characters
def french_text():
    return "Café, naïve, résumé: French text with accents éèêëàâä"
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

        assert result.returncode == 0, f"PyUVStarter failed with encoding: {result.stderr}"

def test_windows_path_handling():
    """Test handling of Windows-style paths."""

    fixture = ProjectFixture(
        name="windows_paths_test",
        files={
            "main.py": """
import sys
import os
from pathlib import Path

def main():
    # Test Windows-style paths
    windows_paths = [
        "C:\\\\Users\\\\Test\\\\Documents\\\\file.py",
        "D:\\\\Program Files\\\\App\\\\app.exe",
        "\\\\server\\\\share\\\\folder\\\\file.txt",
        "C:\\\\Users\\\\Test\\\\My Documents\\\\data.csv",  # Space in path
        "C:\\\\Program Files (x86)\\\\App\\\\app.exe",  # Parentheses
    ]

    for path in windows_paths:
        # Convert to Path object for cross-platform handling
        try:
            p = Path(path)
            print(f"Original: {path}")
            print(f"As Path: {p}")
        except Exception as e:
            print(f"Error with path {path}: {e}")

    return "Windows path handling test"
""",
            "config.py": """
# Configuration with Windows-style paths
def get_config():
    return {
        "data_dir": "C:\\\\Users\\\\Test\\\\AppData\\\\Local\\\\myapp",
        "temp_dir": "C:\\\\Users\\\\Test\\\\AppData\\\\Local\\\\Temp",
        "log_dir": "C:\\\\Users\\\\Test\\\\Documents\\\\Logs",
        "cache_dir": "C:\\\\Users\\\\Test\\\\AppData\\\\Local\\\\myapp\\\\cache"
    }
""",
            "requirements.txt": "pathlib2; python_version<'3.4'"
        },
        directories=[],
        expected_packages=["pathlib2"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dependency-migration", "auto", "--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed with Windows paths: {result.stderr}"

def test_platform_specific_dependencies():
    """Test platform-specific dependency handling."""

    fixture = ProjectFixture(
        name="platform_deps_test",
        files={
            "main.py": """
import sys
import os
import platform

def main():
    print(f"Platform: {platform.system()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python version: {platform.python_version()}")

    # Platform-specific logic
    if platform.system() == "Windows":
        import winreg  # Windows only
        return "Windows detected"
    elif platform.system() == "Darwin":
        try:
            import applescript  # macOS only
            return "macOS detected"
        except ImportError:
            return "macOS detected (no applescript)"
    elif platform.system() == "Linux":
        try:
            import pwd  # Unix-like systems
            return "Linux detected"
        except ImportError:
            return "Linux detected (no pwd module)"
    else:
        return f"Unknown platform: {platform.system()}"

def get_platform_info():
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }
""",
            "requirements.txt": """
# Platform-specific dependencies
pywin32>=227 ; sys_platform == "win32"
pyobjc-framework-Cocoa>=8.0 ; sys_platform == "darwin"
python-decouple>=3.6 ; python_version >= "3.7"
typing-extensions>=4.0.0 ; python_version < "3.8"
dataclasses>=0.6 ; python_version < "3.7"
uvloop>=0.17.0 ; implementation_name == "cpython" and sys_platform != "win32"
"""
        },
        directories=[],
        expected_packages=["python-decouple"]  # This should be included on all platforms
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dependency-migration", "auto", "--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed with platform dependencies: {result.stderr}"

def test_international_package_names():
    """Test international package names and characters."""

    fixture = ProjectFixture(
        name="international_packages_test",
        files={
            "main.py": """
# -*- coding: utf-8 -*-
import sys

def main():
    # Test with international characters in strings
    international_data = {
        "spanish": "¡Hola! ¿Cómo estás?",
        "french": "Bonjour! Ça va bien?",
        "german": "Guten Tag! Wie geht's?",
        "russian": "Привет! Как дела?",
        "chinese": "你好！你好吗？",
        "arabic": "مرحبا! كيف حالك؟",
        "japanese": "こんにちは！元気ですか？",
        "korean": "안녕하세요! 어떻게 지내세요？",
        "emoji": "🌍🌎🌏 Hello World! 🚀🎉✨"
    }

    for lang, message in international_data.items():
        print(f"{lang}: {message}")

    return len(international_data)

# Test with function names containing Unicode (not recommended, but testing robustness)
def cálculo():
    return "Cálculo en español"

def обработка():
    return "Обработка на русском"

def 分析():
    return "分析中文"
""",
            "requirements.txt": """
# Test packages with international characters in comments
# Biblioteca para análisis de datos (Spanish for data analysis library)
pandas>=1.5.0

# Bibliothèque de visualisation (French for visualization library)
matplotlib>=3.5.0

# 日本語パッケージ (Japanese packages)
scipy>=1.10.0

# العربي (Arabic)
requests>=2.25.0

# русский (Russian)
numpy>=1.20.0
"""
        },
        directories=[],
        expected_packages=["pandas", "matplotlib", "scipy", "requests", "numpy"]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dependency-migration", "auto", "--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed with international packages: {result.stderr}"

def test_special_characters_in_filenames():
    """Test handling of special characters in filenames."""

    special_chars_files = [
        "file with spaces.py",
        "file-with-dashes.py",
        "file_with_underscores.py",
        "file.with.dots.py",
        "file(with)parentheses.py",
        "file[with]brackets.py",
        "file{with}braces.py",
        "file'with'quotes.py",
        "file@with@symbols.py",
        "file#with#hash.py",
        "file$with$dollar.py",
        "file%with%percent.py",
        "file&with&ampersand.py",
        "file+with+plus.py",
        "file=with=equals.py"
    ]
    if sys.platform == "win32":
        # Windows NTFS forbids " < > | : * ? \ / in filenames; double-quote variant removed above
        # but also filter any other chars that Windows rejects
        special_chars_files = [f for f in special_chars_files if not any(c in f for c in '<>|:*?\\/"')]

    files = {}
    for filename in special_chars_files:
        safe_name = filename.replace(" ", "_").replace("-", "_").replace(".", "_").replace("(", "_").replace(")", "_").replace("[", "_").replace("]", "_").replace("{", "_").replace("}", "_").replace("'", "_").replace('"', "_").replace("@", "_").replace("#", "_").replace("$", "_").replace("%", "_").replace("&", "_").replace("+", "_").replace("=", "_")

        files[filename] = f"""
# File with special characters in name: {filename}
import sys

def {safe_name}_function():
    return "Function from {filename}"

if __name__ == "__main__":
    print({safe_name}_function())
"""

    fixture = ProjectFixture(
        name="special_chars_test",
        files=files,
        directories=[],
        expected_packages=[]
    )

    with temp_manager.create_temp_project(fixture) as project_dir:
        result = executor.run_pyuvstarter(
            project_dir,
            args=["--dry-run", "--verbose"]
        )

        assert result.returncode == 0, f"PyUVStarter failed with special characters: {result.stderr}"

def main():
    """Run all cross-platform tests."""

    tests = [
        ("unicode_filenames", test_unicode_filenames),
        ("unicode_directory_names", test_unicode_directory_names),
        ("emoji_in_code", test_emoji_in_code),
        ("different_text_encodings", test_different_text_encodings),
        ("windows_path_handling", test_windows_path_handling),
        ("platform_specific_dependencies", test_platform_specific_dependencies),
        ("international_package_names", test_international_package_names),
        ("special_characters_in_filenames", test_special_characters_in_filenames),
    ]

    passed = 0
    total = len(tests)

    print("🚀 Running PyUVStarter Cross-Platform Tests")
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
        print("🎉 All cross-platform tests passed!")
        return 0
    else:
        print(f"💥 {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())