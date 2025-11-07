# Src-Layout Package Fixture

This is a standard Python package fixture using the modern src-layout structure for testing pyuvstarter.

## Expected Behavior

When pyuvstarter is run on this project:

1. **Project Detection**: Should recognize src-layout structure with `/src/myapp/`
2. **Dependency Discovery**: Should discover imports in `main.py`, `utils.py`, and `__init__.py`
3. **Virtual Environment**: Should create `.venv/` directory at project root
4. **Git Configuration**: Should create `.gitignore` appropriate for Python projects
5. **Tool Configuration**: Should set up VS Code, ruff, etc.

## Files

- `pyproject.toml`: Modern Python project configuration
- `src/myapp/__init__.py`: Package initialization with version and exports
- `src/myapp/main.py`: Main module with imports and CLI entry point
- `src/myapp/utils.py`: Utility functions for testing dependency discovery

## Test Scenarios

Use this fixture to test:
- Src-layout project detection and handling
- Import discovery across multiple modules
- Package configuration and setup
- Tool integration with modern project structure
- Dependency discovery from __init__.py imports

## Import Structure

```
src/myapp/
├── __init__.py     → imports from main, utils
├── main.py         → imports from utils, __version__
└── utils.py        → standalone utilities
```

Expected discovered imports: None (all built-in functions) but demonstrates import parsing across src-layout.