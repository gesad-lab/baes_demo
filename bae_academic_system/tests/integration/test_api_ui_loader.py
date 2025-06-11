# Provide a lightweight stub for fastapi if not installed in the test environment
import sys
from types import ModuleType
try:
    import fastapi  # type: ignore
except ModuleNotFoundError:
    fake_fastapi = ModuleType("fastapi")

    class _StubRoute:
        def __init__(self, path: str):
            self.path = path

    class APIRouter:  # type: ignore
        def __init__(self):
            self.routes = []

        def get(self, path):
            def decorator(func):
                self.routes.append(_StubRoute(path))
                return func
            return decorator

    class FastAPI:  # type: ignore
        def __init__(self, *args, **kwargs):
            self.routes = []

        def include_router(self, router, prefix=""):
            for route in getattr(router, "routes", []):
                self.routes.append(_StubRoute(prefix + route.path))

    fake_fastapi.APIRouter = APIRouter
    fake_fastapi.FastAPI = FastAPI
    sys.modules["fastapi"] = fake_fastapi

import os
from pathlib import Path
from importlib import reload

import pytest


@pytest.mark.integration
class TestApiAndUiLoader:
    def _create_dummy_route_module(self):
        routes_dir = Path(__file__).resolve().parent.parent.parent / "generated" / "routes"
        routes_dir.mkdir(parents=True, exist_ok=True)
        module_path = routes_dir / "testentity_routes.py"
        module_code = (
            "from fastapi import APIRouter\n\n"
            "router = APIRouter()\n\n"
            "@router.get('/dummy')\n"
            "def dummy():\n"
            "    return {'hello': 'world'}\n"
        )
        module_path.write_text(module_code)
        return module_path

    def _create_dummy_ui_module(self):
        ui_dir = Path(__file__).resolve().parent.parent.parent / "generated" / "ui"
        ui_dir.mkdir(parents=True, exist_ok=True)
        ui_path = ui_dir / "testentity_ui.py"
        ui_code = """\nimport streamlit as st\n\n
def render():\n    st.write('Dummy UI')\n"""
        ui_path.write_text(ui_code)
        return ui_path

    def test_api_route_loading(self):
        # Arrange: create dummy route module before importing api.main
        module_path = self._create_dummy_route_module()

        # Act: import (or reload) api.main
        from api import main as api_main
        reload(api_main)  # force re-scan of routes
        app = api_main.app

        # Assert: path should include /api/dummy
        paths = {route.path for route in app.routes}
        assert "/api/dummy" in paths

    def test_ui_loader(self):
        # Arrange: create dummy UI module
        ui_path = self._create_dummy_ui_module()

        from ui import app as ui_app
        reload(ui_app)  # reload to clear cache
        modules = ui_app.discover_ui_modules()
        names = [name for name, _ in modules]
        assert "Testentity" in names 