"""Integration tests for API and UI loader functionality."""

from pathlib import Path

import pytest


@pytest.mark.integration
class TestApiAndUiLoader:
    def teardown_method(self):
        """Cleanup test generated directories"""
        import shutil

        test_generated_dir = Path("tests") / "test_generated"
        if test_generated_dir.exists():
            shutil.rmtree(test_generated_dir, ignore_errors=True)

    @pytest.mark.skip(reason="api module removed - now handled by managed system")
    def test_api_route_loading(self):
        # This test is no longer relevant since api/ directory was moved to managed system
        pass

    @pytest.mark.skip(reason="ui module removed - now handled by managed system")
    def test_ui_loader(self):
        # This test is no longer relevant since ui/ directory was moved to managed system
        pass
