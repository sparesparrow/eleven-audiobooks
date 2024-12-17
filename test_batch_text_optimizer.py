import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from batch_text_optimizer import BatchTextOptimizer

class TestBatchTextOptimizer(unittest.IsolatedAsyncioTestCase):
    @patch('batch_text_reader.httpx.AsyncClient')
    @patch('batch_text_optimizer.Anthropic')
    async def test_optimize_chapter(self, mock_anthropic, mock_client):
        # Setup mock response for httpx
        mock_response = MagicMock()
        mock_response.text = '{"custom_id": "chapter_1", "message": {"content": [{"text": "optimized content"}]}}'
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        # Setup mock anthropic client
        mock_anthropic_client = MagicMock()
        mock_anthropic_client.beta.messages.batches.create = AsyncMock(return_value=MagicMock(id='test_batch_id'))
        mock_anthropic_client.beta.messages.batches.retrieve = AsyncMock(return_value=MagicMock(
            processing_status="ended",
            results_url="http://test.com/results"
        ))
        mock_anthropic.return_value = mock_anthropic_client
        
        optimizer = BatchTextOptimizer(api_key='test_key')
        with patch('batch_text_optimizer.BatchTextWriter') as mock_writer, \
             patch('batch_text_optimizer.BatchTextReader') as mock_reader:
            mock_writer_instance = MagicMock()
            mock_writer.return_value = mock_writer_instance
            mock_reader.return_value.get_batch_results = AsyncMock(return_value=[
                MagicMock(custom_id="chapter_1", content="optimized content")
            ])
            
            optimized_path = await optimizer.optimize_chapter(MagicMock(stem='test_chapter'))
            
            mock_writer.return_value.create_batch.assert_awaited_once()
            mock_reader.return_value.get_batch_results.assert_awaited_once_with('test_batch_id')
            self.assertIsNotNone(optimized_path)
