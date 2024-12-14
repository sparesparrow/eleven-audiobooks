import unittest
from unittest.mock import MagicMock, patch

from audio_generator import AudioGenerator

class TestAudioGenerator(unittest.TestCase):
    @patch('audio_generator.ElevenLabs')
    def test_generate_chapter(self, mock_elevenlabs):
        mock_client = MagicMock()
        mock_elevenlabs.return_value = mock_client
        
        audio_generator = AudioGenerator(api_key='test_key', voice_id='test_voice')
        audio_path, request_id = audio_generator.generate_chapter('test_text', 1)
        
        mock_client.text_to_speech.convert_as_stream.assert_called_once_with(
            voice_id='test_voice',
            text='test_text',
            voice_settings=audio_generator.voice_settings,
            previous_request_ids=None
        )
        self.assertIsNotNone(audio_path)
        self.assertIsInstance(request_id, str)
