"""
Domain Models - Core entities with Pydantic validation
All models use strict typing with no Any or generic dicts
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

# Use typing.TYPE_CHECKING to avoid runtime import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic_core import ValidationInfo
else:
    ValidationInfo = object  # Fallback for runtime


# === Value Objects for Type Safety ===


class PropertyValue(BaseModel):
    """Strongly typed property value with tagged union"""

    string_val: str | None = None
    number_val: Decimal | None = None
    boolean_val: bool | None = None
    datetime_val: datetime | None = None

    def get_value(self) -> str | Decimal | bool | datetime:
        """Extract the actual value"""
        if self.string_val is not None:
            return self.string_val
        if self.number_val is not None:
            return self.number_val
        if self.boolean_val is not None:
            return self.boolean_val
        if self.datetime_val is not None:
            return self.datetime_val
        raise ValueError("PropertyValue must have exactly one value set")


class EntityProperty(BaseModel):
    """Key-value pair for entity properties"""

    key: str = Field(min_length=1)
    value: PropertyValue


class EntityProperties(BaseModel):
    """Collection of entity properties"""

    properties: dict[str, EntityProperty] = Field(default_factory=dict)

    def get(self, key: str) -> PropertyValue | None:
        """Get property by key"""
        prop = self.properties.get(key)
        return prop.value if prop else None

    def set(self, key: str, value: PropertyValue) -> None:
        """Set or update property"""
        self.properties[key] = EntityProperty(key=key, value=value)


class StateDelta(BaseModel):
    """State changes for an event"""

    global_changes: dict[str, EntityProperty] = Field(default_factory=dict)
    entity_changes: dict[UUID, dict[str, EntityProperty]] = Field(default_factory=dict)


class WorldState(BaseModel):
    """Complete world state at a point in time"""

    global_properties: dict[str, EntityProperty] = Field(default_factory=dict)
    entity_states: dict[UUID, dict[str, EntityProperty]] = Field(default_factory=dict)


class Metadata(BaseModel):
    """Typed metadata container"""

    properties: dict[str, EntityProperty] = Field(default_factory=dict)


# === Enums ===


class EventType(Enum):
    """Semantic classification of events - domain-agnostic"""

    # Factual/Observational
    OBSERVATION = "observation"
    MEASUREMENT = "measurement"
    DECLARATION = "declaration"

    # Transformational
    TRANSITION = "transition"
    CREATION = "creation"
    DESTRUCTION = "destruction"
    MODIFICATION = "modification"

    # Relational
    INTERACTION = "interaction"
    ASSOCIATION = "association"
    DISSOCIATION = "dissociation"

    # Temporal/Structural
    MILESTONE = "milestone"
    BOUNDARY = "boundary"
    REFERENCE = "reference"

    # Meta
    ANNOTATION = "annotation"
    REVISION = "revision"


class RelationType(Enum):
    """Types of relationships between entities/events"""

    CAUSAL = "causal"
    TEMPORAL = "temporal"
    HIERARCHICAL = "hierarchical"
    REFERENTIAL = "referential"
    CONTRADICTORY = "contradictory"
    REINFORCING = "reinforcing"
    CONDITIONAL = "conditional"
    PERSPECTIVE = "perspective"


class TimelineStatus(Enum):
    """Canonical vs speculative timelines"""

    CANONICAL = "canonical"
    HYPOTHETICAL = "hypothetical"
    DRAFT = "draft"
    SUBJECTIVE = "subjective"
    ARCHIVED = "archived"


class EntityType(Enum):
    """Types of persistent entities"""

    CHARACTER = "character"
    PLACE = "place"
    OBJECT = "object"
    CONCEPT = "concept"
    ORGANIZATION = "organization"
    THEME = "theme"


class SourceType(Enum):
    """Types of relationship sources/targets"""

    EVENT = "event"
    ENTITY = "entity"
    TIMELINE = "timeline"


class ParticipationRole:
    """Standard roles for event-entity participation"""

    # Primary roles
    ACTOR = "actor"
    SUBJECT = "subject"
    LOCATION = "location"
    OBSERVER = "observer"

    # Object roles
    TOOL = "tool"
    TARGET = "target"
    POSSESSION = "possession"

    # Contextual roles
    CAUSE = "cause"
    BENEFICIARY = "beneficiary"
    CONTEXT = "context"

    @classmethod
    def all_roles(cls) -> list[str]:
        """Get all standard role names"""
        return [
            cls.ACTOR,
            cls.SUBJECT,
            cls.LOCATION,
            cls.OBSERVER,
            cls.TOOL,
            cls.TARGET,
            cls.POSSESSION,
            cls.CAUSE,
            cls.BENEFICIARY,
            cls.CONTEXT,
        ]


# === Base Models ===


class TimestampedModel(BaseModel):
    """Base model with creation timestamp"""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IdentifiedModel(TimestampedModel):
    """Base model with UUID and timestamp"""

    id: UUID = Field(default_factory=uuid4)


# === Core Domain Models ===


class Project(IdentifiedModel):
    """Project container for timelines (tenant isolation)"""

    user_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    metadata: Metadata = Field(default_factory=Metadata)


class Timeline(IdentifiedModel):
    """A sequence of events representing temporal progression"""

    project_id: UUID
    user_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    parent_timeline_id: UUID | None = None
    status: TimelineStatus = TimelineStatus.CANONICAL
    metadata: Metadata = Field(default_factory=Metadata)


class Event(IdentifiedModel):
    """Atomic unit of temporal information"""

    timeline_id: UUID
    timestamp: datetime
    end_timestamp: datetime | None = None
    event_type: EventType
    description: str = Field(min_length=1)
    importance_score: Decimal = Field(
        default=Decimal("0.5"), ge=Decimal("0.0"), le=Decimal("1.0")
    )
    detail_level: int = Field(default=1, ge=0, le=2)
    state_delta: StateDelta = Field(default_factory=StateDelta)
    metadata: Metadata = Field(default_factory=Metadata)

    @field_validator("end_timestamp")
    @classmethod
    def validate_end_timestamp(cls, v: datetime | None, info: ValidationInfo) -> datetime | None:
        """Ensure end_timestamp is after timestamp if provided"""
        if v is not None and "timestamp" in info.data:
            if v <= info.data["timestamp"]:
                raise ValueError("end_timestamp must be after timestamp")
        return v


class Entity(IdentifiedModel):
    """Persistent concept across timelines (character, place, object, etc.)"""

    project_id: UUID
    entity_type: EntityType
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    properties: EntityProperties = Field(default_factory=EntityProperties)


class Relationship(IdentifiedModel):
    """Semantic connection between entities or events"""

    source_id: UUID
    source_type: SourceType
    target_id: UUID
    target_type: SourceType
    relation_type: RelationType
    strength: Decimal = Field(default=Decimal("1.0"), ge=Decimal("0.0"), le=Decimal("1.0"))
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: Metadata = Field(default_factory=Metadata)

    @field_validator("valid_until")
    @classmethod
    def validate_valid_until(cls, v: datetime | None, info: ValidationInfo) -> datetime | None:
        """Ensure valid_until is after valid_from if both provided"""
        if v is not None and info.data.get("valid_from") is not None:
            if v <= info.data["valid_from"]:
                raise ValueError("valid_until must be after valid_from")
        return v


class EventParticipation(BaseModel):
    """Many-to-many: entities participating in events"""

    event_id: UUID
    entity_id: UUID
    role: str = Field(min_length=1, max_length=100)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role (normalize to lowercase)"""
        return v.lower()


class StateSnapshot(IdentifiedModel):
    """Cached world state at a specific time"""

    timeline_id: UUID
    timestamp: datetime
    state: WorldState = Field(default_factory=WorldState)


# === Query Result Models ===


class TimelineTree(BaseModel):
    """Hierarchical timeline structure"""

    parent_id: UUID
    children: list[Timeline] = Field(default_factory=list)


class EventRange(BaseModel):
    """Events within a time range"""

    timeline_id: UUID
    start: datetime
    end: datetime
    events: list[Event] = Field(default_factory=list)


class EntityEventLink(BaseModel):
    """Entity participation in an event"""

    entity: Entity
    role: str


class CausalPath(BaseModel):
    """Chain of causally related events"""

    events: list[Event] = Field(default_factory=list)


class SummaryEvent(BaseModel):
    """Compressed event information"""

    timestamp: datetime
    description: str
    importance: Decimal


class TimelineSummary(BaseModel):
    """Multi-resolution timeline summary"""

    recent_events: list[SummaryEvent] = Field(default_factory=list)
    important_events: list[SummaryEvent] = Field(default_factory=list)
    event_count: int = 0
    first_event: datetime | None = None
    last_event: datetime | None = None
