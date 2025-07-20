from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import speech_recognition as sr
from gtts import gTTS
import os
import uuid

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/mic-upload")
async def mic_upload(file: UploadFile = File(...)):
    temp_input_path = f"temp_{uuid.uuid4()}.wav"
    temp_output_path = f"static/response_{uuid.uuid4()}.mp3"

    with open(temp_input_path, "wb") as f:
        f.write(await file.read())

    # Speech Recognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(temp_input_path) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
        except Exception as e:
            text = "Sorry, I didn't catch that."

    # Convert response to voice
    tts = gTTS(text=text)
    tts.save(temp_output_path)

    os.remove(temp_input_path)

    return JSONResponse(content={
        "text": text,
        "audio_url": f"/static/{os.path.basename(temp_output_path)}"
    })
