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

    def __init__(
        self,
        project_path: str = ".",
        max_workers: int = 4,
        exclude_dirs: Optional[Set[str]] = None
    ) -> None:
        """Initialize DepCleaner.
        
        Args:
            project_path: Root path of the project to analyze
            max_workers: Maximum number of worker threads for parallel processing
            exclude_dirs: Additional directories to exclude from scanning
        """
        self.project_path = Path(project_path).resolve()
        
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {self.project_path}")
        
        if not self.project_path.is_dir():
            raise ValueError(f"Project path is not a directory: {self.project_path}")
        
        self.scanner = Scanner(self.project_path, max_workers=max_workers)
        self.fixer = Fixer(self.project_path)
        self.exclude_dirs = exclude_dirs or set()
        
        logger.info(f"Initialized DepCleaner for {self.project_path}")
        logger.debug(f"Using {max_workers} worker threads")

    def scan(self, force_rescan: bool = False) -> Report:
        """Scan project for unused dependencies.
        
        Args:
            force_rescan: Force a new scan even if results are cached
            
        Returns:
            Report object with scan results
        """
        logger.info("Starting dependency scan")
        
        try:
            report = self.scanner.scan()
            logger.info(f"Scan complete: {report.scanned_files} files analyzed")
            return report
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            raise

    def fix(
        self,
        backup: bool = True,
        dry_run: bool = False,
        file_pattern: Optional[str] = None
    ) -> Dict[str, int]:
        """Fix unused dependencies by removing them.
        
        Args:
            backup: Create backup files before modification
            dry_run: Preview changes without applying them
            file_pattern: Optional glob pattern to filter files
            
        Returns:
            Dictionary with fix statistics
        """
        logger.info(f"Starting fix (backup={backup}, dry_run={dry_run})")
        
        try:
            report = self.scan()
            
            # Filter report if pattern provided
            if file_pattern:
                report = self._filter_report(report, file_pattern)
            
            stats = self.fixer.fix(report, backup=backup, dry_run=dry_run)
            
            logger.info(
                f"Fix complete: {stats['files_modified']} files modified, "
                f"{stats['imports_removed']} imports removed"
            )
            
            return stats
        except Exception as e:
            logger.error(f"Fix failed: {e}")
            raise

    def _filter_report(self, report: Report, pattern: str) -> Report:
        """Filter report to only include files matching pattern.
        
        Args:
            report: Original report
            pattern: Glob pattern
            
        Returns:
            Filtered report
        """
        from fnmatch import fnmatch
        
        filtered_imports = {
            path: imports
            for path, imports in report.all_imports.items()
            if fnmatch(str(path), pattern)
        }
        
        filtered_used = {
            path: imports
            for path, imports in report.used_imports.items()
            if path in filtered_imports
        }
        
        return Report(
            project_path=report.project_path,
            scanned_files=len(filtered_imports),
            all_imports=filtered_imports,
            used_imports=filtered_used,
            declared_deps=report.declared_deps,
            used_deps=report.used_deps
        )

    def analyze_file(self, file_path: str) -> Dict[str, Set[str]]:
        """Analyze a single file for imports.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with 'all_imports' and 'used_imports'
        """
        path = Path(file_path).resolve()
        
        if not path.exists():
            raise ValueError(f"File does not exist: {path}")
        
        if not path.is_file() or path.suffix != ".py":
            raise ValueError(f"Not a Python file: {path}")
        
        all_imports = self.scanner._analyze_single_file(path)
        used_imports = self.scanner._detect_usage_single_file(path)
        
        return {
            "all_imports": all_imports,
            "used_imports": used_imports,
            "unused_imports": all_imports - used_imports
        }

    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """Get a graph of which files use which dependencies.
        
        Returns:
            Dictionary mapping dependency names to sets of files using them
        """
        report = self.scan()
        dep_graph: Dict[str, Set[str]] = {}
        
        for file_path, imports in report.used_imports.items():
            rel_path = str(file_path.relative_to(self.project_path))
            for imp in imports:
                if imp not in dep_graph:
                    dep_graph[imp] = set()
                dep_graph[imp].add(rel_path)
        
        return dep_graph

    def find_duplicate_dependencies(self) -> Dict[str, List[str]]:
        """Find dependencies that might be duplicates (similar names).
        
        Returns:
            Dictionary mapping canonical names to lists of similar names
        """
        report = self.scan()
        duplicates: Dict[str, List[str]] = {}
        
        all_deps = list(report.declared_deps)
        
        for i, dep1 in enumerate(all_deps):
            similar = [dep1]
            for dep2 in all_deps[i+1:]:
                # Check for similar names (e.g., 'package' vs 'package-name')
                if (dep1.replace("_", "").replace("-", "") ==
                    dep2.replace("_", "").replace("-", "")):
                    similar.append(dep2)
            
            if len(similar) > 1:
                canonical = min(similar, key=len)
                duplicates[canonical] = similar
        
        return duplicates

    def estimate_cleanup_impact(self) -> Dict[str, any]:
        """Estimate the impact of running cleanup.
        
        Returns:
            Dictionary with impact estimates
        """
        report = self.scan()
        unused_imports = report.get_unused_imports()
        unused_packages = report.get_unused_packages()
        
        total_imports = sum(len(imports) for imports in report.all_imports.values())
        unused_import_count = sum(len(imports) for imports in unused_imports.values())
        
        return {
            "total_files": report.scanned_files,
            "files_with_unused": len(unused_imports),
            "total_imports": total_imports,
            "unused_imports": unused_import_count,
            "unused_packages": len(unused_packages),
            "cleanup_percentage": round(
                (unused_import_count / total_imports * 100) if total_imports > 0 else 0,
                2
            ),
            "affected_files": [
                str(path.relative_to(self.project_path))
                for path in unused_imports.keys()
            ]
        }

    def validate_project(self) -> Dict[str, any]:
        """Validate project structure and configuration.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check for dependency files
        has_requirements = (self.project_path / "requirements.txt").exists()
        has_pyproject = (self.project_path / "pyproject.toml").exists()
        has_setup = (self.project_path / "setup.py").exists()
        
        if not (has_requirements or has_pyproject or has_setup):
            results["warnings"].append(
                "No dependency file found (requirements.txt, pyproject.toml, or setup.py)"
            )
        
        # Check for Python files
        python_files = list(self.project_path.rglob("*.py"))
        if not python_files:
            results["errors"].append("No Python files found in project")
            results["valid"] = False
        
        # Check for common issues
        if (self.project_path / "venv").exists():
            results["warnings"].append(
                "Virtual environment directory 'venv' found in project root"
            )
        
        results["files_found"] = {
            "requirements.txt": has_requirements,
            "pyproject.toml": has_pyproject,
            "setup.py": has_setup,
            "python_files": len(python_files)
        }
        
        return results