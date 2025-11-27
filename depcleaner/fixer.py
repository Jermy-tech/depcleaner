"""Dependency fixer module."""
import ast
import logging
import shutil
from pathlib import Path
from typing import Dict, Set
from depcleaner.report import Report

logger = logging.getLogger(__name__)


class Fixer:
    """Fixes dependency issues by removing unused imports."""

    def __init__(self, project_path: Path) -> None:
        """Initialize Fixer.
        
        Args:
            project_path: Root path of the project
        """
        self.project_path = project_path

    def fix(self, report: Report, backup: bool = True, dry_run: bool = False) -> Dict[str, int]:
        """Fix unused dependencies.
        
        Args:
            report: Scan report with unused dependencies
            backup: Create backup files
            dry_run: Preview changes without applying
            
        Returns:
            Statistics dictionary
        """
        stats = {"files_modified": 0, "imports_removed": 0, "backups_created": 0}
        
        for file_path, all_imports in report.all_imports.items():
            used_imports = report.used_imports.get(file_path, set())
            unused = all_imports - used_imports
            
            if unused:
                logger.info(f"Removing {len(unused)} unused imports from {file_path}")
                
                if not dry_run:
                    if backup:
                        self._create_backup(file_path)
                        stats["backups_created"] += 1
                    
                    self._remove_unused_imports(file_path, unused)
                    stats["files_modified"] += 1
                    stats["imports_removed"] += len(unused)
        
        return stats

    def _create_backup(self, file_path: Path) -> None:
        """Create backup of file.
        
        Args:
            file_path: Path to file to backup
        """
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Created backup: {backup_path}")

    def _remove_unused_imports(self, file_path: Path, unused: Set[str]) -> None:
        """Remove unused imports from file.
        
        Args:
            file_path: Path to file to modify
            unused: Set of unused import names
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            with open(file_path, "w", encoding="utf-8") as f:
                for line in lines:
                    should_keep = True
                    for unused_name in unused:
                        if f"import {unused_name}" in line or f"from {unused_name}" in line:
                            if line.strip().startswith(("import ", "from ")):
                                should_keep = False
                                break
                    
                    if should_keep:
                        f.write(line)
        except Exception as e:
            logger.error(f"Failed to fix {file_path}: {e}")
