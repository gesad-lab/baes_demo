# Implementation Plan: BAES Framework Performance Optimization

**Branch**: `001-performance-optimization` | **Date**: December 23, 2025 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-performance-optimization/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature implements comprehensive performance optimizations to reduce LLM token consumption by 75% and execution time by 60% for standard CRUD entity generation. The primary technical approach consists of:

1. **Template-Based Generation (P1)**: Replace repetitive LLM calls with Jinja2 templates for standard CRUD patterns (models, routes, pages, schemas), falling back to LLM only for custom business logic
2. **Confidence-Based Validation (P1)**: Use regex/AST validation for confident approvals/rejections (70-80% of cases), deferring to LLM only for uncertain/ambiguous code
3. **Two-Tier Persistent Cache (P2)**: Implement in-memory hot cache + SQLite cold cache for entity recognition results, enabling cross-session benefit
4. **Compressed Prompts (P2)**: Reduce prompt sizes by 15-20% using condensed standards documents (20-30 lines vs 467 lines)
5. **Parallel Execution (P3)**: Run independent SWEA tasks concurrently using asyncio for 15-25% time savings
6. **Smart Retry (P3)**: Apply targeted patches for single-issue rejections instead of full regeneration

Target outcomes: Standard entity generation in <15 seconds (currently 40+), <2000 tokens (currently 8000+), maintaining 100% integration test pass rate and constitutional compliance.

## Technical Context

**Language/Version**: Python 3.11+ (required for modern type hints and performance)  
**Primary Dependencies**: 
- OpenAI SDK >=1.3.7 (LLM integration)
- Jinja2 >=3.1.0 (template engine for code generation)
- FastAPI (generated backend framework)
- Pydantic >=2.5.0 (validation)
- pytest >=7.4.3 (testing)

**Storage**: 
- SQLite for persistent entity recognition cache (`database/recognition_cache.db`)
- JSON for context store (`database/context_store.json`)
- SQLite for generated managed systems (`managed_system/app/database/baes_system.db`)

**Testing**: pytest with integration-first approach, manual validation mandatory  
**Target Platform**: Linux server (development), cross-platform Python 3.11+  
**Project Type**: Single project (framework enhancement) with generator components in `baes/` directory  
**Performance Goals**: 
- Token consumption: <2000 tokens per standard entity (currently 8000+) - 75% reduction
- Execution time: <15 seconds per entity generation (currently 40+) - 60% reduction
- Cache hit rate: 40%+ in-session, 60%+ cross-session
- Validation speed: <100ms for confident cases (70-80% of validations)

**Constraints**: 
- 100% constitutional compliance required (PEP 8, DRY, fail-fast, generator-first fixes)
- 100% integration test pass rate mandatory (no functional regressions)
- TechLeadSWEA approval rate ≥85% for template-generated code
- In-memory cache: 100 entry LRU limit, <10MB memory overhead
- Persistent cache: 30-day age cleanup, ACID transaction support
- Backward compatible: No breaking changes to managed_system structure

**Scale/Scope**: 
- 6 user stories (2 P1, 2 P2, 2 P3)
- 34 functional requirements across 6 optimization categories
- Core modifications to: EntityRecognizer, TechLeadSWEA, all SWEAs (Backend/Database/Frontend/Test), EnhancedRuntimeKernel
- New components: TemplateRegistry, RecognitionCache (two-tier), ValidationRule, CompressedStandards
- Estimated: ~2000 lines new code, ~1500 lines template content, 500 lines modified existing code

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Core Principle Compliance:**

- [x] **Domain-Driven Autonomy**: Feature enhances BAE/SWEA performance without changing domain knowledge ownership. Template-based generation preserves domain integrity by maintaining BAE interpretation for business rules while optimizing technical artifact generation.
- [x] **PEP 8 Compliance**: All new code (TemplateRegistry, RecognitionCache, ValidationRule) will adhere to snake_case naming, type hints, docstrings, 100 char lines. Templates generate PEP 8 compliant code.
- [x] **DRY Principle**: Template system inherently reduces duplication. New ValidationRule base class consolidates regex/AST patterns. CompressedStandards extracts common rules avoiding repetition across SWEAs.
- [x] **Integration Testing**: Integration tests will validate: template-generated code passes existing tests, cache persistence across restarts, confidence-based validation accuracy, end-to-end performance targets. Manual testing of cache hit rates and template quality required.
- [x] **Observability**: OptimizationMetrics tracks token consumption, cache hit rates, validation methods, parallel execution savings. Logging for: template vs LLM decisions, cache operations, confidence classifications, persistent cache corruption/migration events.
- [x] **Fail-Fast Error Handling**: Persistent cache corruption fails with clear error and fallback to OpenAI. Regex exceptions in validation trigger uncertain→LLM path (no silent fallbacks). Template application failures fall back to LLM with logged reason.
- [x] **Semantic Coherence**: Template-generated code validated by TechLeadSWEA using confidence-based approach. LLM validation for uncertain cases ensures semantic correctness. 85%+ approval rate target maintains quality.
- [x] **Generator-First Fixes**: All optimizations modify generator components (EntityRecognizer, SWEAs, standards). Templates become part of generator source. No managed_system patches. Template bugs fixed by updating template files in baes/.

**SWEA Governance (if applicable):**

- [x] SWEA responsibilities remain clear: Template application is new responsibility for all SWEAs, with explicit fallback to existing LLM generation for custom logic.
- [x] Generated code passes standards validation: Template-generated code designed to match constitutional patterns (context managers, HTTP codes, error handling).
- [x] TechLeadSWEA review enhanced with confidence-based validation: Confident cases use regex/AST (fast), uncertain cases use LLM (thorough), maintaining quality gates.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
baes/                                    # Generator components (source of truth)
├── core/
│   ├── enhanced_runtime_kernel.py      # [MODIFY] Add parallel execution support
│   ├── entity_recognizer.py            # [MODIFY] Add two-tier caching
│   └── recognition_cache.py            # [NEW] Two-tier cache implementation
├── swea_agents/
│   ├── techlead_swea.py                # [MODIFY] Add confidence-based validation
│   ├── backend_swea.py                 # [MODIFY] Add template-based generation
│   ├── database_swea.py                # [MODIFY] Add template-based generation
│   ├── frontend_swea.py                # [MODIFY] Add template-based generation
│   ├── test_swea.py                    # [MODIFY] Add template-based generation
│   └── base_swea.py                    # [MODIFY] Add template detection/application
├── standards/
│   ├── compressed_standards.py         # [NEW] Compressed prompt standards
│   └── validation_rules.py             # [NEW] Confidence-based validation patterns
├── templates/                           # [NEW] Jinja2 code generation templates
│   ├── backend/
│   │   ├── model.py.j2                 # Pydantic model template
│   │   └── routes.py.j2                # FastAPI CRUD routes template
│   ├── database/
│   │   └── schema.sql.j2               # SQLite schema template
│   ├── frontend/
│   │   └── page.py.j2                  # Streamlit page template
│   └── tests/
│       └── integration.py.j2           # Integration test template
├── utils/
│   ├── template_registry.py            # [NEW] Template management and retrieval
│   └── optimization_metrics.py         # [NEW] Performance tracking

database/
├── context_store.json                  # [EXISTING] Domain knowledge persistence
└── recognition_cache.db                # [NEW] Persistent entity recognition cache

tests/
├── integration/
│   ├── test_template_generation.py     # [NEW] Validate template-generated code
│   ├── test_cache_persistence.py       # [NEW] Validate cache across restarts
│   ├── test_confidence_validation.py   # [NEW] Validate confidence-based validation
│   └── test_performance_targets.py     # [NEW] Validate <15s, <2000 tokens targets
└── unit/
    ├── test_recognition_cache.py       # [NEW] Cache implementation unit tests
    ├── test_validation_rules.py        # [NEW] Validation rule unit tests
    └── test_template_registry.py       # [NEW] Template registry unit tests

specs/001-performance-optimization/     # This feature
├── plan.md                             # This file
├── research.md                         # [TO BE CREATED] Phase 0 output
├── data-model.md                       # [TO BE CREATED] Phase 1 output
├── quickstart.md                       # [TO BE CREATED] Phase 1 output
└── contracts/                          # [TO BE CREATED] Phase 1 output
```

**Structure Decision**: Single project structure maintained. All optimization components added to existing `baes/` generator source tree following constitutional principle VIII (Generator-First Fixes). New components organized by responsibility:
- Core (`baes/core/`): Cache and kernel enhancements  
- SWEA Agents (`baes/swea_agents/`): Template-based generation logic  
- Standards (`baes/standards/`): Validation and compressed standards  
- Templates (`baes/templates/`): Jinja2 code generation templates by artifact type  
- Utils (`baes/utils/`): Registry and metrics tracking  
- Tests (`tests/`): Integration tests mandatory, unit tests for complex logic

## Complexity Tracking

> **No constitutional violations requiring justification.**

All optimizations align with constitutional principles. The feature enhances performance without compromising domain-driven autonomy, code quality standards, or architectural integrity. Template-based generation is additive (fallback to LLM preserved), cache is transparent to domain logic, and validation confidence classification maintains quality gates.

---

## Phase 0: Research (COMPLETED)

✅ **Output**: [research.md](research.md)

**Research Questions Resolved:**
1. Jinja2 configuration for Python code generation → Custom filters + whitespace control
2. SQLite persistent cache schema design → WAL mode + composite indexes + version tracking
3. Regex patterns for confidence-based validation → Pattern catalog with uncertainty classification
4. Template detection heuristics → Attribute analysis + business rule complexity checks
5. Compressed standards content selection → 25 lines per SWEA type, essential rules only
6. Parallel execution dependency resolution → Topological sort into execution waves
7. Cache normalization preprocessing → NLTK lemmatization + stop word removal

**Key Decisions:**
- **Template Engine**: Jinja2 3.1+ with snake_case, pascal_case, python_type custom filters
- **Persistent Cache**: SQLite with WAL mode, composite indexes, schema versioning
- **Validation Patterns**: Regex for standard patterns, AST for structural checks, uncertainty triggers for LLM fallback
- **Template Detection**: Heuristic-based classification (basic types + simple rules = template-eligible)
- **Compressed Standards**: ~25 lines per SWEA, focusing on project-specific conventions
- **Parallel Execution**: Dependency graph with topological sort into waves
- **Cache Normalization**: NLTK WordNetLemmatizer with stop word removal

**Technology Stack Confirmed:**
- Jinja2 >=3.1.0 (template engine)
- NLTK >=3.8.0 (cache normalization)
- SQLite3 (built-in, persistent cache)
- asyncio (built-in, parallel execution)

---

## Phase 1: Design & Contracts (COMPLETED)

✅ **Outputs**: [data-model.md](data-model.md), [quickstart.md](quickstart.md), [contracts/](contracts/)

**Data Models Defined:**
1. **RecognitionCache**: Two-tier cache (in-memory + SQLite) with normalization and hit tracking
2. **ValidationRule**: Pattern-based validation rules with confidence classification
3. **TemplateRegistry**: Template metadata, selection, rendering, and versioning
4. **OptimizationMetrics**: Performance tracking for time, tokens, cache, templates, validation
5. **CompressedStandards**: Condensed coding standards for token-efficient prompts

**API Contracts Created:**
- [recognition-cache-api.md](contracts/recognition-cache-api.md): Cache read/write/cleanup/stats/invalidate operations
- [template-registry-api.md](contracts/template-registry-api.md): Template selection/rendering/registration/validation
- [validation-rule-api.md](contracts/validation-rule-api.md): Confidence-based code validation with rule management

**Design Highlights:**
- Two-tier cache: Hot (<1ms in-memory) + Cold (<50ms SQLite) with promotion on hit
- Template catalog: 7 initial templates (backend models/routes, database schema, frontend forms/tables, integration tests)
- Validation rules: 13 standard rules (backend: 5, frontend: 3, database: 3, test: 2) with confidence-based classification
- Metrics tracking: Real-time structured logs + aggregated CSV exports for analysis

**Developer Documentation:**
- [quickstart.md](quickstart.md): Installation, usage examples, configuration, monitoring, troubleshooting

---

## Post-Design Constitution Re-Evaluation

**Status**: ✅ **ALL PRINCIPLES PASS** (re-checked after design completion)

- [x] **Domain-Driven Autonomy**: Design preserves BAE domain interpretation layer. Templates operate at SWEA technical artifact level only. Business rule extraction remains in BaseBae.
- [x] **PEP 8 Compliance**: All data models use type hints, dataclasses, proper naming. Templates configured to generate PEP 8 compliant code (100 char limit, snake_case/PascalCase filters).
- [x] **DRY Principle**: TemplateRegistry centralizes template management. ValidationRule base class eliminates pattern duplication. Compressed standards extract common rules once.
- [x] **Integration Testing**: Test plan includes template validation tests, cache persistence tests, confidence-based validation accuracy tests, and end-to-end performance tests.
- [x] **Observability**: OptimizationMetrics design tracks all critical metrics. Structured logging for cache operations, template decisions, validation outcomes.
- [x] **Fail-Fast Error Handling**: Cache corruption → explicit error + OpenAI fallback. Template render failure → fallback_used flag + LLM generation. Regex exceptions → uncertain classification.
- [x] **Semantic Coherence**: ValidationRule confidence classification explicitly addresses semantic checking. Uncertain cases route to LLM for semantic validation. 85%+ approval target maintains quality.
- [x] **Generator-First Fixes**: All components added to baes/ generator source. Templates versioned in generator. No managed_system modifications. Template bugs fixed in template files.

**Design Improvements from Research:**
1. Added cache_version field to RecognitionCache for migration support (originally missing)
2. Added uncertainty_triggers to ValidationRule (originally only required/prohibited patterns)
3. Added fallback_used flag to TemplateOutput for transparency (debugging aid)
4. Added template versioning comments in generated code for traceability

**Remaining Design Risks:**
- Cache normalization false positives (mitigated with confidence scores + validation on retrieval)
- Template coverage gaps for uncommon entity patterns (mitigated with LLM fallback + monitoring)
- Validation rule tuning burden (mitigated with pattern testing framework + quarterly review process)

---

## Next Steps

**This planning phase is now COMPLETE**. The following artifacts are ready for implementation:

✅ **Deliverables Created:**
1. [plan.md](plan.md) - This comprehensive implementation plan
2. [research.md](research.md) - Technical research and decision rationale
3. [data-model.md](data-model.md) - Data models and schemas
4. [quickstart.md](quickstart.md) - Developer documentation
5. [contracts/](contracts/) - API contracts for new components

**Branch**: `001-performance-optimization`  
**Implementation Status**: Ready for task breakdown (use `/speckit.tasks` command)

**To Begin Implementation:**
```bash
# Generate task breakdown
/speckit.tasks

# Tasks will be created in:
specs/001-performance-optimization/tasks.md
```

**Implementation Priority:**
1. **P1 Tasks** (Highest ROI - 70%+ combined savings):
   - Template-based generation (40-60% token, 50-60% time savings)
   - Confidence-based validation (20-30% token savings)
   
2. **P2 Tasks** (Medium ROI - 15-20% savings):
   - Two-tier persistent cache (cross-session benefit)
   - Compressed prompts (15-20% token savings)
   
3. **P3 Tasks** (Optional - 10-15% savings):
   - Parallel execution (15-25% time savings)
   - Smart retry (10-15% savings on retries)

**Quality Gates Before Merge:**
- [ ] 100% integration tests passing
- [ ] TechLeadSWEA approval rate ≥85% for template-generated code
- [ ] Performance targets met: <15s, <2000 tokens per standard entity
- [ ] All 8 constitutional principles validated in implementation
- [ ] Manual testing: cache hit rates, template coverage, validation accuracy
