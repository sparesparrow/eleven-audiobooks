from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

class ProcessingStage(Enum):
    INITIALIZED = "initialized"
    PDF_PROCESSING = "pdf_processing"
    TRANSLATION = "translation"
    OPTIMIZATION = "optimization"
    AUDIO_GENERATION = "audio_generation"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProcessingState:
    stage: ProcessingStage
    current_chapter: int
    total_chapters: int
    error: Optional[str] = None
    artifacts: Dict[str, Path] = None

class PipelineState:
    def __init__(self):
        self.state = ProcessingState(
            stage=ProcessingStage.INITIALIZED,
            current_chapter=0,
            total_chapters=0,
            artifacts={}
        )
        self.history = []

    def update_state(self, 
                    stage: ProcessingStage, 
                    current_chapter: int = None,
                    error: str = None) -> None:
        """Update pipeline state and record history."""
        # Store current state in history
        self.history.append(self.state)
        
        # Update state
        self.state.stage = stage
        if current_chapter is not None:
            self.state.current_chapter = current_chapter
        if error:
            self.state.error = error
            self.state.stage = ProcessingStage.FAILED

    def add_artifact(self, name: str, path: Path) -> None:
        """Record processing artifact."""
        self.state.artifacts[name] = path

    def get_artifacts_by_stage(self, stage: ProcessingStage) -> List[Path]:
        """Get all artifacts for a specific processing stage."""
        stage_prefixes = {
            ProcessingStage.PDF_PROCESSING: "pdf_",
            ProcessingStage.TRANSLATION: "translated_",
            ProcessingStage.OPTIMIZATION: "optimized_",
            ProcessingStage.AUDIO_GENERATION: "audio_"
        }
        prefix = stage_prefixes.get(stage)
        if not prefix:
            return []
        
        return [path for name, path in self.state.artifacts.items() 
                if name.startswith(prefix)]

    def can_proceed(self) -> bool:
        """Check if pipeline can proceed to next stage."""
        return self.state.stage != ProcessingStage.FAILED

    def get_progress(self) -> float:
        """Get current progress as percentage."""
        if self.state.total_chapters == 0:
            return 0.0
        return (self.state.current_chapter / self.state.total_chapters) * 100

    def get_last_successful_stage(self) -> ProcessingStage:
        """Get the last successfully completed stage."""
        for state in reversed(self.history):
            if state.stage != ProcessingStage.FAILED:
                return state.stage
        return ProcessingStage.INITIALIZED 