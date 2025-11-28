"""Test suite for DepCleaner.

This test suite covers:
- Core functionality (DepCleaner class)
- Scanner (file discovery, import extraction, usage detection)
- Fixer (import removal, backups, dry-run)
- Package mapper (PyPI name to import name mapping)

Run with: pytest tests/
"""

__version__ = "2.0.0"