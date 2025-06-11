"""
Unit tests for Base Agent module.

Tests the base agent functionality including memory management, 
task handling, and interaction logging.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
from baes.agents.base_agent import BaseAgent


class _TestableAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing"""
    
    def handle_task(self, task: str, payload: dict) -> dict:
        """Test implementation of abstract method"""
        if task == "test_task":
            return {"result": "success", "payload": payload}
        elif task == "error_task":
            return {"error": "Test error"}
        else:
            return {"error": f"Unknown task: {task}"}


@pytest.mark.unit
class TestBaseAgent:
    """Test suite for Base Agent functionality"""
    
    def test_initialization(self):
        """Test agent initialization"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        assert agent.name == "TestAgent"
        assert agent.role == "TestRole"
        assert agent.memory == {}
        assert isinstance(agent.creation_time, datetime)
    
    def test_update_memory_simple_value(self):
        """Test updating memory with simple value"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        agent.update_memory("test_key", "test_value")
        
        assert "test_key" in agent.memory
        memory_item = agent.memory["test_key"]
        assert memory_item["value"] == "test_value"
        assert "timestamp" in memory_item
    
    def test_update_memory_complex_value(self):
        """Test updating memory with complex value"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        complex_value = {
            "nested": {"data": "value"},
            "list": [1, 2, 3],
            "bool": True
        }
        
        agent.update_memory("complex_key", complex_value)
        
        retrieved = agent.get_memory("complex_key")
        assert retrieved["nested"]["data"] == "value"
        assert retrieved["list"] == [1, 2, 3]
        assert retrieved["bool"] is True
    
    def test_get_memory_existing(self):
        """Test retrieving existing memory"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        test_value = {"data": "test"}
        agent.update_memory("test_key", test_value)
        
        result = agent.get_memory("test_key")
        assert result == test_value
    
    def test_get_memory_nonexistent(self):
        """Test retrieving non-existent memory"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        result = agent.get_memory("nonexistent_key")
        assert result is None
    
    def test_get_full_memory(self):
        """Test retrieving full memory item with metadata"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        agent.update_memory("test_key", "test_value")
        
        full_memory = agent.get_full_memory("test_key")
        assert full_memory["value"] == "test_value"
        assert "timestamp" in full_memory
        assert isinstance(full_memory["timestamp"], str)
    
    def test_get_full_memory_nonexistent(self):
        """Test retrieving full memory for non-existent key"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        result = agent.get_full_memory("nonexistent_key")
        assert result == {}
    
    def test_handle_task_success(self):
        """Test successful task handling"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        payload = {"input": "test_input"}
        result = agent.handle_task("test_task", payload)
        
        assert result["result"] == "success"
        assert result["payload"] == payload
    
    def test_handle_task_error(self):
        """Test task handling with error"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        result = agent.handle_task("error_task", {})
        
        assert "error" in result
        assert result["error"] == "Test error"
    
    def test_handle_task_unknown(self):
        """Test handling unknown task"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        result = agent.handle_task("unknown_task", {})
        
        assert "error" in result
        assert "Unknown task" in result["error"]
    
    def test_log_interaction(self):
        """Test interaction logging"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        task = "test_task"
        payload = {"input": "test"}
        result = {"output": "success"}
        
        agent.log_interaction(task, payload, result)
        
        # Check that interaction was logged
        assert "interactions" in agent.memory
        interactions = agent.memory["interactions"]
        assert len(interactions) == 1
        
        logged_interaction = interactions[0]
        assert logged_interaction["task"] == task
        assert logged_interaction["payload"] == payload
        assert logged_interaction["result"] == result
        assert "timestamp" in logged_interaction
    
    def test_log_multiple_interactions(self):
        """Test logging multiple interactions"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        # Log first interaction
        agent.log_interaction("task1", {"input": "1"}, {"output": "1"})
        
        # Log second interaction
        agent.log_interaction("task2", {"input": "2"}, {"output": "2"})
        
        interactions = agent.memory["interactions"]
        assert len(interactions) == 2
        
        assert interactions[0]["task"] == "task1"
        assert interactions[1]["task"] == "task2"
    
    def test_memory_persistence_across_operations(self):
        """Test that memory persists across multiple operations"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        # Store some memory
        agent.update_memory("persistent_key", "persistent_value")
        
        # Handle a task (which might modify memory)
        agent.handle_task("test_task", {"test": "data"})
        
        # Verify original memory is still there
        assert agent.get_memory("persistent_key") == "persistent_value"
    
    def test_memory_update_overwrites_previous(self):
        """Test that memory updates overwrite previous values"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        # Set initial value
        agent.update_memory("test_key", "initial_value")
        assert agent.get_memory("test_key") == "initial_value"
        
        # Update value
        agent.update_memory("test_key", "updated_value")
        assert agent.get_memory("test_key") == "updated_value"
    
    def test_creation_time_set(self):
        """Test that creation time is properly set"""
        before_creation = datetime.now()
        agent = _TestableAgent("TestAgent", "TestRole")
        after_creation = datetime.now()
        
        assert before_creation <= agent.creation_time <= after_creation
    
    def test_agent_identity(self):
        """Test agent identity properties"""
        name = "UniqueAgent"
        role = "SpecialRole"
        agent = _TestableAgent(name, role)
        
        assert agent.name == name
        assert agent.role == role
    
    def test_memory_isolation_between_agents(self):
        """Test that different agents have isolated memory"""
        agent1 = _TestableAgent("Agent1", "Role1")
        agent2 = _TestableAgent("Agent2", "Role2")
        
        agent1.update_memory("shared_key", "agent1_value")
        agent2.update_memory("shared_key", "agent2_value")
        
        assert agent1.get_memory("shared_key") == "agent1_value"
        assert agent2.get_memory("shared_key") == "agent2_value"
    
    def test_memory_with_none_values(self):
        """Test handling None values in memory"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        agent.update_memory("none_key", None)
        assert agent.get_memory("none_key") is None
    
    def test_memory_with_empty_collections(self):
        """Test handling empty collections in memory"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        agent.update_memory("empty_list", [])
        agent.update_memory("empty_dict", {})
        
        assert agent.get_memory("empty_list") == []
        assert agent.get_memory("empty_dict") == {}
    
    def test_interaction_log_timestamp_format(self):
        """Test that interaction log timestamps are in correct format"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        agent.log_interaction("test_task", {}, {})
        
        interactions = agent.memory["interactions"]
        timestamp = interactions[0]["timestamp"]
        
        # Basic check that timestamp is a string and not empty
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
    
    def test_performance_tracking_capability(self):
        """Test that agent can track performance metrics"""
        agent = _TestableAgent("TestAgent", "TestRole")
        
        # Simulate storing performance data
        agent.update_memory("performance_metrics", {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0
        })
        
        # Check that performance data can be retrieved
        metrics = agent.get_memory("performance_metrics")
        assert metrics["total_tasks"] == 0
        assert metrics["successful_tasks"] == 0
        assert metrics["failed_tasks"] == 0 