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
HBE (Human Business Expert) → Runtime Kernel → [Student BAE] → [SWEA Agents] → Generated System
                                                      ↓
                                               [Programmer Agent]
                                               [Frontend Agent]  
                                                      ↓
                                               [FastAPI + Streamlit + SQLite]
```

**Key Innovation**: Unlike traditional LMA systems that simulate software engineering roles, this architecture centers on Business Autonomous Entities (BAEs) that represent domain entities (like "Student", "Course", "Professor") as autonomous agents responsible for their semantic modeling, persistence, interface generation, and coordination with auxiliary agents.

---

## 📦 PROJECT SETUP

### 1. Directory Structure
```
bae_academic_system/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── student_bae.py
│   ├── programmer_agent.py
│   └── frontend_agent.py
├── core/
│   ├── __init__.py
│   ├── runtime_kernel.py
│   └── context_store.py
├── llm/
│   ├── __init__.py
│   ├── openai_client.py
│   └── prompts/
│       ├── student_schema.txt
│       ├── backend_gen.txt
│       └── frontend_gen.txt
├── generated/
│   ├── models/
│   ├── routes/
│   └── ui/
├── api/
│   └── main.py
├── ui/
│   └── app.py
├── database/
│   └── academic.db
├── requirements.txt
├── .env
├── Dockerfile
└── README.md
```

### 2. Dependencies (requirements.txt)
```
fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.1
openai==1.3.7
pydantic==2.5.0
jinja2==3.1.2
python-dotenv==1.0.0
sqlite3
requests==2.31.0
pytest==7.4.3
docker==6.1.3
```

### 3. Environment Setup (.env)
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///database/academic.db
API_HOST=0.0.0.0
API_PORT=8000
UI_HOST=0.0.0.0
UI_PORT=8501
```

---

## 🤖 CORE COMPONENTS

### 1. Base Agent (`agents/base_agent.py`)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
import json

class BaseAgent(ABC):
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.memory = {}
        
    @abstractmethod
    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def update_memory(self, key: str, value: Any):
        self.memory[key] = value
    
    def get_memory(self, key: str) -> Any:
        return self.memory.get(key)
```

### 2. OpenAI Client (`llm/openai_client.py`)
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

### 3. Student BAE (`agents/student_bae.py`)
```python
from agents.base_agent import BaseAgent
from llm.openai_client import OpenAIClient
from typing import Dict, Any
import json

class StudentBAE(BaseAgent):
    def __init__(self):
        super().__init__("StudentBAE", "Domain Entity Representative")
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
        with open("llm/prompts/student_schema.txt", "r") as f:
            prompt = f.read().format(**payload)
        
        system_prompt = """You are a Student BAE (Business Autonomous Entity) responsible for representing the "Student" domain entity as a living, autonomous agent within the system. Your role is to maintain semantic coherence between the business domain vocabulary and the technical artifacts generated. Focus on domain entity representation, not software engineering roles."""
        
        schema_code = self.llm_client.generate_response(prompt, system_prompt)
        
        self.current_schema = {
            "entity": "Student",
            "code": schema_code,
            "attributes": payload.get("attributes", []),
            "domain_context": payload.get("context", "academic")
        }
        
        self.update_memory("current_schema", self.current_schema)
        self._update_domain_knowledge(payload)
        return self.current_schema
    
    def _evolve_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_memory("current_schema")
        new_attributes = payload.get("new_attributes", [])
        
        prompt = f"""
        Current Student entity schema:
        {current.get('code', '')}
        
        Evolution request: Add these new attributes: {new_attributes}
        Context: {current.get('domain_context', 'academic')}
        
        As the Student BAE, update the schema while maintaining semantic coherence between business domain concepts and technical implementation. Ensure the evolution preserves existing domain knowledge while extending capabilities.
        
        Return the updated Pydantic model code.
        """
        
        evolved_code = self.llm_client.generate_response(prompt)
        
        self.current_schema = {
            "entity": "Student",
            "code": evolved_code,
            "attributes": current.get("attributes", []) + new_attributes,
            "domain_context": current.get("domain_context", "academic")
        }
        
        self.update_memory("current_schema", self.current_schema)
        return self.current_schema
    
    def _configure_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Configure BAE for different domain contexts while preserving core entity knowledge"""
        context = payload.get("context", "academic")
        modifications = payload.get("modifications", [])
        
        self.domain_knowledge[context] = modifications
        return {"configured_context": context, "modifications": modifications}
    
    def _update_domain_knowledge(self, payload: Dict[str, Any]):
        """Maintain domain knowledge for reusability across contexts"""
        context = payload.get("context", "default")
        self.domain_knowledge[context] = payload.get("attributes", [])
```

### 4. Programmer Agent (`agents/programmer_agent.py`)
```python
from agents.base_agent import BaseAgent
from llm.openai_client import OpenAIClient
from typing import Dict, Any

class ProgrammerAgent(BaseAgent):
    def __init__(self):
        super().__init__("ProgrammerAgent", "Software Engineering Autonomous Agent")
        self.llm_client = OpenAIClient()
    
    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if task == "generate_api":
            return self._generate_api(payload)
        elif task == "generate_database":
            return self._generate_database(payload)
        elif task == "migrate_schema":
            return self._migrate_schema(payload)
        else:
            return {"error": f"Unknown task: {task}"}
    
    def _generate_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with open("llm/prompts/backend_gen.txt", "r") as f:
            prompt = f.read().format(**payload)
        
        system_prompt = """You are a Programmer SWEA (Software Engineering Autonomous Agent) working under coordination of BAEs. Generate FastAPI code that maintains semantic coherence with the domain entity representation provided by the BAE. Include proper error handling and SQLAlchemy models."""
        
        api_code = self.llm_client.generate_response(prompt, system_prompt)
        
        return {
            "type": "api",
            "code": api_code,
            "filename": f"{payload.get('entity', 'student').lower()}_routes.py"
        }
    
    def _migrate_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle runtime schema evolution while preserving data integrity"""
        current_schema = payload.get("current_schema", "")
        new_schema = payload.get("new_schema", "")
        
        prompt = f"""
        Generate SQLAlchemy migration script to evolve database schema from:
        CURRENT: {current_schema}
        TO: {new_schema}
        
        Ensure data preservation and referential integrity during runtime evolution.
        """
        
        migration_code = self.llm_client.generate_response(prompt)
        
        return {
            "type": "migration",
            "code": migration_code,
            "filename": "migration_script.py"
        }
```

### 5. Runtime Kernel (`core/runtime_kernel.py`)
```python
from agents.student_bae import StudentBAE
from agents.programmer_agent import ProgrammerAgent
from agents.frontend_agent import FrontendAgent
from typing import List, Dict, Any
import os

class RuntimeKernel:
    """
    Orchestrates interaction between HBEs, BAEs, and SWEAs to enable runtime-adaptive system generation.
    Maintains the dynamic flow where BAEs coordinate with SWEAs based on domain entity needs.
    """
    def __init__(self):
        self.agents = {
            "student_bae": StudentBAE(),
            "programmer": ProgrammerAgent(),
            "frontend": FrontendAgent()
        }
        self.execution_history = []
        self.active_baes = {}
    
    def process_natural_language_input(self, input_text: str, hbe_context: str = "academic") -> Dict[str, Any]:
        """Process HBE natural language input and route to appropriate BAE"""
        # Simple routing logic - in practice, this would be more sophisticated
        if "student" in input_text.lower():
            return self.route_to_bae("student_bae", input_text, hbe_context)
        else:
            return {"error": "No appropriate BAE found for input"}
    
    def route_to_bae(self, bae_name: str, input_text: str, context: str) -> Dict[str, Any]:
        """Route HBE input to specific BAE for interpretation and orchestration"""
        if bae_name in self.agents:
            bae = self.agents[bae_name]
            # BAE interprets the natural language and determines required SWEA coordination
            interpretation = self._interpret_domain_request(input_text, context, bae)
            return self.execute_bae_workflow(interpretation)
        return {"error": f"BAE {bae_name} not found"}
    
    def execute_bae_workflow(self, workflow: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute workflow coordinated by BAE, maintaining semantic coherence"""
        results = {}
        
        for step in workflow:
            agent_name = step["agent"]
            task = step["task"]
            payload = step["payload"]
            
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                result = agent.handle_task(task, payload)
                results[f"{agent_name}_{task}"] = result
                
                # Pass results to next step if needed
                if "next_payload_key" in step:
                    next_step_index = workflow.index(step) + 1
                    if next_step_index < len(workflow):
                        workflow[next_step_index]["payload"][step["next_payload_key"]] = result
                
                self.execution_history.append({
                    "agent": agent_name,
                    "task": task,
                    "payload": payload,
                    "result": result,
                    "timestamp": self._get_timestamp()
                })
        
        return results
    
    def evolve_system_runtime(self, evolution_request: str, entity: str = "student") -> Dict[str, Any]:
        """Handle runtime system evolution requests through BAE coordination"""
        bae_name = f"{entity}_bae"
        if bae_name in self.agents:
            bae = self.agents[bae_name]
            # BAE handles evolution while maintaining domain coherence
            evolution_workflow = self._create_evolution_workflow(evolution_request, bae)
            return self.execute_bae_workflow(evolution_workflow)
        return {"error": f"BAE for {entity} not found"}
    
    def generate_files(self, results: Dict[str, Any]):
        """Generate actual files from agent results"""
        for key, result in results.items():
            if isinstance(result, dict) and "code" in result:
                filename = result.get("filename", f"{key}.py")
                filepath = f"generated/{self._get_directory(key)}/{filename}"
                
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w") as f:
                    f.write(result["code"])
    
    def _interpret_domain_request(self, input_text: str, context: str, bae) -> List[Dict[str, Any]]:
        """BAE interprets domain request and creates SWEA coordination workflow"""
        # Simplified interpretation - real implementation would use LLM
        if "create" in input_text.lower() or "generate" in input_text.lower():
            return [
                {
                    "agent": bae.name.lower(),
                    "task": "generate_schema", 
                    "payload": {"context": context, "input": input_text}
                },
                {
                    "agent": "programmer",
                    "task": "generate_api",
                    "payload": {"entity": "Student"}
                },
                {
                    "agent": "frontend", 
                    "task": "generate_ui",
                    "payload": {"entity": "Student"}
                }
            ]
        elif "add" in input_text.lower() or "modify" in input_text.lower():
            return [
                {
                    "agent": bae.name.lower(),
                    "task": "evolve_schema",
                    "payload": {"context": context, "input": input_text}
                }
            ]
        return []
    
    def _create_evolution_workflow(self, request: str, bae) -> List[Dict[str, Any]]:
        """Create workflow for runtime evolution"""
        return [
            {
                "agent": bae.name.lower(),
                "task": "evolve_schema",
                "payload": {"evolution_request": request}
            },
            {
                "agent": "programmer", 
                "task": "migrate_schema",
                "payload": {"entity": "Student"}
            }
        ]
    
    def _get_directory(self, key: str) -> str:
        if "api" in key or "routes" in key:
            return "routes"
        elif "ui" in key or "frontend" in key:
            return "ui"
        else:
            return "models"
    
    def _get_timestamp(self):
        import datetime
        return datetime.datetime.now().isoformat()
```

---

## 🎯 IMPLEMENTATION WORKFLOW

### Phase 1: Natural Language Input Processing
```python
# Example HBE interaction with domain entity focus
hbe_input = "Create a system to manage students with name, email, age, and enrollment_date"

# Runtime Kernel routes to Student BAE for domain interpretation
kernel = RuntimeKernel()
result = kernel.process_natural_language_input(hbe_input, context="university")

# Student BAE orchestrates SWEA agents while maintaining domain coherence
workflow = [
    {
        "agent": "student_bae",
        "task": "generate_schema",
        "payload": {
            "attributes": ["name: str", "email: str", "age: int", "enrollment_date: datetime"],
            "context": "university"
        },
        "next_payload_key": "schema"
    },
    {
        "agent": "programmer", 
        "task": "generate_api",
        "payload": {"entity": "Student"}
    },
    {
        "agent": "frontend",
        "task": "generate_ui", 
        "payload": {"entity": "Student"}
    }
]
```

### Phase 2: Runtime Evolution Example
```python
# HBE requests runtime evolution
evolution_request = "Add birth date and grade point average to student"

# Student BAE handles evolution while preserving domain knowledge
evolution_result = kernel.evolve_system_runtime(evolution_request, "student")

# System adapts dynamically without losing semantic coherence
kernel.generate_files(evolution_result)

# Restart services to reflect changes
import subprocess
subprocess.Popen(["uvicorn", "api.main:app", "--reload"])
subprocess.Popen(["streamlit", "run", "ui/app.py"])
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

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
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
      - ./generated:/app/generated
      - ./database:/app/database
```

---

## 🎯 DEMO SCRIPT

### Scenario: Academic System Evolution

1. **Initial Request**: "Create a system to manage students with name, email, and course"
2. **Student BAE Response**: Interprets domain requirements and coordinates SWEA agents
3. **System Generation**: API + UI + Database created automatically with domain focus
4. **Evolution Request**: "Add grade point average and enrollment status to student entity"
5. **Runtime Adaptation**: Student BAE evolves system without restart, maintaining domain coherence
6. **Validation**: Demonstrate semantic consistency between business vocabulary and technical artifacts

---

## 📊 SUCCESS METRICS

1. **Domain Coherence**: Semantic alignment between business concepts and generated code
2. **Runtime Adaptability**: System evolves without restart while preserving domain knowledge
3. **BAE Autonomy**: Domain entities operate as autonomous agents coordinating SWEAs
4. **Natural Language Processing**: HBEs interact using business vocabulary
5. **Reusability**: Student BAE configurable across different academic contexts (university, open courses, etc.)

---

## 🚀 NEXT STEPS

1. **Week 1**: Implement core BAE agents and runtime kernel with domain focus
2. **Week 2**: Add dynamic code generation and SWEA coordination
3. **Week 3**: Complete integration, testing, and Docker setup with full runtime evolution

This proof-of-concept demonstrates the feasibility of BAEs as autonomous domain entity representatives, validating the innovative architecture proposed in the thesis and providing empirical evidence for the research questions about entity autonomy, reusability, and runtime adaptation. 