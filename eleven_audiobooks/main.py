"""Main module for audiobook generation."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from pymongo import MongoClient

from .pipeline_manager import PipelineManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config() -> Dict[str, str]:
    """
    Load configuration from environment.

    Returns:
        Dictionary of configuration values

    Raises:
        SystemExit: If required environment variables are missing
    """
    required_keys = [
        "ANTHROPIC_API_KEY",
        "ELEVENLABS_API_KEY",
        "MONGO_URI"
    ]
    
    optional_keys = [
        "DEEPL_API_KEY",
        "NLLB_API_KEY",
        "AYA_API_KEY",
        "VOICE_ID"
    ]
    
    config = {}
    
    # Load required keys
    for key in required_keys:
        value = os.getenv(key)
        if not value:
            raise SystemExit(f"Missing required environment variable: {key}")
        config[key] = value
        
    # Load optional keys
    for key in optional_keys:
        value = os.getenv(key)
        if value:
            config[key] = value
            
    return config


async def process_book(
    pdf_path: Path,
    output_dir: Optional[Path] = None,
    translate: bool = False
) -> Optional[str]:
    """
    Process a book through the pipeline.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory (defaults to pdf directory)
        translate: Whether to translate content

    Returns:
        URL to generated audiobook or None if processing failed
    """
    # Set default output directory
    if output_dir is None:
        output_dir = pdf_path.parent / "output"
        
    # Load configuration
    config = load_config()
    
    # Initialize MongoDB client
    client = MongoClient(config["MONGO_URI"])
    db = client.audiobooks
    
    try:
        # Initialize pipeline
        pipeline = PipelineManager(
            pdf_path=pdf_path,
            output_dir=output_dir,
            mongo_db=db,
            config=config
        )
        
        # Process book
        return await pipeline.process(translate=translate)
        
    except Exception as e:
        logger.error("Error processing book: %s", str(e))
        return None
        
    finally:
        client.close()


async def main() -> None:
    """Main entry point."""
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Generate audiobook from PDF",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to PDF file"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        help="Output directory (defaults to pdf directory)"
    )
    parser.add_argument(
        "-t", "--translate",
        action="store_true",
        help="Translate content before generating audio"
    )
    args = parser.parse_args()
    
    # Check PDF exists
    if not args.pdf_path.is_file():
        raise SystemExit(f"PDF file not found: {args.pdf_path}")
        
    try:
        # Process book
        url = await process_book(
            pdf_path=args.pdf_path,
            output_dir=args.output_dir,
            translate=args.translate
        )
        
        if url:
            print(f"Audiobook available at: {url}")
        else:
            print("Failed to generate audiobook")
            raise SystemExit(1)
            
    except KeyboardInterrupt:
        print("\nProcessing interrupted")
        raise SystemExit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main()) 