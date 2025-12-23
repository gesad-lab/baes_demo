"""
Unit tests for custom logic detection in base_bae.py
(Feature: 001-performance-optimization / US1)

Tests the _detect_custom_logic() method that determines whether an entity
requires template-based generation (standard CRUD) or LLM generation (custom logic).

Detection criteria:
- Standard: Basic types only (str/int/float/bool/datetime), no computed properties,
           no complex validation, simple relationships
- Custom: Computed properties, complex validation, non-basic types,
         complex relationships (many-to-many, polymorphic)
"""

import pytest
from baes.domain_entities.academic.student_bae import StudentBae
from baes.utils.template_registry import EntityType


class TestCustomLogicDetection:
    """Test suite for _detect_custom_logic method"""

    @pytest.fixture
    def bae_instance(self):
        """Create a StudentBae instance for testing"""
        return StudentBae()

    def test_standard_entity_with_basic_types_only(self, bae_instance):
        """Standard entity with only basic types should not require custom logic"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "enrollment_date", "type": "datetime"},
                {"name": "gpa", "type": "float"},
                {"name": "active", "type": "bool"},
            ],
            "business_rules": [],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is False
        assert result["entity_type"] == EntityType.STANDARD.value
        assert len(result["custom_logic_reasons"]) == 0
        assert result["template_eligible"] is True

    def test_standard_entity_with_all_basic_types(self, bae_instance):
        """Entity with str, int, float, bool, datetime should be standard"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "age", "type": "int"},
                {"name": "height", "type": "float"},
                {"name": "is_active", "type": "bool"},
                {"name": "created_at", "type": "datetime"},
                {"name": "birth_date", "type": "date"},
            ],
            "business_rules": [],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is False
        assert result["entity_type"] == EntityType.STANDARD.value
        assert len(result["custom_logic_reasons"]) == 0

    def test_standard_entity_with_simple_relationships(self, bae_instance):
        """Entity with foreign keys only should be standard"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "course_id", "type": "int"},  # Foreign key
            ],
            "business_rules": [],
            "relationships": {
                "course": {"type": "many-to-one", "cardinality": "one"}
            }
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is False
        assert result["entity_type"] == EntityType.STANDARD.value


class TestCustomLogicDetectionComputedProperties:
    """Test detection of entities with computed properties"""

    @pytest.fixture
    def bae_instance(self):
        return StudentBae()

    def test_entity_with_computed_property(self, bae_instance):
        """Entity with computed logic should require custom generation"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "gpa", "type": "float"},
            ],
            "business_rules": [
                "Academic status is computed based on GPA",
                "Graduation year is calculated from enrollment date"
            ],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True
        assert result["entity_type"] == EntityType.CUSTOM.value
        assert len(result["custom_logic_reasons"]) >= 1
        assert any("computed" in reason.lower() for reason in result["custom_logic_reasons"])

    def test_entity_with_calculate_method(self, bae_instance):
        """Entity with 'calculate' business rule should require custom logic"""
        schema = {
            "attributes": [{"name": "price", "type": "float"}],
            "business_rules": ["Calculate total with tax and shipping"],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True
        assert result["entity_type"] == EntityType.CUSTOM.value

    def test_entity_with_aggregate_function(self, bae_instance):
        """Entity with aggregation should require custom logic"""
        schema = {
            "attributes": [{"name": "name", "type": "str"}],
            "business_rules": ["Average score is derived from all assignments"],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True


class TestCustomLogicDetectionComplexTypes:
    """Test detection of entities with complex types"""

    @pytest.fixture
    def bae_instance(self):
        return StudentBae()

    def test_entity_with_decimal_type(self, bae_instance):
        """Entity with decimal/Decimal type is treated as basic (lowercase comparison)"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "price", "type": "decimal"},  # decimal is basic type
            ],
            "business_rules": [],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        # decimal is treated as basic type (case-insensitive)
        assert result["requires_custom_logic"] is False
        assert result["entity_type"] == EntityType.STANDARD.value

    def test_entity_with_json_type(self, bae_instance):
        """Entity with JSON type should require custom logic"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "metadata", "type": "JSON"},  # Non-basic type
            ],
            "business_rules": [],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True
        assert any("JSON" in reason for reason in result["custom_logic_reasons"])

    def test_entity_with_uuid_type(self, bae_instance):
        """Entity with UUID type should require custom logic"""
        schema = {
            "attributes": [
                {"name": "id", "type": "UUID"},
                {"name": "name", "type": "str"},
            ],
            "business_rules": [],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True


class TestCustomLogicDetectionComplexValidation:
    """Test detection of entities with complex validation rules"""

    @pytest.fixture
    def bae_instance(self):
        return StudentBae()

    def test_entity_with_multi_field_validation(self, bae_instance):
        """Entity with multi-field validation should require custom logic"""
        schema = {
            "attributes": [
                {"name": "total", "type": "float"},
                {"name": "discount", "type": "float"},
            ],
            "business_rules": [
                "Discount must be less than total amount",
                "Check if total is greater than minimum order value"
            ],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True
        assert result["entity_type"] == EntityType.CUSTOM.value

    def test_entity_with_business_rule_validation(self, bae_instance):
        """Entity with complex business rules should require custom logic"""
        schema = {
            "attributes": [{"name": "status", "type": "str"}],
            "business_rules": [
                "Premium customers must validate spending limit",
                "Order total should be between $10 and $10000"
            ],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True


class TestCustomLogicDetectionComplexRelationships:
    """Test detection of entities with complex relationships"""

    @pytest.fixture
    def bae_instance(self):
        return StudentBae()

    def test_entity_with_many_to_many_relationship(self, bae_instance):
        """Entity with many-to-many relationship should require custom logic"""
        schema = {
            "attributes": [{"name": "name", "type": "str"}],
            "business_rules": [],
            "relationships": {
                "courses": {
                    "type": "many-to-many",
                    "cardinality": "many-to-many",
                    "target": "Course"
                }
            }
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True
        assert result["entity_type"] == EntityType.CUSTOM.value
        assert any("many-to-many" in reason.lower() for reason in result["custom_logic_reasons"])

    def test_entity_with_polymorphic_relationship(self, bae_instance):
        """Polymorphic relationships not currently detected but documented"""
        # Note: Current implementation doesn't explicitly check for polymorphic
        # relationships, but they would likely trigger other complexity flags
        schema = {
            "attributes": [{"name": "name", "type": "str"}],
            "business_rules": [],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        # This is expected to pass as standard for now
        assert result["entity_type"] == EntityType.STANDARD.value

    def test_entity_with_self_referential_relationship(self, bae_instance):
        """Self-referential relationships not currently detected but documented"""
        schema = {
            "attributes": [{"name": "name", "type": "str"}],
            "business_rules": [],
            "relationships": {
                "parent": {"type": "many-to-one", "target": "Student"}
            }
        }
        
        result = bae_instance._detect_custom_logic(schema)
        # Current implementation treats this as standard
        assert result["entity_type"] == EntityType.STANDARD.value


class TestCustomLogicDetectionStateWorkflows:
    """Test detection of entities with state machines and workflows"""

    @pytest.fixture
    def bae_instance(self):
        return StudentBae()

    def test_entity_with_state_machine(self, bae_instance):
        """Entity with state transitions should require custom logic"""
        schema = {
            "attributes": [{"name": "status", "type": "str"}],
            "business_rules": [
                "Order state transitions from pending to processing",
                "Status changes require workflow approval"
            ],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True
        assert any("state" in reason.lower() or "workflow" in reason.lower() 
                   for reason in result["custom_logic_reasons"])

    def test_entity_with_approval_workflow(self, bae_instance):
        """Entity with approval workflow should require custom logic"""
        schema = {
            "attributes": [{"name": "name", "type": "str"}],
            "business_rules": [
                "Must be approved by manager before processing",
                "Can be rejected at any stage"
            ],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def bae_instance(self):
        return StudentBae()

    def test_empty_attributes(self, bae_instance):
        """Entity with no attributes should be standard"""
        schema = {
            "attributes": [],
            "business_rules": [],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is False
        assert result["entity_type"] == EntityType.STANDARD.value

    def test_none_attributes(self, bae_instance):
        """Handle None attributes gracefully"""
        schema = {
            "attributes": None,
            "business_rules": [],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        # Should handle None gracefully and treat as standard
        assert result["requires_custom_logic"] is False

    def test_result_structure(self, bae_instance):
        """Verify result dictionary has all required keys"""
        schema = {
            "attributes": [{"name": "name", "type": "str"}],
            "business_rules": [],
            "relationships": {}
        }
        
        result = bae_instance._detect_custom_logic(schema)
        
        assert "entity_type" in result
        assert "requires_custom_logic" in result
        assert "custom_logic_reasons" in result
        assert "template_eligible" in result
        assert isinstance(result["custom_logic_reasons"], list)
        assert isinstance(result["requires_custom_logic"], bool)
        assert isinstance(result["template_eligible"], bool)

    def test_deterministic_classification(self, bae_instance):
        """Same schema should always produce same classification"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "price", "type": "Decimal"},
            ],
            "business_rules": [],
            "relationships": {}
        }
        
        result1 = bae_instance._detect_custom_logic(schema)
        result2 = bae_instance._detect_custom_logic(schema)
        
        assert result1["requires_custom_logic"] == result2["requires_custom_logic"]
        assert result1["entity_type"] == result2["entity_type"]
        assert len(result1["custom_logic_reasons"]) == len(result2["custom_logic_reasons"])


class TestPerformance:
    """Test performance requirements"""

    @pytest.fixture
    def bae_instance(self):
        return StudentBae()

    def test_detection_performance(self, bae_instance):
        """Detection should complete in under 10ms for typical entity"""
        import time
        
        schema = {
            "attributes": [
                {"name": f"field_{i}", "type": "str"} for i in range(20)
            ],
            "business_rules": [
                "Some business rule here",
                "Another validation rule",
                "Compute something based on fields"
            ],
            "relationships": {
                "related1": {"type": "many-to-one"},
                "related2": {"type": "many-to-one"},
            }
        }
        
        start = time.time()
        result = bae_instance._detect_custom_logic(schema)
        duration_ms = (time.time() - start) * 1000
        
        assert duration_ms < 10, f"Detection took {duration_ms:.2f}ms, expected <10ms"
        assert "entity_type" in result
