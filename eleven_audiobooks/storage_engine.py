"""Storage engine component using MongoDB."""

import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

from bson import ObjectId
from gridfs import GridFS
from pymongo import MongoClient
from pymongo.database import Database

logger = logging.getLogger(__name__)


class StorageEngine:
    """Handles data persistence using MongoDB."""

    def __init__(self, db: Union[MongoClient, Database]):
        """
        Initialize storage engine.

        Args:
            db: MongoDB client or database instance
        """
        # Get database instance
        if isinstance(db, MongoClient):
            self.db = db.audiobooks
        else:
            self.db = db
        
        # Initialize GridFS for audio storage
        self.fs = GridFS(self.db)
        
        # Create necessary indexes
        self._setup_indexes()
        
    def _setup_indexes(self):
        """
        Set up necessary indexes for efficient querying.
        """
        try:
            # Create index on filename in GridFS files collection
            self.db.fs.files.create_index("filename")
            
            # Create index on version and timestamp in document collections
            for collection in ["original_text", "translated_text", "optimized_text"]:
                self.db[collection].create_index("version")
                self.db[collection].create_index("timestamp")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {str(e)}")
            # Non-fatal error, continue without indexes

    def store_original(self, chapters: Dict[int, str]) -> str:
        """
        Store original chapter text.

        Args:
            chapters: Dictionary of chapter text

        Returns:
            ID of stored document

        Raises:
            Exception: If storage fails
        """
        try:
            # Validate input data
            self._validate_chapters(chapters)
            
            # Create document with version and timestamp
            document = {
                "chapters": [
                    {
                        "number": num,
                        "content": content
                    }
                    for num, content in chapters.items()
                ],
                "version": 1,
                "timestamp": time.time(),
                "metadata": {
                    "chapter_count": len(chapters),
                    "total_length": sum(len(content) for content in chapters.values())
                }
            }
            
            result = self.db.original_text.insert_one(document)
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error("Failed to store original text: %s", str(e))
            raise

    def _validate_chapters(self, chapters: Dict[int, str]) -> None:
        """
        Validate chapter data before storage.

        Args:
            chapters: Dictionary of chapter data

        Raises:
            ValueError: If validation fails
        """
        if not chapters:
            raise ValueError("No chapters provided")
            
        if not isinstance(chapters, dict):
            raise ValueError("Chapters must be a dictionary")
            
        for num, content in chapters.items():
            if not isinstance(num, int):
                raise ValueError(f"Chapter number must be an integer, got {type(num)}")
                
            if not isinstance(content, str):
                raise ValueError(f"Chapter content must be a string, got {type(content)}")
                
            if not content.strip():
                raise ValueError(f"Chapter {num} content is empty")
    
    def _validate_audio(self, audio_data: bytes, filename: str) -> None:
        """
        Validate audio data before storage.

        Args:
            audio_data: Audio file data
            filename: Name of audio file

        Raises:
            ValueError: If validation fails
        """
        if not audio_data:
            raise ValueError("No audio data provided")
            
        if not isinstance(audio_data, bytes):
            raise ValueError(f"Audio data must be bytes, got {type(audio_data)}")
            
        if len(audio_data) < 100:  # Minimum size check
            raise ValueError("Audio data too small, likely corrupted")
            
        if not filename:
            raise ValueError("No filename provided")
            
        if not filename.endswith(".mp3"):
            raise ValueError("Audio file must be an MP3")

    def store_translated(self, chapters: Dict[int, str]) -> str:
        """
        Store translated chapter text.

        Args:
            chapters: Dictionary of translated text

        Returns:
            ID of stored document

        Raises:
            Exception: If storage fails
        """
        try:
            # Validate input data
            self._validate_chapters(chapters)
            
            # Create document with version and timestamp
            document = {
                "chapters": [
                    {
                        "number": num,
                        "content": content
                    }
                    for num, content in chapters.items()
                ],
                "version": 1,
                "timestamp": time.time(),
                "metadata": {
                    "chapter_count": len(chapters),
                    "total_length": sum(len(content) for content in chapters.values()),
                    "language": "cs"  # Hardcoded for now, should be passed as parameter
                }
            }
            
            result = self.db.translated_text.insert_one(document)
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error("Failed to store translated text: %s", str(e))
            raise
            
    def store_audio(self, audio_data: bytes, filename: str) -> str:
        """
        Store audio data.

        Args:
            audio_data: Audio file data
            filename: Name of audio file

        Returns:
            ID of stored file

        Raises:
            Exception: If storage fails
        """
        try:
            # Validate input data
            self._validate_audio(audio_data, filename)
            
            # Store metadata alongside the file
            metadata = {
                "timestamp": time.time(),
                "version": 1,
                "content_type": "audio/mpeg",
                "size": len(audio_data)
            }
            
            # Store file with metadata
            file_id = self.fs.put(
                audio_data,
                filename=filename,
                metadata=metadata
            )
            
            return str(file_id)
            
        except Exception as e:
            logger.error("Failed to store audio: %s", str(e))
            raise

    def get_audiobook_url(self, file_id_or_path: Union[str, Path]) -> Optional[str]:
        """
        Get URL for accessing audiobook.

        Args:
            file_id_or_path: Either a file ID string or a Path object to output directory

        Returns:
            URL to access audiobook or None if not found

        Raises:
            Exception: If URL generation fails
        """
        try:
            obj_id = None
            
            # Handle both string ID and Path cases
            if isinstance(file_id_or_path, str):
                # Convert string ID to ObjectId
                obj_id = ObjectId(file_id_or_path)
            elif isinstance(file_id_or_path, Path):
                # Get all audio files from directory
                output_dir = file_id_or_path
                audio_files = sorted(output_dir.glob("audio/*.mp3"))
                
                if not audio_files:
                    return None
                
                # Get last file ID
                last_file = audio_files[-1]
                file_doc = self.db.fs.files.find_one(
                    {"filename": last_file.name},
                    sort=[("uploadDate", -1)]
                )
                
                if not file_doc:
                    return None
                    
                obj_id = file_doc['_id']
            else:
                raise TypeError("Expected string ID or Path object")
            
            # Generate URL
            return f"/api/audiobooks/{obj_id}"
            
        except Exception as e:
            logger.error("Failed to get audiobook URL: %s", str(e))
            raise

    def get_audio_file(self, file_id: str) -> Optional[bytes]:
        """
        Get audio file data.

        Args:
            file_id: ID of audio file

        Returns:
            Audio file data or None if not found

        Raises:
            Exception: If file retrieval fails
        """
        try:
            # Convert string ID to ObjectId
            obj_id = ObjectId(file_id)
            
            # Get file data
            if self.fs.exists(obj_id):
                return self.fs.get(obj_id).read()
            
            return None
            
        except Exception as e:
            logger.error("Failed to get audio file: %s", str(e))
            raise

    def cleanup(self, project_id: Optional[str] = None) -> None:
        """
        Clean up stored data.

        Args:
            project_id: Optional project ID to clean up. If None, all data is removed.

        Raises:
            Exception: If cleanup fails
        """
        try:
            if project_id:
                # Remove specific project data only
                query = {"metadata.project_id": project_id}
                
                # Remove documents from collections
                self.db.original_text.delete_many(query)
                self.db.translated_text.delete_many(query)
                self.db.optimized_text.delete_many(query)
                
                # Find all files for this project
                file_docs = self.db.fs.files.find(
                    {"metadata.project_id": project_id},
                    {"_id": 1}
                )
                
                # Delete each file
                for doc in file_docs:
                    self.fs.delete(doc["_id"])
            else:
                # Remove all documents
                self.db.original_text.delete_many({})
                self.db.translated_text.delete_many({})
                self.db.optimized_text.delete_many({})
                
                # Remove all files
                file_docs = self.db.fs.files.find({}, {"_id": 1})
                for doc in file_docs:
                    self.fs.delete(doc["_id"])
                
            logger.info(f"Cleanup completed successfully for {'all data' if not project_id else f'project {project_id}'}")
            
        except Exception as e:
            logger.error("Failed to clean up storage: %s", str(e))
            raise 