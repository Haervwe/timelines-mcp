"""
Example: Querying events by location

This demonstrates how to:
1. Create places/locations as entities
2. Link events to locations
3. Query all events that happened at a specific place
4. Using dependency injection to get storage adapter
"""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from timelines_mcp.core import close_storage, get_storage_adapter, initialize_storage
from timelines_mcp.domain.models import (
    EntityProperties,
    EntityProperty,
    EntityType,
    EventType,
    PropertyValue,
    StateDelta,
)


async def main() -> None:
    # Get storage adapter from DI container (uses .env config)
    storage = get_storage_adapter()
    await initialize_storage(storage)

    # Create a project
    user_id = uuid4()
    project = await storage.create_project(
        user_id=user_id,
        name="Fantasy Novel",
        description="A tale of adventure",
    )

    # Create timeline
    timeline = await storage.create_timeline(
        project_id=project.id,
        user_id=user_id,
        name="Main Story",
    )

    # === Create Locations/Places ===

    tavern = await storage.create_entity(
        project_id=project.id,
        entity_type=EntityType.PLACE,
        name="The Golden Tankard",
        description="A busy tavern in the port district",
        properties=EntityProperties(
            properties={
                "district": EntityProperty(key="district", value=PropertyValue(string_val="port")),
                "capacity": EntityProperty(key="capacity", value=PropertyValue(number_val=Decimal("50"))),
                "owner": EntityProperty(key="owner", value=PropertyValue(string_val="Old Marcus")),
            }
        ),
    )

    marketplace = await storage.create_entity(
        project_id=project.id,
        entity_type=EntityType.PLACE,
        name="Central Marketplace",
        description="The main trading hub of the city",
        properties=EntityProperties(
            properties={
                "size": EntityProperty(key="size", value=PropertyValue(string_val="large")),
                "stalls": EntityProperty(key="stalls", value=PropertyValue(number_val=Decimal("200"))),
            }
        ),
    )

    castle = await storage.create_entity(
        project_id=project.id,
        entity_type=EntityType.PLACE,
        name="Ironhall Castle",
        description="The royal fortress overlooking the city",
        properties=EntityProperties(
            properties={
                "fortification_level": EntityProperty(
                    key="fortification_level",
                    value=PropertyValue(string_val="high"),
                ),
                "garrison": EntityProperty(key="garrison", value=PropertyValue(number_val=Decimal("500"))),
            }
        ),
    )

    # === Create Characters ===

    alice = await storage.create_entity(
        project_id=project.id,
        entity_type=EntityType.CHARACTER,
        name="Alice the Wanderer",
        description="A skilled ranger and tracker",
        properties=EntityProperties(
            properties={
                "age": EntityProperty(key="age", value=PropertyValue(number_val=Decimal("28"))),
                "class": EntityProperty(key="class", value=PropertyValue(string_val="ranger")),
            }
        ),
    )

    bob = await storage.create_entity(
        project_id=project.id,
        entity_type=EntityType.CHARACTER,
        name="Bob the Merchant",
        description="A wealthy trader",
        properties=EntityProperties(
            properties={
                "age": EntityProperty(key="age", value=PropertyValue(number_val=Decimal("45"))),
                "class": EntityProperty(key="class", value=PropertyValue(string_val="merchant")),
            }
        ),
    )

    # === Create Events ===

    # Event 1: Meeting at the tavern
    event1 = await storage.add_event(
        timeline_id=timeline.id,
        timestamp=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        event_type=EventType.INTERACTION,
        description="Alice meets Bob at the tavern to discuss a job",
        state_delta=StateDelta(
            global_changes={
                "mood": EntityProperty(key="mood", value=PropertyValue(string_val="tense")),
                "lighting": EntityProperty(key="lighting", value=PropertyValue(string_val="dim")),
            },
            entity_changes={},
        ),
    )

    # Link participants (roles are now strings)
    await storage.link_event_entity(event1.id, alice.id, "actor")
    await storage.link_event_entity(event1.id, bob.id, "actor")
    await storage.link_event_entity(event1.id, tavern.id, "location")

    # Event 2: Another meeting at the tavern
    event2 = await storage.add_event(
        timeline_id=timeline.id,
        timestamp=datetime(2024, 1, 2, 20, 0, tzinfo=UTC),
        event_type=EventType.INTERACTION,
        description="Bob returns to the tavern seeking information",
        state_delta=StateDelta(
            global_changes={
                "mood": EntityProperty(key="mood", value=PropertyValue(string_val="suspicious")),
            },
            entity_changes={},
        ),
    )

    await storage.link_event_entity(event2.id, bob.id, "actor")
    await storage.link_event_entity(event2.id, tavern.id, "location")

    # Event 3: Fight at marketplace
    event3 = await storage.add_event(
        timeline_id=timeline.id,
        timestamp=datetime(2024, 1, 3, 12, 0, tzinfo=UTC),
        event_type=EventType.INTERACTION,
        description="Alice confronts thieves at the marketplace",
        state_delta=StateDelta(
            global_changes={
                "violence": EntityProperty(key="violence", value=PropertyValue(string_val="combat")),
                "outcome": EntityProperty(key="outcome", value=PropertyValue(string_val="victory")),
            },
            entity_changes={},
        ),
    )

    await storage.link_event_entity(event3.id, alice.id, "actor")
    await storage.link_event_entity(event3.id, marketplace.id, "location")

    # Event 4: Royal summons at castle
    event4 = await storage.add_event(
        timeline_id=timeline.id,
        timestamp=datetime(2024, 1, 5, 14, 0, tzinfo=UTC),
        event_type=EventType.MILESTONE,
        description="Alice and Bob are summoned to the castle",
        state_delta=StateDelta(
            global_changes={
                "political_tension": EntityProperty(
                    key="political_tension",
                    value=PropertyValue(string_val="high"),
                ),
            },
            entity_changes={},
        ),
    )

    await storage.link_event_entity(event4.id, alice.id, "subject")
    await storage.link_event_entity(event4.id, bob.id, "subject")
    await storage.link_event_entity(event4.id, castle.id, "location")

    # === QUERY: All events at the tavern ===

    print("\n=== Events at The Golden Tankard ===")
    tavern_events = await storage.get_events_at_location(
        location_id=tavern.id,
        timeline_id=timeline.id,
    )

    for event in tavern_events:
        print(f"[{event.timestamp}] {event.description}")

    # === QUERY: All events involving Alice ===

    print("\n=== Events involving Alice ===")
    alice_events = await storage.get_entity_events(
        entity_id=alice.id,
        timeline_id=timeline.id,
    )

    for event in alice_events:
        # Get the location for this event
        entities = await storage.get_event_entities(event.id)
        locations = [link.entity for link in entities if link.role == "location"]
        location_name = locations[0].name if locations else "Unknown location"

        print(f"[{event.timestamp}] at {location_name}: {event.description}")

    # === QUERY: Events with both Alice AND Bob ===

    print("\n=== Events with both Alice and Bob ===")
    both_events = await storage.get_events_by_entities(
        entity_ids=[alice.id, bob.id],
        timeline_id=timeline.id,
        match_all=True,  # Both must be present
    )

    for event in both_events:
        entities = await storage.get_event_entities(event.id)
        locations = [link.entity for link in entities if link.role == "location"]
        location_name = locations[0].name if locations else "Unknown"
        print(f"[{event.timestamp}] at {location_name}: {event.description}")

    # === QUERY: Events at marketplace in specific time range ===

    print("\n=== Events at marketplace in early January ===")
    marketplace_events = await storage.get_events_at_location(
        location_id=marketplace.id,
        timeline_id=timeline.id,
        start=datetime(2024, 1, 1, tzinfo=UTC),
        end=datetime(2024, 1, 10, tzinfo=UTC),
    )

    for event in marketplace_events:
        print(f"[{event.timestamp}] {event.description}")

    # === QUERY: Where did Alice act? (not just observe) ===

    print("\n=== Places where Alice was an actor ===")
    alice_actor_events = await storage.get_entity_events(
        entity_id=alice.id,
        timeline_id=timeline.id,
        role="actor",  # Filter by role
    )

    locations_visited = set()
    for event in alice_actor_events:
        entities = await storage.get_event_entities(event.id)
        for link in entities:
            if link.role == "location":
                locations_visited.add(link.entity.name)

    print(f"Alice actively participated in events at: {', '.join(locations_visited)}")

    await close_storage(storage)


if __name__ == "__main__":
    asyncio.run(main())

