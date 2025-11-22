# 🚀 Deploy con Docker - iCards MCP Server

## 📋 Requisitos Previos

- Docker y Docker Compose instalados
- Token JWT válido de iCards API
- Acceso a la API de iCards

## 🏗️ Construcción de la Imagen

### Opción 1: Build Local
```bash
# Construir imagen
docker build -t icards-mcp .

# Verificar imagen
docker images icards-mcp
```

### Opción 2: Usar Docker Compose
```bash
# Construir con compose
docker-compose build

# Ver imágenes
docker-compose images
```

## 🚀 Despliegue en Producción

### Variables de Entorno Requeridas

Crear archivo `.env`:
```bash
# Autenticación (OBLIGATORIO)
AUTH_TOKEN=tu_jwt_token_real_aqui

# API Configuration (OBLIGATORIO)
API_BASE_URL=https://tu-api.icards.com
API_TIMEOUT=30

# Server Configuration
SSE_PORT=3001
```

### Opción A: Docker Compose (Recomendado)

```bash
# Variables requeridas (sin SCOPE)
export AUTH_TOKEN=tu_token_real
export API_BASE_URL=https://tu-api.com

# Levantar servicio
docker-compose up -d

# Ver logs
docker-compose logs -f icards-mcp

# Ver estado
docker-compose ps
```

### Opción B: Docker Directo

```bash
# Ejecutar contenedor
docker run -d \
  --name icards-mcp-prod \
  -p 3001:3001 \
  --env-file .env.prod \
  --restart unless-stopped \
  icards-mcp

# Ver logs
docker logs -f icards-mcp-prod

# Health check manual
curl -f http://localhost:3001/sse
```

## 🔍 Verificación del Deploy

### 1. Health Check Automático
```bash
docker ps
# Debería mostrar: (healthy) en STATUS
```

### 2. Health Check Manual
```bash
curl -f http://localhost:3001/sse
# Debería devolver un stream SSE
```

### 3. Prueba MCP (usando session_id del SSE)
```bash
# 1. Obtener session_id
curl -N http://localhost:3001/sse | head -2

# 2. Inicializar MCP
curl -X POST "http://localhost:3001/messages?session_id=SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test", "version": "1.0.0"}}}'

# 3. Listar tools
curl -X POST "http://localhost:3001/messages?session_id=SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'
```

## 📊 Monitoreo y Logs

### Ver Logs en Tiempo Real
```bash
# Docker Compose
docker-compose logs -f

# Docker directo
docker logs -f icards-mcp-prod
```

### Logs de Health Checks
```bash
# Ver eventos de health check
docker events --filter event=health_status
```

### Métricas del Contenedor
```bash
# Estadísticas de uso
docker stats icards-mcp-prod

# Información detallada
docker inspect icards-mcp-prod
```

## 🔧 Troubleshooting

### Problema: Health Check Failing
```bash
# Ver logs detallados
docker logs icards-mcp-prod

# Verificar conectividad
docker exec icards-mcp-prod curl -f http://localhost:3001/sse
```

### Problema: API Connection Failed
```
❌ Cannot connect to API server
💡 Make sure iCards API is running on: http://host.docker.internal:3000
```

**Solución:**
- Verificar que `API_BASE_URL` sea correcto
- Verificar que `AUTH_TOKEN` sea válido
- Verificar conectividad de red

### Problema: Puerto Ya en Uso
```bash
# Cambiar puerto de exposición
docker run -p 3002:3001 icards-mcp
```

## 🏭 Deploy en VPS (Hostinger)

### 1. Preparar VPS
```bash
# En tu VPS
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

### 2. Subir Código
```bash
# Subir archivos al VPS
scp -r . user@vps:/path/to/icards-mcp/
```

### 3. Configurar Variables
```bash
# En el VPS
cd /path/to/icards-mcp
echo "AUTH_TOKEN=tu_token_real" > .env.prod
echo "API_BASE_URL=https://tu-api.com" >> .env.prod
```

### 4. Deploy
```bash
docker-compose up -d
```

### 5. Configurar Reverse Proxy (Nginx)
```nginx
# /etc/nginx/sites-available/icards-mcp
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🎯 Configuración Claude Desktop

Una vez desplegado, configura Claude Desktop:

```json
{
  "mcpServers": {
    "icards": {
      "url": "https://tu-dominio.com/sse",
      "transport": "sse",
      "env": {
        "AUTH_TOKEN": "tu_token_aqui",
        "API_BASE_URL": "https://tu-api.com"
      }
    }
  }
}
```

## 📈 Optimizaciones de Producción

### Health Checks Avanzados
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:3001/sse && echo 'OK'"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### Logging Centralizado
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Recursos Limitados
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

¡Tu servidor MCP está listo para producción! 🚀
