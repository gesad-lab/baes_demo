from fastapi import FastAPI
import importlib.util
import glob
import os
from pathlib import Path

from config import Config

app = FastAPI(title="BAE Academic System API", version="0.1.0")


def _load_generated_routes():
    """Dynamically discover and import generated route modules, then include their routers under /api namespace."""
    routes_path = Path(__file__).resolve().parent.parent / "generated" / "routes"
    for file_path in glob.glob(str(routes_path / "*_routes.py")):
        module_name = Path(file_path).stem  # e.g. student_routes
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            router = getattr(module, "router", None)
            if router:
                app.include_router(router, prefix="/api")


# Load routes at import time
_load_generated_routes()


def main():
    """CLI entry-point -> starts Uvicorn using config from .env / Config class."""
    import uvicorn

    host = Config.API_HOST
    port = Config.API_PORT
    print(f"🚀 Starting FastAPI server on http://{host}:{port} (routes prefixed with /api)")
    uvicorn.run("bae_academic_system.api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main() 