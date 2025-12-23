# BAES Framework Constitution
<!--
  Sync Impact Report:
  - Version Change: 1.0.0 → 1.1.0
  - Amendment Date: 2025-12-23
  - Modified Principles:
    * Principle IV: Test-First Development - Simplified to focus on integration tests and manual testing
    * Principle VI: Error Handling & Fail-Fast - Added explicit fail-fast guidance, removed fallback patterns
  - Added Sections: None
  - Removed Sections: None
  - Templates Status:
    ✅ plan-template.md - Updated to reflect simplified testing gates
    ✅ spec-template.md - Compatible (no changes needed)
    ✅ tasks-template.md - Updated to reflect integration-first testing approach
  - Follow-up TODOs: None
-->

## Core Principles

### I. Domain-Driven Autonomy (NON-NEGOTIABLE)

**Business Autonomous Entities (BAEs) MUST maintain domain knowledge ownership and semantic coherence.**

- Each BAE represents a single domain entity (Student, Course, Teacher, etc.) and MUST preserve business vocabulary and semantic relationships
- BAEs MUST interpret natural language business requests using LLM-powered domain knowledge
- BAEs MUST generate SWEA coordination plans that maintain domain integrity across technical layers
- Context Store MUST persist domain knowledge, business vocabulary, and entity relationships across sessions
- Entity recognition MUST route requests to appropriate BAE based on domain semantics, not keyword matching alone

**Rationale**: The core innovation of BAES Framework is adaptive system generation through domain entity autonomy. Breaking this principle undermines the entire architectural paradigm and research thesis foundation.

### II. PEP 8 Compliance & Python Standards (NON-NEGOTIABLE)

**All Python code MUST strictly adhere to PEP 8 style guidelines and Python best practices.**

- Code MUST follow PEP 8 naming conventions: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants
- Line length MUST NOT exceed 100 characters (per BaseStandards.QUALITY_REQUIREMENTS)
- Indentation MUST use 4 spaces (no tabs)
- Type hints MUST be provided for all function parameters and return types (Python 3.11+ style)
- Docstrings MUST be provided for all public methods using Google style format
- Import statements MUST be organized: standard library, third-party, local (with blank lines between groups)

**Rationale**: PEP 8 ensures code consistency, readability, and maintainability across all contributors. Type hints enable better IDE support and catch errors early. This is fundamental to professional Python development.

### III. DRY Principle - Don't Repeat Yourself (NON-NEGOTIABLE)

**Code duplication MUST be eliminated through abstraction, inheritance, and reusable components.**

- Common patterns MUST be extracted into base classes (e.g., `BaseSWEA`, `BaseBAE`, `BaseStandards`)
- Shared logic MUST be moved to utility modules (`baes/utils/`)
- Standards and validation rules MUST be centralized (e.g., `baes/standards/`)
- Duplicated functionality across SWEAs MUST be refactored into shared parent classes or mixins
- Configuration and constants MUST be defined once and imported (not duplicated)

**Rationale**: DRY reduces maintenance burden, eliminates inconsistencies, and makes the codebase more robust. When a bug is fixed or feature is added in one place, all consumers benefit. This is critical for long-term maintainability.

### IV. Integration Testing & Manual Validation (MANDATORY)

**Features MUST be validated through integration tests and manual verification before being considered complete.**

- Integration tests MUST validate complete user workflows in `tests/integration/`
- Integration tests MUST be written to validate critical business scenarios and BAE-SWEA coordination
- Manual testing MUST verify user experience and edge cases before release
- Unit tests are OPTIONAL - use only when they add clear value for complex logic or algorithms
- Focus on testing behavior and outcomes, not implementation details
- TestSWEA SHOULD generate integration tests for SWEA-generated code when appropriate
- All changes MUST be validated manually in addition to automated tests

**Rationale**: Integration tests validate real system behavior and catch issues that unit tests miss. Manual testing ensures user experience quality. Over-testing with exhaustive unit tests creates maintenance burden without proportional value. Focus testing effort where it matters most.

### V. Observability & Structured Logging (MANDATORY)

**All components MUST implement comprehensive logging, metrics tracking, and monitoring.**

- Logger setup MUST follow pattern: `logger = logging.getLogger(__name__)`
- All exceptions MUST be logged with `logger.error(f"Error: {e}")` before re-raising or handling
- LLM requests MUST be logged to `logs/llm_requests/` with request/response pairs and timestamps
- Metrics tracking MUST capture: retry patterns, failure rates, execution times, SWEA feedback scores
- CSV-based feedback analytics MUST be maintained for TechLeadSWEA review loops
- Presentation logging MUST separate user-facing output from debug/system logs

**Rationale**: BAES Framework generates code dynamically via LLM. Observability is critical for debugging, understanding system behavior, improving prompts, and validating that generated systems meet requirements.

### VI. Error Handling & Fail-Fast (MANDATORY)

**All potentially failing operations MUST have explicit error handling. Fail fast rather than masking errors with fallbacks.**

- Try/except blocks MUST wrap: file I/O, LLM API calls, database operations, external service calls
- Exceptions MUST be logged before handling or re-raising
- **Fail-Fast**: When an error occurs, FAIL IMMEDIATELY with clear error message - do NOT use fallbacks that hide problems
- Retry patterns MUST be bounded (MaxRetriesReachedError for graceful failure after retries exhausted)
- Error messages MUST be informative and actionable (what failed, why, what to try next)
- Validation MUST occur at boundaries: user input, LLM responses, generated code, API endpoints
- Schema validation MUST enforce JSON response structure from LLM (using Pydantic models)
- **NO silent fallbacks**: If validation fails, raise exception - don't substitute default values that mask issues

**Rationale**: Fail-fast exposes problems immediately during development, making bugs easier to diagnose and fix. Silent fallbacks and error masking create hard-to-debug issues where the system appears to work but produces incorrect results. It's better to fail loudly than to fail silently.

### VII. Semantic Coherence & Validation (MANDATORY)

**All LLM-generated content MUST be validated for semantic coherence with domain requirements.**

- LLM responses MUST be validated against expected JSON schemas using Pydantic models
- Generated code MUST be validated against BaseStandards, BackendStandards, DatabaseStandards, FrontendStandards, TestStandards
- SWEA coordination plans MUST be validated for completeness before execution
- Business vocabulary MUST be preserved across BAE operations and SWEA generations
- TechLeadSWEA MUST review all generated artifacts and provide feedback for quality assurance

**Rationale**: LLMs can generate plausible but incorrect outputs. Semantic validation ensures generated systems align with business requirements, follow project standards, and maintain domain integrity.

## Technology Standards

### Language & Framework Requirements

- **Python Version**: Python 3.11+ (required for modern type hints and performance)
- **Primary Framework**: OpenAI SDK (>=1.3.7) for LLM integration
- **Web Framework**: FastAPI for backend APIs (generated by BackendSWEA)
- **Database**: SQLite for persistence (generated by DatabaseSWEA)
- **UI Framework**: Streamlit for frontend interfaces (generated by FrontendSWEA)
- **Validation**: Pydantic (>=2.5.0) for data models and schema validation
- **Configuration**: python-dotenv (>=1.0.0) for environment variable management

### Testing Requirements

- **Testing Framework**: pytest (>=7.4.3) with async support
- **Test Organization**: Separate directories for integration tests (`tests/integration/`), optional unit tests (`tests/unit/`)
- **Test Focus**: Integration tests for user workflows and BAE-SWEA coordination; manual validation for UX
- **Test Execution**: Tests MUST run via `pytest` command with proper configuration (`pytest.ini`)
- **Coverage**: Focus on integration test coverage of critical paths, not code coverage percentage targets
- **Manual Testing**: All features MUST be manually validated before release

### Code Generation Standards

- **Standards Enforcement**: All generated code MUST pass validation against domain-specific standards classes
- **Template System**: Jinja2 templates for code generation patterns
- **Code Extraction**: Markdown-wrapped code blocks MUST be extracted cleanly (handle triple backticks)
- **Prompt Engineering**: LLM prompts MUST include relevant standards, examples, and constraints

## Development Workflow

### Feature Development Process

1. **Specification**: Create feature spec following `.specify/templates/spec-template.md`
2. **Planning**: Generate implementation plan following `.specify/templates/plan-template.md`
3. **Constitution Check**: Validate alignment with all core principles (gates must pass)
4. **Research**: Conduct technical research and document findings
5. **Design**: Define data models, APIs/contracts, and interaction flows
6. **Task Breakdown**: Generate task list following `.specify/templates/tasks-template.md`
7. **Implementation**: Build feature following plan with fail-fast error handling
8. **Integration Testing**: Write and run integration tests for critical workflows
9. **Manual Validation**: Test feature manually to verify user experience and edge cases
10. **Review**: TechLeadSWEA-style review for quality and standards compliance
11. **Integration**: Merge with validation that all tests pass and standards are met

### Code Review Requirements

- All code MUST pass PEP 8 linting (no violations)
- All functions MUST have type hints and docstrings
- All public APIs MUST have integration tests
- All generated code MUST pass domain-specific standards validation
- DRY violations MUST be refactored before merge
- Error handling MUST be comprehensive with logging

### Quality Gates

- **Pre-Commit**: Code MUST pass linting and formatting checks
- **Pre-Push**: All integration tests MUST pass
- **Pre-Merge**: Code review MUST confirm standards compliance, no DRY violations, fail-fast error handling
- **Manual Testing**: Feature MUST be manually validated before merge
- **Post-Merge**: Metrics tracking MUST show no regression in error rates or performance

## SWEA Agent Governance

### Agent Responsibilities

- **TechLeadSWEA**: Technical governance, code review, quality oversight, feedback coordination
- **BackendSWEA**: FastAPI route generation, Pydantic model creation, business logic implementation
- **DatabaseSWEA**: SQLite schema design, migration scripts, query optimization
- **FrontendSWEA**: Streamlit UI generation, form handling, data visualization
- **TestSWEA**: Test generation (unit, integration, validation), test execution coordination

### Agent Interaction Rules

- SWEAs MUST NOT duplicate functionality (DRY applies to agents too)
- SWEAs MUST follow base standards (BaseStandards) and domain-specific standards
- SWEAs MUST generate code that passes semantic coherence validation
- TechLeadSWEA MUST review all SWEA outputs and provide feedback via CSV analytics
- Feedback loops MUST be tracked and used to improve future generations

## Governance

### Constitution Authority

This constitution supersedes all other development practices, guidelines, or documentation. In case of conflict, constitutional principles take precedence. All pull requests, code reviews, and feature specifications MUST verify compliance with these principles.

### Amendment Process

1. Proposed amendments MUST be documented with justification and impact analysis
2. Amendments MUST follow semantic versioning:
   - **MAJOR**: Backward incompatible governance/principle removals or redefinitions
   - **MINOR**: New principle/section added or materially expanded guidance
   - **PATCH**: Clarifications, wording refinements, typo fixes
3. Amendments MUST be reviewed against dependent artifacts (templates, standards, docs)
4. Migration plan MUST be provided for breaking changes
5. All templates in `.specify/templates/` MUST be updated to reflect amendments

### Complexity Justification

When constitutional principles must be violated (e.g., DRY, PEP 8, Test-First), violations MUST be:
- Explicitly documented in plan.md Complexity Tracking section
- Justified with clear rationale (technical constraints, external dependencies, research exploration)
- Time-bound with refactoring plan to restore compliance
- Approved by technical governance (TechLeadSWEA-equivalent human review)

### Compliance Review

- Weekly: Review LLM request logs and metrics for standards compliance trends
- Per Feature: Validate constitution check gates before Phase 0 research and after Phase 1 design
- Per Release: Comprehensive audit of DRY violations, PEP 8 compliance, test coverage
- Continuous: Automated linting and testing in CI/CD pipeline

### Version History

- **1.0.0** (2025-12-23): Initial constitution ratified with 7 core principles, technology standards, SWEA governance, and development workflow
- **1.1.0** (2025-12-23): Amended to add fail-fast principle and simplify testing approach (integration-first with manual validation)

**Version**: 1.1.0 | **Ratified**: 2025-12-23 | **Last Amended**: 2025-12-23
