# 🧹 DepCleaner

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
[![PyPI version](https://badge.fury.io/py/depcleaner.svg)](https://pypi.org/project/depcleaner/)
[![Downloads](https://pepy.tech/badge/depcleaner)](https://pepy.tech/project/depcleaner)

**Finally, a Python tool that cleans up your messy imports and unused dependencies!**

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Usage](#-usage) • [API](#-python-api) • [Contributing](#-contributing)

---

### 📜 License & Contributions

**MIT License** - Free and open source!

Want to help out? Got ideas? Found a bug? We'd love to hear from you!  
**Check us out:** [github.com/Jermy-tech/depcleaner](https://github.com/Jermy-tech/depcleaner)

PRs, issues, and feature requests are always welcome! 🚀

---

</div>

## 🌟 What Can It Do?

DepCleaner keeps your Python projects tidy by finding and removing all those imports and packages you're not actually using. You know, the ones you added at 2 AM and totally forgot about.

### The Good Stuff

- 🔍 **Smart Detection** - Uses AST parsing to actually understand your code (way better than regex!)
- 📦 **Works Everywhere** - Handles `requirements.txt`, `pyproject.toml` (Poetry, PEP 621), `setup.py`, `setup.cfg`, and `Pipfile`
- ⚡ **Blazing Fast** - Multi-threaded scanning that automatically figures out the best number of workers
- 🛡️ **Super Safe** - Test it with dry-run mode, get timestamped backups, never lose your work
- 🔄 **Auto-Fix Mode** - Let it clean up your mess automatically (with rollback, just in case!)
- 📁 **Recursive Scanning** - Point it at your project root and let it do its thing
- 🎯 **CI/CD Ready** - Perfect for catching unused deps in your pipeline
- 📊 **Multiple Outputs** - Get your results as text, detailed reports, or JSON
- 🐍 **Python API** - Use it in your own scripts with progress callbacks
- 🧠 **Smart Filtering** - Automatically ignores stdlib stuff (because obviously)
- 🏥 **Health Score** - Get a grade for your dependency hygiene (aim for that A+!)
- 📈 **Progress Tracking** - Watch it work in real-time on bigger projects
- 💾 **Result Caching** - Scans are faster the second time around

### What's New in v2.0?

- ✅ **Way better `from X import Y` detection** - Actually tracks what you use now
- ⚡ **Seriously faster** - Like 3x faster. We're talking serious speed boost here
- 🎯 **Health scoring** - Know exactly how clean (or messy) your dependencies are
- 📊 **Better stats** - More insights into what's going on
- 🔧 **Handles edge cases** - Won't freak out on weird encodings anymore
- 🌐 **More formats** - Now works with `setup.cfg` and `Pipfile` too
- 💡 **Smart tips** - Gets context-aware recommendations based on your project

---

## 📦 Installation

### The easy way (pip)

```bash
pip install depcleaner
```

### Poetry gang

```bash
poetry add depcleaner --group dev
```

### Pipenv users

```bash
pipenv install depcleaner --dev
```

### From source (if you're feeling adventurous)

```bash
git clone https://github.com/Jermy-tech/depcleaner.git
cd depcleaner
pip install -e .
```

### Want Extra Features?

Better `pyproject.toml` parsing (Python < 3.11):
```bash
pip install depcleaner[toml]
```

Pretty console output:
```bash
pip install depcleaner[rich]
```

Everything:
```bash
pip install depcleaner[all]
```

---

## 🚀 Quick Start

### 1. Check how messy things are

```bash
depcleaner stats --show-all
```

### 2. Scan your project

```bash
depcleaner scan
```

### 3. See what would change (no risk!)

```bash
depcleaner fix --dry-run
```

### 4. Actually clean things up

```bash
depcleaner fix
```

### 5. Add it to your CI/CD

```bash
depcleaner check  # Fails if it finds unused stuff
```

---

## 💻 How to Use It

### Command Line Stuff

#### Health Check (the new hotness!)

```bash
# Get your dependency health score
depcleaner stats

# See everything in detail
depcleaner stats --show-all
```

#### Scanning

```bash
# Scan wherever you are
depcleaner scan

# Or point it somewhere specific
depcleaner scan /path/to/project

# JSON output for the data nerds
depcleaner scan --json

# Want more details? We got you
depcleaner scan --format detailed

# Shh, quiet mode
depcleaner -q scan
```

#### Fixing Things

```bash
# Fix it (with backups, because we're not monsters)
depcleaner fix

# Just show me what would happen
depcleaner fix --dry-run

# YOLO mode (no backups - probably don't do this)
depcleaner fix --no-backup

# Clean up requirements.txt too
depcleaner fix --update-requirements

# Tell me everything you're doing
depcleaner -v fix

# Only touch specific files
depcleaner fix --pattern "src/*.py"
```

#### Quick Check (great for CI)

```bash
# Fast validation
depcleaner check

# Use it in your pipeline
depcleaner check || echo "⚠️ Found some unused stuff!"

# GitHub Actions example
- name: Check dependencies
  run: depcleaner check
```

#### Project Stats

```bash
# Basic stats
depcleaner stats

# Show me everything
depcleaner stats --show-all

# Export as JSON
depcleaner stats --json > stats.json
```

### All the Commands

| Command | What it does |
|---------|-------------|
| `scan` | Find unused stuff |
| `fix` | Remove unused stuff |
| `check` | Quick check (perfect for CI) |
| `stats` | Show stats and health score |

| Global Options | What they do |
|---------------|-------------|
| `-v, --verbose` | More logging |
| `-q, --quiet` | Less logging |
| `--version` | Show version |

| Scan Options | What they do |
|--------------|-------------|
| `--path PATH` | Where to scan (default: here) |
| `--json` | JSON output |
| `--format FORMAT` | `summary` or `detailed` |

| Fix Options | What they do |
|-------------|-------------|
| `--dry-run` | Preview only |
| `--no-backup` | No backups (risky!) |
| `--update-requirements` | Clean requirements.txt |
| `--pattern PATTERN` | Filter which files to fix |

---

## 🐍 Python API

### Basic Usage

```python
from depcleaner import DepCleaner

# Fire it up
cleaner = DepCleaner(project_path=".")

# Scan the project
report = cleaner.scan()
print(report)

# See what's not being used
unused_imports = report.get_unused_imports()
unused_packages = report.get_unused_packages()
missing_packages = report.get_missing_packages()

print(f"Unused imports: {len(unused_imports)}")
print(f"Unused packages: {len(unused_packages)}")
print(f"Missing packages: {len(missing_packages)}")
```

### Advanced Usage with Progress Tracking

```python
from depcleaner import DepCleaner

def progress_callback(current, total, message):
    """See what's happening in real-time."""
    percent = (current / total) * 100
    print(f"[{percent:.1f}%] {message}")

# Set it up with all the bells and whistles
cleaner = DepCleaner(
    project_path="./myproject",
    max_workers=None,  # Let it figure out the best number
    cache_results=True  # Speed up re-scans
)

# Scan with live updates
report = cleaner.scan(progress_callback=progress_callback)

# Get your health score
health = cleaner.get_health_score()
print(f"\n📊 Health Score: {health['score']}/100 (Grade: {health['grade']})")
print("\nHere's what you should do:")
for rec in health['recommendations']:
    print(f"  • {rec}")

# See the details for each file
for file_path, imports in report.get_unused_imports().items():
    print(f"\n{file_path}:")
    for imp in imports:
        print(f"  - {imp}")

# Fix everything with progress tracking
stats = cleaner.fix(
    backup=True, 
    dry_run=False,
    progress_callback=progress_callback
)

print(f"\n✅ Files modified: {stats['files_modified']}")
print(f"✅ Imports removed: {stats['imports_removed']}")
print(f"✅ Lines saved: ~{stats['imports_removed']}")
```

### Health Score & Validation

```python
from depcleaner import DepCleaner

cleaner = DepCleaner("./myproject")

# Get the full health report
health = cleaner.get_health_score()
print(f"Score: {health['score']}/100")
print(f"Grade: {health['grade']}")

# Dive into the details
metrics = health['metrics']
print(f"Unused imports: {metrics['unused_imports']}")
print(f"Unused packages: {metrics['unused_packages']}")
print(f"Missing packages: {metrics['missing_packages']}")

# Make sure everything's set up right
validation = cleaner.validate_project()
if not validation['valid']:
    print("❌ Uh oh, something's not right:")
    for error in validation['errors']:
        print(f"  • {error}")

# Get some suggestions
for rec in validation['recommendations']:
    print(f"💡 {rec}")
```

### More Cool Stuff You Can Do

```python
# See how much you could clean up
impact = cleaner.estimate_cleanup_impact()
print(f"You could clean up: {impact['cleanup_percentage']}%")
print(f"Lines you'd save: {impact['estimated_lines_saved']}")
print(f"Files that would change: {len(impact['affected_files'])}")

# See what depends on what
graph = cleaner.get_dependency_graph()
for dep, files in graph.items():
    print(f"{dep} is used by: {', '.join(files)}")

# Find duplicate packages (like package-name vs package_name)
duplicates = cleaner.find_duplicate_dependencies()
for canonical, variants in duplicates.items():
    print(f"Might be duplicates: {', '.join(variants)}")

# Check just one file
results = cleaner.analyze_file("src/main.py")
print(f"All imports: {results['all_imports']}")
print(f"Used imports: {results['used_imports']}")
print(f"Unused imports: {results['unused_imports']}")

# Save the report
report.save("report.json")  # JSON
report.save("report.txt")   # Plain text

# Export your settings
cleaner.export_config("depcleaner-config.json")

# Start fresh (clear the cache)
cleaner.clear_cache()
```

---

## 🗺️ How Does It Work?

1. **Discovery** - Finds all your Python files (skips venv, cache, and huge files)
2. **AST Parsing** - Actually parses your code to understand it properly
3. **Usage Analysis** - Figures out what you're actually using (now works great with `from X import Y`)
4. **Package Mapping** - Matches PyPI names to import names using metadata
5. **Dependency Mapping** - Connects imports to your declared packages
6. **Smart Filtering** - Automatically excludes standard library stuff
7. **Health Scoring** - Gives you a grade based on how clean your dependencies are
8. **Safe Removal** - Cleans things up with backups and preserves your file structure

### Package Name Mapping Magic

DepCleaner knows that PyPI names and import names are often different:

```python
# ✅ It knows these are the SAME thing:
# requirements.txt: cupy-cuda13x==13.6.0
# your code: import cupy

# ✅ More examples:
# pillow → PIL
# python-dateutil → dateutil  
# beautifulsoup4 → bs4
# scikit-learn → sklearn
# pyyaml → yaml
# opencv-python → cv2
```

Works with 50+ common packages plus auto-detection for others!

### Better `from X import Y` Detection

```python
# ✅ Now correctly tracks what you actually use:
from numpy import array
arr = array([1, 2, 3])  # numpy = USED ✓

from requests import get
# (not using get anywhere)  # requests = UNUSED ✗

# ✅ Handles aliases too:
from numpy import array as arr
x = arr([1, 2, 3])  # numpy = USED ✓
```

---

## 📊 What the Output Looks Like

```
====================================================================
DepCleaner Scan Report
====================================================================
Project: /home/user/myproject
Files scanned: 42
Declared dependencies: 15
Used dependencies: 12

📊 Health Score: 78/100 (Grade: C)

Unused Imports:
--------------------------------------------------------------------

src/utils.py:
  - os
  - sys

src/main.py:
  - json

Unused Packages (you can remove these):
--------------------------------------------------------------------
  - requests (from requirements.txt)
  - pandas (from pyproject.toml)
  - numpy (from requirements.txt)

💡 Here's what you should do:
  • Run 'depcleaner fix' to remove those 3 unused imports
  • Remove 3 unused packages from your dependencies
  • Clean things up to get that A grade (90+)!

====================================================================
✅ Ready to clean up? Run 'depcleaner fix'
====================================================================
```

### Health Score Breakdown

```bash
$ depcleaner stats

Project Statistics
==================================================
Python files: 42
Total imports: 156
Unique packages imported: 12
Declared dependencies: 15

Unused imports: 3
Unused packages: 3
Missing packages: 0

📊 Health Score: 78/100 (Grade: C)

Metrics:
  • Import cleanliness: 98.1%
  • Package efficiency: 80.0%
  • Dependency completeness: 100.0%

💡 Next steps:
  • Run 'depcleaner fix' to clean up those 3 imports
  • Remove 3 packages you're not using
```

---

## 🔧 Configuration

DepCleaner works right out of the box, but you can tweak it if you want!

### What Gets Ignored (by default)

Don't worry, these are automatically skipped:
- Virtual environments: `.venv`, `venv`, `env`, etc.
- Cache folders: `__pycache__`, `.pytest_cache`, etc.
- Version control: `.git`, `.hg`, `.svn`
- Build stuff: `build`, `dist`, `.eggs`
- IDE folders: `.idea`, `.vscode`
- Docs: `docs`, `_build`, `site`
- Other stuff: `node_modules`, `htmlcov`

### Customize in Code

```python
from depcleaner import DepCleaner

cleaner = DepCleaner(
    project_path=".",
    max_workers=None,  # Auto-detect (recommended!)
    exclude_dirs={'my_custom_dir', 'another_one'},  # Extra exclusions
    cache_results=True  # Cache for speed
)

# Save your config
cleaner.export_config("config.json")
```

### Use a Config File

Make a `depcleaner-config.json`:

```json
{
  "project_path": ".",
  "max_workers": 8,
  "exclude_dirs": ["vendor", "third_party"],
  "cache_results": true
}
```

---

## 🧪 Testing

```bash
# Install dev stuff
pip install -e ".[dev]"

# Run tests
pytest tests/

# With coverage
pytest --cov=depcleaner tests/

# Make a pretty HTML coverage report
pytest --cov=depcleaner --cov-report=html tests/

# Run one specific test
pytest tests/test_scanner.py::test_scanner_detects_from_import_usage

# Verbose mode
pytest -v tests/
```

### Test Coverage

We're sitting pretty at 95%+ coverage!
- Core: 98%
- Scanner: 96%
- Fixer: 94%
- Package Mapper: 97%
- Report: 99%

---

## 🤝 Want to Help Out?

We'd love your contributions! Whether it's fixing bugs, adding features, or just improving docs - all help is appreciated!

### Getting Started

```bash
# Grab the code
git clone https://github.com/Jermy-tech/depcleaner.git
cd depcleaner

# Install dev dependencies
pip install -e ".[dev]"

# Make sure tests pass
pytest tests/

# Run the linters
black depcleaner tests
flake8 depcleaner tests
mypy depcleaner

# Push your changes
git checkout -b my-cool-feature
git commit -am 'Added something awesome'
git push origin my-cool-feature
```

### The Process

1. **Fork it**
2. **Create a branch** (`git checkout -b feature/my-awesome-thing`)
3. **Write some tests** (we like tests!)
4. **Make sure they pass** (`pytest tests/`)
5. **Format your code** (`black`, `flake8`)
6. **Commit it** (`git commit -am 'Did the thing'`)
7. **Push it** (`git push origin feature/my-awesome-thing`)
8. **Open a PR** (and we'll check it out!)

### What We're Looking For

- 🐛 **Bug fixes** - Help us squash 'em!
- ✨ **Cool new features** - Got an idea? Share it!
- 📚 **Better docs** - Always room for improvement
- 🧪 **More tests** - Can never have too many
- 🎨 **Code improvements** - Make it faster, cleaner, better

### Got an Idea?

Open an issue and tell us about it:  
**[github.com/Jermy-tech/depcleaner/issues](https://github.com/Jermy-tech/depcleaner/issues)**

---

### Recent Stuff

**v2.0.0** (You are here!)
- ✅ Way better `from X import Y` detection
- ⚡ Crazy performance boost (3x faster!)
- 🏥 New health scoring system
- 📊 Better stats and progress tracking
- 🔧 Handles weird edge cases now
- 🌐 Works with more file formats
- 💾 Caches results for speed

**v1.4.1**
- First stable release
- Basic scanning and fixing
- Multi-threaded processing
- Package name mapping

---

## 📜 License

**MIT License** - Do whatever you want with it!

Full legal text: basically, you can use, modify, and distribute this however you want. Just include the copyright notice and don't blame us if something breaks.

See [LICENSE](LICENSE) for the full details.

---

## 🙏 Thanks!

Built with ❤️ for the Python community.

Shoutout to:
- Everyone who's contributed
- The Python packaging folks
- You, for using this tool!

---

## 📮 Get in Touch

- **Found a bug?** [Open an issue](https://github.com/Jermy-tech/depcleaner/issues)
- **Want a feature?** [Tell us about it](https://github.com/Jermy-tech/depcleaner/issues)
- **Check it out on PyPI**: [pypi.org/project/depcleaner](https://pypi.org/project/depcleaner/)

### Need Help?

1. Read the docs (you're doing it!)
2. Search [existing issues](https://github.com/Jermy-tech/depcleaner/issues)
3. Still stuck? [Open a new issue](https://github.com/Jermy-tech/depcleaner/issues/new)

---

<div align="center">

**⭐ If this saved you time, give us a star on GitHub!**

Made with 🧹 and way too much ☕

[Report Bug](https://github.com/Jermy-tech/depcleaner/issues) · [Request Feature](https://github.com/Jermy-tech/depcleaner/issues) · [View Stats](https://pepy.tech/project/depcleaner)

</div>