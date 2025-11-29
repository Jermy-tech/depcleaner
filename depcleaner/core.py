"""Core DepCleaner functionality - Enhanced version.

MIT License - Copyright (c) 2024 DepCleaner
For feature requests or contributions, visit: https://github.com/Jermy-tech/depcleaner
"""
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from depcleaner.scanner import Scanner
from depcleaner.fixer import Fixer
from depcleaner.report import Report

logger = logging.getLogger(__name__)


class DepCleaner:
    """Main class for dependency cleaning operations.
    
    Enhanced with caching, better error handling, and progress tracking.
    """

    def __init__(
        self,
        project_path: str = ".",
        max_workers: int = None,
        exclude_dirs: Optional[Set[str]] = None,
        cache_results: bool = True
    ) -> None:
        """Initialize DepCleaner.
        
        Args:
            project_path: Root path of the project to analyze
            max_workers: Maximum number of worker threads (None = auto-detect)
            exclude_dirs: Additional directories to exclude from scanning
            cache_results: Cache scan results for better performance
        """
        self.project_path = Path(project_path).resolve()
        
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {self.project_path}")
        
        if not self.project_path.is_dir():
            raise ValueError(f"Project path is not a directory: {self.project_path}")
        
        # Auto-detect optimal worker count if not specified
        if max_workers is None:
            import os
            max_workers = min(32, (os.cpu_count() or 1) + 4)
        
        self.scanner = Scanner(
            self.project_path, 
            max_workers=max_workers,
            exclude_dirs=exclude_dirs
        )
        self.fixer = Fixer(self.project_path)
        self.exclude_dirs = exclude_dirs or set()
        self.cache_results = cache_results
        self._cached_report: Optional[Report] = None
        
        logger.info(f"Initialized DepCleaner for {self.project_path}")
        logger.debug(f"Using {max_workers} worker threads")

    def scan(
        self, 
        force_rescan: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Report:
        """Scan project for unused dependencies.
        
        Args:
            force_rescan: Force a new scan even if results are cached
            progress_callback: Optional callback(current, total, message)
            
        Returns:
            Report object with scan results
        """
        # Return cached results if available
        if not force_rescan and self.cache_results and self._cached_report:
            logger.debug("Returning cached scan results")
            return self._cached_report
        
        logger.info("Starting dependency scan")
        
        try:
            report = self.scanner.scan(progress_callback=progress_callback)
            
            if self.cache_results:
                self._cached_report = report
            
            logger.info(f"Scan complete: {report.scanned_files} files analyzed")
            
            # Log summary
            unused_imports = report.get_unused_imports()
            unused_packages = report.get_unused_packages()
            if unused_imports or unused_packages:
                logger.warning(
                    f"Found {sum(len(i) for i in unused_imports.values())} "
                    f"unused imports in {len(unused_imports)} files, "
                    f"{len(unused_packages)} unused packages"
                )
            
            return report
        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            raise

    def fix(
        self,
        backup: bool = True,
        dry_run: bool = False,
        file_pattern: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, int]:
        """Fix unused dependencies by removing them.
        
        Args:
            backup: Create backup files before modification
            dry_run: Preview changes without applying them
            file_pattern: Optional glob pattern to filter files
            progress_callback: Optional callback(current, total, message)
            
        Returns:
            Dictionary with fix statistics
        """
        logger.info(f"Starting fix (backup={backup}, dry_run={dry_run})")
        
        try:
            report = self.scan()
            
            # Filter report if pattern provided
            if file_pattern:
                report = self._filter_report(report, file_pattern)
            
            stats = self.fixer.fix(
                report, 
                backup=backup, 
                dry_run=dry_run,
                progress_callback=progress_callback
            )
            
            # Clear cache after fixing
            if not dry_run:
                self._cached_report = None
            
            logger.info(
                f"Fix complete: {stats['files_modified']} files modified, "
                f"{stats['imports_removed']} imports removed"
            )
            
            return stats
        except Exception as e:
            logger.error(f"Fix failed: {e}", exc_info=True)
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
            Dictionary with 'all_imports', 'used_imports', 'unused_imports'
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
        seen = set()
        
        all_deps = list(report.declared_deps)
        
        for i, dep1 in enumerate(all_deps):
            if dep1 in seen:
                continue
                
            similar = [dep1]
            canonical_form = dep1.replace("_", "").replace("-", "").lower()
            
            for dep2 in all_deps[i+1:]:
                dep2_form = dep2.replace("_", "").replace("-", "").lower()
                if canonical_form == dep2_form:
                    similar.append(dep2)
                    seen.add(dep2)
            
            if len(similar) > 1:
                canonical = min(similar, key=len)
                duplicates[canonical] = similar
        
        return duplicates

    def estimate_cleanup_impact(self) -> Dict[str, any]:
        """Estimate the impact of running cleanup.
        
        Returns:
            Dictionary with impact estimates including size savings
        """
        report = self.scan()
        unused_imports = report.get_unused_imports()
        unused_packages = report.get_unused_packages()
        
        total_imports = sum(len(imports) for imports in report.all_imports.values())
        unused_import_count = sum(len(imports) for imports in unused_imports.values())
        
        # Estimate lines saved
        lines_saved = unused_import_count  # Approximate 1 line per import
        
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
            "estimated_lines_saved": lines_saved,
            "affected_files": [
                str(path.relative_to(self.project_path))
                for path in unused_imports.keys()
            ]
        }

    def validate_project(self) -> Dict[str, any]:
        """Validate project structure and configuration.
        
        Returns:
            Dictionary with validation results and recommendations
        """
        results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check for dependency files
        has_requirements = (self.project_path / "requirements.txt").exists()
        has_pyproject = (self.project_path / "pyproject.toml").exists()
        has_setup = (self.project_path / "setup.py").exists()
        
        if not (has_requirements or has_pyproject or has_setup):
            results["warnings"].append(
                "No dependency file found (requirements.txt, pyproject.toml, or setup.py)"
            )
            results["recommendations"].append(
                "Consider creating a requirements.txt or pyproject.toml to track dependencies"
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
            results["recommendations"].append(
                "Consider renaming to '.venv' to follow common conventions"
            )
        
        # Check for __pycache__ in git
        gitignore = self.project_path / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            if "__pycache__" not in content:
                results["recommendations"].append(
                    "Add __pycache__ to .gitignore to avoid committing cache files"
                )
        
        # Check project size
        if len(python_files) > 1000:
            results["recommendations"].append(
                f"Large project ({len(python_files)} files). Consider increasing max_workers for faster scanning."
            )
        
        results["files_found"] = {
            "requirements.txt": has_requirements,
            "pyproject.toml": has_pyproject,
            "setup.py": has_setup,
            "python_files": len(python_files)
        }
        
        return results

    def clear_cache(self) -> None:
        """Clear cached scan results."""
        self._cached_report = None
        logger.debug("Cleared scan cache")

    def export_config(self, output_path: str) -> None:
        """Export current configuration to a file.
        
        Args:
            output_path: Path to save configuration
        """
        import json
        
        config = {
            "project_path": str(self.project_path),
            "max_workers": self.scanner.max_workers,
            "exclude_dirs": list(self.exclude_dirs),
            "cache_results": self.cache_results
        }
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration exported to {output_path}")

    def get_health_score(self) -> Dict[str, any]:
        """Calculate a health score for the project's dependencies.
        
        Returns:
            Dictionary with health metrics and score (0-100)
        """
        report = self.scan()
        unused_imports = report.get_unused_imports()
        unused_packages = report.get_unused_packages()
        missing_packages = report.get_missing_packages()
        
        total_imports = sum(len(imports) for imports in report.all_imports.values())
        unused_count = sum(len(imports) for imports in unused_imports.values())
        
        # Calculate score (0-100)
        score = 100
        
        # Deduct for unused imports (max -30)
        if total_imports > 0:
            unused_ratio = unused_count / total_imports
            score -= min(30, unused_ratio * 50)
        
        # Deduct for unused packages (max -30)
        if len(report.declared_deps) > 0:
            unused_pkg_ratio = len(unused_packages) / len(report.declared_deps)
            score -= min(30, unused_pkg_ratio * 50)
        
        # Deduct for missing packages (max -40)
        score -= min(40, len(missing_packages) * 5)
        
        score = max(0, round(score))
        
        # Determine grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": score,
            "grade": grade,
            "metrics": {
                "unused_imports": unused_count,
                "unused_packages": len(unused_packages),
                "missing_packages": len(missing_packages),
                "total_imports": total_imports,
                "total_packages": len(report.declared_deps)
            },
            "recommendations": self._get_health_recommendations(
                unused_count, len(unused_packages), len(missing_packages)
            )
        }

    def _get_health_recommendations(
        self, 
        unused_imports: int, 
        unused_packages: int, 
        missing_packages: int
    ) -> List[str]:
        """Get health recommendations based on metrics."""
        recommendations = []
        
        if unused_imports > 0:
            recommendations.append(
                f"Remove {unused_imports} unused import(s) with 'depcleaner fix'"
            )
        
        if unused_packages > 0:
            recommendations.append(
                f"Remove {unused_packages} unused package(s) from dependencies"
            )
        
        if missing_packages > 0:
            recommendations.append(
                f"Add {missing_packages} missing package(s) to your dependency file"
            )
        
        if not recommendations:
            recommendations.append("Great job! Your dependencies are clean and healthy.")
        
        return recommendations