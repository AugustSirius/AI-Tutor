#!/usr/bin/env python3
"""
Flask API wrapper for AI Teaching Assistant with Enhanced Cost Tracking
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
    print("⚠️  Warning: tiktoken not installed. Using approximation.")

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
print(f"Method: {'tiktoken (accurate)' if TIKTOKEN_AVAILABLE else 'approximation'}")
print(f"{'='*60}\n")

def get_or_create_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            'cache_created': False,
            'session_start_time': time.time(),
            'total_cost': 0.0,
            'message_count': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cached_tokens': 0
        }
    return sessions[session_id]

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok", 
        "model": MODEL,
        "cached_size": int(CACHED_TOKENS_SIZE),
        "tiktoken_available": TIKTOKEN_AVAILABLE
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
                max_tokens=8000,  # Increased from 2000
                stream=True
            )
            
            full_response = ""
            thinking_content = ""
            in_thinking = False
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # Detect thinking blocks
                    if '<thinking>' in content:
                        in_thinking = True
                        yield f"data: {json.dumps({'type': 'thinking_start'})}\n\n"
                    
                    if in_thinking:
                        thinking_content += content
                        if '</thinking>' in content:
                            in_thinking = False
                            yield f"data: {json.dumps({'type': 'thinking_end', 'content': thinking_content})}\n\n"
                            thinking_content = ""
                        else:
                            yield f"data: {json.dumps({'type': 'thinking', 'content': content})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
            
            # Calculate costs with accurate token counting
            question_tokens = count_tokens(user_message)
            output_tokens = count_tokens(full_response)
            
            if is_first_message:
                cache_tokens = CACHED_TOKENS_SIZE
                cache_write_cost = (cache_tokens / 1_000_000) * PRICE_CACHE_WRITE
                cache_read_cost = 0
                session['cache_created'] = True
                cost_type = "Write"
            else:
                cache_tokens = CACHED_TOKENS_SIZE
                cache_write_cost = 0
                cache_read_cost = (cache_tokens / 1_000_000) * PRICE_CACHE_READ
                cost_type = "Read"
            
            input_cost = (question_tokens / 1_000_000) * PRICE_INPUT
            output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT
            total_cost = input_cost + output_cost + cache_write_cost + cache_read_cost
            
            # Update session stats
            session['total_cost'] += total_cost
            session['message_count'] += 1
            session['total_input_tokens'] += question_tokens
            session['total_output_tokens'] += output_tokens
            session['total_cached_tokens'] += cache_tokens
            
            # Detailed cost report
            cost_report = "\n\n---\n\n"
            cost_report += "**💰 Cost Analysis (Detailed)**\n\n"
            cost_report += f"**Model:** {MODEL}\n\n"
            cost_report += f"**Pricing:** Input ${PRICE_INPUT}/1M | Output ${PRICE_OUTPUT}/1M | Cache Write ${PRICE_CACHE_WRITE}/1M | Cache Read ${PRICE_CACHE_READ}/1M\n\n"
            cost_report += "**This Message:**\n"
            cost_report += f"- 📦 Cache {cost_type}: {int(cache_tokens):,} tokens × ${PRICE_CACHE_WRITE if is_first_message else PRICE_CACHE_READ}/1M = ${cache_write_cost + cache_read_cost:.6f}\n"
            cost_report += f"- 📥 Input: {question_tokens:,} tokens × ${PRICE_INPUT}/1M = ${input_cost:.6f}\n"
            cost_report += f"- 📤 Output: {output_tokens:,} tokens × ${PRICE_OUTPUT}/1M = ${output_cost:.6f}\n"
            cost_report += f"- **💵 Subtotal: ${total_cost:.6f} (≈¥{total_cost*7.2:.2f})**\n\n"
            
            # Session summary
            elapsed_hours = (time.time() - session['session_start_time']) / 3600
            storage_cost = (CACHED_TOKENS_SIZE / 1_000_000) * PRICE_CACHE_STORAGE * elapsed_hours
            total_with_storage = session['total_cost'] + storage_cost
            
            cost_report += "**📊 Session Summary:**\n"
            cost_report += f"- Messages: {session['message_count']}\n"
            cost_report += f"- Total Input: {session['total_input_tokens']:,} tokens\n"
            cost_report += f"- Total Output: {session['total_output_tokens']:,} tokens\n"
            cost_report += f"- API Cost: ${session['total_cost']:.6f} (≈¥{session['total_cost']*7.2:.2f})\n"
            cost_report += f"- Cache Storage ({elapsed_hours:.2f}h): ${storage_cost:.6f} (≈¥{storage_cost*7.2:.2f})\n"
            cost_report += f"- **💰 Total Cost: ${total_with_storage:.6f} (≈¥{total_with_storage*7.2:.2f})**\n"
            
            yield f"data: {json.dumps({'type': 'cost_report', 'content': cost_report})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
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
    print(f"📝 Max Tokens: 8000")
    print(f"🌐 http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)