import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/baes_system.db")

    # Test Environment Detection
    IS_TEST_ENVIRONMENT = (
        "pytest" in sys.modules
        or "PYTEST_CURRENT_TEST" in os.environ
        or any("test" in arg.lower() for arg in sys.argv)
    )

    # Server Configuration - Centralized Port Management
    API_HOST = os.getenv("API_HOST", "127.0.0.1")  # nosec B104
    API_PORT = int(os.getenv("API_PORT", "8100"))  # Updated to match realworld tests
    UI_HOST = os.getenv("UI_HOST", "127.0.0.1")  # nosec B104
    UI_PORT = int(os.getenv("UI_PORT", "8600"))  # Updated to match realworld tests

    # Realworld Testing Ports (for consistency)
    REALWORLD_FASTAPI_PORT = int(os.getenv("REALWORLD_FASTAPI_PORT", str(API_PORT)))
    REALWORLD_STREAMLIT_PORT = int(os.getenv("REALWORLD_STREAMLIT_PORT", str(UI_PORT)))

    # URL Builders for consistent endpoint generation
    @classmethod
    def get_api_base_url(cls) -> str:
        """Get the base API URL"""
        return f"http://{cls.API_HOST}:{cls.API_PORT}"

    @classmethod
    def get_api_endpoint_url(cls, entity: str = "students") -> str:
        """Get the API endpoint URL for a specific entity"""
        return f"{cls.get_api_base_url()}/api/{entity}/"

    @classmethod
    def get_ui_base_url(cls) -> str:
        """Get the base UI URL"""
        return f"http://{cls.UI_HOST}:{cls.UI_PORT}"

    # BAE-specific configuration
    DOMAIN_ENTITY_FOCUS = True
    SEMANTIC_COHERENCE_VALIDATION = True
    BUSINESS_VOCABULARY_PRESERVATION = True

    # BAE System Retry Configuration
    BAE_MAX_RETRIES = int(os.getenv("BAE_MAX_RETRIES", "3"))

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
            # config.py is in the project root, so we use its parent directory
            bae_project_root = Path(__file__).resolve().parent
            return bae_project_root / managed_path
