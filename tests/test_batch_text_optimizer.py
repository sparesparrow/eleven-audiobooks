import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from batch_text_optimizer import BatchTextOptimizer

class TestBatchTextOptimizer(unittest.IsolatedAsyncioTestCase):
    @patch('batch_text_reader.httpx.AsyncClient')
    @patch('batch_text_optimizer.Anthropic')
    async def test_optimize_chapter(self, mock_anthropic, mock_client):
        # Setup mocks
        mock_response = MagicMock()
        mock_response.text = '{"custom_id": "chapter_1", "message": {"content": [{"text": "optimized content"}]}}'
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        mock_anthropic_client = MagicMock()
        mock_anthropic_client.beta.messages.batches.create = AsyncMock(return_value=MagicMock(id='test_batch_id'))
        mock_anthropic_client.beta.messages.batches.retrieve = AsyncMock(return_value=MagicMock(
            processing_status="ended",
            results_url="http://test.com/results"
        ))
        mock_anthropic.return_value = mock_anthropic_client
        
        # Test optimize_chapter
        optimizer = BatchTextOptimizer(api_key='test_key')
        chapter_path = MagicMock(spec=Path)
        chapter_path.stem = 'test_chapter'
        
        optimized_path = await optimizer.optimize_chapter(chapter_path)
        
        # Verify basic functionality
        self.assertIsNotNone(optimized_path)
