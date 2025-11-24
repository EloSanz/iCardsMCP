# 🐳 Dockerfile Optimizado para iCards MCP Server
# Usa Python 3.12 slim para imagen más pequeña
FROM python:3.12-slim

# 📦 Instalar uv para gestión ultra-rápida de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# 🏠 Establecer directorio de trabajo
WORKDIR /app

# 🔧 Instalar curl para health checks (requerido por docker-compose)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 📋 Copiar archivos de dependencias primero (optimiza cache de Docker)
COPY pyproject.toml uv.lock ./

# ⚡ Instalar dependencias Python usando uv (más rápido que pip)
RUN uv sync --frozen --no-install-project --no-dev

# 📁 Copiar código fuente
COPY server.py ./
COPY app/ ./app/
COPY docs/ ./docs/

# 🔧 Variables de entorno por defecto
ENV SSE_PORT=3001
ENV API_TIMEOUT=30
ENV API_BASE_URL=http://host.docker.internal:3000
ENV PYTHONUNBUFFERED=1
# AUTH_TOKEN se configura via headers HTTP del cliente MCP

# 🚪 Exponer puerto del servidor MCP
EXPOSE 3001

# 🏥 Health check integrado
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3001/sse || exit 1

# 🚀 Comando para ejecutar el servidor MCP
CMD ["uv", "run", "python", "server.py"]

# 🏷️ Metadata de la imagen
LABEL maintainer="iCards Team" \
      description="MCP Server for iCards flashcard management" \
      version="1.0.0" \
      org.opencontainers.image.source="https://github.com/icards/icards-mcp" \
      org.opencontainers.image.licenses="MIT"