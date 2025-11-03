#!/bin/bash

# iCards MCP Server Launcher Script
# This script properly sets up the environment and runs the MCP server
# Environment variables can be passed from Claude Desktop MCP config

set -e  # Exit on any error

# CRITICAL: All output must go to stderr to avoid breaking MCP JSON protocol on stdout
# MCP uses stdout for JSON-RPC communication, any extra output breaks it

# Set the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_DIR"

# === Environment Configuration ===
# Priority: 1) Claude Desktop env vars, 2) .env.local file, 3) defaults

# Set defaults
export SCOPE="${SCOPE:-local}"
export API_BASE_URL="${API_BASE_URL:-http://localhost:3000}"
export API_TIMEOUT="${API_TIMEOUT:-30}"

# For AUTH_TOKEN, we need special handling:
# If not passed via env, try to load from .env.local
if [ -z "$AUTH_TOKEN" ]; then
    # Try to load from .env.local
    if [ -f "$PROJECT_DIR/.env.local" ]; then
        # Extract AUTH_TOKEN from .env.local
        if grep -q "^AUTH_TOKEN=" "$PROJECT_DIR/.env.local"; then
            AUTH_TOKEN=$(grep "^AUTH_TOKEN=" "$PROJECT_DIR/.env.local" | cut -d'=' -f2-)
            export AUTH_TOKEN
        fi
    fi
fi

# Also check .env file as fallback
if [ -z "$AUTH_TOKEN" ] && [ -f "$PROJECT_DIR/.env" ]; then
    if grep -q "^AUTH_TOKEN=" "$PROJECT_DIR/.env"; then
        AUTH_TOKEN=$(grep "^AUTH_TOKEN=" "$PROJECT_DIR/.env" | cut -d'=' -f2-)
        export AUTH_TOKEN
    fi
fi

# Only log errors to stderr
if [ -z "$AUTH_TOKEN" ]; then
    echo "❌ AUTH_TOKEN not configured" >&2
    echo "💡 Set AUTH_TOKEN in .env.local or Claude Desktop config" >&2
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed or not in PATH" >&2
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Run the MCP server with uv
# All environment variables are already exported above
# stdout is used for MCP JSON-RPC communication only
exec uv run python server.py
