"""Pipeline manager for the Eleven Audiobooks project."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

from pymongo import MongoClient

from .pipeline_state import PipelineState, ProcessingStage
from .audio_generator import AudioGenerator
from .batch_text_optimizer import BatchTextOptimizer
from .pdf_processor import PDFProcessor
from .storage_engine import StorageEngine
from .translation_pipeline import TranslationPipeline

logger = logging.getLogger(__name__)


class PipelineManager:
    """Manages the audiobook generation pipeline."""

    def __init__(
        self,
        pdf_path: Path,
        output_dir: Path,
        mongo_db: MongoClient,
        config: Optional[Dict[str, str]] = None
    ):
        """
        Initialize pipeline manager.

        Args:
            pdf_path: Path to PDF file
            output_dir: Output directory
            mongo_db: MongoDB database instance
            config: Optional configuration dictionary
        """
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.db = mongo_db
        self.config = config or {}
        
        # Initialize state
        self.state = PipelineState()
        
        # Initialize components
        self.storage = StorageEngine(self.db)
        self.pdf_processor = PDFProcessor()
        self.translation = TranslationPipeline(
            deepl_api_key=self.config.get("DEEPL_API_KEY"),
            nllb_api_key=self.config.get("NLLB_API_KEY"),
            aya_api_key=self.config.get("AYA_API_KEY")
        )
        self.optimizer = BatchTextOptimizer(
            api_key=self.config.get("ANTHROPIC_API_KEY")
        )
        self.audio_gen = AudioGenerator(
            api_key=self.config.get("ELEVENLABS_API_KEY"),
            voice_id=self.config.get("VOICE_ID", "OJtLHqR5g0hxcgc27j7C")
        )

    async def process(self, translate: bool = False) -> Optional[str]:
        """
        Process book through pipeline.

        Args:
            translate: Whether to translate content

        Returns:
            URL to generated audiobook
        """
        try:
            # Setup directories
            await self._setup_directories()

            # Process PDF
            chapters = await self._process_pdf()
            if not self.state.can_proceed():
                return await self._handle_failure(Exception(self.state.state.error))
            
            # Translate if requested
            if translate:
                chapters = await self._translate_chapters(chapters)
                if not self.state.can_proceed():
                    return await self._handle_failure(Exception(self.state.state.error))
            
            # Optimize chapters
            chapter_paths = await self._optimize_chapters(chapters)
            if not self.state.can_proceed():
                return await self._handle_failure(Exception(self.state.state.error))
            
            # Generate audio
            await self._generate_audio(chapter_paths)
            if not self.state.can_proceed():
                return await self._handle_failure(Exception(self.state.state.error))
            
            # Update state and get final URL
            self.state.update_state(stage=ProcessingStage.COMPLETED)
            return self.storage.get_audiobook_url(self.output_dir)
            
        except Exception as e:
            return await self._handle_failure(e)

    async def _setup_directories(self) -> None:
        """Set up output directories."""
        self.state.update_state(stage=ProcessingStage.INITIALIZED)
        
        try:
            # Create output directories
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            dirs = {
                "dir_chapters": self.output_dir / "chapters",
                "dir_translated": self.output_dir / "translated",
                "dir_optimized": self.output_dir / "optimized",
                "dir_audio": self.output_dir / "audio"
            }
            
            for name, path in dirs.items():
                path.mkdir(exist_ok=True)
                self.state.add_artifact(name, path)
                
        except Exception as e:
            self.state.update_state(error=str(e))
            raise

    async def _process_pdf(self) -> Dict[int, str]:
        """Process PDF file."""
        self.state.update_state(stage=ProcessingStage.PDF_PROCESSING)
        
        try:
            # Process PDF
            chapters = self.pdf_processor.process(self.pdf_path)
            self.state.state.total_chapters = len(chapters)
            
            # Save chapters
            for num, content in chapters.items():
                path = self.state.artifacts["dir_chapters"] / f"chapter_{num}.txt"
                path.write_text(content)
                self.state.add_artifact(f"pdf_chapter_{num}", path)
                
            # Store in database
            self.storage.store_original(chapters)
                
            return chapters
            
        except Exception as e:
            self.state.update_state(error=str(e))
            raise

    async def _translate_chapters(
        self,
        chapters: Dict[int, str]
    ) -> Dict[int, str]:
        """Translate chapters if requested."""
        self.state.update_state(stage=ProcessingStage.TRANSLATION)
        
        try:
            # Translate chapters
            translated = await self.translation.translate_chapters(chapters)
            
            # Save translated chapters
            for num, content in translated.items():
                path = self.state.artifacts["dir_translated"] / f"chapter_{num}.txt"
                path.write_text(content)
                self.state.add_artifact(f"translated_chapter_{num}", path)
                
            # Store in database
            self.storage.store_translated(translated)
                
            return translated
            
        except Exception as e:
            self.state.update_state(error=str(e))
            raise

    async def _optimize_chapters(
        self,
        chapters: Dict[int, str]
    ) -> List[Path]:
        """Optimize chapters for audio generation."""
        self.state.update_state(stage=ProcessingStage.OPTIMIZATION)
        
        try:
            optimized_paths = []
            
            # Optimize each chapter
            for num, content in chapters.items():
                self.state.update_state(current_chapter=num)
                
                # Optimize text
                optimized = await self.optimizer.optimize(content)
                
                # Save optimized text
                path = self.state.artifacts["dir_optimized"] / f"chapter_{num}.txt"
                path.write_text(optimized)
                self.state.add_artifact(f"optimized_chapter_{num}", path)
                optimized_paths.append(path)
                
            return optimized_paths
            
        except Exception as e:
            self.state.update_state(error=str(e))
            raise

    async def _generate_audio(self, chapter_paths: List[Path]) -> None:
        """Generate audio from optimized text."""
        self.state.update_state(stage=ProcessingStage.AUDIO_GENERATION)
        
        try:
            # Generate audio for each chapter
            for i, path in enumerate(chapter_paths, 1):
                self.state.update_state(current_chapter=i)
                
                # Generate audio
                audio_data = await self.audio_gen.generate_chapter(path)
                
                # Save audio
                audio_path = self.state.artifacts["dir_audio"] / f"chapter_{i}.mp3"
                audio_path.write_bytes(audio_data)
                self.state.add_artifact(f"audio_chapter_{i}", audio_path)
                
                # Store in database
                self.storage.store_audio(audio_data, audio_path.name)
                
        except Exception as e:
            self.state.update_state(error=str(e))
            raise

    async def _handle_failure(self, error: Exception) -> Optional[str]:
        """Handle pipeline failure."""
        error_msg = str(error)
        self.state.update_state(
            stage=ProcessingStage.FAILED,
            error=error_msg
        )
        
        # Log error
        logger.error("Pipeline failed: %s", error_msg)
        
        # Try to get partial result
        try:
            return self.storage.get_audiobook_url(self.output_dir)
        except Exception:
            return None 