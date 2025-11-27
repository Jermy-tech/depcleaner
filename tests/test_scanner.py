"""Tests for scanner module."""
import tempfile
from pathlib import Path
import pytest
from depcleaner.scanner import Scanner


def test_scanner_discovers_files() -> None:
    """Test that scanner discovers Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\n")
        (tmppath / "sub").mkdir()
        (tmppath / "sub" / "test2.py").write_text("import sys\n")
        
        scanner = Scanner(tmppath)
        scanner._discover_python_files()
        
        assert len(scanner.python_files) == 2


def test_scanner_extracts_imports() -> None:
    """Test import extraction from code."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text("import os\nimport sys\nfrom pathlib import Path\n")
        
        scanner = Scanner(tmppath)
        scanner._discover_python_files()
        scanner._analyze_imports()
        
        imports = scanner.all_imports[test_file]
        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports


def test_scanner_detects_unused() -> None:
    """Test detection of unused imports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text("import os\nimport sys\nprint(os.path.exists('.'))\n")
        
        scanner = Scanner(tmppath)
        report = scanner.scan()
        
        unused = report.get_unused_imports()
        assert test_file in unused
        assert "sys" in unused[test_file]
        assert "os" not in unused[test_file]
