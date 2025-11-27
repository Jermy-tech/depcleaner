# DepCleaner

A powerful Python dependency cleanup tool that detects and removes unused imports and packages.

## Features

- Detects unused imports in Python source files
- Identifies unused packages in requirements.txt and pyproject.toml
- Static analysis using AST parsing
- Safe mode (preview) and auto-fix mode
- Recursive directory scanning
- CLI and Python API
- Automatic backups before modifications
- Type hints and comprehensive logging

## Installation

pip install depcleaner

## CLI Usage

### Scan for unused dependencies

depcleaner scan

### Scan specific directory

depcleaner scan --path ./src

### Fix unused dependencies

depcleaner fix

### Fix without backup

depcleaner fix --no-backup

### Preview changes (dry run)

depcleaner fix --dry-run

### Verbose output

depcleaner -v scan

## Python API

from depcleaner import DepCleaner

# Initialize
cleaner = DepCleaner(project_path=".")

# Scan for issues
report = cleaner.scan()
print(report)

# Get unused imports per file
unused_imports = report.get_unused_imports()

# Get unused packages
unused_packages = report.get_unused_packages()

# Auto-fix with backup
stats = cleaner.fix(backup=True)
print(f"Modified {stats['files_modified']} files")
print(f"Removed {stats['imports_removed']} imports")

## Development

### Running tests

pytest tests/

### Running with coverage

pytest --cov=depcleaner tests/

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.