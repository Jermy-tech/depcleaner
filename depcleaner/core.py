"""Core DepCleaner functionality."""
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
from depcleaner.scanner import Scanner
from depcleaner.fixer import Fixer
from depcleaner.report import Report

logger = logging.getLogger(__name__)


class DepCleaner:
    """Main class for dependency cleaning operations."""

    def __init__(self, project_path: str = ".") -> None:
        """Initialize DepCleaner.
        
        Args:
            project_path: Root path of the project to analyze
        """
        self.project_path = Path(project_path).resolve()
        self.scanner = Scanner(self.project_path)
        self.fixer = Fixer(self.project_path)
        logger.info(f"Initialized DepCleaner for {self.project_path}")

    def scan(self) -> Report:
        """Scan project for unused dependencies.
        
        Returns:
            Report object with scan results
        """
        logger.info("Starting dependency scan")
        return self.scanner.scan()

    def fix(self, backup: bool = True, dry_run: bool = False) -> Dict[str, int]:
        """Fix unused dependencies by removing them.
        
        Args:
            backup: Create backup files before modification
            dry_run: Preview changes without applying them
            
        Returns:
            Dictionary with fix statistics
        """
        logger.info(f"Starting fix (backup={backup}, dry_run={dry_run})")
        report = self.scan()
        return self.fixer.fix(report, backup=backup, dry_run=dry_run)
