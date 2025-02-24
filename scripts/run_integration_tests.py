#!/usr/bin/env python3
"""Run integration tests for the Eleven Audiobooks project."""

import asyncio
import logging
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

from eleven_audiobooks.pipeline_manager import PipelineManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_integration_test(pdf_path: Path, output_dir: Path) -> bool:
    """
    Run an integration test of the full pipeline.
    
    Args:
        pdf_path: Path to test PDF file
        output_dir: Directory for test outputs
        
    Returns:
        bool: True if test passed, False otherwise
    """
    try:
        # Initialize pipeline
        pipeline = PipelineManager(
            pdf_path=pdf_path,
            output_dir=output_dir,
            mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017/"),
            config={
                "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
                "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
                "DEEPL_API_KEY": os.getenv("DEEPL_API_KEY")
            }
        )
        
        # Process book
        logger.info("Starting pipeline processing")
        url = await pipeline.process(translate=True)
        
        if not url:
            logger.error("Pipeline failed to produce audiobook URL")
            return False
        
        logger.info(f"Pipeline completed successfully. Audiobook URL: {url}")
        
        # Verify outputs
        logger.info("Verifying outputs...")
        
        # Check chapter files
        chapters_dir = output_dir / "chapters"
        if not any(chapters_dir.glob("*.md")):
            logger.error("No chapter files found")
            return False
        
        # Check translated files
        translated_dir = output_dir / "translated"
        if not any(translated_dir.glob("*.md")):
            logger.error("No translated files found")
            return False
        
        # Check optimized files
        optimized_dir = output_dir / "optimized"
        if not any(optimized_dir.glob("*.md")):
            logger.error("No optimized files found")
            return False
        
        # Check audio files
        audio_dir = output_dir / "audio"
        if not any(audio_dir.glob("*.mp3")):
            logger.error("No audio files found")
            return False
        
        logger.info("All outputs verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        return False


def main() -> int:
    """Run integration tests."""
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return 1
    
    # Setup test paths
    test_data_dir = Path(__file__).parent.parent / "tests" / "data"
    pdf_path = test_data_dir / "sample.pdf"
    output_dir = test_data_dir / "integration_test_output"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run integration test
    success = asyncio.run(run_integration_test(pdf_path, output_dir))
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 