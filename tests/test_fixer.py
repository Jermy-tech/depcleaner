"""Tests for fixer module."""
import tempfile
from pathlib import Path
import pytest
from depcleaner import DepCleaner


def test_fixer_removes_unused() -> None:
    """Test that fixer removes unused imports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text("import os\nimport sys\nprint('hello')\n")
        
        cleaner = DepCleaner(tmppath)
        stats = cleaner.fix(backup=False)
        
        assert stats["files_modified"] >= 1
        assert stats["imports_removed"] >= 2


def test_fixer_creates_backup() -> None:
    """Test that fixer creates backup files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text("import os\nprint('hello')\n")
        
        cleaner = DepCleaner(tmppath)
        stats = cleaner.fix(backup=True)
        
        backup_file = test_file.with_suffix(".py.bak")
        assert backup_file.exists()
        assert stats["backups_created"] >= 1
