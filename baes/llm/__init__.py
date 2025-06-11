"""
BAES LLM Package

Contains language model integration components for the Business Autonomous Entities framework:
- OpenAI client for GPT-4o-mini integration
- Prompt templates for domain entity focus
- LLM utilities for semantic coherence maintenance
"""

from baes.llm.openai_client import OpenAIClient

__all__ = [
    "OpenAIClient",
]
