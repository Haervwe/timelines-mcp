#!/bin/bash
# Test the MCP server with a JWT token

set -e

USER_ID="${1:-550e8400-e29b-41d4-a716-446655440000}"

echo "Generating JWT token for user: $USER_ID"
TOKEN=$(uv run python scripts/generate_jwt.py "$USER_ID" 2>/dev/null | grep "^eyJ" | head -1)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to generate token"
    exit 1
fi

echo "Token: ${TOKEN:0:50}..."
echo
echo "Testing server at http://127.0.0.1:8000/mcp"
echo

# Test 1: List tools
echo "=== Test 1: List Available Tools ==="
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' | jq '.'

echo
echo

# Test 2: Create a project
echo "=== Test 2: Create Project ==="
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"create_project","arguments":{"name":"My Test Project","description":"Created via curl"}},"id":2}' | jq '.'

echo
echo

# Test 3: List projects
echo "=== Test 3: List Projects ==="
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_projects","arguments":{}},"id":3}' | jq '.'

echo
