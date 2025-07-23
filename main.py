def ask_gpt(prompt):
    try:
        # Add instruction-style format
        prompt = f"Answer the following like a helpful children's teacher:\n\n{prompt}"

        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-small",
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={"inputs": prompt}
        )

        # Check if valid JSON
        if response.status_code != 200:
            return f"Doodle couldn’t answer (HTTP {response.status_code})"

        result = response.json()

        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]
        else:
            return "Doodle is still thinking..."
    except Exception as e:
        print("HuggingFace error:", e)
        return "Sorry, Doodle couldn't think of an answer right now."
