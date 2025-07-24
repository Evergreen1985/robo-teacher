from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydub import AudioSegment
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from gtts
import speech_recognition as sr
import gTTS
import os
import uuid
import requests
import torch

# Set your HuggingFace API key (store securely in Render env variables)
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

# Load model and tokenizer once (at startup)
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")

# HuggingFace GPT fallback function
def ask_gpt(prompt):
    try:
        full_prompt = f"Answer like a friendly children's teacher: {prompt}"
        print("🧠 Local Prompt:", full_prompt)

        # Tokenize input
        inputs = tokenizer(full_prompt, return_tensors="pt")

        # Generate output
        outputs = model.generate(
            inputs["input_ids"],
            max_length=100,
            num_return_sequences=1,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.8
        )

        # Decode output
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return decoded

    except Exception as e:
        print("❌ Local model error:", e)
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
    except Exception as e:
        text = "Sorry, I didn't catch that."

    os.remove(temp_input_path)
    text_lower = text.lower()

    # Match rhymes
    for key, entry in rhymes.items():
        if key in text_lower:
            return JSONResponse(content={
                "text": f"Sure! Playing the rhyme: {key.title()}",
                "type": entry["type"],
                "media_url": entry["url"]
            })

    # Fallback to HuggingFace GPT
    gpt_response = ask_gpt(text)
    tts = gTTS(text=gpt_response)
    tts.save(temp_output_path)

    return JSONResponse(content={
        "text": gpt_response,
        "type": "mp3",
        "media_url": f"/static/{os.path.basename(temp_output_path)}"
    })
