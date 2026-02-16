from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import base64
import json
import numpy as np
import time

# Import our pipeline
from audio_pipeline import AudioPipeline
from config import Config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline globally
# Note: This loads models on startup, which might take time.
print("Loading models...")

# Check if TTS models exist, if not download them (Fix for Docker volume shadowing)
import os
from config import Config
import download_models

piper_dir = Config.PIPER_MODEL_DIR
if os.path.exists(piper_dir):
    print(f"DEBUG: Piper dir exists. Content: {os.listdir(piper_dir)}")
else:
    print(f"DEBUG: Piper dir does not exist: {piper_dir}")

if not os.path.exists(piper_dir) or not os.listdir(piper_dir):
    print("TTS models not found (likely shadowed by Docker volume). Downloading now...")
    download_models.main()
else:
    # Check specific files just in case
    missing = False
    for filename in download_models.VOICES.keys():
        if not os.path.exists(os.path.join(piper_dir, filename)):
            missing = True
            break
    
    if missing:
        print("Some TTS models missing. Downloading...")
        download_models.main()

pipeline = AudioPipeline()
print("Models loaded.")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Speech-to-Speech Translation Service Running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected via WebSocket")
    
    try:
        # Buffer for audio chunks
        audio_buffer = bytearray()
        
        # Keep track of configuration sent by client
        session_config = {
            "source_lang": "en",
            "target_lang": "ja"
        }

        while True:
            # Receive message (text JSON or binary audio)
            try:
                message = await websocket.receive()
            except RuntimeError:
                # Handle "Cannot call 'receive' once a disconnect message has been received"
                break
            except WebSocketDisconnect:
                break

            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "config":
                        session_config["source_lang"] = data.get("source_lang", "en")
                        session_config["target_lang"] = data.get("target_lang", "ja")
                        print(f"Session config updated: {session_config}")
                        continue
                except:
                    pass

            if "bytes" in message:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)

                # Process every ~3 seconds of audio
                THRESHOLD = 96000 
                
                if len(audio_buffer) >= THRESHOLD:
                    # Convert to numpy array
                    audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # Calculate Volume (RMS)
                    rms = np.sqrt(np.mean(audio_np**2))
                    print(f"DEBUG: Audio RMS: {rms:.4f}")
                    
                    # Silence Threshold (Adjust if needed, 0.01 is a conservative starting point)
                    SILENCE_THRESHOLD = 0.01
                    
                    if rms < SILENCE_THRESHOLD:
                        print("DEBUG: Silence detected, skipping...")
                        audio_buffer = bytearray()
                        continue

                    # 1. STT (Run in thread to avoid blocking heartbeat)
                    transcript = await asyncio.to_thread(
                        pipeline.transcribe, 
                        audio_np, 
                        source_lang=session_config["source_lang"]
                    )
                    
                    if transcript:
                        print(f"Transcript: {transcript}")
                        await websocket.send_json({
                            "type": "transcript",
                            "text": transcript,
                            "is_final": True
                        })
                        
                        # 2. Translate (Run in thread)
                        translation = await asyncio.to_thread(
                            pipeline.translate,
                            transcript, 
                            source_lang=session_config["source_lang"],
                            target_lang=session_config["target_lang"]
                        )
                        
                        print(f"Translation: {translation}")
                        await websocket.send_json({
                            "type": "translation",
                            "text": translation
                        })
                        
                        # 3. TTS (Run in thread)
                        audio_wav = await asyncio.to_thread(
                            pipeline.synthesize,
                            translation, 
                            target_lang=session_config["target_lang"]
                        )
                        
                        if audio_wav:
                            print(f"DEBUG: Sending audio (size: {len(audio_wav)} bytes)")
                            # Send as base64 to play in browser
                            audio_b64 = base64.b64encode(audio_wav).decode('utf-8')
                            await websocket.send_json({
                                "type": "audio",
                                "payload": audio_b64
                            })
                        else:
                            print("DEBUG: Synthesis returned empty audio.")
                    
                    # Clear buffer
                    audio_buffer = bytearray()

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass # Already closed or failed

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
