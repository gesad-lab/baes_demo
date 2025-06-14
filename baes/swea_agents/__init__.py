"""
Software Engineering Autonomous Agents (SWEAs) Package

This package contains SWEA implementations that are coordinated by BAEs
to perform technical software engineering tasks while maintaining
semantic coherence with domain entities.
"""

from .backend_swea import BackendSWEA
from .database_swea import DatabaseSWEA
from .frontend_swea import FrontendSWEA
from .test_swea import TestSWEA

__all__ = ["BackendSWEA", "FrontendSWEA", "DatabaseSWEA", "TestSWEA"]
