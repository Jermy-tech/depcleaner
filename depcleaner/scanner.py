"""Dependency scanner module."""
import ast
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
from depcleaner.report import Report

logger = logging.getLogger(__name__)


class Scanner:
    """Scans Python projects for dependency usage."""

    def __init__(self, project_path: Path) -> None:
        """Initialize Scanner.
        
        Args:
            project_path: Root path of the project
        """
        self.project_path = project_path
        self.python_files: List[Path] = []
        self.all_imports: Dict[Path, Set[str]] = {}
        self.used_imports: Dict[Path, Set[str]] = {}

    def scan(self) -> Report:
        """Perform full project scan.
        
        Returns:
            Report with scan results
        """
        self._discover_python_files()
        self._analyze_imports()
        self._detect_unused()
        declared_deps = self._get_declared_dependencies()
        used_deps = self._get_used_dependencies()
        
        return Report(
            project_path=self.project_path,
            scanned_files=len(self.python_files),
            all_imports=self.all_imports,
            used_imports=self.used_imports,
            declared_deps=declared_deps,
            used_deps=used_deps
        )

    def _discover_python_files(self) -> None:
        """Discover all Python files in project."""
        logger.info("Discovering Python files")
        self.python_files = []
        for path in self.project_path.rglob("*.py"):
            if self._should_include(path):
                self.python_files.append(path)
        logger.info(f"Found {len(self.python_files)} Python files")

    def _should_include(self, path: Path) -> bool:
        """Check if file should be included in analysis.
        
        Args:
            path: File path to check
            
        Returns:
            True if file should be included
        """
        exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs"}
        return not any(part in exclude_dirs for part in path.parts)

    def _analyze_imports(self) -> None:
        """Analyze imports in all Python files."""
        logger.info("Analyzing imports")
        for file_path in self.python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(file_path))
                imports = self._extract_imports(tree)
                self.all_imports[file_path] = imports
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
                self.all_imports[file_path] = set()

    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract import names from AST.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            Set of imported module names
        """
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
        return imports

    def _detect_unused(self) -> None:
        """Detect which imports are actually used."""
        logger.info("Detecting unused imports")
        for file_path in self.python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(file_path))
                
                imports = self.all_imports.get(file_path, set())
                used = self._find_used_names(tree, imports)
                self.used_imports[file_path] = used
            except Exception as e:
                logger.warning(f"Failed to analyze usage in {file_path}: {e}")
                self.used_imports[file_path] = self.all_imports.get(file_path, set())

    def _find_used_names(self, tree: ast.AST, imports: Set[str]) -> Set[str]:
        """Find which imported names are actually used.
        
        Args:
            tree: AST tree to analyze
            imports: Set of imported names
            
        Returns:
            Set of used import names
        """
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id in imports:
                    used.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id in imports:
                    used.add(node.value.id)
        return used

    def _get_declared_dependencies(self) -> Set[str]:
        """Get dependencies declared in requirements/pyproject.
        
        Returns:
            Set of declared package names
        """
        deps = set()
        
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                            deps.add(pkg.replace("-", "_").lower())
            except Exception as e:
                logger.warning(f"Failed to read requirements.txt: {e}")
        
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "r") as f:
                    content = f.read()
                    for line in content.split("\n"):
                        if "==" in line or ">=" in line:
                            parts = line.split('"')
                            if len(parts) >= 2:
                                pkg = parts[1].split("==")[0].split(">=")[0].strip()
                                deps.add(pkg.replace("-", "_").lower())
            except Exception as e:
                logger.warning(f"Failed to read pyproject.toml: {e}")
        
        return deps

    def _get_used_dependencies(self) -> Set[str]:
        """Get all dependencies used in code.
        
        Returns:
            Set of used package names
        """
        all_used = set()
        for used in self.used_imports.values():
            all_used.update(used)
        return {pkg.replace("-", "_").lower() for pkg in all_used}
