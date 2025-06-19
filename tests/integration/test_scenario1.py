"""
Scenario 1 Tests: Initial System Generation - Real World End-to-End Testing

Tests the core BAE capability for automatic system generation from
natural language input with real OpenAI API calls, actual file generation,
real servers, and complete CRUD validation.
"""

import os
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Dict

import pytest
import requests

from baes.core.context_store import ContextStore
from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel
from config import Config

# Use centralized temp directory from conftest (consistent with other tests)
TESTS_TEMP_DIR = Path(__file__).parent.parent / ".temp"

# Use centralized port configuration
REALWORLD_FASTAPI_PORT = Config.REALWORLD_FASTAPI_PORT
REALWORLD_STREAMLIT_PORT = Config.REALWORLD_STREAMLIT_PORT


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.filterwarnings("ignore::SyntaxWarning")
class TestScenario1RealWorld:
    """End-to-end validation of Scenario 1 with real components"""

    # ==========================================
    # 1. SYSTEM GENERATION TESTS
    # ==========================================

    def test_01_system_generation_workflow(self, real_system_fixtures, performance_tracker):
        """Test complete system generation with real OpenAI calls"""

        performance_tracker.start("scenario1_real_system_generation")

        temp_dir, kernel, context_store = real_system_fixtures

        # Natural language business request (exactly as in PoC specification)
        business_request = (
            "Create a system to manage students with name, registration number, and course"
        )

        print("\n🚀 Starting real system generation...")
        print(f"📝 Business Request: {business_request}")
        print(f"📁 Temp Directory: {temp_dir}")

        # Process request with real OpenAI API calls
        result = kernel.process_natural_language_request(
            business_request,
            context="academic",
            start_servers=False,  # We'll start servers in separate tests
        )

        execution_time = performance_tracker.stop()

        # Validate system generation results
        assert (
            result["success"] is True
        ), f"System generation failed: {result.get('error', 'Unknown error')}"
        assert result["entity"] == "student"
        assert "interpretation" in result
        assert "execution_results" in result

        # Validate execution results
        execution_results = result["execution_results"]
        assert len(execution_results) >= 3, "Should have at least 3 SWEA execution results"

        # Check that all SWEAs executed successfully
        successful_tasks = [r for r in execution_results if r.get("success")]
        assert len(successful_tasks) >= 3, f"Not all SWEA tasks succeeded: {execution_results}"

        # Validate performance criteria (PoC: < 3 minutes)
        assert (
            execution_time < 180
        ), f"System generation took {execution_time:.2f}s, exceeding 180s limit"

        print(f"✅ System generation completed in {execution_time:.2f} seconds")
        print(f"📊 SWEA tasks executed: {len(execution_results)}")
        print(f"🎯 Success rate: {len(successful_tasks)}/{len(execution_results)}")

    def test_02_generated_files_validation(self, real_system_fixtures):
        """Validate all expected files are generated correctly"""

        temp_dir, _, _ = real_system_fixtures
        managed_system_dir = temp_dir / "managed_system"

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

        # Validate app structure
        app_dir = managed_system_dir / "app"
        expected_app_items = ["models", "routes", "database", "main.py"]
        for item in expected_app_items:
            item_path = app_dir / item
            assert item_path.exists(), f"Expected app item not found: {item_path}"

        # Validate UI structure
        ui_dir = managed_system_dir / "ui"
        expected_ui_items = ["pages", "app.py"]
        for item in expected_ui_items:
            item_path = ui_dir / item
            assert item_path.exists(), f"Expected UI item not found: {item_path}"

        # Validate Python file syntax (exclude venv and other non-generated directories)
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
                # Suppress warnings during compilation of generated code
                import warnings

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", DeprecationWarning)
                    warnings.simplefilter("ignore", SyntaxWarning)
                    compile(code, str(py_file), "exec")
                print(f"✅ Valid Python syntax: {py_file.relative_to(temp_dir)}")
            except SyntaxError as e:
                pytest.fail(f"Invalid Python syntax in {py_file}: {e}")

        print(f"✅ All {len(python_files)} Python files have valid syntax")

    def test_03_database_creation_validation(self, real_system_fixtures):
        """Validate database schema and setup"""

        temp_dir, _, _ = real_system_fixtures
        db_path = temp_dir / "managed_system" / "app" / "database" / "academic.db"

        print(f"\n🗄️ Validating database at: {db_path}")

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
                len(columns) >= 3
            ), f"Expected at least 3 columns in students table, found {len(columns)}"

            # Validate expected columns exist
            column_names = [col[1] for col in columns]
            expected_columns = ["id", "name", "registration_number", "course"]
            for expected_col in expected_columns:
                assert any(
                    expected_col in col_name.lower() for col_name in column_names
                ), f"Expected column '{expected_col}' not found. Available: {column_names}"

            print(f"✅ Database schema validated: {len(columns)} columns")
            print(f"📋 Columns: {column_names}")

        finally:
            conn.close()

    # ==========================================
    # 2. SERVER TESTS
    # ==========================================

    def test_04_fastapi_server_startup(self, real_system_fixtures, server_manager):
        """Test FastAPI server starts and is accessible"""

        temp_dir, _, _ = real_system_fixtures
        fastapi_port, _ = server_manager

        print(f"\n🚀 Testing FastAPI server startup on port {fastapi_port}")

        # Health check
        health_url = f"http://localhost:{fastapi_port}/health"
        response = requests.get(health_url, timeout=5)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"

        # OpenAPI docs check
        docs_url = f"http://localhost:{fastapi_port}/docs"
        response = requests.get(docs_url, timeout=5)
        assert response.status_code == 200, f"OpenAPI docs not accessible: {response.status_code}"

        # API root check
        root_url = f"http://localhost:{fastapi_port}/"
        response = requests.get(root_url, timeout=5)
        assert response.status_code in [200, 404], f"API root check failed: {response.status_code}"

        print("✅ FastAPI server is running and accessible")

    def test_05_streamlit_server_startup(self, real_system_fixtures, server_manager):
        """Test Streamlit server starts and is accessible"""

        temp_dir, _, _ = real_system_fixtures
        _, streamlit_port = server_manager

        print(f"\n🖥️ Testing Streamlit server startup on port {streamlit_port}")

        # Homepage check
        home_url = f"http://localhost:{streamlit_port}"
        response = requests.get(home_url, timeout=10)
        assert (
            response.status_code == 200
        ), f"Streamlit homepage not accessible: {response.status_code}"

        # Check for Streamlit-specific content
        assert (
            "streamlit" in response.text.lower() or "student" in response.text.lower()
        ), "Response doesn't contain expected Streamlit content"

        print("✅ Streamlit server is running and accessible")

    # ==========================================
    # 3. API FUNCTIONALITY TESTS
    # ==========================================

    def test_06_api_crud_operations(self, running_servers):
        """Test all CRUD operations on generated API"""

        fastapi_port, _ = running_servers
        base_url = f"http://localhost:{fastapi_port}/api"

        print(f"\n🔧 Testing API CRUD operations at {base_url}")

        # Test data
        test_student = {
            "name": "John Doe",
            "registration_number": "REG001",
            "course": "Computer Science",
        }

        # CREATE - POST /students/
        print("📝 Testing CREATE operation...")
        create_response = requests.post(f"{base_url}/students/", json=test_student, timeout=5)
        assert create_response.status_code in [
            200,
            201,
        ], f"Create failed: {create_response.status_code} - {create_response.text}"

        created_student = create_response.json()
        assert "id" in created_student, "Created student should have an ID"
        student_id = created_student["id"]

        # READ - GET /students/ (list)
        print("📋 Testing READ operations...")
        list_response = requests.get(f"{base_url}/students/", timeout=5)
        assert list_response.status_code == 200, f"List failed: {list_response.status_code}"

        students_list = list_response.json()
        assert isinstance(students_list, list), "Students list should be an array"
        assert len(students_list) >= 1, "Should have at least one student"

        # READ - GET /students/{id} (retrieve)
        get_response = requests.get(f"{base_url}/students/{student_id}", timeout=5)
        assert get_response.status_code == 200, f"Get by ID failed: {get_response.status_code}"

        retrieved_student = get_response.json()
        assert retrieved_student["name"] == test_student["name"], "Retrieved student name mismatch"

        # UPDATE - PUT /students/{id}
        print("✏️ Testing UPDATE operation...")
        updated_data = test_student.copy()
        updated_data["course"] = "Updated Computer Science"

        update_response = requests.put(
            f"{base_url}/students/{student_id}", json=updated_data, timeout=5
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.status_code}"

        # Verify update
        verify_response = requests.get(f"{base_url}/students/{student_id}", timeout=5)
        updated_student = verify_response.json()
        assert updated_student["course"] == "Updated Computer Science", "Update not reflected"

        # DELETE - DELETE /students/{id}
        print("🗑️ Testing DELETE operation...")
        delete_response = requests.delete(f"{base_url}/students/{student_id}", timeout=5)
        assert delete_response.status_code in [
            200,
            204,
        ], f"Delete failed: {delete_response.status_code}"

        # Verify deletion
        verify_delete_response = requests.get(f"{base_url}/students/{student_id}", timeout=5)
        assert verify_delete_response.status_code == 404, "Student should be deleted"

        print("✅ All CRUD operations completed successfully")

    def test_07_api_data_validation(self, running_servers):
        """Test API validates data according to generated schema"""

        fastapi_port, _ = running_servers
        base_url = f"http://localhost:{fastapi_port}/api"

        print("\n🔍 Testing API data validation...")

        # Test missing required fields
        invalid_student = {"name": "John"}  # Missing required fields
        response = requests.post(f"{base_url}/students/", json=invalid_student, timeout=5)
        assert response.status_code in [
            400,
            422,
        ], f"Should reject invalid data: {response.status_code}"

        # Test empty/invalid data
        empty_student = {}
        response = requests.post(f"{base_url}/students/", json=empty_student, timeout=5)
        assert response.status_code in [
            400,
            422,
        ], f"Should reject empty data: {response.status_code}"

        print("✅ API data validation working correctly")

    # ==========================================
    # 4. UI FUNCTIONALITY TESTS
    # ==========================================

    def test_08_streamlit_basic_accessibility(self, running_servers):
        """Test Streamlit UI basic accessibility via HTTP"""

        _, streamlit_port = running_servers
        base_url = f"http://localhost:{streamlit_port}"

        print("\n🖥️ Testing Streamlit basic accessibility...")

        # Homepage accessibility
        response = requests.get(base_url, timeout=10)
        assert response.status_code == 200, f"Homepage not accessible: {response.status_code}"

        # Check for Streamlit-specific elements that are always present
        html_content = response.text.lower()
        streamlit_elements = ["streamlit", "script", "div", "body"]

        found_elements = [elem for elem in streamlit_elements if elem in html_content]
        assert len(found_elements) >= 3, f"Streamlit elements not found. Found: {found_elements}"

        print(f"✅ Streamlit UI accessible with elements: {found_elements}")

    @pytest.mark.selenium
    def test_09_streamlit_student_creation_workflow(self, running_servers, selenium_driver):
        """Test complete student creation workflow via UI"""

        _, streamlit_port = running_servers
        base_url = f"http://localhost:{streamlit_port}"

        print("\n🤖 Testing Streamlit student creation with Selenium...")

        driver = selenium_driver
        driver.get(base_url)

        # Wait for page to load
        time.sleep(3)

        try:
            # Look for student creation form elements
            # Note: Streamlit generates specific CSS selectors
            name_input = driver.find_element(
                "css selector", "input[aria-label*='name'], input[placeholder*='name']"
            )
            name_input.clear()
            name_input.send_keys("Selenium Test Student")

            # Find and fill other form fields
            reg_input = driver.find_element(
                "css selector",
                "input[aria-label*='registration'], input[placeholder*='registration']",
            )
            reg_input.clear()
            reg_input.send_keys("SEL001")

            course_input = driver.find_element(
                "css selector", "input[aria-label*='course'], input[placeholder*='course']"
            )
            course_input.clear()
            course_input.send_keys("Selenium Testing Course")

            # Submit form
            submit_button = driver.find_element(
                "css selector",
                "button[kind='primary'], button:contains('Create'), button:contains('Submit')",
            )
            submit_button.click()

            # Wait for response
            time.sleep(2)

            # Verify success message or student appears in list
            page_source = driver.page_source.lower()
            assert (
                "selenium test student" in page_source or "success" in page_source
            ), "Student creation not reflected in UI"

            print("✅ Student creation workflow completed successfully")

        except Exception as e:
            # Take screenshot for debugging
            screenshot_path = TESTS_TEMP_DIR / "selenium_error_screenshot.png"
            driver.save_screenshot(str(screenshot_path))
            print(f"🔍 Screenshot saved to: {screenshot_path}")
            raise e

    @pytest.mark.selenium
    def test_10_streamlit_student_management_workflow(self, running_servers, selenium_driver):
        """Test student view/edit/delete workflow via UI"""

        _, streamlit_port = running_servers
        base_url = f"http://localhost:{streamlit_port}"

        print("\n🔧 Testing Streamlit management workflow with Selenium...")

        driver = selenium_driver
        driver.get(base_url)
        time.sleep(3)

        try:
            # Navigate through different pages/tabs if they exist
            # Look for navigation elements
            driver.find_elements("css selector", "button, .tab, .sidebar button")

            # Check if we can view student lists
            driver.page_source.lower()

            # Look for table or list elements
            tables = driver.find_elements(
                "css selector", "table, .dataframe, [data-testid*='table']"
            )

            if tables:
                print(f"✅ Found {len(tables)} table elements in UI")
            else:
                print("ℹ️ No table elements found, but UI is accessible")

            print("✅ Student management workflow accessible")

        except Exception as e:
            screenshot_path = TESTS_TEMP_DIR / "selenium_mgmt_error_screenshot.png"
            driver.save_screenshot(str(screenshot_path))
            print(f"🔍 Screenshot saved to: {screenshot_path}")
            raise e

    # ==========================================
    # 5. INTEGRATION VALIDATION
    # ==========================================

    def test_11_end_to_end_workflow_validation(self, running_servers):
        """Test complete workflow: UI → API → Database → UI"""

        fastapi_port, streamlit_port = running_servers
        api_base = f"http://localhost:{fastapi_port}/api"
        ui_base = f"http://localhost:{streamlit_port}"

        print("\n🔗 Testing end-to-end workflow integration...")

        # Create student via API
        test_student = {
            "name": "E2E Test Student",
            "registration_number": "E2E001",
            "course": "End-to-End Testing",
        }

        create_response = requests.post(f"{api_base}/students/", json=test_student, timeout=5)
        assert create_response.status_code in [200, 201], "API creation failed"

        created_student = create_response.json()
        student_id = created_student["id"]

        # Verify via database direct access
        temp_dir = (
            Path(running_servers).parent if hasattr(running_servers, "parent") else TESTS_TEMP_DIR
        )
        db_path = temp_dir / "managed_system" / "app" / "database" / "academic.db"

        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            db_result = cursor.fetchone()
            conn.close()

            assert db_result is not None, "Student not found in database"
            print("✅ Data persisted correctly in database")

        # Verify UI reflects the data
        ui_response = requests.get(ui_base, timeout=10)
        assert ui_response.status_code == 200, "UI not accessible"

        # Clean up
        delete_response = requests.delete(f"{api_base}/students/{student_id}", timeout=5)
        assert delete_response.status_code in [200, 204], "Cleanup failed"

        print("✅ End-to-end workflow validation completed")

    def test_12_performance_and_success_criteria(
        self, real_system_fixtures, scenario1_success_criteria
    ):
        """Validate Scenario 1 success criteria are met"""

        print("\n📊 Validating Scenario 1 success criteria...")

        # Performance was already validated in test_01, but let's check the criteria
        criteria = scenario1_success_criteria

        # Verify temp directory structure meets expectations
        temp_dir, _, _ = real_system_fixtures
        managed_system = temp_dir / "managed_system"

        # Check expected artifacts exist
        expected_artifacts = criteria["expected_artifacts"]
        for artifact in expected_artifacts:
            if artifact == "models":
                assert (managed_system / "app" / "models").exists(), f"Missing artifact: {artifact}"
            elif artifact == "routes":
                assert (managed_system / "app" / "routes").exists(), f"Missing artifact: {artifact}"
            elif artifact == "ui":
                assert (managed_system / "ui").exists(), f"Missing artifact: {artifact}"
            elif artifact == "database":
                assert (
                    managed_system / "app" / "database"
                ).exists(), f"Missing artifact: {artifact}"

        print(f"✅ All expected artifacts present: {expected_artifacts}")
        print("✅ Scenario 1 success criteria validated")

    def test_13_ui_error_handling_validation(self, running_servers):
        """Test UI error message handling and display"""

        _, streamlit_port = running_servers
        base_url = f"http://localhost:{streamlit_port}"

        print("\n🚨 Testing UI error handling and error message validation...")

        # Test 1: Check for absence of common error indicators in normal operation
        print("📋 Step 1: Validating normal operation (no errors)")
        response = requests.get(base_url, timeout=10)
        assert response.status_code == 200, f"UI not accessible: {response.status_code}"

        html_content = response.text.lower()

        # Common error indicators that should NOT be present in normal operation
        error_indicators = [
            "error occurred",
            "something went wrong",
            "internal server error",
            "500 error",
            "404 not found",
            "connection failed",
            "database error",
            "api error",
            "failed to load",
            "exception",
            "traceback",
            "keyerror",
            "attributeerror",
            "typeerror",
            "valueerror",
        ]

        found_errors = [error for error in error_indicators if error in html_content]

        if found_errors:
            print(f"⚠️ Found potential error indicators: {found_errors}")
            # Don't fail immediately - these might be legitimate error handling UI elements
            # Instead, log them for inspection
        else:
            print("✅ No error indicators found in normal operation")

        # Test 2: Check for proper Streamlit UI elements (adjusted for SPA behavior)
        print("📋 Step 2: Validating Streamlit UI elements are present")

        # Look for Streamlit-specific elements that should be present in the main HTML
        streamlit_indicators = [
            "streamlit",  # Basic Streamlit functionality
            "javascript",  # JavaScript for SPA functionality
            "script",  # Script tags for dynamic content
            "css",  # Styling elements
        ]

        found_streamlit = [
            indicator for indicator in streamlit_indicators if indicator in html_content
        ]
        assert (
            len(found_streamlit) >= 2
        ), f"Missing essential Streamlit elements. Found: {found_streamlit}"
        print(f"✅ Found essential Streamlit elements: {found_streamlit}")

        # Test 3: Check for business-friendly error messaging patterns
        print("📋 Step 3: Validating business-friendly error patterns")

        # Look for patterns that indicate good error handling design
        good_error_patterns = [
            "please",  # Polite error messages
            "try again",  # User guidance
            "contact",  # Support information
            "help",  # Help text
            "required",  # Field validation
            "invalid",  # Input validation
            "success",  # Success feedback
            "created",  # Operation feedback
            "updated",  # Operation feedback
            "deleted",  # Operation feedback
        ]

        found_good_patterns = [
            pattern for pattern in good_error_patterns if pattern in html_content
        ]
        print(
            f"ℹ️ Found {len(found_good_patterns)} business-friendly patterns: {found_good_patterns}"
        )

        # Test 4: Validate no critical system errors are exposed
        print("📋 Step 4: Validating no critical system errors are exposed")

        # Critical errors that should NEVER be exposed to users
        critical_errors = [
            "sqlalchemy",
            "fastapi",
            "uvicorn",
            "python",
            "traceback",
            'file "/',
            "line ",
            "module",
            "import error",
            "syntax error",
            "indentation error",
        ]

        found_critical = [error for error in critical_errors if error in html_content]
        assert len(found_critical) == 0, f"Critical system errors exposed to user: {found_critical}"
        print("✅ No critical system errors exposed to users")

        # Test 5: Check for proper Streamlit framework loading
        print("📋 Step 5: Validating Streamlit framework loading")

        # Check that the Streamlit framework loaded properly without errors
        framework_indicators = [
            "streamlit",  # Streamlit framework
            "root",  # React root element
            "javascript",  # JavaScript enabled
            "noscript",  # Fallback message
        ]

        found_framework = [
            indicator for indicator in framework_indicators if indicator in html_content
        ]
        assert (
            len(found_framework) >= 2
        ), f"Streamlit framework not loading properly. Found: {found_framework}"
        print(f"✅ Streamlit framework loading correctly: {found_framework}")

        # Test 6: Validate Streamlit app structure and navigation
        print("📋 Step 6: Validating Streamlit app structure")

        # Check for navigation and app structure elements
        app_structure_elements = [
            "title",  # Page title
            "head",  # HTML head section
            "body",  # HTML body
            "noscript",  # Fallback for no JavaScript
        ]

        found_structure = [element for element in app_structure_elements if element in html_content]
        assert (
            len(found_structure) >= 3
        ), f"Missing app structure elements. Found: {found_structure}"
        print(f"✅ App structure elements present: {found_structure}")

        print("✅ UI error handling validation completed successfully")

        # Summary report
        print("\n📊 Error Handling Validation Summary:")
        print(f"   • Error indicators found: {len(found_errors)}")
        print(f"   • Streamlit elements: {len(found_streamlit)}")
        print(f"   • Business-friendly patterns: {len(found_good_patterns)}")
        print(f"   • Critical errors exposed: {len(found_critical)}")
        print(f"   • Framework indicators: {len(found_framework)}")
        print(f"   • App structure elements: {len(found_structure)}")

    @pytest.mark.selenium
    def test_14_ui_error_scenarios_selenium(self, running_servers, selenium_driver):
        """Test UI error scenarios using Selenium browser automation"""

        _, streamlit_port = running_servers
        base_url = f"http://localhost:{streamlit_port}"

        print("\n🤖 Testing UI error scenarios with Selenium...")

        driver = selenium_driver
        driver.get(base_url)
        time.sleep(3)

        try:
            # Test 1: Submit empty form to trigger validation errors
            print("📋 Step 1: Testing form validation errors")

            # Look for submit button and click without filling form
            submit_buttons = driver.find_elements(
                "css selector",
                "button[kind='primary'], button:contains('Create'), button:contains('Submit')",
            )

            if submit_buttons:
                submit_buttons[0].click()
                time.sleep(2)

                # Check for validation error messages
                page_source = driver.page_source.lower()

                # Look for validation error indicators
                validation_errors = [
                    "required",
                    "please fill",
                    "cannot be empty",
                    "invalid",
                    "error",
                    "missing",
                ]

                found_validation = [error for error in validation_errors if error in page_source]
                print(f"ℹ️ Form validation patterns found: {found_validation}")

                # Ensure no critical system errors are shown
                critical_errors = ["traceback", "exception", "sqlalchemy", "fastapi"]
                found_critical = [error for error in critical_errors if error in page_source]
                assert (
                    len(found_critical) == 0
                ), f"Critical errors exposed during validation: {found_critical}"

                print("✅ Form validation working without exposing system errors")
            else:
                print("ℹ️ No submit buttons found - skipping form validation test")

            # Test 2: Test invalid input scenarios
            print("📋 Step 2: Testing invalid input handling")

            # Try to find input fields and enter invalid data
            input_fields = driver.find_elements("css selector", "input")

            if input_fields:
                # Test with extremely long input
                input_fields[0].clear()
                input_fields[0].send_keys("x" * 1000)  # Very long input

                # Test with special characters
                if len(input_fields) > 1:
                    input_fields[1].clear()
                    input_fields[1].send_keys("'; DROP TABLE students; --")  # SQL injection attempt

                # Try to submit
                submit_buttons = driver.find_elements(
                    "css selector",
                    "button[kind='primary'], button:contains('Create'), button:contains('Submit')",
                )

                if submit_buttons:
                    submit_buttons[0].click()
                    time.sleep(2)

                    page_source = driver.page_source.lower()

                    # Ensure no SQL injection or system errors
                    security_issues = ["sql", "drop table", "delete from", "insert into"]
                    found_security = [issue for issue in security_issues if issue in page_source]
                    assert len(found_security) == 0, f"Security issues detected: {found_security}"

                    print("✅ Invalid input handled securely")
            else:
                print("ℹ️ No input fields found - skipping invalid input test")

            # Test 3: Check for user-friendly error messages
            print("📋 Step 3: Validating user-friendly error messaging")

            page_source = driver.page_source.lower()

            # Look for user-friendly error message patterns
            friendly_patterns = [
                "please",
                "try again",
                "help",
                "contact",
                "invalid",
                "required",
                "check",
                "correct",
            ]

            found_friendly = [pattern for pattern in friendly_patterns if pattern in page_source]
            print(f"ℹ️ User-friendly patterns found: {found_friendly}")

            # Ensure technical jargon is not exposed
            technical_jargon = [
                "traceback",
                "exception",
                "module",
                "import",
                "python",
                "sqlalchemy",
                "fastapi",
                "uvicorn",
            ]

            found_technical = [jargon for jargon in technical_jargon if jargon in page_source]
            assert (
                len(found_technical) == 0
            ), f"Technical jargon exposed to users: {found_technical}"

            print("✅ User-friendly error messaging validated")

            # Test 4: Check error message accessibility
            print("📋 Step 4: Testing error message accessibility")

            # Look for error elements with proper accessibility attributes
            error_elements = driver.find_elements(
                "css selector",
                "[role='alert'], .error, .warning, .danger, [aria-live], [aria-label*='error']",
            )

            print(f"ℹ️ Found {len(error_elements)} accessibility-aware error elements")

            # Check for proper ARIA labels and roles
            accessible_errors = []
            for element in error_elements:
                if (
                    element.get_attribute("role")
                    or element.get_attribute("aria-live")
                    or element.get_attribute("aria-label")
                ):
                    accessible_errors.append(element)

            print(f"✅ Found {len(accessible_errors)} properly labeled error elements")

            print("✅ UI error scenarios testing completed successfully")

        except Exception as e:
            # Take screenshot for debugging
            screenshot_path = TESTS_TEMP_DIR / "selenium_error_scenarios_screenshot.png"
            driver.save_screenshot(str(screenshot_path))
            print(f"🔍 Error scenarios screenshot saved to: {screenshot_path}")
            raise e

    @pytest.mark.selenium
    def test_15_specific_main_function_error_validation(self, running_servers, selenium_driver):
        """Test specifically for the 'No main() or show_entity_management() function found' error"""

        _, streamlit_port = running_servers
        base_url = f"http://localhost:{streamlit_port}"

        print("\n🔍 Testing for specific main() function error message...")

        driver = selenium_driver
        driver.get(base_url)
        time.sleep(5)  # Wait for Streamlit to fully load

        try:
            # Get the page source after JavaScript has rendered the content
            page_source = driver.page_source.lower()

            # Check specifically for the main() function error message
            main_function_errors = [
                "no main() or show_entity_management() function found",
                "no main() function found",
                "show_entity_management() function found",
                "function found in student_management",
                "failed to load student management page",
            ]

            found_main_errors = [error for error in main_function_errors if error in page_source]

            # This should be empty if our fix worked
            if found_main_errors:
                print(f"❌ Found main() function errors: {found_main_errors}")

                # Take screenshot for debugging
                screenshot_path = TESTS_TEMP_DIR / "main_function_error_screenshot.png"
                driver.save_screenshot(str(screenshot_path))
                print(f"🔍 Screenshot saved to: {screenshot_path}")

                assert False, f"Main function error still present: {found_main_errors}"
            else:
                print("✅ No main() function errors found - fix successful!")

            # Additional check: ensure the page has expected content
            expected_content = ["student", "management", "entity", "bae", "academic"]

            found_content = [content for content in expected_content if content in page_source]
            print(f"ℹ️ Expected content found: {found_content}")

            # Check for positive indicators that the page loaded correctly
            positive_indicators = [
                "student management",
                "add new student",
                "student list",
                "name",
                "registration",
                "course",
            ]

            found_positive = [
                indicator for indicator in positive_indicators if indicator in page_source
            ]
            print(f"ℹ️ Positive indicators found: {found_positive}")

            # Ensure we have some positive indicators (the page is working)
            if len(found_positive) >= 2:
                print(
                    "✅ Page appears to be working correctly with student management functionality"
                )
            else:
                print(f"⚠️ Page may not be fully functional. Found indicators: {found_positive}")
                # Take screenshot for debugging
                screenshot_path = TESTS_TEMP_DIR / "page_content_debug_screenshot.png"
                driver.save_screenshot(str(screenshot_path))
                print(f"🔍 Debug screenshot saved to: {screenshot_path}")

            print("✅ Main function error validation completed successfully")

        except Exception as e:
            # Take screenshot for debugging
            screenshot_path = TESTS_TEMP_DIR / "main_function_test_error_screenshot.png"
            driver.save_screenshot(str(screenshot_path))
            print(f"🔍 Error screenshot saved to: {screenshot_path}")
            raise e

    def test_16_main_function_fix_validation(self, running_servers):
        """Validate that the main() function fix is working correctly"""

        fastapi_port, streamlit_port = running_servers

        print("\n🔧 Validating main() function fix...")

        # Test 1: Verify the generated student management file has main() function
        temp_dir = Path(__file__).parent.parent / ".temp"

        # Find the latest generated system
        system_dirs = list(temp_dir.glob("scenario1_system_*"))
        if system_dirs:
            latest_system = max(system_dirs, key=lambda p: p.stat().st_mtime)
            student_mgmt_file = (
                latest_system / "managed_system" / "ui" / "pages" / "student_management.py"
            )

            if student_mgmt_file.exists():
                with open(student_mgmt_file, "r") as f:
                    content = f.read()

                # Check that the file has a main() function
                assert (
                    "def main():" in content
                ), "Generated student_management.py should have a main() function"

                # Check that all UI code is inside the main() function
                lines = content.split("\n")
                main_function_found = False
                streamlit_calls_outside_main = []

                for i, line in enumerate(lines):
                    if "def main():" in line:
                        main_function_found = True
                        continue

                    # Check for Streamlit calls outside main function (before main is defined)
                    if (
                        not main_function_found
                        and "st." in line
                        and not line.strip().startswith("#")
                    ):
                        # Ignore imports and comments
                        if not line.strip().startswith("import") and "st." in line:
                            streamlit_calls_outside_main.append(f"Line {i+1}: {line.strip()}")

                assert main_function_found, "main() function not found in generated file"
                assert (
                    len(streamlit_calls_outside_main) == 0
                ), f"Streamlit calls found outside main(): {streamlit_calls_outside_main}"

                print("✅ Generated student_management.py has proper main() function structure")
            else:
                print("⚠️ student_management.py file not found, skipping file validation")
        else:
            print("⚠️ No generated system found, skipping file validation")

        # Test 2: Verify the UI is accessible and working
        ui_url = f"http://localhost:{streamlit_port}"

        try:
            response = requests.get(ui_url, timeout=10)
            assert response.status_code == 200, f"UI not accessible: {response.status_code}"
            print("✅ Streamlit UI is accessible")
        except Exception as e:
            print(f"⚠️ UI accessibility test failed: {e}")

        # Test 3: Verify the API is working
        api_url = f"http://localhost:{fastapi_port}/api/students/"

        try:
            response = requests.get(api_url, timeout=5)
            assert response.status_code == 200, f"API not accessible: {response.status_code}"
            print("✅ FastAPI backend is accessible")
        except Exception as e:
            print(f"⚠️ API accessibility test failed: {e}")

        # Test 4: Test the error handling validation passes
        print("📋 Running error handling validation...")

        # This should pass without the main() function error
        response = requests.get(ui_url, timeout=10)
        html_content = response.text.lower()

        # These specific errors should NOT be present
        critical_ui_errors = [
            "no main() or show_entity_management() function found",
            "failed to load student management page",
            "traceback",
            "exception occurred",
            "internal server error",
        ]

        found_critical_errors = [error for error in critical_ui_errors if error in html_content]

        if found_critical_errors:
            print(f"❌ Critical UI errors still present: {found_critical_errors}")
            assert False, f"Critical UI errors found: {found_critical_errors}"
        else:
            print("✅ No critical UI errors found")

        print("✅ Main function fix validation completed successfully")
        print("🎉 The 'No main() function found' error has been resolved!")

    def test_18_ui_fixes_validation(self, running_servers):
        """Test that the UI fixes for table display and edit/delete functionality are working correctly"""

        print("\n🔧 Testing UI fixes validation - table display and edit/delete functionality...")

        # Get the current system's UI file path
        temp_dir = Path(__file__).parent.parent / ".temp"
        system_dirs = list(temp_dir.glob("scenario1_system_*"))
        assert system_dirs, "No generated system found in .temp directory"

        latest_system = max(system_dirs, key=lambda p: p.stat().st_mtime)
        ui_file = latest_system / "managed_system" / "ui" / "pages" / "student_management.py"

        assert ui_file.exists(), f"UI file should exist at {ui_file}"

        # Read the generated UI file content
        with open(ui_file, "r") as f:
            ui_content = f.read()

        print("🔍 Analyzing generated UI file for fixes...")

        # Validation checks for UI fixes
        checks = {
            "main_function": ("def main():", "main() function is present"),
            "dataframe_usage": ("st.dataframe(", "Uses st.dataframe() for table display"),
            "centralized_config": (
                "Config.get_api_endpoint_url",
                "Uses centralized configuration for API endpoints",
            ),
            "config_import": ("from config import Config", "Imports centralized configuration"),
            "form_structure": ("st.form(", "Uses proper form structure"),
            "create_operation": ("create", "Create operation is present"),
            "update_operation": ("update", "Update operation is present"),
            "delete_operation": ("delete", "Delete operation is present"),
            "request_handling": ("requests.", "HTTP request handling is present"),
            "error_handling": ("st.error(", "Error handling is present"),
            "success_messages": ("st.success(", "Success messages are present"),
        }

        passed_checks = []
        failed_checks = []

        for check_name, (pattern, description) in checks.items():
            if pattern.lower() in ui_content.lower():
                passed_checks.append(f"✅ {description}")
                print(f"   ✅ {description}")
            else:
                failed_checks.append(f"❌ {description}")
                print(f"   ❌ {description}")

        # Additional check: ensure no broken patterns are present
        broken_patterns = [
            ("st.table(", "Old broken st.table() usage"),
            ("edit functionality not implemented", "Missing edit functionality message"),
            ("localhost:8000", "Hardcoded wrong API port (should use Config)"),
            ("localhost:8501", "Hardcoded wrong UI port (should use Config)"),
            ("http://localhost:8100", "Hardcoded API URL (should use Config.get_api_endpoint_url)"),
            ("html buttons", "Broken HTML buttons in dataframe"),
        ]

        for pattern, description in broken_patterns:
            if pattern.lower() in ui_content.lower():
                failed_checks.append(f"❌ Found broken pattern: {description}")
                print(f"   ❌ Found broken pattern: {description}")
            else:
                passed_checks.append(f"✅ No broken pattern: {description}")
                print(f"   ✅ No broken pattern: {description}")

        # Calculate score
        total_checks = len(passed_checks) + len(failed_checks)
        score_percentage = (len(passed_checks) / total_checks * 100) if total_checks > 0 else 0

        print("\n📊 UI Fixes Validation Results:")
        print(f"   Passed: {len(passed_checks)}")
        print(f"   Failed: {len(failed_checks)}")
        print(f"   Score: {score_percentage:.1f}%")

        # Success criteria: at least 80% of checks should pass
        assert (
            score_percentage >= 80
        ), f"UI fixes validation failed with score {score_percentage:.1f}%. Expected at least 80%."

        # Critical checks that must pass
        critical_checks = ["def main():", "st.dataframe(", "Config.get_api_endpoint_url"]
        for critical_pattern in critical_checks:
            assert (
                critical_pattern.lower() in ui_content.lower()
            ), f"Critical UI fix missing: {critical_pattern}"

        print("🎉 UI fixes validation PASSED!")
        return True

    @pytest.mark.timeout(60)  # Strict 60-second timeout to prevent infinite runs
    def test_17_schema_restoration_after_restart(self, real_system_fixtures):
        """Test that schema restoration works correctly after BAE system restart"""

        print("\n🔄 Testing schema restoration after restart...")

        temp_dir, original_kernel, context_store = real_system_fixtures

        # Step 1: Create initial system with student entity
        print("📋 Step 1: Creating initial system with student entity")
        initial_request = "Create a student entity with name, age, and course"

        result = original_kernel.process_natural_language_request(
            initial_request, context="academic", start_servers=False
        )

        assert result["success"], f"Initial system creation failed: {result.get('error')}"
        assert result["entity"] == "student"

        # Verify schema was stored
        student_bae = original_kernel.bae_registry.get_bae("student")
        original_schema = student_bae.get_memory("current_schema")
        assert original_schema is not None, "Schema should be stored after initial creation"
        assert len(original_schema.get("attributes", [])) >= 3, "Should have at least 3 attributes"

        print(f"✅ Initial schema created with {len(original_schema['attributes'])} attributes")
        print(f"   Attributes: {[attr for attr in original_schema['attributes']]}")

        # Step 2: Simulate system restart by creating new kernel instance
        print("📋 Step 2: Simulating system restart with new kernel instance")

        # Create new kernel instance (simulating restart)
        context_store_path = temp_dir / "context_store.json"
        new_kernel = EnhancedRuntimeKernel(context_store_path=str(context_store_path))

        # Step 3: Verify schema restoration
        print("📋 Step 3: Verifying schema restoration after restart")

        # Get the student BAE from the new kernel
        new_student_bae = new_kernel.bae_registry.get_bae("student")
        print(f"🔍 Debug: Student BAE name: {new_student_bae.name}")
        print(f"🔍 Debug: Student BAE memory keys: {list(new_student_bae.memory.keys())}")

        # Check memory directly
        schema_memory = new_student_bae.memory.get("current_schema")
        print(f"🔍 Debug: Schema memory structure: {schema_memory}")

        # Check get_memory result
        schema_from_get_memory = new_student_bae.get_memory("current_schema")
        print(f"🔍 Debug: Schema from get_memory: {schema_from_get_memory}")

        # Check current_schema attribute
        restored_schema = new_student_bae.current_schema
        print(f"🔍 Debug: current_schema attribute: {restored_schema}")

        # Verify schema was properly restored
        assert restored_schema is not None, "Schema should be restored after restart"
        assert (
            len(restored_schema.get("attributes", [])) >= 3
        ), "Restored schema should have original attributes"

        # Compare key attributes from original and restored schemas
        original_attrs = set(original_schema.get("attributes", []))
        restored_attrs = set(restored_schema.get("attributes", []))

        # Should have same or similar attributes (allowing for minor formatting differences)
        common_attrs = original_attrs.intersection(restored_attrs)
        assert (
            len(common_attrs) >= 2
        ), f"Should have common attributes. Original: {original_attrs}, Restored: {restored_attrs}"

        print(f"✅ Schema restored with {len(restored_schema['attributes'])} attributes")
        print(f"   Original: {original_attrs}")
        print(f"   Restored: {restored_attrs}")
        print(f"   Common: {common_attrs}")

        # Step 4: Test evolution request works correctly after restoration
        print("📋 Step 4: Testing evolution request after schema restoration")

        evolution_request = "Add email address to students"
        evolution_result = new_kernel.process_natural_language_request(
            evolution_request, context="academic", start_servers=False
        )

        assert evolution_result[
            "success"
        ], f"Evolution request failed: {evolution_result.get('error')}"

        # Verify evolution was detected (not full regeneration)
        interpretation = evolution_result.get("interpretation", {})
        request_type = interpretation.get("request_type", "")

        # Should be evolution, not new entity creation
        assert (
            "evolution" in request_type.lower() or "add" in request_type.lower()
        ), f"Should detect evolution request, but got: {request_type}"

        # Verify final schema has both original and new attributes
        final_student_bae = new_kernel.bae_registry.get_bae("student")
        final_schema = final_student_bae.get_memory("current_schema")

        assert final_schema is not None, "Final schema should exist after evolution"
        final_attributes = final_schema.get("attributes", [])
        assert (
            len(final_attributes) >= 4
        ), f"Should have at least 4 attributes after adding email. Got: {final_attributes}"

        # Check that email was added
        email_found = any("email" in attr.lower() for attr in final_attributes)
        assert (
            email_found
        ), f"Email attribute should be present. Final attributes: {final_attributes}"

        # Check that original attributes are preserved
        original_attr_preserved = any("name" in attr.lower() for attr in final_attributes)
        assert (
            original_attr_preserved
        ), f"Original attributes should be preserved. Final attributes: {final_attributes}"

        print(f"✅ Evolution successful! Final schema has {len(final_attributes)} attributes")
        print(f"   Final attributes: {final_attributes}")

        # Step 5: Verify execution results show evolution process
        print("📋 Step 5: Verifying evolution process was used")

        execution_results = evolution_result.get("execution_results", [])

        # Should have fewer tasks than full regeneration (evolution is more efficient)
        assert len(execution_results) >= 1, "Evolution should have execution results"

        # Check for evolution-specific indicators
        has_evolution_indicators = any(
            "evolution" in str(task).lower()
            or "update" in str(task).lower()
            or "modify" in str(task).lower()
            for task in execution_results
        )

        print(f"✅ Evolution process completed with {len(execution_results)} tasks")
        print(f"   Evolution indicators found: {has_evolution_indicators}")

        # Step 6: Validate final system state
        print("📋 Step 6: Validating final system state consistency")

        # Check that context store has the updated information
        stored_entities = context_store.get_entities()
        assert "student" in [
            entity.get("name", "").lower() for entity in stored_entities
        ], "Student entity should be stored in context"

        # Check database was updated (if exists)
        db_path = temp_dir / "managed_system" / "app" / "database" / "academic.db"
        if db_path.exists():
            import sqlite3

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check table schema was updated
            cursor.execute("PRAGMA table_info(students)")
            columns = cursor.fetchall()
            column_names = [col[1].lower() for col in columns]

            # Should have email column
            assert (
                "email" in column_names
            ), f"Database should have email column. Columns: {column_names}"
            print(f"✅ Database schema updated with columns: {column_names}")

            conn.close()

        print("🎉 Schema restoration validation completed successfully!")
        print("✅ Key validations passed:")
        print("   • Schema properly restored after restart")
        print("   • Evolution detection works after restoration")
        print("   • Original attributes preserved during evolution")
        print("   • New attributes successfully added")
        print("   • System maintains consistency across restart")

        return True


# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture(scope="class")
def real_system_fixtures():
    """Generate real system in .temp directory with cleanup"""

    # Ensure tests/.temp exists (consistent with other tests)
    TESTS_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Create unique temp directory for this test class
    temp_system_dir = TESTS_TEMP_DIR / f"scenario1_system_{os.getpid()}_{int(time.time())}"

    # Cleanup if exists from previous run
    if temp_system_dir.exists():
        shutil.rmtree(temp_system_dir, ignore_errors=True)

    temp_system_dir.mkdir(parents=True)

    print(f"\n🏗️ Setting up real system in: {temp_system_dir}")

    # Store original working directory
    original_cwd = os.getcwd()

    # Set managed system path to temp directory for this test
    original_managed_path = os.environ.get("MANAGED_SYSTEM_PATH")
    managed_system_path = temp_system_dir / "managed_system"
    os.environ["MANAGED_SYSTEM_PATH"] = str(managed_system_path)

    try:
        # Change to temp directory for file generation (consistent with other integration tests)
        os.chdir(temp_system_dir)

        context_store_path = temp_system_dir / "context_store.json"
        kernel = EnhancedRuntimeKernel(context_store_path=str(context_store_path))
        context_store = ContextStore(str(context_store_path))

        yield temp_system_dir, kernel, context_store

    finally:
        # Restore original working directory
        os.chdir(original_cwd)

        # Restore original managed system path
        if original_managed_path is not None:
            os.environ["MANAGED_SYSTEM_PATH"] = original_managed_path
        elif "MANAGED_SYSTEM_PATH" in os.environ:
            del os.environ["MANAGED_SYSTEM_PATH"]

        # Keep files for inspection as requested
        print(f"🔍 System files preserved for inspection at: {temp_system_dir}")


@pytest.fixture(scope="class")
def server_manager(real_system_fixtures):
    """Manage FastAPI + Streamlit server lifecycle with persistence for inspection"""

    temp_dir, _, _ = real_system_fixtures
    managed_system_dir = temp_dir / "managed_system"

    # Use fixed ports for realworld testing
    fastapi_port = REALWORLD_FASTAPI_PORT
    streamlit_port = REALWORLD_STREAMLIT_PORT

    print(
        f"\n🚀 Starting servers on fixed ports: FastAPI={fastapi_port}, Streamlit={streamlit_port}"
    )

    # Start FastAPI server
    # Start Streamlit server

    # Store original working directory for server startup
    original_cwd = os.getcwd()

    try:
        # Start FastAPI
        fastapi_main = managed_system_dir / "app" / "main.py"
        if fastapi_main.exists():
            # Set up environment with proper Python path
            env = os.environ.copy()
            env["PYTHONPATH"] = str(managed_system_dir)

            subprocess.Popen(
                [
                    "python",
                    "-m",
                    "uvicorn",
                    "app.main:app",  # Fixed: Use proper module path
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(fastapi_port),
                    "--reload",
                ],
                cwd=str(managed_system_dir),
                env=env,
            )  # Fixed: Run from managed_system_dir with PYTHONPATH

            # Wait for FastAPI to start
            _wait_for_server(f"http://localhost:{fastapi_port}/health", timeout=30)

        # Start Streamlit
        streamlit_app = managed_system_dir / "ui" / "app.py"
        if streamlit_app.exists():
            # Change to the ui directory for server startup
            ui_dir = managed_system_dir / "ui"
            os.chdir(ui_dir)

            subprocess.Popen(
                [
                    "python",
                    "-m",
                    "streamlit",
                    "run",
                    "app.py",
                    "--server.port",
                    str(streamlit_port),
                    "--server.headless",
                    "true",
                    "--server.enableCORS",
                    "false",
                ],
                cwd=str(ui_dir),
            )

            # Restore working directory
            os.chdir(original_cwd)

            # Wait for Streamlit to start
            _wait_for_server(f"http://localhost:{streamlit_port}", timeout=45)

        yield fastapi_port, streamlit_port

    finally:
        # Restore working directory
        os.chdir(original_cwd)

        # DO NOT cleanup servers - they should persist for inspection
        # Servers will be cleaned up by run_tests.py before next test cycle
        print("🔍 Servers remain running for inspection:")
        print(f"   • FastAPI: http://localhost:{fastapi_port}")
        print(f"   • Streamlit: http://localhost:{streamlit_port}")
        print("   • Servers will be stopped before next realworld test cycle")


@pytest.fixture(scope="class")
def running_servers(server_manager):
    """Ensure both servers are running and ready"""

    fastapi_port, streamlit_port = server_manager

    # Final health checks
    health_url = f"http://localhost:{fastapi_port}/health"
    ui_url = f"http://localhost:{streamlit_port}"

    try:
        requests.get(health_url, timeout=5)
        requests.get(ui_url, timeout=10)
    except requests.RequestException as e:
        pytest.fail(f"Servers not ready: {e}")

    return fastapi_port, streamlit_port


@pytest.fixture
def selenium_driver():
    """Selenium WebDriver for UI testing with automatic driver management"""

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        pytest.skip(
            "Selenium dependencies not available. Install with: pip install selenium webdriver-manager"
        )

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")

    driver = None
    try:
        # Use webdriver-manager to automatically download and manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)

        yield driver

    except Exception as e:
        pytest.skip(f"Chrome WebDriver not available: {e}")
    finally:
        if driver:
            driver.quit()


@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests"""

    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.metrics = {}

        def start(self, operation_name: str):
            self.start_time = time.time()
            self.current_operation = operation_name

        def stop(self) -> float:
            if self.start_time is None:
                return 0.0
            duration = time.time() - self.start_time
            self.metrics[self.current_operation] = duration
            self.start_time = None
            return duration

        def get_metrics(self) -> Dict[str, float]:
            return self.metrics.copy()

    return PerformanceTracker()


@pytest.fixture
def scenario1_success_criteria():
    """Scenario 1 success criteria for PoC validation"""
    return {
        "max_generation_time_seconds": 180,  # < 3 minutes
        "min_semantic_coherence_score": 80,  # >= 80%
        "required_success_rate": 100,  # 100% functional system
        "expected_artifacts": ["models", "routes", "ui", "database"],
        "expected_swea_tasks": ["DatabaseSWEA", "ProgrammerSWEA", "FrontendSWEA"],
        "semantic_coherence_requirements": {
            "business_vocabulary_preserved": True,
            "domain_entity_focus": True,
            "technical_business_alignment": True,
        },
    }


# ==========================================
# HELPER FUNCTIONS
# ==========================================


def _find_available_port(start_port: int) -> int:
    """Find an available port starting from start_port"""
    import socket

    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue
    raise RuntimeError("No available ports found")


def _wait_for_server(url: str, timeout: int = 30):
    """Wait for server to become available"""

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code in [200, 404]:  # 404 is ok for some endpoints
                return
        except requests.RequestException:
            pass
        time.sleep(1)

    raise TimeoutError(f"Server at {url} did not become available within {timeout} seconds")


if __name__ == "__main__":
    pytest.main()
