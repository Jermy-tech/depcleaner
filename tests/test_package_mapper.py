"""Package name to module name mapping utilities."""
import logging
from typing import Dict, Set, Optional

logger = logging.getLogger(__name__)


class PackageMapper:
    """Maps PyPI package names to their import module names using metadata."""
    
    def __init__(self):
        """Initialize the package mapper."""
        self._import_to_dist: Dict[str, str] = {}
        self._dist_to_imports: Dict[str, Set[str]] = {}
        self._load_mappings()
    
    def _load_mappings(self) -> None:
        """Load package mappings from installed packages metadata."""
        try:
            # Python 3.8+
            from importlib.metadata import packages_distributions
        except ImportError:
            try:
                # Backport for older Python
                from importlib_metadata import packages_distributions  # type: ignore
            except ImportError:
                logger.warning(
                    "Could not import packages_distributions. "
                    "Install importlib-metadata for Python < 3.8"
                )
                return
        
        try:
            # Get the mapping: import_name -> [dist_name1, dist_name2, ...]
            pkg_dist_map = packages_distributions()
            
            for import_name, dist_names in pkg_dist_map.items():
                # Normalize names for comparison
                norm_import = self._normalize_name(import_name)
                
                # Most packages have a single distribution
                # For namespace packages, just use the first one
                if dist_names:
                    dist_name = dist_names[0]
                    norm_dist = self._normalize_name(dist_name)
                    
                    # Build both forward and reverse mappings
                    self._import_to_dist[norm_import] = norm_dist
                    
                    if norm_dist not in self._dist_to_imports:
                        self._dist_to_imports[norm_dist] = set()
                    self._dist_to_imports[norm_dist].add(norm_import)
            
            logger.debug(f"Loaded {len(self._import_to_dist)} package mappings from metadata")
        
        except Exception as e:
            logger.warning(f"Failed to load package mappings: {e}")
    
    def _normalize_name(self, name: str) -> str:
        """Normalize package/module name for comparison.
        
        Args:
            name: Package or module name
            
        Returns:
            Normalized name (PEP 503 compliant)
        """
        return name.lower().replace("-", "_").replace(".", "_")
    
    def get_package_name(self, import_name: str) -> Optional[str]:
        """Get the distribution package name for a given import name.
        
        Args:
            import_name: Python module/import name (e.g., 'yaml', 'PIL', 'cupy')
            
        Returns:
            Distribution package name (e.g., 'pyyaml', 'pillow', 'cupy_cuda12x')
            or None if not found
        """
        normalized = self._normalize_name(import_name)
        return self._import_to_dist.get(normalized)
    
    def get_import_names(self, package_name: str) -> Set[str]:
        """Get possible import names for a given distribution package name.
        
        Args:
            package_name: PyPI distribution package name
            
        Returns:
            Set of possible import names
        """
        normalized = self._normalize_name(package_name)
        return self._dist_to_imports.get(normalized, set())
    
    def match_import_to_package(
        self, 
        import_name: str, 
        declared_packages: Set[str]
    ) -> Optional[str]:
        """Match an import name to a declared package.
        
        Args:
            import_name: Import module name from code
            declared_packages: Set of declared package names (normalized)
            
        Returns:
            Matching package name from declared_packages or None
        """
        norm_import = self._normalize_name(import_name)
        
        # First, try direct match
        if norm_import in declared_packages:
            return norm_import
        
        # Check if we have metadata mapping for this import
        dist_name = self.get_package_name(import_name)
        if dist_name and dist_name in declared_packages:
            return dist_name
        
        # Check all declared packages to see if any map to this import
        for pkg in declared_packages:
            imports = self.get_import_names(pkg)
            if norm_import in imports:
                return pkg
        
        return None
    
    def is_variant_of(self, package1: str, package2: str) -> bool:
        """Check if two packages provide the same import names.
        
        Args:
            package1: First package name
            package2: Second package name
            
        Returns:
            True if they provide the same imports
        """
        imports1 = self.get_import_names(package1)
        imports2 = self.get_import_names(package2)
        
        # If they share any import names, they're variants
        return bool(imports1 & imports2)


# Global instance
_mapper: Optional[PackageMapper] = None


def get_mapper() -> PackageMapper:
    """Get the global PackageMapper instance.
    
    Returns:
        PackageMapper instance
    """
    global _mapper
    if _mapper is None:
        _mapper = PackageMapper()
    return _mapper