from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydub import AudioSegment
from transformers import AutoTokenizer, AutoModelForCausalLM
import speech_recognition as sr
from gtts import gTTS
import os
import uuid
import requests
import torch

# Set your HuggingFace API key (optional fallback later)
HF_API_KEY = os.getenv("HF_API_KEY", "")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Predefined rhymes
rhymes = {
    "twinkle": {
        "type": "youtube",
        "url": "https://www.youtube.com/embed/yCjJyiqpAuU?autoplay=1&mute=0"
    },
    "johnny": {
        "type": "youtube",
        "url": "https://www.youtube.com/embed/dZyxheCtYx8?autoplay=1&mute=0"
    }
}

# Load small GPT model
tokenizer = AutoTokenizer.from_pretrained("sshleifer/tiny-gpt2")
model = AutoModelForCausalLM.from_pretrained("sshleifer/tiny-gpt2")

# Local GPT fallback
def ask_gpt(prompt):
    try:
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids
        output_ids = model.generate(input_ids, max_new_tokens=50, pad_token_id=tokenizer.eos_token_id)
        response = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return response
    except Exception as e:
        print("❌ GPT fallback error:", e)
        return "Sorry, Doodle couldn't think of an answer right now."

# Homepage
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Mic upload route
@app.post("/mic-upload")
async def mic_upload(file: UploadFile = File(...)):
    temp_input_path = f"temp_{uuid.uuid4()}.wav"
    temp_output_path = f"static/response_{uuid.uuid4()}.mp3"

    # Save uploaded audio
    with open(temp_input_path, "wb") as f:
        f.write(await file.read())

    # Speech Recognition
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(temp_input_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            print("🎤 Transcript:", text)
    except Exception as e:
        print("❌ Speech recognition error:", e)
        text = None

    os.remove(temp_input_path)

    # If speech recognition failed
    if not text:
        fallback_msg = "Sorry, I didn't catch that."
        tts = gTTS(text=fallback_msg)
        tts.save(temp_output_path)
        return JSONResponse(content={
            "text": fallback_msg,
            "type": "mp3",
            "media_url": f"/static/{os.path.basename(temp_output_path)}"
        })

    text_lower = text.lower()

    # Match rhymes
    for key, entry in rhymes.items():
        if key in text_lower:
            print(f"✅ Rhyme matched: {key}")
            return JSONResponse(content={
                "text": f"Sure! Playing the rhyme: {key.title()}",
                "type": entry["type"],
                "media_url": entry["url"]
            })

    # Fallback to GPT
    gpt_response = ask_gpt(f"Answer like a children's teacher: {text}")
    tts = gTTS(text=gpt_response)
    tts.save(temp_output_path)

    return JSONResponse(content={
        "text": gpt_response,
        "type": "mp3",
        "media_url": f"/static/{os.path.basename(temp_output_path)}"
    })
