#!/bin/bash
# 🚀 Script de configuración para producción
# Ejecutar en tu VPS después de clonar el repositorio

echo "🚀 Configuración de Producción - iCards MCP Server"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar si estamos en Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}❌ Este script es para Linux (VPS)${NC}"
    exit 1
fi

# Verificar si docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}📦 Instalando Docker...${NC}"
    sudo apt update
    sudo apt install -y docker.io docker-compose
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker instalado${NC}"
fi

# Verificar si .env.production.local existe
if [ ! -f ".env.production.local" ]; then
    echo -e "${YELLOW}📋 Creando archivo de configuración...${NC}"
    cp .env.production.local .env.production.local
    echo -e "${YELLOW}⚠️  Por favor, edita .env.production.local con tus credenciales reales${NC}"
    echo -e "${YELLOW}   nano .env.production.local${NC}"
    exit 1
fi

# Verificar que las variables estén configuradas
source .env.production.local
if [ -z "$AUTH_TOKEN" ] || [ "$AUTH_TOKEN" = "tu_token_jwt_real_aqui" ]; then
    echo -e "${RED}❌ AUTH_TOKEN no configurado en .env.production.local${NC}"
    echo -e "${YELLOW}💡 Edita el archivo: nano .env.production.local${NC}"
    exit 1
fi

if [ -z "$API_BASE_URL" ] || [ "$API_BASE_URL" = "https://tu-backend-api.com" ]; then
    echo -e "${RED}❌ API_BASE_URL no configurado en .env.production.local${NC}"
    echo -e "${YELLOW}💡 Edita el archivo: nano .env.production.local${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuración validada${NC}"

# Construir y ejecutar
echo -e "${YELLOW}🏗️  Construyendo imagen Docker...${NC}"
docker-compose build

echo -e "${YELLOW}🚀 Iniciando servicios...${NC}"
docker-compose up -d

echo -e "${YELLOW}⏳ Esperando que inicie...${NC}"
sleep 5

# Verificar que esté funcionando
if curl -f http://localhost:3001/sse &>/dev/null; then
    echo -e "${GREEN}✅ ¡Servidor MCP funcionando correctamente!${NC}"
    echo -e "${GREEN}🌐 URL del servidor: http://tu-vps-ip:3001/sse${NC}"
    echo ""
    echo -e "${YELLOW}📋 Configura tu Cursor con:${NC}"
    echo '{'
    echo '  "icards": {'
    echo '    "url": "http://tu-vps-ip:3001/sse",'
    echo '    "transport": "sse",'
    echo '    "env": {'
    echo '      "AUTH_TOKEN": "tu_token_produccion",'
    echo '      "LOCAL_API_BASE_URL": "https://tu-backend-api.com"'
    echo '    }'
    echo '  }'
    echo '}'
else
    echo -e "${RED}❌ Error: El servidor no responde${NC}"
    echo -e "${YELLOW}📋 Verifica logs: docker-compose logs${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 ¡Deploy completado exitosamente!${NC}"
