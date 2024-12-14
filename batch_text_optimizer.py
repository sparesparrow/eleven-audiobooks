import logging
from pathlib import Path
from typing import List

from anthropic import Anthropic
from anthropic.types.beta.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.beta.messages.batch_create_params import Request

from batch_text_reader import BatchTextReader
from batch_text_writer import BatchTextWriter

class BatchTextOptimizer:
    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key)
        self.batch_writer = BatchTextWriter(self.client)
        self.batch_reader = BatchTextReader(self.client)
        self.logger = logging.getLogger(__name__)
        
    async def optimize_chapter(self, chapter_path: Path) -> Path:
        """Optimize a chapter using batch text processing."""
        try:
            # Read chapter content and split into lines
            content = chapter_path.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            # Create batch requests for each line 
            requests = [
                Request(
                    custom_id=f"{chapter_path.stem}_line_{i:05d}",
                    params=MessageCreateParamsNonStreaming(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=8192,
                        temperature=0,
                        messages=[{
                            "role": "user", 
                            "content": self._create_optimization_prompt(line)
                        }]
                    )        
                )
                for i, line in enumerate(lines) if line.strip()
            ]
            
            # Create batch and persist batch ID
            batch_id = await self.batch_writer.create_batch(requests)
            self.batch_writer.persist_batch_id(batch_id, chapter_path)
            
            # Retrieve batch results
            results = await self.batch_reader.get_batch_results(batch_id)
            
            # Sort results and save optimized chapter
            sorted_results = sorted(
                results,
                key=lambda x: int(x.custom_id.split('_')[-1])
            )
            optimized_content = "\n".join(r.content for r in sorted_results if r.content)

            optimized_path = chapter_path.with_name(f"{chapter_path.stem}_optimized.md")
            optimized_path.write_text(optimized_content, encoding='utf-8')
            return optimized_path

        except Exception as e:
            self.logger.error(f"Failed to optimize chapter {chapter_path}: {e}")
            raise

    def _create_optimization_prompt(self, line: str) -> str:
        """Create prompt for optimizing a single line."""
        return (
            f"Modify the following text to make it optimal for speech synthesis:\n\n"
            f"{line}\n\n"
            f"Focus solely on improving the text for audio narration without adding explanations." 
        )

