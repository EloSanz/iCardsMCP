# 🐳 Docker Setup - iCards MCP Server

## 🚀 Inicio Rápido

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores reales

# 2. Construir e iniciar
docker-compose up -d

# 3. Verificar que funciona
curl -f http://localhost:3001/sse
```

## 📝 Variables de Entorno (.env)

```bash
# URL de tu API de iCards
API_BASE_URL=http://host.docker.internal:3000

# Timeout opcional (por defecto 30s)
API_TIMEOUT=30
```

## 🔧 Comandos Útiles

```bash
# Ver logs
docker-compose logs -f

# Ver estado
docker-compose ps

# Detener
docker-compose down

# Reconstruir desde cero
docker-compose build --no-cache
docker-compose up -d
```

## 🔍 Solución de Problemas

Si ves error `ContainerConfig`:

```bash
# Limpiar estado corrupto
docker-compose down -v --remove-orphans
docker system prune -f

# Reconstruir
docker-compose build --no-cache
docker-compose up -d
```

## 🌐 Endpoints

- **SSE**: `http://localhost:3001/sse`
- **Health Check**: `curl -f http://localhost:3001/sse`

¡Listo! 🎉
