# 🧪 BAE Test Suite

Comprehensive test suite for the BAE (Business Autonomous Entities) system following Python testing best practices.

**⚠️ IMPORTANT: The actual working tests are located in `bae_academic_system/tests/`, not in this root `tests/` directory.**

## 📁 Test Structure

```
bae_academic_system/
├── tests/                         # Main test directory (working tests)
│   ├── conftest.py               # Shared fixtures and configuration
│   ├── __init__.py               # Package initialization
│   │
│   ├── unit/                     # Unit tests for individual components
│   │   ├── agents/               # Agent component tests
│   │   │   ├── test_base_agent.py     # Base agent functionality
│   │   │   └── test_student_bae.py    # Student BAE domain entity tests
│   │   ├── core/                 # Core system tests
│   │   │   └── test_context_store.py  # Context store and domain knowledge
│   │   └── llm/                  # LLM integration tests
│   │       └── test_openai_client.py  # OpenAI GPT-4o-mini client tests
│   │
│   ├── integration/              # Integration tests
│   │   ├── bae_swea/            # BAE-SWEA interaction tests
│   │   └── end_to_end/          # Complete workflow tests
│   │
│   └── scenarios/                # Proof-of-concept scenario tests
│       ├── test_scenario1.py     # Initial System Generation (main)
│       └── test_scenario1_legacy.py  # Original test file (backup)
│
├── run_tests.py                  # Test runner script
├── pytest.ini                   # Pytest configuration
└── requirements.txt              # Testing dependencies
```

**Note**: This root `tests/` directory contains documentation but the actual working tests are in `bae_academic_system/tests/`.

## 🎯 Test Categories

### Unit Tests (`@pytest.mark.unit`)
Test individual components in isolation with mocked dependencies:
- **OpenAI Client**: LLM integration, domain entity responses, semantic coherence validation
- **Context Store**: Domain knowledge preservation, agent memory, evolution tracking
- **Base Agent**: Memory management, task handling, interaction logging
- **Student BAE**: Domain entity representation, business request interpretation, schema generation

### Integration Tests (`@pytest.mark.integration`)
Test component interactions and workflows:
- **BAE-SWEA Coordination**: How Business Autonomous Entities coordinate Software Engineering Agents
- **End-to-End Workflows**: Complete system generation pipelines

### Scenario Tests (`@pytest.mark.scenario`)
Validate proof-of-concept scenarios as defined in the thesis:
- **Scenario 1**: Initial System Generation (< 3 minutes, 100% functional)
- **Scenario 2**: Runtime Evolution (< 2 minutes, zero downtime) 
- **Scenario 3**: Reusability and Configuration (< 1 minute, >80% reuse)

### Performance Tests (`@pytest.mark.performance`)
Validate timing and efficiency requirements:
- Generation time benchmarks
- Semantic coherence scoring
- Resource usage monitoring

## 🚀 Running Tests

**⚠️ IMPORTANT: All commands must be executed from the `bae_academic_system/` directory:**

```bash
cd bae_academic_system
```

### Using the Test Runner (Recommended)
```bash
# Run all tests
./run_tests.py all

# Run specific test categories
./run_tests.py unit              # Unit tests only
./run_tests.py integration       # Integration tests only  
./run_tests.py scenario          # All scenario tests
./run_tests.py scenario1         # Just Scenario 1

# Performance and quick runs
./run_tests.py performance       # Performance tests only
./run_tests.py quick            # Fast unit tests (excludes slow tests)

# With options
./run_tests.py unit --verbose --coverage
./run_tests.py all --parallel 4
```

### Using pytest directly
```bash
# All tests (from bae_academic_system/ directory)
python -m pytest tests/

# By marker
python -m pytest -m unit tests/
python -m pytest -m scenario tests/
python -m pytest -m "not slow" tests/

# Specific files
python -m pytest tests/unit/agents/test_student_bae.py
python -m pytest tests/scenarios/test_scenario1.py

# With coverage
python -m pytest --cov=. --cov-report=html tests/
```

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery patterns
- Marker definitions
- Output formatting
- Warning filters

### Shared Fixtures (`conftest.py`)
- **mock_openai_client**: Mocked OpenAI GPT-4o-mini client
- **temp_database_path**: Temporary storage for tests
- **clean_test_environment**: Cleanup before/after tests
- **performance_tracker**: Timing and metrics collection
- **scenario success criteria**: Validation thresholds

## 📊 Success Criteria

### Scenario 1: Initial System Generation
- ⏱️ Generation time: < 180 seconds (3 minutes)
- ✅ Success rate: 100% functional system
- 🧠 Semantic coherence: ≥ 80%
- 🤖 Required agents: StudentBAE, ProgrammerSWEA, FrontendSWEA, DatabaseSWEA

### Scenario 2: Runtime Evolution
- ⏱️ Evolution time: < 120 seconds (2 minutes)
- 🔄 Zero downtime required
- 💾 Data preservation: 100%
- 🧠 Semantic coherence: ≥ 85%

### Scenario 3: Reusability
- ⏱️ Adaptation time: < 60 seconds (1 minute)
- 🔄 Reuse percentage: ≥ 80%
- 🎯 Context adaptation: Required

## 🎨 Test Patterns

### Domain Entity Focus
Tests validate that:
- Student BAE operates as autonomous domain entity representative
- Business vocabulary is preserved throughout technical artifacts
- Semantic coherence is maintained between domain concepts and code
- Domain knowledge enables cross-organizational reusability

### Mocking Strategy
- **OpenAI API**: Mocked to avoid API costs and ensure deterministic results
- **File I/O**: Temporary files for database operations
- **External Dependencies**: Isolated testing environment

### Performance Testing
- Execution time tracking with `performance_tracker` fixture
- Memory usage monitoring (planned)
- API call optimization validation (planned)

## 🔍 Test Examples

### Unit Test Example
```python
@pytest.mark.unit
def test_student_bae_domain_entity_representation(mock_openai_client):
    student_bae = StudentBAE()
    
    result = student_bae.handle_task("generate_schema", {
        "attributes": ["name: str", "registration: str"],
        "context": "academic"
    })
    
    assert result["entity"] == "Student"
    assert "business_rules" in result
```

### Scenario Test Example
```python
@pytest.mark.scenario
@pytest.mark.slow
def test_scenario1_complete_workflow(mock_openai_client, performance_tracker, scenario1_success_criteria):
    performance_tracker.start("scenario1")
    
    # Test complete workflow...
    
    execution_time = performance_tracker.stop()
    assert execution_time < scenario1_success_criteria["max_generation_time_seconds"]
```

## 🐛 Debugging Tests

### Verbose Output
```bash
./run_tests.py unit --verbose
pytest -v tests/unit/
```

### Failed Test Investigation
```bash
# Run only failed tests
pytest --lf

# Stop on first failure
pytest -x

# Debug mode
pytest --pdb
```

### Coverage Analysis
```bash
./run_tests.py all --coverage
# View coverage report at htmlcov/index.html
```

## 📈 Continuous Integration

Tests are designed to run in CI/CD environments:
- No external API dependencies (mocked)
- Deterministic results
- Clear success/failure criteria
- Performance regression detection

## 🔄 Adding New Tests

### For New Components
1. Create test file in appropriate directory (`tests/unit/`, `tests/integration/`)
2. Follow naming convention: `test_component_name.py`
3. Use appropriate markers (`@pytest.mark.unit`, etc.)
4. Add fixtures to `conftest.py` if needed

### For New Scenarios
1. Add test to `tests/scenarios/`
2. Define success criteria in `conftest.py`
3. Use `@pytest.mark.scenario` marker
4. Include performance validation

## 🎯 Quality Standards

All tests must:
- ✅ Have clear, descriptive names
- ✅ Include docstrings explaining purpose
- ✅ Use appropriate fixtures for setup/teardown
- ✅ Assert business logic, not just technical functionality
- ✅ Validate domain entity autonomy and semantic coherence
- ✅ Run independently (no test interdependencies)
- ✅ Complete within reasonable time limits

---

**This test suite validates the BAE architecture thesis proposition that domain entities can function as autonomous agents within the system while maintaining semantic coherence and enabling cross-organizational knowledge reuse.** 