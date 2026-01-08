import sys
import os
# Adjust path to include src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_to_sql.llm_provider import LLMProvider
from langchain_core.messages import HumanMessage

def test_groq():
    try:
        print("Testing Groq integration...")
        llm = LLMProvider.get_llm()
        print(f"Provider obtained: {type(llm).__name__}")
        
        # Simple invocation
        response = llm.invoke([HumanMessage(content="Hello, are you working?")])
        print(f"Response: {response.content}")
        print("Groq integration successful!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_groq()
