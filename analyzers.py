import json
import os
import openai
from transformers import GPT2TokenizerFast

tokenizer = None

def get_tokenizer():
    global tokenizer
    if tokenizer is None:
        from transformers import GPT2TokenizerFast
        tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    return tokenizer


# File paths
BASE_DIR = os.path.dirname(__file__)
TASK_KEYWORDS_PATH = os.path.join(BASE_DIR, "task_keywords.json")
TASK_MODEL_MAP_PATH = os.path.join(BASE_DIR, "task_model_map.json")

# Load keyword rules
with open(TASK_KEYWORDS_PATH, "r") as f:
    TASK_KEYWORDS = json.load(f)

# Load model map
if os.path.exists(TASK_MODEL_MAP_PATH):
    with open(TASK_MODEL_MAP_PATH, "r") as f:
        TASK_MODEL_MAP = json.load(f)
else:
    TASK_MODEL_MAP = {}

def detect_input_type(input_data):
    if isinstance(input_data, str):
        return "text"
    elif hasattr(input_data, "filename"):
        ext = input_data.filename.split(".")[-1]
        if ext in ["jpg", "jpeg", "png"]:
            return "image"
        elif ext in ["mp3", "wav"]:
            return "audio"
    return "unknown"

def estimate_token_count(text):
    if not isinstance(text, str):
        return 0
    tok = get_tokenizer()
    return len(tok.encode(text))

def rule_based_classifier(text):
    text = text.lower()
    hits = []
    for task, keywords in TASK_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            hits.append(task)
    return hits

def zero_shot_classifier(text):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    task_list = ", ".join(TASK_KEYWORDS.keys())

    system_prompt = (
        "You are a task classifier and model selector. "
        "Classify the user's input into one or more of the following tasks: "
        + task_list + ". "
        "Then choose the best model (disabled, mistral-small, gemini-pro) for each.\n\n"

        "disabled (OpenAI):\n"
        "- Fast, accessible, and free for light use\n"
        "- Great chat formatting and multilingual support\n"
        "- Best for general conversation, short tasks, and casual summarization\n\n"

        "mistral-small (Mistral AI):\n"
        "- Lightweight, fast open-weight model\n"
        "- Strong at summarization, instruction following, and ethics\n"
        "- Best for summaries, moral reviews, and aligned responses\n\n"

        "gemini-pro (Google):\n"
        "- Solid reasoning and retrieval capability\n"
        "- Fast for structured prompts like code or tabular summaries\n"
        "- Best for lightweight coding, QA, and analysis-like tasks\n\n"

        "Respond like this:\n"
        "Task: <task_name>\nModel: <model_name>\n(Task: <task_name>\nModel: <model_name>) ..."
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classify this: {text}"}
            ],
            temperature=0,
            max_tokens=50
        )

        lines = response.choices[0].message["content"].strip().splitlines()
        tasks = []
        current_task = None

        for line in lines:
            if line.lower().startswith("task:"):
                current_task = line.split(":", 1)[1].strip().lower()
                tasks.append(current_task)
            elif line.lower().startswith("model:") and current_task:
                model = line.split(":", 1)[1].strip()
                if current_task not in TASK_MODEL_MAP:
                    TASK_MODEL_MAP[current_task] = model
                current_task = None

        for task in tasks:
            if task not in TASK_KEYWORDS:
                TASK_KEYWORDS[task] = [text.strip().split()[0]]
            else:
                new_words = [w for w in text.lower().split() if w not in TASK_KEYWORDS[task]]
                if new_words:
                    TASK_KEYWORDS[task].append(new_words[0])

        # Save updates
        with open(TASK_KEYWORDS_PATH, "w") as f:
            json.dump(TASK_KEYWORDS, f, indent=2)
        with open(TASK_MODEL_MAP_PATH, "w") as f:
            json.dump(TASK_MODEL_MAP, f, indent=2)

        return tasks or ["chat"]

    except Exception as e:
        print(f"[ERROR] Zero-shot classification failed: {e}")
        return ["chat"]

def classify_task(text):
    # Step 1: Try rule-based match
    rule_hits = rule_based_classifier(text)
    if rule_hits:
        return rule_hits
    return ['chats']
    return zero_shot_classifier(text)
