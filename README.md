# Audiobook Generator

The Audiobook Generator is a Python application that automates the process of converting a PDF book into an audiobook. It leverages the Anthropic API for text optimization and the ElevenLabs API for text-to-speech conversion.

## Features

- Extracts text from a PDF book and splits it into chapters
- Translates the text from English to Czech using the DeepL API
- Optimizes the translated text for speech synthesis using the Anthropic API
- Generates audio files for each chapter using the ElevenLabs API
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
source .venv/bin/activate
pip install -e .
pip install -r requirements.txt
python setup.py install
```


3. Set up the necessary environment variables:

```bash
export ANTHROPIC_API_KEY=your_anthropic_api_key
export ELEVENLABS_API_KEY=your_elevenlabs_api_key
export DEEPL_API_KEY=your_deepl_api_key
```

## Usage

To generate an audiobook from a PDF file, run the following command:

```bash
python main.py path/to/your/book.pdf
```

The application will process the PDF, translate the content, optimize the text, generate audio files, and provide a URL to access the audiobook.

## Testing

To run the unit tests, use the following command:

```bash
python -m unittest discover tests/
```

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
