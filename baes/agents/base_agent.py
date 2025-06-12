import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the BAE system.
    Provides common functionality for both BAE (Business Autonomous Entities)
    and SWEA (Software Engineering Autonomous Agents).
    """

    def __init__(self, name: str, role: str, agent_type: str = "Unknown"):
        self.name = name
        self.role = role
        self.agent_type = agent_type  # "BAE" or "SWEA"
        self.memory = {}
        self.creation_time = datetime.now()
        self.interaction_count = 0

        logger.info(f"Initialized {agent_type} agent: {name} with role: {role}")

    @abstractmethod
    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a specific task. Must be implemented by all agents.

        Args:
            task: The task identifier
            payload: Task-specific data and context

        Returns:
            Dict containing task result and any additional information
        """
        pass

    def update_memory(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None):
        """Update agent memory with optional metadata"""
        memory_item = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "update_count": self.memory.get(key, {}).get("update_count", 0) + 1,
        }

        if metadata:
            memory_item["metadata"] = metadata

        self.memory[key] = memory_item
        logger.debug(f"{self.name}: Updated memory key '{key}'")

    def get_memory(self, key: str, default: Any = None) -> Any:
        """Retrieve memory value"""
        memory_item = self.memory.get(key)
        return memory_item["value"] if memory_item else default

    def get_memory_with_metadata(self, key: str) -> Dict[str, Any]:
        """Retrieve full memory item with metadata"""
        return self.memory.get(key, {})

    def get_full_memory(self, key: str) -> Dict[str, Any]:
        """Retrieve full memory item with metadata (alias for get_memory_with_metadata)"""
        return self.get_memory_with_metadata(key)

    def get_memory_keys(self) -> List[str]:
        """Get all memory keys"""
        return list(self.memory.keys())

    def clear_memory(self, key: Optional[str] = None):
        """Clear specific memory key or all memory"""
        if key:
            if key in self.memory:
                del self.memory[key]
                logger.info(f"{self.name}: Cleared memory key '{key}'")
        else:
            self.memory.clear()
            logger.info(f"{self.name}: Cleared all memory")

    def log_interaction(
        self,
        task: str,
        payload: Dict[str, Any],
        result: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Log agent interaction for traceability and debugging"""
        self.interaction_count += 1

        interaction = {
            "interaction_id": f"{self.name}_{self.interaction_count}",
            "task": task,
            "payload": payload,
            "result": result,
            "success": success,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
            "duration": None,  # Can be added by calling code
        }

        # Store in memory
        if "interactions" not in self.memory:
            self.memory["interactions"] = []

        self.memory["interactions"].append(interaction)

        # Keep only last 50 interactions to prevent memory bloat
        if len(self.memory["interactions"]) > 50:
            self.memory["interactions"] = self.memory["interactions"][-50:]

        # Log based on success
        if success:
            logger.info(f"{self.name}: Successfully handled task '{task}'")
        else:
            logger.error(f"{self.name}: Failed to handle task '{task}': {error_message}")

    def get_interaction_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get interaction history"""
        interactions = self.memory.get("interactions", [])
        if isinstance(interactions, dict) and "value" in interactions:
            interactions = interactions["value"]
        elif not isinstance(interactions, list):
            interactions = []
        return interactions[-limit:] if limit else interactions

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and statistics"""
        return {
            "name": self.name,
            "role": self.role,
            "agent_type": self.agent_type,
            "creation_time": self.creation_time.isoformat(),
            "interaction_count": self.interaction_count,
            "memory_keys": len(self.memory),
            "uptime_minutes": (datetime.now() - self.creation_time).total_seconds() / 60,
            "last_interaction": self.get_interaction_history(1),
        }

    def validate_task_payload(
        self, task: str, payload: Dict[str, Any], required_keys: List[str]
    ) -> Dict[str, Any]:
        """Validate that payload contains required keys for a task"""
        missing_keys = [key for key in required_keys if key not in payload]

        if missing_keys:
            error_msg = f"Task '{task}' missing required payload keys: {missing_keys}"
            logger.error(f"{self.name}: {error_msg}")
            return {"valid": False, "error": error_msg, "missing_keys": missing_keys}

        return {"valid": True}

    def create_error_response(
        self, task: str, error_message: str, error_type: str = "processing_error"
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        error_response = {
            "success": False,
            "error": error_message,  # Use error message string instead of boolean
            "error_type": error_type,
            "error_message": error_message,
            "task": task,
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
        }

        self.log_interaction(task, {}, error_response, success=False, error_message=error_message)
        return error_response

    def create_success_response(
        self, task: str, data: Any, additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create standardized success response"""
        response = {
            "success": True,
            "error": False,
            "data": data,
            "task": task,
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
        }

        if additional_info:
            response.update(additional_info)

        self.log_interaction(task, {}, response, success=True)
        return response

    def __str__(self) -> str:
        return f"{self.agent_type}({self.name}): {self.role}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', role='{self.role}', type='{self.agent_type}')>"
