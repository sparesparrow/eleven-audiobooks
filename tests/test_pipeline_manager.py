"""Test pipeline manager functionality."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from eleven_audiobooks.pipeline_manager import PipelineManager
from eleven_audiobooks.pipeline_state import ProcessingStage

@pytest.mark.asyncio
async def test_pipeline_initialization(pipeline_manager, tmp_path):
    """Test pipeline initialization."""
    assert pipeline_manager.pdf_path == tmp_path / "test.pdf"
    assert pipeline_manager.output_dir == tmp_path / "output"
    assert pipeline_manager.state is not None

@pytest.mark.asyncio
async def test_setup_directories(pipeline_manager):
    """Test directory setup."""
    await pipeline_manager._setup_directories()
    
    # Check directories were created
    assert pipeline_manager.output_dir.exists()
    assert (pipeline_manager.output_dir / "chapters").exists()
    assert (pipeline_manager.output_dir / "translated").exists()
    assert (pipeline_manager.output_dir / "optimized").exists()
    assert (pipeline_manager.output_dir / "audio").exists()
    
    # Check artifacts were added
    assert "dir_chapters" in pipeline_manager.state.artifacts
    assert "dir_translated" in pipeline_manager.state.artifacts
    assert "dir_optimized" in pipeline_manager.state.artifacts
    assert "dir_audio" in pipeline_manager.state.artifacts

@pytest.mark.asyncio
async def test_process_pdf(pipeline_manager):
    """Test PDF processing."""
    # Set up directories
    await pipeline_manager._setup_directories()
    
    # Mock PDF processor
    mock_chapters = {1: "Chapter 1", 2: "Chapter 2"}
    pipeline_manager.pdf_processor.process.return_value = mock_chapters
    
    # Process PDF
    result = await pipeline_manager._process_pdf()
    
    # Check results
    assert result == mock_chapters
    assert pipeline_manager.state.stage == ProcessingStage.PDF_PROCESSING
    assert len(pipeline_manager.state.get_artifacts_by_stage(ProcessingStage.PDF_PROCESSING)) == 2

@pytest.mark.asyncio
async def test_translate_chapters(pipeline_manager):
    """Test chapter translation."""
    # Set up directories
    await pipeline_manager._setup_directories()
    
    # Mock translation pipeline
    mock_chapters = {1: "Translated 1", 2: "Translated 2"}
    pipeline_manager.translation.translate_chapters.return_value = mock_chapters
    
    # Translate chapters
    result = await pipeline_manager._translate_chapters({1: "Chapter 1", 2: "Chapter 2"})
    
    # Check results
    assert result == mock_chapters
    assert pipeline_manager.state.stage == ProcessingStage.TRANSLATION
    assert len(pipeline_manager.state.get_artifacts_by_stage(ProcessingStage.TRANSLATION)) == 2

@pytest.mark.asyncio
async def test_optimize_chapters(pipeline_manager):
    """Test chapter optimization."""
    # Set up directories
    await pipeline_manager._setup_directories()
    
    # Mock optimizer
    pipeline_manager.optimizer.optimize.return_value = "Optimized text"
    
    # Optimize chapters
    result = await pipeline_manager._optimize_chapters({1: "Chapter 1", 2: "Chapter 2"})
    
    # Check results
    assert len(result) == 2
    assert pipeline_manager.state.stage == ProcessingStage.OPTIMIZATION
    assert len(pipeline_manager.state.get_artifacts_by_stage(ProcessingStage.OPTIMIZATION)) == 2

@pytest.mark.asyncio
async def test_generate_audio(pipeline_manager):
    """Test audio generation."""
    # Set up directories
    await pipeline_manager._setup_directories()
    
    # Mock audio generator
    pipeline_manager.audio_gen.generate_chapter.return_value = b"audio_data"
    
    # Generate audio
    chapter_paths = [
        pipeline_manager.output_dir / "optimized" / "chapter_1.txt",
        pipeline_manager.output_dir / "optimized" / "chapter_2.txt"
    ]
    await pipeline_manager._generate_audio(chapter_paths)
    
    # Check results
    assert pipeline_manager.state.stage == ProcessingStage.AUDIO_GENERATION
    assert len(pipeline_manager.state.get_artifacts_by_stage(ProcessingStage.AUDIO_GENERATION)) == 2

@pytest.mark.asyncio
async def test_handle_failure(pipeline_manager):
    """Test failure handling."""
    # Set up error state
    error_msg = "Test error"
    pipeline_manager.state.update_state(
        stage=ProcessingStage.AUDIO_GENERATION,
        error=error_msg
    )
    
    # Mock storage
    pipeline_manager.storage.get_audiobook_url.return_value = "http://example.com/partial"
    
    # Handle failure
    result = await pipeline_manager._handle_failure(Exception(error_msg))
    
    # Check results
    assert result == "http://example.com/partial"
    assert pipeline_manager.state.stage == ProcessingStage.FAILED
    assert pipeline_manager.state.error == error_msg

@pytest.mark.asyncio
async def test_full_pipeline_success(pipeline_manager):
    """Test successful pipeline execution."""
    # Set up directories
    await pipeline_manager._setup_directories()
    
    # Mock pipeline stages
    pipeline_manager._process_pdf = AsyncMock(return_value={1: "Chapter 1"})
    pipeline_manager._translate_chapters = AsyncMock(return_value={1: "Translated"})
    pipeline_manager._optimize_chapters = AsyncMock(return_value=[Path("/test/1.txt")])
    pipeline_manager._generate_audio = AsyncMock()
    pipeline_manager.storage.get_audiobook_url.return_value = "http://example.com/book"
    
    # Run pipeline
    result = await pipeline_manager.process()
    
    # Check results
    assert result == "http://example.com/book"
    assert pipeline_manager.state.stage == ProcessingStage.COMPLETED

@pytest.mark.asyncio
async def test_pipeline_failure(pipeline_manager):
    """Test pipeline failure handling."""
    # Set up directories
    await pipeline_manager._setup_directories()
    
    # Mock PDF processing to fail
    error_msg = "PDF processing failed"
    pipeline_manager._process_pdf = AsyncMock(side_effect=Exception(error_msg))
    pipeline_manager.storage.get_audiobook_url.return_value = "http://example.com/partial"
    
    # Run pipeline
    result = await pipeline_manager.process()
    
    # Check results
    assert result == "http://example.com/partial"
    assert pipeline_manager.state.stage == ProcessingStage.FAILED
    assert pipeline_manager.state.error == error_msg 