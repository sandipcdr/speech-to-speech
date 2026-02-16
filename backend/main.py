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
                            # Send as base64 to play in browser
                            audio_b64 = base64.b64encode(audio_wav).decode('utf-8')
                            await websocket.send_json({
                                "type": "audio",
                                "payload": audio_b64
                            })
                    
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
