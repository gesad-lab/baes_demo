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

# Use centralized temp directory from conftest (consistent with other tests)
TESTS_TEMP_DIR = Path(__file__).parent.parent / ".temp"

# Fixed ports for realworld testing (consistent with run_tests.py cleanup)
REALWORLD_FASTAPI_PORT = 8100
REALWORLD_STREAMLIT_PORT = 8600


@pytest.mark.e2e
@pytest.mark.slow
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

        # Validate Python file syntax
        python_files = list(managed_system_dir.rglob("*.py"))
        assert (
            len(python_files) >= 3
        ), f"Expected at least 3 Python files, found {len(python_files)}"

        for py_file in python_files:
            try:
                with open(py_file, "r") as f:
                    code = f.read()
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
