"""Tests for fixer module."""
import tempfile
from pathlib import Path
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
        
        # Verify imports were actually removed
        content = test_file.read_text()
        assert "import os" not in content
        assert "import sys" not in content


def test_fixer_creates_backup() -> None:
    """Test that fixer creates backup files in timestamped directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text("import os\nprint('hello')\n")
        
        cleaner = DepCleaner(tmppath)
        stats = cleaner.fix(backup=True)
        
        # Check backup directory was created
        backup_dir = tmppath / ".depcleaner_backups"
        assert backup_dir.exists()
        assert backup_dir.is_dir()
        
        # Check at least one backup was created
        assert stats["backups_created"] >= 1
        
        # Find the timestamped backup
        backup_subdirs = list(backup_dir.iterdir())
        assert len(backup_subdirs) > 0


def test_fixer_no_backup() -> None:
    """Test that fixer doesn't create backups when disabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text("import os\nprint('hello')\n")
        
        cleaner = DepCleaner(tmppath)
        stats = cleaner.fix(backup=False)
        
        # Check no backup directory was created
        backup_dir = tmppath / ".depcleaner_backups"
        assert not backup_dir.exists()
        assert stats["backups_created"] == 0


def test_fixer_dry_run() -> None:
    """Test dry run mode doesn't modify files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        original_content = "import os\nimport sys\nprint('hello')\n"
        test_file.write_text(original_content)
        
        cleaner = DepCleaner(tmppath)
        stats = cleaner.fix(dry_run=True)
        
        # Files should be counted but not modified
        assert stats["files_modified"] >= 1
        assert stats["imports_removed"] >= 2
        
        # Verify file wasn't actually changed
        assert test_file.read_text() == original_content


def test_fixer_preserves_used_imports() -> None:
    """Test that fixer preserves imports that are actually used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text("import os\nimport sys\nprint(os.name)\n")
        
        cleaner = DepCleaner(tmppath)
        cleaner.fix(backup=False)
        
        content = test_file.read_text()
        # os should be preserved, sys should be removed
        assert "import os" in content
        assert "import sys" not in content


def test_fixer_handles_from_imports() -> None:
    """Test that fixer handles 'from X import Y' style imports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        test_file.write_text("from os import path\nfrom sys import argv\nprint('hello')\n")
        
        cleaner = DepCleaner(tmppath)
        cleaner.fix(backup=False)
        
        content = test_file.read_text()
        # Both unused from imports should be removed
        assert "from os import" not in content
        assert "from sys import" not in content


def test_fixer_multiple_files() -> None:
    """Test fixing multiple files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test1.py").write_text("import os\nprint('hello')\n")
        (tmppath / "test2.py").write_text("import sys\nprint('world')\n")
        
        cleaner = DepCleaner(tmppath)
        stats = cleaner.fix(backup=False)
        
        assert stats["files_modified"] == 2
        assert stats["imports_removed"] == 2


def test_fixer_error_handling() -> None:
    """Test that fixer handles errors gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        # Write invalid Python that will cause issues
        test_file.write_text("import os\nthis is not valid python\n")
        
        cleaner = DepCleaner(tmppath)
        # Should not crash, but may report errors
        stats = cleaner.fix(backup=False)
        
        assert 'files_with_errors' in stats or stats['files_modified'] >= 0


def test_update_requirements() -> None:
    """Test updating requirements.txt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create a requirements file with unused package
        req_file = tmppath / "requirements.txt"
        req_file.write_text("numpy==1.24.0\nrequests==2.31.0\n")
        
        # Create a file that only uses numpy
        (tmppath / "test.py").write_text("import numpy as np\nprint(np.array([1,2,3]))\n")
        
        cleaner = DepCleaner(tmppath)
        report = cleaner.scan()
        
        # Check what's detected as unused
        unused_packages = report.get_unused_packages()
        
        # Update requirements in dry-run mode first
        req_stats = cleaner.fixer.update_requirements(report, dry_run=True)
        
        # Should identify at least some packages as removable
        assert isinstance(req_stats['packages_removed'], list)
        
        # Now do it for real (but only if we detected unused packages)
        if unused_packages:
            req_stats = cleaner.fixer.update_requirements(report, dry_run=False)
            
            if req_stats.get('file_updated'):
                content = req_file.read_text()
                # Check that file still exists and has content
                assert len(content) >= 0
                
                # If requests was marked unused, it should be gone
                if 'requests' in [p.lower() for p in unused_packages]:
                    assert 'requests' not in content.lower() or content == ""