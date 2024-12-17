import unittest
from unittest.mock import MagicMock, patch

from audio_generator import AudioGenerator

class TestAudioGenerator(unittest.TestCase):
    @patch('audio_generator.StorageEngine')
    @patch('audio_generator.ElevenLabs')
    def test_generate_chapter(self, mock_elevenlabs, mock_storage_engine):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.headers = {"request-id": "test-request-id"}
        
        mock_client = MagicMock()
        mock_client.text_to_speech.convert_as_stream.return_value = mock_response
        mock_elevenlabs.return_value = mock_client
        
        # Setup mock storage
        mock_storage_instance = MagicMock()
        mock_storage_instance.store_audio.return_value = "test_audio_path"
        mock_storage_engine.return_value = mock_storage_instance
        
        audio_generator = AudioGenerator(api_key='test_key', voice_id='test_voice')
        audio_path, request_id = audio_generator.generate_chapter('test_text', 1)
        
        mock_client.text_to_speech.convert_as_stream.assert_called_once()
        self.assertEqual(audio_path, "test_audio_path")
        self.assertEqual(request_id, "test-request-id")
