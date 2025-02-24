"""Text optimization component using Anthropic API."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)

OPTIMIZATION_PROMPT = """
Please optimize the following text for natural-sounding speech synthesis.
Focus on:
1. Natural flow and rhythm
2. Clear sentence structure
3. Appropriate punctuation for speech
4. Consistent formatting

Text to optimize:
{text}

Return only the optimized text without any explanations.
"""


class BatchTextOptimizer:
    """Handles text optimization using Anthropic API."""
    
    # Rate limiting settings
    MAX_CONCURRENT_REQUESTS = 3  # Maximum concurrent requests
    REQUEST_WAIT_TIME = 1.0  # Time to wait between requests in seconds
    MAX_RETRIES = 3  # Maximum number of retries
    RETRY_DELAY = 2  # Base delay between retries in seconds

    def __init__(self, api_key: str):
        """
        Initialize text optimizer.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)
        self.last_request_time = 0
        self.semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

    async def optimize_chapter(self, text_path: Path) -> Path:
        """
        Optimize chapter text file for speech synthesis.

        Args:
            text_path: Path to text file

        Returns:
            Path to optimized text file

        Raises:
            Exception: If optimization fails
        """
        try:
            # Read input file
            text = text_path.read_text()
            
            # Optimize text
            optimized_text = await self.optimize(text)
            
            # Create output path (same name but in parent directory)
            output_path = text_path.with_suffix('.optimized.txt')
            
            # Write optimized text
            output_path.write_text(optimized_text)
            
            return output_path
            
        except Exception as e:
            logger.error("Failed to optimize chapter: %s", str(e))
            raise
    
    async def optimize(self, text: str) -> str:
        """
        Optimize text for speech synthesis.

        Args:
            text: Text to optimize

        Returns:
            Optimized text

        Raises:
            Exception: If optimization fails
        """
        try:
            # Split text into manageable chunks
            chunks = self._split_text(text)
            
            # Optimize chunks with rate limiting
            tasks = []
            for i, chunk in enumerate(chunks):
                task = self._optimize_chunk_with_rate_limit(chunk)
                tasks.append(task)
            
            optimized_chunks = await asyncio.gather(*tasks)
            
            # Combine optimized chunks
            return "\n\n".join(optimized_chunks)
            
        except Exception as e:
            logger.error("Failed to optimize text: %s", str(e))
            raise

    def _split_text(self, text: str) -> List[str]:
        """
        Split text into manageable chunks preserving paragraphs and sentences.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        # Split on paragraph breaks first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            # If adding this paragraph would exceed chunk size
            if current_length + len(para) > 4000:
                # Save current chunk if not empty
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # If paragraph itself is too long, split it into sentences
                if len(para) > 4000:
                    sentences = self._split_into_sentences(para)
                    temp_chunk = []
                    temp_length = 0
                    
                    for sentence in sentences:
                        # If adding this sentence would exceed chunk size
                        if temp_length + len(sentence) > 4000:
                            if temp_chunk:
                                chunks.append("\n".join(temp_chunk))
                                temp_chunk = []
                                temp_length = 0
                        
                        temp_chunk.append(sentence)
                        temp_length += len(sentence) + 1  # +1 for newline
                    
                    # Add any remaining sentences
                    if temp_chunk:
                        chunks.append("\n".join(temp_chunk))
                else:
                    # Add paragraph as a chunk
                    chunks.append(para)
            else:
                # Add paragraph to current chunk
                current_chunk.append(para)
                current_length += len(para) + 2  # +2 for "\n\n"
        
        # Add any remaining paragraphs
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks
        
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        import re
        
        # Simple regex for sentence splitting that preserves sentence endings
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])'  # Look for period, exclamation, or question mark followed by space and capital letter
        sentences = re.split(sentence_endings, text)
        
        # Ensure all sentences have proper ending
        result = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not sentence[-1] in '.!?':
                sentence += '.'
            if sentence:
                result.append(sentence)
                
        return result
    
    async def _optimize_chunk_with_rate_limit(self, chunk: str) -> str:
        """
        Optimize a chunk of text with rate limiting and retries.

        Args:
            chunk: Text chunk to optimize

        Returns:
            Optimized text chunk
        """
        # Apply rate limiting
        async with self.semaphore:
            # Ensure we wait between requests
            now = time.time()
            time_since_last = now - self.last_request_time
            if time_since_last < self.REQUEST_WAIT_TIME:
                await asyncio.sleep(self.REQUEST_WAIT_TIME - time_since_last)
            
            # Update last request time
            self.last_request_time = time.time()
            
            # Try optimizing with retries
            retries = 0
            last_error = None
            
            while retries < self.MAX_RETRIES:
                try:
                    result = await self._optimize_chunk(chunk)
                    return result
                except Exception as e:
                    last_error = e
                    retries += 1
                    wait_time = self.RETRY_DELAY * (2 ** (retries - 1))  # Exponential backoff
                    logger.warning(f"Optimization failed (attempt {retries}), retrying in {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
            
            # If we get here, all retries failed
            logger.error(f"Failed to optimize chunk after {self.MAX_RETRIES} attempts")
            raise last_error

    async def _optimize_chunk(self, chunk: str) -> str:
        """
        Optimize a single chunk of text.

        Args:
            chunk: Text chunk to optimize

        Returns:
            Optimized text chunk
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": OPTIMIZATION_PROMPT.format(text=chunk)
                }]
            )
        )
        
        return response.content[0].text
