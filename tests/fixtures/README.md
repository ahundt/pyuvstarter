# PyUVStarter Test Fixtures

This directory contains comprehensive test fixtures for validating pyuvstarter functionality across various project structures, dependency scenarios, and edge cases.

## Directory Structure

```
fixtures/
├── README.md                                    # This file
├── basic_project_structures/                   # Simple project layouts
│   ├── simple_python_project/                  # Single-file Python project
│   └── src_layout_package/                     # Modern src-layout package
├── dependency_scenarios/                       # Dependency testing scenarios
│   └── complex_requirements_txt/               # Complex requirements.txt edge cases
├── jupyter_notebooks/                          # Notebook discovery and processing
│   ├── data_analysis_notebook.ipynb           # Comprehensive notebook with imports
│   └── README.md                               # Notebook testing documentation
├── import_fixing_scenarios/                    # Relative import fixing tests
│   └── src_layout_relative_imports/            # Project with relative imports
└── cross_platform_scenarios/                   # Unicode and platform testing
    └── unicode_filenames/                      # Unicode filename and content handling
```

## Fixture Categories

### 1. Basic Project Structures
**Purpose**: Test fundamental project detection and setup

**Scenarios**:
- Single-file Python projects
- Modern src-layout packages
- Flat-layout packages
- Multi-package projects

**Validation Points**:
- Project structure detection
- Basic dependency discovery
- Virtual environment creation
- Tool configuration setup

### 2. Dependency Scenarios
**Purpose**: Test complex dependency management and migration

**Scenarios**:
- Complex requirements.txt with various formats
- Version conflicts and resolution
- Git and URL dependencies
- Environment markers and extras
- Development vs production dependencies

**Validation Points**:
- Requirements.txt to pyproject.toml migration
- Version conflict detection and resolution
- Dependency format preservation
- Migration strategy behavior (auto, all-requirements, only-imported, skip-requirements)

### 3. Jupyter Notebooks
**Purpose**: Test notebook discovery and dependency extraction

**Scenarios**:
- Notebooks with various import patterns
- !pip install magic commands
- Complex notebook structures
- Mixed cell types (code, markdown)
- JSON parsing edge cases

**Validation Points**:
- Notebook file discovery
- Dual-strategy processing (nbconvert + pipreqs, JSON + AST + regex)
- Import extraction from code cells
- Magic command parsing
- Error handling for malformed notebooks

### 4. Import Fixing Scenarios
**Purpose**: Test automatic relative import fixing

**Scenarios**:
- Projects with relative imports
- Complex relative import patterns
- Mixed relative/absolute imports
- Function-scope relative imports
- Circular dependency testing

**Validation Points**:
- Ruff TID252 rule detection
- Automatic import fixing
- Relative to absolute import conversion
- Functionality preservation
- JSON log file validation

### 5. Cross-Platform Scenarios
**Purpose**: Test Unicode and platform-specific handling

**Scenarios**:
- Unicode filenames and content
- Non-ASCII character encoding
- Multi-language source code
- Emoji and special symbols
- Platform-specific path handling

**Validation Points**:
- Unicode file discovery
- Encoding handling
- Cross-platform path operations
- International character support
- Platform-specific tool configuration

## Usage Guidelines

### For Testing
Each fixture is designed to test specific pyuvstarter functionality:

```bash
# Test basic project setup
pyuvstarter /path/to/fixtures/basic_project_structures/simple_python_project

# Test dependency migration
pyuvstarter /path/to/fixtures/dependency_scenarios/complex_requirements_txt --dependency-migration auto

# Test import fixing
pyuvstarter /path/to/fixtures/import_fixing_scenarios/src_layout_relative_imports

# Test Unicode handling
pyuvstarter /path/to/fixtures/cross_platform_scenarios/unicode_filenames
```

### For Development
Use fixtures to validate new pyuvstarter features:

1. **Select appropriate fixture** based on functionality being tested
2. **Run pyuvstarter** on the fixture directory
3. **Validate expected behavior** using fixture documentation
4. **Check JSON log file** for detailed execution information
5. **Verify tool configuration** files are created correctly

### Fixture Creation Standards

When creating new fixtures:

1. **Comprehensive Documentation**: Each fixture needs detailed README.md
2. **Expected Behavior**: Clearly document what pyuvstarter should do
3. **Test Scenarios**: List specific validation points and edge cases
4. **Self-Contained**: Fixtures should work independently
5. **Minimal Dependencies**: Use only dependencies necessary for testing
6. **Cross-Platform**: Ensure fixtures work on Windows, macOS, and Linux

## Integration with Test Suite

These fixtures are used by the comprehensive test suite in `/tests/`:

- `test_project_structure.py` → `basic_project_structures/`
- `test_dependency_migration.py` → `dependency_scenarios/`
- `test_jupyter_pipeline.py` → `jupyter_notebooks/`
- `test_import_fixing.py` → `import_fixing_scenarios/`
- `test_cross_platform.py` → `cross_platform_scenarios/`

## Maintenance

### Adding New Fixtures
1. Create appropriate subdirectory
2. Add fixture files and documentation
3. Update this README.md
4. Create corresponding tests in `/tests/`
5. Update test documentation

### Updating Existing Fixtures
1. Check impact on existing tests
2. Update fixture documentation
3. Validate expected behavior changes
4. Update related test cases
5. Verify cross-platform compatibility

## Quality Assurance

Each fixture should pass these quality checks:

- [ ] **Documentation**: Complete README.md with expected behavior
- [ ] **Functionality**: Code runs without errors
- [ ] **Isolation**: Self-contained, no external dependencies
- [ ] **Cross-Platform**: Works on Windows, macOS, Linux
- [ ] **Test Coverage**: Corresponds to test cases in test suite
- [ ] **Validation**: Clear success/failure criteria
- [ ] **Maintenance**: Easy to understand and modify

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure fixture code is syntactically correct
2. **Path Issues**: Use relative paths and proper path joining
3. **Encoding Problems**: Specify UTF-8 encoding for Unicode content
4. **Dependency Conflicts**: Use compatible package versions
5. **Platform Differences**: Test on multiple platforms

### Debugging Tips

1. **Use Verbose Mode**: `pyuvstarter --verbose` for detailed output
2. **Check JSON Log**: Review `pyuvstarter_setup_log.json`
3. **Validate Manually**: Run fixture code independently
4. **Test Isolation**: Verify fixtures work independently
5. **Platform Testing**: Test on target platforms