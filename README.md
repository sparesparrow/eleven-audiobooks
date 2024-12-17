# Audiobook Generator

The Audiobook Generator is a Python application that automates the process of converting a PDF book into an audiobook. It leverages the Anthropic API for text optimization and the ElevenLabs API for text-to-speech conversion.

## Features

- Extracts text from a PDF book and splits it into chapters
- Translates the text from English to Czech using multiple translation services
- Optimizes the translated text for speech synthesis using Anthropic's API
- Generates audio files with word-level timing information using ElevenLabs API
- Stores the original, translated, and optimized text, as well as the generated audio files
- Provides a URL to access the generated audiobook

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/audiobook-generator.git
cd audiobook-generator
```

2. Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

3. Set up the necessary environment variables:

```bash
export ANTHROPIC_API_KEY=your_anthropic_api_key
export ELEVENLABS_API_KEY=your_elevenlabs_api_key
export DEEPL_API_KEY=your_deepl_api_key
```

## Usage

To generate an audiobook from a PDF file:

```bash
python main.py path/to/your/book.pdf
```

The application will:
1. Process the PDF and extract text
2. Split into chapters using configurable markers
3. Translate content if needed
4. Optimize text for speech synthesis
5. Generate audio with timing information
6. Provide a URL to access the audiobook

## Testing

To run the unit tests:

```bash
python -m pytest tests/
```

## Project Structure

- `pdf_processor.py`: Handles PDF text extraction and chapter splitting
- `translation_pipeline.py`: Manages text translation through multiple services
- `batch_text_optimizer.py`: Optimizes text for speech synthesis
- `audio_generator.py`: Generates audio with timing information
- `storage_engine.py`: Handles data persistence
- `main.py`: Main application entry point

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
