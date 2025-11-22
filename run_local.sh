#!/bin/bash
# Script para ejecutar el servidor MCP localmente en modo SSE

echo "🎴 Iniciando iCards MCP Server - Modo Desarrollo Local"
echo "======================================================"

# Variables para desarrollo local
export AUTH_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImlhdCI6MTc2MzgxMzAxOSwiZXhwIjoxNzYzODk5NDE5fQ.D9CF1aHARW7euPeZdG6ywqmDMw9ocwsUt-NO7H8wb-A"
export LOCAL_API_BASE_URL="http://localhost:3000"
export SSE_PORT=3001

# Para producción, configura:
# export AUTH_TOKEN="tu_token_produccion"
# export LOCAL_API_BASE_URL="https://tu-backend-api.com"
# export SSE_PORT=3001

echo "🔧 Configuración:"
echo "   • API Local: $LOCAL_API_BASE_URL"
echo "   • Puerto SSE: $SSE_PORT"
echo "   • Token: ${AUTH_TOKEN:0:20}..."
echo ""
echo "🌐 Endpoints disponibles:"
echo "   • SSE: http://localhost:$SSE_PORT/sse"
echo "   • Health: curl http://localhost:$SSE_PORT/health"
echo ""
echo "🎯 Conecta Cursor usando la configuración .cursor/mcp.json"
echo "   Las peticiones aparecerán en estos logs."
echo ""
echo "🚀 Iniciando servidor..."
echo ""

# Ejecutar el servidor
uv run python server.py
