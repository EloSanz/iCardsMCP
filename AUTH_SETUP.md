# 🔐 Configuración de Autenticación - AUTH_TOKEN

## ¿Por qué necesito AUTH_TOKEN?

El servidor MCP necesita autenticarse con tu API de iCards para poder:
- ✅ Leer tus flashcards y decks
- ✅ Crear nuevos flashcards
- ✅ Modificar contenido existente
- ✅ Validar permisos de acceso

Sin el token JWT válido, **el servidor MCP no podrá iniciar**.

## 🚀 Cómo obtener tu AUTH_TOKEN

### 1. Verificar que tu API esté corriendo

```bash
curl http://localhost:3000/api/health
# Deberías ver: {"ok": true}
```

### 2. Hacer login para obtener el JWT

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "tu-usuario",
    "password": "tu-password"
  }'
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "username": "tu-usuario"
  }
}
```

### 3. Configurar el token

#### Opción A: Archivo de entorno (.env.local)
```bash
echo "AUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." > .env.local
```

#### Opción B: Variable de entorno directa
```bash
export AUTH_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Opción C: Claude Desktop config
```json
{
  "mcpServers": {
    "icards": {
      "command": "/path/to/run_mcp_stdio.sh",
      "env": {
        "AUTH_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      }
    }
  }
}
```

## 🔍 Verificación

Cuando inicies el servidor MCP, deberías ver:

```
🔍 Validating API connection...
🏥 Checking API health at http://localhost:3000/api/health...
✅ API health check passed: {'ok': True}
🔐 Validating token by fetching decks...
✅ Token validation passed - found X decks
🎉 API connection and token validation successful!
```

## ⚠️ Errores comunes

### "Authentication failed - invalid or missing AUTH_TOKEN"
- **Causa:** Token expirado, inválido o no configurado
- **Solución:** Obtén un nuevo token con login

### "Cannot connect to API at http://localhost:3000"
- **Causa:** La API de iCards no está corriendo
- **Solución:** Inicia tu servidor de iCards API

### "API endpoint not found"
- **Causa:** URL de API incorrecta
- **Solución:** Verifica `API_BASE_URL` en configuración

## 🔄 Renovación del token

Los tokens JWT expiran. Cuando veas errores 401:

1. Vuelve a hacer login
2. Actualiza el `AUTH_TOKEN`
3. Reinicia el servidor MCP

## 🔒 Seguridad

- ✅ El token se valida automáticamente al inicio
- ✅ Nunca se loguea el token completo (solo "configured")
- ✅ El token se envía solo a tu API local
- ✅ Usa HTTPS en producción para tokens en tránsito

## 📞 Soporte

Si tienes problemas:
1. Verifica que la API esté corriendo: `curl http://localhost:3000/api/health`
2. Verifica que el token sea válido: `curl -H "Authorization: Bearer TU_TOKEN" http://localhost:3000/api/decks`
3. Revisa los logs del servidor MCP para mensajes detallados
