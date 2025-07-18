import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_gpt_reply(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a friendly robot teacher for small kids."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )
    return response.choices[0].message.content.strip()
