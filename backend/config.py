import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Config
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    PROCESS_PDF_ENDPOINT = f"{API_BASE_URL}/process-pdf"
    WS_URL = os.getenv("WS_URL", "ws://localhost:8000/ws/realtime-updates")
    
    # LLM Config
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-groq-api-key")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Google Slides Config
    TEMPLATE_PRESENTATION_ID = os.getenv('TEMPLATE_PRESENTATION_ID')
    DELETE_TEST_PRESENTATIONS = os.getenv("DELETE_TEST_PRESENTATIONS", "True").lower() == "true"
    SLIDES_DEBUG_MODE = os.getenv("SLIDES_DEBUG_MODE", "True").lower() == "true"
    
    # Use absolute path for local development and relative path for production
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CREDENTIALS_RELATIVE_PATH = os.path.join("backend", ".credentials", "credentials.json")
    GOOGLE_CREDENTIALS_JSON = os.getenv(
        "GOOGLE_CREDENTIALS_JSON", 
        os.path.join(BASE_DIR, CREDENTIALS_RELATIVE_PATH)
    )