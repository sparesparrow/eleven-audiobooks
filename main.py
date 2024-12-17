import asyncio
import logging
import os
import sys
from pathlib import Path

from audio_generator import AudioGenerator
from batch_text_optimizer import BatchTextOptimizer
from pdf_processor import PDFProcessor
from storage_engine import StorageEngine
from translation_pipeline import TranslationPipeline

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
        self.output_dir = output_dir
        
        # Initialize components
        self.storage_engine = StorageEngine(mongo_uri)
        self.pdf_processor = PDFProcessor()
        self.translation_pipeline = TranslationPipeline()
        self.text_optimizer = BatchTextOptimizer()
        self.audio_generator = AudioGenerator()

    async def process_book(self) -> str:
        """
        Main processing pipeline for converting PDF to audiobook
        
        Returns:
            URL or path to the generated audiobook
        """
        try:
            # 1. PDF Processing: Extract and chunk text
            original_chunks = self.pdf_processor.process(self.pdf_path)
            self.storage_engine.store_original(original_chunks)
            logger.info(f"Stored {len(original_chunks)} original text chunks")

            # 2. Translation: Translate chunks
            translated_chunks = await self.translation_pipeline.translate(original_chunks)
            self.storage_engine.store_translated(translated_chunks)
            logger.info(f"Stored {len(translated_chunks)} translated text chunks")

            # 3. Optimization: Enhance text for speech
            optimized_chunks = []
            for chunk in translated_chunks:
                optimized = await self.text_optimizer.optimize_chapter(chunk)
                optimized_chunks.append(optimized)
                self.storage_engine.store_optimized(optimized)
            logger.info(f"Optimized {len(optimized_chunks)} text chunks")

            # 4. Audio Generation: Create audio files
            audio_responses = []
            for chunk in optimized_chunks:
                audio_response = await self.audio_generator.generate_chapter(chunk)
                audio_id = self.storage_engine.store_audio(audio_response)
                audio_responses.append(audio_id)
            logger.info(f"Generated {len(audio_responses)} audio chapters")

            # 5. Get final audiobook URL
            audiobook_url = self.storage_engine.get_audiobook_url(audio_responses[-1])
            return audiobook_url

        except Exception as e:
            logger.error(f"Error processing audiobook: {e}")
            raise

async def main():
    # Example usage
    pdf_path = Path('./input/book.pdf')
    processor = AudiobookProcessor(pdf_path)
    
    try:
        audiobook_url = await processor.process_book()
        print(f"Audiobook generated: {audiobook_url}")
    except Exception as e:
        print(f"Audiobook generation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
