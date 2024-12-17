import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from batch_text_reader import BatchTextReader, BatchResult

class TestBatchTextReader(unittest.IsolatedAsyncioTestCase):
    @patch('batch_text_reader.httpx.AsyncClient')
    async def test_get_batch_results(self, mock_client):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = '{"custom_id": "chapter_1", "message": {"content": [{"text": "test content"}]}}'
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        # Setup mock Anthropic client
        mock_anthropic = MagicMock()
        mock_anthropic.beta.messages.batches.retrieve = AsyncMock(return_value=MagicMock(
            processing_status="ended",
            results_url="http://test.com/results"
        ))
        
        reader = BatchTextReader(mock_anthropic)
        results = await reader.get_batch_results('test_batch_id')
        
        self.assertIsInstance(results[0], BatchResult)
        self.assertEqual(results[0].custom_id, "chapter_1")
        self.assertEqual(results[0].content, "test content")
