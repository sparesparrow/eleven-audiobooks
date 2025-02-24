"""PDF processing component."""

import logging
import re
from pathlib import Path
from typing import Dict, List

from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF text extraction and processing."""

    def process(self, pdf_path: Path) -> Dict[int, str]:
        """
        Extract and process text from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary mapping chapter numbers to text content

        Raises:
            Exception: If PDF processing fails
        """
        try:
            # Read PDF
            reader = PdfReader(pdf_path)
            
            # Extract text from pages
            pages = [page.extract_text() for page in reader.pages]
            
            # Identify chapters
            chapters = self._identify_chapters(pages)
            
            # Clean and format text
            return self._clean_text(chapters)
            
        except Exception as e:
            logger.error("Failed to process PDF: %s", str(e))
            raise

    def _identify_chapters(self, pages: List[str]) -> Dict[int, List[str]]:
        """
        Identify chapter boundaries in pages.

        Args:
            pages: List of page text content

        Returns:
            Dictionary mapping chapter numbers to lists of page content
        """
        chapters = {}
        current_chapter = 1
        current_pages = []
        
        for page in pages:
            # Check for chapter marker
            if self._is_chapter_start(page):
                # Save previous chapter if it exists
                if current_pages:
                    chapters[current_chapter] = current_pages
                    current_chapter += 1
                    current_pages = []
            
            current_pages.append(page)
        
        # Add final chapter
        if current_pages:
            chapters[current_chapter] = current_pages
        
        return chapters

    def _is_chapter_start(self, text: str) -> bool:
        """
        Check if text indicates start of new chapter.

        Args:
            text: Page text content

        Returns:
            True if text indicates chapter start
        """
        # Common chapter markers with more pattern variations
        patterns = [
            r'^\s*chapter\s+\d+',  # Chapter followed by number
            r'^\s*chapter\s+[ivxlcdm]+',  # Chapter followed by Roman numeral
            r'^\s*chapter\s+[a-z\s]+$',  # Chapter followed by text like "one", "two"
            r'^\s*section\s+\d+(\.\d+)*',  # Section with optional decimal
            r'^\s*part\s+\d+',  # Part followed by number
            r'^\s*part\s+[ivxlcdm]+',  # Part followed by Roman numeral
            r'^\s*\d+\.\s+[A-Z]',  # Numbered headings like "1. Title"
            r'^\s*[A-Z][A-Z\s]+$'  # All caps heading (potential chapter title)
        ]
        
        # Check first few lines
        first_lines = text.split("\n")[:5]
        
        for line in first_lines:
            line = line.strip().lower()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for explicit chapter markers
            for pattern in patterns:
                if re.match(pattern, line):
                    return True
            
            # Check for centered short lines that might be chapter titles
            # If we find a short line (3-30 chars) surrounded by empty lines
            if 3 <= len(line) <= 30 and line[0].isupper():
                line_idx = first_lines.index(line.strip())
                if (line_idx == 0 or not first_lines[line_idx-1].strip()) and \
                   (line_idx == len(first_lines)-1 or not first_lines[line_idx+1].strip()):
                    return True
        
        return False

    def _clean_text(self, chapters: Dict[int, List[str]]) -> Dict[int, str]:
        """
        Clean and format chapter text.

        Args:
            chapters: Dictionary of chapter content

        Returns:
            Dictionary of cleaned chapter text
        """
        cleaned = {}
        
        for num, pages in chapters.items():
            # Join pages
            text = "\n".join(pages)
            
            # Remove headers and footers
            text = self._remove_headers_footers(text)
            
            # Clean formatting
            text = self._clean_formatting(text)
            
            cleaned[num] = text
        
        return cleaned

    def _remove_headers_footers(self, text: str) -> str:
        """
        Remove headers and footers from text.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            # Skip page numbers
            if line.strip().isdigit():
                continue
                
            # Skip common headers/footers
            if any(marker in line.lower() for marker in ["page", "chapter", "book title"]):
                continue
            
            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)

    def _clean_formatting(self, text: str) -> str:
        """
        Clean text formatting.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Fix common OCR issues using context-aware corrections
        # Instead of blanket replacements which can corrupt numeric values
        text = self._smart_ocr_correction(text)
        
        # Add paragraph breaks after sentences, but preserve list formatting
        text = text.replace(". ", ".\n\n")
        text = text.replace("\n\n• ", "\n• ")
        text = text.replace("\n\n- ", "\n- ")
        text = text.replace("\n\n1. ", "\n1. ")
        
        return text.strip()
        
    def _smart_ocr_correction(self, text: str) -> str:
        """
        Perform smart OCR correction based on context.
        
        Args:
            text: Text to correct
            
        Returns:
            Corrected text
        """
        # Fix standalone "1" that should be "I" (common in OCR)
        # Only replace when it's a standalone "1" surrounded by spaces or punctuation
        text = re.sub(r'(?<=[\s.,;:?!])1(?=[\s.,;:?!])', 'I', text)
        
        # Fix standalone "0" that should be "O" (common in OCR)
        # Only replace when it's a standalone "0" surrounded by spaces or punctuation
        text = re.sub(r'(?<=[\s.,;:?!])0(?=[\s.,;:?!])', 'O', text)
        
        # Fix l/I confusion (lowercase L vs uppercase I)
        text = re.sub(r'(?<=[\s.,;:?!])l(?=[\s.,;:?!])', 'I', text)
        
        # Preserve numbers within numeric contexts
        # No corrections inside numbers, dates, times, etc.
        
        return text
