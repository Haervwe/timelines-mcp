"""
Authentication and User Context Management

Provides utilities for extracting user identity from JWT tokens (HTTP mode)
or using a default single-user identity (STDIO mode).
"""

from uuid import UUID

import jwt
from fastmcp.server.dependencies import get_access_token, get_http_headers


def get_user_id() -> UUID:
    """
    Extract user ID from JWT token (HTTP) or use default (STDIO).

    For HTTP: Validates JWT token and extracts 'sub' claim as user_id
    For STDIO: Returns a default single-user UUID

    Returns:
        UUID: User identifier

    Raises:
        ValueError: If JWT token is invalid or missing required claims
    """
    # Check if we have an access token (HTTP mode)
    access_token = get_access_token()

    if access_token is not None:
        # HTTP mode - extract user_id from JWT claims
        claims = access_token.claims
        if not claims or "sub" not in claims:
            raise ValueError("JWT token missing 'sub' claim")

        user_id_str = claims["sub"]
        try:
            return UUID(user_id_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid user_id format in JWT: {user_id_str}") from e

    # Check for headers (HTTP mode without proper auth setup)
    headers = get_http_headers()
    if headers:
        # HTTP mode detected but no proper JWT - reject
        auth_header = headers.get("authorization", "")
        if auth_header:
            # Try to decode JWT manually for better error messages
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    # Decode without verification for error reporting
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    if "sub" not in decoded:
                        raise ValueError("JWT token missing 'sub' claim")
                    raise ValueError("JWT verification failed - check server configuration")
                except jwt.DecodeError as e:
                    raise ValueError("Invalid JWT token format") from e
        raise ValueError("Authentication required - missing Authorization header")

    # STDIO mode - use single-user default
    # This UUID is deterministic for single-user local usage
    return UUID("00000000-0000-0000-0000-000000000001")
