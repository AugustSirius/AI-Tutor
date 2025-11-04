#!/usr/bin/env python3
"""
AI Teaching Assistant with Prompt Caching
Usage: python teacher.py
"""
import openai
import os
import sys
import time

# ============ CONFIGURATION ============
POE_API_KEY = "67oQnDb5KQV8iaUpgEIB5wi_bmwU_dE0Wnm9aJVnA3o"
BASE_URL = "https://api.poe.com/v1"
MODEL = "Gemini-2.5-Flash"

MATERIALS_FILE = "class_materials.txt"
PROMPT_FILE = "system_prompt.txt"

# ===== FEATURE TOGGLES =====
STREAMING = True  # Set to False for instant full response
USE_CACHING = True  # Enable prompt caching

# ===== PRICING (per 1M tokens) - Gemini 2.5 Flash =====
PRICE_INPUT = 0.30        # Regular input tokens
PRICE_OUTPUT = 2.50       # Output tokens (includes thinking)
PRICE_CACHE_WRITE = 0.03  # First time caching (cheaper than input!)
PRICE_CACHE_READ = 0.03   # Reading from cache (10x cheaper!)
PRICE_CACHE_STORAGE = 1.00  # Storage cost per 1M tokens per hour

# Cache settings
CACHE_TTL_HOURS = 2  # How long cache stays valid (for a 2-hour class)

# ============ SETUP ============
client = openai.OpenAI(api_key=POE_API_KEY, base_url=BASE_URL)

# Session statistics
session_stats = {
    'total_input_tokens': 0,
    'total_output_tokens': 0,
    'total_cache_write_tokens': 0,
    'total_cache_read_tokens': 0,
    'total_cost': 0.0,
    'cache_storage_cost': 0.0,
    'message_count': 0,
    'cache_created': False,
    'session_start_time': None,
    'cached_tokens_size': 0  # Size of cached content
}

# ===== CACHE: Load once at startup =====
CACHED_MATERIALS = None
CACHED_SYSTEM_PROMPT = None
CACHED_FULL_PROMPT = None

def load_file(filename):
    """Load content from a text file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: {filename} not found!")
        return ""

def initialize_cache():
    """Load all files once at startup"""
    global CACHED_MATERIALS, CACHED_SYSTEM_PROMPT, CACHED_FULL_PROMPT
    
    print("📂 Loading course materials...", end="", flush=True)
    CACHED_MATERIALS = load_file(MATERIALS_FILE)
    print(" ✓")
    
    print("📋 Loading system prompt...", end="", flush=True)
    CACHED_SYSTEM_PROMPT = load_file(PROMPT_FILE)
    print(" ✓")
    
    # Pre-build the full system prompt (this will be cached)
    CACHED_FULL_PROMPT = f"""{CACHED_SYSTEM_PROMPT}

## Course Materials Available to You:

{CACHED_MATERIALS}

---

Use these materials to answer student questions. Always cite which chapter/section your answer comes from.
"""
    
    # Estimate cached content size
    session_stats['cached_tokens_size'] = len(CACHED_FULL_PROMPT.split()) * 1.3
    
    print("✅ Ready to help!\n")

def calculate_cost(input_tokens, output_tokens, cache_write_tokens=0, cache_read_tokens=0):
    """Calculate cost based on token usage with caching"""
    # Regular input cost (non-cached new tokens)
    input_cost = (input_tokens / 1_000_000) * PRICE_INPUT
    
    # Output cost
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT
    
    # Cache write cost (first message - writing to cache)
    cache_write_cost = (cache_write_tokens / 1_000_000) * PRICE_CACHE_WRITE
    
    # Cache read cost (subsequent messages - reading from cache)
    cache_read_cost = (cache_read_tokens / 1_000_000) * PRICE_CACHE_READ
    
    total_cost = input_cost + output_cost + cache_write_cost + cache_read_cost
    
    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'cache_write_cost': cache_write_cost,
        'cache_read_cost': cache_read_cost,
        'total_cost': total_cost
    }

def calculate_cache_storage_cost():
    """Calculate cache storage cost based on session duration"""
    if not session_stats['session_start_time']:
        return 0.0
    
    # Calculate hours elapsed
    elapsed_seconds = time.time() - session_stats['session_start_time']
    elapsed_hours = elapsed_seconds / 3600
    
    # Storage cost = tokens_size * price_per_1M * hours
    storage_cost = (session_stats['cached_tokens_size'] / 1_000_000) * PRICE_CACHE_STORAGE * elapsed_hours
    
    return storage_cost

def display_stats(input_tokens, output_tokens, cost_info, is_first_message=False):
    """Display token usage and cost statistics"""
    print(f"\n💰 Message Cost:")
    
    if is_first_message and USE_CACHING:
        print(f"   📝 Cache Write: {int(session_stats['cached_tokens_size']):,} tokens (${cost_info['cache_write_cost']:.6f}) [First time]")
        print(f"   📥 New Input:   {input_tokens:,} tokens (${cost_info['input_cost']:.6f})")
    elif USE_CACHING and session_stats['cache_created']:
        print(f"   💾 Cache Read:  {int(session_stats['cached_tokens_size']):,} tokens (${cost_info['cache_read_cost']:.6f}) [From cache!]")
        print(f"   📥 New Input:   {input_tokens:,} tokens (${cost_info['input_cost']:.6f})")
    else:
        print(f"   📥 Input:  {input_tokens:,} tokens (${cost_info['input_cost']:.6f})")
    
    print(f"   📤 Output: {output_tokens:,} tokens (${cost_info['output_cost']:.6f})")
    print(f"   💵 Total:  ${cost_info['total_cost']:.6f}")
    
    # Calculate and show cache storage cost
    storage_cost = calculate_cache_storage_cost()
    session_stats['cache_storage_cost'] = storage_cost
    
    if USE_CACHING and session_stats['cache_created']:
        elapsed_hours = (time.time() - session_stats['session_start_time']) / 3600
        print(f"   🗄️  Cache Storage: ${storage_cost:.6f} ({elapsed_hours:.2f}h × {int(session_stats['cached_tokens_size']):,} tokens)")
    
    # Update session stats
    session_stats['total_input_tokens'] += input_tokens
    session_stats['total_output_tokens'] += output_tokens
    session_stats['total_cost'] += cost_info['total_cost']
    session_stats['message_count'] += 1
    
    # Calculate total including storage
    total_with_storage = session_stats['total_cost'] + session_stats['cache_storage_cost']
    
    print(f"\n📊 Session Stats:")
    print(f"   Messages: {session_stats['message_count']}")
    print(f"   Total Tokens: {session_stats['total_input_tokens'] + session_stats['total_output_tokens']:,}")
    print(f"   API Cost: ${session_stats['total_cost']:.6f}")
    if USE_CACHING and session_stats['cache_created']:
        print(f"   Cache Storage: ${session_stats['cache_storage_cost']:.6f}")
        print(f"   💵 Total (API + Storage): ${total_with_storage:.6f}")

def ask_teacher_streaming(question, conversation_history=None):
    """Ask the AI teacher with streaming response"""
    
    # Check if this is the first message (need to create cache)
    is_first_message = not session_stats['cache_created']
    
    # Build message history
    messages = [{"role": "system", "content": CACHED_FULL_PROMPT}]
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add new question
    messages.append({"role": "user", "content": question})
    
    try:
        # Create streaming response
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            stream=True
        )
        
        # Collect the response as we stream
        answer = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                answer += content
                print(content, end="", flush=True)
        
        print()  # New line after streaming
        
        # Estimate token usage
        # The question tokens (new input each time)
        question_tokens = len(question.split()) * 1.3
        output_tokens = len(answer.split()) * 1.3
        
        # Calculate costs based on caching
        if is_first_message and USE_CACHING:
            # First message: pay cache write for system prompt
            cache_write_tokens = session_stats['cached_tokens_size']
            cache_read_tokens = 0
            input_tokens = question_tokens
            session_stats['cache_created'] = True
            session_stats['total_cache_write_tokens'] = cache_write_tokens
            session_stats['session_start_time'] = time.time()
        elif USE_CACHING:
            # Subsequent messages: pay cache read for system prompt
            cache_write_tokens = 0
            cache_read_tokens = session_stats['cached_tokens_size']
            input_tokens = question_tokens
            session_stats['total_cache_read_tokens'] += cache_read_tokens
        else:
            # No caching: pay full input price
            cache_write_tokens = 0
            cache_read_tokens = 0
            input_tokens = session_stats['cached_tokens_size'] + question_tokens
        
        # Calculate and display costs
        cost_info = calculate_cost(
            int(input_tokens),
            int(output_tokens),
            int(cache_write_tokens),
            int(cache_read_tokens)
        )
        display_stats(int(input_tokens), int(output_tokens), cost_info, is_first_message)
        
        return answer, messages + [{"role": "assistant", "content": answer}]
        
    except Exception as e:
        return f"❌ Error: {str(e)}", messages

def ask_teacher_non_streaming(question, conversation_history=None):
    """Ask the AI teacher with instant full response"""
    
    # Check if this is the first message (need to create cache)
    is_first_message = not session_stats['cache_created']
    
    # Build message history
    messages = [{"role": "system", "content": CACHED_FULL_PROMPT}]
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add new question
    messages.append({"role": "user", "content": question})
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            stream=False
        )
        
        answer = response.choices[0].message.content
        
        # Get actual token usage from API
        total_prompt_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        # Calculate tokens based on caching
        question_tokens = len(question.split()) * 1.3
        
        if is_first_message and USE_CACHING:
            # First message: pay cache write
            cache_write_tokens = session_stats['cached_tokens_size']
            cache_read_tokens = 0
            input_tokens = question_tokens
            session_stats['cache_created'] = True
            session_stats['total_cache_write_tokens'] = cache_write_tokens
            session_stats['session_start_time'] = time.time()
        elif USE_CACHING:
            # Subsequent messages: pay cache read
            cache_write_tokens = 0
            cache_read_tokens = session_stats['cached_tokens_size']
            input_tokens = question_tokens
            session_stats['total_cache_read_tokens'] += cache_read_tokens
        else:
            # No caching
            cache_write_tokens = 0
            cache_read_tokens = 0
            input_tokens = total_prompt_tokens
        
        # Calculate and display costs
        cost_info = calculate_cost(
            int(input_tokens),
            output_tokens,
            int(cache_write_tokens),
            int(cache_read_tokens)
        )
        
        print(answer)
        display_stats(int(input_tokens), output_tokens, cost_info, is_first_message)
        
        return answer, messages + [{"role": "assistant", "content": answer}]
        
    except Exception as e:
        return f"❌ Error: {str(e)}", messages

# ============ INTERACTIVE MODE ============
def main():
    """Run interactive teaching assistant"""
    print("=" * 60)
    print("🎓 AI TEACHING ASSISTANT")
    print("=" * 60)
    print(f"📚 Course: Mass Spectrometry")
    print(f"🤖 Model: {MODEL}")
    print(f"⚡ Streaming: {'ON' if STREAMING else 'OFF'}")
    print(f"💾 Caching: {'ON' if USE_CACHING else 'OFF'}")
    print(f"⏱️  Cache TTL: {CACHE_TTL_HOURS}h (typical class duration)")
    print(f"💵 Pricing:")
    print(f"   • Input: ${PRICE_INPUT}/1M tokens")
    print(f"   • Output: ${PRICE_OUTPUT}/1M tokens")
    if USE_CACHING:
        print(f"   • Cache Write: ${PRICE_CACHE_WRITE}/1M tokens (first message)")
        print(f"   • Cache Read: ${PRICE_CACHE_READ}/1M tokens (subsequent)")
        print(f"   • Cache Storage: ${PRICE_CACHE_STORAGE}/1M tokens/hour")
    print()
    
    # ===== LOAD FILES ONCE AT STARTUP =====
    initialize_cache()
    
    print(f"💡 Type 'quit' or 'exit' to end")
    print(f"💡 Type 'stats' to see session statistics")
    print(f"💡 Type 'reload' to refresh course materials\n")
    
    conversation_history = []
    
    while True:
        # Get student question
        question = input("\n🧑‍🎓 You: ").strip()
        
        # Exit condition
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n" + "=" * 60)
            print("📊 FINAL SESSION STATISTICS")
            print("=" * 60)
            
            elapsed_hours = 0
            if session_stats['session_start_time']:
                elapsed_seconds = time.time() - session_stats['session_start_time']
                elapsed_hours = elapsed_seconds / 3600
            
            print(f"⏱️  Session Duration: {elapsed_hours:.2f} hours")
            print(f"Messages: {session_stats['message_count']}")
            print(f"Total Input Tokens: {session_stats['total_input_tokens']:,}")
            print(f"Total Output Tokens: {session_stats['total_output_tokens']:,}")
            
            if USE_CACHING and session_stats['cache_created']:
                print(f"\n💾 Cache Statistics:")
                print(f"   Cached Content Size: {int(session_stats['cached_tokens_size']):,} tokens")
                print(f"   Cache Write Tokens: {int(session_stats['total_cache_write_tokens']):,}")
                print(f"   Cache Read Tokens: {int(session_stats['total_cache_read_tokens']):,}")
                
                # Calculate savings
                if session_stats['message_count'] > 1:
                    without_cache_cost = (session_stats['cached_tokens_size'] * session_stats['message_count'] / 1_000_000) * PRICE_INPUT
                    with_cache_cost = session_stats['total_cache_write_tokens'] / 1_000_000 * PRICE_CACHE_WRITE + \
                                     session_stats['total_cache_read_tokens'] / 1_000_000 * PRICE_CACHE_READ + \
                                     session_stats['cache_storage_cost']
                    savings = without_cache_cost - with_cache_cost
                    savings_percent = (savings / without_cache_cost) * 100 if without_cache_cost > 0 else 0
                    
                    print(f"\n💰 Cache Savings:")
                    print(f"   Without cache: ${without_cache_cost:.6f}")
                    print(f"   With cache: ${with_cache_cost:.6f}")
                    print(f"   💚 Saved: ${savings:.6f} ({savings_percent:.1f}%)")
            
            total_with_storage = session_stats['total_cost'] + session_stats['cache_storage_cost']
            print(f"\n💵 Total Costs:")
            print(f"   API Calls: ${session_stats['total_cost']:.6f}")
            if USE_CACHING and session_stats['cache_created']:
                print(f"   Cache Storage: ${session_stats['cache_storage_cost']:.6f}")
                print(f"   Grand Total: ${total_with_storage:.6f}")
            
            print("\n👋 Happy studying! See you next time!")
            break
        
        # Reload materials
        if question.lower() == 'reload':
            print("\n🔄 Reloading course materials...")
            # Reset cache stats
            session_stats['cache_created'] = False
            session_stats['session_start_time'] = None
            initialize_cache()
            print("✅ Materials reloaded! Cache will be recreated on next message.\n")
            continue
        
        # Show stats
        if question.lower() == 'stats':
            elapsed_hours = 0
            if session_stats['session_start_time']:
                elapsed_seconds = time.time() - session_stats['session_start_time']
                elapsed_hours = elapsed_seconds / 3600
            
            print("\n📊 Current Session Statistics:")
            print(f"   ⏱️  Duration: {elapsed_hours:.2f} hours")
            print(f"   Messages: {session_stats['message_count']}")
            print(f"   Input Tokens: {session_stats['total_input_tokens']:,}")
            print(f"   Output Tokens: {session_stats['total_output_tokens']:,}")
            
            if USE_CACHING and session_stats['cache_created']:
                print(f"   💾 Cached: {int(session_stats['cached_tokens_size']):,} tokens")
                print(f"   Cache Reads: {int(session_stats['total_cache_read_tokens']):,} tokens")
            
            total_with_storage = session_stats['total_cost'] + session_stats['cache_storage_cost']
            print(f"   💵 Total Cost: ${total_with_storage:.6f}")
            continue
        
        if not question:
            continue
        
        # Get answer from AI teacher
        print("\n🤖 Teacher: ", end="", flush=True)
        
        if STREAMING:
            answer, conversation_history = ask_teacher_streaming(question, conversation_history)
        else:
            answer, conversation_history = ask_teacher_non_streaming(question, conversation_history)
        
        print("\n" + "-" * 60)

if __name__ == "__main__":
    main()