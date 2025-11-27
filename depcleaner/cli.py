"""Command-line interface for DepCleaner."""
import argparse
import logging
import sys
from pathlib import Path
from depcleaner import DepCleaner

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s"
    )


def cmd_scan(args: argparse.Namespace) -> int:
    """Execute scan command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    cleaner = DepCleaner(args.path)
    report = cleaner.scan()
    print(report)
    
    unused_imports = report.get_unused_imports()
    unused_packages = report.get_unused_packages()
    
    if unused_imports or unused_packages:
        return 1
    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    """Execute fix command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    cleaner = DepCleaner(args.path)
    stats = cleaner.fix(backup=args.backup, dry_run=args.dry_run)
    
    print(f"Files modified: {stats['files_modified']}")
    print(f"Imports removed: {stats['imports_removed']}")
    if args.backup:
        print(f"Backups created: {stats['backups_created']}")
    
    return 0


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DepCleaner - Python dependency cleanup tool"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    scan_parser = subparsers.add_parser("scan", help="Scan for unused dependencies")
    scan_parser.add_argument(
        "--path",
        default=".",
        help="Project path to scan (default: current directory)"
    )
    
    fix_parser = subparsers.add_parser("fix", help="Fix unused dependencies")
    fix_parser.add_argument(
        "--path",
        default=".",
        help="Project path to fix (default: current directory)"
    )
    fix_parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup files (default: True)"
    )
    fix_parser.add_argument(
        "--no-backup",
        action="store_false",
        dest="backup",
        help="Do not create backup files"
    )
    fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "scan":
            sys.exit(cmd_scan(args))
        elif args.command == "fix":
            sys.exit(cmd_fix(args))
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
