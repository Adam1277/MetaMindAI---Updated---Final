from flask import Flask, request, jsonify
from router import route_request
from dotenv import load_dotenv
import json
import os

app = Flask(__name__)
load_dotenv()


@app.route('/api/get-data')
def get_data():
    sample_data = {
        "message": "Hello from Flask!",
        "items": [1, 2, 3, 4, 5]
    }
    return jsonify(sample_data)

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
                json.dump([{"input": input_text, "outputs": filtered_outputs}], f, indent=2)

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
