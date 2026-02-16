import os
import requests
import tarfile

# Define where to store models
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "piper")
os.makedirs(MODEL_DIR, exist_ok=True)

# Piper voices to download
# voice_name -> url
VOICES = {
    "en_US-lessac-medium.onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
    "en_US-lessac-medium.onnx.json": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    # Japanese models are currently not available in the main repo.
    # USING PLACEHOLDER: We will use a different English voice (libritts-high) to simulate a "different" voice for now
    # so that the system produces audio.
    # Real Japanese support requires building a custom model or finding a community link.
    "ja_JP-zarvox-low.onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/libritts/high/en_US-libritts-high.onnx",
    "ja_JP-zarvox-low.onnx.json": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/libritts/high/en_US-libritts-high.onnx.json"
}

def download_file(url, filepath):
    if os.path.exists(filepath):
        print(f"File exists: {filepath}")
        return
    
    print(f"Downloading {url}...")
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded to {filepath}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    print("Downloading Piper models...")
    for filename, url in VOICES.items():
        filepath = os.path.join(MODEL_DIR, filename)
        download_file(url, filepath)
    print("Done.")

if __name__ == "__main__":
    main()
