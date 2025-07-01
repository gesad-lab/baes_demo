"""
Scenario 1 Integration Test: Initial System Generation

Tests the core BAE capability for automatic system generation from
natural language input according to Proof of Concept Scenario 1.

Expected workflow:
1. Natural language input → Entity recognition → Student BAE → SWEA coordination
2. Generated system with FastAPI, Streamlit, SQLite
3. Database schema with user-specified attributes (name, email, age)
4. Functional CRUD operations
5. Performance within < 3 minutes
"""

import sqlite3
import time
from pathlib import Path
import os

import pytest
import requests


@pytest.mark.e2e
@pytest.mark.slow
class TestScenario1Integration:
    """Integration test for PoC Scenario 1: Initial System Generation"""

    @pytest.mark.integration
    def test_complete_scenario1_workflow(self, temp_test_dir):
        """Test complete Scenario 1 workflow including all validations"""
        temp_dir = Path(temp_test_dir)
        # Override managed system path for this test run to avoid affecting production system
        os.environ["MANAGED_SYSTEM_PATH"] = str(temp_dir / "managed_system")

        # Patch Config to return the overridden path
        from config import Config
        Config.get_managed_system_path = classmethod(lambda cls: Path(os.environ["MANAGED_SYSTEM_PATH"]))

        managed_system_test_dir = Path(os.environ["MANAGED_SYSTEM_PATH"])
        business_request = "Create a system to manage students with name, email, and age"
        print("\n🚀 Starting Scenario 1 system generation...")
        print(f"📝 Business Request: {business_request}")
        print(f"📁 Temp Directory: {temp_dir}")
        start_time = time.time()
        
        # ====================================================================
        # STEP 1: System Generation Workflow
        # ====================================================================
        print("\n" + "="*60)
        print("STEP 1: SYSTEM GENERATION WORKFLOW")
        print("="*60)
        
        # Import and initialize Enhanced Runtime Kernel
        print("\n🎯 Initializing Enhanced Runtime Kernel...")
        from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel
        
        # Create kernel instance
        kernel = EnhancedRuntimeKernel()
        
        print("\n🎯 Processing natural language request...")
        # Process the natural language request using the kernel
        result = kernel.process_natural_language_request(
            request=business_request,
            context="academic",
            start_servers=False  # Don't start servers in test environment
        )
        
        execution_time = time.time() - start_time
        
        # Validate the result structure
        print(f"📊 Generation result: {result.get('success', False)}")
        assert result.get("success", False), f"System generation failed: {result.get('message', 'Unknown error')}"
        
        # Validate entity detection
        detected_entity = result.get("entity", "")
        assert detected_entity.lower() == "student", f"Expected Student entity, got {detected_entity}"
        
        # Validate BAE interpretation
        interpretation = result.get("interpretation", {})
        assert interpretation, "Missing BAE interpretation"
        
        # Validate attributes extraction
        attributes = interpretation.get("attributes", [])
        expected_attributes = ["name", "email", "age"]
        attribute_names = []
        for attr in attributes:
            if ":" in attr:
                attr_name = attr.split(":")[0].strip()
                attribute_names.append(attr_name)
            else:
                attribute_names.append(attr.strip())
        
        for attr in expected_attributes:
            assert attr in attribute_names, f"Missing expected attribute: {attr}"
        
        # Validate execution results
        execution_results = result.get("execution_results", [])
        assert execution_results, "No execution results returned"
        
        # Check that all tasks were successful
        successful_tasks = [task for task in execution_results if task.get("success", False)]
        assert len(successful_tasks) > 0, "No successful tasks in execution results"
        
        print("✅ System generation workflow completed successfully!")
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        
        # Store results for subsequent validations
        generation_result = {
            "success": True,
            "entity": detected_entity,
            "interpretation": interpretation,
            "attributes": attributes,
            "execution_results": execution_results,
            "execution_time": execution_time,
        }
        
        # Validate performance criteria (< 3 minutes)
        assert execution_time < 180, f"System generation took {execution_time:.2f}s, exceeding 180s limit"
        
        # ====================================================================
        # STEP 2: Generated Files Validation
        # ====================================================================
        print("\n" + "="*60)
        print("STEP 2: GENERATED FILES VALIDATION")
        print("="*60)
        
        managed_system_dir = managed_system_test_dir
        print(f"\n📁 Validating generated files in: {managed_system_dir}")

        # Check managed system structure exists
        assert (
            managed_system_dir.exists()
        ), f"Managed system directory not created: {managed_system_dir}"

        # Validate expected directory structure
        expected_dirs = ["app", "ui"]
        for dir_name in expected_dirs:
            dir_path = managed_system_dir / dir_name
            assert dir_path.exists(), f"Expected directory not found: {dir_path}"

        # Validate app structure (FastAPI)
        app_dir = managed_system_dir / "app"
        expected_app_items = ["models", "routes", "database", "main.py"]
        for item in expected_app_items:
            item_path = app_dir / item
            assert item_path.exists(), f"Expected app item not found: {item_path}"

        # Validate UI structure (Streamlit)
        ui_dir = managed_system_dir / "ui"
        expected_ui_items = ["pages", "app.py"]
        for item in expected_ui_items:
            item_path = ui_dir / item
            assert item_path.exists(), f"Expected UI item not found: {item_path}"

        # Validate Python file syntax
        python_files = []
        for pattern in ["app/**/*.py", "ui/**/*.py"]:
            python_files.extend(list(managed_system_dir.glob(pattern)))

        assert (
            len(python_files) >= 3
        ), f"Expected at least 3 Python files, found {len(python_files)}"

        for py_file in python_files:
            try:
                with open(py_file, "r") as f:
                    code = f.read()
                # Suppress warnings during compilation
                import warnings

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", DeprecationWarning)
                    warnings.simplefilter("ignore", SyntaxWarning)
                    compile(code, str(py_file), "exec")
                print(f"✅ Valid Python syntax: {py_file}")
            except SyntaxError as e:
                pytest.fail(f"Invalid Python syntax in {py_file}: {e}")

        print(f"✅ All {len(python_files)} Python files have valid syntax")
        
        # ====================================================================
        # STEP 3: Database Schema Validation
        # ====================================================================
        print("\n" + "="*60)
        print("STEP 3: DATABASE SCHEMA VALIDATION")
        print("="*60)
        
        db_path = managed_system_dir / "app" / "database" / "baes_system.db"
        print(f"\n🗄️ Validating database schema at: {db_path}")

        # Check database file exists
        assert db_path.exists(), f"Database file not created: {db_path}"
        assert db_path.stat().st_size > 0, "Database file is empty"

        # Validate database schema
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        try:
            # Check that students table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students';")
            tables = cursor.fetchall()
            assert len(tables) > 0, "Students table not created"

            # Validate table schema
            cursor.execute("PRAGMA table_info(students);")
            columns = cursor.fetchall()
            assert (
                len(columns) >= 4
            ), f"Expected at least 4 columns (id + 3 attributes), found {len(columns)}"

            # Validate expected columns exist (PoC: name, email, age)
            column_names = [col[1].lower() for col in columns]
            expected_columns = ["id", "name", "email", "age"]

            for expected_col in expected_columns:
                assert (
                    expected_col in column_names
                ), f"Expected column '{expected_col}' not found. Available: {column_names}"

            print(f"✅ Database schema validated: {len(columns)} columns")
            print(f"📋 Columns: {column_names}")

        finally:
            conn.close()
            
        # ====================================================================
        # STEP 4: API Functionality Validation
        # ====================================================================
        print("\n" + "="*60)
        print("STEP 4: API FUNCTIONALITY VALIDATION")
        print("="*60)
        
        # Start servers for API testing
        managed_system_dir = managed_system_test_dir
        print("\n🔌 Starting servers for API testing...")

        # Start FastAPI server
        import subprocess

        api_process = subprocess.Popen(
            ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8100"],
            cwd=managed_system_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        time.sleep(5)

        try:
            # Test API endpoints
            base_url = "http://127.0.0.1:8100"

            # Test GET / (health check)
            response = requests.get(f"{base_url}/", timeout=10)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"

            # Test GET /api/students/ (list students)
            response = requests.get(f"{base_url}/api/students/", timeout=10)
            assert response.status_code == 200, f"List students failed: {response.status_code}"

            # Test POST /api/students/ (create student)
            student_data = {"name": "John Doe", "email": "john.doe@example.com", "age": 25}
            response = requests.post(f"{base_url}/api/students/", json=student_data, timeout=10)
            assert response.status_code in (200, 201), f"Create student failed: {response.status_code}"

            created_student = response.json()
            assert created_student["name"] == student_data["name"]
            assert created_student["email"] == student_data["email"]
            assert created_student["age"] == student_data["age"]
            assert "id" in created_student

            print("✅ API CRUD operations validated successfully")

        finally:
            # Cleanup
            api_process.terminate()
            api_process.wait()
            
        # ====================================================================
        # STEP 5: Performance Criteria Validation
        # ====================================================================
        print("\n" + "="*60)
        print("STEP 5: PERFORMANCE CRITERIA VALIDATION")
        print("="*60)
        
        print("\n⏱️ Validating performance criteria...")

        # Performance criteria from PoC: < 3 minutes
        max_generation_time = 180  # 3 minutes in seconds

        # Get execution time from generation result
        execution_time = generation_result["execution_time"]

        assert (
            execution_time < max_generation_time
        ), f"Total execution time {execution_time:.2f}s exceeds {max_generation_time}s limit"

        # Validate success rate
        execution_results = generation_result["execution_results"]
        successful_tasks = [r for r in execution_results if r.get("success")]
        success_rate = len(successful_tasks) / len(execution_results) * 100

        assert success_rate >= 80, f"Success rate {success_rate:.1f}% below 80% threshold"

        print("✅ Performance criteria met:")
        print(f"   ⏱️  Execution time: {execution_time:.2f}s (limit: {max_generation_time}s)")
        print(f"   🎯 Success rate: {success_rate:.1f}% (target: ≥80%)")
        
        # ====================================================================
        # STEP 6: Semantic Coherence Validation
        # ====================================================================
        print("\n" + "="*60)
        print("STEP 6: SEMANTIC COHERENCE VALIDATION")
        print("="*60)
        
        print("\n🧠 Validating semantic coherence...")

        interpretation = generation_result["interpretation"]
        
        # Validate that business vocabulary is preserved
        business_vocabulary = interpretation.get("business_vocabulary", [])
        assert business_vocabulary, "Business vocabulary not preserved in interpretation"
        
        # Validate domain entity focus
        entity_focus = interpretation.get("entity_focus", "")
        assert entity_focus == "Student", f"Expected Student entity focus, got {entity_focus}"
        
        # Validate domain operations
        domain_operations = interpretation.get("domain_operations", [])
        assert domain_operations, "Domain operations not defined"
        
        # Check that the interpretation maintains semantic coherence
        semantic_coherence = interpretation.get("semantic_coherence", False)
        assert semantic_coherence, "Semantic coherence not maintained"
        
        # Check that domain knowledge is preserved
        domain_knowledge_preserved = interpretation.get("domain_knowledge_preserved", False)
        assert domain_knowledge_preserved, "Domain knowledge not preserved"
        
        print("✅ Semantic coherence validated:")
        print(f"   🎯 Entity focus: {entity_focus}")
        print(f"   📝 Business vocabulary: {business_vocabulary}")
        print(f"   🔧 Domain operations: {domain_operations}")
        print(f"   🧠 Semantic coherence: {semantic_coherence}")
        print(f"   💾 Domain knowledge preserved: {domain_knowledge_preserved}")
        
        # ====================================================================
        # FINAL SUMMARY
        # ====================================================================
        print("\n" + "="*60)
        print("🎉 SCENARIO 1 COMPLETE - ALL VALIDATIONS PASSED")
        print("="*60)
        print(f"✅ System Generation: {execution_time:.2f}s")
        print(f"✅ Generated Files: {len(python_files)} Python files")
        print(f"✅ Database Schema: {len(columns)} columns")
        print(f"✅ API Functionality: CRUD operations working")
        print(f"✅ Performance: {success_rate:.1f}% success rate")
        print(f"✅ Semantic Coherence: Domain knowledge preserved")
        print("="*60)


@pytest.fixture
def temp_test_dir():
    """Provide a temporary test directory"""
    import shutil
    import tempfile

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="scenario1_test_"))

    yield str(temp_dir)

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
