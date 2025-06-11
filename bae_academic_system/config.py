import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/academic.db")
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    UI_HOST = os.getenv("UI_HOST", "0.0.0.0")
    UI_PORT = int(os.getenv("UI_PORT", "8501"))
    
    # BAE-specific configuration
    DOMAIN_ENTITY_FOCUS = True
    SEMANTIC_COHERENCE_VALIDATION = True
    BUSINESS_VOCABULARY_PRESERVATION = True 