import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/academic.db")
    # Use localhost for development, override with env var for production
    API_HOST = os.getenv("API_HOST", "127.0.0.1")  # nosec B104
    API_PORT = int(os.getenv("API_PORT", "8000"))
    UI_HOST = os.getenv("UI_HOST", "127.0.0.1")  # nosec B104
    UI_PORT = int(os.getenv("UI_PORT", "8501"))

    # BAE-specific configuration
    DOMAIN_ENTITY_FOCUS = True
    SEMANTIC_COHERENCE_VALIDATION = True
    BUSINESS_VOCABULARY_PRESERVATION = True

    # Managed System Configuration
    @classmethod
    def get_managed_system_path(cls) -> Path:
        """Get the managed system path, supporting both absolute and relative paths."""
        managed_path = os.getenv("MANAGED_SYSTEM_PATH", "managed_system")

        if os.path.isabs(managed_path):
            # Absolute path - use as is
            return Path(managed_path)
        else:
            # Relative path - relative to BAE project root
            bae_project_root = Path(__file__).resolve().parent.parent
            return bae_project_root / managed_path
