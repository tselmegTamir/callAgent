from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from twilio.rest import Client
import logging
import os
import asyncio

from utils import (
    download_audio,
    transcribe_audio,
    generate_response,
    synthesize_audio
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()
app.mount("/tts_audio", StaticFiles(directory="static/tts_audio"), name="tts_audio")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
PUBLIC_SERVER_URL = "https://5b0d6554b0fe.ngrok-free.app"  # Update as needed

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


@app.post("/voice")
async def voice_entry():
    # Entry point of the call - ask user a question and record their response
    return Response(content=f"""
<Response>
    <Say>Сайн байна уу? Юугаар туслах вэ?</Say>
    <Record timeout="3" maxLength="30" action="/process-recording" method="POST" playBeep="true" />
</Response>
""", media_type="application/xml")


@app.post("/process-recording")
async def process_recording(request: Request):
    form = await request.form()
    recording_url = form.get("RecordingUrl")
    call_sid = form.get("CallSid")

    logging.info(f"🎯 Full audio URL: {recording_url}")

    # Respond quickly to keep Twilio call alive
    twiml = """
<Response>
    <Say>Боловсруулж байна, түр хүлээнэ үү.</Say>
    <Pause length="10"/>
    <Redirect>/voice</Redirect>
</Response>
"""
    # Start AI work in background
    asyncio.create_task(process_async(call_sid, recording_url))

    return Response(content=twiml, media_type="application/xml")


async def process_async(call_sid: str, recording_url: str):
    try:
        local_audio_path = await download_audio(recording_url)
        logging.info(f"✅ Audio saved: {local_audio_path}")

        transcript = await transcribe_audio(local_audio_path)
        logging.info(f"🗣️ User said (STT): {transcript}")

        response_text = await generate_response(transcript)
        logging.info(f"🤖 GPT response: {response_text}")

        audio_filename = await synthesize_audio(response_text)
        audio_url = f"{PUBLIC_SERVER_URL}/tts_audio/{audio_filename}"
        logging.info(f"📢 TTS ready at: {audio_url}")

        # Tell Twilio to play the audio
        twilio_client.calls(call_sid).update(twiml=f"""
<Response>
    <Play>{audio_url}</Play>
    <Redirect>/voice</Redirect>
</Response>
""")

    except Exception as e:
        logging.error(f"❌ Error in async processing: {e}")
        twilio_client.calls(call_sid).update(twiml="""
<Response>
    <Say>Уучлаарай, алдаа гарлаа.</Say>
</Response>
""")


@app.post("/call-user")
async def call_user():
    call = twilio_client.calls.create(
        url=f"{PUBLIC_SERVER_URL}/voice",
        to="+97694970947",
        from_=TWILIO_NUMBER
    )
    return {"message": "Call initiated", "call_sid": call.sid}
