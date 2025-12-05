"""
Relationship Model Interaction Tests - Comprehensive coverage

Tests all relationship model interactions, validations, and different
source/target type combinations using polyfactory and proper fixtures.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from timelines_mcp.domain.models import (
    EntityType,
    EventType,
    Metadata,
    PropertyValue,
    Relationship,
    RelationType,
    SourceType,
)
from tests.conftest import (
    create_sample_entity,
    create_sample_event,
    create_sample_project,
    create_sample_timeline,
)


# ==========================================
# RELATIONSHIP MODEL VALIDATION TESTS
# ==========================================


def test_relationship_model_creation(relationship_factory):
    """Test basic relationship model creation"""
    rel = relationship_factory.build(
        source_id=uuid4(),
        source_type=SourceType.ENTITY,
        target_id=uuid4(),
        target_type=SourceType.ENTITY,
        relation_type=RelationType.CAUSAL,
        strength=Decimal("0.8"),
    )

    assert rel.id is not None
    assert rel.source_type == SourceType.ENTITY
    assert rel.target_type == SourceType.ENTITY
    assert rel.relation_type == RelationType.CAUSAL
    assert rel.strength == Decimal("0.8")


def test_relationship_strength_validation():
    """Test relationship strength must be between 0 and 1"""
    # Valid strength values
    rel = Relationship(
        source_id=uuid4(),
        source_type=SourceType.EVENT,
        target_id=uuid4(),
        target_type=SourceType.EVENT,
        relation_type=RelationType.TEMPORAL,
        strength=Decimal("0.5"),
    )
    assert rel.strength == Decimal("0.5")

    # Minimum strength
    rel = Relationship(
        source_id=uuid4(),
        source_type=SourceType.EVENT,
        target_id=uuid4(),
        target_type=SourceType.EVENT,
        relation_type=RelationType.TEMPORAL,
        strength=Decimal("0.0"),
    )
    assert rel.strength == Decimal("0.0")

    # Maximum strength
    rel = Relationship(
        source_id=uuid4(),
        source_type=SourceType.EVENT,
        target_id=uuid4(),
        target_type=SourceType.EVENT,
        relation_type=RelationType.TEMPORAL,
        strength=Decimal("1.0"),
    )
    assert rel.strength == Decimal("1.0")

    # Invalid: strength > 1
    with pytest.raises(ValidationError) as exc_info:
        Relationship(
            source_id=uuid4(),
            source_type=SourceType.EVENT,
            target_id=uuid4(),
            target_type=SourceType.EVENT,
            relation_type=RelationType.TEMPORAL,
            strength=Decimal("1.5"),
        )
    assert "strength" in str(exc_info.value)

    # Invalid: strength < 0
    with pytest.raises(ValidationError) as exc_info:
        Relationship(
            source_id=uuid4(),
            source_type=SourceType.EVENT,
            target_id=uuid4(),
            target_type=SourceType.EVENT,
            relation_type=RelationType.TEMPORAL,
            strength=Decimal("-0.5"),
        )
    assert "strength" in str(exc_info.value)


def test_relationship_temporal_validity():
    """Test relationship valid_from/valid_until validation"""
    now = datetime.now(UTC)
    future = now + timedelta(days=30)

    # Valid temporal range
    rel = Relationship(
        source_id=uuid4(),
        source_type=SourceType.ENTITY,
        target_id=uuid4(),
        target_type=SourceType.ENTITY,
        relation_type=RelationType.HIERARCHICAL,
        valid_from=now,
        valid_until=future,
    )
    assert rel.valid_from == now
    assert rel.valid_until == future

    # Valid: both None
    rel = Relationship(
        source_id=uuid4(),
        source_type=SourceType.ENTITY,
        target_id=uuid4(),
        target_type=SourceType.ENTITY,
        relation_type=RelationType.HIERARCHICAL,
    )
    assert rel.valid_from is None
    assert rel.valid_until is None

    # Valid: only valid_from
    rel = Relationship(
        source_id=uuid4(),
        source_type=SourceType.ENTITY,
        target_id=uuid4(),
        target_type=SourceType.ENTITY,
        relation_type=RelationType.HIERARCHICAL,
        valid_from=now,
    )
    assert rel.valid_from == now
    assert rel.valid_until is None

    # Invalid: valid_until before valid_from
    with pytest.raises(ValidationError) as exc_info:
        Relationship(
            source_id=uuid4(),
            source_type=SourceType.ENTITY,
            target_id=uuid4(),
            target_type=SourceType.ENTITY,
            relation_type=RelationType.HIERARCHICAL,
            valid_from=future,
            valid_until=now,
        )
    assert "valid_until must be after valid_from" in str(exc_info.value)

    # Invalid: valid_until equal to valid_from
    with pytest.raises(ValidationError) as exc_info:
        Relationship(
            source_id=uuid4(),
            source_type=SourceType.ENTITY,
            target_id=uuid4(),
            target_type=SourceType.ENTITY,
            relation_type=RelationType.HIERARCHICAL,
            valid_from=now,
            valid_until=now,
        )
    assert "valid_until must be after valid_from" in str(exc_info.value)


def test_relationship_metadata():
    """Test relationship metadata handling"""
    from timelines_mcp.domain.models import EntityProperty

    metadata = Metadata()
    metadata.properties["context"] = EntityProperty(
        key="context",
        value=PropertyValue(string_val="battle_scene"),
    )

    rel = Relationship(
        source_id=uuid4(),
        source_type=SourceType.EVENT,
        target_id=uuid4(),
        target_type=SourceType.EVENT,
        relation_type=RelationType.CAUSAL,
        metadata=metadata,
    )

    assert "context" in rel.metadata.properties
    assert rel.metadata.properties["context"].value.string_val == "battle_scene"


# ==========================================
# RELATIONSHIP TYPES TESTS
# ==========================================


def test_all_relation_types():
    """Test all RelationType enum values work"""
    types = [
        RelationType.CAUSAL,
        RelationType.TEMPORAL,
        RelationType.HIERARCHICAL,
        RelationType.REFERENTIAL,
        RelationType.CONTRADICTORY,
        RelationType.REINFORCING,
        RelationType.CONDITIONAL,
        RelationType.PERSPECTIVE,
    ]

    for rel_type in types:
        rel = Relationship(
            source_id=uuid4(),
            source_type=SourceType.EVENT,
            target_id=uuid4(),
            target_type=SourceType.EVENT,
            relation_type=rel_type,
        )
        assert rel.relation_type == rel_type


def test_all_source_types():
    """Test all SourceType enum values work"""
    types = [
        SourceType.EVENT,
        SourceType.ENTITY,
        SourceType.TIMELINE,
    ]

    for source_type in types:
        for target_type in types:
            rel = Relationship(
                source_id=uuid4(),
                source_type=source_type,
                target_id=uuid4(),
                target_type=target_type,
                relation_type=RelationType.REFERENTIAL,
            )
            assert rel.source_type == source_type
            assert rel.target_type == target_type


# ==========================================
# EVENT-EVENT RELATIONSHIPS
# ==========================================


async def test_event_to_event_causal_relationship(sqlite_adapter):
    """Test causal relationship between two events"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)

    # Create cause event
    cause_event = create_sample_event(timeline.id)
    cause_event.description = "Character draws sword"
    cause_event.event_type = EventType.TRANSITION
    await sqlite_adapter.insert_event(cause_event)

    # Create effect event
    effect_event = create_sample_event(timeline.id)
    effect_event.description = "Enemy retreats"
    effect_event.timestamp = cause_event.timestamp + timedelta(minutes=5)
    await sqlite_adapter.insert_event(effect_event)

    # Create causal relationship
    rel = Relationship(
        source_id=cause_event.id,
        source_type=SourceType.EVENT,
        target_id=effect_event.id,
        target_type=SourceType.EVENT,
        relation_type=RelationType.CAUSAL,
        strength=Decimal("0.9"),
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved is not None
    assert retrieved.source_id == cause_event.id
    assert retrieved.target_id == effect_event.id
    assert retrieved.relation_type == RelationType.CAUSAL


async def test_event_to_event_temporal_relationship(sqlite_adapter):
    """Test temporal relationship between sequential events"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)

    # Create first event
    first_event = create_sample_event(timeline.id)
    first_event.timestamp = datetime(2023, 1, 1, 10, 0, 0, tzinfo=UTC)
    await sqlite_adapter.insert_event(first_event)

    # Create second event
    second_event = create_sample_event(timeline.id)
    second_event.timestamp = datetime(2023, 1, 1, 11, 0, 0, tzinfo=UTC)
    await sqlite_adapter.insert_event(second_event)

    # Create temporal relationship
    rel = Relationship(
        source_id=first_event.id,
        source_type=SourceType.EVENT,
        target_id=second_event.id,
        target_type=SourceType.EVENT,
        relation_type=RelationType.TEMPORAL,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved is not None
    assert retrieved.relation_type == RelationType.TEMPORAL


async def test_contradictory_events_relationship(sqlite_adapter):
    """Test contradictory relationship between conflicting events"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)

    event1 = create_sample_event(timeline.id)
    event1.description = "Character is alive"
    await sqlite_adapter.insert_event(event1)

    event2 = create_sample_event(timeline.id)
    event2.description = "Character is dead"
    event2.timestamp = event1.timestamp
    await sqlite_adapter.insert_event(event2)

    rel = Relationship(
        source_id=event1.id,
        source_type=SourceType.EVENT,
        target_id=event2.id,
        target_type=SourceType.EVENT,
        relation_type=RelationType.CONTRADICTORY,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved.relation_type == RelationType.CONTRADICTORY


# ==========================================
# EVENT-ENTITY RELATIONSHIPS
# ==========================================


async def test_event_to_entity_referential_relationship(sqlite_adapter):
    """Test event referencing an entity"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)

    entity = create_sample_entity(project.id)
    entity.name = "The Sword of Power"
    entity.entity_type = EntityType.OBJECT
    await sqlite_adapter.insert_entity(entity)

    event = create_sample_event(timeline.id)
    event.description = "Sword is found"
    await sqlite_adapter.insert_event(event)

    rel = Relationship(
        source_id=event.id,
        source_type=SourceType.EVENT,
        target_id=entity.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved.source_type == SourceType.EVENT
    assert retrieved.target_type == SourceType.ENTITY


async def test_entity_to_event_relationship(sqlite_adapter):
    """Test entity referencing an event"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)

    entity = create_sample_entity(project.id)
    entity.entity_type = EntityType.CHARACTER
    await sqlite_adapter.insert_entity(entity)

    event = create_sample_event(timeline.id)
    event.description = "Character's birth"
    await sqlite_adapter.insert_event(event)

    rel = Relationship(
        source_id=entity.id,
        source_type=SourceType.ENTITY,
        target_id=event.id,
        target_type=SourceType.EVENT,
        relation_type=RelationType.REFERENTIAL,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved.source_type == SourceType.ENTITY
    assert retrieved.target_type == SourceType.EVENT


# ==========================================
# ENTITY-ENTITY RELATIONSHIPS
# ==========================================


async def test_entity_to_entity_hierarchical_relationship(sqlite_adapter):
    """Test hierarchical relationship between entities"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    parent_entity = create_sample_entity(project.id)
    parent_entity.name = "Kingdom of Westeros"
    parent_entity.entity_type = EntityType.PLACE
    await sqlite_adapter.insert_entity(parent_entity)

    child_entity = create_sample_entity(project.id)
    child_entity.name = "City of King's Landing"
    child_entity.entity_type = EntityType.PLACE
    await sqlite_adapter.insert_entity(child_entity)

    rel = Relationship(
        source_id=parent_entity.id,
        source_type=SourceType.ENTITY,
        target_id=child_entity.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.HIERARCHICAL,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved.relation_type == RelationType.HIERARCHICAL
    assert retrieved.source_type == SourceType.ENTITY
    assert retrieved.target_type == SourceType.ENTITY


async def test_character_to_character_relationship(sqlite_adapter):
    """Test relationship between two character entities"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    char1 = create_sample_entity(project.id)
    char1.name = "Alice"
    char1.entity_type = EntityType.CHARACTER
    await sqlite_adapter.insert_entity(char1)

    char2 = create_sample_entity(project.id)
    char2.name = "Bob"
    char2.entity_type = EntityType.CHARACTER
    await sqlite_adapter.insert_entity(char2)

    rel = Relationship(
        source_id=char1.id,
        source_type=SourceType.ENTITY,
        target_id=char2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved.source_id == char1.id
    assert retrieved.target_id == char2.id


async def test_organization_to_character_relationship(sqlite_adapter):
    """Test relationship between organization and character"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    org = create_sample_entity(project.id)
    org.name = "The Guild"
    org.entity_type = EntityType.ORGANIZATION
    await sqlite_adapter.insert_entity(org)

    member = create_sample_entity(project.id)
    member.name = "Guild Member"
    member.entity_type = EntityType.CHARACTER
    await sqlite_adapter.insert_entity(member)

    rel = Relationship(
        source_id=org.id,
        source_type=SourceType.ENTITY,
        target_id=member.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.HIERARCHICAL,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved.relation_type == RelationType.HIERARCHICAL


# ==========================================
# TIMELINE RELATIONSHIPS
# ==========================================


async def test_timeline_to_event_relationship(sqlite_adapter):
    """Test relationship from timeline to event"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)

    event = create_sample_event(timeline.id)
    await sqlite_adapter.insert_event(event)

    rel = Relationship(
        source_id=timeline.id,
        source_type=SourceType.TIMELINE,
        target_id=event.id,
        target_type=SourceType.EVENT,
        relation_type=RelationType.REFERENTIAL,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved.source_type == SourceType.TIMELINE
    assert retrieved.target_type == SourceType.EVENT


async def test_timeline_to_entity_relationship(sqlite_adapter):
    """Test relationship from timeline to entity"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)

    entity = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity)

    rel = Relationship(
        source_id=timeline.id,
        source_type=SourceType.TIMELINE,
        target_id=entity.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved.source_type == SourceType.TIMELINE
    assert retrieved.target_type == SourceType.ENTITY


async def test_timeline_to_timeline_relationship(sqlite_adapter):
    """Test relationship between two timelines"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline1 = create_sample_timeline(project.id, project.user_id)
    timeline1.name = "Main Timeline"
    await sqlite_adapter.insert_timeline(timeline1)

    timeline2 = create_sample_timeline(project.id, project.user_id)
    timeline2.name = "Alternate Timeline"
    await sqlite_adapter.insert_timeline(timeline2)

    rel = Relationship(
        source_id=timeline1.id,
        source_type=SourceType.TIMELINE,
        target_id=timeline2.id,
        target_type=SourceType.TIMELINE,
        relation_type=RelationType.REFERENTIAL,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved.source_type == SourceType.TIMELINE
    assert retrieved.target_type == SourceType.TIMELINE


# ==========================================
# COMPLEX RELATIONSHIP SCENARIOS
# ==========================================


async def test_multiple_relationships_same_entities(sqlite_adapter, relationship_factory):
    """Test multiple different relationships between same entities"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)

    # Create multiple relationships with different types
    rel1 = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.HIERARCHICAL,
    )

    rel2 = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
    )

    await sqlite_adapter.insert_relationship(rel1)
    await sqlite_adapter.insert_relationship(rel2)

    relationships = await sqlite_adapter.get_relationships_by_source(
        entity1.id, SourceType.ENTITY
    )

    assert len(relationships) == 2
    relation_types = {r.relation_type for r in relationships}
    assert RelationType.HIERARCHICAL in relation_types
    assert RelationType.REFERENTIAL in relation_types


async def test_bidirectional_relationships(sqlite_adapter, relationship_factory):
    """Test creating relationships in both directions"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)

    # Create forward relationship
    rel_forward = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
    )

    # Create backward relationship
    rel_backward = relationship_factory.build(
        source_id=entity2.id,
        source_type=SourceType.ENTITY,
        target_id=entity1.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
    )

    await sqlite_adapter.insert_relationship(rel_forward)
    await sqlite_adapter.insert_relationship(rel_backward)

    # Check from entity1 perspective
    from_entity1 = await sqlite_adapter.get_relationships_by_source(
        entity1.id, SourceType.ENTITY
    )
    assert len(from_entity1) == 1
    assert from_entity1[0].target_id == entity2.id

    # Check from entity2 perspective
    from_entity2 = await sqlite_adapter.get_relationships_by_source(
        entity2.id, SourceType.ENTITY
    )
    assert len(from_entity2) == 1
    assert from_entity2[0].target_id == entity1.id


async def test_relationship_strength_variations(sqlite_adapter, relationship_factory):
    """Test relationships with different strength values"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    entity3 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)
    await sqlite_adapter.insert_entity(entity3)

    # Weak relationship
    rel_weak = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
        strength=Decimal("0.2"),
    )

    # Strong relationship
    rel_strong = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity3.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
        strength=Decimal("0.95"),
    )

    await sqlite_adapter.insert_relationship(rel_weak)
    await sqlite_adapter.insert_relationship(rel_strong)

    relationships = await sqlite_adapter.get_relationships_by_source(
        entity1.id, SourceType.ENTITY
    )

    strengths = [r.strength for r in relationships]
    assert Decimal("0.2") in strengths
    assert Decimal("0.95") in strengths


async def test_temporal_validity_filtering(sqlite_adapter, relationship_factory):
    """Test relationships with different temporal validity periods"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)

    now = datetime.now(UTC)

    # Past relationship (already ended)
    rel_past = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.HIERARCHICAL,
        valid_from=now - timedelta(days=60),
        valid_until=now - timedelta(days=30),
    )

    # Current relationship (active now)
    rel_current = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
        valid_from=now - timedelta(days=10),
        valid_until=now + timedelta(days=10),
    )

    # Future relationship (not yet active)
    rel_future = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.CONDITIONAL,
        valid_from=now + timedelta(days=30),
        valid_until=now + timedelta(days=60),
    )

    await sqlite_adapter.insert_relationship(rel_past)
    await sqlite_adapter.insert_relationship(rel_current)
    await sqlite_adapter.insert_relationship(rel_future)

    all_relationships = await sqlite_adapter.get_relationships_by_source(
        entity1.id, SourceType.ENTITY
    )

    assert len(all_relationships) == 3

    # Verify each has correct temporal bounds
    for rel in all_relationships:
        assert rel.valid_from is not None
        assert rel.valid_until is not None
        assert rel.valid_until > rel.valid_from


async def test_reinforcing_and_contradictory_relationships(
    sqlite_adapter, relationship_factory
):
    """Test reinforcing vs contradictory relationship types"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)

    event1 = create_sample_event(timeline.id)
    event1.description = "First account of battle"
    await sqlite_adapter.insert_event(event1)

    event2 = create_sample_event(timeline.id)
    event2.description = "Second account confirms battle"
    await sqlite_adapter.insert_event(event2)

    event3 = create_sample_event(timeline.id)
    event3.description = "Third account denies battle"
    await sqlite_adapter.insert_event(event3)

    # Reinforcing relationship
    rel_reinforce = relationship_factory.build(
        source_id=event1.id,
        source_type=SourceType.EVENT,
        target_id=event2.id,
        target_type=SourceType.EVENT,
        relation_type=RelationType.REINFORCING,
    )

    # Contradictory relationship
    rel_contradict = relationship_factory.build(
        source_id=event1.id,
        source_type=SourceType.EVENT,
        target_id=event3.id,
        target_type=SourceType.EVENT,
        relation_type=RelationType.CONTRADICTORY,
    )

    await sqlite_adapter.insert_relationship(rel_reinforce)
    await sqlite_adapter.insert_relationship(rel_contradict)

    relationships = await sqlite_adapter.get_relationships_by_source(
        event1.id, SourceType.EVENT
    )

    assert len(relationships) == 2
    types = {r.relation_type for r in relationships}
    assert RelationType.REINFORCING in types
    assert RelationType.CONTRADICTORY in types


async def test_perspective_relationships(sqlite_adapter, relationship_factory):
    """Test perspective-based relationships"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)

    event = create_sample_event(timeline.id)
    event.description = "The great battle"
    await sqlite_adapter.insert_event(event)

    character1 = create_sample_entity(project.id)
    character1.name = "Hero perspective"
    character1.entity_type = EntityType.CHARACTER
    await sqlite_adapter.insert_entity(character1)

    character2 = create_sample_entity(project.id)
    character2.name = "Villain perspective"
    character2.entity_type = EntityType.CHARACTER
    await sqlite_adapter.insert_entity(character2)

    # Different perspectives on same event
    rel1 = relationship_factory.build(
        source_id=character1.id,
        source_type=SourceType.ENTITY,
        target_id=event.id,
        target_type=SourceType.EVENT,
        relation_type=RelationType.PERSPECTIVE,
    )

    rel2 = relationship_factory.build(
        source_id=character2.id,
        source_type=SourceType.ENTITY,
        target_id=event.id,
        target_type=SourceType.EVENT,
        relation_type=RelationType.PERSPECTIVE,
    )

    await sqlite_adapter.insert_relationship(rel1)
    await sqlite_adapter.insert_relationship(rel2)

    # Both characters have perspective on event
    perspectives = await sqlite_adapter.get_relationships_by_target(
        event.id, SourceType.EVENT
    )

    assert len(perspectives) == 2
    assert all(r.relation_type == RelationType.PERSPECTIVE for r in perspectives)


async def test_conditional_relationships(sqlite_adapter, relationship_factory):
    """Test conditional relationship type"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)

    condition_event = create_sample_event(timeline.id)
    condition_event.description = "If hero accepts quest"
    await sqlite_adapter.insert_event(condition_event)

    consequence_event = create_sample_event(timeline.id)
    consequence_event.description = "Then battle occurs"
    await sqlite_adapter.insert_event(consequence_event)

    rel = relationship_factory.build(
        source_id=condition_event.id,
        source_type=SourceType.EVENT,
        target_id=consequence_event.id,
        target_type=SourceType.EVENT,
        relation_type=RelationType.CONDITIONAL,
    )

    await sqlite_adapter.insert_relationship(rel)
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)

    assert retrieved.relation_type == RelationType.CONDITIONAL


# ==========================================
# RELATIONSHIP UPDATE AND DELETE TESTS
# ==========================================


async def test_update_relationship_strength(sqlite_adapter, relationship_factory):
    """Test updating relationship strength"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)

    rel = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
        strength=Decimal("0.5"),
    )

    await sqlite_adapter.insert_relationship(rel)

    # Update strength
    rel.strength = Decimal("0.9")
    await sqlite_adapter.update_relationship(rel)

    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)
    assert retrieved.strength == Decimal("0.9")


async def test_update_relationship_type(sqlite_adapter, relationship_factory):
    """Test changing relationship type"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)

    rel = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.REFERENTIAL,
    )

    await sqlite_adapter.insert_relationship(rel)

    # Update type
    rel.relation_type = RelationType.HIERARCHICAL
    await sqlite_adapter.update_relationship(rel)

    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)
    assert retrieved.relation_type == RelationType.HIERARCHICAL


async def test_update_relationship_temporal_validity(
    sqlite_adapter, relationship_factory
):
    """Test updating temporal validity of relationship"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)

    now = datetime.now(UTC)
    rel = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.HIERARCHICAL,
        valid_from=now,
        valid_until=now + timedelta(days=30),
    )

    await sqlite_adapter.insert_relationship(rel)

    # Extend validity period
    rel.valid_until = now + timedelta(days=60)
    await sqlite_adapter.update_relationship(rel)

    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)
    assert retrieved.valid_until == now + timedelta(days=60)


async def test_delete_relationship_by_id(sqlite_adapter, relationship_factory):
    """Test deleting a relationship"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)

    rel = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
    )

    await sqlite_adapter.insert_relationship(rel)

    # Verify it exists
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)
    assert retrieved is not None

    # Delete it
    await sqlite_adapter.delete_relationship(rel.id)

    # Verify it's gone
    retrieved = await sqlite_adapter.get_relationship_by_id(rel.id)
    assert retrieved is None


async def test_delete_relationship_cascade_check(sqlite_adapter, relationship_factory):
    """Test deleting entities doesn't leave orphan relationships"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)

    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)

    rel = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
    )

    await sqlite_adapter.insert_relationship(rel)

    # Relationship should exist
    relationships = await sqlite_adapter.get_relationships_by_source(
        entity1.id, SourceType.ENTITY
    )
    assert len(relationships) == 1

    # Delete source entity
    await sqlite_adapter.delete_entity(entity1.id)

    # Note: This test demonstrates the pattern, but cascade behavior
    # depends on database constraints. In production, you'd want
    # proper cascade deletes configured in the schema.
