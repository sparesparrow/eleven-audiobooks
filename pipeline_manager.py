import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

from audio_generator import AudioGenerator
from batch_text_optimizer import BatchTextOptimizer
from pdf_processor import PDFProcessor, Chapter
from pipeline_state import PipelineState, ProcessingStage
from storage_engine import StorageEngine
from translation_pipeline import TranslationPipeline

logger = logging.getLogger(__name__)

class PipelineManager:
    def __init__(self, 
                 pdf_path: Path,
                 output_dir: Path,
                 mongo_uri: str = 'mongodb://localhost:27017/',
                 config: Dict = None):
        """
        Initialize pipeline manager with components.
        
        Args:
            pdf_path: Path to input PDF
            output_dir: Output directory
            mongo_uri: MongoDB connection string
            config: Optional configuration dictionary
        """
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.config = config or {}
        
        # Initialize state management
        self.state = PipelineState()
        
        # Initialize components
        self.storage = StorageEngine(mongo_uri)
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

    async def process(self, translate: bool = False) -> str:
        """
        Process the book through the pipeline.
        
        Args:
            translate: Whether to translate the content
            
        Returns:
            URL to the generated audiobook
        """
        try:
            # Setup directories
            await self._setup_directories()
            
            # Process PDF
            chapters = await self._process_pdf()
            if not self.state.can_proceed():
                return self._handle_failure()
            
            # Translation if required
            if translate:
                chapters = await self._translate_chapters(chapters)
                if not self.state.can_proceed():
                    return self._handle_failure()
            
            # Optimize text
            optimized_paths = await self._optimize_chapters(chapters)
            if not self.state.can_proceed():
                return self._handle_failure()
            
            # Generate audio
            audio_url = await self._generate_audio(optimized_paths)
            if not self.state.can_proceed():
                return self._handle_failure()
            
            self.state.update_state(ProcessingStage.COMPLETED)
            return audio_url
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {str(e)}")
            self.state.update_state(ProcessingStage.FAILED, error=str(e))
            return self._handle_failure()

    async def _setup_directories(self) -> None:
        """Setup required directories."""
        for dir_name in ['chapters', 'translated', 'optimized', 'audio']:
            dir_path = self.output_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            self.state.add_artifact(f"dir_{dir_name}", dir_path)

    async def _process_pdf(self) -> Dict[int, Chapter]:
        """Process PDF into chapters."""
        self.state.update_state(ProcessingStage.PDF_PROCESSING)
        try:
            chapters = self.pdf_processor.process(self.pdf_path)
            self.state.state.total_chapters = len(chapters)
            
            # Save chapters
            chapters_dir = self.state.artifacts["dir_chapters"]
            self.pdf_processor.save_chapters(chapters, chapters_dir)
            
            # Store in database
            self.storage.store_original(
                [chapter.content for chapter in chapters.values()]
            )
            
            return chapters
        except Exception as e:
            self.state.update_state(
                ProcessingStage.FAILED,
                error=f"PDF processing failed: {str(e)}"
            )
            raise

    async def _translate_chapters(self, 
                                chapters: Dict[int, Chapter]
                                ) -> Dict[int, Chapter]:
        """Translate chapters if required."""
        self.state.update_state(ProcessingStage.TRANSLATION)
        try:
            translated_dir = self.state.artifacts["dir_translated"]
            translated = await self.translation.translate_chapters(
                chapters, translated_dir
            )
            
            # Store translations
            self.storage.store_translated(
                [chapter.content for chapter in translated.values()]
            )
            
            return translated
        except Exception as e:
            self.state.update_state(
                ProcessingStage.FAILED,
                error=f"Translation failed: {str(e)}"
            )
            raise

    async def _optimize_chapters(self, 
                               chapters: Dict[int, Chapter]
                               ) -> List[Path]:
        """Optimize chapters for speech synthesis."""
        self.state.update_state(ProcessingStage.OPTIMIZATION)
        optimized_paths = []
        
        try:
            for chapter_num, chapter in enumerate(chapters.values(), 1):
                self.state.update_state(
                    ProcessingStage.OPTIMIZATION, 
                    current_chapter=chapter_num
                )
                
                chapter_path = (self.state.artifacts["dir_chapters"] / 
                              f"chapter_{chapter_num:02d}.md")
                optimized_path = await self.optimizer.optimize_chapter(chapter_path)
                optimized_paths.append(optimized_path)
                
                # Record artifact
                self.state.add_artifact(
                    f"optimized_chapter_{chapter_num}", 
                    optimized_path
                )
            
            return optimized_paths
        except Exception as e:
            self.state.update_state(
                ProcessingStage.FAILED,
                error=f"Optimization failed: {str(e)}"
            )
            raise

    async def _generate_audio(self, optimized_paths: List[Path]) -> str:
        """Generate audio from optimized text."""
        self.state.update_state(ProcessingStage.AUDIO_GENERATION)
        try:
            audio_responses = []
            for chapter_num, path in enumerate(optimized_paths, 1):
                self.state.update_state(
                    ProcessingStage.AUDIO_GENERATION,
                    current_chapter=chapter_num
                )
                
                audio_response = await self.audio_gen.generate_chapter(path)
                audio_id = self.storage.store_audio(
                    audio_response,
                    filename=f"chapter_{chapter_num:02d}.mp3"
                )
                audio_responses.append(audio_id)
                
                # Record artifact
                self.state.add_artifact(
                    f"audio_chapter_{chapter_num}",
                    self.state.artifacts["dir_audio"] / f"chapter_{chapter_num:02d}.mp3"
                )
            
            return self.storage.get_audiobook_url(audio_responses[-1])
        except Exception as e:
            self.state.update_state(
                ProcessingStage.FAILED,
                error=f"Audio generation failed: {str(e)}"
            )
            raise

    def _handle_failure(self) -> Optional[str]:
        """Handle pipeline failure and attempt recovery."""
        last_stage = self.state.get_last_successful_stage()
        logger.error(
            f"Pipeline failed at {self.state.state.stage}. "
            f"Last successful stage: {last_stage}. "
            f"Error: {self.state.state.error}"
        )
        
        # If we have any audio generated, return its URL
        audio_artifacts = self.state.get_artifacts_by_stage(
            ProcessingStage.AUDIO_GENERATION
        )
        if audio_artifacts:
            return self.storage.get_audiobook_url(str(audio_artifacts[-1]))
        
        return None 