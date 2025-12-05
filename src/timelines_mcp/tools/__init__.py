"""
MCP Tools - Exposed functionality for LLMs

Each file in this directory defines one or more MCP tools.
Tools are auto-registered with the FastMCP server when imported in server.py.

All tools automatically handle:
- JWT authentication (HTTP mode)
- Single-user mode (STDIO)
- User access control via get_user_id()
"""

# Import all tool modules to register them with the server
from . import project_tools  # noqa: F401

__all__ = ["project_tools"]

