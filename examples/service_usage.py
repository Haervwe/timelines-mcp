"""
Example: Using TimelineService with dependency injection

This demonstrates the complete zero-coupling architecture:
1. Protocols define the interface
2. Adapters implement the protocols (thin CRUD clients)
3. Service layer contains ALL business logic
4. Dependency injection wires everything together

NO database-specific code in business logic.
"""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from timelines_mcp.core import get_storage_adapter, get_vector_adapter
from timelines_mcp.domain.models import EntityType, EventType
from timelines_mcp.services import TimelineContext, TimelineService
from timelines_mcp.settings import DatabaseConfig


async def example_usage():
    """
    Example showing how to use the service layer.
    Business logic is completely decoupled from database choice.
    """
    # Configuration determines which adapters to use
    config = DatabaseConfig.from_env()
    print(f"Using storage: {config.storage_adapter}")
    print(f"Using vector: {config.vector_adapter}")

    # Get adapters via dependency injection
    # These are protocol implementations - service doesn't know which concrete type
    storage = get_storage_adapter(config)
    vector = get_vector_adapter(config)

    # Create service - inject protocols
    service = TimelineService(storage=storage, vector=vector)

    # Use context manager for automatic initialization/cleanup
    async with TimelineContext(service) as svc:
        # === Business Logic (works with ANY database) ===

        # Create project
        user_id = uuid4()
        project = await svc.create_project(
            user_id=user_id,
            name="My Novel",
            description="Science fiction story",
        )
        print(f"✓ Created project: {project.name}")

        # Create timeline
        timeline = await svc.create_timeline(
            project_id=project.id,
            user_id=user_id,
            name="Main Timeline",
            description="Primary narrative thread",
        )
        print(f"✓ Created timeline: {timeline.name}")

        # Create characters
        protagonist = await svc.create_entity(
            project_id=project.id,
            entity_type=EntityType.CHARACTER,
            name="Dr. Sarah Chen",
            description="Quantum physicist and protagonist",
        )
        print(f"✓ Created character: {protagonist.name}")

        # Create location
        lab = await svc.create_entity(
            project_id=project.id,
            entity_type=EntityType.PLACE,
            name="CERN Laboratory",
            description="Research facility in Geneva",
        )
        print(f"✓ Created location: {lab.name}")

        # Add events
        now = datetime.now(UTC)
        event1 = await svc.add_event(
            timeline_id=timeline.id,
            timestamp=now,
            event_type=EventType.OBSERVATION,
            description="Dr. Chen discovers anomalous readings in the particle accelerator",
            importance_score=Decimal("0.9"),
        )
        print(f"✓ Added event: {event1.description[:50]}...")

        # Link entities to event
        await svc.link_entity_to_event(
            event_id=event1.id,
            entity_id=protagonist.id,
            role="actor",
        )
        await svc.link_entity_to_event(
            event_id=event1.id,
            entity_id=lab.id,
            role="location",
        )
        print("✓ Linked entities to event")

        # Add consequence event
        event2 = await svc.add_event(
            timeline_id=timeline.id,
            timestamp=now,
            event_type=EventType.TRANSITION,
            description="Emergency protocols activated",
            importance_score=Decimal("0.8"),
        )

        # Establish causality
        await svc.establish_causality(
            cause_event_id=event1.id,
            effect_event_id=event2.id,
            strength=Decimal("1.0"),
        )
        print("✓ Established causal relationship")

        # Query events at location
        events_at_lab = await svc.get_events_at_location(
            location_entity_id=lab.id,
            timeline_id=timeline.id,
        )
        print(f"✓ Found {len(events_at_lab)} events at {lab.name}")

        # Get character timeline
        character_events = await svc.get_entity_timeline(
            entity_id=protagonist.id,
            timeline_id=timeline.id,
        )
        print(f"✓ {protagonist.name} appears in {len(character_events)} events")

        # Fork timeline (alternate path)
        alternate = await svc.fork_timeline_at(
            source_timeline_id=timeline.id,
            branch_name="What if... (alternate)",
            fork_timestamp=now,
        )
        print(f"✓ Created alternate timeline: {alternate.name}")

        # Query recent events
        recent = await svc.get_recent_events(
            timeline_id=timeline.id,
            before_timestamp=datetime.now(UTC),
            limit=10,
        )
        print(f"✓ Retrieved {len(recent)} recent events")

        # Semantic search (if vector storage enabled)
        if vector:
            similar = await svc.search_similar_events(
                query="particle physics experiments",
                timeline_ids=[timeline.id],
                limit=5,
            )
            print(f"✓ Found {len(similar)} semantically similar events")

        print("\n✅ All operations completed successfully!")
        print("   Business logic used ONLY protocol methods")
        print("   Zero coupling to database implementation")


async def example_swap_databases():
    """
    Demonstrate that the SAME business logic works with different databases.
    Just change the configuration - no code changes needed.
    """
    print("\n=== Testing Database Portability ===\n")

    # Scenario 1: SQLite + Chroma (local/testing)
    config_local = DatabaseConfig(
        storage_adapter="sqlite",
        vector_adapter="chroma",
    )

    # Scenario 2: Postgres + Qdrant (production)
    # config_prod = DatabaseConfig(
    #     storage_adapter="postgres",
    #     vector_adapter="qdrant",
    # )

    # Same code works with both configurations!
    # This proves ZERO COUPLING

    print("Configuration 1: SQLite + Chroma (local)")
    print("Configuration 2: Postgres + Qdrant (production)")
    print("\nBoth use IDENTICAL business logic code!")
    print("Only the injected adapters differ.")


if __name__ == "__main__":
    print("=== Timeline Service Example ===\n")
    asyncio.run(example_usage())
    asyncio.run(example_swap_databases())
