from fastapi import FastAPI, Request, Header
from fastapi.responses import Response
from pydub import AudioSegment
import requests
import io
import os
import uuid

app = FastAPI()

# === Config ===
VAPI_SECRET = "your-vapi-secret"
CHIMEGE_TOKEN = os.getenv("CHIMEGE_TOKEN_TTS")
CHIMEGE_URL = "https://api.chimege.com/v1.2/synthesize"

# === Main Endpoint ===
@app.post("/api/synthesize")
async def synthesize(request: Request, x_vapi_secret: str = Header(...)):
    if x_vapi_secret != VAPI_SECRET:
        return Response(status_code=401, content="Unauthorized")

    body = await request.json()
    message = body.get("message", {})
    text = message.get("text", "")
    sample_rate = message.get("sampleRate", 24000)

    if not text:
        return Response(status_code=400, content="Missing text")

    try:
        pcm_data = await generate_pcm_from_chimege(text, sample_rate)
        return Response(content=pcm_data, media_type="application/octet-stream")
    except Exception as e:
        print("TTS Error:", e)
        return Response(status_code=500, content="TTS processing failed")

# === Generate PCM from Chimege WAV ===
async def generate_pcm_from_chimege(text: str, sample_rate: int) -> bytes:
    headers = {
        "Content-Type": "text/plain",
        "Token": CHIMEGE_TOKEN,
    }

    response = requests.post(CHIMEGE_URL, data=text.encode("utf-8"), headers=headers)

    if response.status_code != 200:
        raise Exception(f"Chimege TTS error: {response.status_code} - {response.text}")

    # Read WAV audio from Chimege response
    wav_audio = AudioSegment.from_file(io.BytesIO(response.content), format="wav")

    # Convert to required format
    pcm_audio = wav_audio.set_frame_rate(sample_rate).set_channels(1).set_sample_width(2)

    pcm_buffer = io.BytesIO()
    pcm_audio.export(pcm_buffer, format="raw")  # raw = PCM s16le
    return pcm_buffer.getvalue()

