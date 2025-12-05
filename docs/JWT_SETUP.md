# JWT Authentication Setup Guide

This guide shows you how to configure JWT authentication for the Timelines MCP server.

## Quick Start (Localhost Testing)

### 1. Create `.env` file

```bash
cp .env.example .env
```

### 2. Configure for HTTP mode with JWT

Edit `.env`:

```bash
# Enable HTTP transport
FASTMCP_TRANSPORT=http
FASTMCP_HOST=127.0.0.1
FASTMCP_PORT=8000

# Enable JWT authentication with symmetric key (HMAC)
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.jwt.JWTVerifier
FASTMCP_SERVER_AUTH_JWT_PUBLIC_KEY=your-secret-key-minimum-32-characters-long
FASTMCP_SERVER_AUTH_JWT_ALGORITHM=HS256
FASTMCP_SERVER_AUTH_JWT_ISSUER=timelines-mcp-local
FASTMCP_SERVER_AUTH_JWT_AUDIENCE=timelines-mcp-api

# Storage (keep SQLite for local testing)
STORAGE_ADAPTER=sqlite
VECTOR_ADAPTER=chroma
```

### 3. Generate a test JWT token

```bash
# Generate token with random user ID
python scripts/generate_jwt.py

# Or specify a user ID
python scripts/generate_jwt.py 550e8400-e29b-41d4-a716-446655440000
```

This will output something like:

```
================================================================================
JWT Token Generated Successfully
================================================================================

User ID: 550e8400-e29b-41d4-a716-446655440000

Token:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJpc3MiOiJ0aW1lbGluZXMtbWNwLWxvY2FsIiwiYXVkIjoidGltZWxpbmVzLW1jcC1hcGkiLCJpYXQiOjE3MzM0MzI0MDAsImV4cCI6MTczMzUxODgwMH0.xyz...

Authorization Header:
Authorization: Bearer eyJhbGci...
```

### 4. Start the server

```bash
python -m timelines_mcp
```

### 5. Test with curl

```bash
# Replace <TOKEN> with your generated token
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

## JWT Token Requirements

The JWT token MUST include these claims:

- **`sub`** (Subject): User ID as a valid UUID string
  - Example: `"550e8400-e29b-41d4-a716-446655440000"`
  - This is extracted by `get_user_id()` for access control

- **`iss`** (Issuer): Must match `FASTMCP_SERVER_AUTH_JWT_ISSUER`
  - Example: `"timelines-mcp-local"`

- **`aud`** (Audience): Must match `FASTMCP_SERVER_AUTH_JWT_AUDIENCE`
  - Example: `"timelines-mcp-api"`

- **`exp`** (Expiration): Unix timestamp when token expires
  - Server rejects expired tokens

- **`iat`** (Issued At): Unix timestamp when token was created

Example payload:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "iss": "timelines-mcp-local",
  "aud": "timelines-mcp-api",
  "iat": 1733432400,
  "exp": 1733518800,
  "name": "Test User",
  "email": "user@example.com"
}
```

## Authentication Methods

### Method 1: Symmetric Key (HMAC) - For Local/Dev

Use a shared secret key. Simple but less secure.

```bash
# .env
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.jwt.JWTVerifier
FASTMCP_SERVER_AUTH_JWT_PUBLIC_KEY=your-secret-key-minimum-32-characters-long
FASTMCP_SERVER_AUTH_JWT_ALGORITHM=HS256  # or HS384, HS512
FASTMCP_SERVER_AUTH_JWT_ISSUER=timelines-mcp-local
FASTMCP_SERVER_AUTH_JWT_AUDIENCE=timelines-mcp-api
```

**Pros**: Simple, works offline, good for local testing  
**Cons**: Shared secret must be kept secure  
**Use case**: Local development, testing, single-tenant deployments

### Method 2: Asymmetric Key (JWKS) - For Production

Use public/private key pairs with JWKS endpoint.

```bash
# .env
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.jwt.JWTVerifier
FASTMCP_SERVER_AUTH_JWT_JWKS_URI=https://auth.example.com/.well-known/jwks.json
FASTMCP_SERVER_AUTH_JWT_ISSUER=https://auth.example.com
FASTMCP_SERVER_AUTH_JWT_AUDIENCE=timelines-mcp-api
FASTMCP_SERVER_AUTH_JWT_REQUIRED_SCOPES=read:timelines,write:timelines
```

**Pros**: More secure, standard OAuth2/OIDC flow  
**Cons**: Requires external auth provider (Auth0, Keycloak, etc.)  
**Use case**: Production, multi-tenant SaaS

## Testing JWT Tokens

### Decode a token (without verification)

```bash
python -c "
import jwt
token = 'eyJhbGci...'
print(jwt.decode(token, options={'verify_signature': False}))
"
```

### Verify token with Python

```python
import jwt

token = "eyJhbGci..."
secret = "your-secret-key-minimum-32-characters-long"

try:
    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        issuer="timelines-mcp-local",
        audience="timelines-mcp-api"
    )
    print(f"Valid token for user: {payload['sub']}")
except jwt.ExpiredSignatureError:
    print("Token expired")
except jwt.InvalidTokenError as e:
    print(f"Invalid token: {e}")
```

## Multi-User Testing

Generate tokens for different users:

```bash
# User 1
python scripts/generate_jwt.py 11111111-1111-1111-1111-111111111111

# User 2
python scripts/generate_jwt.py 22222222-2222-2222-2222-222222222222
```

Each user will only be able to access their own resources. Test access control:

```bash
# User 1 creates a project
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer <USER1_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"create_project","arguments":{"name":"User 1 Project"}},"id":1}'

# User 2 tries to access User 1's project (should fail)
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer <USER2_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_project","arguments":{"project_id":"<PROJECT_ID>"}},"id":1}'
```

## Troubleshooting

### "JWT token missing 'sub' claim"

The token doesn't have a `sub` field. Regenerate with `generate_jwt.py`.

### "Invalid user_id format in JWT"

The `sub` claim is not a valid UUID. Must be format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### "JWT verification failed"

- Check that `FASTMCP_SERVER_AUTH_JWT_PUBLIC_KEY` matches the secret used to sign the token
- Check that `FASTMCP_SERVER_AUTH_JWT_ISSUER` matches the token's `iss` claim
- Check that `FASTMCP_SERVER_AUTH_JWT_AUDIENCE` matches the token's `aud` claim

### "Authentication required - missing Authorization header"

HTTP request doesn't include `Authorization: Bearer <token>` header.

### Token expired

Generate a new token with `generate_jwt.py`. Default expiry is 24 hours.

## STDIO Mode (No JWT Required)

For local development without HTTP, use STDIO mode:

```bash
# .env
FASTMCP_TRANSPORT=stdio
```

In STDIO mode:
- No JWT required
- Single user mode
- User ID is always `00000000-0000-0000-0000-000000000001`
- Perfect for Claude Desktop integration

## Security Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use strong secrets** - Minimum 32 characters for HMAC keys
3. **Rotate keys regularly** - Especially for production
4. **Use HTTPS in production** - Never send tokens over plain HTTP
5. **Set short expiration times** - 1 hour for high-security, 24 hours for convenience
6. **Use JWKS for production** - Better than shared secrets
7. **Validate all claims** - Don't skip issuer/audience checks

## Integration with Auth Providers

### Auth0

```bash
FASTMCP_SERVER_AUTH_JWT_JWKS_URI=https://YOUR_DOMAIN.auth0.com/.well-known/jwks.json
FASTMCP_SERVER_AUTH_JWT_ISSUER=https://YOUR_DOMAIN.auth0.com/
FASTMCP_SERVER_AUTH_JWT_AUDIENCE=timelines-mcp-api
```

### Keycloak

```bash
FASTMCP_SERVER_AUTH_JWT_JWKS_URI=https://keycloak.example.com/realms/YOUR_REALM/protocol/openid-connect/certs
FASTMCP_SERVER_AUTH_JWT_ISSUER=https://keycloak.example.com/realms/YOUR_REALM
FASTMCP_SERVER_AUTH_JWT_AUDIENCE=timelines-mcp-api
```

### Custom OAuth2 Provider

Any OAuth2/OIDC compliant provider works. Just need:
- JWKS endpoint URL
- Issuer URL
- Audience identifier
- Token with `sub` claim containing user UUID
