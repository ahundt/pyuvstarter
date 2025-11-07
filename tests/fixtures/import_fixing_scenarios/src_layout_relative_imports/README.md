# Relative Import Fixing Fixture

This fixture tests pyuvstarter's automatic relative import fixing functionality using Ruff's TID252 rule.

## Expected Behavior

When pyuvstarter is run on this project:

1. **Relative Import Detection**: Ruff should detect all relative imports violating TID252
2. **Automatic Fixing**: pyuvstarter should automatically fix all detected relative imports
3. **Conversion to Absolute**: All `from .module import` should become `from myapp.module import`
4. **Preserve Functionality**: Fixed imports should maintain the same functionality
5. **Logging**: All import fixing actions should be logged in the JSON log file

## Files with Relative Imports

### src/myapp/__init__.py
```python
from .main import main_function                    # Should be: from myapp.main import main_function
from .utils import helper_function, DataProcessor  # Should be: from myapp.utils import helper_function, DataProcessor
from .models import UserModel, ProductModel        # Should be: from myapp.models import UserModel, ProductModel
```

### src/myapp/main.py
```python
from . import utils                                # Should be: import myapp.utils
from .models import UserModel                      # Should be: from myapp.models import UserModel
from .utils import DataProcessor, helper_function  # Should be: from myapp.utils import DataProcessor, helper_function
from .config import settings                       # Should be: from myapp.config import settings
```

### src/myapp/utils.py
```python
from .models import UserModel                      # Should be: from myapp.models import UserModel
from .config import get_config                     # Should be: from myapp.config import get_config
from . import main                                 # Should be: import myapp.main
from .models import ProductModel                   # Should be: from myapp.models import ProductModel
```

### src/myapp/models.py
```python
from .utils import DataProcessor                   # Should be: from myapp.utils import DataProcessor
from .config import settings                       # Should be: from myapp.config import settings
```

### src/myapp/config.py
```python
from . import utils                                # Should be: import myapp.utils
```

## Relative Import Patterns Tested

1. **Simple relative imports**: `from .module import name`
2. **Module imports**: `from . import module`
3. **Multiple imports**: `from .module import func1, func2, Class1`
4. **Function-scope imports**: Relative imports inside functions
5. **Complex dependencies**: Circular relative imports (for testing edge cases)
6. **Mixed imports**: Relative and absolute imports in same file

## Test Scenarios

Use this fixture to test:
- **Detection Accuracy**: Ruff TID252 rule detection of all relative import patterns
- **Fixing Completeness**: Automatic fixing of all detected violations
- **Import Conversion**: Correct conversion from relative to absolute imports
- **Preservation**: Ensuring fixed imports maintain original functionality
- **Edge Cases**: Handling of complex relative import scenarios
- **Error Recovery**: Graceful handling of fixing failures
- **Logging Verification**: JSON log file contains all import fixing actions
- **Performance**: Import fixing performance with multiple files

## Expected Ruff Output

Before fixing:
```
src/myapp/__init__.py:5:1: TID252 All imports are relative
src/myapp/main.py:3:1: TID252 All imports are relative
src/myapp/utils.py:3:1: TID252 All imports are relative
src/myapp/models.py:3:1: TID252 All imports are relative
src/myapp/config.py:3:1: TID252 All imports are relative
```

After fixing:
All relative imports should be converted to absolute imports using `myapp.` prefix.

## Configuration

The `pyproject.toml` is configured with:
- Ruff TID252 rule enabled
- Isort profile set to "black" for consistent formatting
- Project structure optimized for import fixing

## Validation

After pyuvstarter processes this project:
1. All files should have only absolute imports
2. JSON log should show import fixing actions
3. Project should still run without import errors
4. All functionality should be preserved