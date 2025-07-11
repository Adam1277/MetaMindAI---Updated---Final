from .gpt4o import GPT4OClient
from .gemini import GeminiClient
from .mistral import MistralClient

def get_model_client(name):
    clients = {
        "gpt-3.5-turbo": GPT4OClient(),
        "mistral-small": MistralClient(),
        "gemini-pro": GeminiClient(),
    }
    return clients.get(name)

