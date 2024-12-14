import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from batch_text_optimizer import BatchTextOptimizer

class TestBatchTextOptimizer(unittest.IsolatedAsyncioTestCase):
    @patch('batch_text_optimizer.Anthropic')
    async def test_optimize_chapter(self, mock_anthropic):
        mock_client = MagicMock()
        mock_client.beta.messages.batches.create = AsyncMock(return_value=MagicMock(id='test_batch_id'))
        mock_anthropic.return_value = mock_client
        
        optimizer = BatchTextOptimizer(api_key='test_key')
        with patch('batch_text_optimizer.BatchTextWriter') as mock_writer, \
             patch('batch_text_optimizer.BatchTextReader') as mock_reader:
            mock_writer.return_value.create_batch = AsyncMock(return_value='test_batch_id')
            mock_reader.return_value.get_batch_results = AsyncMock(return_value=[])
            
            optimized_path = await optimizer.optimize_chapter(MagicMock(stem='test_chapter'))
            
            mock_writer.return_value.create_batch.assert_awaited_once()
            mock_writer.return_value.persist_batch_id.assert_called_once_with('test_batch_id', unittest.mock.ANY)
            mock_reader.return_value.get_batch_results.assert_awaited_once_with('test_batch_id')
            self.assertIsNotNone(optimized_path)
