import io
import torch
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from piper import PiperVoice
import os
from config import Config

class AudioPipeline:
    def __init__(self):
        print("Initializing Audio Pipeline...")
        self.device = Config.STT_DEVICE
        
        # 1. STT: Faster-Whisper
        print(f"Loading Whisper model ({Config.STT_MODEL_SIZE})...")
        self.stt_model = WhisperModel(
            Config.STT_MODEL_SIZE, 
            device=self.device, 
            compute_type=Config.STT_COMPUTE_TYPE
        )
        
        # 2. Translation: NLLB (using transformers for simplicity in MVP, upgrade to CTranslate2 for speed if needed)
        print(f"Loading Translation model ({Config.TRANSLATION_MODEL})...")
        self.translator_tokenizer = AutoTokenizer.from_pretrained(Config.TRANSLATION_MODEL)
        self.translator_model = AutoModelForSeq2SeqLM.from_pretrained(Config.TRANSLATION_MODEL)
        
        # 3. TTS: Piper
        print("Loading TTS models...")
        self.tts_voices = {}
        for lang_code, model_name in Config.TTS_VOICES.items():
            model_path = os.path.join(Config.PIPER_MODEL_DIR, f"{model_name}.onnx")
            
            # Check if exists, if not, might need to run download_models.py first
            if os.path.exists(model_path):
                # PiperVoice is a wrapper around onnxruntime
                self.tts_voices[lang_code] = PiperVoice.load(model_path)
            else:
                print(f"Warning: TTS model not found at {model_path}. Run download_models.py")

    def transcribe(self, audio_data: np.ndarray, source_lang: str):
        # audio_data is float32 numpy array
        # faster-whisper segments audio itself
        # beam_size=5 for better accuracy
        segments, _ = self.stt_model.transcribe(
            audio_data, 
            language=source_lang, 
            beam_size=5
        )
        # Collect full text
        text = " ".join([segment.text for segment in segments])
        return text.strip()

    def translate(self, text: str, source_lang: str, target_lang: str):
        print(f"DEBUG: Translating '{text}' from {source_lang} to {target_lang}")
        if not text:
            return ""
        
        # Map simple lang codes to NLLB codes
        # en -> eng_Latn, ja -> jpn_Jpan
        lang_map = {
            "en": "eng_Latn",
            "ja": "jpn_Jpan",
            # Add more if needed
        }
        
        src_code = lang_map.get(source_lang)
        tgt_code = lang_map.get(target_lang)
        
        print(f"DEBUG: NLLB Codes: src={src_code}, tgt={tgt_code}")

        if not src_code or not tgt_code:
            print("DEBUG: Language code not found in map, returning original text")
            return text # Fallback: return original
            
        try:
            print("DEBUG: Tokenizing input...")
            inputs = self.translator_tokenizer(text, return_tensors="pt")
            
            print("DEBUG: Generating translation...")
            
            # Use convert_tokens_to_ids for compatibility
            forced_bos_token_id = self.translator_tokenizer.convert_tokens_to_ids(tgt_code)
            print(f"DEBUG: Forced BOS token ID for {tgt_code}: {forced_bos_token_id}")
            
            translated_tokens = self.translator_model.generate(
                **inputs, 
                forced_bos_token_id=forced_bos_token_id, 
                max_length=128
            )
            
            print("DEBUG: Decoding output...")
            result = self.translator_tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
            print(f"DEBUG: Translation result: {result}")
            return result
        except Exception as e:
            print(f"ERROR in translate: {e}")
            return f"[Translation Error] {text}"

    def synthesize(self, text: str, target_lang: str):
        print(f"DEBUG: Synthesizing '{text}' for {target_lang}")
        if not text:
            return None
        
        voice = self.tts_voices.get(target_lang)
        if not voice:
            print(f"No TTS voice found for {target_lang}")
            return None
            
        try:
            # Romanize Japanese if we are using the English placeholder model
            if target_lang == "ja":
                import pykakasi
                kks = pykakasi.kakasi()
                result = kks.convert(text)
                text = " ".join([item['hepburn'] for item in result])
                print(f"DEBUG: Converted to Romaji: {text}")

            # Debug available methods
            # print(f"DEBUG: PiperVoice methods: {dir(voice)}")

            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
            
            try:
                # Synthesize to a file path (most robust method)
                # Piper writes the WAV file directly to this path
                with io.BytesIO() as wav_buffer: 
                   # Legacy attempt removed. Using file path.
                   pass

                # We open the file ourselves? No, existing examples show passing a file-like object usually works. 
                # But to avoid 'channels not specified', let's try passing the file *object* created by wave.open?
                # Actually, let's try passing the raw temporary file PATH if supported, 
                # OR open a simple binary file and pass that.
                
                # Let's try the stream generator approach which is safest if available?
                # No, synthesize_stream_raw failed.
                
                # Fallback: Open a real file and pass it.
                with open(temp_wav_path, "wb") as wav_file:
                    import wave
                    with wave.open(wav_file, "wb") as wf:
                        # We need to rely on piper to write to it? 
                        # If piper uses wave.open internally, passing a binary file object is best.
                        # Wait, if piper uses wave.open, we shouldn't use wave.open.
                        pass
                
                # Let's simple pass a real file object opened in 'wb'
                with open(temp_wav_path, "wb") as f:
                    voice.synthesize(text, f)
                
                # Read back
                with open(temp_wav_path, "rb") as f:
                    wav_bytes = f.read()
                
                return wav_bytes

            finally:
                if os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
        except Exception as e:
            print(f"ERROR in synthesize: {e}")
            return None

# Singleton instance
# pipeline = AudioPipeline()
