# Integration Tests for Template-Based Generation

This directory contains integration tests for the 001-performance-optimization feature, specifically User Story 1 (US1): Template-Based Code Generation.

## Test Files

### test_template_generation.py
Integration tests validating the end-to-end template generation workflow:
- **TestTemplateGeneratedStudentEntity**: Tests template-based generation for standard CRUD entities
- **TestTemplateFallbackOnCustomLogic**: Tests LLM fallback for entities with custom logic
- **TestCodeQualityValidation**: Validates generated code meets quality standards
- **TestPerformanceTargets**: Validates performance targets (<15s, <2000 tokens)

## Prerequisites

### 1. OpenAI API Key
Integration tests make real API calls to OpenAI. You must set the `OPENAI_API_KEY` environment variable:

```bash
# Option 1: Export in shell
export OPENAI_API_KEY=your_api_key_here

# Option 2: Create .env file from template
cp env.template .env
# Edit .env and set OPENAI_API_KEY=your_key
```

### 2. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Running Tests

### Run all integration tests:
```bash
pytest tests/integration/test_template_generation.py -v
```

### Run specific test class:
```bash
pytest tests/integration/test_template_generation.py::TestTemplateGeneratedStudentEntity -v
```

### Run specific test:
```bash
pytest tests/integration/test_template_generation.py::TestTemplateGeneratedStudentEntity::test_student_entity_is_standard -v
```

### Run with coverage:
```bash
pytest tests/integration/test_template_generation.py --cov=baes --cov-report=html
```

## Test Coverage

**T030: Template-Generated Student Entity**
- ✅ Entity classification (standard vs custom)
- ✅ Backend code generation with templates
- ✅ Database schema generation with templates
- ✅ Frontend UI generation with templates
- ✅ Integration test generation with templates
- ✅ Full CRUD performance validation (<60s for 4 artifacts)

**T031: Template Fallback on Custom Logic**
- ✅ Complex entity detection (computed properties, many-to-many, validation, state machines)
- ✅ LLM fallback for complex entities
- ✅ Custom logic classification reasons

**Code Quality Validation**
- ✅ Valid Python syntax
- ✅ Valid SQL schema
- ✅ PEP 8 conventions
- ✅ Token usage estimation

## Performance Targets

| Metric | Target | Validation |
|--------|--------|------------|
| Generation Time (single artifact) | <15s | ✅ Tested per SWEA |
| Total CRUD Time (4 artifacts) | <60s | ✅ Tested end-to-end |
| Token Usage | <2000 | ✅ Estimated |
| Test Pass Rate | 100% | ✅ All assertions |

## Expected Results

When running with a valid API key:
- All tests should pass
- Performance targets should be met
- Generated code should be syntactically valid
- Template system should handle both standard and custom entities

## Troubleshooting

### Error: "The api_key client option must be set"
- Ensure OPENAI_API_KEY is set in environment or .env file
- Check that .env file is in project root if using dotenv

### Error: "Template not found"
- Ensure all templates exist in baes/templates/ directory
- Check template paths match TemplateRegistry configuration

### Slow test execution
- Integration tests make real API calls and may take 30-60 seconds
- Use `-k "specific_test"` to run individual tests during development
- Consider mocking OpenAI calls for faster unit testing

## Notes

- Integration tests are **NOT** run by default in CI/CD (require API key)
- Use unit tests (tests/unit/) for fast, offline validation
- Integration tests validate real-world behavior with actual LLM calls
- Manual testing (T032) should be performed before merging to main
