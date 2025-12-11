"""Tests for core module."""
import tempfile
from pathlib import Path
import pytest  # type: ignore
from depcleaner import DepCleaner


def test_depcleaner_init() -> None:
    """Test DepCleaner initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cleaner = DepCleaner(tmpdir)
        assert cleaner.project_path.exists()
        assert cleaner.project_path.is_dir()


def test_depcleaner_init_with_options() -> None:
    """Test DepCleaner initialization with options."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cleaner = DepCleaner(tmpdir, max_workers=2)
        assert cleaner.scanner.max_workers == 2


def test_depcleaner_invalid_path() -> None:
    """Test DepCleaner with invalid path."""
    with pytest.raises(ValueError):
        DepCleaner("/nonexistent/path")


def test_depcleaner_scan() -> None:
    """Test DepCleaner scan functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\n")
        
        cleaner = DepCleaner(tmppath)
        report = cleaner.scan()
        
        assert report.scanned_files >= 1
        assert len(report.all_imports) >= 1


def test_depcleaner_scan_multiple_files() -> None:
    """Test scanning multiple files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test1.py").write_text("import os\n")
        (tmppath / "test2.py").write_text("import sys\n")
        
        cleaner = DepCleaner(tmppath)
        report = cleaner.scan()
        
        assert report.scanned_files == 2


def test_validate_project() -> None:
    """Test project validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\n")
        
        cleaner = DepCleaner(tmppath)
        validation = cleaner.validate_project()
        
        assert validation['valid'] is True
        assert 'files_found' in validation


def test_estimate_cleanup_impact() -> None:
    """Test cleanup impact estimation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nimport sys\nprint('hello')\n")
        
        cleaner = DepCleaner(tmppath)
        impact = cleaner.estimate_cleanup_impact()
        
        assert 'total_files' in impact
        assert 'unused_imports' in impact
        assert 'cleanup_percentage' in impact


def test_analyze_single_file() -> None:
    """Test analyzing a single file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text("import os\nimport sys\nprint(os.name)\n")
        
        cleaner = DepCleaner(tmppath)
        results = cleaner.analyze_file(str(test_file))
        
        assert 'all_imports' in results
        assert 'used_imports' in results
        assert 'unused_imports' in results
        assert 'os' in results['all_imports']
        assert 'sys' in results['unused_imports']


def test_get_dependency_graph() -> None:
    """Test dependency graph generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import json\ndata = json.dumps({})\n")
        
        cleaner = DepCleaner(tmppath)
        graph = cleaner.get_dependency_graph()
        
        assert isinstance(graph, dict)
        # json might be filtered as stdlib, so just check structure
        assert all(isinstance(v, set) for v in graph.values())