#!/usr/bin/env python3
"""
Generate a JWT token for testing the Timelines MCP server.

Usage:
    python scripts/generate_jwt.py <user_id>
    python scripts/generate_jwt.py 550e8400-e29b-41d4-a716-446655440000
"""

import sys
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt


def generate_token(
    user_id: str | UUID,
    secret_key: str = "your-secret-key-minimum-32-characters-long",
    algorithm: str = "HS256",
    issuer: str = "timelines-mcp-local",
    audience: str = "timelines-mcp-api",
    expires_in_hours: int = 24,
) -> str:
    """
    Generate a JWT token for testing.
    
    Args:
        user_id: User UUID (will be the 'sub' claim)
        secret_key: Secret key for signing (must match server config)
        algorithm: JWT algorithm (HS256, HS384, HS512)
        issuer: Token issuer (must match server config)
        audience: Token audience (must match server config)
        expires_in_hours: Token validity in hours
        
    Returns:
        JWT token string
    """
    # Validate UUID
    if isinstance(user_id, str):
        try:
            user_id = UUID(user_id)
        except ValueError as e:
            raise ValueError(f"Invalid UUID format: {user_id}") from e
    
    now = datetime.now(UTC)
    
    payload = {
        "sub": str(user_id),  # User ID - MUST be valid UUID
        "iss": issuer,        # Issuer - who created the token
        "aud": audience,      # Audience - who the token is for
        "iat": now,           # Issued at
        "exp": now + timedelta(hours=expires_in_hours),  # Expiration
        "name": f"Test User {user_id}",  # Optional: user display name
        "email": f"user-{user_id}@example.com",  # Optional: email
    }
    
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_jwt.py <user_id>")
        print("Example: python scripts/generate_jwt.py 550e8400-e29b-41d4-a716-446655440000")
        print("\nGenerating token with random UUID...")
        user_id = uuid4()
    else:
        user_id = sys.argv[1]
    
    try:
        token = generate_token(user_id)
        
        print("\n" + "=" * 80)
        print("JWT Token Generated Successfully")
        print("=" * 80)
        print(f"\nUser ID: {user_id}")
        print(f"\nToken:\n{token}")
        print(f"\nAuthorization Header:")
        print(f"Authorization: Bearer {token}")
        print("\n" + "=" * 80)
        print("\nTo use with curl:")
        print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/mcp')
        print("\nTo decode and verify (without checking signature):")
        print(f"python -c \"import jwt; print(jwt.decode('{token}', options={{'verify_signature': False}}))\"\n")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
