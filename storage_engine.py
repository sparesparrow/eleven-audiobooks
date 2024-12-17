# storage_engine.py

from pymongo import MongoClient

class StorageEngine:
    def __init__(self, mongo_uri):
        self.client = MongoClient(mongo_uri)
        self.db = self.client["audiobook_db"]
        self.original_collection = self.db["original"]
        self.translated_collection = self.db["translated"]
        self.audio_collection = self.db["audio"]

    def store_original(self, chunks):
        self.original_collection.insert_many([{"text": chunk} for chunk in chunks])

    def store_translated(self, chunks):
        self.translated_collection.insert_many([{"text": chunk} for chunk in chunks])

    def store_audio(self, audio_data, filename=None):
        """Store audio data in MongoDB with optional filename."""
        data = {"audio": audio_data}
        if filename:
            data["filename"] = filename
        audio_id = self.audio_collection.insert_one(data).inserted_id
        return str(audio_id)

    def get_audiobook_url(self, audio_id):
        audio_data = self.audio_collection.find_one({"_id": audio_id})
        if audio_data:
            return audio_data["url"]
        return None
