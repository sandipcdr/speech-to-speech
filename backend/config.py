import os

class Config:
    # Service Settings
    HOST = "0.0.0.0"
    PORT = 8000
    
    # STT Settings (faster-whisper)
    # Models: tiny, base, small, medium, large-v2, large-v3
    # 'small' is a good balance for CPU. 'medium' if you have strong CPU.
    STT_MODEL_SIZE = "small" 
    STT_DEVICE = "cpu"
    STT_COMPUTE_TYPE = "int8" # 'int8' for CPU, 'float16' for GPU
    
    # Translation Settings (NLLB / CTranslate2)
    # Using Facebook's NLLB-200-Distilled-600M for speed
    TRANSLATION_MODEL = "facebook/nllb-200-distilled-600M"
    TRANSLATION_DEVICE = "cpu"
    
    # TTS Settings (Piper)
    # Voices will be downloaded to ./models/piper
    PIPER_MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "piper")
    # Voice mapping structure
    # en_US-lessac-medium is a good standard voice
    # ja_JP-kaito-medium is a good Japanese voice
    TTS_VOICES = {
        "en": "en_US-lessac-medium",
        "ja": "ja_JP-kaito-medium"
    }

    # Audio Settings
    SAMPLE_RATE = 16000 # Standard for speech processing
