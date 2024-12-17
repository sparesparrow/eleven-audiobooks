# Eleven Audiobooks Architecture

## System Architecture
```mermaid
%%{init: {'theme': 'forest'}}%%
graph TB
    subgraph Input
        PDF[PDF Book]
    end
    
    subgraph Processing
        PDFProc[PDF Processor]
        Trans[Translation Pipeline]
        Opt[Text Optimizer]
        Audio[Audio Generator]
    end
    
    subgraph Storage
        MongoDB[(MongoDB)]
    end
    
    subgraph APIs
        Anthropic[Anthropic API]
        ElevenLabs[ElevenLabs API]
        DeepL[Translation APIs]
    end

    PDF --> PDFProc
    PDFProc --> Trans
    Trans --> Opt
    Opt --> Audio
    
    Opt -.-> Anthropic
    Audio -.-> ElevenLabs
    Trans -.-> DeepL
    
    PDFProc --> MongoDB
    Trans --> MongoDB
    Audio --> MongoDB

    style PDF fill:#d4e6b5
    style PDFProc fill:#8cc084
    style Trans fill:#8cc084
    style Opt fill:#8cc084
    style Audio fill:#8cc084
    style MongoDB fill:#3d8361
    style Anthropic fill:#a1c181
    style ElevenLabs fill:#a1c181
    style DeepL fill:#a1c181
```

## Component Interaction
```mermaid
%%{init: {'theme': 'forest'}}%%
sequenceDiagram
    participant M as Main
    participant PDF as PDFProcessor
    participant T as TranslationPipeline
    participant O as BatchTextOptimizer
    participant A as AudioGenerator
    participant S as StorageEngine

    M->>PDF: process(pdf_path)
    PDF->>S: store_original(chunks)
    M->>T: translate(chunks)
    T->>S: store_translated(chunks)
    M->>O: optimize_chapter(chunk)
    O->>S: store_optimized(path)
    M->>A: generate_chapter(path)
    A->>S: store_audio(response)
    S-->>M: get_audiobook_url()
```

## Data Flow
```mermaid
%%{init: {'theme': 'forest'}}%%
flowchart LR
    subgraph Input
        PDF[PDF Book]
    end
    
    subgraph Processing
        Text[Text Extraction]
        Chunks[Chapter Chunks]
        Trans[Translation]
        Opt[Optimization]
        Audio[Audio Generation]
    end
    
    subgraph Storage
        Original[Original Text]
        Translated[Translated Text]
        Optimized[Optimized Text]
        AudioFiles[Audio Files]
    end

    PDF --> Text
    Text --> Chunks
    Chunks --> Trans
    Trans --> Opt
    Opt --> Audio
    
    Chunks --> Original
    Trans --> Translated
    Opt --> Optimized
    Audio --> AudioFiles

    style PDF fill:#d4e6b5
    style Text fill:#8cc084
    style Chunks fill:#8cc084
    style Trans fill:#8cc084
    style Opt fill:#8cc084
    style Audio fill:#8cc084
    style Original fill:#3d8361
    style Translated fill:#3d8361
    style Optimized fill:#3d8361
    style AudioFiles fill:#3d8361
```

## Brief Description

The Eleven Audiobooks system is designed to convert large PDF books into high-quality audiobooks through a series of granular processing steps:

1. **PDF Processing**: 
   - Extracts text from PDF using PyPDF2
   - Splits into chapters using configurable markers
   - Tracks page numbers and references
   - Removes page markers, footnotes
   - Joins hyphenated words
   - Normalizes whitespace
   - Handles long text blocks by intelligent splitting
2. **Translation**: 
   - Processes each line individually through translation services
   - Maintains context between related lines
3. **Optimization**: 
   - Enhances each line for speech synthesis using Anthropic's API
   - Processes in small batches to stay within API limits
4. **Merging**: 
   - Recombines optimized lines while maintaining flow
   - Ensures proper paragraph and chapter transitions
5. **Audio Generation**: 
   - Creates audio files using ElevenLabs' text-to-speech service
   - Maintains consistent voice across merged content
6. **Storage and Data Model**: 
   - Uses Chapter dataclass to store metadata (number, title, content, page range)
   - Persists all intermediate results (chapters, lines, translations)
   - Uses MongoDB for metadata and file references
   - Stores large text chunks as separate files
   - Maintains traceability between original and processed content

The system uses asynchronous processing and batch operations where possible to improve efficiency. Each component is designed to be modular and independently testable.
