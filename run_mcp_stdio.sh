#!/bin/bash

# iCards MCP Server Launcher Script
# This script properly sets up the environment and runs the MCP server
# Environment variables can be passed from Claude Desktop MCP config

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting iCards MCP Server...${NC}"

# Set the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}📁 Project directory: $PROJECT_DIR${NC}"

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_DIR"
echo -e "${YELLOW}🐍 PYTHONPATH set to: $PYTHONPATH${NC}"

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
            echo -e "${YELLOW}📄 Loaded AUTH_TOKEN from .env.local${NC}"
        fi
    fi
fi

# Also check .env file as fallback
if [ -z "$AUTH_TOKEN" ] && [ -f "$PROJECT_DIR/.env" ]; then
    if grep -q "^AUTH_TOKEN=" "$PROJECT_DIR/.env"; then
        AUTH_TOKEN=$(grep "^AUTH_TOKEN=" "$PROJECT_DIR/.env" | cut -d'=' -f2-)
        export AUTH_TOKEN
        echo -e "${YELLOW}📄 Loaded AUTH_TOKEN from .env${NC}"
    fi
fi

echo -e "${YELLOW}⚙️  Environment Configuration:${NC}"
echo -e "   SCOPE: ${CYAN}$SCOPE${NC}"
echo -e "   API_BASE_URL: ${CYAN}$API_BASE_URL${NC}"
echo -e "   API_TIMEOUT: ${CYAN}$API_TIMEOUT${NC}"

if [ -n "$AUTH_TOKEN" ]; then
    # Mask token for display
    TOKEN_MASKED="${AUTH_TOKEN:0:8}..."
    echo -e "   AUTH_TOKEN: ${GREEN}configured${NC} (${TOKEN_MASKED}, ${#AUTH_TOKEN} chars total)"
else
    echo -e "   AUTH_TOKEN: ${RED}not configured${NC}"
    echo -e "${YELLOW}   💡 Set AUTH_TOKEN in one of these ways:${NC}"
    echo -e "      1. Claude Desktop config: add to 'env' object"
    echo -e "      2. Create .env.local file with AUTH_TOKEN=your_token"
    echo -e "      3. Export as shell variable: export AUTH_TOKEN=your_token${NC}"
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ Error: uv is not installed or not in PATH${NC}" >&2
    exit 1
fi

echo -e "${GREEN}🔧 Using uv to run the MCP server...${NC}"

# Change to project directory
cd "$PROJECT_DIR"

# Run the MCP server with uv
# All environment variables are already exported above
exec uv run python server.py
