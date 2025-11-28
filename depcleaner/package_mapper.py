"""Package name to module name mapping utilities."""
import logging
import subprocess
import sys
from typing import Dict, Set, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PackageMapper:
    """Maps PyPI package names to their import module names."""
    
    # Known mappings where package name != import name
    KNOWN_MAPPINGS = {
        # Common cases
        'pyyaml': 'yaml',
        'pillow': 'PIL',
        'python-dateutil': 'dateutil',
        'python-dotenv': 'dotenv',
        'beautifulsoup4': 'bs4',
        'scikit-learn': 'sklearn',
        'scikit-image': 'skimage',
        'opencv-python': 'cv2',
        'opencv-contrib-python': 'cv2',
        'opencv-python-headless': 'cv2',
        'msgpack-python': 'msgpack',
        'protobuf': 'google.protobuf',
        'attrs': 'attr',
        'ruamel.yaml': 'ruamel',
        'python-markdown': 'markdown',
        'python-slugify': 'slugify',
        'mysql-python': 'MySQLdb',
        'mysqlclient': 'MySQLdb',
        'python-ldap': 'ldap',
        'python-magic': 'magic',
        'python-docx': 'docx',
        'python-pptx': 'pptx',
        'pycryptodome': 'Crypto',
        'pycryptodomex': 'Cryptodome',
        'typing-extensions': 'typing_extensions',
        
        # CuPy variants (all import as 'cupy')
        'cupy-cuda11x': 'cupy',
        'cupy-cuda12x': 'cupy',
        'cupy-cuda13x': 'cupy',
        'cupy-rocm-4-3': 'cupy',
        'cupy-rocm-5-0': 'cupy',
        'cupy-rocm-7-0': 'cupy',
        
        # PyTorch variants
        'torch-cpu': 'torch',
        'torch-cuda': 'torch',
        
        # Other GPU packages
        'tensorflow-gpu': 'tensorflow',
        'tensorflow-cpu': 'tensorflow',
        'jaxlib': 'jax',
        
        # Package with extras that are separate
        'django-debug-toolbar': 'debug_toolbar',
        'pytest-cov': 'pytest_cov',
        'pytest-xdist': 'xdist',
        'pytest-django': 'pytest_django',
    }
    
    def __init__(self):
        """Initialize the package mapper."""
        self._cache: Dict[str, str] = {}
        self._reverse_cache: Dict[str, Set[str]] = {}
        self._build_reverse_cache()
    
    def _build_reverse_cache(self) -> None:
        """Build reverse mapping from module name to package names."""
        for pkg_name, module_name in self.KNOWN_MAPPINGS.items():
            normalized_pkg = self._normalize_name(pkg_name)
            base_module = module_name.split('.')[0]
            
            if base_module not in self._reverse_cache:
                self._reverse_cache[base_module] = set()
            self._reverse_cache[base_module].add(normalized_pkg)
    
    def _normalize_name(self, name: str) -> str:
        """Normalize package/module name for comparison.
        
        Args:
            name: Package or module name
            
        Returns:
            Normalized name
        """
        return name.lower().replace('-', '_').replace('.', '_')
    
    def get_module_name(self, package_name: str) -> str:
        """Get the module name for a given package name.
        
        Args:
            package_name: PyPI package name
            
        Returns:
            Module name to use for imports
        """
        normalized = self._normalize_name(package_name)
        
        # Check cache first
        if normalized in self._cache:
            return self._cache[normalized]
        
        # Check known mappings
        for pkg, module in self.KNOWN_MAPPINGS.items():
            if self._normalize_name(pkg) == normalized:
                self._cache[normalized] = module.split('.')[0]
                return self._cache[normalized]
        
        # Try to get from installed package metadata
        module_name = self._get_from_metadata(package_name)
        if module_name:
            self._cache[normalized] = module_name
            return module_name
        
        # Default: assume package name == module name
        # Remove common prefixes/suffixes
        cleaned = package_name.replace('python-', '').replace('-python', '')
        cleaned = cleaned.split('[')[0]  # Remove extras like package[extra]
        
        module_name = self._normalize_name(cleaned)
        self._cache[normalized] = module_name
        return module_name
    
    def get_package_names(self, module_name: str) -> Set[str]:
        """Get possible package names for a given module name.
        
        Args:
            module_name: Python module name
            
        Returns:
            Set of possible PyPI package names
        """
        normalized = self._normalize_name(module_name)
        
        # Check reverse cache
        if normalized in self._reverse_cache:
            return self._reverse_cache[normalized].copy()
        
        # Default mappings
        possible = {
            normalized,
            normalized.replace('_', '-'),
            f'python-{normalized}',
            f'python-{normalized.replace("_", "-")}',
        }
        
        return possible
    
    def _get_from_metadata(self, package_name: str) -> Optional[str]:
        """Try to get module name from installed package metadata.
        
        Args:
            package_name: Package name
            
        Returns:
            Module name if found, None otherwise
        """
        try:
            # Try using importlib.metadata (Python 3.8+)
            try:
                from importlib.metadata import distribution, PackageNotFoundError
            except ImportError:
                from importlib_metadata import distribution, PackageNotFoundError
            
            try:
                dist = distribution(package_name)
                
                # Check top_level.txt for actual module names
                if dist.read_text('top_level.txt'):
                    modules = dist.read_text('top_level.txt').strip().split('\n')
                    if modules and modules[0]:
                        return modules[0]
            except (PackageNotFoundError, FileNotFoundError):
                pass
        except Exception as e:
            logger.debug(f"Could not get metadata for {package_name}: {e}")
        
        return None
    
    def match_import_to_package(
        self, 
        import_name: str, 
        declared_packages: Set[str]
    ) -> Optional[str]:
        """Match an import name to a declared package.
        
        Args:
            import_name: Import module name from code
            declared_packages: Set of declared package names
            
        Returns:
            Matching package name or None
        """
        normalized_import = self._normalize_name(import_name)
        
        for pkg in declared_packages:
            # Direct match
            if self._normalize_name(pkg) == normalized_import:
                return pkg
            
            # Check if package maps to this import
            module_name = self.get_module_name(pkg)
            if self._normalize_name(module_name) == normalized_import:
                return pkg
        
        return None
    
    def is_variant_of(self, package1: str, package2: str) -> bool:
        """Check if two packages are variants of the same library.
        
        Args:
            package1: First package name
            package2: Second package name
            
        Returns:
            True if they're variants of the same package
        """
        module1 = self.get_module_name(package1)
        module2 = self.get_module_name(package2)
        
        return self._normalize_name(module1) == self._normalize_name(module2)


# Global instance
_mapper = None

def get_mapper() -> PackageMapper:
    """Get the global PackageMapper instance.
    
    Returns:
        PackageMapper instance
    """
    global _mapper
    if _mapper is None:
        _mapper = PackageMapper()
    return _mapper