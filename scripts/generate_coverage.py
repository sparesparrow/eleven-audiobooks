#!/usr/bin/env python3
"""Generate code coverage reports for the Eleven Audiobooks project."""

import os
import subprocess
import webbrowser
from pathlib import Path

import coverage


def generate_coverage() -> None:
    """Generate code coverage reports."""
    # Project root directory
    root_dir = Path(__file__).parent.parent
    
    # Coverage configuration
    cov = coverage.Coverage(
        source=["eleven_audiobooks"],
        omit=[
            "*/tests/*",
            "*/scripts/*",
            "*/__init__.py"
        ],
        config_file=root_dir / ".coveragerc"
    )
    
    try:
        # Start coverage collection
        cov.start()
        
        # Run tests
        subprocess.run(
            ["pytest", "tests/"],
            cwd=root_dir,
            check=True
        )
        
    finally:
        # Stop coverage collection
        cov.stop()
    
    # Save coverage data
    cov.save()
    
    # Generate reports directory
    reports_dir = root_dir / "reports" / "coverage"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate HTML report
    html_dir = reports_dir / "html"
    cov.html_report(directory=html_dir)
    
    # Generate XML report for CI
    cov.xml_report(outfile=reports_dir / "coverage.xml")
    
    # Generate text report
    with open(reports_dir / "coverage.txt", "w") as f:
        cov.report(file=f)
    
    # Print summary
    total = cov.report()
    print(f"\nTotal coverage: {total:.2f}%")
    
    # Generate badge
    generate_coverage_badge(total, reports_dir)
    
    # Open report in browser
    webbrowser.open(f"file://{html_dir}/index.html")


def generate_coverage_badge(percentage: float, output_dir: Path) -> None:
    """
    Generate a coverage badge SVG.
    
    Args:
        percentage: Coverage percentage
        output_dir: Output directory for badge
    """
    # Determine color based on coverage
    if percentage >= 90:
        color = "brightgreen"
    elif percentage >= 80:
        color = "green"
    elif percentage >= 70:
        color = "yellowgreen"
    elif percentage >= 60:
        color = "yellow"
    else:
        color = "red"
    
    # Badge SVG template
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="106" height="20">
    <linearGradient id="a" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <rect rx="3" width="106" height="20" fill="#555"/>
    <rect rx="3" x="53" width="53" height="20" fill="#{color}"/>
    <path fill="#{color}" d="M53 0h4v20h-4z"/>
    <rect rx="3" width="106" height="20" fill="url(#a)"/>
    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
        <text x="27.5" y="15" fill="#010101" fill-opacity=".3">coverage</text>
        <text x="27.5" y="14">coverage</text>
        <text x="78.5" y="15" fill="#010101" fill-opacity=".3">{percentage:.0f}%</text>
        <text x="78.5" y="14">{percentage:.0f}%</text>
    </g>
</svg>"""
    
    # Save badge
    (output_dir / "coverage-badge.svg").write_text(svg)


def main() -> None:
    """Run coverage generation."""
    try:
        generate_coverage()
    except subprocess.CalledProcessError as e:
        print(f"Error running tests: {e}")
        exit(1)
    except Exception as e:
        print(f"Error generating coverage report: {e}")
        exit(1)


if __name__ == "__main__":
    main() 