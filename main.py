import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List

from audio_generator import AudioGenerator
from batch_text_optimizer import BatchTextOptimizer
from pdf_processor import PDFProcessor
from storage_engine import StorageEngine
from translation_pipeline import TranslationPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler('audiobook.log')]
)
logger = logging.getLogger(__name__)

class AudiobookProcessor:
    def __init__(self, 
                 pdf_path: Path, 
                 mongo_uri: str = 'mongodb://localhost:27017/', 
                 output_dir: Path = Path('./output')):
        """
        Initialize the audiobook processing pipeline
        
        Args:
            pdf_path: Path to the input PDF file
            mongo_uri: MongoDB connection string
            output_dir: Directory to store processed files
        """
        self.pdf_path = pdf_path
        if not pdf_path.exists() or not pdf_path.is_file() or pdf_path.stat().st_size == 0:
            raise ValueError(f"Invalid PDF file: {pdf_path}")
        
        self.output_dir = output_dir
        
        # Initialize components
        self.storage_engine = StorageEngine(mongo_uri=mongo_uri)
        self.pdf_processor = PDFProcessor()
        self.translation_pipeline = TranslationPipeline(
            deepl_api_key=os.getenv("DEEPL_API_KEY"),
            nllb_api_key=os.getenv("NLLB_API_KEY"),
            aya_api_key=os.getenv("AYA_API_KEY")
        )
        self.text_optimizer = BatchTextOptimizer(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.audio_generator = AudioGenerator(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id="OJtLHqR5g0hxcgc27j7C"  # Default voice ID
        )

    async def process_book(self, translate: bool = False) -> str:
        """
        Main processing pipeline for converting PDF to audiobook
        
        Args:
            translate: Whether to translate the text or not
        
        Returns:
            URL or path to the generated audiobook
        """
        try:
            output_dir = await self._setup_output_directory()
            chapters = await self._process_pdf(output_dir)
            
            if translate:
                chapters = await self._translate_chapters(chapters, output_dir)
            
            optimized_paths = await self._optimize_chapters(chapters, output_dir)
            audio_responses = await self._generate_audio(optimized_paths)
            
            return self.storage_engine.get_audiobook_url(audio_responses[-1])

        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing audiobook: {e}")
            raise

    async def _setup_output_directory(self) -> Path:
        """Create and setup output directory structure."""
        output_dir = Path('./data/LidskeJednani/markdown')
        logger.info(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    async def _process_pdf(self, output_dir: Path) -> List:
        """Process PDF file into chapters."""
        logger.info(f"Processing PDF: {self.pdf_path}")
        chapters = self.pdf_processor.process(self.pdf_path)
        self.pdf_processor.save_chapters(chapters, output_dir)
        logger.info(f"Saved {len(chapters)} chapters to {output_dir}")
        return chapters

    async def _translate_chapters(self, chapters: List, output_dir: Path) -> List:
        """Translate chapters if required."""
        translated_dir = output_dir / 'translated'
        translated_dir.mkdir(exist_ok=True)
        chapters = await self.translation_pipeline.translate_chapters(chapters, translated_dir)
        logger.info(f"Translated chapters saved to {translated_dir}")
        return chapters

    async def _optimize_chapters(self, chapters: List, output_dir: Path) -> List[Path]:
        """Optimize chapters for speech synthesis."""
        optimized_paths = []
        for chapter_num, chapter in enumerate(chapters, 1):
            chapter_path = output_dir / f"chapter_{chapter_num:02d}.md"
            optimized_path = await self.text_optimizer.optimize_chapter(chapter_path)
            optimized_paths.append(optimized_path)
            logger.info(f"Optimized chapter {chapter_num}")
        return optimized_paths

    async def _generate_audio(self, optimized_paths: List[Path]) -> List[str]:
        """Generate audio files from optimized text."""
        audio_responses = []
        for path in optimized_paths:
            audio_response = await self.audio_generator.generate_chapter(path)
            audio_id = self.storage_engine.store_audio(audio_response)
            audio_responses.append(audio_id)
        logger.info(f"Generated {len(audio_responses)} audio chapters")
        return audio_responses

async def main():
    # Example usage
    pdf_path = Path('./data/LidskeJednani.pdf')
    processor = AudiobookProcessor(pdf_path)
    try:
        audiobook_url = await processor.process_book()
        print(f"Audiobook generated: {audiobook_url}")
    except Exception as e:
        print(f"Audiobook generation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
