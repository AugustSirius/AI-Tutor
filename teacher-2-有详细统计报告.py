#!/usr/bin/env python3
"""
AI Teaching Assistant
Usage: python teacher.py
"""
import openai
import os
import sys

# ============ CONFIGURATION ============
POE_API_KEY = "67oQnDb5KQV8iaUpgEIB5wi_bmwU_dE0Wnm9aJVnA3o"
BASE_URL = "https://api.poe.com/v1"
MODEL = "Gemini-2.5-Flash"

MATERIALS_FILE = "class_materials.txt"
PROMPT_FILE = "system_prompt.txt"

# ===== FEATURE TOGGLES =====
STREAMING = True  # Set to False for instant full response

# ===== PRICING (per 1M tokens) =====
# Gemini 2.5 Flash pricing
PRICE_INPUT = 0.30   # $0.30 per 1M input tokens
PRICE_OUTPUT = 2.50  # $2.50 per 1M output tokens

# ============ SETUP ============
client = openai.OpenAI(api_key=POE_API_KEY, base_url=BASE_URL)

# Session statistics
session_stats = {
    'total_input_tokens': 0,
    'total_output_tokens': 0,
    'total_cost': 0.0,
    'message_count': 0
}

def load_file(filename):
    """Load content from a text file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: {filename} not found!")
        return ""

def calculate_cost(input_tokens, output_tokens):
    """Calculate cost based on token usage"""
    input_cost = (input_tokens / 1_000_000) * PRICE_INPUT
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT
    total_cost = input_cost + output_cost
    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': total_cost
    }

def display_stats(input_tokens, output_tokens, cost_info):
    """Display token usage and cost statistics"""
    print(f"\n💰 Message Cost:")
    print(f"   📥 Input:  {input_tokens:,} tokens (${cost_info['input_cost']:.6f})")
    print(f"   📤 Output: {output_tokens:,} tokens (${cost_info['output_cost']:.6f})")
    print(f"   💵 Total:  ${cost_info['total_cost']:.6f}")
    
    # Update session stats
    session_stats['total_input_tokens'] += input_tokens
    session_stats['total_output_tokens'] += output_tokens
    session_stats['total_cost'] += cost_info['total_cost']
    session_stats['message_count'] += 1
    
    print(f"\n📊 Session Stats:")
    print(f"   Messages: {session_stats['message_count']}")
    print(f"   Total Tokens: {session_stats['total_input_tokens'] + session_stats['total_output_tokens']:,}")
    print(f"   Session Cost: ${session_stats['total_cost']:.6f}")

def ask_teacher_streaming(question, conversation_history=None):
    """Ask the AI teacher with streaming response"""
    
    # Load materials and prompt
    materials = load_file(MATERIALS_FILE)
    system_prompt = load_file(PROMPT_FILE)
    
    # Combine system prompt with course materials
    full_system_prompt = f"""{system_prompt}

## Course Materials Available to You:

{materials}

---

Use these materials to answer student questions. Always cite which chapter/section your answer comes from.
"""
    
    # Build message history
    messages = [{"role": "system", "content": full_system_prompt}]
    
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
        
        # For streaming, we need to make another call to get token counts
        # Or estimate based on the response
        # Let's make a non-streaming call just to get usage stats
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages + [{"role": "assistant", "content": answer}],
            temperature=0.7,
            max_tokens=1  # Minimal, just to get stats
        )
        
        # Get token usage from the response
        input_tokens = response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0
        output_tokens = len(answer.split()) * 1.3  # Rough estimate: 1 token ≈ 0.75 words
        
        # Calculate and display costs
        cost_info = calculate_cost(input_tokens, int(output_tokens))
        display_stats(input_tokens, int(output_tokens), cost_info)
        
        return answer, messages + [{"role": "assistant", "content": answer}]
        
    except Exception as e:
        return f"❌ Error: {str(e)}", messages

def ask_teacher_non_streaming(question, conversation_history=None):
    """Ask the AI teacher with instant full response"""
    
    # Load materials and prompt
    materials = load_file(MATERIALS_FILE)
    system_prompt = load_file(PROMPT_FILE)
    
    # Combine system prompt with course materials
    full_system_prompt = f"""{system_prompt}

## Course Materials Available to You:

{materials}

---

Use these materials to answer student questions. Always cite which chapter/section your answer comes from.
"""
    
    # Build message history
    messages = [{"role": "system", "content": full_system_prompt}]
    
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
        
        # Get token usage
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        # Calculate and display costs
        cost_info = calculate_cost(input_tokens, output_tokens)
        
        print(answer)
        display_stats(input_tokens, output_tokens, cost_info)
        
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
    print(f"💵 Pricing: ${PRICE_INPUT}/1M input, ${PRICE_OUTPUT}/1M output")
    print(f"💡 Type 'quit' or 'exit' to end")
    print(f"💡 Type 'stats' to see session statistics\n")
    
    conversation_history = []
    
    while True:
        # Get student question
        question = input("\n🧑‍🎓 You: ").strip()
        
        # Exit condition
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n" + "=" * 60)
            print("📊 FINAL SESSION STATISTICS")
            print("=" * 60)
            print(f"Total Messages: {session_stats['message_count']}")
            print(f"Total Input Tokens: {session_stats['total_input_tokens']:,}")
            print(f"Total Output Tokens: {session_stats['total_output_tokens']:,}")
            print(f"Total Tokens: {session_stats['total_input_tokens'] + session_stats['total_output_tokens']:,}")
            print(f"💵 Total Session Cost: ${session_stats['total_cost']:.6f}")
            print("\n👋 Happy studying! See you next time!")
            break
        
        # Show stats
        if question.lower() == 'stats':
            print("\n📊 Current Session Statistics:")
            print(f"   Messages: {session_stats['message_count']}")
            print(f"   Input Tokens: {session_stats['total_input_tokens']:,}")
            print(f"   Output Tokens: {session_stats['total_output_tokens']:,}")
            print(f"   Total Tokens: {session_stats['total_input_tokens'] + session_stats['total_output_tokens']:,}")
            print(f"   💵 Total Cost: ${session_stats['total_cost']:.6f}")
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