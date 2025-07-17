# server.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import os
import shutil

app = FastAPI()

AUDIO_DIR = "static/audio"
TWIML_DIR = "static/twiml"
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TWIML_DIR, exist_ok=True)

# GET endpoints to serve files
@app.get("/audio/{filename}")
async def get_audio(filename: str):
    return FileResponse(f"{AUDIO_DIR}/{filename}", media_type="audio/wav")

@app.get("/twiml/{filename}")
async def get_twiml(filename: str):
    print(f"[GET] TwiML requested: {filename}")
    return FileResponse(f"{TWIML_DIR}/{filename}", media_type="application/xml")


# POST endpoints to upload files
@app.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    file_path = os.path.join(AUDIO_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "Audio uploaded", "path": file_path}

@app.post("/upload/twiml")
async def upload_twiml(file: UploadFile = File(...)):
    file_path = os.path.join(TWIML_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "TwiML uploaded", "path": file_path}
