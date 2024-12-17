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
            # Read chapter content and split into chunks
            content = chapter_path.read_text(encoding='utf-8')
            chunks = self._split_into_chunks(content)
            
            # Create batch requests for chunks
            requests = [
                Request(
                    custom_id=f"{chapter_path.stem}_chunk_{i:03d}",
                    params=MessageCreateParamsNonStreaming(
                        model="claude-3.5-haiku",
                        max_tokens=8192,
                        temperature=0,
                        messages=[{
                            "role": "user", 
                            "content": self._create_optimization_prompt(chunk)
                        }]
                    )        
                )
                for i, chunk in enumerate(chunks)
            ]
            
            # Process in batches
            BATCH_SIZE = 50  # Adjust based on API limits
            results = []
            for i in range(0, len(requests), BATCH_SIZE):
                batch_requests = requests[i:i + BATCH_SIZE]
                batch_id = await self.batch_writer.create_batch(batch_requests)
                self.batch_writer.persist_batch_id(batch_id, chapter_path)
                batch_results = await self.batch_reader.get_batch_results(batch_id)
                results.extend(batch_results)
            
            # Sort and combine results
            sorted_results = sorted(
                results,
                key=lambda x: int(x.custom_id.split('_')[-1])
            )
            optimized_content = "\n\n".join(r.content for r in sorted_results if r.content)

            optimized_path = chapter_path.with_name(f"{chapter_path.stem}_optimized.md")
            optimized_path.write_text(optimized_content, encoding='utf-8')
            return optimized_path

        except Exception as e:
            self.logger.error(f"Failed to optimize chapter {chapter_path}: {e}")
            raise

    def _split_into_chunks(self, content: str, max_chunk_size: int = 4000) -> List[str]:
        """Split content into meaningful chunks while preserving context."""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            if current_size + len(para) > max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(para)
            current_size += len(para)
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks

    def _create_optimization_prompt(self, text: str) -> str:
        """Create prompt for optimizing text."""
        return (
            f"Modify the following text to make it optimal for speech synthesis:\n\n"
            f"{text}\n\n"
            f"Focus solely on improving the text for audio narration while maintaining context and flow." 
        )
