# Dockerfile optimizado para iCards MCP Server
FROM python:3.12-slim

# Instalar uv para gestión de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Sin dependencias del sistema adicionales - Python puro

# Copiar archivos de dependencias primero (para aprovechar cache de Docker)
COPY pyproject.toml uv.lock ./

# Instalar dependencias Python (más rápido)
RUN uv sync --no-dev

# Copiar código fuente
COPY server.py ./
COPY app/ ./app/
COPY docs/ ./docs/

# Variables de entorno por defecto
ENV SSE_PORT=3001
ENV API_TIMEOUT=30
ENV API_BASE_URL=http://host.docker.internal:3000
# AUTH_TOKEN se configura via variable de entorno del contenedor
ENV PYTHONUNBUFFERED=1

# Puerto correcto para MCP
EXPOSE 3001

# Sin health check por simplicidad

# Comando para ejecutar el servidor MCP
CMD ["uv", "run", "python", "server.py"]

# Metadata de la imagen
LABEL maintainer="iCards Team" \
      description="MCP Server for iCards flashcard management" \
      version="1.0.0" \
      org.opencontainers.image.source="https://github.com/icards/icards-mcp"