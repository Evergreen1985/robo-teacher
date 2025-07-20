from fastapi import FastAPI, UploadFile, File
import speech_recognition as sr
from gtts import gTTS
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Robo Teacher is Ready with Voice!"}

@app.post("/listen/")
async def listen_to_child(audio: UploadFile = File(...)):
    recognizer = sr.Recognizer()
    with open("temp.wav", "wb") as f:
        f.write(await audio.read())

    with sr.AudioFile("temp.wav") as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
        except Exception as e:
            return {"error": str(e)}

    response_text = f"Hello! You said: {text}"

    tts = gTTS(response_text)
    tts.save("response.mp3")

    return {"text": text, "response_audio_url": "/response.mp3"}

@app.get("/response.mp3")
def serve_audio():
    return FileResponse("response.mp3", media_type="audio/mpeg")
