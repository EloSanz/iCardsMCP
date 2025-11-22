# Dockerfile optimizado para iCards MCP Server
FROM python:3.12-slim

# Instalar uv para gestión de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias primero (para aprovechar cache de Docker)
COPY pyproject.toml uv.lock ./

# Instalar dependencias Python
RUN uv sync --frozen --no-cache --no-dev

# Copiar código fuente
COPY server.py ./
COPY app/ ./app/
COPY docs/ ./docs/

# Variables de entorno por defecto
ENV SSE_PORT=3001
ENV API_TIMEOUT=30

# Puerto correcto para MCP
EXPOSE 3001

# Health check para verificar que el servidor responde
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001/sse || exit 1

# Comando para ejecutar el servidor MCP
CMD ["uv", "run", "python", "server.py"]

# Metadata de la imagen
LABEL maintainer="iCards Team" \
      description="MCP Server for iCards flashcard management" \
      version="1.0.0" \
      org.opencontainers.image.source="https://github.com/icards/icards-mcp"