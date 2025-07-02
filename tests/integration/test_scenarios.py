"""
Integration Tests for PoC Scenarios: BAE System Generation and Evolution

Tests all three core BAE capabilities according to Proof of Concept:
- Scenario 1: Initial System Generation
- Scenario 2: Runtime Evolution with data preservation
- Scenario 3: Multi-Entity System with relationship creation

Expected workflows:
Scenario 1: Natural language -> Entity recognition -> BAE -> SWEA coordination -> Generated system
Scenario 2: Evolution request -> BAE -> SWEA migration -> System evolution without data loss
Scenario 3: Multi-entity request -> BAEs -> SWEA coordination -> System with relational schema

IMPORTANT ARCHITECTURAL NOTE:
These tests validate the BAE framework's unified entity-route pattern where BackendSWEA 
intentionally embeds Pydantic models within FastAPI route files rather than generating 
separate model files. This design choice:
- Follows DRY principles (no duplication)
- Maintains domain entity cohesion (all entity logic in one place)
- Simplifies SWEA generation process
- Preserves autonomous entity focus (self-contained artifacts)
"""

import sqlite3
import time
from pathlib import Path
import os
import subprocess
import shutil
import tempfile
from typing import Dict, List, Any, Optional

import pytest
import requests


class BaseScenarioTest:
    """
    Base class with shared functionality for PoC scenario tests.
    
    Validates the BAE framework's unified entity-route architectural pattern:
    - BackendSWEA generates unified route files containing both Pydantic models and FastAPI endpoints.
    - Eliminates code duplication between separate model and route files (DRY principle).
    - Maintains domain entity autonomy through self-contained artifacts.
    - Preserves semantic coherence between business vocabulary and technical implementation.
    """
    
    def __init__(self):
        self.managed_system_dir: Optional[Path] = None
        self.generation_result: Optional[Dict[str, Any]] = None
        self.api_process: Optional[subprocess.Popen] = None
        
    def setup_test_environment(self, temp_dir: Path) -> Path:
        """Setup isolated test environment."""
        managed_system_path = temp_dir / "managed_system"
        os.environ["MANAGED_SYSTEM_PATH"] = str(managed_system_path)
        
        from config import Config
        if not hasattr(self, '_original_get_managed_system_path'):
            self._original_get_managed_system_path = Config.get_managed_system_path
        
        Config.get_managed_system_path = classmethod(lambda cls: managed_system_path)
        
        actual_path = Config.get_managed_system_path()
        print(f"🔍 Test Environment Setup:")
        print(f"   📁 Expected path: {managed_system_path}")
        print(f"   📁 Actual path: {actual_path}")
        assert actual_path == managed_system_path, f"Path mismatch: expected {managed_system_path}, got {actual_path}"
        
        self.managed_system_dir = managed_system_path
        return managed_system_path
        
    def cleanup_test_environment(self):
        """Clean up test environment."""
        if hasattr(self, '_original_get_managed_system_path'):
            from config import Config
            Config.get_managed_system_path = self._original_get_managed_system_path
            delattr(self, '_original_get_managed_system_path')
        
        if "MANAGED_SYSTEM_PATH" in os.environ:
            del os.environ["MANAGED_SYSTEM_PATH"]
        
    def process_natural_language_request(self, request: str, context: str = "academic") -> Dict[str, Any]:
        """Process natural language request through Enhanced Runtime Kernel."""
        print(f"\n🎯 Processing request: {request}")
        
        from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel
        kernel = EnhancedRuntimeKernel()
        
        kernel_path = kernel.managed_system_manager.managed_system_path
        print(f"🔍 Kernel using managed system path: {kernel_path}")
        assert kernel_path == self.managed_system_dir, f"Kernel path mismatch: expected {self.managed_system_dir}, got {kernel_path}"
        
        start_time = time.time()
        result = kernel.process_natural_language_request(
            request=request,
            context=context,
            start_servers=False
        )
        result["execution_time"] = time.time() - start_time
        
        return result
        
    def validate_generation_result(self, result: Dict[str, Any], expected_entity: str) -> None:
        """Validate basic generation result structure."""
        assert result.get("success", False), f"System generation failed: {result.get('message', 'Unknown error')}"
        detected_entity = result.get("entity", "")
        assert detected_entity.lower() == expected_entity.lower(), f"Expected {expected_entity} entity, got {detected_entity}"
        assert result.get("interpretation", {}), "Missing BAE interpretation"
        assert result.get("execution_results", []), "No execution results returned"
        successful_tasks = [task for task in result.get("execution_results", []) if task.get("success", False)]
        assert len(successful_tasks) > 0, "No successful tasks in execution results"
        
    def validate_file_structure(self, expected_entities: List[str]) -> List[Path]:
        """Validate generated file structure and syntax for multiple entities."""
        print(f"\n📁 Validating generated files in: {self.managed_system_dir}")
        assert self.managed_system_dir.exists(), f"Managed system directory not created: {self.managed_system_dir}"
        
        for dir_name in ["app", "ui"]:
            assert (self.managed_system_dir / dir_name).exists(), f"Expected directory not found: {dir_name}"
        
        app_dir = self.managed_system_dir / "app"
        for item in ["routes", "database", "main.py"]:
            assert (app_dir / item).exists(), f"Expected app item not found: {item}"
            
        routes_dir = app_dir / "routes"
        for entity in expected_entities:
            route_file = routes_dir / f"{entity.lower()}_routes.py"
            assert route_file.exists(), f"Route file for entity '{entity}' not found at {route_file}"

        python_files = list(self.managed_system_dir.glob("**/*.py"))
        assert len(python_files) >= 3, f"Expected at least 3 Python files, found {len(python_files)}"
        
        for py_file in python_files:
            try:
                compile(py_file.read_text(), str(py_file), "exec")
            except SyntaxError as e:
                pytest.fail(f"Invalid Python syntax in {py_file}: {e}")
        
        print(f"✅ All {len(python_files)} Python files have valid syntax")
        self.validate_unified_route_files(expected_entities)
        return python_files
        
    def validate_unified_route_files(self, expected_entities: List[str]) -> None:
        """Validate that route files for all expected entities exist and follow the unified pattern."""
        print(f"\n🔗 Validating unified entity-route pattern for entities: {expected_entities}")
        routes_dir = self.managed_system_dir / "app" / "routes"
        
        for entity in expected_entities:
            entity_name = entity.capitalize()
            route_file = routes_dir / f"{entity.lower()}_routes.py"
            assert route_file.exists(), f"Route file for entity '{entity_name}' not found."
            
            code = route_file.read_text()
            assert "from pydantic import BaseModel" in code, f"Missing Pydantic import in {route_file}"
            model_patterns = [f"class {entity_name}", f"class {entity_name}Create", f"class {entity_name}Update"]
            assert any(p in code for p in model_patterns), f"Missing Pydantic model for {entity_name} in {route_file}"
            assert "from fastapi import APIRouter" in code and "router = APIRouter" in code, f"Missing FastAPI router in {route_file}"
            for pattern in ["@router.post", "@router.get", "@router.put", "@router.delete"]:
                assert pattern in code, f"Missing CRUD endpoint {pattern} in {route_file}"
            print(f"✅ Unified entity-route pattern validated for: {route_file.name}")

    def validate_database_schema(self, table_name: str, expected_columns: List[str]) -> List[tuple]:
        """Validate the schema for a specific table in the database."""
        db_path = self.managed_system_dir / "app" / "database" / "baes_system.db"
        print(f"\n🗄️ Validating schema for table '{table_name}' at: {db_path}")
        assert db_path.exists() and db_path.stat().st_size > 0, "Database file not created or is empty"
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            assert cursor.fetchone(), f"Table '{table_name}' not created."
            
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            column_names = [col[1].lower() for col in columns]
            for expected_col in expected_columns:
                assert expected_col.lower() in column_names, f"Expected column '{expected_col}' not found in '{table_name}'. Available: {column_names}"
            
            print(f"✅ Schema for '{table_name}' validated: {len(columns)} columns")
            print(f"📋 Columns: {column_names}")
            return columns
        finally:
            conn.close()

    def validate_data_preservation(self, table_name: str, expected_count: int):
        """Validate that data is preserved in a table after an operation."""
        db_path = self.managed_system_dir / "app" / "database" / "baes_system.db"
        print(f"\n💾 Validating data preservation for table '{table_name}'...")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            assert count == expected_count, f"Data preservation failed! Expected {expected_count} records in '{table_name}', found {count}."
            print(f"✅ Data preservation validated: {count}/{expected_count} records found.")
        finally:
            conn.close()

    def validate_database_relationship(self, from_table: str, to_table: str, fk_column: str):
        """Validate that a foreign key relationship exists between two tables."""
        db_path = self.managed_system_dir / "app" / "database" / "baes_system.db"
        print(f"\n🔗 Validating relationship: {from_table}({fk_column}) -> {to_table}(id)")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        try:
            cursor.execute(f"PRAGMA foreign_key_list({from_table});")
            fks = cursor.fetchall()
            assert fks, f"No foreign keys found on table '{from_table}'."
            
            fk_found = any(fk[2] == to_table and fk[3] == fk_column for fk in fks)
            assert fk_found, f"Foreign key from '{from_table}.{fk_column}' to '{to_table}' not found."
            print(f"✅ Foreign key relationship validated successfully.")
        finally:
            conn.close()

    def start_api_server(self, port: int = 8100) -> subprocess.Popen:
        """Start FastAPI server for testing."""
        print(f"\n🔌 Starting API server on port {port}...")
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=self.managed_system_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(5)
        self.api_process = process
        return process

    def cleanup_api_server(self) -> None:
        """Cleanup API server process."""
        if self.api_process:
            self.api_process.terminate()
            self.api_process.wait()
            self.api_process = None
            
    def cleanup_all(self) -> None:
        """Cleanup all test resources."""
        self.cleanup_api_server()
        self.cleanup_test_environment()


@pytest.mark.e2e
@pytest.mark.slow
class TestPoCScenariosIntegration:
    """Integration tests for PoC Scenarios 1, 2, and 3."""
    
    @pytest.mark.integration
    def test_scenario1_initial_system_generation(self, temp_test_dir):
        """Test Scenario 1: Initial System Generation from natural language."""
        scenario_helper = BaseScenarioTest()
        temp_dir = Path(temp_test_dir)
        scenario_helper.setup_test_environment(temp_dir)
        
        business_request = "Create a system to manage students with name, email, and age"
        print("\n🚀 Starting Scenario 1: Initial System Generation")
        
        scenario_helper.generation_result = scenario_helper.process_natural_language_request(business_request)
        scenario_helper.validate_generation_result(scenario_helper.generation_result, "student")
        
        scenario_helper.validate_file_structure(["student"])
        scenario_helper.validate_database_schema("students", ["id", "name", "email", "age"])
        
        print("\n🎉 SCENARIO 1 COMPLETE - ALL VALIDATIONS PASSED")
        scenario_helper.cleanup_all()
        
    @pytest.mark.integration
    def test_scenario2_runtime_evolution_with_data_preservation(self, temp_test_dir):
        """Test Scenario 2: Runtime Evolution with proper data preservation."""
        scenario_helper = BaseScenarioTest()
        temp_dir = Path(temp_test_dir)
        scenario_helper.setup_test_environment(temp_dir)
        
        print("\n🚀 Starting Scenario 2: Runtime Evolution")
        
        # Step 1: Initial System Setup
        initial_request = "Create a system to manage students with name and email"
        scenario_helper.generation_result = scenario_helper.process_natural_language_request(initial_request)
        scenario_helper.validate_generation_result(scenario_helper.generation_result, "student")
        scenario_helper.validate_database_schema("students", ["id", "name", "email"])
        
        # Step 2: Insert Test Data
        print("\n" + "="*60 + "\nSTEP 2: INSERT TEST DATA" + "\n" + "="*60)
        api_process = scenario_helper.start_api_server(8102)
        test_students = [{"name": "Alice", "email": "alice@test.com"}, {"name": "Bob", "email": "bob@test.com"}]
        try:
            for student in test_students:
                requests.post("http://127.0.0.1:8102/api/students/", json=student, timeout=10)
            print(f"✅ Inserted {len(test_students)} test students.")
        finally:
            scenario_helper.cleanup_api_server()
        
        # Step 3: Runtime Evolution Request
        evolution_request = "Add age field to students"
        scenario_helper.generation_result = scenario_helper.process_natural_language_request(evolution_request)
        scenario_helper.validate_generation_result(scenario_helper.generation_result, "student")
        
        # Step 4: Database Migration and Data Preservation Validation
        print("\n" + "="*60 + "\nSTEP 4: DATABASE MIGRATION & DATA PRESERVATION VALIDATION" + "\n" + "="*60)
        scenario_helper.validate_database_schema("students", ["id", "name", "email", "age"])
        scenario_helper.validate_data_preservation("students", expected_count=len(test_students))
        
        print("\n🎉 SCENARIO 2 COMPLETE - ALL VALIDATIONS PASSED")
        scenario_helper.cleanup_all()

    @pytest.mark.integration
    def test_scenario3_multi_entity_with_relationships(self, temp_test_dir):
        """Test Scenario 3: Multi-Entity System with foreign key relationship creation."""
        scenario_helper = BaseScenarioTest()
        temp_dir = Path(temp_test_dir)
        scenario_helper.setup_test_environment(temp_dir)

        print("\n🚀 Starting Scenario 3: Multi-Entity with Relationships")

        # Step 1: Create Course Entity
        scenario_helper.generation_result = scenario_helper.process_natural_language_request("Create a course entity with a name")
        scenario_helper.validate_generation_result(scenario_helper.generation_result, "course")
        
        # Step 2: Create Student Entity
        scenario_helper.generation_result = scenario_helper.process_natural_language_request("Create a student entity with a name")
        scenario_helper.validate_generation_result(scenario_helper.generation_result, "student")
        
        # Step 3: Create Relationship
        relationship_request = "Add a course to the student entity"
        scenario_helper.generation_result = scenario_helper.process_natural_language_request(relationship_request)
        scenario_helper.validate_generation_result(scenario_helper.generation_result, "student")

        # Step 4: Validation
        print("\n" + "="*60 + "\nSTEP 4: FILE AND DATABASE VALIDATION" + "\n" + "="*60)
        scenario_helper.validate_file_structure(["student", "course"])
        scenario_helper.validate_database_schema("courses", ["id", "name"])
        scenario_helper.validate_database_schema("students", ["id", "name", "course_id"])
        scenario_helper.validate_database_relationship("students", "courses", "course_id")

        print("\n🎉 SCENARIO 3 COMPLETE - ALL VALIDATIONS PASSED")
        scenario_helper.cleanup_all()


@pytest.fixture
def temp_test_dir():
    """Provide a temporary test directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix="poc_scenarios_test_"))
    yield str(temp_dir)
    shutil.rmtree(temp_dir)
