# Speech-to-Speech Translation MVP (Local)

A near-zero-cost speech translation system that runs entirely locally.
Supports microphone input (for your voice) and system audio capture (for meetings).

**Languages:** English <-> Japanese
**Stack:** FastAPI (Backend), Next.js (Frontend), Faster-Whisper (STT), NLLB (Translation), Piper (TTS).

## Prerequisites
- Docker & Docker Compose
- Nvidia GPU (Optional, defaults to CPU)
- ~2GB of Disk Space for models

## Quick Start

1. **Start the application**
   ```bash
   docker-compose up --build
   ```
   *Note: First run will download models (~1-2GB), so be patient.*

2. **Access the UI**
   Open http://localhost:3001

3. **Usage**
   - **Mode Selection**:
     - **Microphone**: Use this to translate your own voice.
     - **System Audio**: Use this to translate others in a meeting (Zoom/Teams). Browser will ask to share a tab/screen - select the meeting window and **check "Share System Audio"**.
   - **Start**: Click Start.
   - **Language**: Toggle between EN <-> JA.

## Development

**Backend**:
```bash
cd backend
pip install -r requirements.txt
python download_models.py
uvicorn main:app --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## Troubleshooting
- **No Audio**: Ensure browser permissions are granted.
- **Slow Performance**: CPU inference is used by default. For faster results, uncomment GPU settings in `backend/config.py` if you have an Nvidia card.
