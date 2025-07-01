# 🌍 Real-World Testing Guide for BAE Scenario 1

## Overview

This guide covers the comprehensive real-world testing implementation for **Scenario 1: Initial System Generation** that uses real OpenAI API calls, actual file generation, live servers, and complete CRUD validation.

---

## 🎯 **Testing Strategy**

### **Hybrid Approach**
- **Real Components**: OpenAI API, file generation, database, servers
- **Hybrid UI Validation**: Both HTTP testing and Selenium browser automation
- **Progressive Validation**: Modular tests that build upon each other

### **Test Categories**

#### **🔧 System Generation Tests**
1. **`test_01_system_generation_workflow`** - Complete end-to-end generation
2. **`test_02_generated_files_validation`** - File structure and syntax validation
3. **`test_03_database_creation_validation`** - Database schema verification

#### **🚀 Server Tests**
4. **`test_04_fastapi_server_startup`** - FastAPI server health and accessibility
5. **`test_05_streamlit_server_startup`** - Streamlit UI server validation

#### **🔌 API Functionality Tests**
6. **`test_06_api_crud_operations`** - Full CRUD operations testing
7. **`test_07_api_data_validation`** - Schema validation and error handling

#### **🖥️ UI Functionality Tests**
8. **`test_08_streamlit_basic_accessibility`** - HTTP-based UI validation
9. **`test_09_streamlit_student_creation_workflow`** ⚡ - Selenium form testing
10. **`test_10_streamlit_student_management_workflow`** ⚡ - Selenium management testing

#### **🔗 Integration Tests**
11. **`test_11_end_to_end_workflow_validation`** - Complete workflow integration
12. **`test_12_performance_and_success_criteria`** - PoC success criteria validation

⚡ = Requires Selenium browser automation

---

## 🏗️ **Test Infrastructure**

### **File Generation Location**
```
tests/.temp/
├── scenario1_system_<timestamp>/
│   ├── managed_system/
│   │   ├── app/
│   │   │   ├── models/
│   │   │   ├── routes/
│   │   │   ├── database/
│   │   │   └── main.py
│   │   └── ui/
│   │       ├── pages/
│   │       └── app.py
│   └── context_store.json
```

### **Server Management**
- **Dynamic Port Allocation**: Automatically finds available ports (8100+ for FastAPI, 8600+ for Streamlit)
- **Process Isolation**: Servers run in separate processes with proper cleanup
- **Health Checks**: Waits for servers to be ready before testing
- **Graceful Shutdown**: Terminates servers cleanly after tests

### **Database Testing**
- **Real SQLite Database**: Created in `.temp` directory
- **Schema Validation**: Verifies table structure matches generated models
- **Data Persistence**: Tests actual CRUD operations with real data
- **Preservation**: Database kept for inspection after tests

---

## 🔧 **Running Real-World Tests**

### **Prerequisites**
```bash
# Install required dependencies
pip install selenium webdriver-manager httpx

# Ensure OpenAI API key is set
export OPENAI_API_KEY="your-api-key-here"
```

### **Test Execution Commands**

#### **Complete Real-World Test Suite**
```bash
# Run all end-to-end tests (without Selenium)
python run_tests.py realworld

# Run complete suite including Selenium UI tests
python run_tests.py e2e

# Run only Scenario 1 real-world tests
python run_tests.py scenario1
```

#### **Specific Test Categories**
```bash
# Run only server and API tests
pytest -m "e2e" -k "server or api" tests/integration/

# Run only Selenium UI tests
python run_tests.py selenium

# Run with coverage reporting
python run_tests.py e2e --coverage
```

#### **Development & Debugging**
```bash
# Run single test with verbose output
pytest -v -s tests/integration/test_scenario1.py::TestScenario1RealWorld::test_01_system_generation_workflow

# Run without cleanup for inspection
pytest --pdb tests/integration/test_scenario1.py::TestScenario1RealWorld::test_02_generated_files_validation
```

---

## 🎭 **Selenium Browser Testing**

### **Selenium Setup**
- **Automatic Driver Management**: Uses `webdriver-manager` for ChromeDriver
- **Headless Mode**: Runs in background without GUI
- **Error Screenshots**: Saves screenshots on test failures
- **Configurable Options**: Optimized for CI/CD environments

### **UI Test Scenarios**

#### **Student Creation Workflow**
```python
# Tests form submission end-to-end
1. Navigate to Streamlit app
2. Fill student creation form
3. Submit form
4. Verify student appears in system
```

#### **Student Management Workflow**
```python
# Tests management interface
1. View student list/table
2. Navigate between different UI sections
3. Verify data display and accessibility
```

### **Selenium Test Markers**
```bash
# Run only Selenium tests
pytest -m selenium

# Skip Selenium tests
pytest -m "not selenium"

# Run Selenium tests with custom browser options
SELENIUM_HEADLESS=false pytest -m selenium
```

---

## 📊 **Success Criteria Validation**

### **Scenario 1 PoC Requirements**
The tests validate all Scenario 1 success criteria:

✅ **Generation Time**: < 3 minutes (180 seconds)
✅ **System Functionality**: 100% operational (API + UI + DB)
✅ **Semantic Coherence**: ≥80% business vocabulary preservation
✅ **SWEA Coordination**: DatabaseSWEA + ProgrammerSWEA + FrontendSWEA
✅ **File Generation**: Complete managed system structure

### **Performance Metrics**
```python
success_metrics = {
    "generation_time": execution_time,
    "semantic_coherence_score": validation_result["semantic_coherence_score"],
    "domain_entity_autonomy": True,
    "swea_coordination_successful": len(coordination_plan) >= 3,
    "business_vocabulary_preserved": validation_result["business_vocabulary_preserved"],
    "domain_knowledge_persisted": preserved_knowledge is not None,
}
```

---

## 🔍 **Debugging & Inspection**

### **Generated Files Inspection**
```bash
# Navigate to generated system
cd tests/.temp/scenario1_system_<timestamp>/managed_system/

# Check file structure
tree .

# Inspect generated code
cat app/models/student.py
cat app/routes/student_routes.py
cat ui/app.py
```

### **Database Inspection**
```bash
# Connect to generated database
sqlite3 tests/.temp/scenario1_system_<timestamp>/managed_system/app/database/baes_system.db

# View schema
.schema

# Check data
SELECT * FROM students;
```

### **Server Logs**
- **FastAPI**: Server process output shows request/response logs
- **Streamlit**: UI interaction logs and component rendering
- **Test Output**: Detailed progress and validation messages

### **Selenium Screenshots**
Failed Selenium tests automatically save screenshots:
```
tests/.temp/selenium_error_screenshot.png
tests/.temp/selenium_mgmt_error_screenshot.png
```

---

## ⚠️ **Known Limitations & Considerations**

### **OpenAI API Dependency**
- **Rate Limits**: May hit API rate limits with frequent testing
- **Cost**: Real API calls incur charges
- **Network**: Requires stable internet connection
- **Response Variability**: LLM responses may vary between runs

### **Server Management**
- **Port Conflicts**: Automatically finds available ports but may conflict with running services
- **Resource Usage**: Servers consume CPU/memory during tests
- **Cleanup**: Servers should terminate cleanly but may require manual cleanup if tests fail

### **Browser Testing**
- **ChromeDriver**: Requires compatible Chrome/Chromium installation
- **Headless Mode**: UI tests run in background, limited visual debugging
- **Platform Dependencies**: May behave differently across operating systems

### **File System**
- **Permissions**: Requires write access to `tests/.temp/` directory
- **Disk Space**: Generated systems may consume significant disk space
- **Cleanup**: Files preserved for inspection but should be cleaned periodically

---

## 🎯 **Integration with CI/CD**

### **GitHub Actions Configuration**
```yaml
- name: Run Real-World Tests
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    python run_tests.py realworld  # Skip Selenium in CI

- name: Run Selenium Tests (if needed)
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    sudo apt-get install -y chromium-browser
    python run_tests.py selenium
```

### **Environment Variables**
```bash
# Required
OPENAI_API_KEY=your-api-key

# Optional
SELENIUM_HEADLESS=true  # Force headless mode
TEST_TIMEOUT=300        # Test timeout in seconds
SKIP_SELENIUM=true      # Skip browser tests
```

---

## 📚 **Related Documentation**

- **[BAE Implementation Guide](BAE_IMPLEMENTATION_GUIDE.md)**: Core architecture details
- **[Proof of Concept](PROOF_OF_CONCEPT.md)**: Scenario 1 specifications
- **[Testing Automation](TESTING_AUTOMATION.md)**: General testing strategy
- **[Implementation Checklist](IMPLEMENTATION_CHECKLIST.md)**: Development milestones

---

**🎉 This real-world testing implementation provides comprehensive validation that the BAE architecture can autonomously generate complete, functional systems while maintaining semantic coherence between business vocabulary and technical artifacts - exactly as specified in the Scenario 1 proof of concept.**
