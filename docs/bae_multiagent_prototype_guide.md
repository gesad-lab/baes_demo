# 🧠 BAE-Driven LLM Multi-Agent System – Implementation Guide

This document outlines the full implementation plan for your prototype: a BAE-based, runtime-adaptive system for generating and evolving information systems using LLM-powered agents, based on the thesis "Agentes Baseados em LLM como Entidades Autônomas de Negócio: Uma Nova Arquitetura para Construção Adaptativa de Sistemas de Informação". The focus is on the entity "Student" in an academic control system, where the Student BAE acts as an autonomous domain entity representative.

---

## 🎯 GOAL

Demonstrate the feasibility of Business Autonomous Entities (BAEs) as domain entity representatives in dynamically creating and evolving a software system (API + UI + DB) at runtime, orchestrating Software Engineering Autonomous Agents (SWEAs), and maintaining semantic coherence between business vocabulary and technical artifacts while interacting with humans through natural language.

---

## 🔧 TECHNOLOGY STACK

- Python 3.11+
- FastAPI (backend generation and live server)
- Streamlit (UI frontend with business vocabulary)
- SQLite (database)
- LangGraph or simple message dispatcher (agent orchestration)
- OpenAI SDK with GPT-4o-mini (LLM agent engine for domain reasoning)
- Jinja2 (template-based code generation with domain focus)
- Pydantic (schema definitions with business rule validation)
- importlib / exec (dynamic module loading for runtime evolution)

---

## 📁 PROJECT STRUCTURE

Create the following structure under your root folder (e.g., bae_academic_system/):

```plaintext
bae_academic_system/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── student_bae.py          # Domain entity representative
│   ├── programmer_agent.py     # SWEA coordinated by BAEs
│   ├── frontend_agent.py       # SWEA coordinated by BAEs
│   └── test_agent.py           # Optional SWEA
│
├── core/
│   ├── __init__.py
│   ├── runtime_kernel.py       # BAE-SWEA orchestration
│   ├── context_store.py        # Domain knowledge preservation
│   └── agent_registry.py       # Agent management
│
├── llm/
│   ├── __init__.py
│   ├── openai_wrapper.py       # GPT-4o-mini integration
│   └── prompts/
│       ├── student_schema.txt   # Domain entity prompts
│       ├── backend_gen.txt      # SWEA coordination prompts
│       └── frontend_form.txt    # Business vocabulary prompts
│
├── generated/
│   ├── models/                  # Generated domain models
│   ├── routes/                  # Generated API endpoints
│   └── ui/                      # Generated business interfaces
│
├── api/
│   └── main.py                  # FastAPI with domain routing
│
├── ui/
│   └── app.py                   # Streamlit with business vocabulary
│
├── database/
│   └── baes_system.db              # Domain data persistence
│
├── .env                         # OpenAI GPT-4o-mini configuration
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## 🧱 STEP-BY-STEP IMPLEMENTATION

### 1. Initialize the Project

```bash
mkdir bae_academic_system
cd bae_academic_system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn openai jinja2 pydantic streamlit python-dotenv sqlalchemy
```

Create .env:

```dotenv
OPENAI_API_KEY=sk-your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///database/baes_system.db
```

### 2. Implement OpenAI Wrapper (llm/openai_wrapper.py)

```python
import openai
import os
from dotenv import load_dotenv

load_dotenv()

class OpenAIWrapper:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def call_openai(self, prompt: str, system_prompt: str = None, temperature: float = 0.2) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

    def generate_domain_response(self, prompt: str, entity_context: str = "Student") -> str:
        """Generate response with domain entity focus"""
        system_prompt = f"""You are working with Business Autonomous Entities (BAEs) that represent domain entities as living, autonomous agents. Focus on maintaining semantic coherence between business vocabulary and technical implementation for the {entity_context} domain entity."""
        return self.call_openai(prompt, system_prompt)
```

### 3. Implement Base Agent (agents/base_agent.py)

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
    def handle(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle specific task with domain or technical focus"""
        pass

    def update_memory(self, key: str, value: Any):
        """Update agent memory for context preservation"""
        self.memory[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }

    def get_memory(self, key: str) -> Any:
        """Retrieve memory value"""
        memory_item = self.memory.get(key)
        return memory_item["value"] if memory_item else None

    def get_full_memory(self, key: str) -> Dict[str, Any]:
        """Retrieve full memory item with metadata"""
        return self.memory.get(key, {})

    def log_interaction(self, task: str, payload: Dict[str, Any], result: Dict[str, Any]):
        """Log agent interaction for traceability"""
        interaction = {
            "task": task,
            "payload": payload,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        if "interactions" not in self.memory:
            self.memory["interactions"] = []
        self.memory["interactions"].append(interaction)
```

### 4. Implement Student BAE (agents/student_bae.py)

```python
from agents.base_agent import BaseAgent
from llm.openai_wrapper import OpenAIWrapper
from typing import Dict, Any, List
import json
import os

class StudentBAE(BaseAgent):
    """
    Business Autonomous Entity representing the Student domain entity.
    Responsible for maintaining semantic coherence between business vocabulary
    and technical artifacts, coordinating SWEA agents, and preserving domain knowledge.
    """

    def __init__(self):
        super().__init__("StudentBAE", "Domain Entity Representative")
        self.llm = OpenAIWrapper()
        self.domain_knowledge = {}
        self.current_schema = {}
        self.context_configurations = {}

    def handle(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain entity tasks maintaining semantic coherence"""
        task_handlers = {
            "interpret_business_request": self._interpret_business_request,
            "generate_schema": self._generate_schema,
            "evolve_schema": self._evolve_schema,
            "configure_context": self._configure_context,
            "coordinate_swea": self._coordinate_swea,
            "validate_domain_rules": self._validate_domain_rules
        }

        if task in task_handlers:
            result = task_handlers[task](payload)
            self.log_interaction(task, payload, result)
            return result
        else:
            return {"error": f"Unknown task: {task}", "supported_tasks": list(task_handlers.keys())}

    def _interpret_business_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret natural language business request and create SWEA coordination plan"""
        business_request = payload.get("request", "")
        context = payload.get("context", "academic")

        prompt = f"""
        As the Student BAE (Business Autonomous Entity), interpret this business request:
        "{business_request}"

        Context: {context}

        Analyze what domain entity operations are needed and create a coordination plan for SWEA agents.

        Return a JSON structure with:
        - interpreted_intent: what the business user wants
        - domain_operations: list of domain entity operations needed
        - swea_coordination: list of SWEA tasks to accomplish the request
        - business_vocabulary: key terms that must be preserved in technical implementation
        """

        response = self.llm.generate_domain_response(prompt, "Student")

        try:
            interpretation = json.loads(response)
            self.update_memory("last_interpretation", interpretation)
            return interpretation
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse business request interpretation",
                "raw_response": response
            }

    def _generate_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Pydantic schema maintaining domain entity focus"""
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")

        # Load domain entity prompt template
        prompt_path = os.path.join("llm", "prompts", "student_schema.txt")
        try:
            with open(prompt_path, "r") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # Fallback prompt
            prompt_template = """
            Generate a Pydantic model for Student entity with attributes: {attributes}
            Context: {context}
            Focus on domain entity representation and business vocabulary.
            """

        prompt = prompt_template.format(attributes=", ".join(attributes), context=context)

        schema_code = self.llm.generate_domain_response(prompt, "Student")

        schema_info = {
            "entity": "Student",
            "code": schema_code,
            "attributes": attributes,
            "context": context,
            "business_rules": self._extract_business_rules(attributes, context)
        }

        self.current_schema = schema_info
        self.update_memory("current_schema", schema_info)
        self._update_domain_knowledge(context, attributes)

        return schema_info

    def _evolve_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evolve schema while preserving domain knowledge and semantic coherence"""
        evolution_request = payload.get("evolution_request", "")
        new_attributes = payload.get("new_attributes", [])

        current_schema = self.get_memory("current_schema")
        if not current_schema:
            return {"error": "No current schema to evolve"}

        prompt = f"""
        As the Student BAE, evolve the current Student entity schema:

        Current Schema Code:
        {current_schema.get('code', '')}

        Current Context: {current_schema.get('context', 'academic')}
        Current Attributes: {current_schema.get('attributes', [])}

        Evolution Request: {evolution_request}
        New Attributes to Add: {new_attributes}

        Generate the evolved Pydantic model code while:
        1. Preserving existing domain knowledge and business rules
        2. Maintaining semantic coherence with business vocabulary
        3. Ensuring compatibility with existing data
        4. Adding new attributes with appropriate domain validation

        Return only the complete updated Python code.
        """

        evolved_code = self.llm.generate_domain_response(prompt, "Student")

        updated_attributes = current_schema.get("attributes", []) + new_attributes

        evolved_schema = {
            "entity": "Student",
            "code": evolved_code,
            "attributes": updated_attributes,
            "context": current_schema.get("context", "academic"),
            "business_rules": self._extract_business_rules(updated_attributes, current_schema.get("context", "academic")),
            "evolution_history": current_schema.get("evolution_history", []) + [evolution_request]
        }

        self.current_schema = evolved_schema
        self.update_memory("current_schema", evolved_schema)

        return evolved_schema

    def _configure_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Configure BAE for different organizational contexts while preserving domain knowledge"""
        target_context = payload.get("target_context", "")
        modifications = payload.get("modifications", [])
        base_context = payload.get("base_context", "academic")

        # Preserve base domain knowledge
        base_knowledge = self.domain_knowledge.get(base_context, {})

        # Configure for new context
        configured_knowledge = {
            "base_knowledge": base_knowledge,
            "context_modifications": modifications,
            "preserved_attributes": base_knowledge.get("core_attributes", []),
            "context_specific_rules": self._generate_context_rules(target_context, modifications)
        }

        self.context_configurations[target_context] = configured_knowledge
        self.update_memory(f"context_config_{target_context}", configured_knowledge)

        return {
            "configured_context": target_context,
            "base_context": base_context,
            "modifications": modifications,
            "reuse_percentage": self._calculate_reuse_percentage(base_knowledge, modifications)
        }

    def _coordinate_swea(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate SWEA agents while maintaining domain entity focus"""
        swea_tasks = payload.get("swea_tasks", [])
        domain_context = payload.get("domain_context", {})

        coordination_plan = []

        for task in swea_tasks:
            swea_task = {
                "swea_agent": task.get("agent", ""),
                "task_type": task.get("task", ""),
                "domain_context": domain_context,
                "business_vocabulary": self._extract_business_vocabulary(),
                "semantic_requirements": {
                    "maintain_domain_coherence": True,
                    "preserve_business_rules": True,
                    "use_business_terminology": True
                }
            }
            coordination_plan.append(swea_task)

        self.update_memory("swea_coordination_plan", coordination_plan)
        return {"coordination_plan": coordination_plan}

    def _validate_domain_rules(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that generated artifacts maintain domain rules and semantic coherence"""
        artifact_code = payload.get("artifact_code", "")
        artifact_type = payload.get("artifact_type", "")

        prompt = f"""
        As the Student BAE, validate this {artifact_type} artifact for domain rule compliance:

        Artifact Code:
        {artifact_code}

        Check for:
        1. Semantic coherence with Student domain entity
        2. Business vocabulary preservation
        3. Domain rule compliance
        4. Business logic consistency

        Return JSON with validation results:
        {{
            "is_valid": boolean,
            "semantic_coherence_score": 0-100,
            "business_vocabulary_preserved": boolean,
            "domain_rules_followed": boolean,
            "issues": [list of issues if any],
            "recommendations": [list of improvements]
        }}
        """

        validation_response = self.llm.generate_domain_response(prompt, "Student")

        try:
            validation_result = json.loads(validation_response)
            return validation_result
        except json.JSONDecodeError:
            return {
                "is_valid": False,
                "error": "Failed to parse validation response",
                "raw_response": validation_response
            }

    def _extract_business_rules(self, attributes: List[str], context: str) -> List[str]:
        """Extract relevant business rules for the domain entity"""
        # Simplified business rules extraction
        # In a real implementation, this would be more sophisticated
        rules = []

        if "email" in str(attributes).lower():
            rules.append("Email must be valid and unique")
        if "age" in str(attributes).lower():
            rules.append("Age must be positive and reasonable for students")
        if "registration" in str(attributes).lower() and context == "academic":
            rules.append("Registration number must be unique within academic context")

        return rules

    def _update_domain_knowledge(self, context: str, attributes: List[str]):
        """Update domain knowledge for reusability"""
        if context not in self.domain_knowledge:
            self.domain_knowledge[context] = {}

        self.domain_knowledge[context].update({
            "core_attributes": attributes,
            "last_updated": datetime.now().isoformat(),
            "usage_count": self.domain_knowledge[context].get("usage_count", 0) + 1
        })

    def _generate_context_rules(self, context: str, modifications: List[str]) -> List[str]:
        """Generate context-specific business rules"""
        rules = []

        if context == "open_courses":
            rules.append("Registration number is optional for open course students")
            rules.append("Modality field is required (in-person/online)")
        elif context == "corporate_training":
            rules.append("Employee ID may substitute for registration number")
            rules.append("Department affiliation is required")

        return rules

    def _extract_business_vocabulary(self) -> List[str]:
        """Extract business vocabulary terms that must be preserved"""
        schema = self.get_memory("current_schema")
        if not schema:
            return []

        # Extract vocabulary from current schema
        vocabulary = ["Student", "Entity", "Academic", "Learning"]

        # Add attribute-specific vocabulary
        attributes = schema.get("attributes", [])
        for attr in attributes:
            if ":" in attr:
                term = attr.split(":")[0].strip()
                vocabulary.append(term.title())

        return list(set(vocabulary))

    def _calculate_reuse_percentage(self, base_knowledge: Dict[str, Any], modifications: List[str]) -> float:
        """Calculate percentage of domain knowledge that can be reused"""
        if not base_knowledge:
            return 0.0

        base_attributes = base_knowledge.get("core_attributes", [])
        if not base_attributes:
            return 0.0

        # Simple calculation - in practice this would be more sophisticated
        modification_count = len(modifications)
        base_count = len(base_attributes)

        if modification_count == 0:
            return 100.0

        reuse_percentage = max(0, (base_count - modification_count) / base_count * 100)
        return round(reuse_percentage, 2)
```

**(Note: The file continues with additional implementation details for SWEA agents, runtime kernel, and integration components, following the same pattern of domain entity focus and semantic coherence emphasis)**

### 5. Continue Implementation

The remaining components (ProgrammerAgent, FrontendAgent, RuntimeKernel) follow the same pattern established in the BAE_IMPLEMENTATION_GUIDE.md, with emphasis on:

- **Domain entity coordination** rather than traditional agent roles
- **Semantic coherence** between business vocabulary and technical artifacts
- **Business vocabulary preservation** throughout all generated code
- **OpenAI GPT-4o-mini** integration for domain reasoning
- **BAE-centered orchestration** where domain entities coordinate technical agents

### 6. Testing and Validation

Follow the validation scenarios outlined in PROOF_OF_CONCEPT.md:

1. **Scenario 1**: Test initial system generation with Student BAE autonomy
2. **Scenario 2**: Test runtime evolution while preserving domain knowledge
3. **Scenario 3**: Test reusability across different organizational contexts

### 7. Deployment

Use Docker configuration from BAE_IMPLEMENTATION_GUIDE.md with proper environment variables for OpenAI GPT-4o-mini.

---

## 🎯 SUCCESS CRITERIA

- **Domain Entity Autonomy**: Student BAE operates independently as domain representative
- **Semantic Coherence**: Business vocabulary preserved throughout technical artifacts
- **Runtime Evolution**: System adapts without losing domain knowledge
- **Cross-Context Reusability**: >80% domain knowledge reuse across organizational contexts
- **Business User Accessibility**: HBEs can interact using familiar business terminology

---

**This implementation guide provides the foundation for validating that Business Autonomous Entities can serve as autonomous domain entity representatives, maintaining semantic coherence and enabling runtime evolution while preserving business vocabulary and domain knowledge across different organizational contexts.**
