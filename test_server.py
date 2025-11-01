"""
Script de prueba para el servidor iCards MCP
Ejecutar con: uv run python test_server.py
"""

import asyncio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def test_server():
    """Prueba las herramientas del servidor MCP"""
    
    print("🎴 Probando servidor iCards MCP\n")
    print("=" * 60)
    
    # Conectar al servidor usando stdio transport
    transport = StdioTransport("python", ["server.py"])
    async with Client(transport) as client:
        
        # 1. Listar herramientas disponibles
        print("\n📋 Herramientas disponibles:")
        print("-" * 60)
        tools = await client.list_tools()
        for tool in tools:
            print(f"\n✓ {tool.name}")
            print(f"  Descripción: {tool.description}")
            if tool.inputSchema and 'properties' in tool.inputSchema:
                print(f"  Parámetros: {', '.join(tool.inputSchema['properties'].keys())}")
        
        print("\n" + "=" * 60)
        
        # 2. Probar add_flashcard
        print("\n📝 Probando: add_flashcard")
        print("-" * 60)
        result = await client.call_tool(
            name="add_flashcard",
            arguments={
                "front": "¿Qué es FastMCP?",
                "back": "Un framework Pythonic para construir servidores MCP",
                "deck_name": "FastMCP Basics"
            }
        )
        print(f"Resultado: {result}")
        
        print("\n" + "=" * 60)
        
        # 3. Probar list_decks
        print("\n📚 Probando: list_decks")
        print("-" * 60)
        result = await client.call_tool(
            name="list_decks",
            arguments={}
        )
        print(f"Resultado: {result}")
        
        print("\n" + "=" * 60)
        
        # 4. Probar get_deck_info
        print("\n ℹ️  Probando: get_deck_info")
        print("-" * 60)
        result = await client.call_tool(
            name="get_deck_info",
            arguments={"deck_name": "FastMCP Basics"}
        )
        print(f"Resultado: {result}")
        
        print("\n" + "=" * 60)
        print("\n✅ Todas las pruebas completadas exitosamente!")


if __name__ == "__main__":
    asyncio.run(test_server())

