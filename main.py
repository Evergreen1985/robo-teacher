from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import speech_recognition as sr
from gtts import gTTS
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.post("/listen/")
async def listen(audio: UploadFile = File(...)):
    recognizer = sr.Recognizer()
    audio_path = "temp.wav"
    output_path = "static/output.mp3"

    with open(audio_path, "wb") as buffer:
        buffer.write(await audio.read())

    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
        except Exception as e:
            return {"error": "Speech recognition failed", "details": str(e)}

    # Simple response logic (can be extended with AI)
    response_text = f"You said: {text}"

    # Convert to speech and save
    tts = gTTS(response_text)
    tts.save(output_path)

    # Return URL to access audio reply
    return JSONResponse(content={
        "text": response_text,
        "voice_url": "/static/output.mp3"
    })
