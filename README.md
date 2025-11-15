# iCards MCP 🎴

Servidor MCP (Model Context Protocol) para gestionar flashcards, construido con FastMCP Python.

## ¿Qué es MCP?

El Model Context Protocol (MCP) permite que los LLMs (Large Language Models) interactúen de forma estandarizada con herramientas y datos externos. Es como un "puerto USB-C para IA":

- **Tools:** Funciones que el LLM puede ejecutar (como `add_flashcard`, `list_decks`)
- **Resources:** Datos que el LLM puede leer (documentación, contenido de decks)
- **Prompts:** Templates reutilizables para interacciones comunes

Este servidor expone las capacidades de iCards a través de MCP, permitiendo que asistentes de IA gestionen tus flashcards de forma inteligente.

## ✨ Features

- 🚀 **FastMCP 2.0:** Framework moderno y Pythonic para MCP
- 🎴 **Gestión de Flashcards:** Tools para crear, editar y gestionar flashcards
- 🌐 **Comunicación HTTP:** Se conecta a la API REST de iCards
- 📚 **Instrucciones Centralizadas:** Carga documentación desde ubicación externa compartida
- ⚙️ **Configuración por entornos:** Local y Producción
- 📦 **Estructura modular:** Servicios, configuración y extensibilidad
- 🔒 **Secure by design:** Sin acceso directo a BD, solo via API

### 📖 **Instrucciones Externas**

Las instrucciones del MCP se cargan desde una ubicación externa compartida:
**Path:** `/Users/esanz/Desktop/ia-mvp/project/server/InstructionsMCP/api_instructions.md`

**Beneficios:**
- ✅ Una sola fuente de verdad
- ✅ Sincronización automática entre proyectos
- ✅ Mantenimiento centralizado de documentación

## 🚀 Quickstart

### 1. Instalar dependencias

Este proyecto usa [uv](https://docs.astral.sh/uv/) para gestionar dependencias (recomendado por FastMCP).

```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias del proyecto
uv sync
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

### 3. Configurar el entorno

Para que el MCP funcione correctamente, necesitas configurar el token de autenticación:

```bash
# Copiar el archivo de ejemplo
cp env.example .env.local

# Obtener el JWT token (requerido)
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "tu-usuario", "password": "tu-password"}'

# Copiar el valor del campo "token" y agregarlo a .env.local
echo "AUTH_TOKEN=tu_jwt_token_aqui" >> .env.local

# Opcionalmente configurar otros valores
# API_BASE_URL=http://tu-api-url:puerto
# API_TIMEOUT=30
```

### 4. Ejecutar el servidor

```bash
# Con uv (recomendado)
uv run python server.py

# O con Python directamente si instalaste con pip
python server.py
```

El servidor MCP estará disponible vía stdio/SSE según tu configuración.

#### 🔍 Validación automática al inicio

El servidor realiza validación automática al iniciarse:

1. **Health Check:** Verifica que la API esté funcionando
2. **Token Validation:** Intenta obtener datos del usuario para validar el JWT
3. **Error Handling:** Si falla, muestra mensajes claros y se detiene

**Ejemplo de output exitoso:**
```
🚀 Starting iCards MCP Server...
🔍 Validating API connection...
🏥 Checking API health at http://localhost:3000/api/health...
✅ API health check passed: {'ok': True}
🔐 Validating token by fetching decks...
✅ Token validation passed - found 5 decks
🎉 API connection and token validation successful!
🎯 Starting MCP server and waiting for requests...
```

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

## 🛠️ **11 Tools Disponibles**

La aplicación incluye **11 tools especializadas** para gestión completa de flashcards:

## 🚀 **Tools Recomendadas por Frecuencia de Uso:**

1. **`bulk_create_flashcards`** ⭐ **PRINCIPAL** - Crear múltiples flashcards (2-50) eficientemente
2. **`create_deck`** - 🚀 Crear mazos con ELICITACIÓN INTERACTIVA para portadas IA
3. **`add_flashcard`** - Crear UNA sola flashcard (solo si no puedes usar bulk)
4. **`list_decks`** - Ver todos los mazos con tags incluidos
5. **`list_untagged_flashcards`** - Ver SOLO flashcards sin tags (optimizado para organización)
6. **`get_deck_stats`** - Estadísticas COMPLETAS y análisis detallado de un deck
7. **`assign_tags_to_flashcards`** - 🚀 **NUEVO:** Organización inteligente con auto-detección
8. **`list_flashcards`** - Ver flashcards con filtros y paginación
9. **`get_deck_info`** - Información básica de un mazo específico
10. **`count_flashcards`** - Conteo eficiente de flashcards
11. **`create_flashcard_template`** - Plantillas para contenido consistente
12. **`update_flashcard`** - Modificar flashcards existentes

## 💡 **Flujo de Trabajo Recomendado:**

1. **Crear mazo** → `create_deck` (🚀 **ELICITACIÓN INTERACTIVA** para portada IA)
2. **Agregar flashcards** → `bulk_create_flashcards` (SIN tags inicialmente)
3. **Verificar organización** → `list_decks` (muestra ⚠️ si hay flashcards sin tags)
4. **Análisis detallado** → `get_deck_stats` (estadísticas completas y insights)
5. **🚀 Organizar automáticamente** → `assign_tags_to_flashcards(filter_criteria="untagged")`
6. **Revisar** → `list_flashcards` o `get_deck_info`

### 🎯 **Nuevo Flujo Optimizado (Recomendado):**

```bash
# 1. Crear mazo con ELICITACIÓN INTERACTIVA
create_deck(name="Portuguese Learning")
# → 🚀 Te pregunta: "¿Quieres imagen de portada con IA?"
# → Responde: "sí" o "no"

# 2. Crear flashcards en bulk (sin tags)
bulk_create_flashcards(deck_name="Portuguese Learning", flashcards=[...])

# 3. 🚀 ¡Organizar automáticamente!
assign_tags_to_flashcards(
    deck_name="Portuguese Learning",
    tag_name="Saudações",
    filter_criteria="untagged"  # ✨ Auto-detecta flashcards sin tags
)
```

**🎨 Elicitación Inteligente + Auto-Organización = Flujo Perfecto!** 🎉

## 🐳 Docker

```bash
# Copiar configuración
cp env.example .env

# Editar .env con tu configuración
# AUTH_TOKEN=tu_jwt_token_real
# API_BASE_URL=https://tu-backend-productivo.com

# Ejecutar
docker-compose up -d
```

### Configuración de URLs

**Para desarrollo local:**
```bash
API_BASE_URL=http://host.docker.internal:3000
```

**Para producción (Hostinger):**
```bash
API_BASE_URL=https://tu-proyecto.hostinger.com
```

**Para pasar como variable de entorno:**
```bash
API_BASE_URL=https://tu-dominio.com docker-compose up -d
```

El servidor MCP estará disponible en `http://localhost:3001` para usar con `mcp-proxy`.

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
Agrega UNA SOLA flashcard a un deck. ⚠️ **Usa solo para flashcards individuales**.

**CUÁNDO USAR:** Para agregar 1 flashcard. Para múltiples (2-50), usa `bulk_create_flashcards`.

**Parámetros:**
- `front` (requerido): Pregunta o frente de la tarjeta
- `back` (requerido): Respuesta o reverso de la tarjeta
- `deck_name` (requerido): Nombre del deck
- `difficulty_level` (opcional): Dificultad 1-5 (default: 2)
- `tag_name` (opcional): ⚠️ **RECOMENDACIÓN: No uses inicialmente, organiza después**

```python
{
    "front": "¿Qué es MCP?",
    "back": "Model Context Protocol - Un protocolo para conectar LLMs a herramientas",
    "deck_name": "MCP Basics",
    "difficulty_level": 2
    // ⚠️ Sin tag_name - organiza después con assign_tags_to_flashcards
}
```

**💡 RECOMENDACIÓN:** Crea flashcards SIN tags inicialmente, luego organiza con `assign_tags_to_flashcards`.

### 📚 list_decks
Lista todos los decks de flashcards disponibles con información de organización.

**NUEVO**: Incluye indicador de flashcards sin tags para mejor organización.

```python
{}  # Sin argumentos
```

**Respuesta incluye (mejorado):**
- Lista completa de decks con estadísticas
- **`untagged_flashcards_count`**: ⚠️ Número de flashcards que necesitan organización
- **`organization_status`**: "organized" | "needs_organization" | "empty"
- **Indicadores visuales**: Emojis para estado de organización

### 📊 get_deck_stats
**NUEVA** 📈 Obtiene estadísticas COMPLETAS y análisis detallado de un deck específico.

**¿Por qué usar esta tool?**
- **📊 Estadísticas completas**: Total, organización, distribución por dificultad y tags
- **🎯 Análisis de organización**: Porcentaje organizado, status, métricas detalladas
- **📚 Métricas de estudio**: Reviews, precisión, rachas, rendimiento
- **💡 Insights automáticos**: Análisis inteligente con recomendaciones

**Uso típico:**
```python
{
    "deck_name": "storage"
}
```

**Respuesta incluye:**
- `statistics`: Datos completos de estadísticas del backend
- `insights[]`: Análisis inteligente con emojis y recomendaciones
- `organization_status`: Estado de organización ("organized" | "needs_organization" | "empty")
- `last_updated`: Timestamp de última actualización

**Campos de estadísticas principales:**
- **Totales**: `totalFlashcards`, `untaggedFlashcards`, `taggedFlashcards`
- **Distribución**: `flashcardsByDifficulty` (1-5), `flashcardsByTag` con porcentajes
- **Organización**: `organizationPercentage`, `tagsCount`, `averageTagsPerFlashcard`
- **Estudio**: `totalReviews`, `accuracyRate`, `currentStreak`, `averageDifficulty`

### ℹ️ get_deck_info
Obtiene información completa sobre un deck específico, incluyendo:
- Información básica del deck (nombre, descripción, fechas)
- Estadísticas de tarjetas (conteo total, distribución de dificultad)
- **Tags del deck con conteo de flashcards por tag**
- Progreso de estudio y actividad

Esta herramienta hace múltiples llamadas a la API para consolidar toda la información en una sola respuesta.

```python
{
    "deck_name": "Japanese Vocabulary"
}
```

**Respuesta incluye:**
- `deck`: Información básica del deck
- `tags`: Lista de tags con `flashcard_count` por cada tag
- `tag_count`: Total de tags en el deck
- `statistics`: Estadísticas consolidadas (total_flashcards, total_tags, difficulty_distribution, average_difficulty)

### 🏷️ list_untagged_flashcards
**NUEVA** 🚀 Lista SOLO las flashcards que NO tienen tags asignados. Optimizada para flujos de organización.

**¿Por qué usar esta tool?**
- **⚡ Endpoint optimizado**: No carga información de tags, más rápido que `list_flashcards`
- **🎯 Foco en organización**: Perfecta para identificar qué tarjetas necesitan categorización
- **📊 Conteo claro**: Muestra exactamente cuántas tarjetas necesitan organización
- **🔄 Flujo eficiente**: Preparación perfecta para `assign_tags_to_flashcards`
- **🛡️ Validación cruzada**: Verifica consistencia entre endpoints para evitar confusiones

**Uso típico:**
```python
{
    "deck_name": "Japanese Learning",
    "all_cards": true  # Recomendado: obtener todas de una vez
}
```

**Respuesta incluye:**
- `untagged_flashcards`: Lista de flashcards sin tags (sin campos `tagId` ni `tag`)
- `untagged_count`: Número de flashcards que necesitan organización
- `message`: Resumen claro del estado de organización

**Validaciones implementadas:**
- ✅ Verificación cruzada con endpoint de conteo
- ✅ Detección de inconsistencias del backend
- ✅ Mensaje claro cuando todo está organizado

## 🔧 **Implementación Backend Recomendada**

Para aprovechar al máximo la organización, modifica tu backend para incluir estos campos en `/api/decks`:

### **Campos a Agregar por Deck:**
```json
{
  "id": 6,
  "name": "Japanese Learning",
  "description": "...",
  "card_count": 11,
  "untagged_flashcards_count": 0,  // ← NUEVO
  "organization_status": "organized",  // ← NUEVO: "organized" | "needs_organization" | "empty"
  "tags": [...]
}
```

### **Lógica Backend:**
```javascript
// En el endpoint GET /api/decks
untagged_flashcards_count = await countUntaggedFlashcards(deck.id)

if (deck.card_count === 0) {
  organization_status = "empty"
} else if (untagged_flashcards_count > 0) {
  organization_status = "needs_organization"
} else {
  organization_status = "organized"
}
```

### **Beneficios:**
- **Vista rápida**: `list_decks` muestra estado de organización al instante
- **Optimización**: No necesitas llamadas adicionales para verificar organización
- **UX mejorada**: Indicadores visuales ⚠️ ✅ 📝 guían la organización

**Flujo recomendado:**
1. Crear flashcards con `bulk_create_flashcards` (sin tags)
2. Usar `list_untagged_flashcards` para ver qué falta organizar
3. Organizar con `assign_tags_to_flashcards`

### 🏷️ create_flashcard_template
Crea una plantilla de flashcard basada en el tipo de deck.

```python
{
    "deck_type": "vocabulary"
}
```

### 📋 list_flashcards
Lista las flashcards de un deck específico.

**Comportamiento:**
- **Por defecto**: Retorna 50 tarjetas (límite configurable 1-100)
- **Con `all_cards=True`**: Retorna TODAS las tarjetas del deck (sin límite)

**Cuándo usar `all_cards=True`:**
- Para análisis completos (contar tags únicos, estadísticas globales)
- Para exportar todas las tarjetas
- Para operaciones que requieren ver el deck completo

**Cuándo usar el límite por defecto:**
- Para previsualizar tarjetas
- Para navegación paginada
- Para mostrar ejemplos

```python
# Ejemplo 1: Primeras 50 tarjetas (por defecto)
{
    "deck_name": "Japanese Vocabulary",
    "limit": 50,
    "sort_by": "created"
}

# Ejemplo 2: TODAS las tarjetas (para análisis completo)
{
    "deck_name": "Japanese Vocabulary",
    "all_cards": True
}
```

**Nota:** Para solo obtener el conteo sin datos, usa `count_flashcards` que es más eficiente.

### 🔢 count_flashcards
Cuenta el número total de flashcards en un deck con una sola llamada a la API usando el parámetro all=true. Obtiene el conteo exacto sin límites de paginación.

```python
{
    "deck_name": "Japanese Vocabulary"
}
```

### 🚀 bulk_create_flashcards ⭐ **RECOMENDADO para múltiples flashcards**
Crea MÚLTIPLES flashcards eficientemente (2-50 por operación). ⚡ **Mucho más rápido que agregar una por una**.

**CUÁNDO USAR:** Siempre que necesites crear 2 o más flashcards. Es la forma más eficiente!

**Características:**
- 🚀 **Crea 2-50 flashcards en UNA sola operación**
- ✅ **Valida todo el contenido antes de crear**
- 📊 **Reporta éxito/fallo detallado por cada flashcard**
- 🎯 **Todas las flashcards van al mismo mazo**
- 💡 **Crea SIN tags inicialmente** (organiza después)

```python
{
  "deck_name": "Italian Learning",
  "flashcards": [
    {
      "front": "Buongiorno",
      "back": "Good morning",
      "difficulty": 1
    },
    {
      "front": "Grazie",
      "back": "Thank you",
      "difficulty": 2
    },
    {
      "front": "Per favore",
      "back": "Please"
      // ⚠️ Sin tag - organiza después
    }
  ]
}
```

**Respuesta incluye:**
- `created_count`: Número de flashcards creadas exitosamente
- `failed_count`: Número de flashcards que fallaron validación
- `validation_errors`: Detalles de errores de validación (si los hay)

**💡 TIP:** Usa esta tool en lugar de `add_flashcard` cuando tengas múltiples flashcards que crear.

## 💡 **Instrucciones Contextuales**

Cada tool proporciona **instrucciones contextuales específicas** en el campo `_instructions` de la respuesta, guiándote sobre los próximos pasos recomendados basados en la operación realizada.

### **Ejemplos de Instrucciones Contextuales:**

**Después de crear un mazo:**
```
¡Mazo 'Italian Learning' creado exitosamente! Ahora puedes:
• Agregar tu primera flashcard con 'add_flashcard(deck_name="Italian Learning", front="...", back="...")
• Crear un template de contenido con 'create_flashcard_template'
• Ver los detalles del mazo con 'get_deck_info(deck_name="Italian Learning")'
```

**Después de agregar una flashcard:**
```
¡Flashcard agregada exitosamente! Ahora puedes:
• Agregar más flashcards con 'add_flashcard'
• Crear un template con 'create_flashcard_template'
• Ver todas las flashcards del mazo con 'list_flashcards(deck_name="Italian Learning")'
```

**Después de listar mazos:**
```
Aquí tienes todos tus mazos. Puedes:
• Crear un nuevo mazo con 'create_deck'
• Ver detalles de un mazo específico con 'get_deck_info'
• Agregar flashcards a cualquier mazo con 'add_flashcard'
```

### **Arquitectura Modular:**

Las instrucciones contextuales están implementadas en `app/mcp/instructions.py` para mantener la separación de responsabilidades y facilitar el mantenimiento.

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

1. **Ubicación del archivo de configuración:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux/VPS: `~/.config/Claude/claude_desktop_config.json`

2. **Configuración completa:**

```json
{
  "mcpServers": {
    "icards": {
      "command": "python",
      "args": ["/ruta/a/iCardsMCP/server.py"],
      "env": {
        "AUTH_TOKEN": "tu_jwt_token_aqui",
        "API_BASE_URL": "https://tu-api-domain.com",
        "API_TIMEOUT": "30",
        "SCOPE": "prod"
      }
    }
  }
}
```

3. **Obtener el AUTH_TOKEN:**
   ```bash
   # Para desarrollo local
   curl -X POST http://localhost:3000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "tu-usuario", "password": "tu-password"}'

   # Para producción/VPS
   curl -X POST https://tu-api-domain.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "tu-usuario", "password": "tu-password"}'
   ```

4. **Reiniciar Claude Desktop** después de actualizar la configuración.

### 🔐 Configuración segura para VPS

Para entornos de producción, nunca pongas tokens sensibles directamente en archivos JSON. Usa variables de entorno:

```bash
# En tu VPS, configura la variable de entorno
export AUTH_TOKEN="tu_jwt_token_real_aqui"

# O en Docker
docker run -e AUTH_TOKEN="tu_token" tu-imagen

# En el JSON de Claude, usa un marcador que indique que debe configurarse
{
  "mcpServers": {
    "icards": {
      "command": "python",
      "args": ["/ruta/a/iCardsMCP/server.py"],
      "env": {
        "AUTH_TOKEN": "CONFIGURAR_EN_ENTORNO",
        "API_BASE_URL": "https://tu-api-domain.com",
        "SCOPE": "prod"
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

