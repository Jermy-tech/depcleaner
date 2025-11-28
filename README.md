# 🧹 DepCleaner

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
[![PyPI version](https://badge.fury.io/py/depcleaner.svg)](https://pypi.org/project/depcleaner/)

**A powerful Python dependency cleanup tool that detects and removes unused imports and packages.**

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Usage](#-usage) • [API](#-python-api) • [Contributing](#-contributing)

</div>

---

## 🌟 Features

DepCleaner helps you maintain clean, efficient Python projects by automatically identifying and removing unused dependencies.

### Core Capabilities

- 🔍 **Smart Detection** - AST-based parsing for accurate import detection
- 📦 **Package Analysis** - Supports `requirements.txt`, `pyproject.toml` (Poetry, PEP 621), and `setup.py`
- ⚡ **Parallel Processing** - Multi-threaded scanning for faster analysis
- 🛡️ **Safe Operations** - Dry-run mode and timestamped backups
- 🔄 **Auto-Fix Mode** - Automatically remove unused dependencies
- 📁 **Recursive Scanning** - Scan entire project directories
- 🎯 **CI/CD Ready** - Quick check command with proper exit codes
- 📊 **Multiple Output Formats** - Text, detailed, and JSON output
- 🐍 **Python API** - Use programmatically in your scripts
- 🧠 **Smart Filtering** - Auto-filters standard library modules

---

## 📦 Installation

### Using pip

```bash
pip install depcleaner
```

### Using poetry

```bash
poetry add depcleaner --group dev
```

### From source

```bash
git clone https://github.com/Jermy-tech/depcleaner.git
cd depcleaner
pip install -e .
```

### Optional Dependencies

For better `pyproject.toml` parsing on Python < 3.11:
```bash
pip install depcleaner[toml]
```

---

## 🚀 Quick Start

### 1. Scan your project

```bash
depcleaner scan
```

### 2. Preview changes

```bash
depcleaner fix --dry-run
```

### 3. Clean up your project

```bash
depcleaner fix
```

### 4. CI/CD Integration

```bash
depcleaner check  # Exit code 1 if unused deps found
```

---

## 💻 Usage

### Command Line Interface

#### Scanning

```bash
# Scan current directory
depcleaner scan

# Scan specific path
depcleaner scan /path/to/project

# Get JSON output
depcleaner scan --json

# Detailed output
depcleaner scan --format detailed

# Quiet mode (errors only)
depcleaner -q scan
```

#### Fixing

```bash
# Fix with backups (default)
depcleaner fix

# Preview changes only
depcleaner fix --dry-run

# Fix without backups
depcleaner fix --no-backup

# Also clean requirements.txt
depcleaner fix --update-requirements

# Verbose output
depcleaner -v fix
```

#### Quick Check (CI/CD)

```bash
# Fast check with exit codes
depcleaner check

# Use in CI pipelines
depcleaner check || echo "Unused dependencies found!"
```

#### Project Statistics

```bash
# View statistics
depcleaner stats

# Show all dependencies
depcleaner stats --show-all
```

### Command Options

| Command | Description |
|---------|-------------|
| `scan` | Scan for unused dependencies |
| `fix` | Remove unused dependencies |
| `check` | Quick validation (CI-friendly) |
| `stats` | Show project statistics |

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose logging |
| `-q, --quiet` | Suppress non-error output |
| `--path PATH` | Project path (default: current directory) |
| `--json` | Output as JSON |
| `--format FORMAT` | Output format: summary or detailed |
| `--dry-run` | Preview without modifying |
| `--no-backup` | Skip backups |
| `--update-requirements` | Clean requirements.txt |

---

## 🐍 Python API

### Basic Usage

```python
from depcleaner import DepCleaner

# Initialize
cleaner = DepCleaner(project_path=".")

# Scan project
report = cleaner.scan()
print(report)

# Get unused items
unused_imports = report.get_unused_imports()
unused_packages = report.get_unused_packages()
missing_packages = report.get_missing_packages()

print(f"Unused imports: {len(unused_imports)}")
print(f"Unused packages: {len(unused_packages)}")
```

### Advanced Usage

```python
from depcleaner import DepCleaner

# Initialize with options
cleaner = DepCleaner(
    project_path="./myproject",
    max_workers=8  # Parallel processing
)

# Get detailed report
report = cleaner.scan()

# Check each file
for file_path, imports in report.get_unused_imports().items():
    print(f"\n{file_path}:")
    for imp in imports:
        print(f"  - {imp}")

# Fix with options
stats = cleaner.fix(backup=True, dry_run=False)

print(f"✓ Files modified: {stats['files_modified']}")
print(f"✓ Imports removed: {stats['imports_removed']}")
```

### Useful Methods

```python
# Validate project structure
validation = cleaner.validate_project()
print(validation)

# Estimate cleanup impact
impact = cleaner.estimate_cleanup_impact()
print(f"Cleanup potential: {impact['cleanup_percentage']}%")

# Get dependency graph
graph = cleaner.get_dependency_graph()

# Find duplicate packages
duplicates = cleaner.find_duplicate_dependencies()

# Analyze single file
results = cleaner.analyze_file("src/main.py")
print(results['unused_imports'])

# Export report
report.save("report.json")  # or "report.txt"
```

---

## 🏗️ How It Works

1. **Discovery** - Recursively finds all Python files (excludes venv, cache dirs)
2. **AST Parsing** - Parses files to extract imports accurately
3. **Usage Analysis** - Detects which imports are actually used in code
4. **Dependency Mapping** - Maps imports to declared packages
5. **Standard Library Filtering** - Excludes stdlib modules automatically
6. **Safe Removal** - Removes unused imports with backups

---

## 📊 Example Output

```
====================================================================
DepCleaner Scan Report
====================================================================
Project: /home/user/myproject
Files scanned: 42
Declared dependencies: 15
Used dependencies: 12

Unused Imports:
--------------------------------------------------------------------

src/utils.py:
  - os
  - sys

src/main.py:
  - json

✓ No unused imports found

Unused Packages (declared but not used):
--------------------------------------------------------------------
  - requests
  - pandas
  - numpy

====================================================================
```

---

## 🔧 Configuration

DepCleaner works out of the box, but you can customize behavior:

### Excluded Directories

By default, these are excluded:
- `.venv`, `venv`, `env`, `.env`
- `__pycache__`, `.pytest_cache`, `.mypy_cache`
- `.git`, `.hg`, `.svn`
- `build`, `dist`, `.eggs`, `*.egg-info`
- `node_modules`, `.tox`, `.coverage`, `htmlcov`

### Programmatic Configuration

```python
cleaner = DepCleaner(
    project_path=".",
    max_workers=4,  # Adjust for your system
    exclude_dirs={'custom_dir', 'another_dir'}
)
```

---

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=depcleaner tests/

# Generate HTML coverage report
pytest --cov=depcleaner --cov-report=html tests/
```

---

## 🤝 Contributing

Contributions welcome! Please check out our [contributing guidelines](CONTRIBUTING.md).

### Quick Start

```bash
# Clone repo
git clone https://github.com/Jermy-tech/depcleaner.git
cd depcleaner

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Submit PR
git checkout -b feature-name
git commit -am 'Add feature'
git push origin feature-name
```

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with ❤️ for the Python community.

---

## 📮 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/Jermy-tech/depcleaner/issues)
- **PyPI**: [pypi.org/project/depcleaner](https://pypi.org/project/depcleaner/)

---

<div align="center">

**⭐ Star us on GitHub if this tool helps you!**

Made with 🐍 and ☕

</div>
