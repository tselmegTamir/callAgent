import os
import requests
import subprocess
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()

# -------------------- Configuration --------------------
FASTAPI_SERVER = "http://127.0.0.1:8080"
public_url = "https://829cf12d2a1f.ngrok-free.app"  # <-- replace with actual ngrok URL
# -------------------------------------------------------


def generate_tts(text: str, token: str, filename: str) -> str:
    headers = {
        'Content-Type': 'text/plain',
        'Token': token,
    }
    response = requests.post(
        "https://api.chimege.com/v1.2/synthesize",
        data=text.encode('utf-8'),
        headers=headers
    )
    local_path = f"{filename}.wav"
    with open(local_path, "wb") as f:
        f.write(response.content)
    return local_path


def convert_to_twilio_format(input_path: str, output_path: str):
    subprocess.run([
        "ffmpeg", "-y",  # overwrite if exists
        "-i", input_path,
        "-ar", "8000",  # 8000 Hz sample rate
        "-ac", "1",     # Mono
        "-c:a", "pcm_s16le",
        output_path
    ])


def upload_file(local_path: str, upload_endpoint: str):
    with open(local_path, "rb") as f:
        response = requests.post(
            f"{public_url}/upload/{upload_endpoint}",
            files={"file": (os.path.basename(local_path), f)}
        )
    return response.status_code == 200


def generate_twiml(audio_url: str, xml_filename: str) -> str:
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
</Response>"""
    
    with open(xml_filename, "w", encoding="utf-8") as f:
        f.write(xml_content)
    return xml_filename


def make_call(to_phone, from_phone, twiml_url, sid, auth_token):
    client = Client(sid, auth_token)
    print(twiml_url)
    call = client.calls.create(
        to=to_phone,
        from_=from_phone,
        url=twiml_url,
        method="GET"
    )
    return call.sid


def notify_customer(
    name: str,
    phone: str,
    deadline: str,
    chimege_token: str,
    twilio_sid: str,
    twilio_auth_token: str,
    twilio_phone: str
):
    # Format message
    year, month, day = deadline.split("-")
    message = f"Сайн байна уу? {name}." \
              f"Таны зээлийн төлөлтийн хугацаа болсон байна. Баярлалаа."

    # Filenames
    raw_audio = "tts_raw.wav"
    final_audio = "tts_final.wav"
    xml_filename = "twiml_test.xml"

    # 1. Generate raw TTS
    generate_tts(message, chimege_token, "tts_raw")

    # 2. Convert to Twilio-compatible format
    convert_to_twilio_format(raw_audio, final_audio)

    # 3. Upload audio
    upload_file(final_audio, "audio")

    # 4. Generate TwiML XML
    audio_url = f"{public_url}/audio/{final_audio}"
    xml_path = generate_twiml(audio_url, xml_filename)

    # 5. Upload TwiML XML
    upload_file(xml_path, "twiml")
    twiml_url = f"{public_url}/twiml/{xml_filename}"

    # 6. Make the call
    sid = make_call(phone, twilio_phone, twiml_url, twilio_sid, twilio_auth_token)
    print(f"[📞] Called {phone}, SID: {sid}")


# ✅ Call this to test
notify_customer(
    name="Түшиг",
    phone="+97694955524",
    deadline="2025-07-15",
    chimege_token=os.getenv("CHIMEGE_TOKEN_TTS"),
    twilio_sid=os.getenv("TWILIO_ACCOUNT_SID"),
    twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
    twilio_phone=os.getenv("TWILIO_PHONE_NUMBER")
)