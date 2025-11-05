#!/usr/bin/env python3
"""
Flask API wrapper for AI Teaching Assistant with Prompt Caching
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import openai
import json
import time

app = Flask(__name__)
CORS(app)

# ============ CONFIGURATION ============
POE_API_KEY = "67oQnDb5KQV8iaUpgEIB5wi_bmwU_dE0Wnm9aJVnA3o"
BASE_URL = "https://api.poe.com/v1"
MODEL = "Gemini-2.5-Flash"

# Pricing
PRICE_INPUT = 0.30
PRICE_OUTPUT = 2.50
PRICE_CACHE_WRITE = 0.03
PRICE_CACHE_READ = 0.03
PRICE_CACHE_STORAGE = 1.00

client = openai.OpenAI(api_key=POE_API_KEY, base_url=BASE_URL)

# Try to import tiktoken
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
    encoder = tiktoken.encoding_for_model("gpt-4")
except ImportError:
    TIKTOKEN_AVAILABLE = False

sessions = {}

def count_tokens(text):
    if TIKTOKEN_AVAILABLE:
        return len(encoder.encode(text))
    else:
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len([w for w in text.split() if any(c.isalpha() for c in w)])
        return int(chinese_chars * 1.5 + english_words * 0.75)

def load_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""

CACHED_MATERIALS = load_file('class_materials.txt')
CACHED_SYSTEM_PROMPT = load_file('system_prompt.txt')

FULL_PROMPT = f"""{CACHED_SYSTEM_PROMPT}

## Course Materials Available to You:

{CACHED_MATERIALS}

---

Use these materials to answer student questions. Always cite which chapter/section your answer comes from.
"""

CACHED_TOKENS_SIZE = count_tokens(FULL_PROMPT)

print(f"\n{'='*60}")
print(f"📊 Token Count:")
print(f"System Prompt: {count_tokens(CACHED_SYSTEM_PROMPT):,} tokens")
print(f"Class Materials: {count_tokens(CACHED_MATERIALS):,} tokens")
print(f"Total Cached: {CACHED_TOKENS_SIZE:,} tokens")
print(f"{'='*60}\n")

def get_or_create_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            'cache_created': False,
            'session_start_time': time.time(),
            'total_cost': 0.0,
            'message_count': 0
        }
    return sessions[session_id]

def calculate_cost(input_tokens, output_tokens, cache_write_tokens=0, cache_read_tokens=0):
    input_cost = (input_tokens / 1_000_000) * PRICE_INPUT
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT
    cache_write_cost = (cache_write_tokens / 1_000_000) * PRICE_CACHE_WRITE
    cache_read_cost = (cache_read_tokens / 1_000_000) * PRICE_CACHE_READ
    total_cost = input_cost + output_cost + cache_write_cost + cache_read_cost
    return total_cost

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok", 
        "model": MODEL,
        "cached_size": int(CACHED_TOKENS_SIZE)
    })

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    history = data.get('history', [])
    session_id = data.get('session_id', 'default')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    session = get_or_create_session(session_id)
    is_first_message = not session['cache_created']
    
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
            
            full_response = ""
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'content': content})}\n\n"
            
            # Calculate costs
            question_tokens = count_tokens(user_message)
            output_tokens = count_tokens(full_response)
            
            if is_first_message:
                cache_write_tokens = CACHED_TOKENS_SIZE
                cache_read_tokens = 0
                input_tokens = question_tokens
                session['cache_created'] = True
                cost_type = "Cache Write"
            else:
                cache_write_tokens = 0
                cache_read_tokens = CACHED_TOKENS_SIZE
                input_tokens = question_tokens
                cost_type = "Cache Read"
            
            total_cost = calculate_cost(input_tokens, output_tokens, cache_write_tokens, cache_read_tokens)
            session['total_cost'] += total_cost
            session['message_count'] += 1
            
            # Simple cost report
            cost_report = f"\n\n---\n\n**💰 Cost:** "
            cost_report += f"{cost_type} {int(CACHED_TOKENS_SIZE):,} tokens | "
            cost_report += f"Input {input_tokens:,} | Output {output_tokens:,} | "
            cost_report += f"${total_cost:.6f} (≈¥{total_cost*7.2:.2f})\n\n"
            cost_report += f"**Session:** {session['message_count']} messages | ${session['total_cost']:.6f} (≈¥{session['total_cost']*7.2:.2f})"
            
            yield f"data: {json.dumps({'content': cost_report})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/materials', methods=['GET'])
def get_materials():
    return jsonify({
        "system_prompt": CACHED_SYSTEM_PROMPT,
        "class_materials": CACHED_MATERIALS
    })

if __name__ == '__main__':
    print("🚀 AI Teaching Assistant API")
    print(f"📚 Model: {MODEL}")
    print(f"💾 Caching: ENABLED")
    print(f"🌐 http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)