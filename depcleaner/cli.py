"""Command-line interface for DepCleaner."""
import argparse
import logging
import sys
from pathlib import Path
from depcleaner import DepCleaner

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging
        quiet: Suppress all but error messages
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add new handler with proper formatting
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def cmd_scan(args: argparse.Namespace) -> int:
    """Execute scan command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    try:
        cleaner = DepCleaner(args.path)
        report = cleaner.scan()
        
        if args.json:
            print(report.to_json())
            return 0
        
        if args.format == "detailed":
            print(report.to_detailed_string())
        else:
            print(report)
        
        unused_imports = report.get_unused_imports()
        unused_packages = report.get_unused_packages()
        
        if unused_imports or unused_packages:
            if not args.quiet:
                print("\n⚠️  Unused dependencies detected!")
            return 1
        
        if not args.quiet:
            print("\n✓ No unused dependencies found!")
        return 0
    
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        if args.verbose:
            raise
        return 2


def cmd_fix(args: argparse.Namespace) -> int:
    """Execute fix command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    try:
        cleaner = DepCleaner(args.path)
        
        if args.dry_run:
            print("DRY RUN - No files will be modified\n")
        
        stats = cleaner.fix(backup=args.backup, dry_run=args.dry_run)
        
        if not args.quiet:
            print("\n" + "="*50)
            print("Fix Summary")
            print("="*50)
            print(f"Files modified: {stats['files_modified']}")
            print(f"Imports removed: {stats['imports_removed']}")
            
            if stats.get('files_with_errors', 0) > 0:
                print(f"⚠️  Files with errors: {stats['files_with_errors']}")
            
            if args.backup and not args.dry_run:
                print(f"Backups created: {stats['backups_created']}")
            
            if args.dry_run:
                print("\n💡 Run without --dry-run to apply changes")
        
        # Update requirements if requested
        if args.update_requirements and not args.dry_run:
            report = cleaner.scan()
            req_stats = cleaner.fixer.update_requirements(report, dry_run=args.dry_run)
            
            if req_stats["file_updated"]:
                print(f"\nUpdated requirements.txt:")
                for pkg in req_stats["packages_removed"]:
                    print(f"  - Removed: {pkg}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Fix failed: {e}")
        if args.verbose:
            raise
        return 2


def cmd_check(args: argparse.Namespace) -> int:
    """Execute check command (like scan but with different output).
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    try:
        cleaner = DepCleaner(args.path)
        report = cleaner.scan()
        
        unused_imports = report.get_unused_imports()
        unused_packages = report.get_unused_packages()
        
        if not unused_imports and not unused_packages:
            if not args.quiet:
                print("✓ All dependencies are being used")
            return 0
        
        # Show results in CI-friendly format
        if unused_imports:
            print("Unused imports found:")
            for file_path, imports in unused_imports.items():
                rel_path = file_path.relative_to(report.project_path)
                print(f"  {rel_path}:")
                for imp in sorted(imports):
                    print(f"    - {imp}")
        
        if unused_packages:
            print("\nUnused packages:")
            for pkg in sorted(unused_packages):
                print(f"  - {pkg}")
        
        return 1
    
    except Exception as e:
        logger.error(f"Check failed: {e}")
        if args.verbose:
            raise
        return 2


def cmd_stats(args: argparse.Namespace) -> int:
    """Show project statistics.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    try:
        cleaner = DepCleaner(args.path)
        report = cleaner.scan()
        
        print("Project Statistics")
        print("="*50)
        print(f"Python files: {report.scanned_files}")
        print(f"Total imports: {sum(len(imports) for imports in report.all_imports.values())}")
        print(f"Unique packages imported: {len(report.used_deps)}")
        print(f"Declared dependencies: {len(report.declared_deps)}")
        
        unused_imports = report.get_unused_imports()
        unused_packages = report.get_unused_packages()
        
        print(f"\nUnused imports: {sum(len(imports) for imports in unused_imports.values())}")
        print(f"Unused packages: {len(unused_packages)}")
        
        if args.show_all:
            print("\n" + "="*50)
            print("All Declared Dependencies:")
            for dep in sorted(report.declared_deps):
                status = "✓" if dep in report.used_deps else "✗"
                print(f"  {status} {dep}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Stats command failed: {e}")
        if args.verbose:
            raise
        return 2


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DepCleaner - Python dependency cleanup tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  depcleaner scan                    # Scan current directory
  depcleaner scan --path /my/project # Scan specific directory
  depcleaner fix --dry-run           # Preview changes
  depcleaner fix --no-backup         # Fix without backups
  depcleaner check                   # Quick check (CI-friendly)
  depcleaner stats --show-all        # Show detailed statistics
        """
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress non-error output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan for unused dependencies"
    )
    scan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project path to scan (default: current directory)"
    )
    scan_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    scan_parser.add_argument(
        "--format",
        choices=["summary", "detailed"],
        default="summary",
        help="Output format (default: summary)"
    )
    
    # Fix command
    fix_parser = subparsers.add_parser(
        "fix",
        help="Fix unused dependencies"
    )
    fix_parser.add_argument(
        "path",
        nargs="?",
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
    fix_parser.add_argument(
        "--update-requirements",
        action="store_true",
        help="Also update requirements.txt to remove unused packages"
    )
    
    # Check command (CI-friendly)
    check_parser = subparsers.add_parser(
        "check",
        help="Check for unused dependencies (CI-friendly)"
    )
    check_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project path to check (default: current directory)"
    )
    
    # Stats command
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show project statistics"
    )
    stats_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project path to analyze (default: current directory)"
    )
    stats_parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all dependencies with usage status"
    )
    
    args = parser.parse_args()
    
    # Setup logging early, before any commands run
    verbose = getattr(args, 'verbose', False)
    quiet = getattr(args, 'quiet', False)
    setup_logging(verbose, quiet)
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "scan":
            sys.exit(cmd_scan(args))
        elif args.command == "fix":
            sys.exit(cmd_fix(args))
        elif args.command == "check":
            sys.exit(cmd_check(args))
        elif args.command == "stats":
            sys.exit(cmd_stats(args))
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()