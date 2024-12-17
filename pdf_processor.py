import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import PyPDF2

@dataclass
class Chapter:
    """
    Represents a single chapter with its metadata and content.
    
    Attributes:
        number (int): Chapter number in the book
        title (str): Chapter title
        content (List[str]): List of text blocks/paragraphs in the chapter
        page_range (Tuple[int, int]): Start and end page numbers for the chapter
    """
    number: int
    title: str
    content: List[str]
    page_range: Tuple[int, int]

class PDFProcessor:
    def __init__(self, 
                 chapter_markers: List[str] = None, 
                 min_chapter_length: int = 100,
                 max_line_length: int = 500):
        """
        Initialize PDF Processor with configurable parameters.
        
        Args:
            chapter_markers: List of regex patterns to identify chapter starts
            min_chapter_length: Minimum number of characters for a valid chapter
            max_line_length: Maximum length of a single text block
        """
        self.logger = logging.getLogger(__name__)
        self.chapter_markers = chapter_markers or [
            r'^Chapter \d+', 
            r'^CHAPTER \d+', 
            r'^\d+\s*$'  # Numeric chapter numbers
        ]
        self.min_chapter_length = min_chapter_length
        self.max_line_length = max_line_length

    def process(self, pdf_path: Path) -> Dict[int, Chapter]:
        """
        Main method to process PDF and extract chapters.
        
        Args:
            pdf_path: Path to the input PDF file
        
        Returns:
            Dictionary of processed chapters
        """
        try:
            raw_text = self._extract_text(pdf_path)
            raw_chapters = self._split_into_chapters(raw_text)
            processed_chapters = self._process_chapters(raw_chapters)
            
            self.logger.info(f"Processed {len(processed_chapters)} chapters from {pdf_path}")
            return processed_chapters
        
        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise

    def _extract_text(self, pdf_path: Path) -> str:
        """
        Extract raw text from PDF, preserving page numbers and structure.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Extracted text as a single string
        """
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            full_text = []
            
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                # Add page number marker for reference
                full_text.append(f"[PAGE {page_num}]\n{page_text}")
        
        return "\n".join(full_text)

    def _split_into_chapters(self, text: str) -> List[Tuple[str, List[str]]]:
        """
        Split text into chapters using predefined markers.
        
        Args:
            text: Full extracted text
        
        Returns:
            List of (chapter_title, chapter_content_blocks)
        """
        chapters = []
        current_chapter_title = "Untitled Chapter"
        current_chapter_content = []
        
        for line in text.split('\n'):
            # Check for chapter markers
            if any(re.search(marker, line.strip()) for marker in self.chapter_markers):
                # Save previous chapter if it exists and meets minimum length
                if current_chapter_content and ''.join(current_chapter_content).strip():
                    chapters.append((current_chapter_title, current_chapter_content))
                
                # Start new chapter
                current_chapter_title = line.strip()
                current_chapter_content = []
            else:
                current_chapter_content.append(line)
        
        # Add last chapter
        if current_chapter_content:
            chapters.append((current_chapter_title, current_chapter_content))
        
        return chapters

    def _process_chapters(self, raw_chapters: List[Tuple[str, List[str]]]) -> Dict[int, Chapter]:
        """
        Process raw chapter content into clean Chapter objects.
        
        Args:
            raw_chapters: List of (title, content_blocks)
        
        Returns:
            Dictionary of processed chapters
        """
        chapters = {}
        for idx, (title, content_blocks) in enumerate(raw_chapters, 1):
            # Clean and split content into manageable blocks
            cleaned_blocks = self._clean_text_blocks(content_blocks)
            
            # Skip chapters that are too short
            if sum(len(block) for block in cleaned_blocks) < self.min_chapter_length:
                self.logger.warning(f"Skipping short chapter {idx}: {title}")
                continue
            
            chapters[idx] = Chapter(
                number=idx,
                title=title.strip(),
                content=cleaned_blocks,
                page_range=(0, 0)  # TODO: Implement page range tracking
            )
        
        return chapters

    def _clean_text_blocks(self, blocks: List[str]) -> List[str]:
        """
        Clean and normalize text blocks.
        
        Args:
            blocks: Raw text blocks
        
        Returns:
            Cleaned and processed text blocks
        """
        cleaned_blocks = []
        for block in blocks:
            # Remove page markers
            block = re.sub(r'\[PAGE \d+\]', '', block)
            
            # Remove footnotes and page numbers
            block = re.sub(r'^\d+\s*$', '', block)
            
            # Join hyphenated words
            block = re.sub(r'-\s+', '', block)
            
            # Normalize whitespace
            block = re.sub(r'\s+', ' ', block).strip()
            
            # Split long blocks
            if len(block) > self.max_line_length:
                # Split by sentences or at max length
                block_parts = self._split_long_block(block)
                cleaned_blocks.extend(block_parts)
            elif block:
                cleaned_blocks.append(block)
        
        return cleaned_blocks

    def _split_long_block(self, block: str) -> List[str]:
        """
        Split long text blocks into smaller, manageable chunks.
        
        Args:
            block: Long text block
        
        Returns:
            List of split text blocks
        """
        # Try to split by sentence
        sentences = re.split(r'(?<=[.!?])\s+', block)
        result = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.max_line_length:
                result.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence
        
        if current_chunk:
            result.append(current_chunk.strip())
        
        return result

    def save_chapters(self, chapters: Dict[int, Chapter], output_dir: Path):
        """
        Save processed chapters to markdown files.
        
        Args:
            chapters: Dictionary of processed chapters
            output_dir: Directory to save markdown files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for chapter_num, chapter in chapters.items():
            filename = output_dir / f"chapter_{chapter_num:02d}.md"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {chapter.title}\n\n")
                for block in chapter.content:
                    f.write(f"{block}\n\n")

            self.logger.info(f"Saved chapter {chapter_num} to {filename}")
