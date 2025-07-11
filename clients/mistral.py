from openai import OpenAI
import os

class MistralClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("MISTRAL_API_KEY"),
            base_url=os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")
        )

    def process(self, prompt):
        response = self.client.chat.completions.create(
            model="mistral-small",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
