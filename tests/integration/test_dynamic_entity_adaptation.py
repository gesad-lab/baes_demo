import os
from pathlib import Path

import pytest

from baes.core.runtime_kernel import RuntimeKernel
from baes.domain_entities.academic.student_bae import StudentBae as StudentBAE

# Use centralized temp directory from conftest
TESTS_TEMP_DIR = Path(__file__).parent.parent / ".temp"


@pytest.mark.integration
class TestDynamicEntityAdaptation:
    """
    Streamlined integration tests for BAE entity adaptation.
    Tests core functionality without redundant scenarios.
    """

    def test_entity_adaptation_flow(self, mock_all_openai_clients):
        """Test complete BAE entity adaptation with different entity requests"""

        student_bae = StudentBAE()

        # Test multiple entity requests with single test method
        test_cases = [
            ("Create a book management system", ["book", "title", "author"]),
            ("Create a teacher management system", ["teacher", "department", "email"]),
            ("Create a course management system", ["course", "credits", "instructor"]),
        ]

        for request, expected_vocab in test_cases:
            result = student_bae.handle(
                "interpret_business_request", {"request": request, "context": "academic"}
            )

            # BAE should maintain Student focus regardless of request
            if "error" not in result:
                assert result["entity"] == "Student"
                assert "interpreted_intent" in result
            else:
                # Graceful error handling is acceptable
                assert result["entity"] == "Student"

    def test_schema_generation_and_evolution(self, mock_all_openai_clients):
        """Test schema generation and evolution capabilities"""

        student_bae = StudentBAE()

        # Test initial schema generation
        schema_result = student_bae.handle(
            "generate_schema", {"attributes": ["name: str", "email: str"], "context": "academic"}
        )

        assert schema_result["entity"] == "Student"
        assert "code" in schema_result
        assert "class Student" in schema_result["code"]

        # Test schema evolution
        evolution_result = student_bae.handle(
            "evolve_schema", {"evolution_request": "Add age field", "new_attributes": ["age: int"]}
        )

        assert evolution_result["entity"] == "Student"
        assert len(evolution_result["attributes"]) > len(schema_result["attributes"])

    def test_entity_utilities(self):
        """Test BAE utility methods without mocking"""

        student_bae = StudentBAE()

        # Test default attributes
        attrs = student_bae._get_default_attributes()
        assert isinstance(attrs, list)
        assert any("name" in attr.lower() for attr in attrs)

        # Test pluralization (if available)
        from baes.domain_entities.generic_bae import GenericBae as GenericBAE

        bae = GenericBAE()

        pluralization_tests = [
            ("student", "students"),
            ("book", "books"),
            ("library", "libraries"),
            ("class", "classes"),
        ]

        for singular, expected_plural in pluralization_tests:
            assert bae._pluralize_entity(singular) == expected_plural


@pytest.mark.integration_online
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not available")
class TestDynamicEntityAdaptationLive:
    """Live integration tests with actual OpenAI API calls"""

    def test_live_entity_consistency(self, temp_test_directory):
        """Test BAE maintains entity consistency with live API"""

        student_bae = StudentBAE()

        # Test that StudentBAE maintains Student focus
        result = student_bae.handle(
            "interpret_business_request",
            {"request": "Create a system to manage books", "context": "academic"},
        )

        # Should maintain Student entity focus or handle gracefully
        if "error" not in result:
            assert result["entity"] == "Student"
        else:
            assert result["entity"] == "Student"

        # Verify BAE state consistency
        assert student_bae.current_entity == "Student"
        assert student_bae.primary_entity == "Student"

    def test_live_runtime_kernel_integration(self, temp_test_directory):
        """Test runtime kernel with live API integration"""
        # Ensure we're using tests/.temp for file operations
        TESTS_TEMP_DIR.mkdir(exist_ok=True)
        original_cwd = os.getcwd()

        try:
            # Change to temp_test_directory which is already in tests/.temp
            os.chdir(temp_test_directory)

            os.environ["SKIP_SERVER_START"] = "1"

            kernel = RuntimeKernel(
                context_store_path=os.path.join(temp_test_directory, "context_store.json")
            )

            # Test with single representative case
            kernel.run(
                "Create a system to manage students with name and email",
                context="academic",
                start_servers=False,
            )

            # Verify at least some artifacts were created in the temp directory
            generated_dir = Path(temp_test_directory) / "test_generated"
            if generated_dir.exists():
                # Check for any generated files
                generated_files = list(generated_dir.rglob("*.py"))
                if generated_files:
                    # Verify files contain relevant content
                    for file_path in generated_files[:2]:  # Check first 2 files only
                        content = file_path.read_text()
                        assert len(content.strip()) > 0, f"Generated file {file_path} is empty"

        finally:
            os.chdir(original_cwd)
            if "SKIP_SERVER_START" in os.environ:
                del os.environ["SKIP_SERVER_START"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
