"""Eleven Audiobooks - Convert PDF books into high-quality audiobooks."""

__version__ = "0.1.0"

from .pipeline_manager import PipelineManager
from .pipeline_state import ProcessingStage, PipelineState

__all__ = ["PipelineManager", "ProcessingStage", "PipelineState"] 