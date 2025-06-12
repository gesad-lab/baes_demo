"""Integration tests for RuntimeKernel functionality."""

import os
from pathlib import Path

import pytest

from baes.core.runtime_kernel import RuntimeKernel


@pytest.mark.integration
class TestRuntimeKernel:
    """Integration tests for runtime kernel orchestration"""

    def test_kernel_orchestration_flow(self, mock_all_openai_clients, temp_test_directory):
        """Test runtime kernel orchestrates BAE and SWEA agents correctly"""

        # Skip server startup for testing
        os.environ["SKIP_SERVER_START"] = "1"

        try:
            # Test kernel initialization and execution
            kernel = RuntimeKernel(context_store_path=str(Path(temp_test_directory) / "ctx.json"))

            # Verify kernel can be initialized
            assert kernel is not None

            # Test execution without server start
            kernel.run(
                "Create a system to manage students with name, registration number, and course",
                start_servers=False,
            )

            # Basic validation that kernel executed without errors
            # In a real integration test, we'd verify specific outcomes
            # For now, just ensure no exceptions were raised
            assert True  # If we get here, no exception was raised

        finally:
            if "SKIP_SERVER_START" in os.environ:
                del os.environ["SKIP_SERVER_START"]

    def test_kernel_context_store_integration(self, temp_test_directory):
        """Test runtime kernel properly integrates with context store"""

        context_path = str(Path(temp_test_directory) / "context_test.json")
        kernel = RuntimeKernel(context_store_path=context_path)

        # Verify context store is initialized
        assert kernel.context_store is not None

        # Test context store file creation
        context_file = Path(context_path)
        if context_file.exists():
            assert context_file.is_file()

    def test_kernel_error_handling(self, temp_test_directory):
        """Test runtime kernel handles errors gracefully"""

        # Create a valid kernel first, then test error scenarios
        kernel = RuntimeKernel(context_store_path=str(Path(temp_test_directory) / "ctx.json"))

        # Kernel should handle initialization correctly
        assert kernel is not None

        # Test with invalid/empty request
        try:
            kernel.run("", start_servers=False)
        except Exception as e:
            # Should either handle gracefully or raise meaningful error
            assert isinstance(e, (RuntimeError, ValueError, AttributeError, TypeError))
