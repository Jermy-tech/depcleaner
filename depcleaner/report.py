"""Report module for DepCleaner."""
import json
from pathlib import Path
from typing import Dict, Set
from dataclasses import dataclass, asdict


@dataclass
class Report:
    """Scan report containing dependency analysis results."""
    
    project_path: Path
    scanned_files: int
    all_imports: Dict[Path, Set[str]]
    used_imports: Dict[Path, Set[str]]
    declared_deps: Set[str]
    used_deps: Set[str]

    def get_unused_imports(self) -> Dict[Path, Set[str]]:
        """Get unused imports per file.
        
        Returns:
            Dictionary mapping file paths to sets of unused imports
        """
        unused = {}
        for file_path, all_imps in self.all_imports.items():
            used_imps = self.used_imports.get(file_path, set())
            diff = all_imps - used_imps
            if diff:
                unused[file_path] = diff
        return unused

    def get_unused_packages(self) -> Set[str]:
        """Get packages that are declared but not used.
        
        Returns:
            Set of unused package names
        """
        return self.declared_deps - self.used_deps

    def get_missing_packages(self) -> Set[str]:
        """Get packages that are used but not declared.
        
        Returns:
            Set of missing package names
        """
        return self.used_deps - self.declared_deps

    def __str__(self) -> str:
        """Generate summary report string.
        
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("="*60)
        lines.append("DepCleaner Scan Report")
        lines.append("="*60)
        lines.append(f"Project: {self.project_path}")
        lines.append(f"Files scanned: {self.scanned_files}")
        lines.append(f"Declared dependencies: {len(self.declared_deps)}")
        lines.append(f"Used dependencies: {len(self.used_deps)}")
        lines.append("")
        
        unused_imports = self.get_unused_imports()
        if unused_imports:
            lines.append("Unused Imports:")
            lines.append("-"*60)
            for file_path, imports in sorted(unused_imports.items()):
                rel_path = file_path.relative_to(self.project_path)
                lines.append(f"\n{rel_path}:")
                for imp in sorted(imports):
                    lines.append(f"  - {imp}")
            lines.append("")
        else:
            lines.append("✓ No unused imports found")
            lines.append("")
        
        unused_packages = self.get_unused_packages()
        if unused_packages:
            lines.append("Unused Packages (declared but not used):")
            lines.append("-"*60)
            for pkg in sorted(unused_packages):
                lines.append(f"  - {pkg}")
            lines.append("")
        else:
            lines.append("✓ No unused packages found")
            lines.append("")
        
        missing_packages = self.get_missing_packages()
        if missing_packages:
            lines.append("Missing Packages (used but not declared):")
            lines.append("-"*60)
            for pkg in sorted(missing_packages):
                lines.append(f"  - {pkg}")
            lines.append("")
        
        lines.append("="*60)
        return "\n".join(lines)

    def to_detailed_string(self) -> str:
        """Generate detailed report string.
        
        Returns:
            Formatted detailed report string
        """
        lines = []
        lines.append("="*60)
        lines.append("DepCleaner Detailed Report")
        lines.append("="*60)
        lines.append(f"Project: {self.project_path}")
        lines.append(f"Files scanned: {self.scanned_files}")
        lines.append("")
        
        # All imports per file
        lines.append("All Imports by File:")
        lines.append("-"*60)
        for file_path in sorted(self.all_imports.keys()):
            rel_path = file_path.relative_to(self.project_path)
            imports = self.all_imports[file_path]
            used = self.used_imports.get(file_path, set())
            unused = imports - used
            
            lines.append(f"\n{rel_path} ({len(imports)} imports):")
            
            if used:
                lines.append("  Used:")
                for imp in sorted(used):
                    lines.append(f"    ✓ {imp}")
            
            if unused:
                lines.append("  Unused:")
                for imp in sorted(unused):
                    lines.append(f"    ✗ {imp}")
        
        lines.append("")
        lines.append("="*60)
        lines.append("Dependency Summary:")
        lines.append("-"*60)
        lines.append(f"Declared: {len(self.declared_deps)}")
        lines.append(f"Used: {len(self.used_deps)}")
        lines.append(f"Unused: {len(self.get_unused_packages())}")
        lines.append(f"Missing: {len(self.get_missing_packages())}")
        lines.append("="*60)
        
        return "\n".join(lines)

    def to_json(self) -> str:
        """Convert report to JSON format.
        
        Returns:
            JSON string representation of the report
        """
        data = {
            "project_path": str(self.project_path),
            "scanned_files": self.scanned_files,
            "declared_dependencies": sorted(list(self.declared_deps)),
            "used_dependencies": sorted(list(self.used_deps)),
            "unused_packages": sorted(list(self.get_unused_packages())),
            "missing_packages": sorted(list(self.get_missing_packages())),
            "unused_imports": {
                str(path.relative_to(self.project_path)): sorted(list(imports))
                for path, imports in self.get_unused_imports().items()
            },
            "summary": {
                "total_files": self.scanned_files,
                "files_with_unused_imports": len(self.get_unused_imports()),
                "total_unused_imports": sum(
                    len(imports) for imports in self.get_unused_imports().values()
                ),
                "unused_packages_count": len(self.get_unused_packages()),
                "missing_packages_count": len(self.get_missing_packages())
            }
        }
        return json.dumps(data, indent=2)

    def to_dict(self) -> Dict:
        """Convert report to dictionary.
        
        Returns:
            Dictionary representation of the report
        """
        return json.loads(self.to_json())

    def save(self, output_path: str) -> None:
        """Save report to file.
        
        Args:
            output_path: Path to save the report
        """
        output = Path(output_path)
        
        if output.suffix == ".json":
            content = self.to_json()
        else:
            content = str(self)
        
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)

    def get_statistics(self) -> Dict[str, any]:
        """Get statistical summary of the report.
        
        Returns:
            Dictionary with statistics
        """
        unused_imports = self.get_unused_imports()
        total_imports = sum(len(imports) for imports in self.all_imports.values())
        unused_import_count = sum(len(imports) for imports in unused_imports.values())
        
        return {
            "scanned_files": self.scanned_files,
            "total_imports": total_imports,
            "unique_imports": len(set().union(*self.all_imports.values())),
            "unused_imports_count": unused_import_count,
            "files_with_unused": len(unused_imports),
            "declared_packages": len(self.declared_deps),
            "used_packages": len(self.used_deps),
            "unused_packages": len(self.get_unused_packages()),
            "missing_packages": len(self.get_missing_packages()),
            "cleanup_potential_pct": round(
                (unused_import_count / total_imports * 100) if total_imports > 0 else 0,
                2
            )
        }