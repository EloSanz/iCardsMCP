# MCP STDIO Protocol - Critical Guidelines

## 🚨 El Problema: "Unexpected token" en Claude Desktop

### Causa raíz
El protocolo MCP (Model Context Protocol) usa **JSON-RPC sobre STDIO** para comunicación:
- **stdout** → Canal exclusivo para mensajes JSON-RPC
- **stderr** → Canal para logs y debugging

**Cualquier output extra a stdout rompe el protocolo JSON** y causa errores como:
```
MCP icards: Unexpected token ',' [0:32m▶... is not valid JSON
MCP icards: Unexpected token 'S', "SCOPE: [0'... is not valid JSON
```

### Qué estaba causando los errores

#### ❌ ANTES (causaba errores):
```python
# En server.py
print(f"📄 Loaded environment variables from {env_file}")  # ← A stdout!
logger.info("🚀 Initializing iCards MCP Server...")        # ← A stdout!
console.print("✅ FastMCP server initialized")             # ← A stdout!
```

```bash
# En run_mcp_stdio.sh
echo -e "${GREEN}🚀 Starting iCards MCP Server...${NC}"    # ← A stdout!
echo -e "${YELLOW}📁 Project directory: $PROJECT_DIR${NC}"  # ← A stdout!
```

#### ✅ DESPUÉS (funciona correctamente):
```python
# En server.py
# No prints a stdout
# Logging configurado a stderr con nivel WARNING
logging.basicConfig(
    level=logging.WARNING,
    stream=sys.stderr  # ← CRÍTICO: stderr only
)

# Console de rich configurado a stderr
console = Console(stderr=True)  # ← CRÍTICO: stderr=True
```

```bash
# En run_mcp_stdio.sh
# Sin echo coloridos
# Solo errores críticos a stderr:
echo "❌ AUTH_TOKEN not configured" >&2  # ← A stderr
```

## 📋 Reglas de Oro para MCP

### 1. **NUNCA escribir a stdout**
```python
# ❌ MAL
print("Starting server...")
logger.info("Server ready")  # Si logging va a stdout

# ✅ BIEN
# Silencio total en stdout
logger.error("Error occurred")  # Solo si logging va a stderr
```

### 2. **Logging SIEMPRE a stderr**
```python
# ✅ Configuración correcta
logging.basicConfig(
    level=logging.WARNING,  # Solo warnings y errores
    stream=sys.stderr       # CRÍTICO
)

# ✅ Rich console a stderr
console = Console(stderr=True)
```

### 3. **Scripts bash: redirigir a stderr**
```bash
# ❌ MAL
echo "Starting..."

# ✅ BIEN
echo "Error occurred" >&2  # Solo errores a stderr
```

### 4. **Minimizar logs en producción**
```python
# Para MCP, menos es más
logging.basicConfig(level=logging.WARNING)  # No INFO, no DEBUG
```

## 🔧 Cómo Debuggear

### Ver logs del MCP en Claude Desktop
Los logs de stderr aparecen en:
- **macOS**: `~/Library/Logs/Claude/mcp*.log`
- **Windows**: `%APPDATA%\Claude\logs\mcp*.log`

### Debuggear localmente
```bash
# Ejecutar el MCP manualmente y ver stderr
cd /Users/esanz/Desktop/ia-mvp/iCardsMCP
./run_mcp_stdio.sh 2>&1 | tee debug.log
```

### Verificar que no hay output a stdout
```bash
# El stdout debe estar vacío hasta que llegue un request MCP
./run_mcp_stdio.sh 2>/dev/null
# Si ves CUALQUIER texto aquí, está roto
```

## 📚 Referencias

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://gofastmcp.com/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

## ✅ Checklist de Validación

Antes de deployar cambios al MCP:

- [ ] No hay `print()` statements en el código
- [ ] Logging configurado con `stream=sys.stderr`
- [ ] Rich Console configurado con `stderr=True`
- [ ] Scripts bash redirigen output a stderr (`>&2`)
- [ ] Nivel de logging es WARNING o superior
- [ ] Probado localmente sin errores "Unexpected token"

---

**Última actualización:** Noviembre 2025

