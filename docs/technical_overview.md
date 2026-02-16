# Technical Overview: Speech-to-Speech Translation

This document details the technical architecture, model selection, and data flow of the local speech-to-speech translation MVP.

## Architecture

The system follows a classic client-server architecture, optimized for real-time streaming.

### 1. Frontend (Next.js)
-   **Role**: Captures audio (Microphone or System), handles user interaction, and plays back translated audio.
-   **Tech**: React, WebSocket API, Web Audio API (`scriptProcessor` / `AudioContext`).
-   **Key Feature**: Uses `navigator.mediaDevices.getDisplayMedia` to capture system audio, enabling translation of meetings (Zoom/Teams) running in other windows.

### 2. Backend (FastAPI)
-   **Role**: Orchestrates the AI pipeline.
-   **Tech**: Python, FastAPI, WebSockets (`/ws`), PyTorch.
-   **Concurrency**: Uses Python's `asyncio` to handle WebSocket connections, though the heavy lifting (inference) is blocking. For an MVP, this is sufficient.

## AI Pipeline & Model Selection

The pipeline consists of three distinct stages: **STT -> Translate -> TTS**. All models run **locally** within the Docker container.

### Phase 1: Speech-to-Text (STT)
-   **Model**: `faster-whisper` (Implementation of OpenAI's Whisper model).
-   **Why this model?**
    -   **Accuracy**: Whisper is currently SOTA (State of the Art) for robust speech recognition.
    -   **Performance**: `faster-whisper` uses CTranslate2, which is up to 4x faster than the original OpenAI PyTorch implementation and uses less memory.
-   **Configuration**:
    -   Model Size: `small` (Good balance of speed vs accuracy for CPU).
    -   Compute Type: `int8` (Quantization for speed).

### Phase 2: Translation (MT)
-   **Model**: `NLLB-200` (No Language Left Behind) by Meta AI.
-   **Implementation**: `facebook/nllb-200-distilled-600M` via HuggingFace Transformers.
-   **Why this model?**
    -   **Context Awareness**: Better than direct word-for-word translation.
    -   **Size**: The distilled 600M version is lightweight enough to run on a CPU while maintaining good quality for casual conversation.
    -   **Multilingual**: Supports 200+ languages, allowing easy expansion beyond JA<->EN.

### Phase 3: Text-to-Speech (TTS)
-   **Model**: `Piper TTS`.
-   **Why this model?**
    -   **Speed**: Designed specifically for low-latency, real-time synthesis on devices like Raspberry Pi, making it incredibly fast on a server CPU.
    -   **Quality**: Uses VITS (Variational Inference with adversarial learning for end-to-end Text-to-Speech), offering natural-sounding voices compared to older concatenative systems (like eSpeak).
-   **Voices**:
    -   English: `en_US-lessac-medium`
    -   Japanese: `ja_JP-ami-medium`

## Data Flow

1.  **Capture**: Frontend captures standard PCM Audio (16kHz, mono).
2.  **Stream**: Audio Chunks are sent over WebSocket to Backend.
3.  **Buffer**: Backend buffers chunks until a threshold (e.g., 2-3 seconds) is met. *Future improvement: Use VAD (Voice Activity Detection) to detect sentence breaks.*
4.  **Inference**:
    -   `STT Start`: Audio -> Japanese Text.
    -   `Translate`: Japanese Text -> English Text.
    -   `TTS`: English Text -> English Audio (WAV bytes).
5.  **Playback**: Backend sends Audio Bytes (Base64) -> Frontend -> AudioContext -> Speakers.

## Infrastructure

-   **Docker**: Encapsulates all dependencies (`ffmpeg`, `python`, system libs) to ensure "it just works" regardless of host OS.
-   **Models Volume**: Models are downloaded to a volume (`./backend/models`) so they persist between restarts and don't need re-downloading.
