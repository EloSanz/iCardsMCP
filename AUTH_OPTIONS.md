# 🔐 Opciones de Autenticación - iCards MCP Server

## 📋 Métodos Disponibles

### 1. **Sin Autenticación** (Desarrollo)
- **Ventaja:** Simple y rápido para testing
- **Configuración:**
  ```json
  {
    "icards": {
      "command": "uvx",
      "args": ["mcp-proxy", "http://localhost:3001/sse"],
      "env": {}
    }
  }
  ```

### 2. **Token por Cliente** (Recomendado para Producción con mcp-proxy)
- **Ventaja:** Cada cliente configura su propio token JWT en el cliente MCP.
- **Configuración (Claude Desktop / Cursor):**
  ```json
  {
    "icards": {
      "command": "uvx",
      "args": [
        "mcp-proxy",
        "-H", "Authorization", "tu_token_jwt_aqui",
        "http://localhost:8081/sse"
      ],
      "env": {},
      "restart": true
    }
  }
  ```

### 3. **OAuth con Descope** (Autenticación Automática)
- **Ventaja:** Los usuarios se autentican automáticamente sin configurar tokens
- **Requisitos:** Cuenta en [Descope](https://www.descope.com)
- **Configuración:**
  ```json
  {
    "icards": {
      "command": "uv",
      "args": ["run", "python", "/path/to/server.py"],
      "env": {
        "DESCOPE_CONFIG_URL": "https://tu-descope-url/.well-known/openid-configuration",
        "SERVER_URL": "https://tu-server.com"
      }
    }
  }
  ```

## 🚀 **¿Cuál usar?**

### **Para Desarrollo/Local:** Opción 1 (Sin auth)
### **Para Equipo Pequeño:** Opción 2 (Token por cliente)
### **Para Producción/Empresa:** Opción 3 (OAuth Descope)

## 📖 **Configuración de Descope**

1. **Crear cuenta** en [Descope](https://www.descope.com)
2. **Crear MCP Server** en la consola de Descope
3. **Habilitar DCR** (Dynamic Client Registration)
4. **Copiar Well-Known URL**
5. **Configurar variables de entorno**

## 🔧 **Migración entre métodos**

- **De Sin Auth → Token por cliente:** Solo cambiar el `mcp.json`
- **De Token → Descope:** Configurar Descope y cambiar variables
- **Todos los métodos** son compatibles con Docker y VPS

## 📋 **Variables de Entorno**

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `AUTH_TOKEN` | JWT token del usuario | Solo método 2 |
| `DESCOPE_CONFIG_URL` | URL de configuración Descope | Solo método 3 |
| `SERVER_URL` | URL pública del servidor | Solo método 3 |
| `SSE_PORT` | Puerto para modo SSE | Opcional |
| `API_BASE_URL` | URL de la API iCards | Siempre |

## 🎯 **Recomendación**

Para **tu caso** (múltiples clientes con tokens diferentes), usa **Opción 2**:

1. **Cada cliente** configura su `AUTH_TOKEN` en el `mcp.json`
2. **El servidor** lee el token del header `x-auth-token`
3. **Sin hardcodear** nada en el código del servidor
4. **Funciona** con Docker y VPS
