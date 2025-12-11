"""Enhanced dependency scanner module with improved performance.

MIT License - Copyright (c) 2024 DepCleaner
For feature requests or contributions, visit: https://github.com/Jermy-tech/depcleaner
"""
import ast
import logging
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from depcleaner.report import Report
from depcleaner.package_mapper import get_mapper

logger = logging.getLogger(__name__)


class Scanner:
    """Scans Python projects for dependency usage with enhanced features."""

    def __init__(
        self, 
        project_path: Path, 
        max_workers: int = 4,
        exclude_dirs: Optional[Set[str]] = None
    ) -> None:
        """Initialize Scanner.
        
        Args:
            project_path: Root path of the project
            max_workers: Maximum number of worker threads
            exclude_dirs: Additional directories to exclude
        """
        self.project_path = project_path
        self.max_workers = max_workers
        self.custom_exclude_dirs = exclude_dirs or set()
        self.python_files: List[Path] = []
        self.all_imports: Dict[Path, Set[str]] = {}
        self.used_imports: Dict[Path, Set[str]] = {}
        self.declared_deps: Set[str] = set()
        self.stdlib_modules: Set[str] = self._load_stdlib_modules()
        
        # Performance tracking
        self._scan_times: Dict[str, float] = {}

    def _load_stdlib_modules(self) -> Set[str]:
        """Load set of standard library module names.
        
        Returns:
            Set of stdlib module names
        """
        stdlib = set(sys.builtin_module_names)
        
        # Comprehensive stdlib module list
        common_stdlib = {
            'os', 'sys', 'pathlib', 'typing', 'collections', 'itertools',
            'functools', 'operator', 'logging', 'json', 'csv', 'pickle',
            'datetime', 'time', 'random', 're', 'math', 'statistics',
            'argparse', 'configparser', 'shutil', 'tempfile', 'subprocess',
            'threading', 'multiprocessing', 'asyncio', 'unittest', 'pytest',
            'io', 'contextlib', 'abc', 'dataclasses', 'enum', 'warnings',
            'urllib', 'http', 'email', 'html', 'xml', 'hashlib', 'hmac',
            'secrets', 'uuid', 'base64', 'struct', 'socket', 'ssl',
            'concurrent', 'queue', 'heapq', 'bisect', 'array', 'weakref',
            'copy', 'pprint', 'textwrap', 'string', 'difflib', 'locale',
            'gettext', 'codecs', 'encodings', 'unicodedata', 'stringprep',
            'readline', 'rlcompleter', 'sqlite3', 'zlib', 'gzip', 'bz2',
            'lzma', 'zipfile', 'tarfile', 'fnmatch', 'linecache', 'token',
            'tokenize', 'keyword', 'builtins', 'inspect', 'ast', 'symtable',
            'symbol', 'dis', 'pickletools', 'formatter', 'msilib', 'msvcrt',
            'winreg', 'winsound', 'posix', 'pwd', 'grp', 'crypt', 'termios',
            'tty', 'pty', 'fcntl', 'resource', 'syslog', 'optparse',
            'getopt', 'imp', 'importlib', 'modulefinder', 'runpy', 'pkgutil',
            'platform', 'errno', 'ctypes', 'trace', 'traceback', 'tracemalloc',
            'gc', 'site', 'user', 'fpectl', 'distutils', 'venv', 'ensurepip',
            'pdb', 'profile', 'pstats', 'timeit', 'cProfile', 'cmd', 'code',
            'codeop', 'pyclbr', 'py_compile', 'compileall', 'doctest',
            'xmlrpc', 'test', 'bdb', 'faulthandler', 'selectors', 'signal',
            'mmap', 'mailbox', 'mimetypes', 'smtplib', 'poplib', 'imaplib',
            'nntplib', 'telnetlib', 'ftplib', 'socketserver', 'wsgiref',
            'asynchat', 'asyncore', 'netrc', 'xdrlib', 'plistlib', 'calendar',
            'pydoc', 'docutils', 'decimal', 'fractions', 'numbers', 'cmath',
            'turtle', 'tkinter', 'wave', 'chunk', 'sunau', 'aifc', 'audioop',
            'colorsys', 'imghdr', 'sndhdr', 'ossaudiodev', 'getpass', 'curses',
            'platform', 'errno', 'glob', 'fileinput', 'filecmp', 'pipes',
            'select', 'shelve', 'marshal', 'dbm', 'graphlib', 'contextvars',
            'dataclasses', 'graphlib', 'zoneinfo'
        }
        stdlib.update(common_stdlib)
        
        # Add version-specific modules
        if sys.version_info >= (3, 11):
            stdlib.update({'tomllib'})
        
        return stdlib

    def scan(self, progress_callback: Optional[Callable[..., Any]] = None) -> Report:
        """Perform full project scan with progress tracking.
        
        Args:
            progress_callback: Optional callback(current, total, message)
        
        Returns:
            Report with scan results
        """
        import time
        start_time = time.time()
        
        # Step 1: Discover files
        if progress_callback:
            progress_callback(0, 100, "Discovering Python files...")
        self._discover_python_files()
        self._scan_times['discovery'] = time.time() - start_time
        
        # Step 2: Analyze imports
        if progress_callback:
            progress_callback(25, 100, f"Analyzing {len(self.python_files)} files...")
        step_start = time.time()
        self._analyze_imports_parallel()
        self._scan_times['analysis'] = time.time() - step_start
        
        # Step 3: Detect usage
        if progress_callback:
            progress_callback(60, 100, "Detecting unused imports...")
        step_start = time.time()
        self._detect_unused_parallel()
        self._scan_times['detection'] = time.time() - step_start
        
        # Step 4: Parse dependencies
        if progress_callback:
            progress_callback(85, 100, "Parsing dependency files...")
        step_start = time.time()
        self.declared_deps = self._get_declared_dependencies()
        used_deps = self._get_used_dependencies()
        self._scan_times['dependencies'] = time.time() - step_start
        
        self._scan_times['total'] = time.time() - start_time
        
        if progress_callback:
            progress_callback(100, 100, "Scan complete!")
        
        logger.info(f"Scan completed in {self._scan_times['total']:.2f}s")
        
        return Report(
            project_path=self.project_path,
            scanned_files=len(self.python_files),
            all_imports=self.all_imports,
            used_imports=self.used_imports,
            declared_deps=self.declared_deps,
            used_deps=used_deps
        )

    def _discover_python_files(self) -> None:
        """Discover all Python files in project with improved filtering."""
        logger.info("Discovering Python files")
        self.python_files = []
        
        exclude_dirs = {
            ".venv", "venv", "env", ".env", "virtualenv",
            "__pycache__", ".git", ".hg", ".svn", ".bzr",
            "build", "dist", ".eggs", "*.egg-info", "*.egg",
            "node_modules", ".tox", ".pytest_cache", ".nox",
            ".mypy_cache", ".coverage", "htmlcov", ".hypothesis",
            ".cache", "*.so", "*.pyc", "*.pyo", "*.pyd",
            ".idea", ".vscode", ".vs", "*.sublime-*",
            "docs", "_build", "site", ".next", "out"
        }
        exclude_dirs.update(self.custom_exclude_dirs)
        
        try:
            for path in self.project_path.rglob("*.py"):
                if self._should_include(path, exclude_dirs):
                    self.python_files.append(path)
        except PermissionError as e:
            logger.warning(f"Permission denied accessing some files: {e}")
        
        # Sort for consistent ordering
        self.python_files.sort()
        
        logger.info(f"Found {len(self.python_files)} Python files")

    def _should_include(self, path: Path, exclude_dirs: Set[str]) -> bool:
        """Check if file should be included in analysis.
        
        Args:
            path: File path to check
            exclude_dirs: Set of directory names to exclude
            
        Returns:
            True if file should be included
        """
        # Check if any part of the path matches exclude patterns
        path_parts = set(p.lower() for p in path.parts)
        exclude_lower = {e.lower().replace("*", "") for e in exclude_dirs}
        
        if path_parts & exclude_lower:
            return False
        
        # Skip files that are too large (>1MB) - likely generated
        try:
            if path.stat().st_size > 1_000_000:
                logger.debug(f"Skipping large file: {path}")
                return False
        except OSError:
            pass
        
        return True

    def _analyze_imports_parallel(self) -> None:
        """Analyze imports in all Python files using parallel processing."""
        logger.info("Analyzing imports in parallel")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(self._analyze_single_file, path): path
                for path in self.python_files
            }
            
            completed = 0
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    imports = future.result()
                    self.all_imports[path] = imports
                except Exception as e:
                    logger.warning(f"Failed to parse {path}: {e}")
                    self.all_imports[path] = set()
                
                completed += 1
                if completed % 100 == 0:
                    logger.debug(f"Analyzed {completed}/{len(self.python_files)} files")

    def _analyze_imports(self) -> None:
        """Analyze imports in all Python files (non-parallel version for backward compatibility)."""
        logger.info("Analyzing imports")
        for file_path in self.python_files:
            self.all_imports[file_path] = self._analyze_single_file(file_path)

    def _analyze_single_file(self, file_path: Path) -> Set[str]:
        """Analyze imports in a single file with improved error handling.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Set of imported module names
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Skip empty files
            if not content.strip():
                return set()
            
            tree = ast.parse(content, filename=str(file_path))
            return self._extract_imports(tree)
            
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    tree = ast.parse(content, filename=str(file_path))
                    return self._extract_imports(tree)
                except Exception:
                    continue
            logger.warning(f"Cannot decode {file_path}")
            return set()
            
        except SyntaxError as e:
            logger.debug(f"Syntax error in {file_path}: {e}")
            return set()
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            return set()

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
                elif node.level == 0:
                    # from __future__ import ... style
                    for alias in node.names:
                        if alias.name != "*":
                            imports.add(alias.name.split(".")[0])
        
        return imports

    def _detect_unused_parallel(self) -> None:
        """Detect which imports are actually used (parallel version)."""
        logger.info("Detecting unused imports in parallel")
        
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

    def _detect_unused(self) -> None:
        """Detect which imports are actually used (non-parallel version for backward compatibility)."""
        logger.info("Detecting unused imports")
        for file_path in self.python_files:
            self.used_imports[file_path] = self._detect_usage_single_file(file_path)

    def _detect_usage_single_file(self, file_path: Path) -> Set[str]:
        """Detect usage in a single file with improved accuracy.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Set of used import names
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.strip():
                return set()
            
            tree = ast.parse(content, filename=str(file_path))
            imports = self.all_imports.get(file_path, set())
            return self._find_used_names(tree, imports)
            
        except (UnicodeDecodeError, SyntaxError):
            # If we can't parse, assume all imports are used
            return self.all_imports.get(file_path, set())
        except Exception as e:
            logger.warning(f"Cannot analyze usage in {file_path}: {e}")
            return self.all_imports.get(file_path, set())

    def _find_used_names(self, tree: ast.AST, imports: Set[str]) -> Set[str]:
        """Find which imports are actually used in the code.
        
        Args:
            tree: AST tree
            imports: Set of imported names
            
        Returns:
            Set of used import names
        """
        used = set()
        alias_map = {}

        # Build comprehensive alias map
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if alias.asname:
                        alias_map[alias.asname] = top
                    # Also map the original name
                    alias_map[top] = top
                    
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    for alias in node.names:
                        if alias.name != "*":
                            # Map imported symbol to top-level module
                            name = alias.asname if alias.asname else alias.name
                            alias_map[name] = top

        # Detect usage in all contexts
        for node in ast.walk(tree):
            # Direct name usage
            if isinstance(node, ast.Name):
                name = node.id
                if name in imports:
                    used.add(name)
                if name in alias_map and alias_map[name] in imports:
                    used.add(alias_map[name])

            # Attribute access (e.g., os.path, np.array)
            elif isinstance(node, ast.Attribute):
                root = node
                while isinstance(root, ast.Attribute):  # type: ignore
                    root = root.value
                    
                if isinstance(root, ast.Name):
                    name = root.id
                    if name in imports:
                        used.add(name)
                    if name in alias_map and alias_map[name] in imports:
                        used.add(alias_map[name])
            
            # Function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                    if name in alias_map and alias_map[name] in imports:
                        used.add(alias_map[name])

        return used

    def _get_declared_dependencies(self) -> Set[str]:
        """Get dependencies declared in requirements/pyproject/setup.
        
        Returns:
            Set of declared package names (normalized)
        """
        deps = set()
        
        # Parse all dependency sources
        deps.update(self._parse_requirements_txt())
        deps.update(self._parse_pyproject_toml())
        deps.update(self._parse_setup_py())
        deps.update(self._parse_setup_cfg())
        deps.update(self._parse_pipfile())
        
        logger.debug(f"Found {len(deps)} declared dependencies")
        return deps

    def _parse_requirements_txt(self) -> Set[str]:
        """Parse requirements.txt file."""
        deps = set()
        req_file = self.project_path / "requirements.txt"
        
        if not req_file.exists():
            return deps
        
        try:
            with open(req_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith(("-", "git+", "hg+", "svn+", "bzr+")):
                        continue
                    
                    # Extract package name
                    for sep in ["==", ">=", "<=", "~=", "!=", "<", ">", ";"]:
                        if sep in line:
                            line = line.split(sep)[0]
                            break
                    
                    # Remove extras
                    if "[" in line:
                        line = line.split("[")[0]
                    
                    pkg = line.strip()
                    if pkg:
                        deps.add(self._normalize_package_name(pkg))
                        
        except Exception as e:
            logger.warning(f"Failed to read requirements.txt: {e}")
        
        return deps

    def _parse_pyproject_toml(self) -> Set[str]:
        """Parse pyproject.toml file with proper TOML support."""
        deps = set()
        pyproject = self.project_path / "pyproject.toml"
        
        if not pyproject.exists():
            return deps
        
        try:
            # Try modern tomllib (Python 3.11+)
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib  # type: ignore
                except ImportError:
                    tomllib = None
            
            if tomllib:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                    
                    # Handle Poetry dependencies
                    if "tool" in data and "poetry" in data["tool"]:
                        poetry_deps = data["tool"]["poetry"].get("dependencies", {})
                        for pkg in poetry_deps:
                            if pkg not in ("python", "python3"):
                                deps.add(self._normalize_package_name(pkg))
                        
                        # Dev dependencies
                        dev_deps = data["tool"]["poetry"].get("dev-dependencies", {})
                        for pkg in dev_deps:
                            if pkg not in ("python", "python3"):
                                deps.add(self._normalize_package_name(pkg))
                    
                    # Handle PEP 621 dependencies
                    if "project" in data:
                        proj_deps = data["project"].get("dependencies", [])
                        for dep in proj_deps:
                            pkg = self._extract_package_name(dep)
                            if pkg:
                                deps.add(self._normalize_package_name(pkg))
                        
                        # Optional dependencies
                        opt_deps = data["project"].get("optional-dependencies", {})
                        for group in opt_deps.values():
                            for dep in group:
                                pkg = self._extract_package_name(dep)
                                if pkg:
                                    deps.add(self._normalize_package_name(pkg))
                                    
        except Exception as e:
            logger.warning(f"Failed to parse pyproject.toml: {e}")
        
        return deps

    def _parse_setup_py(self) -> Set[str]:
        """Parse setup.py file."""
        deps = set()
        setup_file = self.project_path / "setup.py"
        
        if not setup_file.exists():
            return deps
        
        try:
            with open(setup_file, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == "setup":
                            for keyword in node.keywords:
                                if keyword.arg in ("install_requires", "requires"):
                                    deps.update(self._extract_from_list(keyword.value))
                                elif keyword.arg == "extras_require":
                                    if isinstance(keyword.value, ast.Dict):
                                        for value in keyword.value.values:
                                            deps.update(self._extract_from_list(value))
                                            
        except Exception as e:
            logger.warning(f"Failed to parse setup.py: {e}")
        
        return deps

    def _parse_setup_cfg(self) -> Set[str]:
        """Parse setup.cfg file."""
        deps = set()
        setup_cfg = self.project_path / "setup.cfg"
        
        if not setup_cfg.exists():
            return deps
        
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(setup_cfg)
            
            if "options" in config:
                install_requires = config["options"].get("install_requires", "")
                for line in install_requires.strip().split("\n"):
                    pkg = self._extract_package_name(line)
                    if pkg:
                        deps.add(self._normalize_package_name(pkg))
                        
        except Exception as e:
            logger.warning(f"Failed to parse setup.cfg: {e}")
        
        return deps

    def _parse_pipfile(self) -> Set[str]:
        """Parse Pipfile."""
        deps = set()
        pipfile = self.project_path / "Pipfile"
        
        if not pipfile.exists():
            return deps
        
        try:
            # Pipfile uses TOML format
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib  # type: ignore
                except ImportError:
                    return deps
            
            with open(pipfile, "rb") as f:
                data = tomllib.load(f)
                
                for section in ["packages", "dev-packages"]:
                    if section in data:
                        for pkg in data[section]:
                            deps.add(self._normalize_package_name(pkg))
                            
        except Exception as e:
            logger.warning(f"Failed to parse Pipfile: {e}")
        
        return deps

    def _extract_from_list(self, node: ast.AST) -> Set[str]:
        """Extract package names from AST list node."""
        deps = set()
        
        if isinstance(node, ast.List):
            for elt in node.elts:
                if isinstance(elt, ast.Constant):
                    value = elt.value
                    pkg = self._extract_package_name(str(value))
                    if pkg:
                        deps.add(self._normalize_package_name(pkg))
        
        return deps

    def _extract_package_name(self, spec: str) -> Optional[str]:
        """Extract package name from a dependency specification."""
        spec = spec.strip()
        if not spec:
            return None
        
        # Remove version specifiers
        for sep in ["==", ">=", "<=", "~=", "!=", "<", ">", ";"]:
            if sep in spec:
                spec = spec.split(sep)[0]
                break
        
        # Remove extras
        if "[" in spec:
            spec = spec.split("[")[0]
        
        return spec.strip() if spec.strip() else None

    def _normalize_package_name(self, name: str) -> str:
        """Normalize package name (PEP 503)."""
        return name.lower().replace("-", "_").replace(".", "_")

    def _get_used_dependencies(self) -> Set[str]:
        """Get all dependencies used in code."""
        all_used_imports = set()
        for used in self.used_imports.values():
            all_used_imports.update(used)
        
        # Filter out standard library
        external_imports = {
            pkg for pkg in all_used_imports
            if pkg.lower() not in self.stdlib_modules
        }
        
        # Map imports to packages
        mapper = get_mapper()
        used_packages = set()
        
        for import_name in external_imports:
            matched = mapper.match_import_to_package(import_name, self.declared_deps)
            if matched:
                used_packages.add(matched)
            else:
                normalized = self._normalize_package_name(import_name)
                if normalized in self.declared_deps:
                    used_packages.add(normalized)
                else:
                    used_packages.add(normalized)
        
        return used_packages

    def get_import_to_package_mapping(self) -> Dict[str, str]:
        """Get mapping of import names to package names."""
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
                    mapping[import_name] = self._normalize_package_name(import_name)
        
        return mapping

    def get_scan_statistics(self) -> Dict[str, Any]:
        """Get detailed scanning statistics."""
        return {
            "scan_times": self._scan_times,
            "files_scanned": len(self.python_files),
            "total_imports": sum(len(imps) for imps in self.all_imports.values()),
            "unique_imports": len(set().union(*self.all_imports.values()) if self.all_imports else set()),
            "workers_used": self.max_workers
        }