#!/usr/bin/env python3
"""
Flask API wrapper for AI Teaching Assistant
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

# Pricing (per 1M tokens)
PRICE_INPUT = 0.30
PRICE_OUTPUT = 2.50
PRICE_CACHE_WRITE = 0.03
PRICE_CACHE_READ = 0.03
PRICE_CACHE_STORAGE = 1.00

client = openai.OpenAI(api_key=POE_API_KEY, base_url=BASE_URL)

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
    encoder = tiktoken.encoding_for_model("gpt-4")
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("⚠️  tiktoken not installed. Using approximation.")

sessions = {}

CACHED_MATERIALS = ""
CACHED_SYSTEM_PROMPT = ""

def count_tokens(text):
    """Accurately count tokens"""
    if TIKTOKEN_AVAILABLE:
        return len(encoder.encode(text))
    else:
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len([w for w in text.split() if any(c.isalpha() for c in w)])
        other_chars = len(text) - chinese_chars - sum(len(w) for w in text.split())
        return int(chinese_chars * 1.5 + english_words * 0.75 + other_chars * 0.3)

def load_file(filename):
    """Load content from a text file"""
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
print(f"📊 Token Count Verification:")
print(f"{'='*60}")
print(f"System Prompt: {count_tokens(CACHED_SYSTEM_PROMPT):,} tokens")
print(f"Class Materials: {count_tokens(CACHED_MATERIALS):,} tokens")
print(f"Full Cached Prompt: {CACHED_TOKENS_SIZE:,} tokens")
print(f"Method: {'tiktoken (accurate)' if TIKTOKEN_AVAILABLE else 'approximation'}")
print(f"{'='*60}\n")

def get_or_create_session(session_id):
    """Get or create a session"""
    if session_id not in sessions:
        sessions[session_id] = {
            'cache_created': False,
            'session_start_time': time.time(),
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cache_write_tokens': 0,
            'total_cache_read_tokens': 0,
            'total_cost': 0.0,
            'message_count': 0
        }
    return sessions[session_id]

def calculate_cost(input_tokens, output_tokens, cache_write_tokens=0, cache_read_tokens=0):
    """Calculate cost based on token usage with caching"""
    input_cost = (input_tokens / 1_000_000) * PRICE_INPUT
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT
    cache_write_cost = (cache_write_tokens / 1_000_000) * PRICE_CACHE_WRITE
    cache_read_cost = (cache_read_tokens / 1_000_000) * PRICE_CACHE_READ
    
    total_cost = input_cost + output_cost + cache_write_cost + cache_read_cost
    
    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'cache_write_cost': cache_write_cost,
        'cache_read_cost': cache_read_cost,
        'total_cost': total_cost
    }

def format_cost_report(session, input_tokens, output_tokens, cost_info, is_first_message):
    """Format a concise cost report"""
    report = "\n\n---\n\n"
    report += "**💰 Cost Analysis** (Gemini-2.5-Flash)\n\n"
    report += f"*Pricing: Input ${PRICE_INPUT}/1M | Output ${PRICE_OUTPUT}/1M | Cache Write ${PRICE_CACHE_WRITE}/1M | Cache Read ${PRICE_CACHE_READ}/1M*\n\n"
    
    if is_first_message:
        report += f"- 📝 Cache Write: {int(CACHED_TOKENS_SIZE):,} tokens (${cost_info['cache_write_cost']:.6f})\n"
        report += f"- 📥 Input: {input_tokens:,} tokens (${cost_info['input_cost']:.6f})\n"
    else:
        report += f"- 💾 Cache Read: {int(CACHED_TOKENS_SIZE):,} tokens (${cost_info['cache_read_cost']:.6f})\n"
        report += f"- 📥 Input: {input_tokens:,} tokens (${cost_info['input_cost']:.6f})\n"
    
    report += f"- 📤 Output: {output_tokens:,} tokens (${cost_info['output_cost']:.6f})\n"
    report += f"- **💵 Total: ${cost_info['total_cost']:.6f} (≈¥{cost_info['total_cost']*7.2:.4f})**\n\n"
    
    elapsed_hours = (time.time() - session['session_start_time']) / 3600
    storage_cost = (CACHED_TOKENS_SIZE / 1_000_000) * PRICE_CACHE_STORAGE * elapsed_hours
    total_with_storage = session['total_cost'] + storage_cost
    
    report += f"**📊 Session:** {session['message_count']} messages | ${total_with_storage:.6f} (≈¥{total_with_storage*7.2:.4f})"
    
    return report

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok", 
        "model": MODEL,
        "caching_enabled": True,
        "cached_size": int(CACHED_TOKENS_SIZE),
        "tiktoken_available": TIKTOKEN_AVAILABLE
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint - streaming response with cost tracking"""
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
            
            question_tokens = count_tokens(user_message)
            output_tokens = count_tokens(full_response)
            
            if is_first_message:
                cache_write_tokens = CACHED_TOKENS_SIZE
                cache_read_tokens = 0
                input_tokens = question_tokens
                session['cache_created'] = True
                session['total_cache_write_tokens'] = cache_write_tokens
            else:
                cache_write_tokens = 0
                cache_read_tokens = CACHED_TOKENS_SIZE
                input_tokens = question_tokens
                session['total_cache_read_tokens'] += cache_read_tokens
            
            cost_info = calculate_cost(
                int(input_tokens),
                int(output_tokens),
                int(cache_write_tokens),
                int(cache_read_tokens)
            )
            
            session['total_input_tokens'] += int(input_tokens)
            session['total_output_tokens'] += int(output_tokens)
            session['total_cost'] += cost_info['total_cost']
            session['message_count'] += 1
            
            cost_report = format_cost_report(session, int(input_tokens), int(output_tokens), 
                                            cost_info, is_first_message)
            yield f"data: {json.dumps({'type': 'cost_report', 'content': cost_report})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/materials', methods=['GET'])
def get_materials():
    """Return class materials"""
    return jsonify({
        "system_prompt": CACHED_SYSTEM_PROMPT,
        "class_materials": CACHED_MATERIALS
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AI Teaching Assistant API")
    print("=" * 60)
    print(f"📚 Model: {MODEL}")
    print(f"💾 Caching: ENABLED")
    print(f"📦 Cached Size: {int(CACHED_TOKENS_SIZE):,} tokens")
    print(f"🌐 Server: http://0.0.0.0:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)