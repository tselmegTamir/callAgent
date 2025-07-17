# from fastapi import FastAPI
# from pydantic import BaseModel
# import openai
# import os
# from dotenv import load_dotenv

# load_dotenv()  # Load .env variables

# app = FastAPI()

# class ChatRequest(BaseModel):
#     user_message: str

# product_info = """
#     MyCompany makes eco-friendly water bottles:
#     - Keeps water cold for 24 hours
#     - Available in blue, green, black
#     - Shipping: 3-5 business days worldwide
#     - Customer support: 9am-6pm UTC
#     """

# @app.post("/chat")
# async def chat_with_assistant(request: ChatRequest):
#     client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#     response = client.chat.completions.create(
#         model="gpt-4",
#         messages = [
#             {"role": "system", "content": f"You are a helpful assistant for MyCompany.\n{product_info}"},
#             {"role": "user", "content": request.user_message}
#         ]
#     )
#     return {"response": response.choices[0].message.content}



#main.py
from fastapi import FastAPI, File, UploadFile
import requests
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

app = FastAPI()
CHIMEGE_TOKEN_STT = os.getenv("CHIMEGE_TOKEN_STT")
CHIMEGE_TOKEN_TTS = os.getenv("CHIMEGE_TOKEN_TTS")

@app.post("/stt")
async def transcribe_audio(file: UploadFile = File(...)):
    audio = await file.read()

    headers = {
        "Content-Type": "application/octet-stream",
        "Token": CHIMEGE_TOKEN_STT,
        "Punctuate": "true"
    }
    
    response = requests.post(
        "https://api.chimege.com/v1.2/transcribe",
        headers=headers,
        data=audio
    )

    transcript = response.content.decode("utf-8")
    return {"transcript": transcript}

# main.py (continued)

@app.post("/tts")
async def synthesize_text(text: str):
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

    print(response.headers.get("Content-Type"))  # Should be audio/x-wav
    print(response.content[:100])  # First 100 bytes (should begin with 'RIFF')


    with open("output.wav", "wb") as f:
        f.write(response.content)

    return {"message": "Audio saved as output.wav"}
