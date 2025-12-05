"""
Project Management Tools

Tools for creating and managing projects (top-level containers for timelines).
"""

from typing import Any
from uuid import UUID

from ..auth import get_user_id
from ..dependencies import get_service
from ..server import mcp


@mcp.tool
async def create_project(name: str, description: str | None = None) -> dict[str, Any]:
    """
    Create a new project for organizing timelines.

    Args:
        name: Project name
        description: Optional project description

    Returns:
        Project details including id, name, description, created_at
    """
    user_id = get_user_id()
    service = await get_service()

    project = await service.create_project(
        user_id=user_id,
        name=name,
        description=description,
    )

    return {
        "id": str(project.id),
        "user_id": str(project.user_id),
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
    }


@mcp.tool
async def list_projects() -> list[dict[str, Any]]:
    """
    List all projects for the authenticated user.

    Returns:
        List of projects with their details
    """
    user_id = get_user_id()
    service = await get_service()

    projects = await service.list_user_projects(user_id)

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "created_at": p.created_at.isoformat(),
        }
        for p in projects
    ]


@mcp.tool
async def get_project(project_id: str) -> dict[str, Any]:
    """
    Get details of a specific project.

    Args:
        project_id: UUID of the project

    Returns:
        Project details

    Raises:
        ValueError: If project not found or user doesn't have access
    """
    user_id = get_user_id()
    service = await get_service()

    project = await service.get_project(UUID(project_id))

    if project is None:
        raise ValueError(f"Project {project_id} not found")

    # Verify ownership
    if project.user_id != user_id:
        raise ValueError(f"Access denied: project {project_id} belongs to another user")

    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
    }
