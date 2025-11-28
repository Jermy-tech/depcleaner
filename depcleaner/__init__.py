"""DepCleaner - Python dependency cleanup tool."""
from depcleaner.core import DepCleaner
from depcleaner.scanner import Scanner
from depcleaner.fixer import Fixer

__version__ = "1.3.3"
__all__ = ["DepCleaner", "Scanner", "Fixer"]
