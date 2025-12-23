# Feature Specification: BAES Framework Performance Optimization

**Feature Branch**: `001-performance-optimization`  
**Created**: December 23, 2025  
**Status**: Draft  
**Input**: Comprehensive performance optimization plan to reduce LLM token consumption and execution time based on architecture analysis findings

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Template-Based CRUD Generation (Priority: P1)

As a developer using BAES Framework, when I request generation of a standard CRUD system for an entity (Student, Course, Product, etc.), the system generates the complete backend, frontend, and database code using pre-built templates instead of calling the LLM for every component, reducing token consumption by 40-60% and generation time by 50-60%.

**Why this priority**: This provides the single largest performance improvement with reasonable implementation effort. Standard CRUD operations represent 90% of typical entity requests, making this a high-impact optimization. Benchmarking shows BAES currently underperforms competitors primarily due to excessive LLM calls for repetitive patterns.

**Independent Test**: Can be fully tested by requesting generation of a simple Student entity with name and registration attributes. System should complete in under 15 seconds (down from 40+ seconds) using <2000 tokens (down from 8000+ tokens) for standard patterns. Generated code must pass all existing integration tests.

**Acceptance Scenarios**:

1. **Given** a request for standard Student entity with basic attributes, **When** system generates the code, **Then** it uses Jinja2 templates for models/routes/pages and only calls LLM for business rule interpretation
2. **Given** a request for entity with complex business rules (validation beyond standard patterns), **When** system detects non-standard requirements, **Then** it falls back to LLM generation for custom logic while using templates for standard parts
3. **Given** multiple requests for similar CRUD entities, **When** each is processed, **Then** template application time remains constant (~5 seconds) regardless of entity count
4. **Given** generated template-based code, **When** TechLeadSWEA reviews it, **Then** review uses rule-based validation instead of LLM call (see US2)

---

### User Story 2 - Rule-Based Code Validation (Priority: P1)

As the system processing entity requests, when TechLeadSWEA needs to validate generated code for standard patterns (database connections, HTTP status codes, error handling), I use a confidence-based hybrid approach: regex patterns provide instant approval/rejection for clear cases (70-80% of validations, 0 tokens), while uncertain or ambiguous code triggers LLM semantic review, reducing token consumption by 20-30% overall.

**Why this priority**: TechLeadSWEA currently reviews every artifact with full LLM calls even for template-generated code following known patterns. A confidence-based approach allows regex to handle obvious approvals and clear violations instantly, while safely deferring to LLM for truly ambiguous cases. This balances performance optimization with validation reliability based on real-world regex limitations.

**Independent Test**: Can be tested by generating a standard entity and monitoring TechLeadSWEA review calls. Template-generated code should pass regex confident approval in <100ms with 0 tokens (60-70% of cases). Clear pattern violations should be rejected by regex with specific feedback in <100ms (10-20% of cases). Only custom/ambiguous logic should trigger LLM reviews (20% of cases).

**Acceptance Scenarios**:

1. **Given** template-generated FastAPI routes with all standard patterns present, **When** regex validation executes, **Then** it returns confident_approval with 0 tokens and validation completes in <100ms without LLM call
2. **Given** code with clear pattern violation (missing @contextmanager), **When** regex validation executes, **Then** it returns confident_rejection with specific feedback ("Line 15: Missing @contextmanager decorator") using 0 tokens
3. **Given** custom business logic with non-standard patterns, **When** regex validation executes, **Then** it returns uncertain classification and defers to LLM for semantic review
4. **Given** Pydantic model validation, **When** AST parser checks structure, **Then** confident approval/rejection is determined in <100ms based on type hints and field definitions without LLM call
5. **Given** mixed standard/custom code (80% template patterns, 20% custom validation), **When** validation executes, **Then** standard parts pass regex confident approval, custom parts trigger LLM review for that section only

---

### User Story 3 - Entity Recognition Caching (Priority: P2)

As the system processing natural language requests, when users make similar or repeated requests ("create student system", "add student"), I cache entity recognition results using a two-tier architecture (in-memory hot cache + persistent SQLite cold cache) that survives framework restarts, reducing token consumption by 10-15% per session and compounding savings across sessions.

**Why this priority**: Entity recognition happens on every request and uses OpenAI even for identical requests. Two-tier caching provides immediate in-memory speed (microseconds) for active entities while persistent storage enables cross-session benefits. First request after restart uses cached results instead of re-recognizing common entities. This optimization compounds over time as the persistent cache builds historical knowledge.

**Independent Test**: Can be tested by making the same request twice ("create a student management system"), then restarting BAES and making it again. First request: OpenAI call (~500 tokens). Second request in same session: in-memory cache hit (0 tokens, <1ms). Third request after restart: persistent cache hit promoted to memory (0 tokens, <50ms). Cache hit rate should exceed 40% in-session, 60%+ cross-session.

**Acceptance Scenarios**:

1. **Given** a request "create student system", **When** processed for the first time ever, **Then** EntityRecognizer calls OpenAI, caches result in both memory and persistent store (async background write to SQLite)
2. **Given** cached entity recognition for "student" in memory, **When** similar request "add student management" arrives, **Then** system returns cached result from memory in <1ms with 0 tokens
3. **Given** BAES framework restart with persistent cache containing "student", **When** request "create student system" arrives, **Then** system loads from persistent store (<50ms), promotes to memory cache, returns result with 0 tokens
4. **Given** 100 requests across multiple sessions, **When** 60% are variations of cached entities, **Then** system saves ~30,000 tokens total (improved from in-memory only due to cross-session hits)
5. **Given** entity schema evolution (Student adds 'email' attribute), **When** new request with updated schema arrives, **Then** system invalidates both memory and persistent cache entries for "student", makes new OpenAI call
6. **Given** memory cache contains 100 entries, **When** LRU eviction triggers, **Then** least recently used entries are removed from memory but remain in persistent store

---

### User Story 4 - Compressed Prompt Context (Priority: P2)

As the system generating prompts for LLM calls, instead of including full standards documents (467 lines of backend_standards.py), I include compressed essential rules (20-30 lines), reducing prompt token consumption by 15-20% without sacrificing code quality.

**Why this priority**: Current prompts are verbose with redundant information, full example code, and extensive explanations. LLMs like GPT-4o-mini are trained on common patterns and don't need full documentation. Compressed prompts reduce every single LLM call's token cost.

**Independent Test**: Can be tested by comparing prompt sizes before/after compression. Standard backend generation prompt should reduce from ~2000 tokens to ~1600 tokens. Generated code quality (measured by TechLeadSWEA approval rate) should remain above 85%.

**Acceptance Scenarios**:

1. **Given** backend code generation request, **When** building prompt, **Then** system includes compressed standards (critical rules only: context manager, status codes, error handling) instead of full 467-line document
2. **Given** compressed prompt with essential rules, **When** BackendSWEA generates code, **Then** output maintains constitutional compliance (PEP8, DRY, fail-fast) with 85%+ first-attempt approval rate
3. **Given** multiple SWEA types (Backend, Frontend, Database), **When** each generates prompts, **Then** all use domain-specific compressed standards reducing average prompt size by 300-400 tokens
4. **Given** complex custom business logic, **When** compression might lose critical context, **Then** system includes additional relevant standards maintaining generation quality

---

### User Story 5 - Parallel SWEA Execution (Priority: P3)

As the system coordinating SWEA agents, when executing independent tasks (DatabaseSWEA and FrontendSWEA have no dependencies), I run them in parallel using async execution, reducing wall-clock time by 15-25% without changing token consumption.

**Why this priority**: This is pure time optimization without token savings. While valuable for user experience, it provides lower cost-benefit than token optimizations since benchmarking focuses on token efficiency. Implementation requires async refactoring which carries moderate complexity.

**Independent Test**: Can be tested by generating a complete system and measuring execution timeline. Database schema generation (8s) and frontend page generation (10s) should overlap, completing in ~10s total instead of 18s sequential. Token consumption should remain unchanged.

**Acceptance Scenarios**:

1. **Given** SWEA coordination plan with independent tasks (Database + Frontend), **When** executing plan, **Then** both tasks run concurrently with asyncio.gather()
2. **Given** dependent tasks (Backend depends on Database), **When** executing plan, **Then** system respects dependencies executing Database first, then Backend
3. **Given** parallel execution of 2 tasks taking 8s and 10s, **When** both complete, **Then** total time is ~10s (max) instead of 18s (sum)
4. **Given** parallel task failure, **When** one SWEA task raises exception, **Then** other tasks are cancelled gracefully and error is propagated with clear context

---

### User Story 6 - Smart Retry with Targeted Fixes (Priority: P3)

As the system handling TechLeadSWEA rejection feedback, when code review identifies a specific issue ("missing context manager"), I apply targeted patches to fix only that issue instead of regenerating the entire artifact, reducing retry token consumption by 10-15%.

**Why this priority**: Full regeneration on retry wastes tokens recreating correct parts. However, this is complex to implement (requires code parsing and precise patching) and only affects retry scenarios (10-20% of cases). Other optimizations provide better ROI.

**Independent Test**: Can be tested by forcing a validation failure (remove @contextmanager) and observing retry behavior. System should patch only the specific issue (add decorator) rather than regenerating entire 200-line route file, using ~500 tokens instead of 2000.

**Acceptance Scenarios**:

1. **Given** TechLeadSWEA feedback "Missing @contextmanager on get_db_connection", **When** retry executes, **Then** system applies targeted patch adding decorator without regenerating entire file
2. **Given** feedback about multiple unrelated issues, **When** retry executes, **Then** system falls back to full regeneration since targeted patching is not feasible
3. **Given** successful targeted patch, **When** re-validation occurs, **Then** patched code passes TechLeadSWEA review without additional iterations
4. **Given** targeted patch application failure, **When** patch cannot be applied cleanly, **Then** system falls back to full regeneration logging the failure reason

---

### Edge Cases

- **Cache invalidation**: What happens when entity schema evolves (Student adds 'email' attribute) but persistent cached recognition returns old schema even after restart? System must detect schema evolution and invalidate both memory and persistent cache entries. Cache entries must include version/timestamp for staleness detection.

- **Persistent cache corruption**: What happens if SQLite persistent cache file is corrupted or locked by another process? System must gracefully fall back to OpenAI calls and attempt cache rebuild, logging corruption events.

- **Cache migration**: What happens when cache format changes (e.g., adding new fields to cached entries)? System must detect cache_version mismatch and either migrate old entries or invalidate incompatible cache.

- **Template limitations**: How does system handle entity with highly custom requirements that don't fit template patterns? Must detect non-standard patterns early and fall back to LLM generation without attempting template application.

- **Parallel execution failures**: What happens when one parallel task fails while others succeed? System must handle partial completion gracefully, rolling back interdependent artifacts.

- **Regex confidence calibration**: What happens if regex confident_approval rate is too low (e.g., 30% instead of 60-70%), causing most validations to fall back to LLM? System must log confidence classification distribution and allow regex pattern tuning to improve confident detection rate.

- **Compressed prompt ambiguity**: What if compressed standards lose critical context causing generation errors? Must monitor TechLeadSWEA rejection rate and adjust compression level if quality degrades below 85%.

- **Memory constraints**: What happens when entity recognition cache grows to 1000+ entries consuming excessive memory? Must implement LRU eviction with configurable max size (default 100 entries).

- **Mixed standard/custom entities**: How does system handle entity with 80% standard CRUD but 20% custom validation logic? Should use templates for standard parts and LLM augmentation for custom logic.

- **Concurrent requests**: What happens when multiple users generate entities simultaneously with caching enabled? Cache must be thread-safe with proper locking mechanisms.

- **Backward compatibility**: How does optimization affect existing generated systems? Must ensure template-generated code is functionally equivalent to LLM-generated code for all integration tests.

## Requirements *(mandatory)*

### Functional Requirements

**Template-Based Generation (P1)**

- **FR-001**: System MUST detect when entity request follows standard CRUD pattern (attributes without complex validation, relationships, or custom business rules)
- **FR-002**: System MUST use Jinja2 template engine to generate Pydantic models, FastAPI routes, Streamlit pages, and database schemas for standard CRUD entities
- **FR-003**: System MUST fall back to LLM generation when entity includes non-standard requirements (complex validations, custom workflows, computed properties)
- **FR-004**: Template-generated code MUST be functionally equivalent to LLM-generated code, passing all existing integration tests
- **FR-005**: System MUST maintain template library for: Pydantic models, FastAPI CRUD routes, Streamlit forms/tables, SQLite schemas, integration tests

**Rule-Based Validation (P1)**

- **FR-006**: TechLeadSWEA MUST use confidence-based hybrid validation with three classification outcomes: confident_approval, confident_rejection, uncertain
- **FR-006a**: Regex validation MUST return confident_approval when all required patterns are clearly present (context manager, HTTP status codes, exception handling)
- **FR-006b**: Regex validation MUST return confident_rejection when required patterns are clearly absent or incorrect, with specific line-number feedback
- **FR-006c**: Regex validation MUST return uncertain when code contains ambiguous patterns, non-standard structures, or custom business logic requiring semantic understanding
- **FR-007**: TechLeadSWEA MUST use AST parsing for structural validation: type hints presence, docstring format, PEP 8 compliance (naming, indentation), returning confident approval/rejection/uncertain
- **FR-008**: System MUST call LLM for validation ONLY when regex/AST returns uncertain classification (estimated 20% of validations)
- **FR-009**: Confident approval/rejection validations MUST complete in under 100ms with 0 token consumption (target: 70-80% of validations)
- **FR-010**: Confident rejection feedback MUST identify specific line numbers and pattern violations (e.g., "Line 23: Missing @contextmanager decorator")
- **FR-010a**: System MUST log validation method used (confident_regex_approval, confident_regex_rejection, llm_semantic_review) for performance monitoring

**Entity Recognition Caching (P2)**

- **FR-011**: EntityRecognizer MUST implement two-tier cache architecture: in-memory hot cache (fast, volatile) + SQLite persistent cold cache (durable, survives restarts)
- **FR-011a**: Cache MUST store recognition results keyed by normalized request text (lowercase, stripped, lemmatized)
- **FR-012**: Cache entries MUST include: detected entity, confidence score, action intent, timestamp, cache_version, hit_count
- **FR-013**: In-memory cache MUST implement LRU eviction when exceeding 100 entries; persistent cache unlimited with age-based cleanup (30 days default)
- **FR-014**: Cache MUST be thread-safe using locks for in-memory access and SQLite ACID transactions for persistent access
- **FR-015**: Cache lookup MUST try memory first (<1ms), then persistent (<50ms), promoting persistent hits to memory
- **FR-015a**: Cache writes MUST update memory immediately and persistent asynchronously (background thread) to avoid blocking requests
- **FR-016**: System MUST invalidate both memory and persistent cache entries when entity schema evolves (new attributes added/removed)
- **FR-016a**: System MUST provide cache management operations: invalidate by entity, invalidate by age, clear all, export/import for migration
- **FR-017**: Cache format MUST include version number for migration compatibility when cache schema changes
- **FR-018**: Cache hit rate MUST be logged separately for memory hits and persistent hits (targets: 40%+ in-session, 60%+ cross-session)

**Compressed Prompt Context (P2)**

- **FR-017**: System MUST create compressed versions of all standards documents containing only critical rules and patterns
- **FR-018**: Compressed standards MUST include: context manager pattern, HTTP status codes, error handling template, PEP 8 essentials, DRY examples
- **FR-019**: Prompt construction MUST use compressed standards by default, full standards only when complexity detected
- **FR-020**: System MUST monitor TechLeadSWEA approval rate to ensure compression doesn't degrade quality below 85%
- **FR-021**: Each SWEA type (Backend, Frontend, Database, Test) MUST have domain-specific compressed standards

**Parallel Execution (P3)**

- **FR-022**: EnhancedRuntimeKernel MUST analyze SWEA coordination plan to identify independent tasks
- **FR-023**: System MUST execute independent tasks concurrently using asyncio.gather()
- **FR-024**: System MUST respect task dependencies (Backend depends on Database, Tests depend on all)
- **FR-025**: System MUST handle partial failures in parallel execution, cancelling remaining tasks and rolling back as needed
- **FR-026**: Execution timeline MUST be logged showing parallel vs sequential duration for performance monitoring

**Smart Retry (P3)**

- **FR-027**: System MUST analyze TechLeadSWEA feedback to determine if targeted patch is feasible (single, localized issue)
- **FR-028**: For targeted patches, system MUST modify only affected code section using AST manipulation
- **FR-029**: System MUST fall back to full regeneration when: multiple unrelated issues, structural changes needed, patch application fails
- **FR-030**: Retry mechanism MUST track token savings from targeted patches vs full regeneration in metrics

**Cross-Cutting Requirements**

- **FR-031**: All optimizations MUST maintain constitutional compliance (PEP 8, DRY, fail-fast, generator-first fixes, integration-first testing)
- **FR-032**: System MUST log optimization metrics: token consumption per request, cache hit rate, template usage percentage, validation method (rule vs LLM), parallel execution time savings
- **FR-033**: Optimizations MUST be backwards compatible with existing generated systems (no breaking changes to managed_system structure)
- **FR-034**: System MUST provide configuration flags to enable/disable each optimization independently for testing and rollback

### Key Entities

- **TemplateRegistry**: Central registry managing Jinja2 templates for each artifact type (models, routes, pages, schemas). Attributes: template_name, template_content, applicable_patterns, variable_schema. Supports template retrieval by artifact type and pattern matching.

- **RecognitionCache**: Two-tier cache storing entity recognition results with hot (in-memory) and cold (persistent SQLite) layers. Attributes: normalized_request_key, detected_entity, confidence_score, action_intent, timestamp, hit_count, cache_version. Memory tier: LRU eviction at 100 entries, microsecond access. Persistent tier: SQLite with ACID transactions, unlimited size with 30-day age cleanup, millisecond access. Thread-safe with locks (memory) and DB transactions (persistent). Async background writes to persistent layer. Supports promotion (cold→hot), invalidation (by entity/age), and version migration.

- **ValidationRule**: Represents a confidence-based validation pattern (regex or AST-based). Attributes: rule_name, pattern_type (regex/ast), validation_logic, confidence_threshold, error_message_template, applicable_artifact_types. Returns classification: confident_approval (all patterns match), confident_rejection (clear violation with line numbers), uncertain (ambiguous, requires LLM). Used by TechLeadSWEA for zero-token validation in confident cases.

- **CompressedStandards**: Condensed version of full standards documents. Attributes: swea_type, critical_rules, pattern_examples, token_count. Relationships: derived from full BaseStandards/BackendStandards/etc. Each SWEA has corresponding compressed standards.

- **OptimizationMetrics**: Performance tracking entity. Attributes: request_id, template_usage_count, llm_call_count, token_consumption, cache_hit_rate, validation_method (rule/llm), execution_time, parallel_time_savings. Enables ROI analysis and optimization monitoring.

- **TaskDependencyGraph**: Represents SWEA task dependencies for parallel execution planning. Attributes: task_id, task_type, depends_on (list), estimated_duration. Used by EnhancedRuntimeKernel to group independent tasks for concurrent execution.

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Performance Targets (Primary Goals)**

- **SC-001**: Standard CRUD entity generation completes in under 15 seconds (currently 40+ seconds) - **60% time reduction**
- **SC-002**: Token consumption for standard entity reduces to under 2000 tokens per request (currently 8000+ tokens) - **75% token reduction**
- **SC-003**: Template-based generation accounts for 80%+ of entity requests with 0 LLM calls for standard patterns
- **SC-004**: Entity recognition cache achieves 40%+ hit rate in-session and 60%+ hit rate cross-session with persistent storage, eliminating ~500 tokens per cached request and compounding savings over time
- **SC-005**: Confidence-based validation achieves 70-80% confident approvals/rejections with 0 tokens in <100ms, 20% uncertain cases use LLM (down from 100% LLM currently)

**Quality Assurance**

- **SC-006**: Template-generated code maintains 100% pass rate on existing integration test suite (no functional regressions)
- **SC-007**: TechLeadSWEA approval rate remains above 85% for template-generated code (equivalent to current LLM generation quality)
- **SC-008**: System constitutional compliance (PEP 8, DRY, fail-fast) maintained at 100% for all optimization paths
- **SC-009**: Compressed prompts maintain code quality with approval rate ≥85% (within 5% of full prompt quality)

**Operational Metrics**

- **SC-010**: Optimization metrics logged for 100% of requests enabling performance monitoring and ROI analysis
- **SC-011**: Parallel execution reduces wall-clock time by 15-25% for multi-SWEA workflows without affecting token usage
- **SC-012**: Smart retry mechanism (when implemented) reduces retry token consumption by 50%+ for targeted fixes
- **SC-013**: System handles 50+ concurrent requests with caching enabled maintaining thread safety and <10MB memory overhead

**Benchmarking Outcomes**

- **SC-014**: BAES Framework performance in benchmarks improves to match or exceed competitor frameworks in token efficiency
- **SC-015**: End-to-end entity generation (request to running system) completes in under 30 seconds (currently 60-90 seconds) - **50%+ improvement**
- **SC-016**: Cost per entity generation (based on OpenAI token pricing) reduces by 70%+ making BAES commercially competitive
