"""Dependency scanner module."""
import ast
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from depcleaner.report import Report
from depcleaner.package_mapper import get_mapper

logger = logging.getLogger(__name__)


class Scanner:
    """Scans Python projects for dependency usage."""

    def __init__(self, project_path: Path, max_workers: int = 4) -> None:
        """Initialize Scanner.
        
        Args:
            project_path: Root path of the project
            max_workers: Maximum number of worker threads for parallel processing
        """
        self.project_path = project_path
        self.max_workers = max_workers
        self.python_files: List[Path] = []
        self.all_imports: Dict[Path, Set[str]] = {}
        self.used_imports: Dict[Path, Set[str]] = {}
        self.declared_deps: Set[str] = set()
        self.stdlib_modules: Set[str] = self._load_stdlib_modules()

    def _load_stdlib_modules(self) -> Set[str]:
        """Load set of standard library module names.
        
        Returns:
            Set of stdlib module names
        """
        import sys
        stdlib = set(sys.builtin_module_names)
        
        # Add common stdlib modules not in builtin_module_names
        common_stdlib = {
            'os', 'sys', 'pathlib', 'typing', 'collections', 'itertools',
            'functools', 'operator', 'logging', 'json', 'csv', 'pickle',
            'datetime', 'time', 'random', 're', 'math', 'statistics',
            'argparse', 'configparser', 'shutil', 'tempfile', 'subprocess',
            'threading', 'multiprocessing', 'asyncio', 'unittest', 'pytest',
            'io', 'contextlib', 'abc', 'dataclasses', 'enum', 'warnings',
            'urllib', 'http', 'email', 'html', 'xml', 'hashlib', 'hmac',
            'secrets', 'uuid', 'base64', 'struct', 'socket', 'ssl',
        }
        stdlib.update(common_stdlib)
        return stdlib

    def scan(self) -> Report:
        """Perform full project scan.
        
        Returns:
            Report with scan results
        """
        self._discover_python_files()
        self._analyze_imports_parallel()
        self._detect_unused_parallel()
        self.declared_deps = self._get_declared_dependencies()
        used_deps = self._get_used_dependencies()
        
        return Report(
            project_path=self.project_path,
            scanned_files=len(self.python_files),
            all_imports=self.all_imports,
            used_imports=self.used_imports,
            declared_deps=self.declared_deps,
            used_deps=used_deps
        )

    def _discover_python_files(self) -> None:
        """Discover all Python files in project."""
        logger.info("Discovering Python files")
        self.python_files = []
        
        try:
            for path in self.project_path.rglob("*.py"):
                if self._should_include(path):
                    self.python_files.append(path)
        except PermissionError as e:
            logger.warning(f"Permission denied accessing some files: {e}")
        
        logger.info(f"Found {len(self.python_files)} Python files")

    def _should_include(self, path: Path) -> bool:
        """Check if file should be included in analysis.
        
        Args:
            path: File path to check
            
        Returns:
            True if file should be included
        """
        exclude_dirs = {
            ".venv", "venv", "env", ".env",
            "__pycache__", ".git", ".hg", ".svn",
            "build", "dist", ".eggs", "*.egg-info",
            "node_modules", ".tox", ".pytest_cache",
            ".mypy_cache", ".coverage", "htmlcov"
        }
        
        # Check if any part of the path matches exclude patterns
        path_parts = set(path.parts)
        if path_parts & exclude_dirs:
            return False
        
        # Exclude test files if desired (can be made configurable)
        # if path.stem.startswith('test_') or path.stem.endswith('_test'):
        #     return False
        
        return True

    def _analyze_imports_parallel(self) -> None:
        """Analyze imports in all Python files using parallel processing."""
        logger.info("Analyzing imports")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(self._analyze_single_file, path): path
                for path in self.python_files
            }
            
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    imports = future.result()
                    self.all_imports[path] = imports
                except Exception as e:
                    logger.warning(f"Failed to parse {path}: {e}")
                    self.all_imports[path] = set()

    def _analyze_single_file(self, file_path: Path) -> Set[str]:
        """Analyze imports in a single file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Set of imported module names
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
            return self._extract_imports(tree)
        except (UnicodeDecodeError, SyntaxError) as e:
            logger.warning(f"Cannot parse {file_path}: {e}")
            return set()

    def _analyze_imports(self) -> None:
        """Analyze imports in all Python files (non-parallel version)."""
        logger.info("Analyzing imports")
        for file_path in self.python_files:
            self.all_imports[file_path] = self._analyze_single_file(file_path)

    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract import names from AST.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            Set of imported module names (top-level packages only)
        """
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level = alias.name.split(".")[0]
                    imports.add(top_level)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_level = node.module.split(".")[0]
                    imports.add(top_level)
                elif node.level > 0:
                    # Relative import - skip for dependency analysis
                    continue
        return imports

    def _detect_unused_parallel(self) -> None:
        """Detect which imports are actually used (parallel version)."""
        logger.info("Detecting unused imports")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(self._detect_usage_single_file, path): path
                for path in self.python_files
            }
            
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    used = future.result()
                    self.used_imports[path] = used
                except Exception as e:
                    logger.warning(f"Failed to analyze usage in {path}: {e}")
                    # Assume all imports are used if we can't analyze
                    self.used_imports[path] = self.all_imports.get(path, set())

    def _detect_usage_single_file(self, file_path: Path) -> Set[str]:
        """Detect usage in a single file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Set of used import names
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
            
            imports = self.all_imports.get(file_path, set())
            return self._find_used_names(tree, imports)
        except (UnicodeDecodeError, SyntaxError) as e:
            logger.warning(f"Cannot analyze usage in {file_path}: {e}")
            return self.all_imports.get(file_path, set())

    def _detect_unused(self) -> None:
        """Detect which imports are actually used (non-parallel version)."""
        logger.info("Detecting unused imports")
        for file_path in self.python_files:
            self.used_imports[file_path] = self._detect_usage_single_file(file_path)

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
                # Handle chained attributes: module.submodule.function
                root = node
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name) and root.id in imports:
                    used.add(root.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                # Skip import statements themselves
                continue
        
        return used

    def _get_declared_dependencies(self) -> Set[str]:
        """Get dependencies declared in requirements/pyproject.
        
        Returns:
            Set of declared package names (normalized)
        """
        deps = set()
        
        # Parse requirements.txt
        deps.update(self._parse_requirements_txt())
        
        # Parse pyproject.toml
        deps.update(self._parse_pyproject_toml())
        
        # Parse setup.py
        deps.update(self._parse_setup_py())
        
        return deps

    def _parse_requirements_txt(self) -> Set[str]:
        """Parse requirements.txt file.
        
        Returns:
            Set of package names
        """
        deps = set()
        req_file = self.project_path / "requirements.txt"
        
        if req_file.exists():
            try:
                with open(req_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if not line or line.startswith("#"):
                            continue
                        # Skip -e and other flags
                        if line.startswith("-"):
                            continue
                        # Extract package name before version specifiers
                        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].split("[")[0].strip()
                        if pkg:
                            deps.add(self._normalize_package_name(pkg))
            except Exception as e:
                logger.warning(f"Failed to read requirements.txt: {e}")
        
        return deps

    def _parse_pyproject_toml(self) -> Set[str]:
        """Parse pyproject.toml file.
        
        Returns:
            Set of package names
        """
        deps = set()
        pyproject = self.project_path / "pyproject.toml"
        
        if pyproject.exists():
            try:
                # Try to use tomli/tomllib for proper TOML parsing
                try:
                    import tomllib
                except ImportError:
                    try:
                        import tomli as tomllib
                    except ImportError:
                        tomllib = None
                
                if tomllib:
                    with open(pyproject, "rb") as f:
                        data = tomllib.load(f)
                        # Handle poetry dependencies
                        if "tool" in data and "poetry" in data["tool"]:
                            poetry_deps = data["tool"]["poetry"].get("dependencies", {})
                            for pkg in poetry_deps:
                                if pkg != "python":
                                    deps.add(self._normalize_package_name(pkg))
                        
                        # Handle PEP 621 dependencies
                        if "project" in data:
                            proj_deps = data["project"].get("dependencies", [])
                            for dep in proj_deps:
                                pkg = dep.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].split("[")[0].strip()
                                if pkg:
                                    deps.add(self._normalize_package_name(pkg))
                else:
                    # Fallback to simple parsing
                    with open(pyproject, "r", encoding="utf-8") as f:
                        content = f.read()
                        in_deps_section = False
                        for line in content.split("\n"):
                            line = line.strip()
                            if line.startswith("[") and "dependencies" in line:
                                in_deps_section = True
                            elif line.startswith("["):
                                in_deps_section = False
                            elif in_deps_section and "=" in line:
                                parts = line.split("=")[0].strip().strip('"').strip("'")
                                if parts and parts != "python":
                                    deps.add(self._normalize_package_name(parts))
            except Exception as e:
                logger.warning(f"Failed to read pyproject.toml: {e}")
        
        return deps

    def _parse_setup_py(self) -> Set[str]:
        """Parse setup.py file.
        
        Returns:
            Set of package names
        """
        deps = set()
        setup_file = self.project_path / "setup.py"
        
        if setup_file.exists():
            try:
                with open(setup_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Name) and node.func.id == "setup":
                                for keyword in node.keywords:
                                    if keyword.arg in ("install_requires", "requires"):
                                        if isinstance(keyword.value, ast.List):
                                            for elt in keyword.value.elts:
                                                if isinstance(elt, ast.Constant):
                                                    pkg = str(elt.value).split("==")[0].split(">=")[0].split("<=")[0].strip()
                                                    if pkg:
                                                        deps.add(self._normalize_package_name(pkg))
            except Exception as e:
                logger.warning(f"Failed to parse setup.py: {e}")
        
        return deps

    def _normalize_package_name(self, name: str) -> str:
        """Normalize package name for comparison.
        
        Args:
            name: Package name
            
        Returns:
            Normalized package name
        """
        # PEP 503 normalization
        return name.lower().replace("-", "_").replace(".", "_")

    def _get_used_dependencies(self) -> Set[str]:
        """Get all dependencies used in code.
        
        Returns:
            Set of used package names (excluding stdlib)
        """
        all_used_imports = set()
        for used in self.used_imports.values():
            all_used_imports.update(used)
        
        # Filter out standard library modules
        external_imports = {
            pkg for pkg in all_used_imports
            if pkg.lower() not in self.stdlib_modules
        }
        
        # Map import names to package names using declared packages
        mapper = get_mapper()
        used_packages = set()
        
        for import_name in external_imports:
            # Try to match against declared packages
            matched = mapper.match_import_to_package(import_name, self.declared_deps)
            if matched:
                used_packages.add(matched)
            else:
                # No match found, add normalized import name as fallback
                used_packages.add(self._normalize_package_name(import_name))
        
        return used_packages
    
    def get_import_to_package_mapping(self) -> Dict[str, str]:
        """Get mapping of import names to their package names.
        
        Returns:
            Dictionary mapping import names to package names
        """
        mapper = get_mapper()
        mapping = {}
        
        all_imports = set()
        for imports in self.all_imports.values():
            all_imports.update(imports)
        
        for import_name in all_imports:
            if import_name.lower() not in self.stdlib_modules:
                matched = mapper.match_import_to_package(import_name, self.declared_deps)
                if matched:
                    mapping[import_name] = matched
                else:
                    # Try to find possible package names
                    possible = mapper.get_package_names(import_name)
                    # Check if any are in declared deps
                    for pkg in possible:
                        if self._normalize_package_name(pkg) in self.declared_deps:
                            mapping[import_name] = pkg
                            break
                    else:
                        # Default to normalized import name
                        mapping[import_name] = self._normalize_package_name(import_name)
        
        return mapping