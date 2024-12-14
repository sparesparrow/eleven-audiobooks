import asyncio
import logging
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


async def process_book(pdf_path: Path):
    logger.info(f"Starting audiobook generation for {pdf_path}")

    # Initialize components
    pdf_processor = PDFProcessor()
    translation_pipeline = TranslationPipeline()
    storage_engine = StorageEngine()
    audio_generator = AudioGenerator(api_key="", voice_id="OJtLHqR5g0hxcgc27j7C")
    optimizer = BatchTextOptimizer()

    try:
        # Process PDF
        logger.info("Processing PDF...")
        markdown_chunks = pdf_processor.process(pdf_path)
        
        # Translate content
        logger.info("Translating content...")
        translated_chunks = translation_pipeline.translate(markdown_chunks)
        
        # Store original and translated content
        logger.info("Storing original and translated content...")
        storage_engine.store_original(markdown_chunks)
        storage_engine.store_translated(translated_chunks)

        # Optimize translated content 
        logger.info("Optimizing translated content...")
        for chunk in translated_chunks:
            optimized_path = await optimizer.optimize_chapter(chunk)
            storage_engine.store_optimized(optimized_path)

        # Generate audio from optimized text
        logger.info("Generating audio...")
        for optimized_path in storage_engine.get_optimized_chapters():
            audio_generator.generate_chapter(optimized_path)
            
        # Provide audiobook
        logger.info("Generating audiobook...")
        audiobook_url = storage_engine.get_audiobook_url()
        logger.info(f"Audiobook generation completed. URL: {audiobook_url}")
        return audiobook_url

    except Exception as e:
        logger.error(f"Audiobook generation failed: {e}")
        raise


async def main():
    try:
        if len(sys.argv) != 2:
            print("Usage: python main.py <pdf_path>")
            sys.exit(1)

        pdf_path = Path(sys.argv[1])
        if not pdf_path.exists() or not pdf_path.is_file():
            print(f"Error: {pdf_path} does not exist or is not a file")
            sys.exit(1)

        await process_book(pdf_path)

    except Exception as e:
        logger.error(f"Process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
