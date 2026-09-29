import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import CHATBOT_NAME, MODEL_NAME, REFUSAL_MESSAGE, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


@app.route("/")
def index():
    return render_template("index.html", chatbot_name=CHATBOT_NAME)


@app.route("/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({"reply": "Server error: GEMINI_API_KEY is missing in the .env file."}), 500

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"reply": "Please type a question about oceans."}), 400

    contents = []
    for item in history[-10:]:
        role = "user" if item.get("role") == "user" else "model"
        text = str(item.get("text", "")).strip()
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
            ),
        )
        reply = (response.text or "").strip() or REFUSAL_MESSAGE
        return jsonify({"reply": reply})
    except Exception:
        return jsonify({"reply": "Sorry, something went wrong. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
