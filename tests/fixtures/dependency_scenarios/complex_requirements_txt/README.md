# Complex Requirements.txt Fixture

This fixture tests pyuvstarter's handling of complex requirements.txt files with various dependency specification formats.

## Expected Behavior

When pyuvstarter is run on this project:

1. **Dependency Migration**: Should convert all requirements.txt entries to pyproject.toml format
2. **Conflict Resolution**: Should handle version conflicts and compatibility issues
3. **Format Preservation**: Should maintain version ranges, extras, and environment markers
4. **Git Dependencies**: Should properly handle git+https dependencies
5. **URL Dependencies**: Should process direct URL dependencies correctly

## Dependency Categories Tested

- **Standard pinned**: `package==version`
- **Version ranges**: `package>=min,<max`
- **Git dependencies**: `git+https://github.com/user/repo@branch#egg=package`
- **Extras**: `package[extra]==version`
- **Environment markers**: `package==version; sys_platform == "win32"`
- **URL dependencies**: Direct URLs to packages
- **Development tools**: pytest, black, flake8
- **Data science stack**: numpy, pandas, scipy, scikit-learn, tensorflow
- **Web frameworks**: django, flask
- **Database**: sqlalchemy, psycopg2-binary
- **Async**: aiohttp, asyncio-mqtt

## Test Scenarios

Use this fixture to test:
- Complex requirements.txt parsing and conversion
- Version conflict detection and resolution
- Git and URL dependency handling
- Environment marker preservation
- Development dependency categorization
- Data science stack migration
- Web framework dependency management

## Migration Strategies Test

- **auto**: Should intelligently choose between requirements.txt and discovered imports
- **all-requirements**: Should migrate ALL requirements.txt entries
- **only-imported**: Should only migrate packages actually used in code
- **skip-requirements**: Should ignore requirements.txt and only use discovered imports