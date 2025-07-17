# from fastapi import FastAPI, Request, Form
# from fastapi.responses import PlainTextResponse
# import requests
# import openai
# from pydub import AudioSegment
# import os
# from xml.etree.ElementTree import Element, tostring

# app = FastAPI()

# # === Configuration ===
# CHIMEGE_TOKEN = "YOUR_CHIMEGE_API_TOKEN"
# OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
# TWILIO_BASE_URL = "https://api.twilio.com"  # If needed

# openai.api_key = OPENAI_API_KEY

# # === Helper: Generate TwiML ===
# def build_twiml_response(say_text=None, record_action_url=None, play_url=None):
#     response = Element("Response")
#     if say_text:
#         say = Element("Say")
#         say.text = say_text
#         response.append(say)
#     if record_action_url:
#         record = Element("Record", maxLength="10", action=record_action_url, method="POST", playBeep="false")
#         response.append(record)
#     if play_url:
#         play = Element("Play")
#         play.text = play_url
#         response.append(play)
#     return PlainTextResponse(tostring(response, encoding='unicode'))

# # === Route 1: Initial call entry ===
# @app.post("/voice")
# async def voice():
#     return build_twiml_response(
#         say_text="Сайн байна уу. Асуултаа хэлнэ үү.",
#         record_action_url="/process"
#     )

# # === Route 2: After recording ===
# @app.post("/process")
# async def process(request: Request):
#     form = await request.form()
#     recording_url = form.get("RecordingUrl")

#     # Download the audio
#     audio_url = f"{recording_url}.wav"
#     audio_response = requests.get(audio_url)
#     audio_path = "input.wav"
#     with open(audio_path, "wb") as f:
#         f.write(audio_response.content)

#     # === Send to Chimege STT ===
#     with open(audio_path, 'rb') as f:
#         audio_data = f.read()
#     stt_res = requests.post(
#         "https://api.chimege.com/v1.2/transcribe",
#         data=audio_data,
#         headers={
#             "Content-Type": "application/octet-stream",
#             "Punctuate": "true",
#             "Token": CHIMEGE_TOKEN,
#         }
#     )
#     transcript = stt_res.text.strip()

#     # === Send to GPT-4 ===
#     gpt_response = openai.ChatCompletion.create(
#         model="gpt-4",
#         messages=[
#             {"role": "system", "content": "Чи бол тусламж үзүүлэх автомат ярианы туслах. Эелдэг бөгөөд товчхон хариул."},
#             {"role": "user", "content": transcript},
#         ]
#     )
#     gpt_reply = gpt_response["choices"][0]["message"]["content"]

#     # === Send GPT reply to Chimege TTS ===
#     tts_res = requests.post(
#         "https://api.chimege.com/v1.2/synthesize",
#         data=gpt_reply.encode("utf-8"),
#         headers={
#             "Content-Type": "plain/text",
#             "Token": CHIMEGE_TOKEN,
#             "voice-id": "FEMALE3v2",
#             "speed": "1",
#             "pitch": "1",
#         }
#     )
#     output_audio_path = "output.wav"
#     with open(output_audio_path, "wb") as f:
#         f.write(tts_res.content)

#     # Convert WAV to MP3 or serve WAV statically
#     audio_url = "https://your-server.com/static/output.wav"  # Adjust for deployment
#     return build_twiml_response(play_url=audio_url)

# # Optional: serve static files if needed
# from fastapi.staticfiles import StaticFiles
# app.mount("/static", StaticFiles(directory="."), name="static")


# import sounddevice as sd
# from scipy.io.wavfile import write

# # Settings
# fs = 44100  # Sample rate (Hz)
# seconds = 5  # Duration of recording

# print("Recording...")
# recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
# sd.wait()  # Wait until recording is finished
# print("Done!")

# write("my_recording.wav", fs, recording)
# print("Saved as my_recording.wav")


# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

call = client.calls.create(
    url="https://66ba5ce0a2e7.ngrok-free.app/audio/tts_final.wav",
    to="+97694970947",
    from_=os.getenv("TWILIO_PHONE_NUMBER"),
)

print(call.sid)
