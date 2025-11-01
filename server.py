"""
iCards MCP Server
A FastMCP server for managing flashcards and study sessions.
"""

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("iCards 🎴")


@mcp.tool()
def add_flashcard(front: str, back: str, deck_name: str = "default") -> dict:
    """
    Add a new flashcard to a deck.
    
    Args:
        front: The front side of the flashcard (question/prompt)
        back: The back side of the flashcard (answer)
        deck_name: The name of the deck to add the card to
    
    Returns:
        Dictionary with success status and flashcard details
    """
    return {
        "success": True,
        "flashcard": {
            "front": front,
            "back": back,
            "deck": deck_name
        },
        "message": f"Flashcard added to deck '{deck_name}'"
    }


@mcp.tool()
def get_deck_info(deck_name: str) -> dict:
    """
    Get information about a specific deck.
    
    Args:
        deck_name: The name of the deck to retrieve information for
    
    Returns:
        Dictionary with deck information
    """
    return {
        "deck_name": deck_name,
        "card_count": 0,
        "message": "This is a placeholder. Connect to your database for real data."
    }


@mcp.tool()
def list_decks() -> dict:
    """
    List all available flashcard decks.
    
    Returns:
        Dictionary with list of decks
    """
    return {
        "decks": [],
        "message": "This is a placeholder. Connect to your database for real data."
    }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()

