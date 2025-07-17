import os
import aiohttp
import requests
import openai
import uuid
import logging
import asyncio
import time
import re
from dotenv import load_dotenv
from aiohttp import BasicAuth

load_dotenv()

CHIMEGE_TOKEN_STT = os.getenv("CHIMEGE_TOKEN_STT")
CHIMEGE_TOKEN_TTS = os.getenv("CHIMEGE_TOKEN_TTS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 1. Download Twilio recording
from aiohttp import BasicAuth

RETRY_COUNT = 5
RETRY_WAIT_SECONDS = 2
MIN_VALID_FILE_SIZE = 6000  # 6KB
POLL_INTERVAL = 1    # seconds between polls
POLL_TIMEOUT  = 60   # max seconds to wait

async def download_audio(recording_url: str) -> str:
    # Prepare Twilio URL for the .wav version
    audio_url = f"{recording_url}.wav"
    logging.info(f"🎯 Full audio URL: {audio_url}")

    # Set up local path
    os.makedirs("recordings", exist_ok=True)
    local_filename = f"recordings/{uuid.uuid4().hex}.wav"

    # Get Twilio credentials from env
    auth = BasicAuth(
        login=os.getenv("TWILIO_ACCOUNT_SID"),
        password=os.getenv("TWILIO_AUTH_TOKEN")
    )

    # Retry download logic
    for attempt in range(RETRY_COUNT):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(audio_url, auth=auth) as response:
                    logging.info(f"➡️ Attempt {attempt+1}: Status = {response.status}")
                    logging.info(f"➡️ Content-Type: {response.headers.get('Content-Type')}")

                    content = await response.read()
                    logging.info(f"📦 Downloaded {len(content)} bytes")

                    if response.status == 200 and len(content) >= MIN_VALID_FILE_SIZE:
                        with open(local_filename, "wb") as f:
                            f.write(content)
                        logging.info(f"✅ Audio saved at {local_filename}")
                        return local_filename
                    else:
                        logging.warning("⚠️ Audio too small or invalid. Retrying...")

            except Exception as e:
                logging.error(f"❌ Error during download: {e}")

        # Wait before next retry
        logging.info(f"🔁 Waiting {RETRY_WAIT_SECONDS}s before retrying...")
        await asyncio.sleep(RETRY_WAIT_SECONDS)

    raise Exception("❌ Failed to download a valid audio file after multiple attempts.")

# 2. Transcribe with Chimege STT
async def transcribe_audio(audio_path: str) -> str:
    # Step 1: Upload audio to /stt-long
    with open(audio_path, 'rb') as f:
        audio_bytes = f.read()

    logging.info("🎧 Uploading audio to Chimege /stt-long...")
    upload_resp = requests.post(
        "https://api.chimege.com/v1.2/stt-long",
        data=audio_bytes,
        headers={
            "Content-Type": "application/octet-stream",
            "Token": CHIMEGE_TOKEN_STT,
        }
    )
    if upload_resp.status_code != 200:
        raise Exception(f"❌ STT-long upload failed: {upload_resp.status_code} - {upload_resp.text}")

    uuid_ = upload_resp.json().get("uuid")
    if not uuid_:
        raise Exception(f"❌ No UUID returned from STT-long: {upload_resp.text}")
    logging.info(f"🆔 Got UUID from Chimege: {uuid_}")

    # Step 2: Poll until transcription is done (or timeout)
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > POLL_TIMEOUT:
            raise TimeoutError(f"❌ STT-long timeout after {POLL_TIMEOUT}s")

        logging.info(f"🔁 Polling Chimege for transcription (elapsed {int(elapsed)}s)...")
        poll_resp = requests.get(
            "https://api.chimege.com/v1.2/stt-long-transcript",
            headers={
                "Token": CHIMEGE_TOKEN_STT,
                "UUID": uuid_
            }
        )
        if poll_resp.status_code != 200:
            raise Exception(f"❌ STT-long polling failed: {poll_resp.status_code} - {poll_resp.text}")

        data = poll_resp.json()
        logging.debug(f"📥 Full transcription response: {data}")

        # Handle dict format { done: bool, transcription: str, ... }
        if isinstance(data, dict):
            if data.get("done"):
                transcript = data.get("transcription", "").strip()
                logging.info(f"✅ Final transcript: {transcript}")
                return transcript
            # else done==False → wait and retry

        # Handle list format [ { done: bool, transcription: str, ... }, ... ]
        elif isinstance(data, list) and data:
            first = data[0]
            if first.get("done"):
                transcript = first.get("transcription", "").strip()
                logging.info(f"✅ Final transcript: {transcript}")
                return transcript
            # else done==False → wait and retry

        # Not ready yet
        logging.info("⌛ Transcript not ready yet, retrying...")
        time.sleep(POLL_INTERVAL)

# 3. Generate GPT Response
async def generate_response(user_message):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    product_info = """
        Role (Үүрэг):
        Та бол Монгол хэл дээр ярьдаг, эелдэг, эмчийн хуваарийн талаарх мэдээллийг өгч чадвартай виртуал дуу хоолойн туслах юм.

        Task (Даалгавар):
        Хэрэглэгчийн асуултад хариулах, үйлчилгээ танилцуулах, цагийн мэдээлэл өгөх.

        Specific Context (Тодорхой нөхцөл байдал):
        Батаа эмч даваа, лхагва, баасан гаригуудад эмчлэнэ.
        Доржоо эмч мягмар, пүрэв гаригуудад эмчлэнэ.
        Балдан эмч бямба, ням гаригуудад эмчлэх хуваарьтай.

        Хариулт маш тодорхой, богинохон байх ёстой. 15 үгэнд багтсан хариулт өг.
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages = [
            {"role": "system", "content": f"{product_info}"},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content

# 4. Synthesize with Chimege TTS
async def synthesize_audio(text):
    headers = {
        "Content-Type": "text/plain",
        "Token": CHIMEGE_TOKEN_TTS,
        "voice-id": "FEMALE3v2",
        "speed": "1",
        "pitch": "1",
        "sample-rate": "22050"
    }
    response = requests.post(
        "https://api.chimege.com/v1.2/synthesize",
        headers=headers,
        data=text.encode("utf-8")
    )

    audio_id = f"{uuid.uuid4()}.wav"
    audio_path = f"static/tts_audio/{audio_id}"
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    with open(audio_path, "wb") as f:
        f.write(response.content)

    return audio_id

def sanitize_text_for_tts(text: str) -> str:
    # Allow only Cyrillic letters, numbers, punctuation that Chimege allows
    allowed_chars = re.compile(r"[а-яА-ЯёЁ0-9\s.,!?\"':\-]+")
    matches = allowed_chars.findall(text)
    return " ".join(matches).strip()
