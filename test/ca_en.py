from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
import openai
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

app = FastAPI()

@app.post("/voice")
async def voice():
    response = VoiceResponse()
    gather = Gather(input="speech", action="/process", method="POST", timeout=3, speech_timeout="auto")
    gather.say("Hello! How can I help you today?")
    response.append(gather)
    response.say("Sorry, I didn't get any response. Goodbye.")
    return PlainTextResponse(str(response), media_type="application/xml")

@app.post("/process")
async def process(request: Request):
    form = await request.form()
    user_input = form.get("SpeechResult", "")

    print(f"User said: {user_input}")

    # Generate response from GPT-4
    reply = chat_with_gpt(user_input)

    # Build next TwiML response
    response = VoiceResponse()
    response.say(reply)
    response.redirect("/voice")  # Go back to gathering
    return PlainTextResponse(str(response), media_type="application/xml")

def chat_with_gpt(prompt: str) -> str:
       
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4",
        messages = [
            {"role": "system", "content": f"You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

