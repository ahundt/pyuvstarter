# Unicode Filename Cross-Platform Fixture

This fixture tests pyuvstarter's handling of Unicode filenames and content across different platforms and encodings.

## Files with Unicode Characters

### naive_data_processor.py
- Tests French accented characters (é, è, ê, à, ç) in content
- Tests class names with Unicode (naïveDataProcessor)
- Tests Unicode strings in content and comments
- Tests emoji handling (😀, 😎, 🚀, 💡, ⚡)
- Uses ASCII filename for cross-platform compatibility

### chinese_data_processor.py
- Tests Chinese characters in Python code content (but ASCII filename)
- Tests Chinese class and function names
- Tests Chinese variable names and strings
- Tests non-ASCII character encoding

## Expected Behavior

When pyuvstarter is run on this project:

1. **File Discovery**: Should correctly discover and enumerate Unicode-named files
2. **Encoding Handling**: Should properly read files with UTF-8 encoding
3. **Content Parsing**: Should extract imports from Unicode content correctly
4. **Path Processing**: Should handle Unicode paths on all platforms
5. **Virtual Environment**: Should create .venv directory respecting Unicode paths
6. **Git Configuration**: Should create .gitignore that handles Unicode filenames

## Unicode Scenarios Tested

### Character Sets
- **French/Latin**: naïve, résumé, café, François, André, Sébastien
- **Chinese**: 数据处理器, 姓名, 地址, 主函数, 张三, 北京
- **Emoji**: 😀 😎 🚀 💡 ⚡ 😊
- **Special Symbols**: Accented characters, non-ASCII symbols

### File Naming
- Unicode characters in filenames
- Mixed ASCII/Unicode filenames
- Long Unicode filenames
- Unicode characters in directory paths

### Content Encoding
- UTF-8 encoded Python files
- Unicode strings in source code
- Unicode comments and docstrings
- Unicode variable and function names
- JSON content with Unicode (ensure_ascii=False)

## Cross-Platform Considerations

### Windows
- Unicode path handling
- Filesystem encoding issues
- Console output encoding
- Git configuration for Unicode

### macOS/Linux
- UTF-8 default encoding
- Proper Unicode filename support
- Shell compatibility with Unicode

### Python Runtime
- sys.getdefaultencoding() handling
- File I/O with explicit encoding
- Import system Unicode support
- String processing with Unicode

## Test Scenarios

Use this fixture to test:
- **File Discovery**: Unicode filename enumeration across platforms
- **Import Parsing**: Extract imports from Unicode-encoded files
- **Path Operations**: Directory operations with Unicode paths
- **Encoding Detection**: Automatic encoding detection and handling
- **Output Generation**: Creating files with Unicode names
- **Git Integration**: .gitignore handling for Unicode files
- **Tool Configuration**: VS Code and other tools with Unicode paths
- **Error Handling**: Graceful failure with encoding issues

## Validation Criteria

After pyuvstarter processes this project:
1. All Unicode files should be discovered and processed
2. Imports should be correctly extracted from Unicode content
3. Virtual environment should be created successfully
4. No encoding errors should occur during processing
5. Unicode filenames should be preserved in .gitignore
6. JSON log should properly encode Unicode content

## Platform-Specific Notes

### Windows
- May need `os.environ['PYTHONIOENCODING'] = 'utf-8'`
- File system limitations for certain Unicode characters
- Console output encoding challenges

### macOS
- Generally excellent Unicode support
- Normalization differences (NFC vs NFD)
- HFS+ filename limitations

### Linux
- Excellent Unicode support in modern distributions
- Varying levels of support in older systems
- Terminal encoding considerations