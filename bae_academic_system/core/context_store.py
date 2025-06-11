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
        self.domain_contexts = {}
        self.agent_memories = {}
        self.business_vocabularies = {}
        self.entity_relationships = {}
        self.evolution_history = []
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # Load existing data
        self._load_from_storage()
        
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
    
    def get_agent_memory(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent memory"""
        try:
            memory_entry = self.agent_memories.get(agent_name)
            return memory_entry.get("memory_data") if memory_entry else None
            
        except Exception as e:
            logger.error(f"Failed to retrieve agent memory for {agent_name}: {str(e)}")
            return None
    
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
    
    def get_evolution_history(self, entity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get evolution history for analysis"""
        try:
            if entity:
                return [entry for entry in self.evolution_history 
                       if entry.get("entity") == entity]
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
            store_data = {
                "domain_contexts": self.domain_contexts,
                "agent_memories": self.agent_memories,
                "business_vocabularies": self.business_vocabularies,
                "entity_relationships": self.entity_relationships,
                "evolution_history": self.evolution_history,
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
                
                logger.info("Loaded existing context store data")
            else:
                logger.info("No existing context store found, starting fresh")
                
        except Exception as e:
            logger.error(f"Failed to load context store: {str(e)}")
            # Continue with empty store 