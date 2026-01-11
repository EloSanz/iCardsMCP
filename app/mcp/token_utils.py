"""Token utilities for MCP authentication."""
import logging
import os

# Per-connection token storage (connection_id -> token)
connection_tokens = {}

def get_auth_token_for_connection(connection_id: str = None):
    """Get auth token for specific connection or from env var."""
    # First try environment variable (for development/testing)
    token = os.getenv("AUTH_TOKEN")
    if token:
        return token

    # Then try connection-specific token
    if connection_id and connection_id in connection_tokens:
        token = connection_tokens[connection_id]
        if token:
            logging.debug(f"🔄 Using connection token for {connection_id} ({len(token)} chars)")
            return token

    return None

def set_auth_token_for_connection(connection_id: str, token: str):
    """Store auth token for specific connection."""
    if connection_id:
        connection_tokens[connection_id] = token
        logging.info(f"✅ Auth token stored for connection {connection_id} ({len(token)} chars)")
        # Clean up old connections (keep only last 10 to prevent memory leaks)
        if len(connection_tokens) > 10:
            oldest_key = next(iter(connection_tokens))
            del connection_tokens[oldest_key]
            logging.debug(f"🧹 Cleaned up old connection token for {oldest_key}")

def set_current_auth_token(token: str):
    """Set the auth token in the current context and global fallback."""
    from app.services.base_service import set_current_auth_token as base_set_token
    # We could check if it changed, but simpler to just reduce log level to DEBUG
    # as this is called on every request by the middleware
    base_set_token(token)
    logging.debug(f"🔑 Token set globally via base_service ({len(token)} chars)")

def get_auth_token():
    """Environment fallback removed - this always returns None or needs refactor."""
    # We removed global env fallback, so this helper is likely obsolete or should return None
    return None
