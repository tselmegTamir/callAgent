import requests
import os
from dotenv import load_dotenv

load_dotenv()
CHIMEGE_TOKEN_TTS = os.getenv("CHIMEGE_TOKEN_TTS")

def generate_tts(text: str) -> str:    
    
    headers = {
        "Content-Type": "text/plain",
        "Token": CHIMEGE_TOKEN_TTS,
        "voice-id": "FEMALE3v2",  # Optional
        "speed": "1",
        "pitch": "1",
        "sample-rate": "22050"
    }

    response = requests.post(
        "https://api.chimege.com/v1.2/synthesize",
        headers=headers,
        data=text.encode("utf-8")
    )

    
    if response.status_code == 200:
        with open("static/tts_audio/hold-music.mp3", "wb") as f:
            f.write(response.content)
        print("✅ MP3 saved to static/hold-music.mp3")
    else:
        print("❌ Failed to generate TTS:", response.status_code, response.text)


TEXT = "Танд өөр асуух зүйл байна уу?"
generate_tts(TEXT)