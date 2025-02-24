"""Tests for the main entry point."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from eleven_audiobooks.main import load_config, process_book, main


def test_load_config():
    """Test configuration loading from environment variables."""
    # Set test environment variables
    test_env = {
        "ANTHROPIC_API_KEY": "test-anthropic",
        "ELEVENLABS_API_KEY": "test-elevenlabs",
        "DEEPL_API_KEY": "test-deepl",
        "NLLB_API_KEY": "test-nllb",
        "AYA_API_KEY": "test-aya",
        "VOICE_ID": "test-voice",
        "MONGO_URI": "mongodb://test:27017/"
    }
    
    with patch.dict(os.environ, test_env):
        config = load_config()
        
        # Check all values are loaded correctly
        assert config["ANTHROPIC_API_KEY"] == "test-anthropic"
        assert config["ELEVENLABS_API_KEY"] == "test-elevenlabs"
        assert config["DEEPL_API_KEY"] == "test-deepl"
        assert config["NLLB_API_KEY"] == "test-nllb"
        assert config["AYA_API_KEY"] == "test-aya"
        assert config["VOICE_ID"] == "test-voice"
        assert config["MONGO_URI"] == "mongodb://test:27017/"


def test_load_config_defaults():
    """Test configuration loading with default values."""
    # Environment variables are already mocked in conftest.py
    config = load_config()
    
    # Check required keys
    assert config["ANTHROPIC_API_KEY"] == "test_anthropic_key"
    assert config["ELEVENLABS_API_KEY"] == "test_elevenlabs_key"
    
    # Check optional keys
    assert config["DEEPL_API_KEY"] == "test_deepl_key"
    assert config["NLLB_API_KEY"] == "test_nllb_key"
    assert config["AYA_API_KEY"] == "test_aya_key"
    assert config["VOICE_ID"] == "test_voice_id"
    assert config["MONGO_URI"] == "mongodb://localhost:27017/"


def test_load_config_missing_keys():
    """Test configuration loading with missing required keys."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit):
            load_config()


@pytest.mark.asyncio
async def test_process_book_success():
    """Test successful book processing."""
    # Create test files
    pdf_path = Path("test.pdf")
    output_dir = Path("output")
    
    # Mock pipeline manager
    with patch("eleven_audiobooks.main.PipelineManager") as mock_manager:
        # Configure mock
        instance = mock_manager.return_value
        instance.process = AsyncMock(return_value="http://example.com/audiobook")
        
        # Process book
        result = await process_book(pdf_path, output_dir)
        
        # Check result
        assert result == "http://example.com/audiobook"
        instance.process.assert_called_once_with(translate=False)


@pytest.mark.asyncio
async def test_process_book_failure():
    """Test book processing failure."""
    # Create test files
    pdf_path = Path("test.pdf")
    output_dir = Path("output")
    
    # Mock pipeline manager
    with patch("eleven_audiobooks.main.PipelineManager") as mock_manager:
        # Configure mock to fail
        instance = mock_manager.return_value
        instance.process = AsyncMock(side_effect=Exception("Processing failed"))
        
        # Process book
        result = await process_book(pdf_path, output_dir)
        
        # Check result
        assert result is None


@pytest.mark.asyncio
async def test_process_book_no_result():
    """Test book processing with no result."""
    # Mock pipeline manager to return None
    mock_pipeline = AsyncMock()
    mock_pipeline.process.return_value = None
    
    with patch("eleven_audiobooks.main.PipelineManager", return_value=mock_pipeline):
        # Process book
        result = await process_book(Path("test.pdf"))
        
        # Check result
        assert result is None


@pytest.mark.asyncio
async def test_main_missing_args():
    """Test main function with missing arguments."""
    with patch("sys.argv", ["main.py"]):
        with pytest.raises(SystemExit):
            await main()


@pytest.mark.asyncio
async def test_main_success():
    """Test main function with successful processing."""
    # Create test PDF
    pdf_path = Path("test.pdf")
    
    # Mock command line arguments
    with patch("sys.argv", ["main.py", str(pdf_path)]), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("eleven_audiobooks.main.process_book", new_callable=AsyncMock) as mock_process:
        # Configure mock
        mock_process.return_value = "http://example.com/audiobook"
        
        # Run main
        await main()
        
        # Check process_book was called
        mock_process.assert_called_once_with(
            pdf_path=pdf_path,
            output_dir=None,
            translate=False
        )


@pytest.mark.asyncio
async def test_main_file_not_found():
    """Test main function with non-existent PDF file."""
    with patch("sys.argv", ["main.py", "nonexistent.pdf"]), \
         patch("pathlib.Path.is_file", return_value=False):
        with pytest.raises(SystemExit):
            await main()


@pytest.mark.asyncio
async def test_main_failure():
    """Test main function with processing failure."""
    # Mock process_book to raise an exception
    mock_process = AsyncMock(side_effect=Exception("Processing failed"))
    
    with patch("sys.argv", ["main.py", "test.pdf"]), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("eleven_audiobooks.main.process_book", mock_process):
        # Run main and check error handling
        await main()
        
        # Verify process_book was called
        mock_process.assert_called_once() 