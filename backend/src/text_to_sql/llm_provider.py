import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from config_loader import GLOBAL_CONFIG

load_dotenv()

class LLMProvider:
    @staticmethod
    def get_llm(model_name: str = None):
        settings = GLOBAL_CONFIG.get('settings', {})
        provider = settings.get('active_provider', 'openai')
        temperature = settings.get('temperature', 0)
        max_retries = settings.get('max_retries', 3)

        if provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables.")
            
            # Use provided model_name or get from config
            model = model_name or GLOBAL_CONFIG.get('providers', {}).get('openai', {}).get('model_name', 'gpt-3.5-turbo')
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                max_retries=max_retries,
                api_key=api_key
            )
        
        elif provider == 'gemini':
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables.")
            
            # Use provided model_name or get from config
            model = model_name or GLOBAL_CONFIG.get('providers', {}).get('gemini', {}).get('model_name', 'gemini-pro')
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                max_retries=max_retries,
                google_api_key=api_key
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")