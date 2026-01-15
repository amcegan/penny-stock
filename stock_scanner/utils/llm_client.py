from langchain_google_genai import ChatGoogleGenerativeAI
from stock_scanner.config import config

def get_llm():
    """Returns the configured Gemini Flash LLM instance."""
    if not config.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set")
        
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.0, # Low temperature for factual tasks
        google_api_key=config.GOOGLE_API_KEY,
        max_retries=3
    )
