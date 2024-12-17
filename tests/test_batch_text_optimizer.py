import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

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
        
        # Test optimize_chapter
        optimizer = BatchTextOptimizer(api_key='test_key')
        chapter_path = MagicMock(spec=Path)
        chapter_path.stem = 'test_chapter'
        chapter_path.read_text.return_value = "Test content\n\nMore content"
        
        optimized_path = await optimizer.optimize_chapter(chapter_path)
        
        # Verify basic functionality
        self.assertIsNotNone(optimized_path)
        mock_anthropic_client.beta.messages.batches.create.assert_awaited_once()

    def test_split_into_chunks(self):
        optimizer = BatchTextOptimizer()
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = optimizer._split_into_chunks(content, max_chunk_size=30)
        
        self.assertGreater(len(chunks), 1)
        self.assertIn("First paragraph", chunks[0])
