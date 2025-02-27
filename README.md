# MOVED [HERE](https://github.com/sparesparrow/human-action)

---

---

# Eleven Audiobooks - LEGACY

[![Test](https://github.com/sparesparrow/eleven-audiobooks/actions/workflows/test.yml/badge.svg)](https://github.com/sparesparrow/eleven-audiobooks/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/sparesparrow/eleven-audiobooks/branch/main/graph/badge.svg)](https://codecov.io/gh/sparesparrow/eleven-audiobooks)
[![PyPI version](https://badge.fury.io/py/eleven-audiobooks.svg)](https://badge.fury.io/py/eleven-audiobooks)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python application that automates the process of converting PDF books into high-quality audiobooks. It leverages the Anthropic API for text optimization and the ElevenLabs API for text-to-speech conversion.

## Features

- 📚 Extracts text from PDF books with intelligent chapter detection
- 🌐 Translates content from English to Czech using multiple translation services
- ✨ Optimizes text for natural-sounding speech synthesis using Anthropic's API
- 🎧 Generates high-quality audio with word-level timing using ElevenLabs API
- 💾 Stores all processing artifacts with MongoDB integration
- 📊 Provides detailed progress tracking and error recovery
- 🔄 Supports resuming from the last successful stage

## Requirements

- Python 3.8 or higher
- MongoDB 4.4 or higher
- API keys for:
  - Anthropic (Claude)
  - ElevenLabs
  - DeepL (optional, for translation)

## Installation

### From PyPI

```bash
pip install eleven-audiobooks
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/sparesparrow/eleven-audiobooks.git
cd eleven-audiobooks
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev,test]"
```

## Configuration

Set up the following environment variables:

```bash
export ANTHROPIC_API_KEY=your_anthropic_api_key
export ELEVENLABS_API_KEY=your_elevenlabs_api_key
export DEEPL_API_KEY=your_deepl_api_key  # Optional, for translation
export MONGO_URI=mongodb://localhost:27017/  # Optional, defaults to localhost
export VOICE_ID=your_preferred_voice_id  # Optional, defaults to a standard voice
```

Or create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
DEEPL_API_KEY=your_deepl_api_key
MONGO_URI=mongodb://localhost:27017/
VOICE_ID=your_preferred_voice_id
```

## Usage

### Command Line

Process a PDF book:
```bash
python -m eleven_audiobooks data/book.pdf
```

Process and translate a book:
```bash
python -m eleven_audiobooks data/book.pdf --translate
```

### Python API

```python
import asyncio
from pathlib import Path
from eleven_audiobooks import PipelineManager

async def process_book(pdf_path: str) -> str:
    pipeline = PipelineManager(
        pdf_path=Path(pdf_path),
        output_dir=Path('./output'),
        mongo_db=your_mongo_client,
        config={
            "ANTHROPIC_API_KEY": "your_api_key",
            "ELEVENLABS_API_KEY": "your_api_key",
            "DEEPL_API_KEY": "your_api_key",  # Optional
        }
    )
    
    # Process book and get audiobook URL
    audiobook_url = await pipeline.process(translate=False)
    return audiobook_url

# Run the pipeline
url = asyncio.run(process_book('path/to/book.pdf'))
print(f"Audiobook available at: {url}")
```

## Project Status

The project is currently under active development, with several key components functional and others in progress:

- ✅ **Core Pipeline** - Complete
- ✅ **PDF Processing** - Basic functionality working, enhancements in progress
- ✅ **Translation** - Basic functionality working, service abstraction in progress
- ✅ **Text Optimization** - Working with improvements for large inputs
- ✅ **Audio Generation** - Working with chunking and retries
- ✅ **Storage Engine** - Complete with data validation and indexing

The application follows a modular pipeline architecture with enhanced error handling and recovery mechanisms. Refer to `TODO.txt` for detailed implementation plans and progress tracking.

## Recent Improvements

### Critical Bug Fixes

1. **BatchTextOptimizer Integration** - Fixed implementation of `optimize_chapter` method to properly handle file operations
2. **Storage Engine URL Generation** - Updated to handle both file IDs and paths correctly
3. **PDF Processor Text Cleaning** - Improved OCR correction to preserve numeric values with context-aware processing
4. **Translation Chunk Recombination** - Enhanced chapter boundary preservation during translation

### Module Enhancements

1. **Text Optimization**
   - Added rate limiting and concurrency control for API calls
   - Improved text splitting to preserve paragraph and sentence structure
   - Implemented retry mechanism with exponential backoff

2. **Audio Generation**
   - Added text chunking for handling large inputs
   - Implemented audio file concatenation 
   - Added retry logic with configurable parameters

3. **Storage Engine**
   - Added data validation before storage operations
   - Implemented versioning for all stored artifacts
   - Added proper MongoDB indexing for efficient queries
   - Enhanced cleanup mechanism with project-specific options

## Known Issues and Limitations

Please refer to the `TODO.txt` file for current issues and planned improvements. The main limitations currently are:

1. OCR quality can be inconsistent with certain PDF formats
2. Translation may not preserve all nuances of the original text
3. Large files may require significant processing time and resources
4. API rate limits may affect processing speed

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=eleven_audiobooks

# Run specific test file
pytest tests/test_pdf_processor.py
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
ruff check .

# Type check
mypy .
```

### Debugging

When encountering issues, check the log file at `audiobook.log` for detailed information. You can increase verbosity with:

```bash
export LOG_LEVEL=DEBUG
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for their Claude API
- [ElevenLabs](https://elevenlabs.io/) for their text-to-speech API
- [DeepL](https://www.deepl.com/) for their translation API
- All contributors who have helped improve this project
