import json
import logging
from dataclasses import dataclass
from typing import List, Optional

import httpx
from anthropic import Anthropic

@dataclass
class BatchResult:
    custom_id: str
    content: str
    error: Optional[str] = None

class BatchTextReader:
    def __init__(self, client: Anthropic):
        self.client = client
        self.logger = logging.getLogger(__name__)

    async def get_batch_results(self, batch_id: str) -> List[BatchResult]:
        """Retrieve the results for a given batch ID."""
        try:
            status = await self.client.beta.messages.batches.retrieve(batch_id)
            
            if status.processing_status == "ended" and status.results_url:
                results = await self._download_results(status.results_url)
                return [
                    BatchResult(
                        custom_id=r["custom_id"],
                        content=r["message"]["content"][0]["text"],
                        error=r.get("error")
                    )
                    for r in results
                ]
            else:
                self.logger.warning(f"Batch {batch_id} not ready, status: {status.processing_status}")
                return []
        
        except Exception as e:
            self.logger.error(f"Failed to get batch results: {e}")
            raise
        
    async def _download_results(self, results_url: str) -> List[dict]:
        """Download the JSONL results file from the given URL."""
        headers = self.client.headers 
        headers["anthropic-version"] = "2023-06-01"
        headers["anthropic-beta"] = "message-batches-2024-09-24"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(results_url, headers=headers)
            response.raise_for_status()
            
            results = []
            for line in response.text.splitlines():
                results.append(json.loads(line))
            return results

