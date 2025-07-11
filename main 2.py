from flask import Flask, request, jsonify
from router import route_request
from dotenv import load_dotenv
import json
import os

app = Flask(__name__)
load_dotenv()

@app.route("/run", methods=["POST"])
def handle_input():
    data = request.get_json()
    input_text = data.get("input", "")

    if not input_text:
        return jsonify({"error": "No input provided"}), 400

    # Log the input
    log_entry = {"input": input_text}
    log_path = "execution_log.json"
    if os.path.exists(log_path):
        with open(log_path, "r+", encoding="utf-8") as file:
            try:
                existing_data = json.load(file)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
            except json.JSONDecodeError:
                existing_data = []
            existing_data.append(log_entry)
            file.seek(0)
            json.dump(existing_data, file, indent=2)
    else:
        with open(log_path, "w", encoding="utf-8") as file:
            json.dump([log_entry], file, indent=2)

    # Process input through routing pipeline
    results = route_request(input_text)

    # Log output if present
    filtered_outputs = [r for r in results if r.get("output")]
    if filtered_outputs:
        output_log_path = "output_only_log.json"
        if os.path.exists(output_log_path):
            with open(output_log_path, "r+", encoding="utf-8") as f:
                try:
                    prev_outputs = json.load(f)
                    if not isinstance(prev_outputs, list):
                        prev_outputs = [prev_outputs]
                except json.JSONDecodeError:
                    prev_outputs = []
                prev_outputs.append({
                    "input": input_text,
                    "outputs": filtered_outputs
                })
                f.seek(0)
                json.dump(prev_outputs, f, indent=2)
        else:
            with open(output_log_path, "w", encoding="utf-8") as f:
                json.dump([{
                    "input": input_text,
                    "outputs": filtered_outputs
                }], f, indent=2)

    return jsonify(results)

@app.route("/usage", methods=["POST"])
def usage_summary():
    output_log_path = "output_only_log.json"

    if not os.path.exists(output_log_path):
        return jsonify({"error": "No usage log found"}), 404

    try:
        with open(output_log_path, "r", encoding="utf-8") as f:
            log_entries = json.load(f)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in output log"}), 500

    usage_by_model = {}
    total_calls = 0

    for entry in log_entries:
        for result in entry.get("outputs", []):
            model = result.get("model")

            if model not in usage_by_model:
                usage_by_model[model] = {"calls": 0}

            usage_by_model[model]["calls"] += 1
            total_calls += 1

    # Calculate percentage usage
    for model in usage_by_model:
        calls = usage_by_model[model]["calls"]
        usage_by_model[model]["usage_percent"] = round((calls / total_calls) * 100, 2)

    return jsonify({
        "summary": usage_by_model,
        "total_model_calls": total_calls
    })

@app.route("/prompts", methods=["POST"])
def list_prompts():
    output_log_path = "output_only_log.json"

    if not os.path.exists(output_log_path):
        return jsonify({"error": "No log file found"}), 404

    try:
        with open(output_log_path, "r", encoding="utf-8") as f:
            log_entries = json.load(f)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON structure in log"}), 500

    response = []
    for entry in log_entries:
        input_text = entry.get("input", "")
        for result in entry.get("outputs", []):
            response.append({
                "input": input_text,
                "model": result.get("model", ""),
                "output": result.get("output", "")
            })

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    print('runnning')