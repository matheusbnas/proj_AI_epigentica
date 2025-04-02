# config.py
import os

class Config:
    # API Config
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    PROCESS_PDF_ENDPOINT = f"{API_BASE_URL}/process-pdf"
    WS_URL = os.getenv("WS_URL", "ws://localhost:8000/ws/realtime-updates")
    
    # LLM Config
    LLM_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "your-mistral-api-key")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-groq-api-key")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")