import openai
import os

class GPT4OClient:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def process(self, prompt):
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
