"""Translation pipeline component."""

import asyncio
import logging
from typing import Dict, List, Optional

import deepl

logger = logging.getLogger(__name__)


class TranslationPipeline:
    """Handles text translation using multiple services."""

    def __init__(
        self,
        deepl_api_key: Optional[str] = None,
        nllb_api_key: Optional[str] = None,
        aya_api_key: Optional[str] = None
    ):
        """
        Initialize translation pipeline.

        Args:
            deepl_api_key: DeepL API key
            nllb_api_key: NLLB API key
            aya_api_key: Aya API key
        """
        self.deepl_client = deepl.Translator(deepl_api_key) if deepl_api_key else None
        self.nllb_api_key = nllb_api_key
        self.aya_api_key = aya_api_key

    async def translate_chapters(
        self,
        chapters: Dict[int, str],
        target_lang: str = "CS"  # Czech
    ) -> Dict[int, str]:
        """
        Translate chapters to target language.

        Args:
            chapters: Dictionary mapping chapter numbers to text
            target_lang: Target language code

        Returns:
            Dictionary of translated chapters

        Raises:
            Exception: If translation fails
        """
        try:
            # Split chapters into chunks for translation
            chunks = self._split_chapters(chapters)
            
            # Translate chunks in parallel
            tasks = [
                self._translate_chunk(chunk["text"], target_lang)
                for chunk in chunks
            ]
            translated_texts = await asyncio.gather(*tasks)
            
            # Combine translated chunks with their metadata
            translated_chunks = [
                {"text": text, "metadata": chunks[i]["metadata"]}
                for i, text in enumerate(translated_texts)
            ]
            
            # Combine translated chunks back into chapters
            return self._combine_chunks(translated_chunks)
            
        except Exception as e:
            logger.error("Failed to translate chapters: %s", str(e))
            raise

    def _split_chapters(self, chapters: Dict[int, str]) -> List[Dict[str, any]]:
        """
        Split chapters into manageable chunks for translation.

        Args:
            chapters: Dictionary of chapters

        Returns:
            List of chunk objects with metadata
        """
        chunks = []
        current_chunk = []
        current_length = 0
        current_metadata = {
            "chapter_id": None,
            "is_chapter_start": False,
            "is_chapter_end": False,
            "position": 0
        }
        
        for chapter_id, text in chapters.items():
            # Split text into sentences
            sentences = [s.strip() + "." for s in text.split(".") if s.strip()]
            position_in_chapter = 0
            
            for sentence in sentences:
                # If this is the first sentence in the chapter
                if position_in_chapter == 0:
                    # If we have a current chunk, mark it as chapter end
                    if current_chunk:
                        current_metadata["is_chapter_end"] = True
                        chunks.append({
                            "text": " ".join(current_chunk),
                            "metadata": current_metadata.copy()
                        })
                        current_chunk = []
                        current_length = 0
                    
                    # Start a new chunk with chapter start metadata
                    current_metadata = {
                        "chapter_id": chapter_id,
                        "is_chapter_start": True,
                        "is_chapter_end": False,
                        "position": position_in_chapter
                    }
                
                # If adding this sentence would exceed chunk size
                if current_length + len(sentence) > 4000:
                    if current_chunk:
                        chunks.append({
                            "text": " ".join(current_chunk),
                            "metadata": current_metadata.copy()
                        })
                        current_chunk = []
                        current_length = 0
                        
                        # Update metadata for next chunk
                        current_metadata["is_chapter_start"] = False
                        current_metadata["position"] = position_in_chapter
                
                current_chunk.append(sentence)
                current_length += len(sentence) + 1  # +1 for space
                position_in_chapter += 1
            
            # Mark the last chunk of the chapter
            current_metadata["is_chapter_end"] = True
        
        # Add any remaining chunk
        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "metadata": current_metadata.copy()
            })
        
        return chunks

    async def _translate_chunk(self, text: str, target_lang: str) -> str:
        """
        Translate a chunk of text.

        Args:
            text: Text to translate
            target_lang: Target language code

        Returns:
            Translated text
        """
        try:
            if self.deepl_client:
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.deepl_client.translate_text(
                        text,
                        target_lang=target_lang
                    )
                )
                return str(result)
            else:
                # Fallback to other services or raise error
                raise NotImplementedError("No translation service available")
            
        except Exception as e:
            logger.error("Failed to translate chunk: %s", str(e))
            raise

    def _combine_chunks(
        self,
        chunks: List[Dict[str, any]]
    ) -> Dict[int, str]:
        """
        Combine translated chunks back into chapters using metadata.

        Args:
            chunks: List of translated chunks with metadata

        Returns:
            Dictionary of translated chapters
        """
        translated = {}
        current_chapter_id = None
        current_chapter_content = []
        
        # Sort chunks by chapter_id and position
        sorted_chunks = sorted(
            chunks,
            key=lambda x: (x["metadata"]["chapter_id"], x["metadata"]["position"])
        )
        
        for chunk in sorted_chunks:
            metadata = chunk["metadata"]
            text = chunk["text"]
            chapter_id = metadata["chapter_id"]
            
            # If starting a new chapter
            if chapter_id != current_chapter_id:
                # Save previous chapter if it exists
                if current_chapter_content:
                    translated[current_chapter_id] = "\n\n".join(current_chapter_content)
                    current_chapter_content = []
                
                current_chapter_id = chapter_id
            
            # Add chunk to current chapter
            current_chapter_content.append(text)
        
        # Add the last chapter
        if current_chapter_content and current_chapter_id is not None:
            translated[current_chapter_id] = "\n\n".join(current_chapter_content)
        
        return translated 