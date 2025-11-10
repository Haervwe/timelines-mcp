# timelines-mcp

MCP server to aid LLMs in maintaining coherent long generations for time dependent narratives (fiction / history).

## Overview

This is a FastMCP server that helps Language Models maintain coherent timelines, track events, and manage characters across long-form narratives, whether fiction or historical accounts.

## Project Structure

```
timelines-mcp/
├── src/
│   └── timelines_mcp/
│       ├── __init__.py          # Main package initialization
│       ├── server.py            # FastMCP server entry point
│       ├── domain/              # Domain objects (Timeline, Event, Character, etc.)
│       │   └── __init__.py
│       ├── adapters/            # Database adapters for persistence
│       │   └── __init__.py
│       ├── tools/               # MCP tools exposed via FastMCP
│       │   └── __init__.py
│       └── agents/              # Agent implementations for complex operations
│           └── __init__.py
├── tests/                       # Test suite
│   └── __init__.py
├── pyproject.toml              # Python project configuration
├── README.md                   # This file
└── LICENSE
```

## Installation

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Development

The project uses:
- **FastMCP** for the MCP server framework
- **pytest** for testing
- **ruff** for linting and formatting

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
ruff format .
```

## Usage

```bash
# Run the server (implementation details to be added)
python -m timelines_mcp.server
```

## License

See LICENSE file for details.
