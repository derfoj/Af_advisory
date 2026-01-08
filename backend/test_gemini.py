import sys
import os
# Adjust path to include src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_to_sql.llm_provider import LLMProvider
from langchain_core.messages import HumanMessage

def test_gemini():
    try:
        print("Testing Gemini integration...")
        llm = LLMProvider.get_llm(provider="gemini", model_name="gemini-2.0-flash-exp")
        print(f"Provider obtained: {type(llm).__name__}")
        
        # Simple invocation
        response = llm.invoke([HumanMessage(content="Hello, are you working?")])
        print(f"Response: {response.content}")
        print("Gemini integration successful!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_gemini()
