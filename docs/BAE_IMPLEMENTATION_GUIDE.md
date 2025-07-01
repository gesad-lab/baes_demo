# 🧠 BAE-Driven LLM Multi-Agent System – Implementation Guide

**PROOF-OF-CONCEPT: Academic System with Student BAE**

Based on the thesis proposal "Agentes Baseados em LLM como Entidades Autônomas de Negócio: Uma Nova Arquitetura para Construção Adaptativa de Sistemas de Informação", this guide implements a runtime-adaptive system where Business Autonomous Entities (BAEs) generate and evolve software dynamically, representing domain entities as living, autonomous agents within the system.

---

## 🎯 OBJECTIVES

**Proof of Concept:** Validate BAE architecture through three progressive scenarios that demonstrate BAEs as autonomous domain entity representatives capable of runtime evolution and semantic reuse:

1. **Scenario 1: Initial Generation** - Automatic creation of functional system via natural language interaction with domain-focused BAEs
2. **Scenario 2: Runtime Evolution** - Dynamic adaptation without system reinitialization, maintaining semantic coherence between business domain and technical artifacts
3. **Scenario 3: Reusability** - Demonstration of BAE configurability across different contexts while preserving domain knowledge
4. **Empirical Validation** - Collection of quantitative and qualitative metrics to validate research questions about domain entity autonomy and reusability

For complete scenario details, see: `docs/PROOF_OF_CONCEPT.md`

---

## 🏗️ ARCHITECTURE OVERVIEW

```
HBE (Human Business Expert) → Enhanced Runtime Kernel → [Student BAE] → [SWEA Agents] → Managed System
                                                              ↓
                                                       [TechLeadSWEA] ←→ [TestSWEA]
                                                              ↓              ↓
                                                       [DatabaseSWEA]  [BackendSWEA]
                                                       [FrontendSWEA]        ↓
                                                              ↓         [Quality Gates]
                                                       [FastAPI + Streamlit + SQLite]
```

**Key Innovation**: Unlike traditional LMA systems that simulate software engineering roles, this architecture centers on Business Autonomous Entities (BAEs) that represent domain entities (like "Student", "Course", "Teacher") as autonomous agents responsible for their semantic modeling, persistence, interface generation, and coordination with auxiliary agents.

**PoC Enhancement**: The system includes automatic server restart functionality that ensures new entities appear immediately in the web UI, making demonstrations seamless and user-friendly.

**TechLeadSWEA Enhancement**: The system now includes a TechLeadSWEA that acts as a technical governance layer, providing:
- Technical architecture decisions and coordination oversight
- Quality gate management and code review authority
- SWEA conflict resolution and autonomous collaboration coordination
- Test-driven development coordination with TestSWEA
- Performance, security, and technical standards enforcement

---

## 📦 PROJECT SETUP

### 1. Directory Structure
```
baes_demo/
├── baes/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── base_agent.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── enhanced_runtime_kernel.py
│   │   ├── bae_registry.py
│   │   ├── context_store.py
│   │   └── managed_system_manager.py
│   ├── domain_entities/
│   │   ├── __init__.py
│   │   ├── base_bae.py
│   │   ├── generic_bae.py
│   │   └── academic/
│   │       ├── __init__.py
│   │       ├── student_bae.py
│   │       ├── course_bae.py
│   │       └── teacher_bae.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── openai_client.py
│   │   └── prompts/
│   │       └── (prompt templates)
│   └── swea_agents/
│       ├── __init__.py
│       ├── database_swea.py
│       ├── backend_swea.py
│       ├── frontend_swea.py
│       ├── test_swea.py
│       └── techlead_swea.py
├── managed_system/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   └── database/
│   └── ui/
│       └── pages/
├── tests/
│   ├── unit/
│   └── integration/
├── database/
├── requirements.txt
├── config.py
├── run_tests.py
└── README.md
```

### 2. Dependencies (requirements.txt)
```
fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.1
openai==1.3.7
pydantic==2.5.0
python-dotenv==1.0.0
requests==2.31.0
pytest==7.4.3
pytest-cov==4.1.0
sqlalchemy==2.0.23
sqlite3
```

### 3. Environment Setup (.env)
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///database/baes_system.db
API_HOST=0.0.0.0
API_PORT=8000
UI_HOST=0.0.0.0
UI_PORT=8501
```

---

## 🤖 CORE COMPONENTS

### 1. Base Agent (`baes/agents/base_agent.py`)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.memory = {}
        self.creation_time = datetime.now()

    @abstractmethod
    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def update_memory(self, key: str, value: Any):
        self.memory[key] = value

    def get_memory(self, key: str) -> Any:
        return self.memory.get(key)
```

### 2. OpenAI Client (`baes/llm/openai_client.py`)
```python
import openai
import os
from dotenv import load_dotenv

load_dotenv()

class OpenAIClient:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2
        )
        return response.choices[0].message.content
```

### 3. Student BAE (`baes/domain_entities/academic/student_bae.py`)
```python
from baes.domain_entities.base_bae import BaseBae
from baes.llm.openai_client import OpenAIClient
from typing import Dict, Any
import json

class StudentBae(BaseBae):
    def __init__(self):
        super().__init__("Student", "academic")
        self.llm_client = OpenAIClient()
        self.current_schema = {}
        self.domain_knowledge = {}

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if task == "generate_schema":
            return self._generate_schema(payload)
        elif task == "evolve_schema":
            return self._evolve_schema(payload)
        elif task == "validate_business_rules":
            return self._validate_business_rules(payload)
        elif task == "configure_context":
            return self._configure_context(payload)
        else:
            return {"error": f"Unknown task: {task}"}

    def _generate_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Pydantic schema maintaining domain entity focus"""
        # Implementation details...
        pass

    def _evolve_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evolve schema while preserving domain knowledge"""
        # Implementation details...
        pass
```

### 4. TechLeadSWEA (`baes/swea_agents/techlead_swea.py`)
```python
from baes.agents.base_agent import BaseAgent
from baes.llm.openai_client import OpenAIClient
from typing import Dict, Any
import json

class TechLeadSWEA(BaseAgent):
    """
    Technical Lead Software Engineering Autonomous Agent responsible for:
    - Technical architecture decisions and technology stack management
    - Quality gate management and code review authority
    - SWEA coordination and conflict resolution
    - Performance, security, and technical standards enforcement
    - Continuous improvement and optimization oversight
    """

    def __init__(self):
        super().__init__("TechLeadSWEA", "Technical Leadership and Coordination Agent")
        self.llm_client = OpenAIClient()
        self.architecture_decisions = {}
        self.quality_standards = {}
        self.conflict_resolution_history = []

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if task == "coordinate_system_generation":
            return self._coordinate_system_generation(payload)
        elif task == "review_and_approve":
            return self._review_and_approve(payload)
        elif task == "resolve_technical_conflict":
            return self._resolve_technical_conflict(payload)
        elif task == "coordinate_test_fixes":
            return self._coordinate_test_fixes(payload)
        else:
            return {"error": f"Unknown task: {task}"}

    def _coordinate_system_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate overall system generation with technical oversight"""
        # Implementation details...
        pass
```

### 5. DatabaseSWEA (`baes/swea_agents/database_swea.py`)
```python
from baes.agents.base_agent import BaseAgent
from typing import Dict, Any
import sqlite3
import os

class DatabaseSWEA(BaseAgent):
    def __init__(self):
        super().__init__("DatabaseSWEA", "Database Management SWEA")

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if task == "setup_database":
            return self._setup_database(payload)
        elif task == "migrate_schema":
            return self._migrate_schema(payload)
        else:
            return {"error": f"Unknown task: {task}"}

    def _setup_database(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Setup database tables for domain entities"""
        # Implementation details...
        pass
```

### 5. ProgrammerSWEA (`baes/swea_agents/programmer_swea.py`)
```python
from baes.agents.base_agent import BaseAgent
from baes.llm.openai_client import OpenAIClient
from typing import Dict, Any

class ProgrammerSWEA(BaseAgent):
    def __init__(self):
        super().__init__("ProgrammerSWEA", "Programming SWEA")
        self.llm_client = OpenAIClient()

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if task == "generate_model":
            return self._generate_model(payload)
        elif task == "generate_api":
            return self._generate_api(payload)
        else:
            return {"error": f"Unknown task: {task}"}

    def _generate_model(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Pydantic models for domain entities"""
        # Implementation details...
        pass

    def _generate_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate FastAPI routes for domain entities"""
        # Implementation details...
        pass
```

### 6. Enhanced Runtime Kernel (`baes/core/enhanced_runtime_kernel.py`)
```python
from baes.domain_entities.academic.student_bae import StudentBae
from baes.domain_entities.academic.course_bae import CourseBae
from baes.domain_entities.academic.teacher_bae import TeacherBae
from baes.swea_agents.database_swea import DatabaseSWEA
from baes.swea_agents.backend_swea import BackendSWEA
from baes.swea_agents.frontend_swea import FrontendSWEA
from baes.swea_agents.test_swea import TestSWEA
from baes.swea_agents.techlead_swea import TechLeadSWEA
from baes.core.bae_registry import EnhancedBAERegistry
from baes.core.managed_system_manager import ManagedSystemManager
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class EnhancedRuntimeKernel:
    """
    Orchestrates interaction between HBEs, BAEs, and SWEAs to enable runtime-adaptive system generation.
    Maintains the dynamic flow where BAEs coordinate with SWEAs based on domain entity needs.
    """
    def __init__(self, context_store_path: str = "database/context_store.json"):
        # BAE registry for multi-entity support
        self.bae_registry = EnhancedBAERegistry()
        self.bae_registry.register_bae("student", StudentBae())
        self.bae_registry.register_bae("course", CourseBae())
        self.bae_registry.register_bae("teacher", TeacherBae())

        # SWEA agents (coordinated by BAEs and TechLeadSWEA)
        self.database_swea = DatabaseSWEA()
        self.backend_swea = BackendSWEA()
        self.frontend_swea = FrontendSWEA()
        self.test_swea = TestSWEA()
        self.techlead_swea = TechLeadSWEA()

        # Managed system manager
        self.managed_system_manager = ManagedSystemManager()

        self.execution_history = []

    def process_natural_language_request(self, request: str, start_servers: bool = True) -> Dict[str, Any]:
        """Process HBE natural language input and route to appropriate BAE"""
        try:
            # Determine entity type from request
            entity_type = self._determine_entity_type(request)

            if not entity_type:
                return {"error": "Could not determine entity type from request", "success": False}

            # Get appropriate BAE
            bae = self.bae_registry.get_bae(entity_type)
            if not bae:
                return {"error": f"No BAE found for entity type: {entity_type}", "success": False}

            # BAE interprets request and creates coordination plan
            interpretation = bae.interpret_business_request(request)

            # Execute coordination plan
            execution_results = self._execute_coordination_plan(
                interpretation.get("swea_coordination", []),
                entity_type
            )

            # Generate managed system files
            if execution_results:
                self.managed_system_manager.generate_managed_system(execution_results, entity_type)

            # Start servers if requested
            if start_servers and execution_results:
                self.managed_system_manager.start_servers()

            return {
                "success": True,
                "entity": entity_type,
                "interpretation": interpretation,
                "execution_results": execution_results
            }

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {"error": str(e), "success": False}

    def _execute_coordination_plan(self, coordination_plan: list, entity_type: str) -> list:
        """Execute SWEA coordination plan created by BAE"""
        results = []

        for task in coordination_plan:
            swea_agent = task.get("swea_agent", "")
            task_type = task.get("task_type", "")
            payload = task.get("payload", {})

            # Route to appropriate SWEA agent
            swea_agent_lower = swea_agent.lower()
            if swea_agent_lower in ["database", "databaseswea", "database_swea"]:
                agent = self.database_swea
            elif swea_agent_lower in ["backend", "backendswea", "backend_swea", "programmer", "programmerswea", "programmer_swea"]:
                agent = self.backend_swea
            elif swea_agent_lower in ["frontend", "frontendswea", "frontend_swea"]:
                agent = self.frontend_swea
            elif swea_agent_lower in ["test", "testswea", "test_swea"]:
                agent = self.test_swea
            elif swea_agent_lower in ["techlead", "techleadswea", "techlead_swea", "tech_lead", "tech_lead_swea"]:
                agent = self.techlead_swea
            else:
                available_agents = ["BackendSWEA", "FrontendSWEA", "DatabaseSWEA", "TestSWEA", "TechLeadSWEA"]
                logger.error("❌ Unknown SWEA agent: %s", swea_agent)
                results.append({
                    "task": f"{swea_agent}.{task_type}",
                    "success": False,
                    "error": f"Unknown SWEA agent: {swea_agent}",
                    "available_agents": available_agents
                })
                continue

            # Execute task
            try:
                result = agent.handle_task(task_type, payload)
                results.append({
                    "task": f"{swea_agent}.{task_type}",
                    "success": True,
                    "result": result
                })
                logger.info("✅ Executed: %s.%s", swea_agent, task_type)
            except Exception as e:
                logger.error("❌ Failed: %s.%s - %s", swea_agent, task_type, str(e))
                results.append({
                    "task": f"{swea_agent}.{task_type}",
                    "success": False,
                    "error": str(e)
                })

        return results

    def _determine_entity_type(self, request: str) -> str:
        """Determine entity type from natural language request"""
        request_lower = request.lower()

        if any(word in request_lower for word in ["student", "aluno", "estudante"]):
            return "student"
        elif any(word in request_lower for word in ["course", "curso", "disciplina"]):
            return "course"
        elif any(word in request_lower for word in ["teacher", "professor", "instrutor"]):
            return "teacher"

        return "student"  # Default to student for POC
```

---

## 🔄 **AUTO-RESTART FEATURE (PoC Enhancement)**

### **Automatic Server Refresh for Multi-Entity Systems**

When adding new entities to an existing system, the BAE CLI automatically restarts servers to ensure the web UI immediately reflects the changes. This is especially important for PoC demonstrations where seamless entity addition is crucial.

#### **How It Works**
1. **Entity Detection**: System detects when new entity models are generated
2. **Smart Restart**: Only restarts if servers are already running and new entities were added
3. **User Feedback**: Clear messages about what's happening and why
4. **Immediate Availability**: New entities appear in web UI without manual intervention

#### **Configuration**
```python
# Default: Enabled for PoC demonstrations
"auto_restart_on_entity_changes": True

# Toggle via CLI command
🔄 HBE> toggle auto restart
✅ Auto-restart ENABLED - Servers will restart automatically after adding new entities

# Or disable for manual control
🔄 HBE> toggle auto restart
⚠️  Auto-restart DISABLED - You'll need to manually restart servers to see new entities
```

#### **Benefits for PoC Validation**
- **Seamless Multi-Entity Demos**: Add Student → Course → Teacher without manual restarts
- **Improved User Experience**: Business experts see immediate results
- **Demonstration Flow**: No interruptions during Scenario 3 (Multi-Entity System) validation
- **Technical Transparency**: Clear feedback about system operations

---

## 🎯 IMPLEMENTATION WORKFLOW

### Phase 1: Natural Language Input Processing
```python
# Example HBE interaction with domain entity focus
hbe_input = "Create a system to manage students with name, email, age, and enrollment_date"

# Enhanced Runtime Kernel routes to Student BAE for domain interpretation
kernel = EnhancedRuntimeKernel()
result = kernel.process_natural_language_request(hbe_input)

# Student BAE orchestrates SWEA agents while maintaining domain coherence
# Coordination plan includes:
# 1. DatabaseSWEA.setup_database
# 2. ProgrammerSWEA.generate_model
# 3. ProgrammerSWEA.generate_api
# 4. FrontendSWEA.generate_ui
```

### Phase 2: Runtime Evolution Example
```python
# HBE requests runtime evolution
evolution_request = "Add birth date and grade point average to student"

# Student BAE handles evolution while preserving domain knowledge
evolution_result = kernel.process_natural_language_request(evolution_request)

# System adapts dynamically without losing semantic coherence
# Managed system files are regenerated and servers restarted
```

---

## 🧪 TESTING SCENARIOS

### 1. Initial System Generation
- HBE provides natural language requirement
- Student BAE interprets domain needs
- BAE coordinates SWEAs to generate system components
- System creates API + UI + DB with domain coherence

### 2. Runtime Evolution
- HBE requests entity modification
- Student BAE handles evolution intelligently
- System regenerates affected components preserving data
- Semantic coherence maintained throughout evolution

### 3. Context Reusability
- Student BAE adapts to different contexts (university vs. open courses)
- Domain knowledge preserved and reconfigured
- Minimal recoding required for new contexts
- Demonstrates BAE reusability across organizations

---

## 🐳 DOCKER CONFIGURATION

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 8501

CMD ["python", "-m", "uvicorn", "managed_system.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'
services:
  bae-system:
    build: .
    ports:
      - "8000:8000"
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=gpt-4o-mini
    volumes:
      - ./managed_system:/app/managed_system
      - ./database:/app/database
```

---

## 🎯 DEMO SCRIPT

### Scenario: Academic System Evolution

1. **Initial Request**: "Create a system to manage students with name, email, and course"
2. **Student BAE Response**: Interprets domain requirements and coordinates SWEA agents
3. **System Generation**: Database + API + UI created automatically with domain focus
4. **Evolution Request**: "Add grade point average and enrollment status to student entity"
5. **Runtime Adaptation**: Student BAE evolves system without restart, maintaining domain coherence
6. **Validation**: Demonstrate semantic consistency between business vocabulary and technical artifacts

---

## 📊 SUCCESS METRICS

1. **Domain Coherence**: Semantic alignment between business concepts and generated code
2. **Runtime Adaptability**: System evolves without restart while preserving domain knowledge
3. **BAE Autonomy**: Domain entities operate as autonomous agents coordinating SWEAs
4. **Natural Language Processing**: HBEs interact using business vocabulary
5. **Reusability**: Student BAE configurable across different academic contexts
6. **Test Coverage**: 100% coverage target with percentage-based reporting

---

## 🚀 NEXT STEPS

1. **Week 1**: Implement core BAE agents and enhanced runtime kernel with domain focus
2. **Week 2**: Add dynamic code generation and SWEA coordination with DatabaseSWEA integration
3. **Week 3**: Complete integration, testing, and Docker setup with full runtime evolution

This proof-of-concept demonstrates the feasibility of BAEs as autonomous domain entity representatives, validating the innovative architecture proposed in the thesis and providing empirical evidence for the research questions about entity autonomy, reusability, and runtime adaptation.
