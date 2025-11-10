"""
Main FastMCP Server

This module initializes and runs the FastMCP server for the timelines application.
"""

from fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("Timelines MCP Server")


@mcp.tool()
def get_server_info() -> dict:
    """Get information about the Timelines MCP server."""
    return {
        "name": "Timelines MCP Server",
        "version": "0.1.0",
        "description": "MCP server for maintaining coherent timelines in narratives",
    }


def main():
    """Run the server."""
    # The FastMCP server will be started by the MCP protocol
    # This can be customized based on deployment needs
    pass


if __name__ == "__main__":
    main()
