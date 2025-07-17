from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from twilio.rest import Client
import asyncio, logging, os

from utils import (
    download_audio,
    transcribe_audio,
    generate_response,
    synthesize_audio,
    sanitize_text_for_tts
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()
app.mount("/tts_audio", StaticFiles(directory="static/tts_audio"), name="tts_audio")

TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_CLIENT = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
PUBLIC_URL = "https://805ae74452fa.ngrok-free.app"  

@app.post("/voice")
async def initial_voice():
    # Initial greeting + first record
    twiml = f"""
<Response>
  <Play>{PUBLIC_URL}/tts_audio/output.wav</Play>
  <Record action="/process-recording" method="POST" maxLength="30" playBeep="true"/>
</Response>
"""
    return Response(twiml, media_type="application/xml")

@app.post("/voice-loop")
async def loop_voice():
    # Fresh TwiML for every subsequent turn
    twiml = f"""
<Response>
  <Play>{PUBLIC_URL}/tts_audio/hold-music.mp3</Play>
  <Record action="/process-recording" method="POST" maxLength="30" playBeep="true"/>
</Response>
"""
    return Response(twiml, media_type="application/xml")

@app.post("/process-recording")
async def process_recording(request: Request):
    form = await request.form()
    call_sid    = form["CallSid"]
    recording_url = form["RecordingUrl"]

    # Kick off the async work
    asyncio.create_task(handle_turn(call_sid, recording_url))

    # Immediately return a short hold so the call stays alive
    hold = f"""
<Response>
  <Play loop="0">{PUBLIC_URL}/tts_audio/hold-music.mp3</Play>
</Response>
"""
    return Response(hold, media_type="application/xml")


@app.post("/call-user")
async def call_user():
    call = TWILIO_CLIENT.calls.create(
        url=f"{PUBLIC_URL}/voice",
        to="+97694970947",
        from_=TWILIO_NUMBER
    )
    return {"message": "Call initiated", "call_sid": call.sid}

async def handle_turn(call_sid: str, recording_url: str):
    try:
        # 1. Download & transcribe
        path = await download_audio(recording_url)
        logging.info(f"✅ Audio saved: {path}")

        text = await transcribe_audio(path)
        logging.info(f"🗣️ User said (STT): {text}")

        # 2. GPT → TTS
        reply = await generate_response(text)
        logging.info(f"🤖 GPT response: {reply}")

        clean = sanitize_text_for_tts(reply)
        logging.info(f"🧹 Sanitized TTS text: {clean}")

        filename = await synthesize_audio(clean)

        # 3. Redirect the live call to /voice-loop (fresh TwiML)
        tts_url = f"{PUBLIC_URL}/tts_audio/{filename}"
        logging.info(f"📢 TTS ready at: {tts_url}")

        TWILIO_CLIENT.calls(call_sid).update(twiml=f"""
<Response>
  <Play>{tts_url}</Play>
  <Redirect>{PUBLIC_URL}/voice-loop</Redirect>
</Response>
""")
    except Exception as e:
        logging.error("Turn failed", exc_info=e)
        try:
            TWILIO_CLIENT.calls(call_sid).update(twiml="""
<Response>
  <Say>Уучлаарай, алдаа гарлаа.</Say>
  <Hangup/>
</Response>
""")
        except: pass
