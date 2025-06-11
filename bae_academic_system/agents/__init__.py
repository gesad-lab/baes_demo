import sys

# Expose this package as top-level 'agents' for backward compatibility in tests
sys.modules.setdefault('agents', sys.modules[__name__])

# BAE Agents (Business Autonomous Entities)
from .base_agent import BaseAgent
from .generic_bae import GenericBAE
from .student_bae import StudentBAE

# SWEA Agents (Software Engineering Autonomous Agents)  
from .programmer_swea import ProgrammerSWEA
from .database_swea import DatabaseSWEA
from .frontend_swea import FrontendSWEA

# Compatibility aliases for import resolution
BaseAgent = BaseAgent
GenericBAE = GenericBAE
StudentBAE = StudentBAE
ProgrammerSWEA = ProgrammerSWEA
DatabaseSWEA = DatabaseSWEA
FrontendSWEA = FrontendSWEA
