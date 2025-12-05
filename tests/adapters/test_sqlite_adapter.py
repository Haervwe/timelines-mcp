"""
SQLite Adapter Tests - 100% coverage with real database operations

Tests all CRUD operations without mocks using actual SQLite database.
Uses polyfactory for test data generation and pytest fixtures for cleanup.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from timelines_mcp.domain.models import (
    EntityProperties,
    EntityProperty,
    EntityType,
    EventType,
    Metadata,
    PropertyValue,
    RelationType,
    SourceType,
    StateDelta,
    TimelineStatus,
    WorldState,
)
from tests.conftest import (
    create_sample_entity,
    create_sample_event,
    create_sample_project,
    create_sample_timeline,
)


# ==========================================
# PROJECT CRUD TESTS
# ==========================================


async def test_insert_and_get_project(sqlite_adapter, project_factory):
    """Test inserting and retrieving a project"""
    project = project_factory.build()
    
    await sqlite_adapter.insert_project(project)
    retrieved = await sqlite_adapter.get_project_by_id(project.id)
    
    assert retrieved is not None
    assert retrieved.id == project.id
    assert retrieved.user_id == project.user_id
    assert retrieved.name == project.name
    assert retrieved.description == project.description


async def test_get_project_by_id_not_found(sqlite_adapter):
    """Test getting non-existent project returns None"""
    result = await sqlite_adapter.get_project_by_id(uuid4())
    assert result is None


async def test_get_projects_by_user(sqlite_adapter, project_factory):
    """Test getting all projects for a user"""
    user_id = uuid4()
    project1 = project_factory.build(user_id=user_id)
    project2 = project_factory.build(user_id=user_id)
    project3 = project_factory.build(user_id=uuid4())  # Different user
    
    await sqlite_adapter.insert_project(project1)
    await sqlite_adapter.insert_project(project2)
    await sqlite_adapter.insert_project(project3)
    
    projects = await sqlite_adapter.get_projects_by_user(user_id)
    
    assert len(projects) == 2
    assert all(p.user_id == user_id for p in projects)


async def test_update_project(sqlite_adapter):
    """Test updating a project"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    # Update project
    project.name = "Updated Name"
    project.description = "Updated Description"
    await sqlite_adapter.update_project(project)
    
    retrieved = await sqlite_adapter.get_project_by_id(project.id)
    assert retrieved.name == "Updated Name"
    assert retrieved.description == "Updated Description"


async def test_delete_project(sqlite_adapter):
    """Test deleting a project"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    await sqlite_adapter.delete_project(project.id)
    
    retrieved = await sqlite_adapter.get_project_by_id(project.id)
    assert retrieved is None


# ==========================================
# TIMELINE CRUD TESTS
# ==========================================


async def test_insert_and_get_timeline(sqlite_adapter, timeline_factory):
    """Test inserting and retrieving a timeline"""
    # Create project first
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = timeline_factory.build(
        project_id=project.id,
        user_id=project.user_id,
        parent_timeline_id=None,
    )
    
    await sqlite_adapter.insert_timeline(timeline)
    retrieved = await sqlite_adapter.get_timeline_by_id(timeline.id)
    
    assert retrieved is not None
    assert retrieved.id == timeline.id
    assert retrieved.project_id == timeline.project_id
    assert retrieved.name == timeline.name
    assert retrieved.status == timeline.status


async def test_get_timeline_by_id_not_found(sqlite_adapter):
    """Test getting non-existent timeline returns None"""
    result = await sqlite_adapter.get_timeline_by_id(uuid4())
    assert result is None


async def test_get_timelines_by_project(sqlite_adapter):
    """Test getting all timelines in a project"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline1 = create_sample_timeline(project.id, project.user_id)
    timeline2 = create_sample_timeline(project.id, project.user_id)
    
    await sqlite_adapter.insert_timeline(timeline1)
    await sqlite_adapter.insert_timeline(timeline2)
    
    timelines = await sqlite_adapter.get_timelines_by_project(project.id)
    
    assert len(timelines) == 2
    assert all(t.project_id == project.id for t in timelines)


async def test_get_timelines_by_parent(sqlite_adapter):
    """Test getting child timelines"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    parent = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(parent)
    
    child1 = create_sample_timeline(project.id, project.user_id)
    child1.parent_timeline_id = parent.id
    child2 = create_sample_timeline(project.id, project.user_id)
    child2.parent_timeline_id = parent.id
    
    await sqlite_adapter.insert_timeline(child1)
    await sqlite_adapter.insert_timeline(child2)
    
    children = await sqlite_adapter.get_timelines_by_parent(parent.id)
    
    assert len(children) == 2
    assert all(t.parent_timeline_id == parent.id for t in children)


async def test_update_timeline(sqlite_adapter):
    """Test updating a timeline"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    timeline.name = "Updated Timeline"
    timeline.status = TimelineStatus.DRAFT
    await sqlite_adapter.update_timeline(timeline)
    
    retrieved = await sqlite_adapter.get_timeline_by_id(timeline.id)
    assert retrieved.name == "Updated Timeline"
    assert retrieved.status == TimelineStatus.DRAFT


async def test_delete_timeline(sqlite_adapter):
    """Test deleting a timeline"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    await sqlite_adapter.delete_timeline(timeline.id)
    
    retrieved = await sqlite_adapter.get_timeline_by_id(timeline.id)
    assert retrieved is None


async def test_timeline_cascade_delete(sqlite_adapter):
    """Test that deleting project cascades to timelines"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    await sqlite_adapter.delete_project(project.id)
    
    retrieved_timeline = await sqlite_adapter.get_timeline_by_id(timeline.id)
    assert retrieved_timeline is None


# ==========================================
# EVENT CRUD TESTS
# ==========================================


async def test_insert_and_get_event(sqlite_adapter, event_factory):
    """Test inserting and retrieving an event"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    event = event_factory.build(timeline_id=timeline.id)
    
    await sqlite_adapter.insert_event(event)
    retrieved = await sqlite_adapter.get_event_by_id(event.id)
    
    assert retrieved is not None
    assert retrieved.id == event.id
    assert retrieved.timeline_id == event.timeline_id
    assert retrieved.description == event.description
    assert retrieved.event_type == event.event_type


async def test_event_with_end_timestamp(sqlite_adapter):
    """Test event with time range"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    event = create_sample_event(timeline.id)
    event.end_timestamp = event.timestamp + timedelta(hours=2)
    
    await sqlite_adapter.insert_event(event)
    retrieved = await sqlite_adapter.get_event_by_id(event.id)
    
    assert retrieved.end_timestamp is not None
    assert retrieved.end_timestamp == event.end_timestamp


async def test_get_event_by_id_not_found(sqlite_adapter):
    """Test getting non-existent event returns None"""
    result = await sqlite_adapter.get_event_by_id(uuid4())
    assert result is None


async def test_get_events_by_timeline(sqlite_adapter):
    """Test getting all events for a timeline"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    event1 = create_sample_event(timeline.id)
    event2 = create_sample_event(timeline.id)
    
    await sqlite_adapter.insert_event(event1)
    await sqlite_adapter.insert_event(event2)
    
    events = await sqlite_adapter.get_events_by_timeline(timeline.id)
    
    assert len(events) == 2
    assert all(e.timeline_id == timeline.id for e in events)


async def test_update_event(sqlite_adapter):
    """Test updating an event"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    event = create_sample_event(timeline.id)
    await sqlite_adapter.insert_event(event)
    
    event.description = "Updated description"
    event.importance_score = Decimal("0.9")
    await sqlite_adapter.update_event(event)
    
    retrieved = await sqlite_adapter.get_event_by_id(event.id)
    assert retrieved.description == "Updated description"
    assert retrieved.importance_score == Decimal("0.9")


async def test_delete_event(sqlite_adapter):
    """Test deleting an event"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    event = create_sample_event(timeline.id)
    await sqlite_adapter.insert_event(event)
    
    await sqlite_adapter.delete_event(event.id)
    
    retrieved = await sqlite_adapter.get_event_by_id(event.id)
    assert retrieved is None


# ==========================================
# ENTITY CRUD TESTS
# ==========================================


async def test_insert_and_get_entity(sqlite_adapter, entity_factory):
    """Test inserting and retrieving an entity"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity = entity_factory.build(project_id=project.id)
    
    await sqlite_adapter.insert_entity(entity)
    retrieved = await sqlite_adapter.get_entity_by_id(entity.id)
    
    assert retrieved is not None
    assert retrieved.id == entity.id
    assert retrieved.project_id == entity.project_id
    assert retrieved.name == entity.name
    assert retrieved.entity_type == entity.entity_type


async def test_get_entity_by_id_not_found(sqlite_adapter):
    """Test getting non-existent entity returns None"""
    result = await sqlite_adapter.get_entity_by_id(uuid4())
    assert result is None


async def test_get_entities_by_project(sqlite_adapter):
    """Test getting all entities in a project"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)
    
    entities = await sqlite_adapter.get_entities_by_project(project.id)
    
    assert len(entities) == 2
    assert all(e.project_id == project.id for e in entities)


async def test_update_entity(sqlite_adapter):
    """Test updating an entity"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity)
    
    entity.name = "Updated Entity"
    entity.entity_type = EntityType.PLACE
    await sqlite_adapter.update_entity(entity)
    
    retrieved = await sqlite_adapter.get_entity_by_id(entity.id)
    assert retrieved.name == "Updated Entity"
    assert retrieved.entity_type == EntityType.PLACE


async def test_delete_entity(sqlite_adapter):
    """Test deleting an entity"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity)
    
    await sqlite_adapter.delete_entity(entity.id)
    
    retrieved = await sqlite_adapter.get_entity_by_id(entity.id)
    assert retrieved is None


# ==========================================
# RELATIONSHIP CRUD TESTS
# ==========================================


async def test_insert_and_get_relationship(sqlite_adapter, relationship_factory):
    """Test inserting and retrieving a relationship"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)
    
    relationship = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
    )
    
    await sqlite_adapter.insert_relationship(relationship)
    retrieved = await sqlite_adapter.get_relationship_by_id(relationship.id)
    
    assert retrieved is not None
    assert retrieved.id == relationship.id
    assert retrieved.source_id == relationship.source_id
    assert retrieved.target_id == relationship.target_id


async def test_get_relationship_by_id_not_found(sqlite_adapter):
    """Test getting non-existent relationship returns None"""
    result = await sqlite_adapter.get_relationship_by_id(uuid4())
    assert result is None


async def test_get_relationships_by_source(sqlite_adapter, relationship_factory):
    """Test getting relationships by source"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    entity3 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)
    await sqlite_adapter.insert_entity(entity3)
    
    rel1 = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
    )
    rel2 = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity3.id,
        target_type=SourceType.ENTITY,
    )
    
    await sqlite_adapter.insert_relationship(rel1)
    await sqlite_adapter.insert_relationship(rel2)
    
    relationships = await sqlite_adapter.get_relationships_by_source(
        entity1.id, SourceType.ENTITY
    )
    
    assert len(relationships) == 2
    assert all(r.source_id == entity1.id for r in relationships)


async def test_get_relationships_by_target(sqlite_adapter, relationship_factory):
    """Test getting relationships by target"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    entity3 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)
    await sqlite_adapter.insert_entity(entity3)
    
    rel1 = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity3.id,
        target_type=SourceType.ENTITY,
    )
    rel2 = relationship_factory.build(
        source_id=entity2.id,
        source_type=SourceType.ENTITY,
        target_id=entity3.id,
        target_type=SourceType.ENTITY,
    )
    
    await sqlite_adapter.insert_relationship(rel1)
    await sqlite_adapter.insert_relationship(rel2)
    
    relationships = await sqlite_adapter.get_relationships_by_target(
        entity3.id, SourceType.ENTITY
    )
    
    assert len(relationships) == 2
    assert all(r.target_id == entity3.id for r in relationships)


async def test_update_relationship(sqlite_adapter, relationship_factory):
    """Test updating a relationship"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)
    
    relationship = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
    )
    await sqlite_adapter.insert_relationship(relationship)
    
    relationship.relation_type = RelationType.CAUSAL
    relationship.strength = Decimal("0.9")
    await sqlite_adapter.update_relationship(relationship)
    
    retrieved = await sqlite_adapter.get_relationship_by_id(relationship.id)
    assert retrieved.relation_type == RelationType.CAUSAL
    assert retrieved.strength == Decimal("0.9")


async def test_delete_relationship(sqlite_adapter):
    """Test deleting a relationship"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)
    
    from timelines_mcp.domain.models import Relationship
    relationship = Relationship(
        id=uuid4(),
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        relation_type=RelationType.TEMPORAL,
        strength=Decimal("1.0"),
    )
    await sqlite_adapter.insert_relationship(relationship)
    
    await sqlite_adapter.delete_relationship(relationship.id)
    
    retrieved = await sqlite_adapter.get_relationship_by_id(relationship.id)
    assert retrieved is None


# ==========================================
# STATE SNAPSHOT CRUD TESTS
# ==========================================


async def test_insert_and_get_snapshot(sqlite_adapter, snapshot_factory):
    """Test inserting and retrieving a state snapshot"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    snapshot = snapshot_factory.build(timeline_id=timeline.id)
    
    await sqlite_adapter.insert_snapshot(snapshot)
    retrieved = await sqlite_adapter.get_snapshot_by_id(snapshot.id)
    
    assert retrieved is not None
    assert retrieved.id == snapshot.id
    assert retrieved.timeline_id == snapshot.timeline_id
    assert retrieved.timestamp == snapshot.timestamp


async def test_get_snapshot_by_id_not_found(sqlite_adapter):
    """Test getting non-existent snapshot returns None"""
    result = await sqlite_adapter.get_snapshot_by_id(uuid4())
    assert result is None


async def test_get_snapshots_by_timeline(sqlite_adapter, snapshot_factory):
    """Test getting all snapshots for a timeline"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    snapshot1 = snapshot_factory.build(timeline_id=timeline.id)
    snapshot2 = snapshot_factory.build(timeline_id=timeline.id)
    
    await sqlite_adapter.insert_snapshot(snapshot1)
    await sqlite_adapter.insert_snapshot(snapshot2)
    
    snapshots = await sqlite_adapter.get_snapshots_by_timeline(timeline.id)
    
    assert len(snapshots) == 2
    assert all(s.timeline_id == timeline.id for s in snapshots)


async def test_delete_snapshot(sqlite_adapter):
    """Test deleting a state snapshot"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    from timelines_mcp.domain.models import StateSnapshot
    snapshot = StateSnapshot(
        id=uuid4(),
        timeline_id=timeline.id,
        timestamp=datetime.now(UTC),
        state=WorldState(),
    )
    await sqlite_adapter.insert_snapshot(snapshot)
    
    await sqlite_adapter.delete_snapshot(snapshot.id)
    
    retrieved = await sqlite_adapter.get_snapshot_by_id(snapshot.id)
    assert retrieved is None


# ==========================================
# EVENT-ENTITY LINK TESTS
# ==========================================


async def test_insert_and_get_event_entity_link(sqlite_adapter):
    """Test inserting and retrieving event-entity links"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    event = create_sample_event(timeline.id)
    await sqlite_adapter.insert_event(event)
    
    entity = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity)
    
    await sqlite_adapter.insert_event_entity_link(event.id, entity.id, "actor")
    
    links = await sqlite_adapter.get_event_entity_links_by_event(event.id)
    
    assert len(links) == 1
    assert links[0][0] == entity.id
    assert links[0][1] == "actor"


async def test_get_event_entity_links_by_entity(sqlite_adapter):
    """Test getting event links by entity"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    event1 = create_sample_event(timeline.id)
    event2 = create_sample_event(timeline.id)
    await sqlite_adapter.insert_event(event1)
    await sqlite_adapter.insert_event(event2)
    
    entity = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity)
    
    await sqlite_adapter.insert_event_entity_link(event1.id, entity.id, "actor")
    await sqlite_adapter.insert_event_entity_link(event2.id, entity.id, "observer")
    
    links = await sqlite_adapter.get_event_entity_links_by_entity(entity.id)
    
    assert len(links) == 2
    event_ids = [link[0] for link in links]
    assert event1.id in event_ids
    assert event2.id in event_ids


async def test_delete_event_entity_link_with_role(sqlite_adapter):
    """Test deleting a specific event-entity link with role"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    event = create_sample_event(timeline.id)
    await sqlite_adapter.insert_event(event)
    
    entity = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity)
    
    await sqlite_adapter.insert_event_entity_link(event.id, entity.id, "actor")
    await sqlite_adapter.insert_event_entity_link(event.id, entity.id, "observer")
    
    await sqlite_adapter.delete_event_entity_link(event.id, entity.id, "actor")
    
    links = await sqlite_adapter.get_event_entity_links_by_event(event.id)
    assert len(links) == 1
    assert links[0][1] == "observer"


async def test_delete_event_entity_link_all_roles(sqlite_adapter):
    """Test deleting all event-entity links (no role specified)"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    event = create_sample_event(timeline.id)
    await sqlite_adapter.insert_event(event)
    
    entity = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity)
    
    await sqlite_adapter.insert_event_entity_link(event.id, entity.id, "actor")
    await sqlite_adapter.insert_event_entity_link(event.id, entity.id, "observer")
    
    await sqlite_adapter.delete_event_entity_link(event.id, entity.id, role=None)
    
    links = await sqlite_adapter.get_event_entity_links_by_event(event.id)
    assert len(links) == 0


# ==========================================
# INTEGRATION & EDGE CASE TESTS
# ==========================================


async def test_file_based_sqlite_persistence(sqlite_file_adapter):
    """Test that file-based adapter persists data"""
    project = create_sample_project()
    await sqlite_file_adapter.insert_project(project)
    
    retrieved = await sqlite_file_adapter.get_project_by_id(project.id)
    assert retrieved is not None
    assert retrieved.id == project.id


async def test_complex_entity_properties(sqlite_adapter):
    """Test entity with complex properties"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity = create_sample_entity(project.id)
    entity.properties.set("strength", PropertyValue(number_val=Decimal("10.5")))
    entity.properties.set("is_alive", PropertyValue(boolean_val=True))
    entity.properties.set("last_seen", PropertyValue(datetime_val=datetime.now(UTC)))
    
    await sqlite_adapter.insert_entity(entity)
    retrieved = await sqlite_adapter.get_entity_by_id(entity.id)
    
    assert retrieved.properties.get("strength").number_val == Decimal("10.5")
    assert retrieved.properties.get("is_alive").boolean_val is True
    assert retrieved.properties.get("last_seen").datetime_val is not None


async def test_event_with_state_delta(sqlite_adapter):
    """Test event with complex state delta"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    event = create_sample_event(timeline.id)
    event.state_delta.global_changes["weather"] = EntityProperty(
        key="weather",
        value=PropertyValue(string_val="rainy"),
    )
    
    entity_id = uuid4()
    event.state_delta.entity_changes[entity_id] = {
        "health": EntityProperty(
            key="health",
            value=PropertyValue(number_val=Decimal("75.0")),
        )
    }
    
    await sqlite_adapter.insert_event(event)
    retrieved = await sqlite_adapter.get_event_by_id(event.id)
    
    assert "weather" in retrieved.state_delta.global_changes
    assert entity_id in retrieved.state_delta.entity_changes


async def test_empty_collections(sqlite_adapter):
    """Test queries on empty collections"""
    projects = await sqlite_adapter.get_projects_by_user(uuid4())
    assert projects == []
    
    timelines = await sqlite_adapter.get_timelines_by_project(uuid4())
    assert timelines == []
    
    events = await sqlite_adapter.get_events_by_timeline(uuid4())
    assert events == []


async def test_relationship_with_time_validity(sqlite_adapter, relationship_factory):
    """Test relationship with temporal validity"""
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    entity1 = create_sample_entity(project.id)
    entity2 = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity1)
    await sqlite_adapter.insert_entity(entity2)
    
    now = datetime.now(UTC)
    relationship = relationship_factory.build(
        source_id=entity1.id,
        source_type=SourceType.ENTITY,
        target_id=entity2.id,
        target_type=SourceType.ENTITY,
        valid_from=now,
        valid_until=now + timedelta(days=30),
    )
    
    await sqlite_adapter.insert_relationship(relationship)
    retrieved = await sqlite_adapter.get_relationship_by_id(relationship.id)
    
    assert retrieved.valid_from == now
    assert retrieved.valid_until == now + timedelta(days=30)


async def test_event_with_complex_state_delta(sqlite_adapter):
    """Test event with state delta containing datetime and number values"""
    from timelines_mcp.domain.models import EntityProperty
    
    project = create_sample_project()
    await sqlite_adapter.insert_project(project)
    
    timeline = create_sample_timeline(project.id, project.user_id)
    await sqlite_adapter.insert_timeline(timeline)
    
    entity = create_sample_entity(project.id)
    await sqlite_adapter.insert_entity(entity)
    
    # Create event with state delta containing datetime and number values
    event = create_sample_event(timeline.id)
    event.state_delta.global_changes["time"] = EntityProperty(
        key="time",
        value=PropertyValue(datetime_val=datetime.now(UTC))
    )
    event.state_delta.global_changes["score"] = EntityProperty(
        key="score",
        value=PropertyValue(number_val=Decimal("99.5"))
    )
    event.state_delta.entity_changes[entity.id] = {
        "health": EntityProperty(
            key="health",
            value=PropertyValue(number_val=Decimal("75.0"))
        ),
        "last_seen": EntityProperty(
            key="last_seen",
            value=PropertyValue(datetime_val=datetime.now(UTC))
        )
    }
    
    await sqlite_adapter.insert_event(event)
    retrieved = await sqlite_adapter.get_event_by_id(event.id)
    
    # Verify datetime and number values are properly serialized/deserialized
    assert retrieved.state_delta.global_changes["time"].value.datetime_val is not None
    assert retrieved.state_delta.global_changes["score"].value.number_val == Decimal("99.5")
    assert entity.id in retrieved.state_delta.entity_changes
    assert retrieved.state_delta.entity_changes[entity.id]["health"].value.number_val == Decimal("75.0")
    assert retrieved.state_delta.entity_changes[entity.id]["last_seen"].value.datetime_val is not None

