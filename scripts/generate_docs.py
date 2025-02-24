#!/usr/bin/env python3
"""Generate documentation for the Eleven Audiobooks project."""

import os
import shutil
import subprocess
from pathlib import Path

import pdoc


def generate_docs() -> None:
    """Generate documentation using pdoc."""
    # Project root directory
    root_dir = Path(__file__).parent.parent
    
    # Documentation output directory
    docs_dir = root_dir / "docs"
    api_dir = docs_dir / "api"
    
    # Clean existing documentation
    if api_dir.exists():
        shutil.rmtree(api_dir)
    
    # Create documentation directories
    api_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate API documentation
    module_name = "eleven_audiobooks"
    pdoc.pdoc(
        module_name,
        output_directory=api_dir,
        template_directory=docs_dir / "_templates" if (docs_dir / "_templates").exists() else None
    )
    
    # Copy README.md to docs
    shutil.copy2(root_dir / "README.md", docs_dir / "index.md")
    
    # Generate additional documentation files
    generate_architecture_doc(docs_dir)
    generate_contributing_doc(docs_dir)
    generate_changelog_doc(docs_dir)


def generate_architecture_doc(docs_dir: Path) -> None:
    """Generate architecture documentation."""
    content = """# Architecture

## Overview

The Eleven Audiobooks project is designed as a pipeline-based system for converting PDF books into audiobooks. The system is composed of several key components that work together to process, translate, optimize, and generate audio content.

## Components

### PDF Processor

- Extracts text from PDF files
- Splits content into chapters
- Handles page markers and footnotes
- Validates chapter structure

### Translation Pipeline

- Supports multiple translation services
- Handles API rate limiting and retries
- Preserves text formatting
- Validates translation quality

### Text Optimizer

- Uses Anthropic's API for text optimization
- Improves text for speech synthesis
- Handles batch processing
- Maintains context across chunks

### Audio Generator

- Uses ElevenLabs API for text-to-speech
- Generates high-quality audio
- Provides word-level timing information
- Supports multiple voices

### Storage Engine

- Manages persistent storage with MongoDB
- Handles artifact management
- Provides URL generation
- Supports data versioning

### Pipeline Manager

- Orchestrates component interaction
- Manages pipeline state
- Handles error recovery
- Tracks progress

## Data Flow

1. PDF Processing
   - Input: PDF file
   - Output: Structured chapter text

2. Translation (Optional)
   - Input: Chapter text
   - Output: Translated text

3. Text Optimization
   - Input: (Translated) text
   - Output: Optimized text for speech

4. Audio Generation
   - Input: Optimized text
   - Output: Audio files with timing

## State Management

The pipeline uses a state management system to:
- Track progress
- Handle failures
- Support resumption
- Manage artifacts

## Error Handling

- Component-level error handling
- Pipeline-level recovery
- Partial results handling
- Comprehensive logging

## Performance

- Asynchronous processing
- Batch optimization
- Parallel audio generation
- Progress tracking

## Security

- API key management
- Input validation
- Error sanitization
- Rate limiting

## Future Improvements

1. Enhanced Error Recovery
   - Automatic retries
   - Checkpoint system
   - State persistence

2. Performance Optimization
   - Caching system
   - Parallel processing
   - Resource management

3. Quality Improvements
   - Enhanced text cleaning
   - Better chapter detection
   - Audio quality validation

4. Monitoring
   - Performance metrics
   - Error tracking
   - Usage statistics"""
    
    (docs_dir / "architecture.md").write_text(content)


def generate_contributing_doc(docs_dir: Path) -> None:
    """Generate contributing documentation."""
    # Copy CONTRIBUTING.md to docs
    root_dir = Path(__file__).parent.parent
    if (root_dir / "CONTRIBUTING.md").exists():
        shutil.copy2(root_dir / "CONTRIBUTING.md", docs_dir / "contributing.md")


def generate_changelog_doc(docs_dir: Path) -> None:
    """Generate changelog documentation."""
    content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- PDF processing functionality
- Translation pipeline
- Text optimization
- Audio generation
- MongoDB integration
- Pipeline state management
- Comprehensive testing
- Documentation

### Changed
- None

### Deprecated
- None

### Removed
- None

### Fixed
- None

### Security
- None

## [0.1.0] - 2024-01-01

### Added
- Initial release
- Basic PDF to audiobook conversion
- English to Czech translation
- Text optimization
- Audio generation"""
    
    (docs_dir / "changelog.md").write_text(content)


if __name__ == "__main__":
    generate_docs() 