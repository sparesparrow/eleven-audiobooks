import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pdf_processor import PDFProcessor, Chapter

class TestPDFProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = PDFProcessor(chapter_markers=[
            r'^ČÁST',
            r'^KAPITOLA'
        ])
        self.test_pdf_content = """
[PAGE 1]
ČÁST PRVNÍ
This is the first chapter content.
With multiple lines.

[PAGE 2]
1 This is a footnote
Normal text continues here.
Some-
thing with hyphenation.

[PAGE 3]
KAPITOLA II
Second chapter content.

[PAGE 4]
ČÁST DRUHÁ
Third chapter content.
        """

    @patch('builtins.open')
    @patch('pdf_processor.PyPDF2.PdfReader')
    def test_extract_text(self, mock_reader, mock_open):
        # Setup mock
        mock_page = MagicMock()
        mock_page.extract_text.return_value = self.test_pdf_content
        mock_reader.return_value.pages = [mock_page]
        mock_open.return_value.__enter__.return_value = MagicMock()
        
        result = self.processor._extract_text(Path("test.pdf"))
        
        self.assertIn("ČÁST PRVNÍ", result)
        self.assertIn("KAPITOLA II", result)

    def test_split_into_chapters(self):
        chapters = self.processor._split_into_chapters(self.test_pdf_content)
        
        self.assertEqual(len(chapters), 4)  # Number of chapters found
        self.assertEqual(chapters[1][0], "ČÁST PRVNÍ")  # First real chapter
        self.assertEqual(chapters[2][0], "KAPITOLA II")  # Second chapter
        self.assertEqual(chapters[3][0], "ČÁST DRUHÁ")  # Third chapter

    def test_clean_text_blocks(self):
        blocks = [
            "[PAGE 1]\nSome text",
            "Some-\nthing with hyphenation.",
            "1 This is a footnote",
            "Normal text continues here."
        ]
        
        cleaned = self.processor._clean_text_blocks(blocks)
        
        # Test page marker removal
        self.assertNotIn("[PAGE 1]", cleaned[0])
        # Test hyphenation joining
        self.assertIn("Something with hyphenation.", cleaned)
        # Test normal text preservation
        self.assertIn("Normal text continues here.", cleaned)

    def test_process_chapters(self):
        raw_chapters = [
            ("ČÁST PRVNÍ", ["First chapter content " * 10]),
            ("KAPITOLA II", ["Second chapter content " * 10])
        ]
        
        chapters = self.processor._process_chapters(raw_chapters)
        
        self.assertEqual(len(chapters), 2)
        self.assertIsInstance(chapters[1], Chapter)
        self.assertEqual(chapters[1].title, "ČÁST PRVNÍ")  # Dictionary uses 1-based indexing
        self.assertEqual(chapters[1].number, 1)

    def test_split_long_block(self):
        long_text = "First sentence. " * 50  # Make text longer than max_line_length
        blocks = self.processor._split_long_block(long_text)
        
        self.assertGreater(len(blocks), 1)
        self.assertIn("First sentence", blocks[0])
