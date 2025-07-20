from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import speech_recognition as sr
from gtts import gTTS

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Voice Robo Teacher Ready"}

@app.post("/listen/")
async def listen_to_child(audio: UploadFile = File(...)):
    with open("temp.wav", "wb") as f:
        f.write(await audio.read())

    recognizer = sr.Recognizer()
    with sr.AudioFile("temp.wav") as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
        except Exception as e:
            return {"error": str(e)}

    reply = f"You said: {text}"
    tts = gTTS(reply)
    tts.save("response.mp3")

    return {"text": text, "voice_url": "/response.mp3"}

@app.get("/response.mp3")
def get_audio():
    return FileResponse("response.mp3", media_type="audio/mpeg")
