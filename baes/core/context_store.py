from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
import os

logger = logging.getLogger(__name__)

class ContextStore:
    """
    Context Store for BAE System
    
    Manages domain knowledge preservation, agent memory, and semantic coherence
    across runtime evolution and context adaptation. Serves as the central
    repository for business vocabulary, domain rules, and entity relationships.
    """
    
    def __init__(self, storage_path: str = "database/context_store.json"):
        self.storage_path = storage_path
        self.database_path = storage_path  # Alias for tests compatibility
        self.domain_contexts = {}
        self.agent_memories = {}
        self.business_vocabularies = {}
        self.entity_relationships = {}
        self.evolution_history = []
        self.domain_knowledge = {}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # Load existing data
        self._load_from_storage()
        
        # Save initial structure if file doesn't exist or is empty
        if not os.path.exists(storage_path) or os.path.getsize(storage_path) == 0:
            self._save_to_storage()
        
        logger.info(f"ContextStore initialized with storage: {storage_path}")
    
    def store_domain_context(self, context_name: str, context_data: Dict[str, Any], 
                           entity_focus: str = "Student") -> bool:
        """Store domain context with business vocabulary preservation"""
        try:
            context_entry = {
                "context_name": context_name,
                "entity_focus": entity_focus,
                "context_data": context_data,
                "timestamp": datetime.now().isoformat(),
                "version": self._get_next_version(context_name)
            }
            
            if context_name not in self.domain_contexts:
                self.domain_contexts[context_name] = []
            
            self.domain_contexts[context_name].append(context_entry)
            
            # Save to persistent storage
            self._save_to_storage()
            
            logger.info(f"Stored domain context: {context_name} for entity: {entity_focus}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store domain context {context_name}: {str(e)}")
            return False
    
    def get_domain_context(self, context_name: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieve domain context, optionally specific version"""
        try:
            contexts = self.domain_contexts.get(context_name, [])
            
            if not contexts:
                return None
            
            if version is None:
                # Return latest version
                return contexts[-1]
            else:
                # Return specific version
                for context in contexts:
                    if context.get("version") == version:
                        return context
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve domain context {context_name}: {str(e)}")
            return None
    
    def store_agent_memory(self, agent_name: str, memory_data: Dict[str, Any]) -> bool:
        """Store agent memory for persistence across sessions"""
        try:
            memory_entry = {
                "agent_name": agent_name,
                "memory_data": memory_data,
                "timestamp": datetime.now().isoformat()
            }
            
            self.agent_memories[agent_name] = memory_entry
            self._save_to_storage()
            
            logger.debug(f"Stored memory for agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store agent memory for {agent_name}: {str(e)}")
            return False
    
    def get_agent_memory(self, agent_name: str, key: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve agent memory"""
        try:
            memory_entry = self.agent_memories.get(agent_name)
            if not memory_entry:
                return None
            
            memory_data = memory_entry.get("memory_data", {})
            
            # If key is provided, return specific key value
            if key:
                return memory_data.get(key)
            
            # Otherwise return full memory data
            return memory_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve agent memory for {agent_name}: {str(e)}")
            return None
    
    def get_full_agent_memory(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve full agent memory data (without metadata)"""
        try:
            memory_entry = self.agent_memories.get(agent_name)
            if memory_entry:
                return memory_entry.get("memory_data", {})
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve full agent memory for {agent_name}: {str(e)}")
            return None
    
    def preserve_domain_knowledge(self, entity: str, knowledge: Dict[str, Any]) -> bool:
        """Preserve domain knowledge for an entity"""
        try:
            knowledge_entry = {
                "entity": entity,
                "knowledge": knowledge,
                "timestamp": datetime.now().isoformat()
            }
            
            if not hasattr(self, 'domain_knowledge'):
                self.domain_knowledge = {}
            
            self.domain_knowledge[entity] = knowledge_entry
            self._save_to_storage()
            
            logger.info(f"Preserved domain knowledge for entity: {entity}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to preserve domain knowledge for {entity}: {str(e)}")
            return False
    
    def get_domain_knowledge(self, entity: str) -> Optional[Dict[str, Any]]:
        """Retrieve domain knowledge for an entity"""
        try:
            if not hasattr(self, 'domain_knowledge'):
                self.domain_knowledge = {}
            
            knowledge_entry = self.domain_knowledge.get(entity)
            return knowledge_entry.get("knowledge") if knowledge_entry else None
            
        except Exception as e:
            logger.error(f"Failed to retrieve domain knowledge for {entity}: {str(e)}")
            return None
    
    def track_evolution(self, evolution_event: Dict[str, Any]) -> bool:
        """Track evolution event (enhanced version)"""
        try:
            # Support both direct evolution event and record_evolution format
            if "operation" in evolution_event:
                # Direct evolution event format (as used by tests)
                evolution_entry = {
                    "entity": evolution_event.get("entity", "unknown"),
                    "evolution_type": evolution_event.get("operation", "unknown"),
                    "operation": evolution_event.get("operation", "unknown"),  # Keep original key
                    "changes": evolution_event.get("changes", []),
                    "timestamp": evolution_event.get("timestamp", datetime.now().isoformat()),
                    "success": evolution_event.get("success", True),
                    "evolution_id": len(self.evolution_history) + 1
                }
                
                self.evolution_history.append(evolution_entry)
                self._save_to_storage()
                
                logger.info(f"Tracked evolution: {evolution_event.get('entity')} - {evolution_event.get('operation')}")
                return True
            else:
                # Use record_evolution format
                entity = evolution_event.get("entity", "unknown")
                evolution_type = evolution_event.get("type", "unknown")
                details = evolution_event.get("details", {})
                
                return self.record_evolution(entity, evolution_type, details)
                
        except Exception as e:
            logger.error(f"Failed to track evolution: {str(e)}")
            return False
    
    def clear_agent_memory(self, agent_name: str) -> bool:
        """Clear memory for a specific agent"""
        try:
            if agent_name in self.agent_memories:
                del self.agent_memories[agent_name]
                self._save_to_storage()
                logger.info(f"Cleared memory for agent: {agent_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to clear agent memory for {agent_name}: {str(e)}")
            return False
    
    def update_agent_memory_key(self, agent_name: str, key: str, value: Any) -> bool:
        """Update a specific key in agent memory"""
        try:
            if agent_name not in self.agent_memories:
                self.agent_memories[agent_name] = {
                    "agent_name": agent_name,
                    "memory_data": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            self.agent_memories[agent_name]["memory_data"][key] = value
            self._save_to_storage()
            
            logger.debug(f"Updated memory key '{key}' for agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent memory key for {agent_name}: {str(e)}")
            return False
    
    def get_all_agents(self) -> List[str]:
        """Get list of all agents with stored memory"""
        try:
            return list(self.agent_memories.keys())
        except Exception as e:
            logger.error(f"Failed to get all agents: {str(e)}")
            return []
    
    def get_all_domain_entities(self) -> List[str]:
        """Get list of all domain entities with preserved knowledge"""
        try:
            if not hasattr(self, 'domain_knowledge'):
                self.domain_knowledge = {}
            return list(self.domain_knowledge.keys())
        except Exception as e:
            logger.error(f"Failed to get all domain entities: {str(e)}")
            return []
    
    def backup_and_restore(self, backup_path: str = None) -> Dict[str, Any]:
        """Backup current state and provide restore capability"""
        try:
            backup_data = {
                "domain_contexts": self.domain_contexts,
                "agent_memories": self.agent_memories,
                "business_vocabularies": self.business_vocabularies,
                "entity_relationships": self.entity_relationships,
                "evolution_history": self.evolution_history,
                "timestamp": datetime.now().isoformat()
            }
            
            if hasattr(self, 'domain_knowledge'):
                backup_data["domain_knowledge"] = self.domain_knowledge
            
            if backup_path:
                with open(backup_path, 'w') as f:
                    json.dump(backup_data, f, indent=2)
                logger.info(f"Backup saved to: {backup_path}")
            
            return backup_data
            
        except Exception as e:
            logger.error(f"Failed to backup: {str(e)}")
            return {}
    
    def create_backup(self, backup_path: str) -> bool:
        """Create backup at specified path (alias for backup_and_restore)"""
        try:
            backup_data = self.backup_and_restore(backup_path)
            return len(backup_data) > 0
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return False
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore data from backup file"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            # Restore all data from backup
            self.domain_contexts = backup_data.get("domain_contexts", {})
            self.agent_memories = backup_data.get("agent_memories", {})
            self.business_vocabularies = backup_data.get("business_vocabularies", {})
            self.entity_relationships = backup_data.get("entity_relationships", {})
            self.evolution_history = backup_data.get("evolution_history", [])
            self.domain_knowledge = backup_data.get("domain_knowledge", {})
            
            # Save restored data to storage
            self._save_to_storage()
            
            logger.info(f"Successfully restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {str(e)}")
            return False
    
    def store_business_vocabulary(self, context: str, vocabulary: List[str], 
                                entity_focus: str = "Student") -> bool:
        """Store business vocabulary for semantic coherence"""
        try:
            vocab_entry = {
                "context": context,
                "entity_focus": entity_focus,
                "vocabulary": vocabulary,
                "timestamp": datetime.now().isoformat()
            }
            
            vocab_key = f"{context}_{entity_focus}"
            self.business_vocabularies[vocab_key] = vocab_entry
            self._save_to_storage()
            
            logger.info(f"Stored business vocabulary for {context}/{entity_focus}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store business vocabulary: {str(e)}")
            return False
    
    def get_business_vocabulary(self, context: str, entity_focus: str = "Student") -> List[str]:
        """Retrieve business vocabulary for semantic coherence validation"""
        try:
            vocab_key = f"{context}_{entity_focus}"
            vocab_entry = self.business_vocabularies.get(vocab_key)
            return vocab_entry.get("vocabulary", []) if vocab_entry else []
            
        except Exception as e:
            logger.error(f"Failed to retrieve business vocabulary: {str(e)}")
            return []
    
    def store_entity_relationship(self, primary_entity: str, related_entity: str, 
                                relationship_type: str, context: str = "academic") -> bool:
        """Store entity relationships for domain coherence"""
        try:
            relationship_key = f"{primary_entity}_{related_entity}_{context}"
            relationship_data = {
                "primary_entity": primary_entity,
                "related_entity": related_entity,
                "relationship_type": relationship_type,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
            self.entity_relationships[relationship_key] = relationship_data
            self._save_to_storage()
            
            logger.info(f"Stored relationship: {primary_entity} -> {related_entity} ({relationship_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store entity relationship: {str(e)}")
            return False
    
    def get_entity_relationships(self, entity: str, context: str = "academic") -> List[Dict[str, Any]]:
        """Get all relationships for an entity"""
        relationships = []
        
        try:
            for key, relationship in self.entity_relationships.items():
                if (relationship.get("primary_entity") == entity or 
                    relationship.get("related_entity") == entity) and \
                   relationship.get("context") == context:
                    relationships.append(relationship)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to retrieve entity relationships: {str(e)}")
            return []
    
    def record_evolution(self, entity: str, evolution_type: str, details: Dict[str, Any]) -> bool:
        """Record evolution events for Scenario 2 validation"""
        try:
            evolution_entry = {
                "entity": entity,
                "evolution_type": evolution_type,
                "details": details,
                "timestamp": datetime.now().isoformat(),
                "evolution_id": len(self.evolution_history) + 1
            }
            
            self.evolution_history.append(evolution_entry)
            self._save_to_storage()
            
            logger.info(f"Recorded evolution: {entity} - {evolution_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record evolution: {str(e)}")
            return False
    
    def get_evolution_history(self, entity: Optional[str] = None, entity_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get evolution history for analysis"""
        try:
            # Support both entity and entity_filter parameters for compatibility
            filter_entity = entity or entity_filter
            
            if filter_entity:
                return [entry for entry in self.evolution_history 
                       if entry.get("entity") == filter_entity]
            return self.evolution_history
            
        except Exception as e:
            logger.error(f"Failed to retrieve evolution history: {str(e)}")
            return []
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of all stored contexts for monitoring"""
        return {
            "domain_contexts": list(self.domain_contexts.keys()),
            "agent_memories": list(self.agent_memories.keys()),
            "business_vocabularies": list(self.business_vocabularies.keys()),
            "entity_relationships_count": len(self.entity_relationships),
            "evolution_events": len(self.evolution_history),
            "last_updated": datetime.now().isoformat()
        }
    
    def clear_context(self, context_name: Optional[str] = None) -> bool:
        """Clear specific context or all contexts"""
        try:
            if context_name:
                if context_name in self.domain_contexts:
                    del self.domain_contexts[context_name]
                    self._save_to_storage()
                    logger.info(f"Cleared context: {context_name}")
                return True
            else:
                # Clear all
                self.domain_contexts.clear()
                self.agent_memories.clear()
                self.business_vocabularies.clear()
                self.entity_relationships.clear()
                self.evolution_history.clear()
                self._save_to_storage()
                logger.info("Cleared all contexts")
                return True
                
        except Exception as e:
            logger.error(f"Failed to clear context: {str(e)}")
            return False
    
    def _get_next_version(self, context_name: str) -> int:
        """Get next version number for context"""
        contexts = self.domain_contexts.get(context_name, [])
        if not contexts:
            return 1
        return max(ctx.get("version", 0) for ctx in contexts) + 1
    
    def _save_to_storage(self):
        """Save context store to persistent storage"""
        try:
            # Convert agent_memories to legacy test format for compatibility
            agents_format = {}
            for agent_name, agent_data in self.agent_memories.items():
                agents_format[agent_name] = {
                    "memory": agent_data.get("memory_data", {})
                }
            
            store_data = {
                "domain_contexts": self.domain_contexts,
                "agent_memories": self.agent_memories,
                "agents": agents_format,  # Legacy format for tests
                "business_vocabularies": self.business_vocabularies,
                "entity_relationships": self.entity_relationships,
                "evolution_history": self.evolution_history,
                "domain_knowledge": self.domain_knowledge,
                "last_saved": datetime.now().isoformat()
            }
            
            with open(self.storage_path, "w") as f:
                json.dump(store_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save context store: {str(e)}")
    
    def _load_from_storage(self):
        """Load context store from persistent storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r") as f:
                    store_data = json.load(f)
                
                self.domain_contexts = store_data.get("domain_contexts", {})
                self.agent_memories = store_data.get("agent_memories", {})
                self.business_vocabularies = store_data.get("business_vocabularies", {})
                self.entity_relationships = store_data.get("entity_relationships", {})
                self.evolution_history = store_data.get("evolution_history", [])
                self.domain_knowledge = store_data.get("domain_knowledge", {})
                
                # Support legacy test data format
                if "agents" in store_data and not self.agent_memories:
                    # Convert legacy agent format to current format
                    for agent_name, agent_data in store_data["agents"].items():
                        memory_data = agent_data.get("memory", {})
                        self.agent_memories[agent_name] = {
                            "agent_name": agent_name,
                            "memory_data": memory_data,
                            "timestamp": datetime.now().isoformat()
                        }
                
                # Handle legacy domain knowledge format (override if loading legacy data)
                legacy_domain_knowledge = store_data.get("domain_knowledge", {})
                if legacy_domain_knowledge:
                    # If this is direct legacy format (like test data), use it directly
                    for entity, knowledge in legacy_domain_knowledge.items():
                        if isinstance(knowledge, dict):
                            # Check if this is already in our format or legacy format
                            if "knowledge" in knowledge and "entity" in knowledge:
                                # Already in our format
                                self.domain_knowledge[entity] = knowledge
                            else:
                                # Legacy format - convert it
                                self.domain_knowledge[entity] = {
                                    "entity": entity,
                                    "knowledge": knowledge,
                                    "preserved_timestamp": datetime.now().isoformat()
                                }
                
                logger.info("Loaded existing context store data")
            else:
                logger.info("No existing context store found, starting fresh")
                
        except Exception as e:
            logger.error(f"Failed to load context store: {str(e)}")
            # Continue with empty store 