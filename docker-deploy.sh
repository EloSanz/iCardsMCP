#!/bin/bash

# 🚀 iCards MCP Server - Deploy en VPS
# Uso: ./docker-deploy.sh [comando]

set -e

# 🎨 Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 🔍 Verificar prerrequisitos
check_prerequisites() {
    print_info "Verificando prerrequisitos..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado"
        exit 1
    fi

    if [ ! -f ".env" ]; then
        print_error "Archivo .env no encontrado. Copia .env.example y configúralo"
        exit 1
    fi

    print_success "Prerrequisitos OK"
}

# 🧹 Limpiar estado corrupto
clean_corrupted() {
    print_warning "Limpiando estado corrupto de Docker..."

    # Detener todo
    docker-compose down -v --remove-orphans 2>/dev/null || true

    # Remover contenedores con problemas
    docker container prune -f

    # Remover imágenes problemáticas
    docker images | grep icards-mcp | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

    # Limpiar sistema
    docker system prune -f

    print_success "Estado corrupto limpiado"
}

# 🏗️ Construir imagen desde cero
build_fresh() {
    print_info "Construyendo imagen desde cero..."
    docker-compose build --no-cache --pull
    print_success "Imagen construida"
}

# 🚀 Deploy completo
deploy() {
    check_prerequisites

    print_info "🚀 Iniciando deploy completo de iCards MCP Server..."

    # Limpiar estado anterior
    clean_corrupted

    # Construir imagen fresca
    build_fresh

    # Iniciar servicios
    print_info "Iniciando servicios..."
    docker-compose up -d

    # Esperar health check
    print_info "Esperando que el servicio esté saludable..."
    sleep 15

    # Verificar estado
    if docker-compose ps | grep -q "healthy\|running"; then
        print_success "🎉 Deploy exitoso!"
        print_info "🌐 Servicio disponible en:"
        print_info "   SSE: http://localhost:3001/sse"
        print_info "   Health: curl -f http://localhost:3001/sse"
        print_info ""
        print_info "📊 Ver logs: docker-compose logs -f"
        print_info "🛑 Detener: docker-compose down"
    else
        print_error "❌ El servicio no está saludable"
        print_info "Ver logs: docker-compose logs -f"
        exit 1
    fi
}

# 🔍 Status del servicio
status() {
    print_info "📊 Estado del servicio:"
    docker-compose ps

    print_info "🔍 Health checks:"
    docker stats --no-stream icards-mcp-server 2>/dev/null || echo "Servicio no corriendo"

    print_info "📜 Últimos logs:"
    docker-compose logs --tail=10
}

# 📜 Logs en tiempo real
logs() {
    print_info "📜 Mostrando logs en tiempo real (Ctrl+C para salir)..."
    docker-compose logs -f
}

# 🛑 Detener servicios
stop() {
    print_info "🛑 Deteniendo servicios..."
    docker-compose down
    print_success "Servicios detenidos"
}

# 🔄 Reiniciar
restart() {
    stop
    sleep 3
    deploy
}

# 🆘 Función de rescate para errores de ContainerConfig
rescue() {
    print_warning "🆘 Modo rescate activado - Solucionando error 'ContainerConfig'..."

    # Paso 1: Detener todo forzosamente
    print_info "Paso 1: Deteniendo todo forzosamente..."
    docker-compose down -v --remove-orphans 2>/dev/null || true
    docker stop $(docker ps -aq) 2>/dev/null || true
    docker rm -f $(docker ps -aq) 2>/dev/null || true

    # Paso 2: Limpiar imágenes e imágenes dangling
    print_info "Paso 2: Limpiando imágenes problemáticas..."
    docker rmi -f $(docker images -q) 2>/dev/null || true
    docker image prune -f
    docker system prune -f

    # Paso 3: Recrear redes
    print_info "Paso 3: Recreando redes..."
    docker network prune -f

    print_success "🆘 Modo rescate completado. Ahora intenta: ./docker-deploy.sh deploy"
}

# 📋 Función de ayuda
help() {
    echo "🚀 iCards MCP Server - Deploy en VPS"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  deploy     Deploy completo (limpia, construye e inicia)"
    echo "  build      Construir imagen Docker"
    echo "  up         Iniciar servicios"
    echo "  down       Detener servicios"
    echo "  restart    Reiniciar servicios"
    echo "  status     Ver estado del servicio"
    echo "  logs       Ver logs en tiempo real"
    echo "  clean      Limpiar estado corrupto"
    echo "  rescue     Modo rescate para error 'ContainerConfig'"
    echo "  help       Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 deploy     # Deploy completo"
    echo "  $0 status     # Ver estado"
    echo "  $0 logs       # Ver logs"
    echo "  $0 rescue     # Si hay error ContainerConfig"
    echo ""
    echo "Variables requeridas en .env:"
    echo "  API_BASE_URL=https://tu-api.com"
    echo "  AUTH_TOKEN=tu_token_jwt"
}

# 🎯 Lógica principal
case "${1:-help}" in
    deploy)
        deploy
        ;;
    build)
        check_prerequisites
        build_fresh
        ;;
    up)
        check_prerequisites
        docker-compose up -d
        ;;
    down)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    clean)
        clean_corrupted
        ;;
    rescue)
        rescue
        ;;
    help|*)
        help
        ;;
esac
