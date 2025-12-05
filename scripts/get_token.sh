#!/bin/bash
# User identity file - keeps track of your user ID
# This file should be kept safe - it's your identity in the system

USER_ID_FILE="$HOME/.timelines_mcp_user_id"

# Create or read user ID
if [ -f "$USER_ID_FILE" ]; then
    USER_ID=$(cat "$USER_ID_FILE")
    echo "📋 Your user ID: $USER_ID"
else
    # Generate new user ID
    USER_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
    echo "$USER_ID" > "$USER_ID_FILE"
    chmod 600 "$USER_ID_FILE"
    echo "🆕 New user ID created: $USER_ID"
    echo "   Saved to: $USER_ID_FILE"
fi

echo
echo "Generating fresh JWT token (valid 24 hours)..."
cd "$(dirname "$0")/.." || exit 1
uv run python scripts/generate_jwt.py "$USER_ID"
