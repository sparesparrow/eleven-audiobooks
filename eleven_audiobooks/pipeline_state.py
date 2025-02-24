"""Pipeline state management for the Eleven Audiobooks project."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import copy


class ProcessingStage(str, Enum):
    """Processing stages for the pipeline."""
    INITIALIZED = "initialized"
    PDF_PROCESSING = "pdf_processing"
    TRANSLATION = "translation"
    OPTIMIZATION = "optimization"
    AUDIO_GENERATION = "audio_generation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class State:
    """Pipeline state."""
    stage: ProcessingStage = ProcessingStage.INITIALIZED
    current_chapter: int = 0
    total_chapters: int = 0
    error: Optional[str] = None
    artifacts: Dict[str, Path] = field(default_factory=dict)


class PipelineState:
    """Pipeline state manager."""
    def __init__(self):
        """Initialize pipeline state."""
        self.state = State()
        self.history = []

    def update_state(
        self,
        stage: Optional[ProcessingStage] = None,
        current_chapter: Optional[int] = None,
        total_chapters: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Update the pipeline state.

        Args:
            stage: New processing stage
            current_chapter: Current chapter being processed
            total_chapters: Total number of chapters
            error: Error message if any
        """
        # Save current state to history
        self.history.append(copy.deepcopy(self.state))

        # Update state fields if provided
        if stage is not None:
            self.state.stage = stage
        if current_chapter is not None:
            self.state.current_chapter = current_chapter
        if total_chapters is not None:
            self.state.total_chapters = total_chapters
        if error is not None:
            self.state.error = error
            self.state.stage = ProcessingStage.FAILED

    def add_artifact(self, name: str, path: Path) -> None:
        """
        Add an artifact to the state.

        Args:
            name: Artifact name
            path: Path to artifact
        """
        self.state.artifacts[name] = path

    def get_artifacts_by_stage(self, stage: ProcessingStage) -> List[Path]:
        """
        Get artifacts for a specific processing stage.

        Args:
            stage: Processing stage to get artifacts for

        Returns:
            List of artifact paths for the stage
        """
        prefix = {
            ProcessingStage.PDF_PROCESSING: "pdf_",
            ProcessingStage.TRANSLATION: "translated_",
            ProcessingStage.OPTIMIZATION: "optimized_",
            ProcessingStage.AUDIO_GENERATION: "audio_"
        }.get(stage, "")

        if not prefix:
            return []

        artifacts = [
            path for key, path in self.state.artifacts.items()
            if key.startswith(prefix)
        ]

        # Extract chapter numbers and sort
        def get_chapter_num(path: Path) -> int:
            try:
                # Extract number from patterns like "chapter_1.txt" or "1.txt"
                name = path.stem
                if "_" in name:
                    return int(name.split("_")[-1])
                return int(name)
            except ValueError:
                return 0

        return sorted(artifacts, key=get_chapter_num)

    def get_progress(self) -> float:
        """
        Calculate pipeline progress.

        Returns:
            Progress percentage (0-100)
        """
        if self.state.total_chapters == 0:
            return 0.0

        return (self.state.current_chapter / self.state.total_chapters) * 100

    def can_proceed(self) -> bool:
        """
        Check if pipeline can proceed.

        Returns:
            True if pipeline can proceed, False otherwise
        """
        return self.state.stage != ProcessingStage.FAILED

    def get_last_successful_stage(self) -> ProcessingStage:
        """
        Get the last successful processing stage.

        Returns:
            Last successful stage
        """
        if not self.history:
            return ProcessingStage.INITIALIZED

        for state in reversed(self.history):
            if state.stage != ProcessingStage.FAILED:
                return state.stage

        return ProcessingStage.INITIALIZED 