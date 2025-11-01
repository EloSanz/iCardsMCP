# iCards MCP 🎴

Servidor MCP (Model Context Protocol) para gestionar flashcards y sesiones de estudio, construido con FastMCP Python.

## ¿Qué es MCP?

El Model Context Protocol (MCP) permite que los LLMs (Large Language Models) interactúen de forma estandarizada con herramientas y datos externos. Es como un "puerto USB-C para IA":

- **Tools:** Funciones que el LLM puede ejecutar (como `add_flashcard`, `list_decks`)
- **Resources:** Datos que el LLM puede leer (documentación, contenido de decks)
- **Prompts:** Templates reutilizables para interacciones comunes

Este servidor expone las capacidades de iCards a través de MCP, permitiendo que asistentes de IA gestionen tus flashcards de forma inteligente.

## ✨ Features

- 🚀 **FastMCP 2.0:** Framework moderno y Pythonic para MCP
- 🎴 **Gestión de Flashcards:** Tools para crear, editar y estudiar flashcards
- 🌐 **Comunicación HTTP:** Se conecta a la API REST de iCards
- ⚙️ **Configuración por entornos:** Local y Producción
- 📦 **Estructura modular:** Servicios, configuración y extensibilidad
- 🔒 **Secure by design:** Sin acceso directo a BD, solo via API

## 🚀 Quickstart

### 1. Instalar dependencias

Este proyecto usa [uv](https://docs.astral.sh/uv/) para gestionar dependencias (recomendado por FastMCP).

```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias del proyecto
uv sync
```

Alternativamente, puedes usar pip:

```bash
pip install -r requirements.txt
```

### 2. Verificar instalación

```bash
uv run fastmcp version
```

Deberías ver:

```
FastMCP version:                           2.11.3
MCP version:                               1.20.0
Python version:                            3.13.3
Platform:            macOS-15.7.1-arm64-arm-64bit
```

### 3. Configurar el entorno (opcional)

Por defecto usa configuración **local**. Para personalizar:

```bash
# Copiar el archivo de ejemplo
cp env.example .env

# Editar con tus valores
# API_BASE_URL=http://localhost:3000
```

### 4. Ejecutar el servidor

```bash
# Con uv (recomendado)
uv run python server.py

# O con Python directamente si instalaste con pip
python server.py
```

El servidor MCP estará disponible vía stdio/SSE según tu configuración.

### 5. Probar el servidor

Ejecuta el script de prueba incluido:

```bash
uv run python test_server.py
```

O prueba desde Python:

```python
import asyncio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

async def main():
    transport = StdioTransport("python", ["server.py"])
    async with Client(transport) as client:
        # Listar decks
        result = await client.call_tool(
            name="list_decks",
            arguments={}
        )
        print(result.data)

asyncio.run(main())
```

## 📁 Estructura del Proyecto

```
iCardsMCP/
├── server.py                    # Punto de entrada del servidor MCP
├── app/
│   ├── config/
│   │   └── config.py           # Configuración por entornos (local, prod)
│   ├── services/               # Lógica de negocio (próximamente)
│   │   ├── flashcard_service.py
│   │   ├── deck_service.py
│   │   └── study_service.py
│   └── adapters/               # Adaptadores HTTP (próximamente)
│       └── icards_api_adapter.py
├── requirements.txt            # Dependencias del proyecto
├── env.example                 # Ejemplo de configuración
└── README.md                   # Este archivo
```

## 🛠️ Tools Disponibles

### 📝 add_flashcard
Agrega una nueva flashcard a un deck.

```python
{
    "front": "¿Qué es MCP?",
    "back": "Model Context Protocol - Un protocolo para conectar LLMs a herramientas",
    "deck_name": "MCP Basics"
}
```

### 📚 list_decks
Lista todos los decks de flashcards disponibles.

```python
{}  # Sin argumentos
```

### ℹ️ get_deck_info
Obtiene información sobre un deck específico.

```python
{
    "deck_name": "Japanese Vocabulary"
}
```

### 🏷️ create_flashcard_template
Crea una plantilla de flashcard basada en el tipo de deck.

```python
{
    "deck_type": "vocabulary"
}
```

### 📋 list_flashcards
Lista todas las flashcards en un deck específico.

```python
{
    "deck_name": "Japanese Vocabulary",
    "limit": 50,
    "sort_by": "created"
}
```

## ⚙️ Configuración

El proyecto usa configuración basada en **SCOPE** (entornos):

### Local (default)
```bash
# No requiere configuración
python server.py
```

```python
{
    "MCP_ICARDS_NAME": "iCards-MCP-Local",
    "API_BASE_URL": "http://localhost:3000",
    "LOG_LEVEL": "DEBUG"
}
```

### Production
```bash
# Requiere variables de entorno
SCOPE=prod API_BASE_URL=https://api.icards.com python server.py
```

```python
{
    "MCP_ICARDS_NAME": "iCards-MCP-Prod",
    "API_BASE_URL": os.getenv("API_BASE_URL"),  # Requerido
    "LOG_LEVEL": "WARNING"
}
```

## 🔧 Agregar Nuevos Tools

1. **Crear el servicio** en `app/services/`:

```python
# app/services/study_service.py
from app.config.config import Config
import httpx

async def start_study_session(deck_id: int, card_count: int) -> dict:
    """Inicia una sesión de estudio."""
    api_url = Config.get("API_BASE_URL")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{api_url}/api/study/start",
            json={"deck_id": deck_id, "card_count": card_count}
        )
        return response.json()
```

2. **Registrar el tool** en `server.py`:

```python
from app.services.study_service import start_study_session

@mcp.tool()
async def start_study(deck_id: int, card_count: int = 10) -> dict:
    """Start a study session with flashcards from a deck."""
    return await start_study_session(deck_id, card_count)
```

3. **Reiniciar el servidor** y el tool estará disponible.

## 📖 Usando con LLMs

### Claude Desktop

Agrega al archivo de configuración de Claude Desktop:

```json
{
  "mcpServers": {
    "icards": {
      "command": "python",
      "args": ["/path/to/iCardsMCP/server.py"],
      "env": {
        "API_BASE_URL": "http://localhost:3000"
      }
    }
  }
}
```

### Cursor / VS Code

Usa el cliente MCP en tu código:

```python
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

transport = StdioTransport("python", ["server.py"])
async with Client(transport) as client:
    tools = await client.list_tools()
    result = await client.call_tool("add_flashcard", {
        "front": "Question",
        "back": "Answer",
        "deck_name": "My Deck"
    })
    print(result.data)
```

## 🧪 Testing

El proyecto incluye dependencias de desarrollo para testing. Para ejecutar tests:

```bash
# Instalar dependencias de desarrollo
uv sync --all-extras

# Ejecutar tests (cuando estén implementados)
uv run pytest tests/

# Con coverage
uv run pytest --cov=app tests/

# Ver reporte de coverage en HTML
uv run pytest --cov=app --cov-report=html tests/
```

## 📚 Recursos

- [Documentación FastMCP](https://gofastmcp.com/)
- [Instalación con uv](https://gofastmcp.com/getting-started/installation)
- [Especificación MCP](https://spec.modelcontextprotocol.io/)
- [Repositorio FastMCP](https://github.com/jlowin/fastmcp)
- [Documentación de uv](https://docs.astral.sh/uv/)
- [Proyecto iCards principal](../project/)

## 🎯 Roadmap

- [ ] Implementar adaptadores HTTP para la API de iCards (Flashcard, Deck, Tag APIs)
- [ ] Agregar más tools (editar flashcards, eliminar decks, gestión de tags)
- [ ] Implementar Resources para exponer contenido de decks
- [ ] Agregar Prompts comunes (generar flashcards basadas en templates)
- [ ] Tests unitarios y de integración
- [ ] Autenticación y autorización
- [ ] Métricas y logging avanzado
- [ ] Deploy a producción

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

MIT

