# 🧹 DepCleaner

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)

**A powerful Python dependency cleanup tool that detects and removes unused imports and packages.**

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Usage](#-usage) • [API](#-python-api) • [Contributing](#-contributing)

</div>

---

## 🌟 Features

DepCleaner helps you maintain clean, efficient Python projects by automatically identifying and removing unused dependencies.

### Core Capabilities

- 🔍 **Smart Detection** - Detects unused imports in Python source files using AST parsing
- 📦 **Package Analysis** - Identifies unused packages in `requirements.txt` and `pyproject.toml`
- 🛡️ **Safe Operations** - Preview changes before applying them with dry-run mode
- 🔄 **Auto-Fix Mode** - Automatically remove unused dependencies with one command
- 📁 **Recursive Scanning** - Scan entire project directories recursively
- 🔐 **Automatic Backups** - Creates backups before making any modifications
- 🎯 **Type Hints** - Full type hint support for better IDE integration
- 📊 **Comprehensive Logging** - Detailed logging for debugging and auditing
- 🐍 **Python API** - Use DepCleaner programmatically in your scripts
- ⚡ **Fast & Lightweight** - Minimal dependencies, maximum performance

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

---

## 🚀 Quick Start

### 1. Scan your project for unused dependencies

```bash
depcleaner scan
```

This will analyze your project and show you all unused imports and packages without making any changes.

### 2. Preview changes before applying

```bash
depcleaner fix --dry-run
```

See exactly what will be removed before making any modifications.

### 3. Clean up your project

```bash
depcleaner fix
```

Automatically remove all unused dependencies with automatic backups.

---

## 💻 Usage

### Command Line Interface

#### Scanning

Scan the current directory:
```bash
depcleaner scan
```

Scan a specific path:
```bash
depcleaner scan --path ./src
```

Scan with verbose output:
```bash
depcleaner -v scan
```

#### Fixing

Fix with automatic backups (default):
```bash
depcleaner fix
```

Fix without creating backups:
```bash
depcleaner fix --no-backup
```

Preview changes without modifying files:
```bash
depcleaner fix --dry-run
```

Fix a specific directory:
```bash
depcleaner fix --path ./myproject
```

Combine options:
```bash
depcleaner -v fix --path ./src --dry-run
```

### Command Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose logging |
| `--path PATH` | Specify the project path to analyze (default: current directory) |
| `--no-backup` | Skip creating backups before fixing |
| `--dry-run` | Show what would be changed without modifying files |

---

## 🐍 Python API

DepCleaner can also be used programmatically in your Python scripts.

### Basic Usage

```python
from depcleaner import DepCleaner

# Initialize the cleaner
cleaner = DepCleaner(project_path=".")

# Scan for unused dependencies
report = cleaner.scan()
print(report)

# Get specific information
unused_imports = report.get_unused_imports()
unused_packages = report.get_unused_packages()

print(f"Found {len(unused_imports)} unused imports")
print(f"Found {len(unused_packages)} unused packages")
```

### Advanced Usage

```python
from depcleaner import DepCleaner

cleaner = DepCleaner(
    project_path="./myproject",
    verbose=True
)

# Scan and get detailed report
report = cleaner.scan()

# Process each file with unused imports
for file_path, imports in report.get_unused_imports().items():
    print(f"\n{file_path}:")
    for imp in imports:
        print(f"  - {imp}")

# Fix issues with backup
stats = cleaner.fix(backup=True)

print(f"✓ Modified {stats['files_modified']} files")
print(f"✓ Removed {stats['imports_removed']} imports")
print(f"✓ Removed {stats['packages_removed']} packages")
```

### Dry Run Mode

```python
cleaner = DepCleaner(project_path=".")

# Preview changes without modifying files
changes = cleaner.fix(dry_run=True)

print("Would make the following changes:")
for change in changes:
    print(f"  - {change}")
```

---

## 🏗️ How It Works

DepCleaner uses a multi-step process to ensure accurate detection:

1. **AST Parsing** - Parses Python files using Abstract Syntax Trees to identify all imports
2. **Usage Analysis** - Scans code to determine which imports are actually used
3. **Dependency Mapping** - Maps imports to installed packages
4. **Cross-referencing** - Compares used packages against declared dependencies
5. **Safe Removal** - Removes only confirmed unused dependencies with optional backups

---

## 🔧 Configuration

### Ignoring Files or Packages

Create a `.depcleanerignore` file in your project root:

```
# Ignore specific files
tests/
*_test.py

# Ignore specific packages
pytest
black
```

### Custom Configuration

Create a `pyproject.toml` configuration:

```toml
[tool.depcleaner]
exclude = ["tests/", "docs/"]
keep_packages = ["pytest", "black"]
aggressive_mode = false
```

---

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=depcleaner tests/
```

Generate coverage report:

```bash
pytest --cov=depcleaner --cov-report=html tests/
```

---

## 📊 Example Output

```
🔍 Scanning project for unused dependencies...

📁 Project: ./myproject
📄 Files scanned: 42
⚠️  Unused imports found: 8
📦 Unused packages found: 3

Unused imports:
  src/utils.py:
    - os (line 1)
    - sys (line 2)
  
  src/main.py:
    - json (line 5)

Unused packages:
  - requests (not used in any file)
  - pandas (not used in any file)
  - numpy (not used in any file)

💡 Run 'depcleaner fix --dry-run' to preview changes
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Reporting Bugs

Found a bug? Please open an issue with:
- A clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Your Python version and OS

### Suggesting Features

Have an idea? Open an issue with:
- A clear description of the feature
- Why it would be useful
- Example use cases

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Run the test suite: `pytest tests/`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to your fork: `git push origin feature-name`
7. Submit a pull request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Jermy-tech/depcleaner.git
cd depcleaner

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with ❤️ by the Python community
- Inspired by the need for cleaner, more maintainable codebases
- Thanks to all contributors who help improve this tool

---

## 📮 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/Jermy-tech/depcleaner/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Jermy-tech/depcleaner/discussions)
- **Twitter**: [@YourTwitter](https://twitter.com/yourhandle)

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with 🐍 and ☕

</div>
