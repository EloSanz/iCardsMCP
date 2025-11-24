#!/bin/bash

# 🚀 iCards MCP Server - Script de Docker
# Uso: ./docker-run.sh [comando]

set -e

# 🎨 Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 📍 Directorio del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 🔧 Función para imprimir mensajes coloreados
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 🏗️ Función para construir la imagen
build() {
    print_info "Construyendo imagen Docker icards-mcp..."
    docker-compose build --no-cache
    print_success "Imagen construida exitosamente"
}

# 🚀 Función para iniciar servicios
up() {
    print_info "Iniciando servicios con Docker Compose..."
    docker-compose up -d
    print_success "Servicios iniciados"

    # 🏥 Esperar a que el health check pase
    print_info "Esperando a que el servicio esté saludable..."
    sleep 10

    # 🔍 Verificar estado
    if docker-compose ps | grep -q "healthy"; then
        print_success "Servicio saludable en http://localhost:3001"
        print_info "📡 SSE endpoint: http://localhost:3001/sse"
        print_info "🔍 Health check: curl -f http://localhost:3001/sse"
    else
        print_warning "Servicio puede estar iniciándose..."
        print_info "Ver logs: docker-compose logs -f"
    fi
}

# 🛑 Función para detener servicios
down() {
    print_info "Deteniendo servicios..."
    docker-compose down
    print_success "Servicios detenidos"
}

# 📜 Función para ver logs
logs() {
    print_info "Mostrando logs del servicio..."
    docker-compose logs -f
}

# 🔍 Función para verificar estado
status() {
    print_info "Estado de los servicios:"
    docker-compose ps

    print_info "Estado de health checks:"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

# 🧹 Función para limpiar
clean() {
    print_warning "Limpiando contenedores, imágenes y volúmenes..."
    docker-compose down -v --rmi all
    docker system prune -f
    print_success "Limpieza completada"
}

# 🔄 Función para reiniciar
restart() {
    down
    sleep 2
    up
}

# 📋 Función para mostrar ayuda
help() {
    echo "🚀 iCards MCP Server - Gestión Docker"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  build     Construir imagen Docker"
    echo "  up        Iniciar servicios"
    echo "  down      Detener servicios"
    echo "  restart   Reiniciar servicios"
    echo "  logs      Ver logs en tiempo real"
    echo "  status    Ver estado de servicios"
    echo "  clean     Limpiar contenedores e imágenes"
    echo "  help      Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 build    # Construir imagen"
    echo "  $0 up       # Iniciar servicios"
    echo "  $0 logs     # Ver logs"
    echo ""
    echo "Variables de entorno requeridas en .env:"
    echo "  API_BASE_URL=http://host.docker.internal:3000"
    echo "  AUTH_TOKEN=tu_token_jwt_aqui"
}

# 🎯 Lógica principal del script
cd "$PROJECT_DIR"

case "${1:-help}" in
    build)
        build
        ;;
    up)
        up
        ;;
    down)
        down
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    help|*)
        help
        ;;
esac
