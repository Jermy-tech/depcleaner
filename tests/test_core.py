"""Tests for core module."""
import tempfile
from pathlib import Path
import pytest
from depcleaner import DepCleaner


def test_depcleaner_init() -> None:
    """Test DepCleaner initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cleaner = DepCleaner(tmpdir)
        assert cleaner.project_path.exists()


def test_depcleaner_scan() -> None:
    """Test DepCleaner scan functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\n")
        
        cleaner = DepCleaner(tmppath)
        report = cleaner.scan()
        
        assert report.scanned_files >= 1
        assert len(report.all_imports) >= 1
