# Quick Start: JWT Authentication on Localhost

Run the timelines-mcp server on localhost with JWT authentication.

## 🚀 One-Command Setup

```bash
./scripts/setup_jwt_localhost.sh
```

This will:
1. Create `.env` file with JWT configuration
2. Configure HTTP server on `127.0.0.1:8000`
3. Generate a test JWT token for you
4. Show you how to test it

## 📝 Manual Setup

If you prefer to set it up manually:

### 1. Copy the example environment file

```bash
cp .env.example .env
```

### 2. Edit `.env` to enable HTTP mode with JWT

```bash
# Server Transport
FASTMCP_TRANSPORT=http
FASTMCP_HOST=127.0.0.1
FASTMCP_PORT=8000

# JWT Authentication (symmetric key)
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.jwt.JWTVerifier
FASTMCP_SERVER_AUTH_JWT_PUBLIC_KEY=your-secret-key-minimum-32-characters-long
FASTMCP_SERVER_AUTH_JWT_ALGORITHM=HS256
FASTMCP_SERVER_AUTH_JWT_ISSUER=timelines-mcp-local
FASTMCP_SERVER_AUTH_JWT_AUDIENCE=timelines-mcp-api
```

### 3. Generate a JWT token

```bash
uv run python scripts/generate_jwt.py 550e8400-e29b-41d4-a716-446655440000
```

### 4. Start the server

```bash
uv run python -m timelines_mcp
```

### 5. Test with curl

```bash
# Replace <TOKEN> with the generated token
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## 🔧 Testing Multiple Users

Generate tokens for different users:

```bash
# User 1
uv run python scripts/generate_jwt.py 11111111-1111-1111-1111-111111111111

# User 2  
uv run python scripts/generate_jwt.py 22222222-2222-2222-2222-222222222222
```

Each user will only see their own projects and timelines.

## 📚 Full Documentation

For detailed information about:
- JWT token requirements
- Production configuration with JWKS
- Troubleshooting
- Security best practices

See **[docs/JWT_SETUP.md](../docs/JWT_SETUP.md)**

## 🔄 Switching Back to STDIO Mode

To run without JWT (single-user mode):

```bash
# Edit .env
FASTMCP_TRANSPORT=stdio

# Or just run without .env
rm .env
uv run python -m timelines_mcp
```

## ⚠️ Important Security Notes

1. **Never commit `.env`** - It's in `.gitignore` already
2. **Change the secret key** - The example key is NOT secure
3. **Use HTTPS in production** - Never send tokens over plain HTTP
4. **Token expires in 24 hours** - Regenerate when needed

## 🆘 Troubleshooting

### "Authentication required - missing Authorization header"

You forgot to include the JWT token:

```bash
curl -H "Authorization: Bearer <YOUR_TOKEN>" http://127.0.0.1:8000/mcp ...
```

### "JWT token missing 'sub' claim"

The token is invalid. Regenerate with `scripts/generate_jwt.py`.

### "Invalid user_id format in JWT"

The `sub` claim must be a valid UUID format.

### "JWT verification failed"

The server's JWT secret doesn't match the one used to sign the token. Check that `FASTMCP_SERVER_AUTH_JWT_PUBLIC_KEY` in `.env` matches the secret in `generate_jwt.py`.

### Port already in use

Change the port in `.env`:

```bash
FASTMCP_PORT=8001
```
