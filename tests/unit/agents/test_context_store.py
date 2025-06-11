"""
Unit tests for Context Store module.

Tests the context store functionality including domain knowledge preservation,
agent memory management, and data persistence operations.
"""

import pytest
import json
import os
from baes.core.context_store import ContextStore


@pytest.mark.unit
class TestContextStore:
    """Test suite for Context Store functionality"""
    
    def test_initialization_with_new_file(self, temp_database_path):
        """Test initialization with a new database file"""
        context_store = ContextStore(temp_database_path)
        
        assert context_store.database_path == temp_database_path
        assert os.path.exists(temp_database_path)
        
        # Check initial data structure
        with open(temp_database_path, 'r') as f:
            data = json.load(f)
        
        assert "agents" in data
        assert "domain_knowledge" in data
        assert "evolution_history" in data
    
    def test_initialization_with_existing_file(self, temp_database_path):
        """Test initialization with existing database file"""
        # Create initial data
        initial_data = {
            "agents": {"test_agent": {"memory": {"key": "value"}}},
            "domain_knowledge": {"Student": {"attributes": ["name"]}},
            "evolution_history": []
        }
        
        with open(temp_database_path, 'w') as f:
            json.dump(initial_data, f)
        
        # Initialize context store
        context_store = ContextStore(temp_database_path)
        
        # Verify existing data is preserved
        assert context_store.get_agent_memory("test_agent", "key") == "value"
        assert context_store.get_domain_knowledge("Student")["attributes"] == ["name"]
    
    def test_store_agent_memory(self, temp_database_path):
        """Test storing agent memory"""
        context_store = ContextStore(temp_database_path)
        
        test_data = {
            "current_schema": {
                "entity": "Student",
                "attributes": ["name", "registration"]
            },
            "last_interaction": "generate_schema"
        }
        
        context_store.store_agent_memory("StudentBAE", test_data)
        
        # Verify data was stored
        retrieved_data = context_store.get_agent_memory("StudentBAE", "current_schema")
        assert retrieved_data["entity"] == "Student"
        assert len(retrieved_data["attributes"]) == 2
    
    def test_get_agent_memory_existing(self, temp_database_path):
        """Test retrieving existing agent memory"""
        context_store = ContextStore(temp_database_path)
        
        # Store test data
        context_store.store_agent_memory("TestAgent", {"test_key": "test_value"})
        
        # Retrieve data
        result = context_store.get_agent_memory("TestAgent", "test_key")
        assert result == "test_value"
    
    def test_get_agent_memory_nonexistent(self, temp_database_path):
        """Test retrieving non-existent agent memory"""
        context_store = ContextStore(temp_database_path)
        
        result = context_store.get_agent_memory("NonExistentAgent", "test_key")
        assert result is None
    
    def test_get_full_agent_memory(self, temp_database_path):
        """Test retrieving full agent memory"""
        context_store = ContextStore(temp_database_path)
        
        test_memory = {
            "key1": "value1",
            "key2": {"nested": "value"}
        }
        
        context_store.store_agent_memory("TestAgent", test_memory)
        
        full_memory = context_store.get_full_agent_memory("TestAgent")
        assert full_memory == test_memory
    
    def test_preserve_domain_knowledge(self, temp_database_path):
        """Test domain knowledge preservation"""
        context_store = ContextStore(temp_database_path)
        
        domain_knowledge = {
            "entity": "Student",
            "core_attributes": ["name", "registration", "course"],
            "business_rules": ["Unique registration", "Required name"],
            "contexts": {
                "academic": {"mandatory_fields": ["registration"]},
                "open_courses": {"optional_fields": ["registration"]}
            }
        }
        
        context_store.preserve_domain_knowledge("Student", domain_knowledge)
        
        # Verify knowledge was preserved
        retrieved = context_store.get_domain_knowledge("Student")
        assert retrieved["entity"] == "Student"
        assert len(retrieved["core_attributes"]) == 3
        assert len(retrieved["business_rules"]) == 2
        assert "academic" in retrieved["contexts"]
    
    def test_get_domain_knowledge_existing(self, temp_database_path):
        """Test retrieving existing domain knowledge"""
        context_store = ContextStore(temp_database_path)
        
        knowledge = {"entity": "Student", "version": "1.0"}
        context_store.preserve_domain_knowledge("Student", knowledge)
        
        result = context_store.get_domain_knowledge("Student")
        assert result["entity"] == "Student"
        assert result["version"] == "1.0"
    
    def test_get_domain_knowledge_nonexistent(self, temp_database_path):
        """Test retrieving non-existent domain knowledge"""
        context_store = ContextStore(temp_database_path)
        
        result = context_store.get_domain_knowledge("NonExistentEntity")
        assert result is None
    
    def test_track_evolution(self, temp_database_path):
        """Test evolution history tracking"""
        context_store = ContextStore(temp_database_path)
        
        evolution_event = {
            "entity": "Student",
            "operation": "add_attributes",
            "changes": ["birth_date", "gpa"],
            "timestamp": "2023-01-01T00:00:00",
            "success": True
        }
        
        context_store.track_evolution(evolution_event)
        
        # Verify evolution was tracked
        history = context_store.get_evolution_history()
        assert len(history) == 1
        assert history[0]["entity"] == "Student"
        assert history[0]["operation"] == "add_attributes"
        assert len(history[0]["changes"]) == 2
    
    def test_get_evolution_history_empty(self, temp_database_path):
        """Test getting evolution history when empty"""
        context_store = ContextStore(temp_database_path)
        
        history = context_store.get_evolution_history()
        assert history == []
    
    def test_get_evolution_history_with_filter(self, temp_database_path):
        """Test getting filtered evolution history"""
        context_store = ContextStore(temp_database_path)
        
        # Add multiple evolution events
        events = [
            {"entity": "Student", "operation": "create", "timestamp": "2023-01-01T00:00:00"},
            {"entity": "Course", "operation": "create", "timestamp": "2023-01-02T00:00:00"},
            {"entity": "Student", "operation": "evolve", "timestamp": "2023-01-03T00:00:00"}
        ]
        
        for event in events:
            context_store.track_evolution(event)
        
        # Filter by entity
        student_history = context_store.get_evolution_history(entity_filter="Student")
        assert len(student_history) == 2
        assert all(event["entity"] == "Student" for event in student_history)
    
    def test_clear_agent_memory(self, temp_database_path):
        """Test clearing agent memory"""
        context_store = ContextStore(temp_database_path)
        
        # Store some data
        context_store.store_agent_memory("TestAgent", {"key": "value"})
        assert context_store.get_agent_memory("TestAgent", "key") == "value"
        
        # Clear memory
        context_store.clear_agent_memory("TestAgent")
        assert context_store.get_agent_memory("TestAgent", "key") is None
    
    def test_update_agent_memory_key(self, temp_database_path):
        """Test updating specific agent memory key"""
        context_store = ContextStore(temp_database_path)
        
        # Store initial data
        context_store.store_agent_memory("TestAgent", {"key1": "value1", "key2": "value2"})
        
        # Update specific key
        context_store.update_agent_memory_key("TestAgent", "key1", "updated_value")
        
        # Verify update
        assert context_store.get_agent_memory("TestAgent", "key1") == "updated_value"
        assert context_store.get_agent_memory("TestAgent", "key2") == "value2"
    
    def test_get_all_agents(self, temp_database_path):
        """Test getting all registered agents"""
        context_store = ContextStore(temp_database_path)
        
        # Store data for multiple agents
        context_store.store_agent_memory("StudentBAE", {"test": "data1"})
        context_store.store_agent_memory("ProgrammerSWEA", {"test": "data2"})
        
        agents = context_store.get_all_agents()
        assert "StudentBAE" in agents
        assert "ProgrammerSWEA" in agents
        assert len(agents) == 2
    
    def test_get_all_domain_entities(self, temp_database_path):
        """Test getting all domain entities"""
        context_store = ContextStore(temp_database_path)
        
        # Store knowledge for multiple entities
        context_store.preserve_domain_knowledge("Student", {"entity": "Student"})
        context_store.preserve_domain_knowledge("Course", {"entity": "Course"})
        
        entities = context_store.get_all_domain_entities()
        assert "Student" in entities
        assert "Course" in entities
        assert len(entities) == 2
    
    def test_backup_and_restore(self, temp_database_path):
        """Test backup and restore functionality"""
        context_store = ContextStore(temp_database_path)
        
        # Store test data
        context_store.store_agent_memory("TestAgent", {"key": "value"})
        context_store.preserve_domain_knowledge("Student", {"entity": "Student"})
        
        # Create backup
        backup_path = temp_database_path + ".backup"
        context_store.create_backup(backup_path)
        
        assert os.path.exists(backup_path)
        
        # Clear original data
        context_store.clear_agent_memory("TestAgent")
        
        # Restore from backup
        context_store.restore_from_backup(backup_path)
        
        # Verify data is restored
        assert context_store.get_agent_memory("TestAgent", "key") == "value"
        assert context_store.get_domain_knowledge("Student")["entity"] == "Student"
        
        # Cleanup
        if os.path.exists(backup_path):
            os.unlink(backup_path)
    
    def test_data_persistence_after_reinitialization(self, temp_database_path):
        """Test that data persists after reinitializing context store"""
        # First instance
        context_store1 = ContextStore(temp_database_path)
        context_store1.store_agent_memory("TestAgent", {"persistent": "data"})
        context_store1.preserve_domain_knowledge("Student", {"entity": "Student"})
        
        # Second instance (simulating restart)
        context_store2 = ContextStore(temp_database_path)
        
        # Verify data persists
        assert context_store2.get_agent_memory("TestAgent", "persistent") == "data"
        assert context_store2.get_domain_knowledge("Student")["entity"] == "Student" 