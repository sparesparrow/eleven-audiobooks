import typing
from pathlib import Path
from elevenlabs import ElevenLabs, VoiceSettings
from storage_engine import StorageEngine

class AudioGenerator:
    def __init__(self, api_key: str, voice_id: str, voice_settings: typing.Optional[VoiceSettings] = None, mongo_uri: str = "mongodb://localhost:27017"):
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.voice_settings = voice_settings or VoiceSettings()
        self.storage_engine = StorageEngine(mongo_uri=mongo_uri)

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

    def generate_chapter(self, chapter_input: typing.Union[str, Path], chapter_index: int = None, previous_request_ids: typing.Optional[typing.Sequence[str]] = None) -> typing.Tuple[str, str]:
        """
        Generates audio for a specific chapter.

        Args:
            chapter_input (Union[str, Path]): The text or file path of the chapter.
            chapter_index (Optional[int]): The index of the chapter for filename generation.
            previous_request_ids (typing.Optional[typing.Sequence[str]]): Request IDs of previous audio generations for context.

        Returns:
            typing.Tuple[str, str]: A tuple containing the file path of the generated audio and the request ID.
        """
        # If input is a file path, read its contents
        if isinstance(chapter_input, Path):
            with open(chapter_input, 'r', encoding='utf-8') as f:
                chapter_text = f.read()
        else:
            chapter_text = chapter_input
        # Converts text into speech using a voice of your choice and returns JSON containing audio as a base64 encoded string together with information on when which character was spoken.
        response = self.client.text_to_speech.convert_with_timestamps(
            voice_id=self.voice_id,
            text=chapter_text,
            voice_settings=self.voice_settings,
            previous_request_ids=previous_request_ids,
        )

        request_id = response.headers["request-id"]
        
        # Generate filename if chapter_index is provided
        filename = f"chapter_{chapter_index}.mp3" if chapter_index is not None else None
        audio_path = self.storage_engine.store_audio(response, filename=filename)
        
        return audio_path, request_id
