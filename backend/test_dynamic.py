import sys
import os
# Adjust path to include src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_to_sql.llm_generator import LLMGenerator
from text_to_sql.llm_provider import LLMProvider
from langchain_core.messages import HumanMessage

def test_dynamic_switching():
    print("--- Testing Dynamic Model Switching ---")
    
    # 1. Test Default (should be Groq as per config)
    print("\n1. Testing Default Config (Groq)...")
    gen = LLMGenerator()
    provider_name = type(gen.default_llm).__name__
    print(f"Default Provider Class: {provider_name}")
    
    # 2. Test Override (e.g. OpenAI if available, or just Groq with different model)
    # Assuming OpenAI key is there, let's try to switch to OpenAI
    print("\n2. Testing OpenAI Override...")
    try:
        openai_llm = LLMProvider.get_llm(provider='openai', model_name='gpt-3.5-turbo')
        print(f"Override Provider Class: {type(openai_llm).__name__}")
        if "ChatOpenAI" in type(openai_llm).__name__:
            print("Successfully switched to OpenAI!")
    except Exception as e:
        print(f"OpenAI switch failed (might be missing key): {e}")

    # 3. Test Groq Specific Model
    print("\n3. Testing Groq with specific model...")
    try:
        groq_llm = LLMProvider.get_llm(provider='groq', model_name='llama-3.3-70b-versatile')
        print(f"Groq Provider Class: {type(groq_llm).__name__}")
        print(f"Groq Model: {groq_llm.model_name}")
    except Exception as e:
        print(f"Groq switch failed: {e}")

if __name__ == "__main__":
    test_dynamic_switching()
