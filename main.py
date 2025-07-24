from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import speech_recognition as sr
from gtts import gTTS
import os
import uuid
import requests
from pydub import AudioSegment

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

# HuggingFace GPT fallback function
def ask_gpt(prompt):
    try:
        prompt = f"Answer like a friendly children's teacher: {prompt}"

        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={"inputs": prompt}
        )

        print("🧠 GPT STATUS:", response.status_code)
        print("🧠 GPT RESPONSE:", response.text)

        if response.status_code != 200:
            return f"Doodle couldn’t answer (HTTP {response.status_code})"

        result = response.json()

        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        else:
            return "Doodle is still thinking..."

    except Exception as e:
        print("❌ HuggingFace error:", e)
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
