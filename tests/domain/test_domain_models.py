"""
Domain Models Tests - Test model validation and methods

Tests PropertyValue, EntityProperty, EntityProperties, and model validators.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from timelines_mcp.domain.models import (
    EntityProperties,
    EntityProperty,
    Event,
    EventParticipation,
    EventType,
    ParticipationRole,
    PropertyValue,
    Relationship,
    RelationType,
    SourceType,
)


# ==========================================
# PROPERTY VALUE TESTS
# ==========================================


def test_property_value_string():
    """Test PropertyValue with string value"""
    prop = PropertyValue(string_val="test_string")
    assert prop.get_value() == "test_string"
    assert prop.string_val == "test_string"
    assert prop.number_val is None
    assert prop.boolean_val is None
    assert prop.datetime_val is None


def test_property_value_number():
    """Test PropertyValue with number value"""
    prop = PropertyValue(number_val=Decimal("123.45"))
    assert prop.get_value() == Decimal("123.45")
    assert prop.number_val == Decimal("123.45")
    assert prop.string_val is None
    assert prop.boolean_val is None
    assert prop.datetime_val is None


def test_property_value_boolean():
    """Test PropertyValue with boolean value"""
    prop = PropertyValue(boolean_val=True)
    assert prop.get_value() is True
    assert prop.boolean_val is True
    assert prop.string_val is None
    assert prop.number_val is None
    assert prop.datetime_val is None


def test_property_value_datetime():
    """Test PropertyValue with datetime value"""
    now = datetime.now(UTC)
    prop = PropertyValue(datetime_val=now)
    assert prop.get_value() == now
    assert prop.datetime_val == now
    assert prop.string_val is None
    assert prop.number_val is None
    assert prop.boolean_val is None


def test_property_value_no_value_set():
    """Test PropertyValue with no value raises error"""
    prop = PropertyValue()
    with pytest.raises(ValueError) as exc_info:
        prop.get_value()
    assert "PropertyValue must have exactly one value set" in str(exc_info.value)


def test_property_value_all_none():
    """Test PropertyValue with all None values raises error"""
    prop = PropertyValue(
        string_val=None,
        number_val=None,
        boolean_val=None,
        datetime_val=None,
    )
    with pytest.raises(ValueError) as exc_info:
        prop.get_value()
    assert "PropertyValue must have exactly one value set" in str(exc_info.value)


# ==========================================
# ENTITY PROPERTY TESTS
# ==========================================


def test_entity_property_creation():
    """Test EntityProperty creation"""
    prop_value = PropertyValue(string_val="test")
    entity_prop = EntityProperty(key="name", value=prop_value)
    
    assert entity_prop.key == "name"
    assert entity_prop.value.string_val == "test"


def test_entity_property_key_min_length():
    """Test EntityProperty key must have minimum length"""
    prop_value = PropertyValue(string_val="test")
    
    # Valid key with 1 character
    entity_prop = EntityProperty(key="x", value=prop_value)
    assert entity_prop.key == "x"
    
    # Invalid key with 0 characters
    with pytest.raises(ValidationError) as exc_info:
        EntityProperty(key="", value=prop_value)
    assert "key" in str(exc_info.value)


# ==========================================
# ENTITY PROPERTIES TESTS
# ==========================================


def test_entity_properties_get_existing():
    """Test EntityProperties.get() with existing key"""
    props = EntityProperties()
    prop_value = PropertyValue(string_val="value1")
    props.set("key1", prop_value)
    
    retrieved = props.get("key1")
    assert retrieved is not None
    assert retrieved.string_val == "value1"


def test_entity_properties_get_non_existing():
    """Test EntityProperties.get() with non-existing key"""
    props = EntityProperties()
    retrieved = props.get("nonexistent")
    assert retrieved is None


def test_entity_properties_set():
    """Test EntityProperties.set() creates property"""
    props = EntityProperties()
    prop_value = PropertyValue(number_val=Decimal("42"))
    
    props.set("score", prop_value)
    
    assert "score" in props.properties
    assert props.properties["score"].key == "score"
    assert props.properties["score"].value.number_val == Decimal("42")


def test_entity_properties_set_overwrite():
    """Test EntityProperties.set() overwrites existing property"""
    props = EntityProperties()
    
    # Set initial value
    props.set("key", PropertyValue(string_val="old"))
    assert props.get("key").string_val == "old"
    
    # Overwrite with new value
    props.set("key", PropertyValue(string_val="new"))
    assert props.get("key").string_val == "new"


def test_entity_properties_multiple_keys():
    """Test EntityProperties with multiple keys"""
    props = EntityProperties()
    
    props.set("name", PropertyValue(string_val="Alice"))
    props.set("age", PropertyValue(number_val=Decimal("30")))
    props.set("active", PropertyValue(boolean_val=True))
    
    assert len(props.properties) == 3
    assert props.get("name").string_val == "Alice"
    assert props.get("age").number_val == Decimal("30")
    assert props.get("active").boolean_val is True


# ==========================================
# EVENT VALIDATOR TESTS
# ==========================================


def test_event_end_timestamp_after_timestamp():
    """Test Event validator: end_timestamp must be after timestamp"""
    from uuid import uuid4
    
    start = datetime(2023, 1, 1, 10, 0, 0, tzinfo=UTC)
    end = datetime(2023, 1, 1, 11, 0, 0, tzinfo=UTC)
    
    # Valid: end after start
    event = Event(
        timeline_id=uuid4(),
        timestamp=start,
        end_timestamp=end,
        event_type=EventType.OBSERVATION,
        description="Test event",
    )
    assert event.timestamp == start
    assert event.end_timestamp == end


def test_event_end_timestamp_validation_error():
    """Test Event validator rejects end_timestamp before timestamp"""
    from uuid import uuid4
    
    start = datetime(2023, 1, 1, 10, 0, 0, tzinfo=UTC)
    end = datetime(2023, 1, 1, 9, 0, 0, tzinfo=UTC)  # Before start
    
    with pytest.raises(ValidationError) as exc_info:
        Event(
            timeline_id=uuid4(),
            timestamp=start,
            end_timestamp=end,
            event_type=EventType.OBSERVATION,
            description="Test event",
        )
    assert "end_timestamp must be after timestamp" in str(exc_info.value)


def test_event_end_timestamp_equal_validation_error():
    """Test Event validator rejects end_timestamp equal to timestamp"""
    from uuid import uuid4
    
    same_time = datetime(2023, 1, 1, 10, 0, 0, tzinfo=UTC)
    
    with pytest.raises(ValidationError) as exc_info:
        Event(
            timeline_id=uuid4(),
            timestamp=same_time,
            end_timestamp=same_time,
            event_type=EventType.OBSERVATION,
            description="Test event",
        )
    assert "end_timestamp must be after timestamp" in str(exc_info.value)


def test_event_end_timestamp_none_is_valid():
    """Test Event with None end_timestamp is valid"""
    from uuid import uuid4
    
    event = Event(
        timeline_id=uuid4(),
        timestamp=datetime.now(UTC),
        end_timestamp=None,
        event_type=EventType.OBSERVATION,
        description="Test event",
    )
    assert event.end_timestamp is None


# ==========================================
# RELATIONSHIP VALIDATOR TESTS
# ==========================================


def test_relationship_valid_until_after_valid_from():
    """Test Relationship validator: valid_until must be after valid_from"""
    from uuid import uuid4
    
    start = datetime(2023, 1, 1, tzinfo=UTC)
    end = datetime(2023, 12, 31, tzinfo=UTC)
    
    # Valid: end after start
    rel = Relationship(
        source_id=uuid4(),
        source_type=SourceType.EVENT,
        target_id=uuid4(),
        target_type=SourceType.EVENT,
        relation_type=RelationType.TEMPORAL,
        valid_from=start,
        valid_until=end,
    )
    assert rel.valid_from == start
    assert rel.valid_until == end


def test_relationship_valid_until_validation_error():
    """Test Relationship validator rejects valid_until before valid_from"""
    from uuid import uuid4
    
    start = datetime(2023, 12, 31, tzinfo=UTC)
    end = datetime(2023, 1, 1, tzinfo=UTC)  # Before start
    
    with pytest.raises(ValidationError) as exc_info:
        Relationship(
            source_id=uuid4(),
            source_type=SourceType.EVENT,
            target_id=uuid4(),
            target_type=SourceType.EVENT,
            relation_type=RelationType.TEMPORAL,
            valid_from=start,
            valid_until=end,
        )
    assert "valid_until must be after valid_from" in str(exc_info.value)


def test_relationship_valid_until_equal_validation_error():
    """Test Relationship validator rejects valid_until equal to valid_from"""
    from uuid import uuid4
    
    same_time = datetime(2023, 1, 1, tzinfo=UTC)
    
    with pytest.raises(ValidationError) as exc_info:
        Relationship(
            source_id=uuid4(),
            source_type=SourceType.EVENT,
            target_id=uuid4(),
            target_type=SourceType.EVENT,
            relation_type=RelationType.TEMPORAL,
            valid_from=same_time,
            valid_until=same_time,
        )
    assert "valid_until must be after valid_from" in str(exc_info.value)


def test_relationship_valid_dates_none_is_valid():
    """Test Relationship with None valid_from and valid_until is valid"""
    from uuid import uuid4
    
    rel = Relationship(
        source_id=uuid4(),
        source_type=SourceType.EVENT,
        target_id=uuid4(),
        target_type=SourceType.EVENT,
        relation_type=RelationType.TEMPORAL,
        valid_from=None,
        valid_until=None,
    )
    assert rel.valid_from is None
    assert rel.valid_until is None


# ==========================================
# PARTICIPATION ROLE TESTS
# ==========================================


def test_participation_role_all_roles():
    """Test ParticipationRole.all_roles() returns all standard roles"""
    roles = ParticipationRole.all_roles()
    
    assert isinstance(roles, list)
    assert len(roles) == 10  # All standard roles
    
    # Verify all expected roles are present
    assert ParticipationRole.ACTOR in roles
    assert ParticipationRole.SUBJECT in roles
    assert ParticipationRole.LOCATION in roles
    assert ParticipationRole.OBSERVER in roles
    assert ParticipationRole.TOOL in roles
    assert ParticipationRole.TARGET in roles
    assert ParticipationRole.POSSESSION in roles
    assert ParticipationRole.CAUSE in roles
    assert ParticipationRole.BENEFICIARY in roles
    assert ParticipationRole.CONTEXT in roles


# ==========================================
# EVENT PARTICIPATION TESTS
# ==========================================


def test_event_participation_role_normalization():
    """Test EventParticipation normalizes role to lowercase"""
    from uuid import uuid4
    
    # Role with uppercase should be normalized
    participation = EventParticipation(
        event_id=uuid4(),
        entity_id=uuid4(),
        role="ACTOR"
    )
    assert participation.role == "actor"
    
    # Role with mixed case should be normalized
    participation = EventParticipation(
        event_id=uuid4(),
        entity_id=uuid4(),
        role="SubJect"
    )
    assert participation.role == "subject"
    
    # Already lowercase role stays the same
    participation = EventParticipation(
        event_id=uuid4(),
        entity_id=uuid4(),
        role="location"
    )
    assert participation.role == "location"


def test_event_participation_role_min_length():
    """Test EventParticipation role must have minimum length"""
    from uuid import uuid4
    
    # Valid role with 1 character
    participation = EventParticipation(
        event_id=uuid4(),
        entity_id=uuid4(),
        role="x"
    )
    assert participation.role == "x"
    
    # Invalid role with 0 characters
    with pytest.raises(ValidationError) as exc_info:
        EventParticipation(
            event_id=uuid4(),
            entity_id=uuid4(),
            role=""
        )
    assert "role" in str(exc_info.value)


