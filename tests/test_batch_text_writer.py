import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from batch_text_writer import BatchTextWriter
from anthropic.types.beta.messages.batch_create_params import Request

class TestBatchTextWriter(unittest.IsolatedAsyncioTestCase):
    async def test_create_batch(self):
        mock_client = MagicMock()
        mock_client.beta.messages.batches.create = AsyncMock(return_value=MagicMock(id='test_batch_id'))
        
        writer = BatchTextWriter(mock_client)
        requests: List[Request] = []  # Empty list for simple test
        
        batch_id = await writer.create_batch(requests)
        
        self.assertEqual(batch_id, 'test_batch_id')
        mock_client.beta.messages.batches.create.assert_awaited_once_with(requests=requests)
