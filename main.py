import asyncio
import logging
import os
import sys
from pathlib import Path

from pipeline_manager import PipelineManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler('audiobook.log')]
)
logger = logging.getLogger(__name__)

def load_config() -> dict:
    """Load configuration from environment variables."""
    return {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        "DEEPL_API_KEY": os.getenv("DEEPL_API_KEY"),
        "NLLB_API_KEY": os.getenv("NLLB_API_KEY"),
        "AYA_API_KEY": os.getenv("AYA_API_KEY"),
        "VOICE_ID": os.getenv("VOICE_ID", "OJtLHqR5g0hxcgc27j7C"),
        "MONGO_URI": os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    }

async def process_book(pdf_path: Path, translate: bool = False) -> str:
    """
    Process a PDF book into an audiobook.
    
    Args:
        pdf_path: Path to the PDF file
        translate: Whether to translate the content
        
    Returns:
        URL to the generated audiobook
    """
    try:
        # Load configuration
        config = load_config()
        
        # Setup output directory
        output_dir = Path('./data/processed')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize pipeline
        pipeline = PipelineManager(
            pdf_path=pdf_path,
            output_dir=output_dir,
            mongo_uri=config["MONGO_URI"],
            config=config
        )
        
        # Process book
        audiobook_url = await pipeline.process(translate=translate)
        
        if audiobook_url:
            logger.info(f"Successfully generated audiobook: {audiobook_url}")
            return audiobook_url
        else:
            logger.error("Failed to generate audiobook")
            return None
            
    except Exception as e:
        logger.error(f"Error processing book: {str(e)}")
        raise

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <pdf_path> [--translate]")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    translate = "--translate" in sys.argv
    
    try:
        audiobook_url = asyncio.run(process_book(pdf_path, translate))
        if audiobook_url:
            print(f"Audiobook generated successfully: {audiobook_url}")
        else:
            print("Failed to generate audiobook")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
