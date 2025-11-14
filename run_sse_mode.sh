#!/bin/bash
# Script para correr iCards MCP en modo SSE (con logs visibles)

echo "🚀 Starting iCards MCP Server in SSE mode..."
echo "📊 You'll see all logs in this terminal"
echo "🔗 Server will be available at: http://localhost:3001"
echo ""
echo "📝 To use this mode:"
echo "   1. Keep this terminal open"
echo "   2. Copy claude_desktop_config_sse.json to your Claude Desktop config"
echo "   3. Restart Claude Desktop"
echo ""

cd "$(dirname "$0")"

# Export environment variables
export SCOPE=local
export API_BASE_URL=http://localhost:3000
export API_TIMEOUT=30
export AUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjIsImlhdCI6MTc2MjU1MzQxOSwiZXhwIjoxNzYyNjM5ODE5fQ.pw3TGRHDc_MiEIoW5RVxPfGfOuYjL_UOLQ3SNMajcTM

# Run in SSE mode
SSE_PORT=3001 uv run python server.py

