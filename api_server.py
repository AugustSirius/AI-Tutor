#!/usr/bin/env python3
"""
Flask API wrapper for AI Teaching Assistant
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import openai
import json

app = Flask(__name__)
CORS(app)  # Allow frontend to call this API

# ============ CONFIGURATION ============
POE_API_KEY = "67oQnDb5KQV8iaUpgEIB5wi_bmwU_dE0Wnm9aJVnA3o"
BASE_URL = "https://api.poe.com/v1"
MODEL = "Gemini-2.5-Flash"

client = openai.OpenAI(api_key=POE_API_KEY, base_url=BASE_URL)

# Load materials once at startup
CACHED_MATERIALS = ""
CACHED_SYSTEM_PROMPT = ""

def load_file(filename):
    """Load content from a text file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""

# Initialize on startup
CACHED_MATERIALS = load_file('class_materials.txt')
CACHED_SYSTEM_PROMPT = load_file('system_prompt.txt')

FULL_PROMPT = f"""{CACHED_SYSTEM_PROMPT}

## Course Materials Available to You:

{CACHED_MATERIALS}

---

Use these materials to answer student questions. Always cite which chapter/section your answer comes from.
"""

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "model": MODEL})

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint - streaming response"""
    data = request.json
    user_message = data.get('message', '')
    history = data.get('history', [])
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Build messages
    messages = [{"role": "system", "content": FULL_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    
    def generate():
        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'content': content})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/materials', methods=['GET'])
def get_materials():
    """Return class materials"""
    return jsonify({
        "system_prompt": CACHED_SYSTEM_PROMPT,
        "class_materials": CACHED_MATERIALS
    })

if __name__ == '__main__':
    print("🚀 Starting AI Teaching Assistant API...")
    print(f"📚 Model: {MODEL}")
    print(f"🌐 Server: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
