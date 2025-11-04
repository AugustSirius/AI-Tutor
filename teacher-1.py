#!/usr/bin/env python3
"""
AI Teaching Assistant
Usage: python teacher.py
"""

import openai
import os

# ============ CONFIGURATION ============
POE_API_KEY = "67oQnDb5KQV8iaUpgEIB5wi_bmwU_dE0Wnm9aJVnA3o"
BASE_URL = "https://api.poe.com/v1"
MODEL = "Gemini-2.5-Flash"

MATERIALS_FILE = "class_materials.txt"
PROMPT_FILE = "system_prompt.txt"

# ============ SETUP ============
client = openai.OpenAI(api_key=POE_API_KEY, base_url=BASE_URL)

def load_file(filename):
    """Load content from a text file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: {filename} not found!")
        return ""

def ask_teacher(question, conversation_history=None):
    """Ask the AI teacher a question"""
    
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
            max_tokens=2000
        )
        
        answer = response.choices[0].message.content
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
    print(f"💡 Type 'quit' or 'exit' to end\n")
    
    conversation_history = []
    
    while True:
        # Get student question
        question = input("\n🧑‍🎓 You: ").strip()
        
        # Exit condition
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Happy studying! See you next time!")
            break
        
        if not question:
            continue
        
        # Get answer from AI teacher
        print("\n🤖 Teacher: ", end="", flush=True)
        answer, conversation_history = ask_teacher(question, conversation_history)
        print(answer)
        
        print("\n" + "-" * 60)

if __name__ == "__main__":
    main()