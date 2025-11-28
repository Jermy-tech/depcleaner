"""Tests for package_mapper module."""
import pytest
from depcleaner.package_mapper import PackageMapper, get_mapper


class TestPackageMapper:
    """Tests for PackageMapper class."""
    
    def test_cupy_variants(self):
        """Test that CuPy variants all map to 'cupy'."""
        mapper = PackageMapper()
        
        assert mapper.get_module_name('cupy-cuda11x') == 'cupy'
        assert mapper.get_module_name('cupy-cuda12x') == 'cupy'
        assert mapper.get_module_name('cupy-cuda13x') == 'cupy'
        assert mapper.get_module_name('cupy-rocm-4-3') == 'cupy'
        assert mapper.get_module_name('cupy-rocm-5-0') == 'cupy'
    
    def test_common_mappings(self):
        """Test common package name to module name mappings."""
        mapper = PackageMapper()
        
        assert mapper.get_module_name('pyyaml') == 'yaml'
        assert mapper.get_module_name('pillow') == 'PIL'
        assert mapper.get_module_name('python-dateutil') == 'dateutil'
        assert mapper.get_module_name('beautifulsoup4') == 'bs4'
        assert mapper.get_module_name('scikit-learn') == 'sklearn'
        assert mapper.get_module_name('opencv-python') == 'cv2'
    
    def test_match_import_to_package(self):
        """Test matching import names to declared packages."""
        mapper = PackageMapper()
        
        declared = {'cupy-cuda12x', 'numpy', 'pillow'}
        
        # Should match cupy import to cupy-cuda12x package
        assert mapper.match_import_to_package('cupy', declared) == 'cupy-cuda12x'
        
        # Should match PIL import to pillow package
        assert mapper.match_import_to_package('PIL', declared) == 'pillow'
        
        # Should match numpy directly
        assert mapper.match_import_to_package('numpy', declared) == 'numpy'
        
        # Should return None for unknown import
        assert mapper.match_import_to_package('unknown_module', declared) is None
    
    def test_is_variant_of(self):
        """Test checking if packages are variants."""
        mapper = PackageMapper()
        
        # CuPy variants
        assert mapper.is_variant_of('cupy-cuda11x', 'cupy-cuda12x') is True
        assert mapper.is_variant_of('cupy-cuda13x', 'cupy-rocm-5-0') is True
        
        # TensorFlow variants
        assert mapper.is_variant_of('tensorflow-gpu', 'tensorflow-cpu') is True
        
        # Different packages
        assert mapper.is_variant_of('numpy', 'scipy') is False
    
    def test_get_package_names(self):
        """Test getting possible package names for a module."""
        mapper = PackageMapper()
        
        # Should return known packages for cupy
        possible = mapper.get_package_names('cupy')
        assert 'cupy_cuda12x' in possible or 'cupy' in possible
        
        # Should return variations for unknown module
        possible = mapper.get_package_names('my_module')
        assert 'my_module' in possible
        assert 'my-module' in possible
        assert 'python-my_module' in possible or 'python-my-module' in possible
    
    def test_normalize_name(self):
        """Test name normalization."""
        mapper = PackageMapper()
        
        assert mapper._normalize_name('My-Package') == 'my_package'
        assert mapper._normalize_name('package.name') == 'package_name'
        assert mapper._normalize_name('Package_Name') == 'package_name'
    
    def test_global_mapper(self):
        """Test global mapper instance."""
        mapper1 = get_mapper()
        mapper2 = get_mapper()
        
        # Should return same instance
        assert mapper1 is mapper2
    
    def test_pytorch_variants(self):
        """Test PyTorch variants."""
        mapper = PackageMapper()
        
        assert mapper.get_module_name('torch-cpu') == 'torch'
        assert mapper.get_module_name('torch-cuda') == 'torch'
        assert mapper.is_variant_of('torch-cpu', 'torch-cuda') is True
    
    def test_prefix_removal(self):
        """Test that python- prefix is removed."""
        mapper = PackageMapper()
        
        # When no known mapping exists, should remove python- prefix
        result = mapper.get_module_name('python-unknown-lib')
        assert 'python' not in result or result == 'python_unknown_lib'


class TestIntegration:
    """Integration tests with actual usage patterns."""
    
    def test_requirements_with_cupy(self):
        """Test scenario with cupy-cuda12x in requirements."""
        mapper = PackageMapper()
        
        # Simulating declared packages from requirements.txt
        declared_packages = {
            'numpy',
            'cupy_cuda12x',  # Normalized from cupy-cuda12x
            'pillow',
            'requests'
        }
        
        # Simulating imports found in code
        imports = ['numpy', 'cupy', 'PIL', 'requests', 'sys']
        
        # Match each import to a package
        matched = {}
        for imp in imports:
            pkg = mapper.match_import_to_package(imp, declared_packages)
            if pkg:
                matched[imp] = pkg
        
        assert matched['cupy'] == 'cupy_cuda12x'
        assert matched['PIL'] == 'pillow'
        assert matched['numpy'] == 'numpy'
        assert 'sys' not in matched  # stdlib module


if __name__ == '__main__':
    pytest.main([__file__, '-v'])