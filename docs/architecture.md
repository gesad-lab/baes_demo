# BAES Framework Architecture

**Version**: 0.1.0  
**Last Updated**: December 23, 2025  
**Status**: Production

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architectural Overview](#architectural-overview)
3. [Core Components](#core-components)
4. [Domain Entities (BAEs)](#domain-entities-baes)
5. [Software Engineering Agents (SWEAs)](#software-engineering-agents-sweas)
6. [Runtime System](#runtime-system)
7. [LLM Integration Layer](#llm-integration-layer)
8. [Data Persistence](#data-persistence)
9. [Code Generation & Standards](#code-generation--standards)
10. [System Flows](#system-flows)
11. [Configuration & Environment](#configuration--environment)
12. [Testing Architecture](#testing-architecture)

---

## Executive Summary

The **BAES (Business Autonomous Entities) Framework** is an LLM-powered system that generates adaptive software systems through domain-driven autonomous agents. The framework represents a paradigm shift where domain entities (Students, Courses, Teachers, etc.) are modeled as autonomous agents that interpret business requirements, maintain semantic coherence, and coordinate specialized software engineering agents to generate complete, running systems.

### Key Innovation

Unlike traditional code generators that directly translate requirements into code, BAES introduces:
- **Domain Entity Autonomy**: Each business entity is represented by a BAE that maintains domain knowledge and semantic coherence
- **Multi-Agent Coordination**: BAEs coordinate specialized SWEA agents for technical implementation
- **Runtime Evolution**: Generated systems can evolve based on new requirements while preserving domain integrity
- **Fail-Fast Architecture**: Errors in generated code are fixed in generator components, not in output

### Technology Stack

- **Language**: Python 3.11+
- **LLM Provider**: OpenAI GPT-4o-mini
- **Generated Backend**: FastAPI + Pydantic
- **Generated Database**: SQLite
- **Generated Frontend**: Streamlit
- **Testing**: pytest with integration-first approach

---

## Architectural Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Human Business Expert (HBE)                 │
│                    "Create a system to manage students"             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ Natural Language Request
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ENHANCED RUNTIME KERNEL                        │
│  ┌────────────────────┐   ┌──────────────────┐   ┌───────────────┐│
│  │ Entity Recognizer  │──▶│  BAE Registry    │──▶│ Managed System││
│  │ (OpenAI-powered)   │   │ (Student/Course/ │   │    Manager    ││
│  └────────────────────┘   │  Teacher/Generic)│   └───────────────┘│
└───────────────────────────┴──────────────────┴─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BUSINESS AUTONOMOUS ENTITIES (BAEs)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ StudentBAE   │  │  CourseBAE   │  │ TeacherBAE   │  ┌─────────┐│
│  │ (Registered) │  │ (Registered) │  │ (Registered) │  │ Generic ││
│  │              │  │              │  │              │  │   BAE   ││
│  │ - Interprets │  │ - Interprets │  │ - Interprets │  │(Fallback││
│  │   requests   │  │   requests   │  │   requests   │  │for any  ││
│  │ - Maintains  │  │ - Maintains  │  │ - Maintains  │  │entity)  ││
│  │   domain     │  │   domain     │  │   domain     │  │         ││
│  │   knowledge  │  │   knowledge  │  │   knowledge  │  │         ││
│  │ - Coordinates│  │ - Coordinates│  │ - Coordinates│  │         ││
│  │   SWEAs      │  │   SWEAs      │  │   SWEAs      │  │         ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────┬────┘│
└─────────┼──────────────────┼──────────────────┼───────────────┼─────┘
          │                  │                  │               │
          └──────────────────┴──────────────────┴───────────────┘
                              │ SWEA Coordination Plan
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│          SOFTWARE ENGINEERING AUTONOMOUS AGENTS (SWEAs)             │
│  ┌────────────────┐ ┌─────────────┐ ┌──────────────┐              │
│  │ TechLeadSWEA   │ │DatabaseSWEA │ │ BackendSWEA  │              │
│  │ - Technical    │ │ - SQLite    │ │ - FastAPI    │              │
│  │   governance   │ │   schemas   │ │   routes     │              │
│  │ - Quality gates│ │ - Migrations│ │ - Pydantic   │              │
│  │ - Reviews code │ │ - Queries   │ │   models     │              │
│  └────────────────┘ └─────────────┘ └──────────────┘              │
│  ┌────────────────┐ ┌─────────────┐                               │
│  │ FrontendSWEA   │ │  TestSWEA   │                               │
│  │ - Streamlit UI │ │ - Integration│                              │
│  │ - Forms/Tables │ │   tests     │                               │
│  └────────────────┘ └─────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
                              │ Generated Code
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       MANAGED SYSTEM (Output)                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ managed_system/                                              │  │
│  │  ├── app/                                                    │  │
│  │  │   ├── main.py          (FastAPI app entry point)         │  │
│  │  │   ├── models/          (Pydantic models)                 │  │
│  │  │   ├── routes/          (API endpoints)                   │  │
│  │  │   └── database/        (SQLite DB + schemas)             │  │
│  │  ├── ui/                                                     │  │
│  │  │   ├── app.py           (Streamlit UI entry point)        │  │
│  │  │   ├── pages/           (UI pages)                        │  │
│  │  │   └── components/      (Reusable UI components)          │  │
│  │  └── tests/               (Generated integration tests)     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ⚠️  EPHEMERAL: This directory is regenerated on demand.           │
│      All fixes must be done in BAEs/SWEAs, NOT here.               │
└─────────────────────────────────────────────────────────────────────┘
```

### Architectural Principles

1. **Generator-First Fixes (Constitutional Principle VIII)**: All bug fixes and improvements must be implemented in generator components (BAEs/SWEAs), never in the generated managed system. The managed system is disposable output.

2. **Domain-Driven Autonomy (Constitutional Principle I)**: Each BAE represents a single domain entity and maintains semantic coherence between business vocabulary and technical artifacts.

3. **Fail-Fast Error Handling (Constitutional Principle VI)**: Errors fail immediately with clear messages. No silent fallbacks that mask problems.

4. **Integration-First Testing (Constitutional Principle IV)**: Focus on integration tests that validate complete workflows. Unit tests are optional.

5. **PEP 8 & DRY (Constitutional Principles II & III)**: All code strictly adheres to PEP 8 standards and eliminates duplication through abstraction.

---

## Core Components

### 1. Base Agent (`baes/agents/base_agent.py`)

Abstract base class for all agents (both BAEs and SWEAs).

**Responsibilities:**
- Agent lifecycle management
- Memory management with metadata
- Interaction logging and traceability
- Task handling interface

**Key Features:**
```python
class BaseAgent(ABC):
    - name: str                          # Agent identifier
    - role: str                          # Agent purpose
    - agent_type: str                    # "BAE" or "SWEA"
    - memory: Dict[str, Any]             # Persistent memory
    - interaction_count: int             # Tracking
    
    @abstractmethod
    def handle_task(task, payload) -> Dict
```

**Memory Management:**
- Structured memory with timestamps
- Update counters for evolution tracking
- Metadata support for contextual information
- Full memory retrieval for debugging

### 2. Enhanced Runtime Kernel (`baes/core/enhanced_runtime_kernel.py`)

The central orchestrator that processes natural language requests and coordinates the entire system.

**Responsibilities:**
- Natural language request processing
- Entity recognition and routing
- BAE coordination
- SWEA orchestration
- Error handling with retry logic
- Server lifecycle management

**Key Features:**
- **Multi-entity support**: Handles Student, Course, Teacher, and dynamic entities via GenericBAE
- **OpenAI-powered entity recognition**: Multilingual support (English/Portuguese)
- **Retry patterns with analytics**: MaxRetriesReachedError for fail-fast
- **Execution history tracking**: Full audit trail of operations
- **Server management**: Auto-start/stop of FastAPI and Streamlit servers

**Processing Flow:**
```python
1. Receive natural language request
2. Entity recognition via OpenAI (EntityRecognizer)
3. Route to appropriate BAE (via BAERegistry)
4. BAE interprets request and creates SWEA coordination plan
5. Execute SWEA coordination plan with retry logic
6. Generate complete system in managed_system/
7. Start servers if requested
8. Return execution summary
```

### 3. BAE Registry (`baes/core/bae_registry.py`)

Centralized registry for managing all Business Autonomous Entities.

**Responsibilities:**
- BAE lifecycle initialization
- Metadata management
- Entity lookup and retrieval
- Keyword management for entity recognition

**Registered BAEs:**
- **StudentBAE**: Keywords: student, aluno, estudante, discente
- **CourseBAE**: Keywords: course, curso, disciplina, matéria, subject
- **TeacherBAE**: Keywords: teacher, professor, docente, instrutor, instructor

**Metadata Structure:**
```python
{
    "keywords": List[str],              # Recognition keywords
    "description": str,                 # BAE purpose
    "domain_attributes": List[str],     # Core attributes
    "business_rules": List[str],        # Domain constraints
    "contexts": List[str],              # Applicable contexts
    "status": str,                      # active/inactive
    "version": str,                     # BAE version
}
```

### 4. Entity Recognizer (`baes/core/entity_recognizer.py`)

OpenAI-powered component that analyzes natural language requests to identify the primary entity.

**Responsibilities:**
- Entity extraction from natural language
- Confidence scoring
- Language detection (multilingual)
- Action intent classification
- Relationship analysis

**Recognition Process:**
```python
1. Analyze user request with OpenAI
2. Identify primary entity (subject being modified)
3. Determine action intent (create/update/delete/list/relationship)
4. Extract confidence score (0.0-1.0)
5. Return structured classification:
   {
       "detected_entity": str,
       "confidence": float,
       "reasoning": str,
       "language_detected": str,
       "action_intent": str,
       "relationship_analysis": {...}
   }
```

**Relationship Handling:**
For relationship requests (e.g., "add course to student"), correctly identifies:
- **Primary entity**: The one being modified (student)
- **Secondary entity**: The one being referenced (course)
- **Relationship direction**: from secondary to primary

**Fallback Strategy:**
- Registered entities (student/course/teacher) → specific BAEs
- Unknown entities → GenericBAE for dynamic handling
- Very low confidence (<0.5) → return "unknown"

### 5. Managed System Manager (`baes/core/managed_system_manager.py`)

Manages the generated system structure, files, and server lifecycle.

**Responsibilities:**
- Directory structure creation
- Base configuration files generation
- Entity-specific code integration
- Server lifecycle management (FastAPI + Streamlit)

**Generated Structure:**
```
managed_system/
├── app/
│   ├── main.py                 # FastAPI app with all entity routes
│   ├── models/                 # Pydantic models per entity
│   ├── routes/                 # FastAPI routes per entity
│   └── database/               # SQLite DB and schemas
├── ui/
│   ├── app.py                  # Streamlit app with all entity pages
│   ├── pages/                  # Per-entity pages
│   └── components/             # Shared UI components
├── tests/                      # Integration tests
├── requirements.txt            # Dependencies
├── .env                        # Configuration
└── README.md                   # Documentation
```

**Server Management:**
- **FastAPI**: Runs on configurable port (default: 8100)
- **Streamlit**: Runs on configurable port (default: 8600)
- Background process management with subprocess
- Health checks and auto-restart on entity changes

### 6. Context Store (`baes/core/context_store.py`)

Persistent storage for domain knowledge, agent memory, and semantic coherence.

**Responsibilities:**
- Domain context preservation across sessions
- Agent memory persistence
- Business vocabulary management
- Entity relationship tracking
- Evolution history auditing

**Storage Structure:**
```json
{
    "domain_contexts": {
        "context_name": [
            {
                "context_name": str,
                "entity_focus": str,
                "context_data": {...},
                "timestamp": ISO8601,
                "version": int
            }
        ]
    },
    "agent_memories": {
        "agent_name": {
            "memory_data": {...},
            "timestamp": ISO8601
        }
    },
    "domain_knowledge": {
        "entity_name": {
            "interpretation": {...},
            "context": str,
            "timestamp": ISO8601
        }
    },
    "evolution_history": [...]
}
```

**Key Operations:**
- `store_domain_context()`: Save context with versioning
- `store_agent_memory()`: Persist agent state
- `store_domain_knowledge()`: Save entity interpretations
- `track_evolution()`: Record schema changes
- `get_evolution_history()`: Retrieve change timeline

---

## Domain Entities (BAEs)

### Base BAE (`baes/domain_entities/base_bae.py`)

Abstract base class providing common BAE functionality.

**Core Capabilities:**
1. **Domain Knowledge Management**
2. **Schema Evolution Detection**
3. **Business Request Interpretation**
4. **SWEA Coordination**
5. **Semantic Coherence Validation**

**Inheritance Hierarchy:**
```
BaseAgent (abstract)
    └── BaseBae (abstract)
            ├── StudentBae (concrete)
            ├── CourseBae (concrete)
            ├── TeacherBae (concrete)
            └── GenericBae (concrete)
```

**Task Interface:**
```python
handle_task(task: str, payload: Dict) -> Dict

Supported tasks:
- interpret_business_request    # Parse NL requirements
- coordinate_swea              # Create SWEA coordination plan
- generate_schema              # Create Pydantic models
- evolve_schema                # Modify existing schemas
- validate_domain_coherence    # Semantic validation
- get_domain_knowledge         # Retrieve entity knowledge
```

**Evolution Detection:**
Detects schema changes and triggers appropriate updates:
```python
def _detect_schema_evolution(current, previous):
    - Added attributes
    - Removed attributes
    - Modified attributes
    - Type changes
    
Returns: EvolutionType (NEW, ADDITION, REMOVAL, MODIFICATION, NO_CHANGE)
```

### StudentBAE (`baes/domain_entities/academic/student_bae.py`)

Specialized BAE for student domain entity.

**Domain Knowledge:**
- **Keywords**: student, aluno, estudante, discente
- **Default Attributes**: name, registration_number, course, email, age
- **Business Rules**:
  - Registration number must be unique
  - Email validation required
  - Age must be positive and reasonable

**Contexts:**
- University: Traditional academic settings
- Corporate Training: Employee learning management
- Open Courses: Online education platforms

### CourseBAE (`baes/domain_entities/academic/course_bae.py`)

Specialized BAE for course domain entity.

**Domain Knowledge:**
- **Keywords**: course, curso, disciplina, matéria, subject
- **Default Attributes**: name, code, credits, duration, description
- **Business Rules**:
  - Course code must be unique
  - Credits must be positive
  - Prerequisites must exist in system

### TeacherBAE (`baes/domain_entities/academic/teacher_bae.py`)

Specialized BAE for teacher domain entity.

**Domain Knowledge:**
- **Keywords**: teacher, professor, docente, instrutor, instructor
- **Default Attributes**: name, employee_id, department, subjects, email
- **Business Rules**:
  - Employee ID must be unique
  - Department must be valid
  - At least one subject assignment required

### GenericBAE (`baes/domain_entities/generic_bae.py`)

Dynamic fallback BAE that can represent ANY domain entity.

**Purpose:**
Provides BAE functionality for entities not registered in the system, enabling truly dynamic entity handling without pre-configuration.

**Key Features:**
- **Dynamic Entity Adaptation**: Can switch entity focus at runtime
- **Entity-Agnostic Processing**: Works with any business entity
- **Automatic Schema Inference**: Derives schemas from requests
- **Full BAE Capabilities**: All standard BAE operations

**Adaptation Flow:**
```python
1. Initialize as GenericBAE("Book")        # Primary entity: Book
2. Receive request about "Product"         # Detection via interpretation
3. Adapt current_entity to "Product"       # Dynamic switching
4. Process request for Product entity      # Generate Product system
5. Can adapt again for different entity    # Fully reusable
```

**Use Cases:**
- One-off entity requests (Book, Product, Vehicle, etc.)
- Prototyping without BAE registration
- Dynamic systems with unknown entity types
- Cross-domain applications

---

## Software Engineering Agents (SWEAs)

### TechLeadSWEA (`baes/swea_agents/techlead_swea.py`)

Technical governance and coordination agent.

**Responsibilities:**
- System generation coordination
- Code review and approval
- Quality gate management
- Technical conflict resolution
- Architecture decisions
- Performance/security oversight

**Key Tasks:**
```python
- coordinate_system_generation     # Orchestrate all SWEAs
- review_and_approve              # Code quality validation
- verify_user_request_compliance  # Check against requirements
- verify_artifact_compliance      # Validate generated code
- coordinate_test_fixes           # Handle test failures
- resolve_technical_conflict      # Mediate SWEA disagreements
- make_tech_decision              # Architecture choices
- assess_system_health            # System diagnostics
```

**Review Criteria:**
- Database connection patterns (context managers)
- HTTP status codes (201 for POST, 204 for DELETE, etc.)
- Error handling (try/except with logging)
- PEP 8 compliance
- Type hints and docstrings
- DRY principle adherence

**Feedback System:**
Maintains structured feedback with CSV analytics:
```python
feedback_storage = {
    "entity_name": {
        "iteration": int,
        "swea_agent": str,
        "task_type": str,
        "feedback": List[str],
        "approval": bool,
        "timestamp": ISO8601
    }
}
```

### DatabaseSWEA (`baes/swea_agents/database_swea.py`)

Database schema and migration agent.

**Responsibilities:**
- SQLite schema generation
- Database initialization
- Migration scripts
- Query optimization
- Data integrity constraints

**Generated Artifacts:**
```python
database_schema.sql:
- CREATE TABLE statements
- Primary keys and indexes
- Foreign key constraints
- Default values
- NOT NULL constraints

initialization code:
- Database file creation
- Schema application
- Initial data seeding (optional)
```

**Standards Compliance:**
- Table naming: lowercase with underscores
- Column naming: snake_case
- Proper data types (INTEGER, TEXT, REAL, BLOB)
- Transaction handling for data integrity

### BackendSWEA (`baes/swea_agents/backend_swea.py`)

FastAPI backend generation agent.

**Responsibilities:**
- Pydantic model generation
- FastAPI route creation
- CRUD operations implementation
- Request/response handling
- API documentation

**Generated Artifacts:**
```python
models/{entity}_model.py:
- Pydantic BaseModel classes
- Field validation rules
- Type hints
- Example values

routes/{entity}_routes.py:
- APIRouter instance
- CRUD endpoints (POST, GET, PUT, DELETE)
- Database connection management
- Error handling
- HTTP status codes
```

**Endpoint Pattern:**
```python
POST   /api/{entity}/              # Create (201 Created)
GET    /api/{entity}/              # List all (200 OK)
GET    /api/{entity}/{id}          # Get one (200 OK)
PUT    /api/{entity}/{id}          # Update (200 OK)
DELETE /api/{entity}/{id}          # Delete (204 No Content)
```

**Key Standards:**
- Context manager for database connections
- Proper HTTP status codes
- Exception handling with rollback
- Response models for validation

### FrontendSWEA (`baes/swea_agents/frontend_swea.py`)

Streamlit UI generation agent.

**Responsibilities:**
- Streamlit page generation
- Form creation for CRUD operations
- Data table display
- User interaction handling
- API integration

**Generated Artifacts:**
```python
pages/{entity}_page.py:
- Create form (st.form)
- List/table view (st.dataframe)
- Edit functionality
- Delete confirmation
- API client integration
```

**UI Components:**
- Input forms with validation
- Data tables with sorting/filtering
- Success/error messages (st.success/st.error)
- Confirmation dialogs
- Navigation between pages

### TestSWEA (`baes/swea_agents/test_swea.py`)

Integration test generation agent.

**Responsibilities:**
- Integration test generation
- API endpoint testing
- Database operation validation
- Test fixture creation
- Test execution coordination

**Generated Artifacts:**
```python
tests/integration/test_{entity}_integration.py:
- Database setup/teardown
- API endpoint tests
- CRUD operation validation
- Error case handling
- Response validation
```

**Test Patterns:**
```python
test_create_{entity}()           # POST endpoint
test_read_{entity}()             # GET endpoint
test_update_{entity}()           # PUT endpoint
test_delete_{entity}()           # DELETE endpoint
test_{entity}_validation()       # Input validation
```

---

## Runtime System

### Request Processing Flow

```
1. USER INPUT
   └─▶ Natural language request (e.g., "Create a system to manage students")

2. ENTITY RECOGNITION (EntityRecognizer)
   └─▶ OpenAI analyzes request
   └─▶ Identifies primary entity: "student"
   └─▶ Confidence score: 0.95
   └─▶ Action intent: "create"

3. BAE ROUTING (BAERegistry)
   └─▶ Lookup entity: "student"
   └─▶ Retrieve: StudentBAE instance
   └─▶ If not found: Fallback to GenericBAE

4. BUSINESS INTERPRETATION (StudentBAE)
   └─▶ Task: interpret_business_request
   └─▶ Extract attributes: [name, registration_number, course, email]
   └─▶ Identify business rules
   └─▶ Preserve business vocabulary
   └─▶ Create SWEA coordination plan

5. TECHLEAD COORDINATION (TechLeadSWEA)
   └─▶ Task: coordinate_system_generation
   └─▶ Verify user request compliance
   └─▶ Define quality gates
   └─▶ Create enhanced coordination plan
   └─▶ Technical analysis

6. SWEA EXECUTION (Sequential with Retry)
   A. DatabaseSWEA
      └─▶ Generate database schema
      └─▶ TechLeadSWEA review ✓
      
   B. BackendSWEA
      └─▶ Generate Pydantic models
      └─▶ Generate FastAPI routes
      └─▶ TechLeadSWEA review ✓
      
   C. FrontendSWEA
      └─▶ Generate Streamlit UI
      └─▶ TechLeadSWEA review ✓
      
   D. TestSWEA
      └─▶ Generate integration tests
      └─▶ TechLeadSWEA review ✓

7. SYSTEM INTEGRATION (ManagedSystemManager)
   └─▶ Create directory structure
   └─▶ Write all generated files
   └─▶ Configure environment
   └─▶ Install dependencies

8. SERVER STARTUP
   └─▶ Start FastAPI server (port 8100)
   └─▶ Start Streamlit server (port 8600)
   └─▶ Health checks

9. CONTEXT PERSISTENCE (ContextStore)
   └─▶ Store domain knowledge
   └─▶ Save agent memories
   └─▶ Record evolution history
   └─▶ Update business vocabulary

10. RESPONSE GENERATION
    └─▶ Execution summary
    └─▶ Generated artifacts list
    └─▶ Server URLs
    └─▶ Performance metrics
```

### Error Handling & Retry Logic

**Retry Strategy:**
```python
MAX_RETRIES = 3                    # Configurable per task
RETRY_DELAY = 1 second             # Backoff between retries

For each SWEA task:
1. Execute task (e.g., generate_api_code)
2. TechLeadSWEA review
3. If REJECTED:
   - Log feedback
   - Retry with feedback context
   - Increment retry counter
4. If retry_count >= MAX_RETRIES:
   - Raise MaxRetriesReachedError
   - Fail-fast (no silent fallbacks)
5. If APPROVED:
   - Proceed to next task
```

**MaxRetriesReachedError:**
```python
class MaxRetriesReachedError(Exception):
    - task_name: str
    - swea_agent: str
    - task_type: str
    - retry_count: int
    - max_retries: int
    - last_error: str
    - feedback: List[str]
```

**Fail-Fast Principle:**
- NO silent fallbacks
- NO default value substitution
- Immediate failure with clear error message
- Better to fail during development than silently in production

### Evolution Detection & Handling

**Schema Evolution Types:**
```python
NEW:           No previous schema exists
ADDITION:      New attributes added
REMOVAL:       Attributes removed
MODIFICATION:  Attribute types/constraints changed
NO_CHANGE:     Schema identical to previous
```

**Evolution Flow:**
```python
1. Load previous schema from ContextStore
2. Compare with current request
3. Detect changes:
   - added = new - previous
   - removed = previous - new
   - modified = type/constraint changes
4. If evolution detected:
   - Set is_evolution = True
   - Pass to TechLeadSWEA coordination
   - Generate migration scripts
   - Preserve existing data
5. Store new schema version
```

---

## LLM Integration Layer

### OpenAI Client (`baes/llm/openai_client.py`)

Centralized OpenAI GPT-4o-mini integration.

**Responsibilities:**
- API communication
- Response parsing
- JSON enforcement
- Error handling
- Request logging
- Token tracking

**Key Methods:**

**1. generate_response()**
```python
def generate_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0,
    max_tokens: int = 2000,
    ensure_json: bool = False,
    json_schema: Optional[Dict] = None
) -> str
```
General-purpose text generation with optional JSON enforcement.

**2. generate_json_response()**
```python
def generate_json_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0,
    max_tokens: int = 2000,
    json_schema: Optional[Dict] = None,
    fallback_schema: Optional[Dict] = None
) -> Dict
```
Enforced JSON response with schema validation and fallback.

**3. interpret_business_request()**
```python
def interpret_business_request(
    request: str,
    context: str = "academic"
) -> Dict
```
Specialized method for BAE business request interpretation.

**4. generate_code()**
```python
def generate_code(
    prompt: str,
    language: str = "python",
    include_standards: bool = True
) -> str
```
Code generation with language-specific standards.

**JSON Enforcement Strategy:**
```python
1. Enhance prompt with JSON instructions
2. Add schema example to prompt
3. Call OpenAI with enhanced prompt
4. Extract JSON from response (handle markdown)
5. Parse and validate JSON
6. If parse fails:
   - Log error with LLM request logger
   - Retry with clearer instructions (up to 2 times)
   - If still fails: return fallback_schema
7. Validate against json_schema if provided
8. Return parsed Dict
```

**Request Logging:**
All LLM requests are logged to `logs/llm_requests/` with:
- Request prompt and system prompt
- Response content
- Model and parameters
- Timestamp and duration
- Token usage
- Success/failure status

**Error Handling:**
- API errors: Retry with exponential backoff
- Parse errors: Return fallback schema with error flag
- Rate limits: Wait and retry
- Invalid API key: Raise immediate exception

---

## Data Persistence

### Context Store Schema

**File**: `database/context_store.json`

**Structure:**
```json
{
  "domain_contexts": {
    "academic": [
      {
        "context_name": "academic",
        "entity_focus": "Student",
        "context_data": {...},
        "timestamp": "2025-12-23T10:30:00",
        "version": 1
      }
    ]
  },
  
  "agent_memories": {
    "StudentBAE": {
      "current_schema": {
        "entity": "Student",
        "attributes": ["name", "registration_number", "course"],
        "context": "academic",
        "generated_at": "2025-12-23T10:30:00"
      },
      "domain_knowledge": {...}
    }
  },
  
  "domain_knowledge": {
    "student": {
      "interpretation": {
        "intent": "manage_student",
        "extracted_attributes": [...],
        "business_vocabulary": [...]
      },
      "context": "academic",
      "timestamp": "2025-12-23T10:30:00"
    }
  },
  
  "business_vocabularies": {
    "student": {
      "keywords": ["student", "aluno", "estudante"],
      "synonyms": {...},
      "context_variations": {...}
    }
  },
  
  "entity_relationships": {
    "student_course": {
      "source_entity": "student",
      "target_entity": "course",
      "relationship_type": "many_to_one",
      "established_at": "2025-12-23T10:30:00"
    }
  },
  
  "evolution_history": [
    {
      "entity": "Student",
      "evolution_type": "ADDITION",
      "changes": {
        "added_attributes": ["email", "age"],
        "removed_attributes": [],
        "modified_attributes": []
      },
      "previous_version": 1,
      "new_version": 2,
      "timestamp": "2025-12-23T11:00:00"
    }
  ]
}
```

### Generated System Database

**File**: `managed_system/app/database/baes_system.db`

**Schema per Entity:**
```sql
CREATE TABLE {entity_lowercase} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {attribute1} {type1} NOT NULL,
    {attribute2} {type2},
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_{entity}_{attribute} ON {entity}({attribute});
```

**Example (Student):**
```sql
CREATE TABLE student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    registration_number TEXT UNIQUE NOT NULL,
    course TEXT NOT NULL,
    email TEXT,
    age INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_student_registration ON student(registration_number);
CREATE INDEX idx_student_course ON student(course);
```

---

## Code Generation & Standards

### Standards Hierarchy

```
BaseStandards (base_standards.py)
├── Common patterns (imports, logging, error handling)
├── Quality requirements (docstrings, type hints)
└── Validation methods

DatabaseStandards (database_standards.py)
├── SQLite patterns
├── Schema best practices
└── Query optimization

BackendStandards (backend_standards.py)
├── FastAPI patterns
├── Pydantic model patterns
├── HTTP status codes
├── Database connection management
└── Error handling requirements

FrontendStandards (frontend_standards.py)
├── Streamlit patterns
├── Form handling
├── Data display
└── API integration

TestStandards (test_standards.py)
├── pytest patterns
├── Integration test structure
├── Fixture patterns
└── Assertion standards
```

### Backend Standards Detail

**Critical Patterns (addresses TechLeadSWEA validation):**

**1. Database Connection Context Manager:**
```python
from contextlib import contextmanager
import sqlite3
from pathlib import Path

@contextmanager
def get_db_connection():
    db_path = Path("app/database/baes_system.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_db():
    with get_db_connection() as conn:
        yield conn
```

**2. HTTP Status Codes:**
```python
# POST - Create
@router.post("/", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)

# GET - Read
@router.get("/", response_model=List[EntityResponse])
@router.get("/{id}", response_model=EntityResponse)

# PUT - Update
@router.put("/{id}", response_model=EntityResponse)

# DELETE - Remove
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity(id: int, db: sqlite3.Connection = Depends(get_db)):
    # ... delete logic ...
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

**3. Error Handling:**
```python
try:
    cursor = db.cursor()
    cursor.execute("INSERT INTO ...", (...))
    db.commit()
    return created_entity
except sqlite3.IntegrityError as e:
    logger.error(f"Database integrity error: {e}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Integrity constraint violation: {str(e)}"
    )
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )
```

### Code Validation Process

**TechLeadSWEA Validation Checks:**

1. **Database Connection Pattern**
   - ✓ Uses @contextmanager
   - ✓ Has try/yield/except/finally structure
   - ✓ Includes conn.rollback() in except
   - ✓ Includes conn.close() in finally

2. **HTTP Status Codes**
   - ✓ POST uses 201 Created
   - ✓ DELETE uses 204 No Content
   - ✓ DELETE returns Response(status_code=204)

3. **Error Handling**
   - ✓ Try/except blocks around database ops
   - ✓ Logger.error() before raising exceptions
   - ✓ HTTPException with appropriate status codes
   - ✓ Specific exception types (IntegrityError, etc.)

4. **PEP 8 Compliance**
   - ✓ snake_case for functions/variables
   - ✓ PascalCase for classes
   - ✓ Line length ≤ 100 characters
   - ✓ 4-space indentation

5. **Type Hints & Documentation**
   - ✓ All function parameters have type hints
   - ✓ All functions have return type hints
   - ✓ Public methods have docstrings (Google style)
   - ✓ Complex logic has inline comments

6. **DRY Principle**
   - ✓ No duplicated code blocks
   - ✓ Common patterns extracted to functions
   - ✓ Reusable utilities properly imported

---

## System Flows

### Flow 1: Initial System Generation

```
User: "Create a system to manage students with name, registration, and course"

1. EnhancedRuntimeKernel.process_natural_language_request()
   ├─▶ EntityRecognizer.recognize_entity()
   │   └─▶ OpenAI analysis → "student" (confidence: 0.95)
   │
   ├─▶ BAERegistry.get_bae("student")
   │   └─▶ Returns: StudentBAE instance
   │
   ├─▶ StudentBAE.handle_task("interpret_business_request")
   │   ├─▶ OpenAI.interpret_business_request()
   │   ├─▶ Extract attributes: [name, registration_number, course]
   │   ├─▶ Business vocabulary: [student, registration, enrollment]
   │   └─▶ Returns: SWEA coordination plan
   │
   ├─▶ TechLeadSWEA.handle_task("coordinate_system_generation")
   │   ├─▶ Verify user request compliance
   │   ├─▶ Define quality gates
   │   ├─▶ Create enhanced coordination plan
   │   │
   │   ├─▶ DatabaseSWEA.generate_database_schema()
   │   │   ├─▶ Generate SQL CREATE TABLE
   │   │   ├─▶ TechLeadSWEA review → APPROVED
   │   │   └─▶ Write database_schema.sql
   │   │
   │   ├─▶ BackendSWEA.generate_api_code()
   │   │   ├─▶ Generate Pydantic model
   │   │   ├─▶ Generate FastAPI routes
   │   │   ├─▶ TechLeadSWEA review → REJECTED (retry)
   │   │   ├─▶ Regenerate with feedback
   │   │   ├─▶ TechLeadSWEA review → APPROVED
   │   │   └─▶ Write models/student_model.py, routes/student_routes.py
   │   │
   │   ├─▶ FrontendSWEA.generate_ui_code()
   │   │   ├─▶ Generate Streamlit page
   │   │   ├─▶ TechLeadSWEA review → APPROVED
   │   │   └─▶ Write pages/student_page.py
   │   │
   │   └─▶ TestSWEA.generate_tests()
   │       ├─▶ Generate integration tests
   │       ├─▶ TechLeadSWEA review → APPROVED
   │       └─▶ Write tests/integration/test_student_integration.py
   │
   ├─▶ ManagedSystemManager.ensure_managed_system_structure()
   │   ├─▶ Create directory structure
   │   ├─▶ Generate main.py (FastAPI)
   │   ├─▶ Generate app.py (Streamlit)
   │   ├─▶ Write requirements.txt, .env, README.md
   │   └─▶ Initialize database
   │
   ├─▶ ManagedSystemManager.start_servers()
   │   ├─▶ Start FastAPI (port 8100)
   │   └─▶ Start Streamlit (port 8600)
   │
   └─▶ ContextStore operations
       ├─▶ store_domain_knowledge("student", ...)
       ├─▶ store_agent_memory("StudentBAE", ...)
       └─▶ track_evolution(NEW, ...)

Result: Complete running system at http://localhost:8100 (API) and http://localhost:8600 (UI)
```

### Flow 2: Schema Evolution

```
User: "Add email and age to student"

1. EnhancedRuntimeKernel.process_natural_language_request()
   ├─▶ EntityRecognizer → "student"
   ├─▶ BAERegistry → StudentBAE
   │
   ├─▶ StudentBAE.handle_task("interpret_business_request")
   │   ├─▶ Load previous schema from ContextStore
   │   ├─▶ Previous: [name, registration_number, course]
   │   ├─▶ Current:  [name, registration_number, course, email, age]
   │   ├─▶ Detect evolution: ADDITION
   │   │   └─▶ Added: [email, age]
   │   └─▶ Create evolution coordination plan (is_evolution=True)
   │
   ├─▶ TechLeadSWEA.coordinate_system_generation(is_evolution=True)
   │   ├─▶ Enhanced coordination for evolution
   │   │
   │   ├─▶ DatabaseSWEA.update_schema()
   │   │   ├─▶ Generate ALTER TABLE statements
   │   │   ├─▶ CREATE migration script
   │   │   └─▶ Apply to database (preserving existing data)
   │   │
   │   ├─▶ BackendSWEA.update_api_code()
   │   │   ├─▶ Update Pydantic model (add email, age fields)
   │   │   └─▶ Routes remain compatible (no breaking changes)
   │   │
   │   ├─▶ FrontendSWEA.update_ui_code()
   │   │   └─▶ Update form to include email and age inputs
   │   │
   │   └─▶ TestSWEA.update_tests()
   │       └─▶ Update tests to cover new attributes
   │
   ├─▶ ManagedSystemManager.restart_servers()
   │   ├─▶ Stop existing servers
   │   └─▶ Start with updated code
   │
   └─▶ ContextStore.track_evolution()
       └─▶ Record: Student v1 → v2 (ADDITION: email, age)

Result: Updated system with new attributes, existing data preserved
```

### Flow 3: Dynamic Entity (GenericBAE)

```
User: "Create a system to manage books with title, author, and ISBN"

1. EnhancedRuntimeKernel.process_natural_language_request()
   ├─▶ EntityRecognizer.recognize_entity()
   │   └─▶ OpenAI → "book" (confidence: 0.92)
   │
   ├─▶ BAERegistry.get_bae("book")
   │   └─▶ NOT FOUND (not registered)
   │   └─▶ Fallback: GenericBAE.adapt_entity("book")
   │
   ├─▶ GenericBAE.handle_task("interpret_business_request")
   │   ├─▶ Current entity: "book" (dynamically set)
   │   ├─▶ Extract attributes: [title, author, isbn]
   │   ├─▶ Infer business rules from context
   │   └─▶ Create SWEA coordination plan for "book"
   │
   ├─▶ TechLeadSWEA.coordinate_system_generation()
   │   └─▶ Same SWEA coordination as registered BAEs
   │       (DatabaseSWEA, BackendSWEA, FrontendSWEA, TestSWEA)
   │       with entity="book"
   │
   └─▶ Result: Complete system for Book entity without pre-registration

Note: GenericBAE can handle ANY entity dynamically!
```

---

## Configuration & Environment

### Config Class (`config.py`)

Centralized configuration management.

**Key Settings:**
```python
# OpenAI Configuration
OPENAI_API_KEY: str              # From .env
OPENAI_MODEL: str                # Default: "gpt-4o-mini"

# Server Configuration
API_HOST: str                    # Default: "127.0.0.1"
API_PORT: int                    # Default: 8100
UI_HOST: str                     # Default: "127.0.0.1"
UI_PORT: int                     # Default: 8600

# Database
DATABASE_URL: str                # SQLite path

# Test Environment Detection
IS_TEST_ENVIRONMENT: bool        # Auto-detected

# Path Helpers
get_api_base_url() -> str
get_api_endpoint_url(entity) -> str
get_ui_base_url() -> str
get_managed_system_path() -> Path
```

### Environment Variables

**.env file:**
```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (with defaults)
OPENAI_MODEL=gpt-4o-mini
API_HOST=127.0.0.1
API_PORT=8100
UI_HOST=127.0.0.1
UI_PORT=8600

# Debug Mode
BAE_DEBUG=0                      # 1=verbose logging

# Context Store
BAE_CONTEXT_STORE_PATH=database/context_store.json

# Metrics Logging
BAE_METRICS_LOG=logs/metrics.jsonl
```

### Managed System Paths

```
PROJECT_ROOT/
├── baes/                        # Generator components (SOURCE OF TRUTH)
│   ├── domain_entities/         # BAEs
│   ├── swea_agents/             # SWEAs
│   ├── core/                    # Runtime kernel, registries
│   ├── llm/                     # OpenAI integration
│   ├── standards/               # Code generation standards
│   └── utils/                   # Utilities
│
├── database/                    # Context store
│   └── context_store.json
│
├── logs/                        # LLM request logs, metrics
│   ├── llm_requests/
│   └── metrics.jsonl
│
├── managed_system/              # Generated system (EPHEMERAL OUTPUT)
│   ├── app/                     # FastAPI backend
│   ├── ui/                      # Streamlit frontend
│   └── tests/                   # Integration tests
│
├── tests/                       # Framework tests
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
│
├── config.py                    # Configuration
├── bae_chat.py                  # Interactive CLI
└── bae_noninteractive.py        # Batch processing CLI
```

---

## Testing Architecture

### Testing Philosophy (Constitutional Principle IV)

**Integration-First Approach:**
- Integration tests are **MANDATORY** for critical workflows
- Unit tests are **OPTIONAL** (use only when they add clear value)
- Manual testing is **MANDATORY** before release
- Focus on behavior and outcomes, not implementation details

### Test Organization

```
tests/
├── unit/                        # Optional unit tests
│   ├── agents/
│   ├── core/
│   ├── llm/
│   └── swea_agents/
│
├── integration/                 # Mandatory integration tests
│   ├── test_scenarios.py        # End-to-end scenarios
│   ├── test_student_flow.py     # Student entity workflow
│   ├── test_course_flow.py      # Course entity workflow
│   └── test_evolution.py        # Schema evolution
│
└── conftest.py                  # Shared fixtures
```

### Integration Test Example

```python
# tests/integration/test_student_flow.py
import pytest
import requests
from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel

@pytest.fixture
def kernel():
    """Initialize runtime kernel for testing"""
    return EnhancedRuntimeKernel("database/test_context_store.json")

def test_complete_student_workflow(kernel):
    """Test complete student CRUD workflow"""
    
    # 1. Generate system
    result = kernel.process_natural_language_request(
        "Create a system to manage students with name and registration",
        context="academic",
        start_servers=True
    )
    assert result["success"]
    
    # 2. Wait for servers to start
    time.sleep(5)
    
    # 3. Test API endpoints
    api_url = f"http://localhost:8100/api/students/"
    
    # Create student
    response = requests.post(api_url, json={
        "name": "John Doe",
        "registration_number": "2025001"
    })
    assert response.status_code == 201
    student_id = response.json()["id"]
    
    # Read student
    response = requests.get(f"{api_url}{student_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"
    
    # Update student
    response = requests.put(f"{api_url}{student_id}", json={
        "name": "Jane Doe",
        "registration_number": "2025001"
    })
    assert response.status_code == 200
    
    # Delete student
    response = requests.delete(f"{api_url}{student_id}")
    assert response.status_code == 204
    
    # 4. Verify context store persistence
    domain_knowledge = kernel.context_store.get_domain_knowledge("student")
    assert domain_knowledge is not None
```

### Test Fixtures

```python
# conftest.py
import pytest
from pathlib import Path
import shutil

@pytest.fixture(scope="session")
def test_context_store(tmp_path_factory):
    """Temporary context store for testing"""
    store_path = tmp_path_factory.mktemp("database") / "test_context_store.json"
    yield str(store_path)
    # Cleanup after all tests
    if store_path.exists():
        store_path.unlink()

@pytest.fixture
def clean_managed_system():
    """Clean managed system before test"""
    managed_path = Path("managed_system_test")
    if managed_path.exists():
        shutil.rmtree(managed_path)
    yield managed_path
    # Cleanup after test
    if managed_path.exists():
        shutil.rmtree(managed_path)
```

### Manual Testing Checklist

Before each release, manually verify:

- [ ] System generation from natural language
- [ ] API endpoints (CRUD operations)
- [ ] UI functionality (forms, tables, navigation)
- [ ] Database persistence
- [ ] Schema evolution
- [ ] Error handling (invalid inputs)
- [ ] Server startup/shutdown
- [ ] Context store persistence
- [ ] Multi-entity support
- [ ] GenericBAE fallback for unknown entities

---

## Appendix

### Key Metrics

**Performance Targets:**
- Entity recognition: < 2 seconds
- System generation: < 60 seconds
- API response time: < 100ms (p95)
- UI page load: < 2 seconds

**Quality Metrics:**
- PEP 8 compliance: 100%
- Type hint coverage: 100% for public APIs
- Integration test coverage: > 80% of critical paths
- TechLeadSWEA approval rate: > 90% first attempt

### Common Issues & Solutions

**Issue**: MaxRetriesReachedError during code generation  
**Solution**: Check TechLeadSWEA feedback, update BackendStandards, fix generator

**Issue**: Entity recognition returning "unknown"  
**Solution**: Check confidence score, add keywords to BAE metadata, improve prompt

**Issue**: Server won't start  
**Solution**: Check port availability, review generated code for syntax errors

**Issue**: Schema evolution losing data  
**Solution**: Verify migration scripts, check DatabaseSWEA evolution logic

### Future Enhancements

1. **Multi-LLM Support**: Integrate Claude, Llama, etc.
2. **Advanced Relationships**: Many-to-many, cascading deletes
3. **Authentication/Authorization**: User management, role-based access
4. **Deployment Automation**: Docker, Kubernetes integration
5. **Monitoring Dashboard**: Real-time metrics, performance tracking
6. **Version Control Integration**: Git integration for managed system
7. **Custom SWEA Plugins**: Extensible SWEA architecture
8. **Cross-Context Migration**: Move entities between contexts

---

## Document Metadata

- **Generated**: December 23, 2025
- **Framework Version**: 0.1.0
- **Author**: BAES Development Team
- **Last Updated**: December 23, 2025
- **Constitution Version**: 1.2.0

This architecture document describes the current implementation as of version 0.1.0. All information is derived from actual codebase analysis and reflects production implementation details.
