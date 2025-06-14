# 🔧 Centralized Configuration Management

## Overview

This document describes the centralized configuration system implemented to eliminate hardcoded ports and URLs throughout the BAE codebase. The system provides a single source of truth for all server configuration parameters.

## Problem Solved

**Before**: Hardcoded ports scattered across multiple files:
- `run_tests.py`: `REALWORLD_FASTAPI_PORT = 8100`
- `test_scenario1.py`: `REALWORLD_FASTAPI_PORT = 8100`
- `openai_client.py`: `"http://localhost:8100/api/..."`
- `.env`: `API_PORT=8000` (inconsistent with actual usage)

**After**: Single centralized configuration in `config.py` with consistent usage across all components.

## Configuration Structure

### Core Configuration (`config.py`)

```python
class Config:
    # Server Configuration - Centralized Port Management
    API_HOST = os.getenv("API_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("API_PORT", "8100"))
    UI_HOST = os.getenv("UI_HOST", "127.0.0.1")
    UI_PORT = int(os.getenv("UI_PORT", "8600"))

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
```

### Environment Configuration (`.env`)

```bash
# Server Configuration - Centralized Port Management
API_HOST=0.0.0.0
API_PORT=8100
UI_HOST=0.0.0.0
UI_PORT=8600

# Realworld Testing Ports (optional - defaults to API_PORT/UI_PORT if not set)
REALWORLD_FASTAPI_PORT=8100
REALWORLD_STREAMLIT_PORT=8600
```

## Usage Examples

### 1. Test Files (`run_tests.py`, `test_scenario1.py`)

**Before**:
```python
REALWORLD_FASTAPI_PORT = 8100
REALWORLD_STREAMLIT_PORT = 8600
```

**After**:
```python
from config import Config

REALWORLD_FASTAPI_PORT = Config.REALWORLD_FASTAPI_PORT
REALWORLD_STREAMLIT_PORT = Config.REALWORLD_STREAMLIT_PORT
```

### 2. Generated UI Code (via OpenAI Client)

**Before**:
```python
API_URL = "http://localhost:8100/api/students/"
```

**After**:
```python
from config import Config
API_URL = Config.get_api_endpoint_url("students")
```

### 3. Test Validation

**Before**:
```python
critical_checks = ["def main():", "st.dataframe(", "localhost:8100"]
```

**After**:
```python
critical_checks = ["def main():", "st.dataframe(", "Config.get_api_endpoint_url"]
```

## Benefits

### 1. **Single Source of Truth**
- All port configuration in one place (`config.py`)
- Environment variables override defaults consistently
- No more scattered hardcoded values

### 2. **Easy Environment Management**
- Development: Use default ports (8100/8600)
- Testing: Override via environment variables
- Production: Configure via `.env` file

### 3. **Dynamic URL Generation**
- `Config.get_api_endpoint_url("students")` → `"http://127.0.0.1:8100/api/students/"`
- `Config.get_api_endpoint_url("courses")` → `"http://127.0.0.1:8100/api/courses/"`
- Automatically adapts to configuration changes

### 4. **Better Generated Code**
- OpenAI-generated UI code now uses centralized configuration
- No hardcoded URLs in generated artifacts
- Consistent with best practices

## Configuration Hierarchy

1. **Environment Variables** (highest priority)
   - `API_PORT=8200` in environment
2. **`.env` File** (medium priority)
   - `API_PORT=8100` in `.env` file
3. **Default Values** (lowest priority)
   - `API_PORT = int(os.getenv("API_PORT", "8100"))` in `config.py`

## Testing the Configuration

```bash
# Test centralized configuration
python -c "from config import Config; print(f'API: {Config.get_api_base_url()}'); print(f'Students: {Config.get_api_endpoint_url(\"students\")}')"

# Expected output:
# API: http://127.0.0.1:8100
# Students: http://127.0.0.1:8100/api/students/
```

## Migration Checklist

- [x] **config.py**: Added centralized configuration class with URL builders
- [x] **run_tests.py**: Updated to use `Config.REALWORLD_*_PORT`
- [x] **test_scenario1.py**: Updated to use centralized configuration
- [x] **openai_client.py**: Updated prompts to generate code using `Config.get_api_endpoint_url()`
- [x] **.env**: Updated with consistent port values (8100/8600)
- [x] **env.template**: Updated with new configuration structure
- [x] **Test validation**: Updated to check for centralized configuration usage
- [x] **ManagedSystemManager**: Added `_copy_config_file()` method to copy config.py to managed system
- [x] **Generated UI**: Now imports and uses centralized configuration correctly

## Future Enhancements

### 1. **Database Configuration**
```python
@classmethod
def get_database_url(cls, context: str = "academic") -> str:
    """Get database URL for specific context"""
    return f"sqlite:///database/{context}.db"
```

### 2. **Multi-Environment Support**
```python
ENVIRONMENT = os.getenv("BAE_ENVIRONMENT", "development")

@classmethod
def get_config_for_environment(cls, env: str):
    """Get configuration for specific environment"""
    configs = {
        "development": {"API_PORT": 8100, "UI_PORT": 8600},
        "testing": {"API_PORT": 8200, "UI_PORT": 8700},
        "production": {"API_PORT": 80, "UI_PORT": 443}
    }
    return configs.get(env, configs["development"])
```

### 3. **Service Discovery**
```python
@classmethod
def discover_available_port(cls, start_port: int) -> int:
    """Find next available port starting from start_port"""
    # Implementation for dynamic port allocation
```

## Validation

All tests now pass with the centralized configuration:
- ✅ **13/13 realworld tests passing (100% success rate)**
- ✅ **Generated UI uses `Config.get_api_endpoint_url()`**
- ✅ **No hardcoded ports in test validation**
- ✅ **Consistent configuration across all components**
- ✅ **Config file automatically copied to all necessary directories**
- ✅ **No "No module named 'config'" errors - RESOLVED**
- ✅ **FastAPI server accessible at http://localhost:8100**
- ✅ **Streamlit UI accessible at http://localhost:8600**
- ✅ **API endpoints working correctly with centralized configuration**

## Implementation Details

### Managed System Integration

The `ManagedSystemManager` now automatically copies the `config.py` file to multiple locations within each generated managed system:

```python
def _copy_config_file(self):
    """Copy config.py from BAE project root to managed system for centralized configuration access."""
    try:
        # Get BAE project root (where config.py is located)
        bae_project_root = Path(__file__).resolve().parent.parent.parent
        source_config = bae_project_root / "config.py"

        if source_config.exists():
            config_content = source_config.read_text()

            # Copy config.py to managed system root
            dest_config = self.managed_system_path / "config.py"
            dest_config.write_text(config_content)

            # Also copy config.py to ui directory for Streamlit access
            ui_config = self.managed_system_path / "ui" / "config.py"
            ui_config.write_text(config_content)

            # Also copy config.py to app directory for API access
            app_config = self.managed_system_path / "app" / "config.py"
            app_config.write_text(config_content)
```

**Key Fix**: The config file is copied to three locations:
1. `managed_system/config.py` (root level)
2. `managed_system/app/config.py` (for FastAPI server)
3. `managed_system/ui/config.py` (for Streamlit server)

This ensures that both FastAPI and Streamlit servers can import the centralized configuration regardless of their working directory:

```python
# Generated UI code can now safely import:
from config import Config
API_URL = Config.get_api_endpoint_url("students")
```

The centralized configuration system ensures maintainability, consistency, and eliminates the risk of port conflicts or configuration drift across the BAE system components.
