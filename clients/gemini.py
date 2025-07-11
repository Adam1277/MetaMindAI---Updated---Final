import google.generativeai as genai
import os

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    def process(self, prompt):
        response = self.model.generate_content(prompt)
        return response.text
