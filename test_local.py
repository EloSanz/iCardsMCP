#!/usr/bin/env python3
"""
Test script to verify local functionality.
"""
import asyncio
import os
from app.services.deck_service import DeckService
from app.services import base_service

async def test_local():
    """Test local functionality."""
    # Set the auth token globally
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjIsImlhdCI6MTc2NDI4NzM2OSwiZXhwIjoxNzY0MzczNzY5fQ._pjbfB_xmK4LBpLMA5IRPBlzjgNPdK2KyEX4UY_1TUE"
    base_service.current_auth_token = token

    print("🔧 Testing with token set globally")

    # Create a new instance to force reload
    deck_service = DeckService()

    try:
        # Test list decks
        print("📋 Testing list_decks_mcp...")
        response = await deck_service.list_decks_mcp()
        print(f"✅ Success: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Set environment to use remote server
    os.environ["API_BASE_URL"] = "http://72.61.45.36:3000"

    asyncio.run(test_local())
