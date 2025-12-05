"""
Main entry point for running the Timelines MCP server.

Run with:
    python -m timelines_mcp
"""

import os

from .server import mcp


def main() -> None:
    """Run the server with configured transport."""
    # Determine transport from environment or default to stdio
    transport = os.getenv("FASTMCP_TRANSPORT", "stdio").lower()

    if transport == "http":
        # HTTP mode - requires JWT authentication
        host = os.getenv("FASTMCP_HOST", "0.0.0.0")
        port = int(os.getenv("FASTMCP_PORT", "8000"))
        mcp.run(transport="http", host=host, port=port)
    else:
        # STDIO mode - single user, no authentication required
        mcp.run()  # Defaults to stdio


if __name__ == "__main__":
    main()
