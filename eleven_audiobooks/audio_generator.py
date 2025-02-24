"""Audio generation component using ElevenLabs API."""

import asyncio
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiofiles
from elevenlabs import generate, set_api_key, voices
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class AudioGenerator:
    """Handles audio generation using ElevenLabs API."""

    # Maximum text length for a single API call (4096 is ElevenLabs limit)
    MAX_CHUNK_SIZE = 4000
    
    # Maximum number of concurrent API calls to avoid rate limiting
    MAX_CONCURRENT_REQUESTS = 5
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(self, api_key: str, voice_id: Optional[str] = None):
        """
        Initialize audio generator.

        Args:
            api_key: ElevenLabs API key
            voice_id: Optional voice ID to use
        """
        self.voice_id = voice_id or "OJtLHqR5g0hxcgc27j7C"  # Default voice
        set_api_key(api_key)
        
        # Verify voice exists
        available_voices = voices()
        if not any(v.voice_id == self.voice_id for v in available_voices):
            raise ValueError(f"Voice ID {self.voice_id} not found")

    async def generate_chapter(self, text_path: Path) -> bytes:
        """
        Generate audio for a chapter.

        Args:
            text_path: Path to text file

        Returns:
            Generated audio data

        Raises:
            Exception: If audio generation fails
        """
        try:
            # Read text content
            text = text_path.read_text()
            
            # Split text into chunks
            text_chunks = self._split_text(text)
            
            # Create a semaphore to limit concurrent API calls
            semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)
            
            # Generate audio for each chunk with concurrency control
            async def process_chunk(chunk: str) -> bytes:
                async with semaphore:
                    return await self._generate_audio_with_retry(chunk)
            
            tasks = [process_chunk(chunk) for chunk in text_chunks]
            audio_chunks = await asyncio.gather(*tasks)
            
            # Combine audio chunks
            return await self._combine_audio_chunks(audio_chunks)

        except Exception as e:
            logger.error("Failed to generate audio: %s", str(e))
            raise
            
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks for processing.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        # Split on sentence boundaries
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            
            # Check for sentence end (period, question mark, exclamation mark followed by space)
            if char in [".", "?", "!"] and current_sentence.strip():
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        # Add any remaining text as a sentence
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # Combine sentences into chunks
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed max size, start a new chunk
            if len(current_chunk) + len(sentence) > self.MAX_CHUNK_SIZE:
                if current_chunk:
                    chunks.append(current_chunk)
                # If the sentence itself is too long, split it further
                if len(sentence) > self.MAX_CHUNK_SIZE:
                    words = sentence.split()
                    sub_chunk = ""
                    for word in words:
                        if len(sub_chunk) + len(word) + 1 > self.MAX_CHUNK_SIZE:
                            chunks.append(sub_chunk)
                            sub_chunk = word
                        else:
                            sub_chunk += (" " + word) if sub_chunk else word
                    if sub_chunk:
                        current_chunk = sub_chunk
                    else:
                        current_chunk = ""
                else:
                    current_chunk = sentence
            else:
                # Add space between sentences
                separator = " " if current_chunk and not current_chunk.endswith(" ") else ""
                current_chunk += separator + sentence
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
    
    async def _generate_audio_with_retry(self, text: str) -> bytes:
        """
        Generate audio with retry mechanism.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio data
        """
        retries = 0
        last_error = None
        
        while retries < self.MAX_RETRIES:
            try:
                # Generate audio in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                audio_data = await loop.run_in_executor(
                    None,
                    lambda: generate(
                        text=text,
                        voice=self.voice_id,
                        model="eleven_multilingual_v2"
                    )
                )
                
                return audio_data
                
            except Exception as e:
                last_error = e
                retries += 1
                await asyncio.sleep(self.RETRY_DELAY * retries)  # Exponential backoff
        
        # If we exhausted retries, raise the last error
        logger.error(f"Failed to generate audio after {self.MAX_RETRIES} retries")
        raise last_error
    
    async def _combine_audio_chunks(self, audio_chunks: List[bytes]) -> bytes:
        """
        Combine audio chunks into a single audio file.
        
        Args:
            audio_chunks: List of audio data chunks
            
        Returns:
            Combined audio data
        """
        # If there's only one chunk, return it directly
        if len(audio_chunks) == 1:
            return audio_chunks[0]
        
        # Create temporary directory to store audio chunks
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write chunks to temporary files
            temp_files = []
            for i, chunk in enumerate(audio_chunks):
                temp_file = os.path.join(temp_dir, f"chunk_{i}.mp3")
                async with aiofiles.open(temp_file, "wb") as f:
                    await f.write(chunk)
                temp_files.append(temp_file)
            
            # Combine audio files
            combined = AudioSegment.empty()
            for temp_file in temp_files:
                segment = AudioSegment.from_mp3(temp_file)
                combined += segment
            
            # Export combined audio to a file
            output_file = os.path.join(temp_dir, "combined.mp3")
            combined.export(output_file, format="mp3")
            
            # Read combined file
            async with aiofiles.open(output_file, "rb") as f:
                return await f.read() 