"""
BAES - Business Autonomous Entities Framework

A framework for creating and managing Business Autonomous Entities (BAEs) that represent
domain entities as living, autonomous agents capable of runtime evolution and semantic
coherence between business vocabulary and technical artifacts.

This framework enables:
- Domain entity representation through autonomous agents
- Runtime system generation and evolution
- Semantic coherence between business and technical domains
- Cross-organizational reusability of domain knowledge
"""

__version__ = "0.1.0"
__author__ = "Anderson Martins Gomes"
__email__ = "your.email@example.com"
__description__ = "Business Autonomous Entities Framework for adaptive system generation"

# Base agents
from .agents.base_agent import BaseAgent

# Core imports for easy access - updated for new structure
from .core.context_store import ContextStore
from .domain_entities.academic.course_bae import CourseBae
from .domain_entities.academic.student_bae import StudentBae
from .domain_entities.academic.teacher_bae import TeacherBae

# Domain Entities (BAEs) - direct imports to avoid circular dependencies
from .domain_entities.base_bae import BaseBae
from .domain_entities.generic_bae import GenericBae
from .swea_agents.database_swea import DatabaseSWEA
from .swea_agents.frontend_swea import FrontendSWEA

# SWEA Agents - using actual class names (with SWEA suffix)
from .swea_agents.programmer_swea import ProgrammerSWEA

# Backward compatibility aliases (old naming convention)
StudentBAE = StudentBae
TeacherBAE = TeacherBae
CourseBAE = CourseBae

# New naming aliases for consistency
ProgrammerSwea = ProgrammerSWEA
FrontendSwea = FrontendSWEA
DatabaseSwea = DatabaseSWEA

__all__ = [
    # Core components
    "ContextStore",
    "BaseAgent",
    # Domain Entities (BAEs) - new naming
    "BaseBae",
    "GenericBae",
    "StudentBae",
    "TeacherBae",
    "CourseBae",
    # SWEA Agents - actual class names
    "ProgrammerSWEA",
    "FrontendSWEA",
    "DatabaseSWEA",
    # New naming aliases
    "ProgrammerSwea",
    "FrontendSwea",
    "DatabaseSwea",
    # Backward compatibility - old naming
    "StudentBAE",
    "TeacherBAE",
    "CourseBAE",
]
