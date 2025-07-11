def calculate_cost(model, tokens_in, tokens_out):
    pricing = {
        "gpt-3.5-turbo": {"input": 0.0025, "output": 0.01},
        "mistral-small": {"input": 0.003, "output": 0.015},
        "gemini-pro": {"input": 0.00125, "output": 0.005},
    }
    p = pricing.get(model)
    return (tokens_in * p["input"] + tokens_out * p["output"]) / 1000
