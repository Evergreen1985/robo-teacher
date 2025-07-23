from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import speech_recognition as sr
from gtts import gTTS
import os
import uuid
from pydub import AudioSegment

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/mic-upload")
async def mic_upload(file: UploadFile = File(...)):
    input_ext = file.filename.split(".")[-1]
    raw_input_path = f"temp_input_{uuid.uuid4()}.{input_ext}"
    converted_wav_path = f"temp_converted_{uuid.uuid4()}.wav"
    output_audio_path = f"static/response_{uuid.uuid4()}.mp3"

    with open(raw_input_path, "wb") as f:
        f.write(await file.read())

    try:
        audio = AudioSegment.from_file(raw_input_path)
        audio.export(converted_wav_path, format="wav")
    except Exception as e:
        return JSONResponse(content={"error": "Conversion failed", "details": str(e)}, status_code=500)

    recognizer = sr.Recognizer()
    with sr.AudioFile(converted_wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
        except Exception:
            text = "Sorry, I didn't catch that."

    os.remove(raw_input_path)
    os.remove(converted_wav_path)

    text_lower = text.lower()

    # 🌟 Predefined rhymes (MP3/YouTube)
    rhymes = {
        "twinkle": {"type": "mp3", "url": "https://www.youtube.com/embed/yCjJyiqpAuU"},
        "abc": {"type": "mp3", "url": "https://www2.cs.uic.edu/~i101/SoundFiles/AlphabetSong.mp3"},
        "baa baa": {"type": "mp3", "url": "https://youtu.be/yCjJyiqpAuU?si=_G9dLIQ42hZxsr6r"},
        "johnny": {"type": "youtube", "url": "https://www.youtube.com/embed/dZyxheCtYx8"}
    }

    for key, entry in rhymes.items():
        if key in text_lower:
            return JSONResponse(content={
                "text": f"Sure! Playing the rhyme: {key.title()}",
                "type": entry["type"],
                "media_url": entry["url"]
            })

    # 🗣️ Fallback: convert what child said to TTS
    tts = gTTS(text=text)
    tts.save(output_audio_path)

    return JSONResponse(content={
        "text": text,
        "type": "mp3",
        "media_url": f"/static/{os.path.basename(output_audio_path)}"
    })
