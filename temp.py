import google.generativeai as genai
import os
import dotenv
dotenv.load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def list_available_models():
    models = genai.list_models()
    for model in models:
        print(model.name)

if __name__ == "__main__":
    list_available_models()
