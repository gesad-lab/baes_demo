# Tasks: BAES Framework Performance Optimization

**Input**: Design documents from `/specs/001-performance-optimization/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Integration tests are MANDATORY per BAES Constitution Principle IV. Unit tests included for complex logic components (cache, validation rules, template registry).

**Organization**: Tasks grouped by user story to enable independent implementation and testing. Each story can be delivered as an MVP increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story this task belongs to (US1-US6)
- File paths included for clarity

## Path Conventions

BAES Framework structure at repository root:
- Generator components: `baes/core/`, `baes/swea_agents/`, `baes/domain_entities/`, `baes/standards/`, `baes/utils/`, `baes/templates/`
- Tests: `tests/unit/`, `tests/integration/`
- Database: `database/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency installation

- [X] T001 Install new dependencies: Jinja2>=3.1.0 and NLTK>=3.8.0 in requirements.txt and pyproject.toml
- [X] T002 Download NLTK data: wordnet and omw-1.4 for cache normalization (one-time setup script)
- [X] T003 [P] Create templates directory structure: baes/templates/backend/, baes/templates/database/, baes/templates/frontend/, baes/templates/tests/
- [X] T004 [P] Create persistent cache database directory: database/recognition_cache.db (initialize empty SQLite DB with schema)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create OptimizationMetrics data class in baes/utils/optimization_metrics.py with PerformanceMetrics and AggregatedMetrics
- [X] T006 [P] Create CompressedStandards base class in baes/standards/compressed_standards.py with token counting
- [X] T007 [P] Add optimization configuration flags to config.py: enable_cache, enable_templates, enable_confidence_validation, enable_parallel_execution, enable_smart_retry
- [X] T008 Setup structured logging for optimization events in baes/utils/presentation_logger.py (cache operations, template usage, validation methods)
- [X] T009 Document constitutional compliance for optimizations in docs/PERFORMANCE_OPTIMIZATION.md (PEP 8, DRY, fail-fast, generator-first fixes)
- [X] T010 Add metrics collection hooks in baes/core/enhanced_runtime_kernel.py for request_id, timestamps, token counts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Template-Based CRUD Generation (Priority: P1) 🎯 MVP

**Goal**: Replace repetitive LLM calls with Jinja2 templates for standard CRUD patterns, achieving 40-60% token savings and 50-60% time savings

**Independent Test**: Generate simple Student entity with name/enrollment_date/gpa. System should complete in <15s using <2000 tokens with template-generated code passing all integration tests.

### Implementation for US1

- [X] T011 [P] [US1] Create TemplateMetadata and TemplateInput/TemplateOutput data classes in baes/utils/template_registry.py
- [X] T012 [P] [US1] Implement TemplateRegistry class with Jinja2 environment configuration (trim_blocks, lstrip_blocks, keep_trailing_newline, autoescape=False)
- [X] T013 [P] [US1] Add custom Jinja2 filters to TemplateRegistry: snake_case(), pascal_case(), python_type() for code generation
- [X] T014 [P] [US1] Implement template selection logic in TemplateRegistry.select_template() based on entity_type, swea_type, requires_custom_logic
- [X] T015 [P] [US1] Implement template rendering in TemplateRegistry.render_template() with error handling and fallback_used flag
- [X] T016 [P] [US1] Create backend model template: baes/templates/backend/model_crud.py.j2 (SQLAlchemy model + Pydantic schema)
- [X] T017 [P] [US1] Create backend routes template: baes/templates/backend/routes_crud.py.j2 (FastAPI CRUD endpoints)
- [X] T018 [P] [US1] Create database schema template: baes/templates/database/schema_crud.sql.j2 (CREATE TABLE with indexes)
- [X] T019 [P] [US1] Create frontend form template: baes/templates/frontend/streamlit_form.py.j2 (create/update form)
- [X] T020 [P] [US1] Create frontend table template: baes/templates/frontend/streamlit_table.py.j2 (list view with pagination)
- [X] T021 [P] [US1] Create integration test template: baes/templates/tests/integration_crud.py.j2 (full CRUD lifecycle test)
- [X] T022 [US1] Add template detection logic to baes/domain_entities/base_bae.py._detect_custom_logic() checking for: basic attribute types only, no computed properties, no complex validation, simple relationships
- [X] T023 [US1] Modify BackendSWEA.generate_api_code() in baes/swea_agents/backend_swea.py to use TemplateRegistry with LLM fallback
- [X] T024 [US1] Modify DatabaseSWEA.generate_schema() in baes/swea_agents/database_swea.py to use TemplateRegistry with LLM fallback
- [X] T025 [US1] Modify FrontendSWEA.generate_page_code() in baes/swea_agents/frontend_swea.py to use TemplateRegistry with LLM fallback
- [X] T026 [US1] Modify TestSWEA.generate_test_code() in baes/swea_agents/test_swea.py to use TemplateRegistry with LLM fallback
- [X] T027 [US1] Update OptimizationMetrics collection in all SWEAs to log template_used, template_id, fallback_used

### Tests for US1 (MANDATORY)

- [X] T028 [P] [US1] Unit test for TemplateRegistry in tests/unit/test_template_registry.py: template selection, rendering, custom filters
- [X] T029 [P] [US1] Unit test for custom logic detection in tests/unit/test_base_bae.py: standard vs custom classification
- [X] T030 [US1] Integration test for template-generated Student entity in tests/integration/test_template_generation.py: full CRUD, code quality, test pass rate
- [X] T031 [US1] Integration test for template fallback on custom logic in tests/integration/test_template_generation.py: complex entity triggers LLM
- [ ] T032 [US1] Manual testing: Generate 5 different standard CRUD entities, verify <15s, <2000 tokens, 100% test pass rate

---

## Phase 4: User Story 2 - Rule-Based Code Validation (Priority: P1) 🎯 MVP

**Goal**: Use confidence-based hybrid validation (regex/AST for 70-80% of cases, LLM for uncertain), reducing token consumption by 20-30%

**Independent Test**: Generate standard entity, monitor TechLeadSWEA review. Template code should pass regex confident_approval in <100ms with 0 tokens (60-70% cases).

### Implementation for US2

- [X] T033 [P] [US2] Create ValidationRule and ValidationResult data classes in baes/standards/validation_rules.py
- [X] T034 [P] [US2] Implement base validation logic: validate_code() with regex pattern matching and confidence classification
- [X] T035 [P] [US2] Define backend validation rules in baes/standards/validation_rules.py: context_manager, http_status, error_handling, response_models, dependency_injection
- [X] T036 [P] [US2] Define frontend validation rules in baes/standards/validation_rules.py: form_validation, error_display, success_feedback
- [X] T037 [P] [US2] Define database validation rules in baes/standards/validation_rules.py: primary_key, indexes, constraints
- [X] T038 [P] [US2] Define test validation rules in baes/standards/validation_rules.py: integration_lifecycle, error_cases, cleanup
- [X] T039 [P] [US2] Implement AST-based structural validation for type hints, docstrings, PEP 8 naming in baes/standards/validation_rules.py
- [X] T040 [P] [US2] Implement rule management operations: add_rule(), update_rule(), disable_rule(), list_rules() in baes/standards/validation_rules.py
- [X] T041 [US2] Modify TechLeadSWEA.evaluate_artifact() in baes/swea_agents/techlead_swea.py to use confidence-based validation with ValidationRule
- [X] T042 [US2] Add LLM fallback logic in TechLeadSWEA when ValidationResult.overall_outcome == "uncertain"
- [X] T043 [US2] Add confident rejection feedback with line numbers from ValidationResult.rule_results to TechLeadSWEA response
- [X] T044 [US2] Update OptimizationMetrics to log validation_outcome (confident_approval/confident_rejection/uncertain), validation_llm_called

### Tests for US2 (MANDATORY)

- [X] T045 [P] [US2] Unit test for ValidationRule in tests/unit/test_validation_rules.py: pattern matching, confidence classification, rule catalog
- [X] T046 [P] [US2] Unit test for AST structural validation in tests/unit/test_validation_rules.py: type hints, docstrings, PEP 8
- [ ] T047 [US2] Integration test for confidence-based validation in tests/integration/test_confidence_validation.py: confident_approval rate 60-70%, confident_rejection with feedback, uncertain triggers LLM
- [ ] T048 [US2] Integration test for validation accuracy in tests/integration/test_confidence_validation.py: no false approvals on violating code, approval rate ≥85%
- [ ] T049 [US2] Manual testing: Generate 10 entities (5 template, 5 custom), verify confident validation rate 70-80%, <100ms validation time

---

## Phase 5: User Story 3 - Entity Recognition Caching (Priority: P2)

**Goal**: Implement two-tier cache (in-memory + SQLite persistent) for entity recognition, achieving 10-15% per-session savings and 60%+ cross-session hit rate

**Independent Test**: Make same request twice ("create student system"), restart BAES, make again. First: OpenAI call. Second: memory cache (<1ms, 0 tokens). Third: persistent cache (<50ms, 0 tokens).

### Implementation for US3

- [X] T050 [P] [US3] Create CachedRecognition data class in baes/core/recognition_cache.py with all required attributes
- [X] T051 [P] [US3] Create SQLite schema in baes/core/recognition_cache.py: recognition_cache table with indexes, WAL mode, user_version pragma
- [X] T052 [P] [US3] Implement cache normalization in RecognitionCache._normalize_key() using NLTK lemmatization and stop word removal
- [X] T053 [P] [US3] Implement in-memory cache with LRU eviction (max 100 entries) using OrderedDict in RecognitionCache
- [X] T054 [P] [US3] Implement SQLite persistent cache with ACID transactions in RecognitionCache
- [X] T055 [P] [US3] Implement cache_write() in RecognitionCache: immediate memory write, async SQLite write
- [X] T056 [P] [US3] Implement cache_read() in RecognitionCache: check memory first, then persistent, promote cold→hot on hit
- [X] T057 [P] [US3] Implement cache_cleanup() in RecognitionCache: remove entries older than 30 days from SQLite
- [X] T058 [P] [US3] Implement cache_stats() in RecognitionCache: hit rate, sizes, oldest/newest entries
- [X] T059 [P] [US3] Implement cache_invalidate() in RecognitionCache: by entity name or clear all
- [X] T060 [P] [US3] Add thread-safety with threading.Lock() for in-memory cache operations
- [X] T061 [US3] Integrate RecognitionCache into EntityRecognizer in baes/core/entity_recognizer.py: cache_read before OpenAI, cache_write after
- [X] T062 [US3] Add cache versioning and migration detection in RecognitionCache: check cache_version on read, invalidate if mismatch
- [X] T063 [US3] Add entity schema evolution detection in baes/domain_entities/base_bae.py: invalidate cache when attributes change
- [X] T064 [US3] Update OptimizationMetrics to log cache_hit (bool), cache_hit_time (ms), cache_tier (memory/persistent)

### Tests for US3

- [ ] T065 [P] [US3] Unit test for RecognitionCache in tests/unit/test_recognition_cache.py: normalization, LRU eviction, SQLite persistence
- [ ] T066 [P] [US3] Unit test for cache thread-safety in tests/unit/test_recognition_cache.py: concurrent reads/writes
- [ ] T067 [US3] Integration test for cache persistence in tests/integration/test_cache_persistence.py: write, restart, read (simulate framework restart)
- [ ] T068 [US3] Integration test for cache hit rates in tests/integration/test_cache_persistence.py: 40%+ in-session, 60%+ cross-session over 20 requests
- [ ] T069 [US3] Integration test for cache invalidation in tests/integration/test_cache_persistence.py: entity schema evolution triggers invalidation
- [ ] T070 [US3] Manual testing: Generate 20 entities with 50% duplicates, restart, generate 10 more, verify hit rates and <50ms cold cache access

---

## Phase 6: User Story 4 - Compressed Prompt Context (Priority: P2)

**Goal**: Reduce prompt sizes by 15-20% using compressed standards (20-30 lines vs 467 lines) while maintaining 85%+ approval rate

**Independent Test**: Compare prompt sizes before/after. Backend generation should reduce from ~2000 tokens to ~1600 tokens with approval rate ≥85%.

### Implementation for US4

- [X] T071 [P] [US4] Create BackendCompressedStandard in baes/standards/compressed_standards.py: context manager, HTTP status codes, error handling, PEP 8 essentials (~25 lines)
- [X] T072 [P] [US4] Create DatabaseCompressedStandard in baes/standards/compressed_standards.py: primary keys, indexes, constraints, schema patterns (~20 lines)
- [X] T073 [P] [US4] Create FrontendCompressedStandard in baes/standards/compressed_standards.py: form validation, error display, success feedback (~20 lines)
- [X] T074 [P] [US4] Create TestCompressedStandard in baes/standards/compressed_standards.py: lifecycle testing, error cases, cleanup patterns (~25 lines)
- [X] T075 [P] [US4] Add token counting utility in baes/standards/compressed_standards.py using tiktoken for OpenAI models
- [X] T076 [US4] Modify BackendSWEA to use compressed standards in prompts with fallback to full standards if approval rate <85%
- [ ] T077 [US4] Modify DatabaseSWEA to use compressed standards in prompts with fallback to full standards if approval rate <85%
- [ ] T078 [US4] Modify FrontendSWEA to use compressed standards in prompts with fallback to full standards if approval rate <85%
- [ ] T079 [US4] Modify TestSWEA to use compressed standards in prompts with fallback to full standards if approval rate <85%
- [ ] T080 [US4] Add approval rate monitoring per SWEA in baes/utils/optimization_metrics.py: track compressed vs full standards usage
- [ ] T081 [US4] Update OptimizationMetrics to log standards_type (compressed/full), prompt_token_count

### Tests for US4

- [ ] T082 [P] [US4] Unit test for compressed standards in tests/unit/test_compressed_standards.py: token counts, content validation, all SWEAs covered
- [ ] T083 [US4] Integration test for compressed prompt quality in tests/integration/test_compressed_prompts.py: generate 10 entities, verify approval rate ≥85%
- [ ] T084 [US4] Integration test for token reduction in tests/integration/test_compressed_prompts.py: compare prompt sizes, verify 15-20% reduction
- [ ] T085 [US4] Manual testing: Generate 5 entities with compressed standards, compare TechLeadSWEA approval rate vs baseline (should be within 5%)

---

## Phase 7: User Story 5 - Parallel SWEA Execution (Priority: P3)

**Goal**: Run independent SWEA tasks concurrently (Database + Frontend) reducing wall-clock time by 15-25% without changing token consumption

**Independent Test**: Generate complete system, measure timeline. Database (8s) + Frontend (10s) should overlap, completing in ~10s total instead of 18s sequential.

### Implementation for US5

- [ ] T086 [P] [US5] Create TaskDependencyGraph data class in baes/core/enhanced_runtime_kernel.py with task dependencies
- [ ] T087 [P] [US5] Implement dependency analysis in EnhancedRuntimeKernel._build_dependency_graph(): identify hard dependencies (Backend→Database, Tests→All)
- [ ] T088 [P] [US5] Implement topological sort in EnhancedRuntimeKernel._topological_sort(): group tasks into execution waves
- [ ] T089 [US5] Implement parallel execution in EnhancedRuntimeKernel.execute_parallel_tasks() using asyncio.gather() for each wave
- [ ] T090 [US5] Add parallel execution error handling: cancel remaining tasks on failure, propagate exception with context
- [ ] T091 [US5] Convert SWEA execute methods to async: BackendSWEA, DatabaseSWEA, FrontendSWEA, TestSWEA (maintain sync compatibility)
- [ ] T092 [US5] Update OptimizationMetrics to log parallel_execution_enabled (bool), sequential_time (estimated), parallel_time (actual), parallel_savings_pct

### Tests for US5

- [ ] T093 [P] [US5] Unit test for TaskDependencyGraph in tests/unit/test_enhanced_runtime_kernel.py: dependency detection, topological sort
- [ ] T094 [US5] Integration test for parallel execution in tests/integration/test_parallel_execution.py: verify Database+Frontend overlap, time reduction 15-25%
- [ ] T095 [US5] Integration test for dependency respect in tests/integration/test_parallel_execution.py: Backend waits for Database, Tests wait for all
- [ ] T096 [US5] Integration test for parallel failure handling in tests/integration/test_parallel_execution.py: one task fails, others cancelled gracefully
- [ ] T097 [US5] Manual testing: Generate 3 complete systems, measure sequential vs parallel timing, verify token consumption unchanged

---

## Phase 8: User Story 6 - Smart Retry with Targeted Fixes (Priority: P3)

**Goal**: Apply targeted patches for single-issue rejections instead of full regeneration, reducing retry token consumption by 10-15%

**Independent Test**: Force validation failure (remove @contextmanager), observe retry. System should patch only that issue using ~500 tokens instead of 2000 for full regeneration.

### Implementation for US6

- [ ] T098 [P] [US6] Implement TechLeadSWEA feedback analysis in baes/swea_agents/techlead_swea.py: determine if single localized issue vs multiple/structural
- [ ] T099 [P] [US6] Create targeted patch generation logic using AST manipulation in baes/utils/code_patcher.py: add decorator, fix status code, add error handling
- [ ] T100 [P] [US6] Implement patch application in baes/utils/code_patcher.py: modify code section, preserve formatting, validate syntax
- [ ] T101 [US6] Add retry decision logic to all SWEAs: if feedback indicates targeted fix feasible, use patch; else full regeneration
- [ ] T102 [US6] Add fallback to full regeneration if patch application fails (parse error, semantic mismatch)
- [ ] T103 [US6] Update OptimizationMetrics to log retry_method (targeted_patch/full_regen), retry_tokens, retry_success

### Tests for US6

- [ ] T104 [P] [US6] Unit test for feedback analysis in tests/unit/test_techlead_swea.py: single issue vs multiple, localized vs structural
- [ ] T105 [P] [US6] Unit test for code patcher in tests/unit/test_code_patcher.py: AST manipulation, patch application, syntax validation
- [ ] T106 [US6] Integration test for targeted retry in tests/integration/test_smart_retry.py: single issue triggers patch, verify token reduction 50%+
- [ ] T107 [US6] Integration test for fallback behavior in tests/integration/test_smart_retry.py: complex issues trigger full regeneration
- [ ] T108 [US6] Manual testing: Force 5 different validation failures, verify targeted patches applied when feasible, full regen otherwise

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, documentation, and performance validation

- [ ] T109 [P] Create comprehensive quickstart guide in docs/PERFORMANCE_OPTIMIZATION_QUICKSTART.md (already exists at specs/001-performance-optimization/quickstart.md, copy to docs/)
- [ ] T110 [P] Create API documentation for new components in docs/API.md: TemplateRegistry, RecognitionCache, ValidationRule, OptimizationMetrics
- [ ] T111 [P] Update main README.md with performance optimization overview and links to quickstart
- [ ] T112 [P] Add troubleshooting guide for common issues: low cache hit rate, low template usage, low confident validation rate
- [ ] T113 Add configuration examples in examples/optimization_config.py: enable/disable individual optimizations, adjust thresholds
- [ ] T114 [P] Create metrics export CLI in baes/utils/metrics_export.py: export aggregated metrics to CSV for analysis
- [ ] T115 [P] Add monitoring dashboard script in examples/metrics_dashboard.py: visualize cache hit rates, token savings, approval rates
- [ ] T116 Integration test for end-to-end performance targets in tests/integration/test_performance_targets.py: <15s, <2000 tokens per standard entity, 100% test pass rate
- [ ] T117 Integration test for constitutional compliance in tests/integration/test_constitutional_compliance.py: all optimizations maintain PEP 8, DRY, fail-fast
- [ ] T118 Integration test for backward compatibility in tests/integration/test_backward_compatibility.py: existing generated systems unaffected
- [ ] T119 Manual testing: Full benchmark suite with 20 diverse entities, verify all success criteria SC-001 through SC-016
- [ ] T120 Performance regression testing: Compare baseline vs optimized on identical workload, document improvements in PERFORMANCE_RESULTS.md

---

## Dependencies & Execution Strategy

### User Story Dependencies

```
Phase 1 (Setup)  →  Phase 2 (Foundational)  →  Phase 3-8 (User Stories - can run in parallel)  →  Phase 9 (Polish)
                                                      ↓
                            ┌─────────────────────────┼─────────────────────────┐
                            ↓                         ↓                         ↓
                    US1 (Template Gen)        US2 (Validation)        US3 (Cache)
                    INDEPENDENT ✓             INDEPENDENT ✓           INDEPENDENT ✓
                    T011-T032                 T033-T049               T050-T070
                            
                            ↓                         ↓                         ↓
                    US4 (Compressed)          US5 (Parallel)          US6 (Retry)
                    INDEPENDENT ✓             INDEPENDENT ✓           INDEPENDENT ✓
                    T071-T085                 T086-T097               T098-T108
```

**Story Independence**: Each user story (US1-US6) can be implemented and tested independently. No inter-story dependencies exist.

**Recommended Implementation Order**:
1. **P1 Stories FIRST** (US1 + US2): 70%+ combined savings, highest ROI
2. **P2 Stories SECOND** (US3 + US4): 15-20% additional savings
3. **P3 Stories OPTIONAL** (US5 + US6): 10-15% additional savings, lower priority

### Parallel Execution Opportunities

Within each phase, tasks marked **[P]** can be executed in parallel:

**Phase 2 (Foundational)**: T006, T007 can run parallel to T005  
**Phase 3 (US1)**: T011-T021 (all template/registry work) can run in parallel  
**Phase 4 (US2)**: T033-T040 (validation rule definitions) can run in parallel  
**Phase 5 (US3)**: T050-T060 (cache implementation) can run in parallel  
**Phase 6 (US4)**: T071-T075 (compressed standards) can run in parallel  
**Phase 7 (US5)**: T086-T088 (dependency graph) can run in parallel  
**Phase 8 (US6)**: T098-T100 (patch logic) can run in parallel  
**Phase 9 (Polish)**: T109-T115 (documentation and tools) can run in parallel

### MVP Definition

**Minimum Viable Product = Phase 1 + Phase 2 + Phase 3 (US1) + Phase 4 (US2)**

This delivers the highest-impact optimizations:
- Template-based generation (40-60% token, 50-60% time savings)
- Confidence-based validation (20-30% token savings)
- Combined: ~70% total savings achieving target <15s, <2000 tokens

US3-US6 are incremental enhancements that can be added post-MVP.

---

## Task Summary

**Total Tasks**: 120  
**By Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 6 tasks
- Phase 3 (US1 - Template Gen): 22 tasks (17 implementation + 5 tests)
- Phase 4 (US2 - Validation): 17 tasks (12 implementation + 5 tests)
- Phase 5 (US3 - Cache): 21 tasks (15 implementation + 6 tests)
- Phase 6 (US4 - Compressed): 15 tasks (11 implementation + 4 tests)
- Phase 7 (US5 - Parallel): 12 tasks (7 implementation + 5 tests)
- Phase 8 (US6 - Retry): 11 tasks (6 implementation + 5 tests)
- Phase 9 (Polish): 12 tasks

**By Priority**:
- P1 (MVP - US1+US2): 39 tasks (70%+ savings)
- P2 (US3+US4): 36 tasks (15-20% additional savings)
- P3 (US5+US6): 23 tasks (10-15% additional savings)
- Setup/Polish: 22 tasks

**Parallelizable Tasks**: 58 tasks marked [P] (48% of total)

**Estimated Effort** (based on complexity):
- Setup/Foundational: 1-2 days
- US1 (Template Gen): 3-4 days
- US2 (Validation): 2-3 days
- US3 (Cache): 3-4 days
- US4 (Compressed): 1-2 days
- US5 (Parallel): 2-3 days
- US6 (Retry): 2-3 days
- Polish/Testing: 2-3 days

**Total Estimated**: 16-24 days (single developer), 8-12 days (parallel team of 2-3)

---

## Implementation Strategy

### Incremental Delivery Approach

1. **Sprint 1 (MVP)**: Phase 1 + Phase 2 + US1 + US2
   - Deliverable: Template-based generation + confidence validation
   - Target: 70%+ combined savings
   - Duration: 7-10 days

2. **Sprint 2 (Enhanced)**: US3 + US4
   - Deliverable: Persistent cache + compressed prompts
   - Target: Additional 15-20% savings
   - Duration: 4-6 days

3. **Sprint 3 (Advanced)**: US5 + US6 + Polish
   - Deliverable: Parallel execution + smart retry + documentation
   - Target: Final 10-15% savings + production readiness
   - Duration: 5-8 days

### Quality Gates

Before merging each sprint:
- [ ] All integration tests passing (100% pass rate)
- [ ] TechLeadSWEA approval rate ≥85% for that sprint's features
- [ ] Performance targets met for that sprint (measured via OptimizationMetrics)
- [ ] Constitutional compliance validated (PEP 8, DRY, fail-fast)
- [ ] Manual testing completed per sprint checklist

### Rollback Strategy

Each optimization has independent configuration flag:
- `enable_cache=False`: Revert to OpenAI calls for recognition
- `enable_templates=False`: Revert to LLM generation
- `enable_confidence_validation=False`: Revert to full LLM validation
- `enable_parallel_execution=False`: Revert to sequential execution
- `enable_smart_retry=False`: Revert to full regeneration

This enables A/B testing and quick rollback if issues detected.

---

## Success Validation

After completing all phases, validate against spec.md Success Criteria:

**Performance Targets**:
- [ ] SC-001: Standard entity generation <15s (vs 40s baseline)
- [ ] SC-002: Token consumption <2000 per entity (vs 8000 baseline)
- [ ] SC-003: Template usage 80%+ for standard entities
- [ ] SC-004: Cache hit rate 40%+ in-session, 60%+ cross-session
- [ ] SC-005: Confident validation 70-80% (0 tokens, <100ms)

**Quality Assurance**:
- [ ] SC-006: Template code 100% integration test pass rate
- [ ] SC-007: TechLeadSWEA approval rate ≥85%
- [ ] SC-008: Constitutional compliance 100%
- [ ] SC-009: Compressed prompts maintain quality (approval ≥85%)

**Operational**:
- [ ] SC-010: Metrics logged for 100% of requests
- [ ] SC-011: Parallel execution 15-25% time reduction
- [ ] SC-012: Smart retry 50%+ token reduction on retries
- [ ] SC-013: 50+ concurrent requests, <10MB memory overhead

**Benchmarking**:
- [ ] SC-014: Match or exceed competitor frameworks in token efficiency
- [ ] SC-015: End-to-end generation <30s (vs 60-90s baseline)
- [ ] SC-016: Cost per entity reduced 70%+ (OpenAI pricing)
