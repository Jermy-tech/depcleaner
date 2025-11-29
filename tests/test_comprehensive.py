"""Comprehensive tests for CLI module to improve coverage.

MIT License - Copyright (c) 2024 DepCleaner
For feature requests or contributions, visit: https://github.com/Jermy-tech/depcleaner
"""
import sys
import tempfile
import json
from pathlib import Path
from io import StringIO
import pytest
from unittest.mock import patch
from depcleaner.cli import (
    setup_logging, cmd_scan, cmd_fix, cmd_check, cmd_stats, main
)
import argparse


def test_setup_logging_verbose():
    """Test verbose logging setup."""
    setup_logging(verbose=True, quiet=False)
    import logging
    assert logging.getLogger().level == logging.DEBUG


def test_setup_logging_quiet():
    """Test quiet logging setup."""
    setup_logging(verbose=False, quiet=True)
    import logging
    assert logging.getLogger().level == logging.ERROR


def test_setup_logging_normal():
    """Test normal logging setup."""
    setup_logging(verbose=False, quiet=False)
    import logging
    assert logging.getLogger().level == logging.INFO


def test_cmd_scan_basic():
    """Test basic scan command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint(os.name)\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            json=False,
            format='summary',
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_scan(args)
        assert exit_code == 0


def test_cmd_scan_with_unused():
    """Test scan command with unused imports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nimport sys\nprint('hello')\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            json=False,
            format='summary',
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_scan(args)
        assert exit_code == 1  # Has unused deps


def test_cmd_scan_json_output():
    """Test scan command with JSON output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            json=True,
            format='summary',
            verbose=False,
            quiet=False
        )
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            exit_code = cmd_scan(args)
        
        output = captured_output.getvalue()
        # Should be valid JSON
        assert json.loads(output)
        assert exit_code == 0


def test_cmd_scan_detailed_format():
    """Test scan command with detailed format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint(os.name)\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            json=False,
            format='detailed',
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_scan(args)
        assert exit_code == 0


def test_cmd_scan_quiet_mode():
    """Test scan in quiet mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint(os.name)\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            json=False,
            format='summary',
            verbose=False,
            quiet=True
        )
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            exit_code = cmd_scan(args)
        
        # Should have minimal output
        assert exit_code == 0


def test_cmd_scan_error_handling():
    """Test scan error handling."""
    args = argparse.Namespace(
        path="/nonexistent/path",
        json=False,
        format='summary',
        verbose=False,
        quiet=False
    )
    
    exit_code = cmd_scan(args)
    assert exit_code == 2  # Error code


def test_cmd_fix_basic():
    """Test basic fix command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nimport sys\nprint('hello')\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            backup=False,
            dry_run=False,
            update_requirements=False,
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_fix(args)
        assert exit_code == 0


def test_cmd_fix_dry_run():
    """Test fix in dry-run mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.py"
        original = "import os\nimport sys\nprint('hello')\n"
        test_file.write_text(original)
        
        args = argparse.Namespace(
            path=str(tmppath),
            backup=True,
            dry_run=True,
            update_requirements=False,
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_fix(args)
        
        # File should not be modified
        assert test_file.read_text() == original
        assert exit_code == 0


def test_cmd_fix_with_backup():
    """Test fix with backup enabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nimport sys\nprint('hello')\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            backup=True,
            dry_run=False,
            update_requirements=False,
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_fix(args)
        
        # Backup directory should exist
        backup_dir = tmppath / ".depcleaner_backups"
        assert backup_dir.exists()
        assert exit_code == 0


def test_cmd_fix_update_requirements():
    """Test fix with requirements update."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import numpy as np\nprint(np.array([1]))\n")
        
        req_file = tmppath / "requirements.txt"
        req_file.write_text("numpy==1.24.0\nrequests==2.31.0\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            backup=False,
            dry_run=False,
            update_requirements=True,
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_fix(args)
        assert exit_code == 0


def test_cmd_fix_quiet_mode():
    """Test fix in quiet mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint('hello')\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            backup=False,
            dry_run=False,
            update_requirements=False,
            verbose=False,
            quiet=True
        )
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            exit_code = cmd_fix(args)
        
        assert exit_code == 0


def test_cmd_fix_error_handling():
    """Test fix error handling."""
    args = argparse.Namespace(
        path="/nonexistent/path",
        backup=False,
        dry_run=False,
        update_requirements=False,
        verbose=False,
        quiet=False
    )
    
    exit_code = cmd_fix(args)
    assert exit_code == 2


def test_cmd_check_no_unused():
    """Test check command with no unused deps."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint(os.name)\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_check(args)
        assert exit_code == 0


def test_cmd_check_with_unused():
    """Test check command with unused deps."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nimport sys\nprint('hello')\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_check(args)
        assert exit_code == 1  # Has unused


def test_cmd_check_quiet():
    """Test check in quiet mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint(os.name)\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            verbose=False,
            quiet=True
        )
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            exit_code = cmd_check(args)
        
        assert exit_code == 0


def test_cmd_check_error_handling():
    """Test check error handling."""
    args = argparse.Namespace(
        path="/nonexistent/path",
        verbose=False,
        quiet=False
    )
    
    exit_code = cmd_check(args)
    assert exit_code == 2


def test_cmd_stats_basic():
    """Test basic stats command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint(os.name)\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            show_all=False,
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_stats(args)
        assert exit_code == 0


def test_cmd_stats_show_all():
    """Test stats with show_all flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint(os.name)\n")
        
        req_file = tmppath / "requirements.txt"
        req_file.write_text("requests==2.31.0\n")
        
        args = argparse.Namespace(
            path=str(tmppath),
            show_all=True,
            verbose=False,
            quiet=False
        )
        
        exit_code = cmd_stats(args)
        assert exit_code == 0


def test_cmd_stats_error_handling():
    """Test stats error handling."""
    args = argparse.Namespace(
        path="/nonexistent/path",
        show_all=False,
        verbose=False,
        quiet=False
    )
    
    exit_code = cmd_stats(args)
    assert exit_code == 2


def test_main_no_command():
    """Test main with no command."""
    with patch('sys.argv', ['depcleaner']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


def test_main_scan_command():
    """Test main with scan command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint(os.name)\n")
        
        with patch('sys.argv', ['depcleaner', 'scan', str(tmppath)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_main_fix_command():
    """Test main with fix command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint('hello')\n")
        
        with patch('sys.argv', ['depcleaner', 'fix', str(tmppath), '--no-backup']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_main_check_command():
    """Test main with check command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\nprint(os.name)\n")
        
        with patch('sys.argv', ['depcleaner', 'check', str(tmppath)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_main_stats_command():
    """Test main with stats command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\n")
        
        with patch('sys.argv', ['depcleaner', 'stats', str(tmppath)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_main_keyboard_interrupt():
    """Test main with keyboard interrupt."""
    with patch('sys.argv', ['depcleaner', 'scan', '.']):
        with patch('depcleaner.cli.cmd_scan', side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 130


def test_main_verbose_flag():
    """Test main with verbose flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\n")
        
        with patch('sys.argv', ['depcleaner', '-v', 'scan', str(tmppath)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1


def test_main_quiet_flag():
    """Test main with quiet flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test.py").write_text("import os\n")
        
        with patch('sys.argv', ['depcleaner', '-q', 'scan', str(tmppath)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1


def test_main_help():
    """Test main with help flag."""
    with patch('sys.argv', ['depcleaner', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_main_scan_help():
    """Test scan subcommand help."""
    with patch('sys.argv', ['depcleaner', 'scan', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0