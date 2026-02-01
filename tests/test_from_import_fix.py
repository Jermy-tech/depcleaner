"""Test script to verify the from-import fix works correctly."""
import tempfile
from pathlib import Path
from depcleaner import DepCleaner


def test_schema_example():
    """Test with imports similar to schema.py but using external packages."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create a file with external package imports
        schema_file = tmppath / "schema.py"
        schema_file.write_text("""
import requests
from bs4 import BeautifulSoup
from numpy import array

def test_func():
    soup = BeautifulSoup("<html></html>", "html.parser")
    arr = array([1, 2, 3])
    return requests.get("http://example.com")
""")
        
        # Run the scanner
        cleaner = DepCleaner(tmppath)
        report = cleaner.scan()
        
        print("="*70)
        print("Testing fix for 'from X import Y' detection")
        print("="*70)
        print("\nFile: schema.py")
        print(f"Imports found: {report.all_imports.get(schema_file, set())}")
        print(f"Imports used: {report.used_imports.get(schema_file, set())}")
        
        unused = report.get_unused_imports()
        
        if schema_file in unused and unused[schema_file]:
            print(f"\n❌ FAILED: Incorrectly marked as unused: {unused[schema_file]}")
            return False
        else:
            print("\n✅ PASSED: All imports correctly detected as used!")
            return True


def test_multiple_scenarios():
    """Test various import scenarios."""
    
    test_cases = [
        (
            "from_import_used.py",
            "from numpy import array\narr = array([1, 2, 3])",
            {"numpy"},
            set()
        ),
        (
            "from_import_unused.py",
            "from numpy import array\nprint('hello')",
            set(),
            {"numpy"}
        ),
        (
            "regular_import_used.py",
            "import numpy\narr = numpy.array([1, 2, 3])",
            {"numpy"},
            set()
        ),
        (
            "mixed_imports.py",
            "import requests\nfrom numpy import array\narr = array([1])\nresp = requests.get('http://example.com')",
            {"requests", "numpy"},
            set()
        ),
        (
            "import_with_alias.py",
            "from numpy import array as arr\nx = arr([1, 2, 3])",
            {"numpy"},
            set()
        ),
        (
            "multiple_symbols.py",
            "from numpy import array, zeros\nx = array([1])\ny = zeros(5)",
            {"numpy"},
            set()
        ),
    ]
    
    print("\n" + "="*70)
    print("Testing multiple scenarios")
    print("="*70)
    
    all_passed = True
    
    for filename, code, expected_used, expected_unused in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            test_file = tmppath / filename
            test_file.write_text(code)
            
            cleaner = DepCleaner(tmppath)
            report = cleaner.scan()
            
            actual_used = report.used_imports.get(test_file, set())
            actual_unused = report.get_unused_imports().get(test_file, set())
            
            # Check if results match expectations
            used_match = expected_used == actual_used
            unused_match = expected_unused == actual_unused
            
            status = "✅" if (used_match and unused_match) else "❌"
            print(f"\n{status} {filename}")
            print(f"   Expected used: {expected_used}")
            print(f"   Actual used:   {actual_used}")
            print(f"   Expected unused: {expected_unused}")
            print(f"   Actual unused:   {actual_unused}")
            
            if not (used_match and unused_match):
                all_passed = False
    
    return all_passed


if __name__ == "__main__":
    print("\n" + "="*70)
    print("FROM-IMPORT FIX VERIFICATION")
    print("="*70)
    
    result1 = test_schema_example()
    result2 = test_multiple_scenarios()
    
    print("\n" + "="*70)
    if result1 and result2:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70)