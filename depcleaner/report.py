"""Report generation module."""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set


@dataclass
class Report:
    """Scan report containing analysis results."""
    
    project_path: Path
    scanned_files: int
    all_imports: Dict[Path, Set[str]]
    used_imports: Dict[Path, Set[str]]
    declared_deps: Set[str]
    used_deps: Set[str]

    def get_unused_imports(self) -> Dict[Path, Set[str]]:
        """Get unused imports per file.
        
        Returns:
            Dictionary mapping file paths to unused imports
        """
        unused = {}
        for file_path, all_imp in self.all_imports.items():
            used_imp = self.used_imports.get(file_path, set())
            diff = all_imp - used_imp
            if diff:
                unused[file_path] = diff
        return unused

    def get_unused_packages(self) -> Set[str]:
        """Get declared but unused packages.
        
        Returns:
            Set of unused package names
        """
        return self.declared_deps - self.used_deps

    def __str__(self) -> str:
        """Generate report string.
        
        Returns:
            Formatted report string
        """
        lines = [
            f"DepCleaner Report",
            f"=" * 50,
            f"Project: {self.project_path}",
            f"Files scanned: {self.scanned_files}",
            f"",
        ]
        
        unused_imports = self.get_unused_imports()
        if unused_imports:
            lines.append(f"Unused imports found in {len(unused_imports)} files:")
            for file_path, imports in unused_imports.items():
                rel_path = file_path.relative_to(self.project_path)
                lines.append(f"  {rel_path}: {', '.join(sorted(imports))}")
            lines.append("")
        
        unused_pkgs = self.get_unused_packages()
        if unused_pkgs:
            lines.append(f"Unused packages: {', '.join(sorted(unused_pkgs))}")
        else:
            lines.append("No unused packages found")
        
        return "\n".join(lines)
