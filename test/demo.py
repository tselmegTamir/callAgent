import requests
import os
from pyngrok import ngrok
from twilio.rest import Client
from dotenv import load_dotenv  
load_dotenv()

FASTAPI_SERVER = "http://127.0.0.1:8080"

# Start ngrok
public_url = "https://6a6ee28a11e6.ngrok-free.app"
print(f"[✔] Ngrok Public URL: {public_url}")

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
    call = client.calls.create(
        to=to_phone,
        from_=from_phone,
        url=twiml_url
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

    # Message
    year, month, day = deadline.split("-")
    message = f"Сайн байна уу? {name}." \
              f"Таны зээлийн төлөлтийн хугацаа болсон байна. Баярлалаа."

    # Filenames
    audio_filename = f"tts_test.wav"
    xml_filename = f"twiml_test.xml"

    # 1. Generate TTS file
    wav_path = generate_tts(message, chimege_token, audio_filename.replace(".wav", ""))

    # 2. Upload to FastAPI server
    upload_file(wav_path, "audio")

    # 3. Generate TwiML XML
    audio_url = f"{public_url}/audio/{audio_filename}"
    xml_path = generate_twiml(audio_url, xml_filename)

    # 4. Upload TwiML
    upload_file(xml_path, "twiml")
    twiml_url = f"{public_url}/twiml/{xml_filename}"

    # 5. Call
    sid = make_call(phone, twilio_phone, twiml_url, twilio_sid, twilio_auth_token)
    print(f"[📞] Called {phone}, SID: {sid}")


notify_customer(
    name="Цэлмэг",
    phone="+97694970947",
    deadline="2025-07-15",
    chimege_token=os.getenv("CHIMEGE_TOKEN_TTS"),
    twilio_sid=os.getenv("TWILIO_ACCOUNT_SID"),
    twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
    twilio_phone=os.getenv("TWILIO_PHONE_NUMBER")
)
