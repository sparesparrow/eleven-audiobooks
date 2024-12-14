import io
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

@dataclass
class Chapter:
    number: int
    title: str
    content: List[str]

class PDFProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Pattern to match page markers like "01_Lidske jednani_final.qxd 5.5.2006 16:01 StrÆnka 1"
        self.page_marker_pattern = re.compile(
            r'\d+_[^\.]+\.qxd\s+\d+\.\d+\.\d+\s+\d+:\d+\s+StrÆnka\s+\d+'
        )
        # Pattern to detect chapter headers like "ČÁST PRVNÍ" or numbered chapters
        self.chapter_header_pattern = re.compile(
            r'^(?:ČÁST|KAPITOLA)\s+(?:[IVX]+|PRVNÍ|DRUHÁ|TŘETÍ|ČTVRTÁ|PÁTÁ)',
            re.IGNORECASE
        )

    def process(self, pdf_path: str) -> Dict[int, Chapter]:
        """
        Process PDF file and return chapters with their content.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dict[int, Chapter]: Dictionary mapping chapter numbers to Chapter objects
        """
        raw_text = self._extract_text(pdf_path)
        chapters = self._split_into_chapters(raw_text)
        return self._process_chapters(chapters)

    def _extract_text(self, pdf_path: str) -> str:
        """Extract raw text from PDF file."""
        self.logger.info(f"Extracting text from {pdf_path}")
        output_string = io.StringIO()

        try:
            with open(pdf_path, 'rb') as in_file:
                parser = PDFParser(in_file)
                doc = PDFDocument(parser)
                rsrcmgr = PDFResourceManager()
                device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
                interpreter = PDFPageInterpreter(rsrcmgr, device)

                for page in PDFPage.create_pages(doc):
                    interpreter.process_page(page)

            return output_string.getvalue()

        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {e}")
            raise
        finally:
            output_string.close()

    def _split_into_chapters(self, text: str) -> List[Tuple[str, List[str]]]:
        """
        Split text into chapters based on chapter markers and page breaks.

        Returns:
            List[Tuple[str, List[str]]]: List of tuples containing chapter title and content blocks
        """
        # First split by page markers
        pages = self.page_marker_pattern.split(text)
        pages = [page.strip() for page in pages if page.strip()]

        chapters = []
        current_chapter_title = ""
        current_chapter_content = []

        for page in pages:
            # Look for chapter headers at the start of pages
            lines = page.split('\n')
            first_line = lines[0].strip() if lines else ""

            if self.chapter_header_pattern.match(first_line):
                # If we have content from previous chapter, save it
                if current_chapter_content:
                    chapters.append((current_chapter_title, current_chapter_content))

                current_chapter_title = first_line
                current_chapter_content = ['\n'.join(lines[1:])]
            else:
                current_chapter_content.append(page)

        # Add the last chapter
        if current_chapter_content:
            chapters.append((current_chapter_title, current_chapter_content))

        return chapters

    def _process_chapters(self, raw_chapters: List[Tuple[str, List[str]]]) -> Dict[int, Chapter]:
        """
        Process raw chapter content into clean Chapter objects.
        """
        chapters = {}
        for idx, (title, content_blocks) in enumerate(raw_chapters, 1):
            # Clean up the content
            cleaned_blocks = []
            for block in content_blocks:
                # Remove footnotes (lines starting with numbers)
                lines = [line for line in block.split('\n')
                        if not re.match(r'^\d+\s', line.strip())]

                # Join hyphenated words at line breaks
                text = ' '.join(lines)
                text = re.sub(r'-\s+', '', text)

                # Remove multiple spaces
                text = re.sub(r'\s+', ' ', text)

                if text.strip():
                    cleaned_blocks.append(text.strip())

            chapters[idx] = Chapter(
                number=idx,
                title=title.strip(),
                content=cleaned_blocks
            )

        return chapters

    def save_chapters(self, chapters: Dict[int, Chapter], output_dir: Path):
        """
        Save processed chapters to markdown files.

        Args:
            chapters: Dictionary of processed chapters
            output_dir: Directory to save the markdown files
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
