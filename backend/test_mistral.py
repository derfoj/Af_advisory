import sys
import os
# Adjust path to include src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_to_sql.llm_provider import LLMProvider
from langchain_core.messages import HumanMessage

def test_mistral():
    try:
        print("Testing Mistral integration...")
        llm = LLMProvider.get_llm(provider="mistral", model_name="mistral-large-latest")
        print(f"Provider obtained: {type(llm).__name__}")
        
        # Simple invocation
        response = llm.invoke([HumanMessage(content="Hello, are you working?")])
        print(f"Response: {response.content}")
        print("Mistral integration successful!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mistral()
