# Configuración del Proyecto iCards MCP

Este documento describe la configuración del proyecto usando **uv** y **FastMCP**.

## 📦 Gestión de Dependencias con uv

El proyecto usa [uv](https://docs.astral.sh/uv/) como gestor de dependencias, siguiendo las [recomendaciones oficiales de FastMCP](https://gofastmcp.com/getting-started/installation).

### ¿Por qué uv?

- ⚡ **Rápido:** Instalación y resolución de dependencias ultra-rápida
- 🐍 **Gestión de Python:** Maneja múltiples versiones de Python
- 📦 **Compatible:** Usa `pyproject.toml` estándar
- 🔒 **Lockfile:** `uv.lock` asegura builds reproducibles
- 🎯 **Recomendado por FastMCP:** FastMCP recomienda oficialmente usar uv

### Instalación de uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Con pip
pip install uv
```

## 🚀 Comandos Principales

### Instalación inicial

```bash
# Instalar dependencias de producción
uv sync

# Instalar incluyendo dependencias de desarrollo
uv sync --dev
```

### Ejecutar el servidor

```bash
# Ejecutar servidor MCP
uv run python server.py

# Ejecutar tests
uv run python test_server.py
```

### Agregar nuevas dependencias

```bash
# Agregar dependencia de producción (pinned version)
uv add package==1.0.0

# Agregar dependencia de desarrollo
uv add --dev pytest

# Remover dependencia
uv remove package
```

### Actualizar dependencias

```bash
# Actualizar todas las dependencias
uv sync --upgrade

# Actualizar dependencia específica
uv add package --upgrade
```

## 📋 Estructura de pyproject.toml

```toml
[project]
name = "icardsmcp"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    "fastmcp==2.11.3",      # Versión pinned (recomendado por FastMCP)
    "httpx>=0.28.1",         # Cliente HTTP asíncrono
    "python-dotenv>=1.2.1",  # Variables de entorno
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.8.0",
]
```

## 🔒 Política de Versiones

Siguiendo las [recomendaciones de FastMCP](https://gofastmcp.com/getting-started/installation#versioning-policy):

### ✅ Buenas prácticas

```toml
fastmcp==2.11.3  # ✓ Versión exacta pinned (RECOMENDADO)
httpx>=0.28.1    # ✓ Para librerías estables
```

### ❌ Evitar en producción

```toml
fastmcp>=2.11.0  # ✗ Puede instalar breaking changes
fastmcp~=2.11    # ✗ Puede actualizar minor versions con cambios
```

**Razón:** FastMCP sigue semantic versioning pragmático. Los cambios breaking pueden ocurrir en minor versions (ej: 2.3.x → 2.4.0) para mantenerse actualizado con el protocolo MCP.

## 🔄 Verificar instalación

```bash
# Verificar versión de FastMCP
uv run fastmcp version
```

Salida esperada:

```
FastMCP version:                           2.11.3
MCP version:                               1.20.0
Python version:                            3.13.3
Platform:            macOS-15.7.1-arm64-arm-64bit
```

## 🐍 Gestión de Versiones de Python

El proyecto requiere Python 3.12 o superior:

```bash
# Ver versión actual de Python
uv python list

# Instalar versión específica de Python
uv python install 3.12

# Usar versión específica para el proyecto
uv python pin 3.12
```

## 📦 Archivos Importantes

- **`pyproject.toml`**: Configuración del proyecto y dependencias
- **`uv.lock`**: Lockfile con versiones exactas (debe ser versionado)
- **`.python-version`**: Versión de Python del proyecto
- **`requirements.txt`**: Mantenido para compatibilidad con pip

## 🔄 Migración desde pip

Si vienes de usar pip:

```bash
# Los requirements.txt siguen funcionando
uv pip install -r requirements.txt

# Pero se recomienda usar pyproject.toml
uv sync
```

## 🆘 Solución de Problemas

### Error: "Could not find uv"

```bash
# Asegúrate de que uv está en tu PATH
export PATH="$HOME/.local/bin:$PATH"

# O reinstala uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Error: Build backend failure

Si ves errores con hatchling:

```bash
# Sincronizar sin instalar el proyecto como paquete
uv sync --no-install-project
```

### Dependencias no resuelven

```bash
# Limpiar caché y reinstalar
rm uv.lock
uv sync --refresh
```

## 📚 Recursos

- [Documentación de uv](https://docs.astral.sh/uv/)
- [Instalación FastMCP con uv](https://gofastmcp.com/getting-started/installation)
- [Política de versiones FastMCP](https://gofastmcp.com/getting-started/installation#versioning-policy)
- [pyproject.toml specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)

