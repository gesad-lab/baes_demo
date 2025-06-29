"""
Test Stage 5: Prompt Contextualization with Examples
Validates that all SWEA agent prompts now include comprehensive examples for better LLM guidance.
"""

from pathlib import Path

import pytest


class TestStage5PromptContextualization:
    """Test suite for Stage 5: Prompt Contextualization with Examples"""

    def test_backendswea_prompt_has_examples(self):
        """Test that BackendSWEA prompt includes comprehensive examples"""
        prompt_file = Path("baes/llm/prompts/backend_gen.txt")
        assert prompt_file.exists(), "BackendSWEA prompt file should exist"

        content = prompt_file.read_text()

        # Check for EXAMPLES section
        assert "## EXAMPLES" in content, "BackendSWEA prompt should have EXAMPLES section"

        # Check for Pydantic model example
        assert "### Pydantic Model Example" in content, "Should have Pydantic model example"
        assert "<EntityName>Base(BaseModel)" in content, "Should have entity placeholder in model"
        assert "class <EntityName>Create" in content, "Should have create model example"
        assert "class <EntityName>Update" in content, "Should have update model example"

        # Check for FastAPI endpoint example
        assert "### FastAPI Endpoint Example" in content, "Should have FastAPI endpoint example"
        assert "router = APIRouter" in content, "Should have router setup"
        assert "@router.post" in content, "Should have POST endpoint"
        assert "@router.get" in content, "Should have GET endpoint"
        assert "@router.put" in content, "Should have PUT endpoint"
        assert "@router.delete" in content, "Should have DELETE endpoint"

        # Check for proper placeholders
        assert "<EntityName>" in content, "Should use EntityName placeholder"
        assert "<entity_name_lower>" in content, "Should use entity_name_lower placeholder"

        # Check for task instructions
        assert "## TASK INSTRUCTIONS" in content, "Should have task instructions section"
        assert "BackendSWEA" in content, "Should identify as BackendSWEA"

    def test_frontendswea_prompt_has_examples(self):
        """Test that FrontendSWEA prompt includes comprehensive examples"""
        prompt_file = Path("baes/llm/prompts/frontend_gen.txt")
        assert prompt_file.exists(), "FrontendSWEA prompt file should exist"

        content = prompt_file.read_text()

        # Check for EXAMPLES section
        assert "## EXAMPLES" in content, "FrontendSWEA prompt should have EXAMPLES section"

        # Check for Streamlit main app example
        assert "### Streamlit Main App Example" in content, "Should have Streamlit main app example"
        assert "st.set_page_config" in content, "Should have page configuration"
        assert "def main():" in content, "Should have main function"
        assert "st.sidebar.selectbox" in content, "Should have navigation"
        assert "st.dataframe" in content, "Should have data display"

        # Check for Streamlit component example
        assert "### Streamlit Component Example" in content, "Should have component example"
        assert "def <entity_name_lower>_form" in content, "Should have form component"
        assert "st.form" in content, "Should have form usage"
        assert "st.text_input" in content, "Should have input fields"

        # Check for proper placeholders
        assert "<EntityName>" in content, "Should use EntityName placeholder"
        assert "<entity_name_lower>" in content, "Should use entity_name_lower placeholder"

        # Check for task instructions
        assert "## TASK INSTRUCTIONS" in content, "Should have task instructions section"
        assert "FrontendSWEA" in content, "Should identify as FrontendSWEA"

    def test_databaseswea_prompt_has_examples(self):
        """Test that DatabaseSWEA prompt includes comprehensive examples"""
        prompt_file = Path("baes/llm/prompts/database_gen.txt")
        assert prompt_file.exists(), "DatabaseSWEA prompt file should exist"

        content = prompt_file.read_text()

        # Check for EXAMPLES section
        assert "## EXAMPLES" in content, "DatabaseSWEA prompt should have EXAMPLES section"

        # Check for SQLAlchemy model example
        assert "### SQLAlchemy Model Example" in content, "Should have SQLAlchemy model example"
        assert "class <EntityName>(Base):" in content, "Should have entity model class"
        assert "__tablename__ = '<entity_name_lower>s'" in content, "Should have table name"
        assert "Column(Integer, primary_key=True" in content, "Should have primary key"
        assert "Column(String" in content, "Should have string columns"
        assert "Column(DateTime" in content, "Should have datetime columns"

        # Check for database setup example
        assert "### Database Setup Example" in content, "Should have database setup example"
        assert "def create_database_engine()" in content, "Should have engine creation"
        assert "def get_db()" in content, "Should have database session"
        assert "def init_database()" in content, "Should have database initialization"

        # Check for migration example
        assert "### Database Migration Example" in content, "Should have migration example"
        assert (
            "def migrate_<entity_name_lower>_table()" in content
        ), "Should have migration function"
        assert "ALTER TABLE" in content, "Should have ALTER TABLE statements"

        # Check for repository example
        assert "### Database Utility Functions Example" in content, "Should have repository example"
        assert "class <EntityName>Repository" in content, "Should have repository class"
        assert "def create(" in content, "Should have create method"
        assert "def get_by_id(" in content, "Should have get method"
        assert "def update(" in content, "Should have update method"
        assert "def delete(" in content, "Should have delete method"

        # Check for proper placeholders
        assert "<EntityName>" in content, "Should use EntityName placeholder"
        assert "<entity_name_lower>" in content, "Should use entity_name_lower placeholder"

        # Check for task instructions
        assert "## TASK INSTRUCTIONS" in content, "Should have task instructions section"
        assert "DatabaseSWEA" in content, "Should identify as DatabaseSWEA"

    def test_testswea_prompt_has_examples(self):
        """Test that TestSWEA prompt includes comprehensive examples"""
        prompt_file = Path("baes/llm/prompts/test_gen.txt")
        assert prompt_file.exists(), "TestSWEA prompt file should exist"

        content = prompt_file.read_text()

        # Check for EXAMPLES section
        assert "## EXAMPLES" in content, "TestSWEA prompt should have EXAMPLES section"

        # Check for pytest test suite example
        assert "### Pytest Test Suite Example" in content, "Should have pytest test suite example"
        assert "class Test<EntityName>API:" in content, "Should have API test class"
        assert "def test_create_<entity_name_lower>_success(" in content, "Should have create test"
        assert "def test_get_<entity_name_lower>s_list(" in content, "Should have list test"
        assert "def test_update_<entity_name_lower>_success(" in content, "Should have update test"
        assert "def test_delete_<entity_name_lower>_success(" in content, "Should have delete test"

        # Check for validation tests
        assert "class Test<EntityName>Validation:" in content, "Should have validation test class"
        assert "def test_name_validation(" in content, "Should have name validation test"
        assert "def test_email_validation(" in content, "Should have email validation test"

        # Check for integration tests
        assert "class Test<EntityName>Integration:" in content, "Should have integration test class"
        assert "def test_full_crud_workflow(" in content, "Should have CRUD workflow test"

        # Check for unit test example
        assert "### Unit Test Example" in content, "Should have unit test example"
        assert "class Test<EntityName>Unit:" in content, "Should have unit test class"
        assert "class Test<EntityName>Performance:" in content, "Should have performance test class"

        # Check for fixtures
        assert "@pytest.fixture" in content, "Should have pytest fixtures"
        assert "def sample_<entity_name_lower>_data(" in content, "Should have sample data fixture"
        assert "def created_<entity_name_lower>(" in content, "Should have created entity fixture"

        # Check for proper placeholders
        assert "<EntityName>" in content, "Should use EntityName placeholder"
        assert "<entity_name_lower>" in content, "Should use entity_name_lower placeholder"
        assert "<ENTITY_NAME_UPPER>" in content, "Should use ENTITY_NAME_UPPER placeholder"

        # Check for task instructions
        assert "## TASK INSTRUCTIONS" in content, "Should have task instructions section"
        assert "TestSWEA" in content, "Should identify as TestSWEA"

    def test_techleadswea_prompt_has_examples(self):
        """Test that TechLeadSWEA prompt includes comprehensive examples"""
        prompt_file = Path("baes/llm/prompts/techlead_gen.txt")
        assert prompt_file.exists(), "TechLeadSWEA prompt file should exist"

        content = prompt_file.read_text()

        # Check for EXAMPLES section
        assert "## EXAMPLES" in content, "TechLeadSWEA prompt should have EXAMPLES section"

        # Check for system coordination example
        assert (
            "### System Coordination Example" in content
        ), "Should have system coordination example"
        assert "class <EntityName>SystemCoordinator:" in content, "Should have coordinator class"
        assert "def coordinate_system_generation(" in content, "Should have coordination method"
        assert "def _plan_architecture(" in content, "Should have architecture planning"
        assert "def _create_coordination_plan(" in content, "Should have coordination planning"
        assert "def _define_quality_gates(" in content, "Should have quality gate definition"
        assert "def _assess_risks(" in content, "Should have risk assessment"

        # Check for quality gate management example
        assert (
            "### Quality Gate Management Example" in content
        ), "Should have quality gate management example"
        assert "class <EntityName>QualityManager:" in content, "Should have quality manager class"
        assert "def review_and_approve(" in content, "Should have review and approve method"
        assert (
            "def _assess_component_quality(" in content
        ), "Should have component quality assessment"
        assert "def _assess_integration(" in content, "Should have integration assessment"
        assert "def _assess_performance(" in content, "Should have performance assessment"
        assert "def _assess_security(" in content, "Should have security assessment"
        assert "def _make_approval_decision(" in content, "Should have approval decision"

        # Check for conflict resolution example
        assert (
            "### Conflict Resolution Example" in content
        ), "Should have conflict resolution example"
        assert (
            "class <EntityName>ConflictResolver:" in content
        ), "Should have conflict resolver class"
        assert (
            "def resolve_technical_conflict(" in content
        ), "Should have conflict resolution method"
        assert (
            "def _resolve_dependency_conflict(" in content
        ), "Should have dependency conflict resolution"
        assert "def _resolve_naming_conflict(" in content, "Should have naming conflict resolution"
        assert (
            "def _resolve_architecture_conflict(" in content
        ), "Should have architecture conflict resolution"
        assert (
            "def _resolve_quality_conflict(" in content
        ), "Should have quality conflict resolution"

        # Check for proper placeholders
        assert "<EntityName>" in content, "Should use EntityName placeholder"
        assert "<entity_name_lower>" in content, "Should use entity_name_lower placeholder"

        # Check for task instructions
        assert "## TASK INSTRUCTIONS" in content, "Should have task instructions section"
        assert "TechLeadSWEA" in content, "Should identify as TechLeadSWEA"

    def test_all_prompts_have_consistent_structure(self):
        """Test that all prompts have consistent structure with examples"""
        prompt_files = [
            "baes/llm/prompts/backend_gen.txt",
            "baes/llm/prompts/frontend_gen.txt",
            "baes/llm/prompts/database_gen.txt",
            "baes/llm/prompts/test_gen.txt",
            "baes/llm/prompts/techlead_gen.txt",
        ]

        for prompt_file in prompt_files:
            file_path = Path(prompt_file)
            assert file_path.exists(), f"Prompt file {prompt_file} should exist"

            content = file_path.read_text()

            # Check for consistent structure
            assert "# " in content, f"{prompt_file} should have title comment"
            assert "## EXAMPLES" in content, f"{prompt_file} should have EXAMPLES section"
            assert (
                "## TASK INSTRUCTIONS" in content
            ), f"{prompt_file} should have TASK INSTRUCTIONS section"

            # Check that examples come before task instructions
            examples_pos = content.find("## EXAMPLES")
            instructions_pos = content.find("## TASK INSTRUCTIONS")
            assert (
                examples_pos < instructions_pos
            ), f"{prompt_file} should have EXAMPLES before TASK INSTRUCTIONS"

    def test_examples_use_placeholders_for_reusability(self):
        """Test that examples use placeholders for maximum reusability"""
        prompt_files = [
            "baes/llm/prompts/backend_gen.txt",
            "baes/llm/prompts/frontend_gen.txt",
            "baes/llm/prompts/database_gen.txt",
            "baes/llm/prompts/test_gen.txt",
            "baes/llm/prompts/techlead_gen.txt",
        ]

        for prompt_file in prompt_files:
            file_path = Path(prompt_file)
            content = file_path.read_text()

            # Check for placeholder usage
            assert "<EntityName>" in content, f"{prompt_file} should use <EntityName> placeholder"
            assert (
                "<entity_name_lower>" in content
            ), f"{prompt_file} should use <entity_name_lower> placeholder"

            # Check that examples don't use hardcoded entity names
            hardcoded_entities = ["Student", "Course", "Teacher", "student", "course", "teacher"]
            for entity in hardcoded_entities:
                # Allow some hardcoded references in comments or descriptions, but not in code examples
                if entity in content:
                    # Check if it's in a code block (```python)
                    code_blocks = content.split("```python")
                    for i, block in enumerate(code_blocks[1:], 1):  # Skip first split
                        if "```" in block:
                            code_content = block.split("```")[0]
                            if entity in code_content:
                                # This is acceptable if it's in a comment or string
                                if not (
                                    f"# {entity}" in code_content
                                    or f'"{entity}"' in code_content
                                    or f"'{entity}'" in code_content
                                ):
                                    pytest.fail(
                                        f"{prompt_file} should not use hardcoded entity '{entity}' in code examples"
                                    )

    def test_examples_are_comprehensive_and_detailed(self):
        """Test that examples are comprehensive and provide sufficient detail"""
        prompt_files = [
            "baes/llm/prompts/backend_gen.txt",
            "baes/llm/prompts/frontend_gen.txt",
            "baes/llm/prompts/database_gen.txt",
            "baes/llm/prompts/test_gen.txt",
            "baes/llm/prompts/techlead_gen.txt",
        ]

        for prompt_file in prompt_files:
            file_path = Path(prompt_file)
            content = file_path.read_text()

            # Check that examples section is substantial
            examples_section = content.split("## EXAMPLES")[1].split("## TASK INSTRUCTIONS")[0]
            assert (
                len(examples_section) > 1000
            ), f"{prompt_file} should have substantial examples section"

            # Check for multiple example types
            assert (
                examples_section.count("### ") >= 2
            ), f"{prompt_file} should have multiple example types"

            # Check for code blocks
            assert (
                "```python" in examples_section
            ), f"{prompt_file} should have Python code examples"

    def test_task_instructions_are_clear_and_comprehensive(self):
        """Test that task instructions are clear and comprehensive"""
        prompt_files = [
            "baes/llm/prompts/backend_gen.txt",
            "baes/llm/prompts/frontend_gen.txt",
            "baes/llm/prompts/database_gen.txt",
            "baes/llm/prompts/test_gen.txt",
            "baes/llm/prompts/techlead_gen.txt",
        ]

        for prompt_file in prompt_files:
            file_path = Path(prompt_file)
            content = file_path.read_text()

            # Check for clear responsibilities
            assert (
                "### RESPONSIBILITIES:" in content
            ), f"{prompt_file} should have clear responsibilities"

            # Check for requirements
            assert "### REQUIREMENTS:" in content, f"{prompt_file} should have requirements"

            # Check for output format
            assert "### OUTPUT FORMAT:" in content, f"{prompt_file} should have output format"

            # Check for important notes
            assert "### IMPORTANT NOTES:" in content, f"{prompt_file} should have important notes"

            # Check that instructions reference examples
            assert (
                "examples above" in content.lower()
            ), f"{prompt_file} should reference examples in instructions"

    def test_prompts_include_business_vocabulary_focus(self):
        """Test that prompts maintain focus on business vocabulary and domain context"""
        prompt_files = [
            "baes/llm/prompts/backend_gen.txt",
            "baes/llm/prompts/frontend_gen.txt",
            "baes/llm/prompts/database_gen.txt",
            "baes/llm/prompts/test_gen.txt",
            "baes/llm/prompts/techlead_gen.txt",
        ]

        for prompt_file in prompt_files:
            file_path = Path(prompt_file)
            content = file_path.read_text()

            # Check for business vocabulary focus
            business_terms = ["business", "domain", "semantic", "vocabulary", "entity"]
            found_terms = [term for term in business_terms if term in content.lower()]
            assert (
                len(found_terms) >= 2
            ), f"{prompt_file} should focus on business vocabulary and domain context"

    def test_stage5_implementation_completeness(self):
        """Test that Stage 5 implementation is complete and comprehensive"""
        # Check that all required prompt files exist
        required_files = [
            "baes/llm/prompts/backend_gen.txt",
            "baes/llm/prompts/frontend_gen.txt",
            "baes/llm/prompts/database_gen.txt",
            "baes/llm/prompts/test_gen.txt",
            "baes/llm/prompts/techlead_gen.txt",
        ]

        for file_path in required_files:
            assert Path(file_path).exists(), f"Required prompt file {file_path} should exist"

        # Check that all prompts have been updated with examples
        total_examples_sections = 0
        for file_path in required_files:
            content = Path(file_path).read_text()
            if "## EXAMPLES" in content:
                total_examples_sections += 1

        assert total_examples_sections == len(
            required_files
        ), "All prompt files should have EXAMPLES sections"

        # Check that examples are substantial (not just placeholders)
        total_code_blocks = 0
        for file_path in required_files:
            content = Path(file_path).read_text()
            total_code_blocks += content.count("```python")

        assert total_code_blocks >= 10, "Should have substantial code examples across all prompts"

        print("✅ Stage 5 Implementation Complete:")
        print(f"   - {len(required_files)} prompt files updated")
        print(f"   - {total_examples_sections} examples sections added")
        print(f"   - {total_code_blocks} code examples provided")
        print("   - All SWEA agents now have comprehensive examples")
        print("   - Placeholder-based examples for maximum reusability")
        print("   - Business vocabulary focus maintained")
        print("   - Clear task instructions with example references")
