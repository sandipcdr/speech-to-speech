import os
import requests
import tarfile

# Define where to store models
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "piper")
os.makedirs(MODEL_DIR, exist_ok=True)

# Piper voices to download
# voice_name -> url
VOICES = {
    "en_US-lessac-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
    "en_US-lessac-medium.json": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    
    # Selecting a Japanese voice (there are fewer options in Piper main repo, checking for alternatives)
    # Using 'ja_JP-ami-medium' if available or fallback. For now, we will use a known one.
    # Note: If this URL is 404, we might need to find a specific release. 
    # Checking specific valid URL for Japanese model...
    "ja_JP-ami-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ja/ja_JP/ami/medium/ja_JP-ami-medium.onnx",
    "ja_JP-ami-medium.json": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ja/ja_JP/ami/medium/ja_JP-ami-medium.onnx.json"
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

if __name__ == "__main__":
    print("Downloading Piper models...")
    for filename, url in VOICES.items():
        filepath = os.path.join(MODEL_DIR, filename)
        download_file(url, filepath)
    print("Done.")
