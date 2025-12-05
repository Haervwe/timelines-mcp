"""
SQLite Storage Adapter - Pure CRUD implementation

Thin wrapper around aiosqlite with no business logic.
Uses in-memory or file-based SQLite for local/test deployments.
"""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import aiosqlite

from ...domain.models import (
    Entity,
    EntityProperties,
    EntityProperty,
    EntityType,
    Event,
    EventType,
    Metadata,
    Project,
    PropertyValue,
    Relationship,
    RelationType,
    SourceType,
    StateDelta,
    StateSnapshot,
    Timeline,
    TimelineStatus,
    WorldState,
)


class SQLiteAdapter:
    """SQLite adapter implementing StorageAdapter protocol"""

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize SQLite adapter
        
        Args:
            db_path: Path to SQLite database file or ":memory:" for in-memory
        """
        self.db_path = db_path
        self.db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Initialize database schema and connection"""
        # Create parent directory if using file-based storage
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db = await aiosqlite.connect(self.db_path)
        # Enable foreign keys
        await self.db.execute("PRAGMA foreign_keys = ON")
        # Enable WAL mode for better concurrency
        await self.db.execute("PRAGMA journal_mode = WAL")

        # Create schema
        await self._create_schema()

    async def close(self) -> None:
        """Close database connection"""
        if self.db:
            await self.db.close()
            self.db = None

    async def _create_schema(self) -> None:
        """Create database tables"""
        await self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS timelines (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                parent_timeline_id TEXT,
                status TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_timeline_id) REFERENCES timelines(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                timeline_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                end_timestamp TEXT,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                importance_score TEXT NOT NULL,
                detail_level INTEGER NOT NULL,
                state_delta TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (timeline_id) REFERENCES timelines(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                properties TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                strength TEXT NOT NULL,
                valid_from TEXT,
                valid_until TEXT,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS state_snapshots (
                id TEXT PRIMARY KEY,
                timeline_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (timeline_id) REFERENCES timelines(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS event_entity_links (
                event_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                role TEXT NOT NULL,
                PRIMARY KEY (event_id, entity_id, role),
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_timelines_project ON timelines(project_id);
            CREATE INDEX IF NOT EXISTS idx_timelines_parent ON timelines(parent_timeline_id);
            CREATE INDEX IF NOT EXISTS idx_events_timeline ON events(timeline_id);
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_entities_project ON entities(project_id);
            CREATE INDEX IF NOT EXISTS idx_snapshots_timeline ON state_snapshots(timeline_id);
            CREATE INDEX IF NOT EXISTS idx_event_entity_event ON event_entity_links(event_id);
            CREATE INDEX IF NOT EXISTS idx_event_entity_entity ON event_entity_links(entity_id);
            """
        )
        await self.db.commit()

    # === Helper methods for serialization ===

    @staticmethod
    def _serialize_metadata(metadata: Metadata) -> str:
        """Serialize Metadata to JSON"""
        def convert_value(v: PropertyValue) -> dict:
            data = v.model_dump()
            # Convert datetime to ISO format string
            if data.get('datetime_val'):
                data['datetime_val'] = data['datetime_val'].isoformat()
            # Convert Decimal to string
            if data.get('number_val') is not None:
                data['number_val'] = str(data['number_val'])
            return data

        return json.dumps({k: convert_value(v.value) for k, v in metadata.properties.items()})

    @staticmethod
    def _deserialize_metadata(data: str) -> Metadata:
        """Deserialize Metadata from JSON"""
        parsed = json.loads(data)
        properties = {}
        for k, v in parsed.items():
            # Convert strings back to proper types
            if v.get('datetime_val'):
                v['datetime_val'] = datetime.fromisoformat(v['datetime_val'])
            if v.get('number_val') is not None:
                v['number_val'] = Decimal(v['number_val'])
            properties[k] = EntityProperty(key=k, value=PropertyValue(**v))
        return Metadata(properties=properties)

    @staticmethod
    def _serialize_properties(properties: EntityProperties) -> str:
        """Serialize EntityProperties to JSON"""
        def convert_value(v: PropertyValue) -> dict:
            data = v.model_dump()
            if data.get('datetime_val'):
                data['datetime_val'] = data['datetime_val'].isoformat()
            if data.get('number_val') is not None:
                data['number_val'] = str(data['number_val'])
            return data

        return json.dumps({k: convert_value(v.value) for k, v in properties.properties.items()})

    @staticmethod
    def _deserialize_properties(data: str) -> EntityProperties:
        """Deserialize EntityProperties from JSON"""
        parsed = json.loads(data)
        properties = {}
        for k, v in parsed.items():
            if v.get('datetime_val'):
                v['datetime_val'] = datetime.fromisoformat(v['datetime_val'])
            if v.get('number_val') is not None:
                v['number_val'] = Decimal(v['number_val'])
            properties[k] = EntityProperty(key=k, value=PropertyValue(**v))
        return EntityProperties(properties=properties)

    @staticmethod
    def _serialize_state_delta(delta: StateDelta) -> str:
        """Serialize StateDelta to JSON"""
        def convert_property(prop: EntityProperty) -> dict:
            data = prop.model_dump()
            if data['value'].get('datetime_val'):
                data['value']['datetime_val'] = data['value']['datetime_val'].isoformat()
            if data['value'].get('number_val') is not None:
                data['value']['number_val'] = str(data['value']['number_val'])
            return data

        return json.dumps(
            {
                "global_changes": {k: convert_property(v) for k, v in delta.global_changes.items()},
                "entity_changes": {
                    str(entity_id): {k: convert_property(v) for k, v in changes.items()}
                    for entity_id, changes in delta.entity_changes.items()
                },
            }
        )

    @staticmethod
    def _deserialize_state_delta(data: str) -> StateDelta:
        """Deserialize StateDelta from JSON"""
        parsed = json.loads(data)

        def convert_property(prop_data: dict) -> EntityProperty:
            if prop_data['value'].get('datetime_val'):
                prop_data['value']['datetime_val'] = datetime.fromisoformat(prop_data['value']['datetime_val'])
            if prop_data['value'].get('number_val') is not None:
                prop_data['value']['number_val'] = Decimal(prop_data['value']['number_val'])
            return EntityProperty(**prop_data)

        return StateDelta(
            global_changes={k: convert_property(v) for k, v in parsed["global_changes"].items()},
            entity_changes={
                UUID(entity_id): {k: convert_property(v) for k, v in changes.items()}
                for entity_id, changes in parsed["entity_changes"].items()
            },
        )

    @staticmethod
    def _serialize_world_state(state: WorldState) -> str:
        """Serialize WorldState to JSON"""
        def convert_property(prop: EntityProperty) -> dict:
            data = prop.model_dump()
            if data['value'].get('datetime_val'):
                data['value']['datetime_val'] = data['value']['datetime_val'].isoformat()
            if data['value'].get('number_val') is not None:
                data['value']['number_val'] = str(data['value']['number_val'])
            return data

        return json.dumps(
            {
                "global_properties": {
                    k: convert_property(v) for k, v in state.global_properties.items()
                },
                "entity_states": {
                    str(entity_id): {k: convert_property(v) for k, v in props.items()}
                    for entity_id, props in state.entity_states.items()
                },
            }
        )

    @staticmethod
    def _deserialize_world_state(data: str) -> WorldState:
        """Deserialize WorldState from JSON"""
        parsed = json.loads(data)

        def convert_property(prop_data: dict) -> EntityProperty:
            if prop_data['value'].get('datetime_val'):
                prop_data['value']['datetime_val'] = datetime.fromisoformat(prop_data['value']['datetime_val'])
            if prop_data['value'].get('number_val') is not None:
                prop_data['value']['number_val'] = Decimal(prop_data['value']['number_val'])
            return EntityProperty(**prop_data)

        return WorldState(
            global_properties={
                k: convert_property(v) for k, v in parsed["global_properties"].items()
            },
            entity_states={
                UUID(entity_id): {k: convert_property(v) for k, v in props.items()}
                for entity_id, props in parsed["entity_states"].items()
            },
        )

    # === PROJECT CRUD ===

    async def insert_project(self, project: Project) -> None:
        """Insert project record"""
        await self.db.execute(
            """
            INSERT INTO projects (id, user_id, name, description, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(project.id),
                str(project.user_id),
                project.name,
                project.description,
                self._serialize_metadata(project.metadata),
                project.created_at.isoformat(),
            ),
        )
        await self.db.commit()

    async def get_project_by_id(self, project_id: UUID) -> Project | None:
        """Get single project by ID"""
        async with self.db.execute(
            "SELECT * FROM projects WHERE id = ?", (str(project_id),)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            return Project(
                id=UUID(row[0]),
                user_id=UUID(row[1]),
                name=row[2],
                description=row[3],
                metadata=self._deserialize_metadata(row[4]),
                created_at=datetime.fromisoformat(row[5]),
            )

    async def get_projects_by_user(self, user_id: UUID) -> list[Project]:
        """Get all projects for user"""
        async with self.db.execute(
            "SELECT * FROM projects WHERE user_id = ?", (str(user_id),)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                Project(
                    id=UUID(row[0]),
                    user_id=UUID(row[1]),
                    name=row[2],
                    description=row[3],
                    metadata=self._deserialize_metadata(row[4]),
                    created_at=datetime.fromisoformat(row[5]),
                )
                for row in rows
            ]

    async def update_project(self, project: Project) -> None:
        """Update project record"""
        await self.db.execute(
            """
            UPDATE projects
            SET user_id = ?, name = ?, description = ?, metadata = ?
            WHERE id = ?
            """,
            (
                str(project.user_id),
                project.name,
                project.description,
                self._serialize_metadata(project.metadata),
                str(project.id),
            ),
        )
        await self.db.commit()

    async def delete_project(self, project_id: UUID) -> None:
        """Delete project record"""
        await self.db.execute("DELETE FROM projects WHERE id = ?", (str(project_id),))
        await self.db.commit()

    # === TIMELINE CRUD ===

    async def insert_timeline(self, timeline: Timeline) -> None:
        """Insert timeline record"""
        await self.db.execute(
            """
            INSERT INTO timelines 
            (id, project_id, user_id, name, description, parent_timeline_id, status, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(timeline.id),
                str(timeline.project_id),
                str(timeline.user_id),
                timeline.name,
                timeline.description,
                str(timeline.parent_timeline_id) if timeline.parent_timeline_id else None,
                timeline.status.value,
                self._serialize_metadata(timeline.metadata),
                timeline.created_at.isoformat(),
            ),
        )
        await self.db.commit()

    async def get_timeline_by_id(self, timeline_id: UUID) -> Timeline | None:
        """Get single timeline by ID"""
        async with self.db.execute(
            "SELECT * FROM timelines WHERE id = ?", (str(timeline_id),)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            return Timeline(
                id=UUID(row[0]),
                project_id=UUID(row[1]),
                user_id=UUID(row[2]),
                name=row[3],
                description=row[4],
                parent_timeline_id=UUID(row[5]) if row[5] else None,
                status=TimelineStatus(row[6]),
                metadata=self._deserialize_metadata(row[7]),
                created_at=datetime.fromisoformat(row[8]),
            )

    async def get_timelines_by_project(self, project_id: UUID) -> list[Timeline]:
        """Get all timelines in project"""
        async with self.db.execute(
            "SELECT * FROM timelines WHERE project_id = ?", (str(project_id),)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                Timeline(
                    id=UUID(row[0]),
                    project_id=UUID(row[1]),
                    user_id=UUID(row[2]),
                    name=row[3],
                    description=row[4],
                    parent_timeline_id=UUID(row[5]) if row[5] else None,
                    status=TimelineStatus(row[6]),
                    metadata=self._deserialize_metadata(row[7]),
                    created_at=datetime.fromisoformat(row[8]),
                )
                for row in rows
            ]

    async def get_timelines_by_parent(self, parent_timeline_id: UUID) -> list[Timeline]:
        """Get child timelines"""
        async with self.db.execute(
            "SELECT * FROM timelines WHERE parent_timeline_id = ?", (str(parent_timeline_id),)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                Timeline(
                    id=UUID(row[0]),
                    project_id=UUID(row[1]),
                    user_id=UUID(row[2]),
                    name=row[3],
                    description=row[4],
                    parent_timeline_id=UUID(row[5]) if row[5] else None,
                    status=TimelineStatus(row[6]),
                    metadata=self._deserialize_metadata(row[7]),
                    created_at=datetime.fromisoformat(row[8]),
                )
                for row in rows
            ]

    async def update_timeline(self, timeline: Timeline) -> None:
        """Update timeline record"""
        await self.db.execute(
            """
            UPDATE timelines
            SET project_id = ?, user_id = ?, name = ?, description = ?,
                parent_timeline_id = ?, status = ?, metadata = ?
            WHERE id = ?
            """,
            (
                str(timeline.project_id),
                str(timeline.user_id),
                timeline.name,
                timeline.description,
                str(timeline.parent_timeline_id) if timeline.parent_timeline_id else None,
                timeline.status.value,
                self._serialize_metadata(timeline.metadata),
                str(timeline.id),
            ),
        )
        await self.db.commit()

    async def delete_timeline(self, timeline_id: UUID) -> None:
        """Delete timeline record"""
        await self.db.execute("DELETE FROM timelines WHERE id = ?", (str(timeline_id),))
        await self.db.commit()

    # === EVENT CRUD ===

    async def insert_event(self, event: Event) -> None:
        """Insert event record"""
        await self.db.execute(
            """
            INSERT INTO events 
            (id, timeline_id, timestamp, end_timestamp, event_type, description, 
             importance_score, detail_level, state_delta, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(event.id),
                str(event.timeline_id),
                event.timestamp.isoformat(),
                event.end_timestamp.isoformat() if event.end_timestamp else None,
                event.event_type.value,
                event.description,
                str(event.importance_score),
                event.detail_level,
                self._serialize_state_delta(event.state_delta),
                self._serialize_metadata(event.metadata),
                event.created_at.isoformat(),
            ),
        )
        await self.db.commit()

    async def get_event_by_id(self, event_id: UUID) -> Event | None:
        """Get single event by ID"""
        async with self.db.execute(
            "SELECT * FROM events WHERE id = ?", (str(event_id),)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            return Event(
                id=UUID(row[0]),
                timeline_id=UUID(row[1]),
                timestamp=datetime.fromisoformat(row[2]),
                end_timestamp=datetime.fromisoformat(row[3]) if row[3] else None,
                event_type=EventType(row[4]),
                description=row[5],
                importance_score=Decimal(row[6]),
                detail_level=row[7],
                state_delta=self._deserialize_state_delta(row[8]),
                metadata=self._deserialize_metadata(row[9]),
                created_at=datetime.fromisoformat(row[10]),
            )

    async def get_events_by_timeline(self, timeline_id: UUID) -> list[Event]:
        """Get ALL events for timeline"""
        async with self.db.execute(
            "SELECT * FROM events WHERE timeline_id = ?", (str(timeline_id),)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                Event(
                    id=UUID(row[0]),
                    timeline_id=UUID(row[1]),
                    timestamp=datetime.fromisoformat(row[2]),
                    end_timestamp=datetime.fromisoformat(row[3]) if row[3] else None,
                    event_type=EventType(row[4]),
                    description=row[5],
                    importance_score=Decimal(row[6]),
                    detail_level=row[7],
                    state_delta=self._deserialize_state_delta(row[8]),
                    metadata=self._deserialize_metadata(row[9]),
                    created_at=datetime.fromisoformat(row[10]),
                )
                for row in rows
            ]

    async def update_event(self, event: Event) -> None:
        """Update event record"""
        await self.db.execute(
            """
            UPDATE events
            SET timeline_id = ?, timestamp = ?, end_timestamp = ?, event_type = ?,
                description = ?, importance_score = ?, detail_level = ?,
                state_delta = ?, metadata = ?
            WHERE id = ?
            """,
            (
                str(event.timeline_id),
                event.timestamp.isoformat(),
                event.end_timestamp.isoformat() if event.end_timestamp else None,
                event.event_type.value,
                event.description,
                str(event.importance_score),
                event.detail_level,
                self._serialize_state_delta(event.state_delta),
                self._serialize_metadata(event.metadata),
                str(event.id),
            ),
        )
        await self.db.commit()

    async def delete_event(self, event_id: UUID) -> None:
        """Delete event record"""
        await self.db.execute("DELETE FROM events WHERE id = ?", (str(event_id),))
        await self.db.commit()

    # === ENTITY CRUD ===

    async def insert_entity(self, entity: Entity) -> None:
        """Insert entity record"""
        await self.db.execute(
            """
            INSERT INTO entities 
            (id, project_id, entity_type, name, description, properties, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(entity.id),
                str(entity.project_id),
                entity.entity_type.value,
                entity.name,
                entity.description,
                self._serialize_properties(entity.properties),
                entity.created_at.isoformat(),
            ),
        )
        await self.db.commit()

    async def get_entity_by_id(self, entity_id: UUID) -> Entity | None:
        """Get single entity by ID"""
        async with self.db.execute(
            "SELECT * FROM entities WHERE id = ?", (str(entity_id),)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            return Entity(
                id=UUID(row[0]),
                project_id=UUID(row[1]),
                entity_type=EntityType(row[2]),
                name=row[3],
                description=row[4],
                properties=self._deserialize_properties(row[5]),
                created_at=datetime.fromisoformat(row[6]),
            )

    async def get_entities_by_project(self, project_id: UUID) -> list[Entity]:
        """Get all entities in project"""
        async with self.db.execute(
            "SELECT * FROM entities WHERE project_id = ?", (str(project_id),)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                Entity(
                    id=UUID(row[0]),
                    project_id=UUID(row[1]),
                    entity_type=EntityType(row[2]),
                    name=row[3],
                    description=row[4],
                    properties=self._deserialize_properties(row[5]),
                    created_at=datetime.fromisoformat(row[6]),
                )
                for row in rows
            ]

    async def update_entity(self, entity: Entity) -> None:
        """Update entity record"""
        await self.db.execute(
            """
            UPDATE entities
            SET project_id = ?, entity_type = ?, name = ?, description = ?, properties = ?
            WHERE id = ?
            """,
            (
                str(entity.project_id),
                entity.entity_type.value,
                entity.name,
                entity.description,
                self._serialize_properties(entity.properties),
                str(entity.id),
            ),
        )
        await self.db.commit()

    async def delete_entity(self, entity_id: UUID) -> None:
        """Delete entity record"""
        await self.db.execute("DELETE FROM entities WHERE id = ?", (str(entity_id),))
        await self.db.commit()

    # === RELATIONSHIP CRUD ===

    async def insert_relationship(self, relationship: Relationship) -> None:
        """Insert relationship record"""
        await self.db.execute(
            """
            INSERT INTO relationships 
            (id, source_id, source_type, target_id, target_type, relation_type,
             strength, valid_from, valid_until, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(relationship.id),
                str(relationship.source_id),
                relationship.source_type.value,
                str(relationship.target_id),
                relationship.target_type.value,
                relationship.relation_type.value,
                str(relationship.strength),
                relationship.valid_from.isoformat() if relationship.valid_from else None,
                relationship.valid_until.isoformat() if relationship.valid_until else None,
                self._serialize_metadata(relationship.metadata),
                relationship.created_at.isoformat(),
            ),
        )
        await self.db.commit()

    async def get_relationship_by_id(self, relationship_id: UUID) -> Relationship | None:
        """Get single relationship by ID"""
        async with self.db.execute(
            "SELECT * FROM relationships WHERE id = ?", (str(relationship_id),)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            return Relationship(
                id=UUID(row[0]),
                source_id=UUID(row[1]),
                source_type=SourceType(row[2]),
                target_id=UUID(row[3]),
                target_type=SourceType(row[4]),
                relation_type=RelationType(row[5]),
                strength=Decimal(row[6]),
                valid_from=datetime.fromisoformat(row[7]) if row[7] else None,
                valid_until=datetime.fromisoformat(row[8]) if row[8] else None,
                metadata=self._deserialize_metadata(row[9]),
                created_at=datetime.fromisoformat(row[10]),
            )

    async def get_relationships_by_source(
        self, source_id: UUID, source_type: SourceType
    ) -> list[Relationship]:
        """Get relationships where this is the source"""
        async with self.db.execute(
            "SELECT * FROM relationships WHERE source_id = ? AND source_type = ?",
            (str(source_id), source_type.value),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                Relationship(
                    id=UUID(row[0]),
                    source_id=UUID(row[1]),
                    source_type=SourceType(row[2]),
                    target_id=UUID(row[3]),
                    target_type=SourceType(row[4]),
                    relation_type=RelationType(row[5]),
                    strength=Decimal(row[6]),
                    valid_from=datetime.fromisoformat(row[7]) if row[7] else None,
                    valid_until=datetime.fromisoformat(row[8]) if row[8] else None,
                    metadata=self._deserialize_metadata(row[9]),
                    created_at=datetime.fromisoformat(row[10]),
                )
                for row in rows
            ]

    async def get_relationships_by_target(
        self, target_id: UUID, target_type: SourceType
    ) -> list[Relationship]:
        """Get relationships where this is the target"""
        async with self.db.execute(
            "SELECT * FROM relationships WHERE target_id = ? AND target_type = ?",
            (str(target_id), target_type.value),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                Relationship(
                    id=UUID(row[0]),
                    source_id=UUID(row[1]),
                    source_type=SourceType(row[2]),
                    target_id=UUID(row[3]),
                    target_type=SourceType(row[4]),
                    relation_type=RelationType(row[5]),
                    strength=Decimal(row[6]),
                    valid_from=datetime.fromisoformat(row[7]) if row[7] else None,
                    valid_until=datetime.fromisoformat(row[8]) if row[8] else None,
                    metadata=self._deserialize_metadata(row[9]),
                    created_at=datetime.fromisoformat(row[10]),
                )
                for row in rows
            ]

    async def update_relationship(self, relationship: Relationship) -> None:
        """Update relationship record"""
        await self.db.execute(
            """
            UPDATE relationships
            SET source_id = ?, source_type = ?, target_id = ?, target_type = ?,
                relation_type = ?, strength = ?, valid_from = ?, valid_until = ?, metadata = ?
            WHERE id = ?
            """,
            (
                str(relationship.source_id),
                relationship.source_type.value,
                str(relationship.target_id),
                relationship.target_type.value,
                relationship.relation_type.value,
                str(relationship.strength),
                relationship.valid_from.isoformat() if relationship.valid_from else None,
                relationship.valid_until.isoformat() if relationship.valid_until else None,
                self._serialize_metadata(relationship.metadata),
                str(relationship.id),
            ),
        )
        await self.db.commit()

    async def delete_relationship(self, relationship_id: UUID) -> None:
        """Delete relationship record"""
        await self.db.execute("DELETE FROM relationships WHERE id = ?", (str(relationship_id),))
        await self.db.commit()

    # === STATE SNAPSHOT CRUD ===

    async def insert_snapshot(self, snapshot: StateSnapshot) -> None:
        """Insert snapshot record"""
        await self.db.execute(
            """
            INSERT INTO state_snapshots (id, timeline_id, timestamp, state, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(snapshot.id),
                str(snapshot.timeline_id),
                snapshot.timestamp.isoformat(),
                self._serialize_world_state(snapshot.state),
                snapshot.created_at.isoformat(),
            ),
        )
        await self.db.commit()

    async def get_snapshot_by_id(self, snapshot_id: UUID) -> StateSnapshot | None:
        """Get single snapshot by ID"""
        async with self.db.execute(
            "SELECT * FROM state_snapshots WHERE id = ?", (str(snapshot_id),)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            return StateSnapshot(
                id=UUID(row[0]),
                timeline_id=UUID(row[1]),
                timestamp=datetime.fromisoformat(row[2]),
                state=self._deserialize_world_state(row[3]),
                created_at=datetime.fromisoformat(row[4]),
            )

    async def get_snapshots_by_timeline(self, timeline_id: UUID) -> list[StateSnapshot]:
        """Get all snapshots for timeline"""
        async with self.db.execute(
            "SELECT * FROM state_snapshots WHERE timeline_id = ?", (str(timeline_id),)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                StateSnapshot(
                    id=UUID(row[0]),
                    timeline_id=UUID(row[1]),
                    timestamp=datetime.fromisoformat(row[2]),
                    state=self._deserialize_world_state(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                )
                for row in rows
            ]

    async def delete_snapshot(self, snapshot_id: UUID) -> None:
        """Delete snapshot record"""
        await self.db.execute("DELETE FROM state_snapshots WHERE id = ?", (str(snapshot_id),))
        await self.db.commit()

    # === EVENT-ENTITY LINKS ===

    async def insert_event_entity_link(
        self, event_id: UUID, entity_id: UUID, role: str
    ) -> None:
        """Insert event-entity link"""
        await self.db.execute(
            """
            INSERT INTO event_entity_links (event_id, entity_id, role)
            VALUES (?, ?, ?)
            """,
            (str(event_id), str(entity_id), role.lower()),
        )
        await self.db.commit()

    async def get_event_entity_links_by_event(self, event_id: UUID) -> list[tuple[UUID, str]]:
        """Get (entity_id, role) pairs for event"""
        async with self.db.execute(
            "SELECT entity_id, role FROM event_entity_links WHERE event_id = ?",
            (str(event_id),),
        ) as cursor:
            rows = await cursor.fetchall()
            return [(UUID(row[0]), row[1]) for row in rows]

    async def get_event_entity_links_by_entity(self, entity_id: UUID) -> list[tuple[UUID, str]]:
        """Get (event_id, role) pairs for entity"""
        async with self.db.execute(
            "SELECT event_id, role FROM event_entity_links WHERE entity_id = ?",
            (str(entity_id),),
        ) as cursor:
            rows = await cursor.fetchall()
            return [(UUID(row[0]), row[1]) for row in rows]

    async def delete_event_entity_link(
        self, event_id: UUID, entity_id: UUID, role: str | None = None
    ) -> None:
        """Delete event-entity link(s)"""
        if role:
            await self.db.execute(
                "DELETE FROM event_entity_links WHERE event_id = ? AND entity_id = ? AND role = ?",
                (str(event_id), str(entity_id), role.lower()),
            )
        else:
            await self.db.execute(
                "DELETE FROM event_entity_links WHERE event_id = ? AND entity_id = ?",
                (str(event_id), str(entity_id)),
            )
        await self.db.commit()
