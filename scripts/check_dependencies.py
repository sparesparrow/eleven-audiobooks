#!/usr/bin/env python3
"""Check dependencies for updates in the Eleven Audiobooks project."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import toml
from packaging import version


@dataclass
class Dependency:
    """Container for dependency information."""
    name: str
    current_version: str
    latest_version: Optional[str] = None
    is_outdated: bool = False


def get_pypi_version(package_name: str) -> Optional[str]:
    """
    Get the latest version of a package from PyPI.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Latest version string or None if not found
    """
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        response.raise_for_status()
        return response.json()["info"]["version"]
    except Exception:
        return None


def parse_version_spec(spec: str) -> Tuple[str, str]:
    """
    Parse version specification into operator and version.
    
    Args:
        spec: Version specification (e.g., ">=1.0.0")
        
    Returns:
        Tuple of (operator, version)
    """
    operators = [">=", "<=", "==", ">", "<", "~=", "!="]
    for op in operators:
        if spec.startswith(op):
            return op, spec[len(op):].strip()
    return "==", spec.strip()


def check_dependencies(project_root: Path) -> Dict[str, List[Dependency]]:
    """
    Check all project dependencies for updates.
    
    Args:
        project_root: Path to project root
        
    Returns:
        Dictionary of dependency groups and their status
    """
    # Read pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    project_data = toml.load(pyproject_path)
    
    # Initialize results
    results: Dict[str, List[Dependency]] = {
        "dependencies": [],
        "dev-dependencies": [],
        "test-dependencies": []
    }
    
    # Check main dependencies
    if "project" in project_data and "dependencies" in project_data["project"]:
        for dep in project_data["project"]["dependencies"]:
            name, spec = dep.split(" ", 1) if " " in dep else (dep, "")
            _, current = parse_version_spec(spec) if spec else ("==", "")
            latest = get_pypi_version(name)
            
            is_outdated = False
            if latest and current:
                try:
                    is_outdated = version.parse(latest) > version.parse(current)
                except version.InvalidVersion:
                    pass
            
            results["dependencies"].append(Dependency(
                name=name,
                current_version=current,
                latest_version=latest,
                is_outdated=is_outdated
            ))
    
    # Check optional dependencies
    if "project" in project_data and "optional-dependencies" in project_data["project"]:
        for group, deps in project_data["project"]["optional-dependencies"].items():
            if group not in results:
                results[group] = []
            
            for dep in deps:
                name, spec = dep.split(" ", 1) if " " in dep else (dep, "")
                _, current = parse_version_spec(spec) if spec else ("==", "")
                latest = get_pypi_version(name)
                
                is_outdated = False
                if latest and current:
                    try:
                        is_outdated = version.parse(latest) > version.parse(current)
                    except version.InvalidVersion:
                        pass
                
                results[group].append(Dependency(
                    name=name,
                    current_version=current,
                    latest_version=latest,
                    is_outdated=is_outdated
                ))
    
    return results


def format_results(results: Dict[str, List[Dependency]]) -> str:
    """
    Format dependency check results as a string.
    
    Args:
        results: Dictionary of dependency groups and their status
        
    Returns:
        Formatted string
    """
    output = []
    
    for group, deps in results.items():
        if not deps:
            continue
        
        output.append(f"\n{group.upper()}")
        output.append("=" * len(group))
        
        outdated = [d for d in deps if d.is_outdated]
        if outdated:
            output.append("\nOutdated packages:")
            for dep in outdated:
                output.append(
                    f"  {dep.name:<30} {dep.current_version:<10} -> {dep.latest_version}"
                )
        
        up_to_date = [d for d in deps if not d.is_outdated and d.latest_version]
        if up_to_date:
            output.append("\nUp-to-date packages:")
            for dep in up_to_date:
                output.append(
                    f"  {dep.name:<30} {dep.current_version}"
                )
        
        unknown = [d for d in deps if not d.latest_version]
        if unknown:
            output.append("\nUnable to check:")
            for dep in unknown:
                output.append(
                    f"  {dep.name:<30} {dep.current_version}"
                )
    
    return "\n".join(output)


def generate_report(results: Dict[str, List[Dependency]], output_dir: Path) -> None:
    """
    Generate dependency check report.
    
    Args:
        results: Dictionary of dependency groups and their status
        output_dir: Output directory for report
    """
    # Create reports directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate text report
    text_report = format_results(results)
    (output_dir / "dependencies.txt").write_text(text_report)
    
    # Generate JSON report
    json_data = {
        group: [
            {
                "name": dep.name,
                "current_version": dep.current_version,
                "latest_version": dep.latest_version,
                "is_outdated": dep.is_outdated
            }
            for dep in deps
        ]
        for group, deps in results.items()
    }
    (output_dir / "dependencies.json").write_text(
        json.dumps(json_data, indent=2)
    )


def main() -> None:
    """Run dependency check."""
    try:
        # Get project root
        project_root = Path(__file__).parent.parent
        
        # Check dependencies
        print("Checking dependencies...")
        results = check_dependencies(project_root)
        
        # Generate report
        reports_dir = project_root / "reports" / "dependencies"
        generate_report(results, reports_dir)
        
        # Print results
        print(format_results(results))
        print(f"\nDetailed reports saved to {reports_dir}")
        
    except Exception as e:
        print(f"Error checking dependencies: {e}")
        exit(1)


if __name__ == "__main__":
    main() 