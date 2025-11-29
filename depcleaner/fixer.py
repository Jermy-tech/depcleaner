"""Enhanced dependency fixer module.

MIT License - Copyright (c) 2024 DepCleaner
For feature requests or contributions, visit: https://github.com/Jermy-tech/depcleaner
"""
import ast
import logging
import shutil
from pathlib import Path
from typing import Dict, Set, List, Optional
from datetime import datetime
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
        self.backup_dir = project_path / ".depcleaner_backups"

    def fix(
        self, 
        report: Report, 
        backup: bool = True, 
        dry_run: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, int]:
        """Fix unused dependencies with progress tracking.
        
        Args:
            report: Scan report with unused dependencies
            backup: Create backup files
            dry_run: Preview changes without applying
            progress_callback: Optional callback(current, total, message)
            
        Returns:
            Statistics dictionary
        """
        stats = {
            "files_modified": 0,
            "imports_removed": 0,
            "backups_created": 0,
            "files_with_errors": 0
        }
        
        if backup and not dry_run:
            self._setup_backup_dir()
        
        # Get files with unused imports
        unused_by_file = {
            file_path: all_imports - report.used_imports.get(file_path, set())
            for file_path, all_imports in report.all_imports.items()
        }
        
        files_to_process = [
            (file_path, unused) 
            for file_path, unused in unused_by_file.items() 
            if unused
        ]
        
        total_files = len(files_to_process)
        
        for idx, (file_path, unused) in enumerate(files_to_process, 1):
            if progress_callback:
                progress_callback(
                    idx, 
                    total_files, 
                    f"Processing {file_path.relative_to(self.project_path)}"
                )
            
            logger.info(
                f"Processing {file_path.relative_to(self.project_path)}: "
                f"{len(unused)} unused imports"
            )
            logger.debug(f"Unused imports: {', '.join(sorted(unused))}")
            
            if dry_run:
                print(f"\n{file_path.relative_to(self.project_path)}:")
                print(f"  Would remove: {', '.join(sorted(unused))}")
                stats["files_modified"] += 1
                stats["imports_removed"] += len(unused)
            else:
                try:
                    if backup:
                        self._create_backup(file_path)
                        stats["backups_created"] += 1
                    
                    removed_count = self._remove_unused_imports(file_path, unused)
                    stats["files_modified"] += 1
                    stats["imports_removed"] += removed_count
                    
                except Exception as e:
                    logger.error(f"Failed to fix {file_path}: {e}")
                    stats["files_with_errors"] += 1
        
        if backup and not dry_run and stats["backups_created"] > 0:
            logger.info(f"Backups saved to: {self.backup_dir}")
        
        return stats

    def _setup_backup_dir(self) -> None:
        """Setup backup directory with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.project_path / ".depcleaner_backups" / timestamp
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Backup directory: {self.backup_dir}")

    def _create_backup(self, file_path: Path) -> None:
        """Create backup of file in backup directory.
        
        Args:
            file_path: Path to file to backup
        """
        try:
            # Preserve directory structure in backup
            relative_path = file_path.relative_to(self.project_path)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")

    def _remove_unused_imports(self, file_path: Path, unused: Set[str]) -> int:
        """Remove unused imports from file using AST-based approach.
        
        Args:
            file_path: Path to file to modify
            unused: Set of unused import names
            
        Returns:
            Number of imports actually removed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines(keepends=True)
            
            tree = ast.parse(content, filename=str(file_path))
            
            # Find line numbers of import statements to remove
            lines_to_remove = set()
            removed_count = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Check if all names in this import are unused
                    names_to_keep = []
                    for alias in node.names:
                        top_level = alias.name.split(".")[0]
                        if top_level not in unused:
                            names_to_keep.append(alias)
                        else:
                            removed_count += 1
                    
                    # If no names to keep, mark entire line for removal
                    if not names_to_keep:
                        lines_to_remove.add(node.lineno - 1)  # 0-indexed
                    # If some names to keep, rewrite the line
                    elif len(names_to_keep) < len(node.names):
                        # Reconstruct import statement
                        new_import = "import " + ", ".join(
                            f"{alias.name} as {alias.asname}" if alias.asname 
                            else alias.name
                            for alias in names_to_keep
                        )
                        lines[node.lineno - 1] = new_import + "\n"
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        top_level = node.module.split(".")[0]
                        if top_level in unused:
                            lines_to_remove.add(node.lineno - 1)
                            removed_count += 1
            
            # Remove marked lines
            new_lines = [
                line for i, line in enumerate(lines)
                if i not in lines_to_remove
            ]
            
            # Remove consecutive blank lines left after import removal
            cleaned_lines = self._clean_blank_lines(new_lines)
            
            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(cleaned_lines)
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to remove imports from {file_path}: {e}")
            raise

    def _clean_blank_lines(self, lines: List[str]) -> List[str]:
        """Remove excessive blank lines.
        
        Args:
            lines: List of lines
            
        Returns:
            Cleaned list of lines
        """
        cleaned = []
        blank_count = 0
        
        for line in lines:
            if line.strip():
                cleaned.append(line)
                blank_count = 0
            else:
                blank_count += 1
                # Allow max 2 consecutive blank lines
                if blank_count <= 2:
                    cleaned.append(line)
        
        return cleaned

    def update_requirements(
        self, 
        report: Report, 
        dry_run: bool = False
    ) -> Dict[str, any]:
        """Update requirements.txt to remove unused packages.
        
        Args:
            report: Scan report
            dry_run: Preview changes without applying
            
        Returns:
            Statistics dictionary
        """
        stats = {"packages_removed": [], "file_updated": False}
        
        unused_packages = report.get_unused_packages()
        
        if not unused_packages:
            logger.info("No unused packages to remove from requirements")
            return stats
        
        req_file = self.project_path / "requirements.txt"
        
        if not req_file.exists():
            logger.warning("requirements.txt not found")
            return stats
        
        try:
            with open(req_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            new_lines = []
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    new_lines.append(line)
                    continue
                
                # Extract package name
                pkg_name = stripped.split("==")[0].split(">=")[0].split("<=")[0].strip()
                normalized = pkg_name.lower().replace("-", "_")
                
                if normalized in unused_packages:
                    if dry_run:
                        print(f"Would remove from requirements.txt: {pkg_name}")
                    stats["packages_removed"].append(pkg_name)
                    logger.info(f"Removing {pkg_name} from requirements.txt")
                else:
                    new_lines.append(line)
            
            if not dry_run and stats["packages_removed"]:
                # Backup original
                backup_path = req_file.with_suffix(".txt.bak")
                shutil.copy2(req_file, backup_path)
                
                with open(req_file, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                
                stats["file_updated"] = True
                logger.info(f"Updated requirements.txt (backup: {backup_path})")
        
        except Exception as e:
            logger.error(f"Failed to update requirements.txt: {e}")
        
        return stats