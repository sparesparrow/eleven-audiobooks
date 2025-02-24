"""Test configuration and fixtures for the Eleven Audiobooks project."""

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from pymongo import MongoClient
from pymongo.database import Database
from unittest.mock import MagicMock, AsyncMock

from eleven_audiobooks.pipeline_manager import PipelineManager
from eleven_audiobooks.pipeline_state import PipelineState, ProcessingStage


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    env_vars = {
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "ELEVENLABS_API_KEY": "test_elevenlabs_key",
        "DEEPL_API_KEY": "test_deepl_key",
        "NLLB_API_KEY": "test_nllb_key",
        "AYA_API_KEY": "test_aya_key",
        "VOICE_ID": "test_voice_id",
        "MONGO_URI": "mongodb://localhost:27017/"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for test outputs."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_pdf_path() -> Path:
    """Get path to sample PDF file for testing."""
    return Path(__file__).parent / "data" / "sample.pdf"


@pytest.fixture
def mock_config() -> dict:
    """Create mock configuration for testing."""
    return {
        "ANTHROPIC_API_KEY": "mock-anthropic-key",
        "ELEVENLABS_API_KEY": "mock-elevenlabs-key",
        "DEEPL_API_KEY": "mock-deepl-key",
        "VOICE_ID": "mock-voice-id"
    }


@pytest.fixture
async def mongodb():
    """Create a MongoDB client for testing."""
    # Create mock MongoDB client
    client = MagicMock(spec=MongoClient)
    db = MagicMock(spec=Database)
    client.audiobooks = db
    
    yield db
    
    # No need to clean up since we're using a mock


@pytest.fixture
def pipeline_state():
    """Create a pipeline state instance for testing."""
    return PipelineState()


@pytest.fixture
def pipeline_manager(tmp_path, mongodb):
    """Create a pipeline manager instance for testing."""
    # Create test paths
    pdf_path = tmp_path / "test.pdf"
    output_dir = tmp_path / "output"
    
    # Create mock components
    manager = PipelineManager(
        pdf_path=pdf_path,
        output_dir=output_dir,
        mongo_db=mongodb
    )
    
    # Mock component methods
    manager.pdf_processor = MagicMock()
    manager.translation = AsyncMock()
    manager.optimizer = MagicMock()
    manager.audio_gen = AsyncMock()
    manager.storage = MagicMock()
    
    return manager 