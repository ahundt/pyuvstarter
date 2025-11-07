# Simple Python Project

This is a basic single-file Python project fixture for testing pyuvstarter.

## Expected Behavior

When pyuvstarter is run on this project:

1. **Project Initialization**: Should create `pyproject.toml`
2. **Virtual Environment**: Should create `.venv/` directory
3. **Git Configuration**: Should create `.gitignore`
4. **Dependency Discovery**: Should discover any imports (none in this basic case)
5. **Tool Configuration**: Should set up VS Code, ruff, etc.

## Files

- `main.py`: Main Python script with basic functionality
- `README.md`: This file

## Test Scenarios

Use this fixture to test:
- New project setup from scratch
- Minimal project handling
- Basic dependency discovery (no dependencies expected)
- Tool installation and configuration