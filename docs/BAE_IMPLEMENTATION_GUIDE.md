# 🧠 BAE-Driven LLM Multi-Agent System – Implementation Guide

**PROOF-OF-CONCEPT: Academic System with Student BAE**

Based on your thesis proposal and our discussion, this guide implements a runtime-adaptive system where Business Autonomous Entities (BAEs) generate and evolve software dynamically.

---

## 🎯 OBJECTIVES

1. **Demonstrate BAE feasibility** - Student entity as autonomous agent
2. **Runtime system evolution** - Dynamic schema/UI/API generation
3. **Agent orchestration** - BAE + SWEA collaboration
4. **Natural language interaction** - Human-driven system evolution

---

## 🏗️ ARCHITECTURE OVERVIEW

```
Human Input → Runtime Kernel → [Student BAE] → [SWEA Agents] → Generated System
                                     ↓
                              [Programmer Agent]
                              [Frontend Agent]
                                     ↓
                              [FastAPI + Streamlit + SQLite]
```

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
        super().__init__("StudentBAE", "Business Autonomous Entity")
        self.llm_client = OpenAIClient()
        self.current_schema = {}
        
    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if task == "generate_schema":
            return self._generate_schema(payload)
        elif task == "evolve_schema":
            return self._evolve_schema(payload)
        elif task == "validate_business_rules":
            return self._validate_business_rules(payload)
        else:
            return {"error": f"Unknown task: {task}"}
    
    def _generate_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with open("llm/prompts/student_schema.txt", "r") as f:
            prompt = f.read().format(**payload)
        
        system_prompt = """You are a Student BAE responsible for modeling student entities.
        Return only valid Python code for a Pydantic model."""
        
        schema_code = self.llm_client.generate_response(prompt, system_prompt)
        
        self.current_schema = {
            "entity": "Student",
            "code": schema_code,
            "attributes": payload.get("attributes", [])
        }
        
        self.update_memory("current_schema", self.current_schema)
        return self.current_schema
    
    def _evolve_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_memory("current_schema")
        new_attributes = payload.get("new_attributes", [])
        
        prompt = f"""
        Current Student schema:
        {current.get('code', '')}
        
        Add these new attributes: {new_attributes}
        
        Return the updated Pydantic model code.
        """
        
        evolved_code = self.llm_client.generate_response(prompt)
        
        self.current_schema = {
            "entity": "Student",
            "code": evolved_code,
            "attributes": current.get("attributes", []) + new_attributes
        }
        
        self.update_memory("current_schema", self.current_schema)
        return self.current_schema
```

### 4. Programmer Agent (`agents/programmer_agent.py`)
```python
from agents.base_agent import BaseAgent
from llm.openai_client import OpenAIClient
from typing import Dict, Any

class ProgrammerAgent(BaseAgent):
    def __init__(self):
        super().__init__("ProgrammerAgent", "Software Engineering Agent")
        self.llm_client = OpenAIClient()
    
    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if task == "generate_api":
            return self._generate_api(payload)
        elif task == "generate_database":
            return self._generate_database(payload)
        else:
            return {"error": f"Unknown task: {task}"}
    
    def _generate_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with open("llm/prompts/backend_gen.txt", "r") as f:
            prompt = f.read().format(**payload)
        
        system_prompt = """You are a backend developer. Generate FastAPI code with CRUD operations.
        Include proper error handling and SQLAlchemy models."""
        
        api_code = self.llm_client.generate_response(prompt, system_prompt)
        
        return {
            "type": "api",
            "code": api_code,
            "filename": f"{payload.get('entity', 'student').lower()}_routes.py"
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
    def __init__(self):
        self.agents = {
            "student_bae": StudentBAE(),
            "programmer": ProgrammerAgent(),
            "frontend": FrontendAgent()
        }
        self.execution_history = []
    
    def execute_workflow(self, workflow: List[Dict[str, Any]]) -> Dict[str, Any]:
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
                    next_step = workflow[workflow.index(step) + 1]
                    next_step["payload"][step["next_payload_key"]] = result
                
                self.execution_history.append({
                    "agent": agent_name,
                    "task": task,
                    "payload": payload,
                    "result": result
                })
        
        return results
    
    def generate_files(self, results: Dict[str, Any]):
        """Generate actual files from agent results"""
        for key, result in results.items():
            if isinstance(result, dict) and "code" in result:
                filename = result.get("filename", f"{key}.py")
                filepath = f"generated/{self._get_directory(key)}/{filename}"
                
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w") as f:
                    f.write(result["code"])
    
    def _get_directory(self, key: str) -> str:
        if "api" in key or "routes" in key:
            return "routes"
        elif "ui" in key or "frontend" in key:
            return "ui"
        else:
            return "models"
```

---

## 🎯 IMPLEMENTATION WORKFLOW

### Phase 1: Natural Language Input
```python
# Example user input processing
user_input = "Create a student management system with name, email, age, and enrollment_date"

# Parse input and create workflow
workflow = [
    {
        "agent": "student_bae",
        "task": "generate_schema",
        "payload": {"attributes": ["name: str", "email: str", "age: int", "enrollment_date: datetime"]},
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

### Phase 2: Runtime Execution
```python
# Execute the workflow
kernel = RuntimeKernel()
results = kernel.execute_workflow(workflow)
kernel.generate_files(results)

# Start the generated system
import subprocess
subprocess.Popen(["uvicorn", "api.main:app", "--reload"])
subprocess.Popen(["streamlit", "run", "ui/app.py"])
```

---

## 🧪 TESTING SCENARIOS

### 1. Initial System Generation
- User requests student management system
- BAE generates initial schema
- System creates API + UI + DB

### 2. Runtime Evolution
- User adds "grade" attribute to Student
- StudentBAE evolves schema
- System regenerates affected components

### 3. Multi-Agent Collaboration  
- StudentBAE defines business rules
- ProgrammerAgent implements validation
- FrontendAgent creates corresponding UI

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
    volumes:
      - ./generated:/app/generated
      - ./database:/app/database
```

---

## 🎯 DEMO SCRIPT

### Scenario: Academic System Evolution

1. **Initial Request**: "Create a basic student registration system"
2. **BAE Response**: Generates Student entity with basic attributes
3. **System Generation**: API + UI + Database created automatically
4. **Evolution Request**: "Add student grades and GPA tracking"
5. **Runtime Adaptation**: System evolves without restart
6. **Validation**: Show before/after system capabilities

---

## 📊 SUCCESS METRICS

1. **Functional Completeness**: System generates working API + UI + DB
2. **Runtime Adaptability**: System evolves without restart
3. **Agent Collaboration**: BAE + SWEA agents work together
4. **Natural Language Interface**: Users can request changes in plain English
5. **Reusability**: StudentBAE can be reused in different contexts

---

## 🚀 NEXT STEPS

1. **Week 1**: Implement core agents and runtime kernel
2. **Week 2**: Add code generation and dynamic loading
3. **Week 3**: Complete integration, testing, and Docker setup

This proof-of-concept will demonstrate the feasibility of your BAE architecture and provide a solid foundation for your thesis work. 