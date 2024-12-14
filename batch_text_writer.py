import logging
from pathlib import Path
from typing import List

from anthropic import Anthropic
from anthropic.types.beta.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.beta.messages.batch_create_params import Request

class BatchTextWriter:
    def __init__(self, client: Anthropic):
        self.client = client
        self.logger = logging.getLogger(__name__)

    async def create_batch(self, requests: List[Request]) -> str:
        """Create a new message batch and return the batch ID."""
        try:
            batch_response = await self.client.beta.messages.batches.create(requests=requests)
            return batch_response.id
        except Exception as e:
            self.logger.error(f"Failed to create batch: {e}")
            raise

    def persist_batch_id(self, batch_id: str, chapter_path: Path):
        """Save the batch ID to a file for the given chapter."""
        batch_id_path = chapter_path.with_suffix(".batch_id")
        with open(batch_id_path, "w") as f:
            f.write(batch_id)

