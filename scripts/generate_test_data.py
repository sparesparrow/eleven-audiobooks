#!/usr/bin/env python3
"""Generate test data for the Eleven Audiobooks project."""

import os
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_test_pdf(output_path: Path, num_chapters: int = 3) -> None:
    """Create a test PDF file with multiple chapters."""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    # Sample text for each chapter
    chapter_text = [
        "This is a sample chapter with some text that will be processed.",
        "Here's another chapter with different content to test translation.",
        "The final chapter contains text that will be optimized for speech."
    ]
    
    for i in range(num_chapters):
        # Add chapter title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, 750, f"Chapter {i+1}")
        
        # Add chapter content
        c.setFont("Helvetica", 12)
        text = chapter_text[i % len(chapter_text)]
        y_position = 700
        
        # Split text into lines
        words = text.split()
        line = []
        for word in words:
            line.append(word)
            if len(" ".join(line)) > 60:  # Approximate line length
                c.drawString(72, y_position, " ".join(line[:-1]))
                line = [line[-1]]
                y_position -= 20
        
        if line:
            c.drawString(72, y_position, " ".join(line))
        
        # Add page number
        c.setFont("Helvetica", 10)
        c.drawString(300, 50, f"Page {i+1}")
        
        c.showPage()
    
    c.save()


def create_test_data() -> None:
    """Create all necessary test data."""
    # Create test data directory if it doesn't exist
    test_data_dir = Path(__file__).parent.parent / "tests" / "data"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test PDF
    pdf_path = test_data_dir / "sample.pdf"
    create_test_pdf(pdf_path)
    print(f"Created test PDF at {pdf_path}")
    
    # Create directories for test artifacts
    artifacts_dir = test_data_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    for subdir in ["chapters", "translated", "optimized", "audio"]:
        (artifacts_dir / subdir).mkdir(exist_ok=True)
        print(f"Created directory: {artifacts_dir / subdir}")


if __name__ == "__main__":
    create_test_data() 