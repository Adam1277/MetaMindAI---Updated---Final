from analyzers import detect_input_type, estimate_token_count, classify_task
from clients import get_model_client
from utils import calculate_cost
import json
import os
from store_data import qa_production_data

def should_inject_data(prompt: str) -> bool:
    keywords = ["failure rate", "swabbing", "microbial", "atp", "production", "produce thrown", "produce made"]
    return any(word in prompt.lower() for word in keywords)

def load_model_map():
    model_map_path = os.path.join(os.path.dirname(__file__), "task_model_map.json")
    with open(model_map_path, "r") as f:
        return json.load(f)

def route_request(input_data):
    TASK_MODEL_MAP = load_model_map()
    input_type = detect_input_type(input_data)
    token_count = estimate_token_count(input_data)
    tasks = classify_task(input_data)

    # Determine routing mode
    mode = "single"
    if len(tasks) > 1:
        lowered_text = input_data.lower() if isinstance(input_data, str) else ""
        if any(word in lowered_text for word in ["then", "after that", "next", "followed by"]):
            mode = "sequential"
        else:
            mode = "parallel"

    responses = []
    output = input_data
    prev_model = None
    
    if should_inject_data(input_data):
        print('here')
        input_data += f"\n\n[QA AND PRODUCTION DATA]\n{json.dumps(qa_production_data)}"


    if mode == "single":
        task = tasks[0]
        model_name = TASK_MODEL_MAP.get(task, "gpt-3.5-turbo")

        if token_count > 100_000:
            model_name = "gemini-pro"
        if input_type in ["image", "audio"]:
            model_name = "gpt-3.5-turbo"

        client = get_model_client(model_name)
        output = client.process(input_data)
        out_tokens = estimate_token_count(output)
        cost = calculate_cost(model_name, token_count, out_tokens)

        responses.append({
            "task": task,
            "model": model_name,
            "output": output,
            "tokens_in": token_count,
            "tokens_out": out_tokens,
            "cost": round(cost, 4)
        })

    elif mode == "parallel":
        for task in tasks:
            model_name = TASK_MODEL_MAP.get(task, "gpt-3.5-turbo")
            client = get_model_client(model_name)
            partial_output = client.process(input_data)
            out_tokens = estimate_token_count(partial_output)
            cost = calculate_cost(model_name, token_count, out_tokens)

            responses.append({
                "task": task,
                "model": model_name,
                "output": partial_output,
                "tokens_in": token_count,
                "tokens_out": out_tokens,
                "cost": round(cost, 4)
            })

    elif mode == "sequential":
        for task in tasks:
            model_name = TASK_MODEL_MAP.get(task, "gpt-3.5-turbo")

            if model_name == prev_model:
                responses.append({
                    "task": task,
                    "model": model_name,
                    "output": "[SKIPPED: same model as previous step]",
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "cost": 0.0
                })
                continue

            prev_model = model_name
            client = get_model_client(model_name)
            output = client.process(output)  # Output from previous step
            out_tokens = estimate_token_count(output)
            cost = calculate_cost(model_name, token_count, out_tokens)

            responses.append({
                "task": task,
                "model": model_name,
                "output": output,
                "tokens_in": token_count,
                "tokens_out": out_tokens,
                "cost": round(cost, 4)
            })

    print(f"[INFO] Mode: {mode} | Tasks: {tasks}")
    return responses
