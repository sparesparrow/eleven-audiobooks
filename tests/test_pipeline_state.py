"""Tests for the pipeline state management system."""

from pathlib import Path

import pytest

from eleven_audiobooks.pipeline_state import PipelineState, ProcessingStage


def test_initial_state(pipeline_state: PipelineState):
    """Test initial pipeline state."""
    assert pipeline_state.state.stage == ProcessingStage.INITIALIZED
    assert pipeline_state.state.current_chapter == 0
    assert pipeline_state.state.total_chapters == 0
    assert pipeline_state.state.error is None
    assert pipeline_state.state.artifacts == {}
    assert len(pipeline_state.history) == 0


def test_update_state(pipeline_state: PipelineState):
    """Test updating pipeline state."""
    # Update state
    pipeline_state.update_state(
        stage=ProcessingStage.PDF_PROCESSING,
        current_chapter=1
    )
    
    # Check current state
    assert pipeline_state.state.stage == ProcessingStage.PDF_PROCESSING
    assert pipeline_state.state.current_chapter == 1
    
    # Check history
    assert len(pipeline_state.history) == 1
    assert pipeline_state.history[0].stage == ProcessingStage.INITIALIZED


def test_error_state(pipeline_state: PipelineState):
    """Test error state handling."""
    error_message = "Test error"
    pipeline_state.update_state(
        stage=ProcessingStage.PDF_PROCESSING,
        error=error_message
    )
    
    assert pipeline_state.state.stage == ProcessingStage.FAILED
    assert pipeline_state.state.error == error_message
    assert not pipeline_state.can_proceed()


def test_artifacts(pipeline_state: PipelineState):
    """Test artifact management."""
    # Add artifacts
    test_path = Path("/test/path")
    pipeline_state.add_artifact("pdf_chapter_1", test_path)
    
    # Check artifact was added
    assert pipeline_state.state.artifacts["pdf_chapter_1"] == test_path
    
    # Get artifacts by stage
    pdf_artifacts = pipeline_state.get_artifacts_by_stage(
        ProcessingStage.PDF_PROCESSING
    )
    assert len(pdf_artifacts) == 1
    assert pdf_artifacts[0] == test_path
    
    # Check non-existent stage
    empty_artifacts = pipeline_state.get_artifacts_by_stage(
        ProcessingStage.TRANSLATION
    )
    assert len(empty_artifacts) == 0


def test_progress_tracking(pipeline_state: PipelineState):
    """Test progress tracking."""
    # Set total chapters
    pipeline_state.state.total_chapters = 10
    
    # Check initial progress
    assert pipeline_state.get_progress() == 0.0
    
    # Update progress
    pipeline_state.update_state(
        stage=ProcessingStage.PDF_PROCESSING,
        current_chapter=5
    )
    assert pipeline_state.get_progress() == 50.0
    
    # Complete all chapters
    pipeline_state.update_state(
        stage=ProcessingStage.PDF_PROCESSING,
        current_chapter=10
    )
    assert pipeline_state.get_progress() == 100.0


def test_last_successful_stage(pipeline_state: PipelineState):
    """Test tracking of last successful stage."""
    # Initial state
    assert pipeline_state.get_last_successful_stage() == ProcessingStage.INITIALIZED
    
    # Update through multiple stages
    pipeline_state.update_state(ProcessingStage.PDF_PROCESSING)
    pipeline_state.update_state(ProcessingStage.TRANSLATION)
    pipeline_state.update_state(ProcessingStage.OPTIMIZATION)
    
    # Fail at audio generation
    pipeline_state.update_state(
        stage=ProcessingStage.AUDIO_GENERATION,
        error="Audio generation failed"
    )
    
    # Check last successful stage
    assert pipeline_state.get_last_successful_stage() == ProcessingStage.OPTIMIZATION


@pytest.mark.parametrize("stage,prefix,expected_count", [
    (ProcessingStage.PDF_PROCESSING, "pdf_", 2),
    (ProcessingStage.TRANSLATION, "translated_", 2),
    (ProcessingStage.OPTIMIZATION, "optimized_", 2),
])
def test_get_artifacts_by_stage(
    pipeline_state: PipelineState,
    stage: ProcessingStage,
    prefix: str,
    expected_count: int
):
    """Test getting artifacts by stage with different scenarios."""
    # Add test artifacts
    pipeline_state.add_artifact(f"{prefix}1", Path("/test/1"))
    pipeline_state.add_artifact(f"{prefix}2", Path("/test/2"))
    pipeline_state.add_artifact("other_artifact", Path("/test/other"))
    
    # Get artifacts for stage
    artifacts = pipeline_state.get_artifacts_by_stage(stage)
    
    # Check count matches expected
    assert len(artifacts) == expected_count 