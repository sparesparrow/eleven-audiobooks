import unittest
from unittest.mock import AsyncMock, MagicMock, patch

class TestMain(unittest.IsolatedAsyncioTestCase):
    @patch('main.PDFProcessor')
    @patch('main.TranslationPipeline')
    @patch('main.StorageEngine')
    @patch('main.AudioGenerator')
    @patch('main.BatchTextOptimizer')
    async def test_process_book(self, mock_optimizer, mock_audio_generator,
                                mock_storage_engine, mock_translation_pipeline, mock_pdf_processor):
        mock_pdf_processor.return_value.process.return_value = ['chunk1', 'chunk2']
        mock_translation_pipeline.return_value.translate.return_value = ['translated1', 'translated2']
        mock_optimizer.return_value.optimize_chapter = AsyncMock(side_effect=['optimized1', 'optimized2'])
        mock_storage_engine.return_value.get_optimized_chapters.return_value = ['optimized1', 'optimized2']
        mock_storage_engine.return_value.get_audiobook_url.return_value = 'test_url'
        
        audiobook_url = await process_book(MagicMock())
        
        mock_pdf_processor.return_value.process.assert_called_once()
        mock_translation_pipeline.return_value.translate.assert_called_once_with(['chunk1', 'chunk2'])
        mock_storage_engine.return_value.store_original.assert_called_once_with(['chunk1', 'chunk2'])
        mock_storage_engine.return_value.store_translated.assert_called_once_with(['translated1', 'translated2'])
        mock_optimizer.return_value.optimize_chapter.assert_awaited_with('translated1')
        mock_optimizer.return_value.optimize_chapter.assert_awaited_with('translated2')
        mock_storage_engine.return_value.store_optimized.assert_any_call('optimized1')
        mock_storage_engine.return_value.store_optimized.assert_any_call('optimized2')
        mock_audio_generator.return_value.generate_chapter.assert_any_call('optimized1')
        mock_audio_generator.return_value.generate_chapter.assert_any_call('optimized2')
        self.assertEqual(audiobook_url, 'test_url')
