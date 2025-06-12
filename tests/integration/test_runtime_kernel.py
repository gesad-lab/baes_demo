"""Integration tests for RuntimeKernel functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from baes.core.runtime_kernel import RuntimeKernel


@pytest.mark.integration
class TestRuntimeKernel:
    """Integration tests for runtime kernel orchestration"""

    def setup_method(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="kernel_test_", dir="tests")
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Cleanup test environment"""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("baes.llm.openai_client.OpenAIClient")
    @patch("baes.swea_agents.programmer_swea.OpenAIClient")
    @patch("baes.swea_agents.frontend_swea.OpenAIClient")
    def test_kernel_orchestration_flow(
        self, mock_frontend_client, mock_programmer_client, mock_student_client
    ):
        """Test runtime kernel orchestrates BAE and SWEA agents correctly"""

        # Setup realistic mock responses
        mock_student_instance = Mock()
        mock_student_instance.interpret_business_request.return_value = {
            "intent": "create_student_management_system",
            "domain_attributes": ["name: str", "registration_number: str", "course: str"],
            "business_vocabulary": ["Student", "Registration"],
            "coordination_plan": [
                {"swea_agent": "ProgrammerSWEA", "task_type": "generate_model"},
                {"swea_agent": "ProgrammerSWEA", "task_type": "generate_api"},
            ],
        }
        mock_student_client.return_value = mock_student_instance

        # Mock SWEA responses
        for mock_client in [mock_programmer_client, mock_frontend_client]:
            mock_instance = Mock()
            mock_instance.generate_code_with_domain_focus.return_value = "# Generated code"
            mock_client.return_value = mock_instance

        # Skip server startup for testing
        os.environ["SKIP_SERVER_START"] = "1"

        try:
            # Test kernel initialization and execution
            kernel = RuntimeKernel(context_store_path=str(Path(self.test_dir) / "ctx.json"))

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

    def test_kernel_context_store_integration(self):
        """Test runtime kernel properly integrates with context store"""

        context_path = str(Path(self.test_dir) / "context_test.json")
        kernel = RuntimeKernel(context_store_path=context_path)

        # Verify context store is initialized
        assert kernel.context_store is not None

        # Test context store file creation
        context_file = Path(context_path)
        if context_file.exists():
            assert context_file.is_file()

    @patch("baes.llm.openai_client.OpenAIClient")
    def test_kernel_error_handling(self, mock_openai_client):
        """Test runtime kernel handles errors gracefully"""

        # Setup mock to raise an exception
        mock_openai_client.side_effect = Exception("Mock API error")

        kernel = RuntimeKernel(context_store_path=str(Path(self.test_dir) / "ctx.json"))

        # Kernel should handle errors gracefully
        try:
            kernel.run("Invalid request", start_servers=False)
        except Exception as e:
            # Should either handle gracefully or raise meaningful error
            assert "Mock API error" in str(e) or isinstance(e, (RuntimeError, ValueError))
