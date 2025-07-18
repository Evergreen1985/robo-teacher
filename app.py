from fastapi import FastAPI
from gpt_helper import get_gpt_reply

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Robo Teacher is online!"}

@app.get("/ask")
def ask_robo(q: str):
    answer = get_gpt_reply(q)
    return {"question": q, "answer": answer}
