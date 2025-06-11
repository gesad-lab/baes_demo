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
    def teardown_method(self):
        """Cleanup test generated directories"""
        import shutil
        test_generated_dir = Path("tests") / "test_generated"
        if test_generated_dir.exists():
            shutil.rmtree(test_generated_dir, ignore_errors=True)
    def _create_dummy_route_module(self):
        # Create test route module in tests directory
        test_routes_dir = Path("tests") / "test_generated" / "routes"
        test_routes_dir.mkdir(parents=True, exist_ok=True)
        module_path = test_routes_dir / "testentity_routes.py"
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
        # Create test UI module in tests directory
        test_ui_dir = Path("tests") / "test_generated" / "ui"
        test_ui_dir.mkdir(parents=True, exist_ok=True)
        ui_path = test_ui_dir / "testentity_ui.py"
        ui_code = """\nimport streamlit as st\n\n
def render():\n    st.write('Dummy UI')\n"""
        ui_path.write_text(ui_code)
        return ui_path

    @pytest.mark.skip(reason="api module removed - now handled by managed system")
    def test_api_route_loading(self):
        # This test is no longer relevant since api/ directory was moved to managed system
        pass

    @pytest.mark.skip(reason="ui module removed - now handled by managed system")
    def test_ui_loader(self):
        # This test is no longer relevant since ui/ directory was moved to managed system
        pass 