"""
Main FastMCP Server - Infrastructure Layer

This module initializes the FastMCP server.
Tools are defined in the tools/ directory and imported here.
"""

from fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP(name="Timelines MCP")

# Import and register tools (they will auto-register via decorators)
from .tools import project_tools  # noqa: F401
