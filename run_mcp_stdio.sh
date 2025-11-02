#!/bin/bash

# iCards MCP Server Launcher Script
# This script properly sets up the environment and runs the MCP server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting iCards MCP Server...${NC}"

# Set the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}📁 Project directory: $PROJECT_DIR${NC}"

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_DIR"
echo -e "${YELLOW}🐍 PYTHONPATH set to: $PYTHONPATH${NC}"

# Optional environment variables (can be overridden)
export SCOPE="${SCOPE:-local}"
export API_BASE_URL="${API_BASE_URL:-http://localhost:3000}"
export API_TIMEOUT="${API_TIMEOUT:-30}"

echo -e "${YELLOW}⚙️  Environment:${NC}"
echo -e "   SCOPE: $SCOPE"
echo -e "   API_BASE_URL: $API_BASE_URL"
echo -e "   API_TIMEOUT: $API_TIMEOUT"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ Error: uv is not installed or not in PATH${NC}" >&2
    exit 1
fi

echo -e "${GREEN}🔧 Using uv to run the MCP server...${NC}"

# Change to project directory
cd "$PROJECT_DIR"

# Run the MCP server with uv
exec uv run python server.py
