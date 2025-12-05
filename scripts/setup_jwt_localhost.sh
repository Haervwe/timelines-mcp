#!/bin/bash
# Quick setup script for JWT authentication on localhost

set -e

echo "========================================="
echo "Timelines MCP - JWT Setup for Localhost"
echo "========================================="
echo

# Check if .env exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

# Create .env with JWT configuration
cat > .env << 'EOF'
# Storage Configuration
STORAGE_ADAPTER=sqlite
SQLITE_PATH=./data/timelines.db
VECTOR_ADAPTER=chroma
CHROMA_PERSIST_DIR=./data/chroma

# Server Transport
FASTMCP_TRANSPORT=http
FASTMCP_HOST=127.0.0.1
FASTMCP_PORT=8000

# JWT Authentication (symmetric key for localhost)
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.jwt.JWTVerifier
FASTMCP_SERVER_AUTH_JWT_PUBLIC_KEY=your-secret-key-minimum-32-characters-long
FASTMCP_SERVER_AUTH_JWT_ALGORITHM=HS256
FASTMCP_SERVER_AUTH_JWT_ISSUER=timelines-mcp-local
FASTMCP_SERVER_AUTH_JWT_AUDIENCE=timelines-mcp-api
EOF

echo "✓ Created .env file with JWT configuration"
echo

# Generate a test token
echo "Generating test JWT token..."
echo
uv run python scripts/generate_jwt.py 550e8400-e29b-41d4-a716-446655440000 > /tmp/jwt_token.txt 2>&1

# Extract the token
TOKEN=$(grep "^eyJ" /tmp/jwt_token.txt | head -1)

echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo
echo "Your server is configured to run on: http://127.0.0.1:8000"
echo
echo "To start the server:"
echo "  uv run python -m timelines_mcp"
echo
echo "Test JWT Token (valid for 24 hours):"
echo "  User ID: 550e8400-e29b-41d4-a716-446655440000"
echo
echo "  Token: $TOKEN"
echo
echo "Test with curl:"
echo "  curl -X POST http://127.0.0.1:8000/mcp \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'Authorization: Bearer $TOKEN' \\"
echo "    -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}'"
echo
echo "Generate more tokens:"
echo "  uv run python scripts/generate_jwt.py [user_id]"
echo
echo "Full documentation: docs/JWT_SETUP.md"
echo
