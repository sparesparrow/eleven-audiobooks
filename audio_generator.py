import typing
from elevenlabs import ElevenLabs, VoiceSettings
from .storage_engine import StorageEngine

class AudioGenerator:
    def __init__(self, api_key: str, voice_id: str, voice_settings: typing.Optional[VoiceSettings] = None):
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.voice_settings = voice_settings or VoiceSettings()
        self.storage_engine = StorageEngine()

    def generate(self, text: str, previous_request_ids: typing.Optional[typing.Sequence[str]] = None) -> str:
        """
        Generates audio from the given text using the ElevenLabs API.

        Args:
            text (str): The text to generate audio from.
            previous_request_ids (typing.Optional[typing.Sequence[str]]): Request IDs of previous audio generations for context.

        Returns:
            str: The file path of the generated audio.
        """
        response = self.client.text_to_speech.convert_as_stream(
            voice_id=self.voice_id,
            text=text,
            voice_settings=self.voice_settings,
            previous_request_ids=previous_request_ids,
        )

        audio_path = self.storage_engine.store_audio(response)
        return audio_path

    def generate_chapter(self, chapter_text: str, chapter_index: int, previous_request_ids: typing.Optional[typing.Sequence[str]] = None) -> typing.Tuple[str, str]:
        """
        Generates audio for a specific chapter.

        Args:
            chapter_text (str): The text of the chapter.
            chapter_index (int): The index of the chapter.
            previous_request_ids (typing.Optional[typing.Sequence[str]]): Request IDs of previous audio generations for context.

        Returns:
            typing.Tuple[str, str]: A tuple containing the file path of the generated audio and the request ID.
        """
        response = self.client.text_to_speech.convert_as_stream(
            voice_id=self.voice_id,
            text=chapter_text,
            voice_settings=self.voice_settings,
            previous_request_ids=previous_request_ids,
        )

        request_id = response.headers["request-id"]
        audio_path = self.storage_engine.store_audio(response, filename=f"chapter_{chapter_index}.mp3")
        return audio_path, request_id
