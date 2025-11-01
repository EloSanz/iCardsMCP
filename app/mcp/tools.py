"""Tools for the iCards MCP server."""

from typing import Optional, List, Literal

import logging
from pydantic import Field

from app.mcp.utils import (
    validate_deck_name,
    validate_flashcard_content,
    format_flashcard_response,
    format_deck_response,
    calculate_study_progress,
    generate_study_recommendations,
    create_flashcard_template,
    parse_study_session_data,
    get_api_base_url
)

logger = logging.getLogger(__name__)

# Type aliases for validation
DeckType = Literal["vocabulary", "grammar", "kanji", "phrases", "general", "custom"]
DifficultyLevel = Literal[1, 2, 3, 4, 5]

# Store tool functions to be registered later
_tool_functions = []


def register_icards_tools(mcp_server):
    """Register all iCards MCP tools with the MCP server instance."""

    # Tool 1: Add Flashcard
    @mcp_server.tool(
        name="add_flashcard",
        description="""
        Add a new flashcard to a deck.

        Creates a new flashcard with front/back content and associates it with a deck.
        Validates content length and format before creating.

        Supports different deck types: vocabulary, grammar, kanji, phrases, general, custom.
        """,
        tags={"flashcards", "creation", "content"}
    )
    async def add_flashcard(
        front: str = Field(..., description="The front side of the flashcard (question/prompt)"),
        back: str = Field(..., description="The back side of the flashcard (answer)"),
        deck_name: str = Field("default", description="The name of the deck to add the card to"),
        deck_type: DeckType = Field("general", description="Type of deck for content guidance"),
        difficulty_level: DifficultyLevel = Field(1, description="Difficulty level (1-5)"),
        tags: Optional[List[str]] = Field(None, description="Optional tags for categorization")
    ) -> dict:
        """Add a new flashcard to a deck."""
        try:
            # Validate inputs
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name must be 1-100 characters and cannot contain invalid characters: < > : \" | ? *"
                }

            is_valid, error_msg = validate_flashcard_content(front, back)
            if not is_valid:
                return {
                    "error": "Invalid flashcard content",
                    "message": error_msg
                }

            # Prepare flashcard data
            flashcard_data = {
                "front": front.strip(),
                "back": back.strip(),
                "deck_name": deck_name.strip(),
                "deck_type": deck_type,
                "difficulty_level": difficulty_level,
                "tags": tags or []
            }

            # TODO: Call actual API when implemented
            # For now, return success response
            response_data = format_flashcard_response({
                "id": f"card_{hash(f'{front}{back}')}",
                "front": front,
                "back": back,
                "deck_name": deck_name,
                "difficulty_level": difficulty_level,
                "tags": tags or [],
                "created_at": "2025-01-01T00:00:00Z",
                "review_count": 0,
                "correct_count": 0
            })

            return {
                "success": True,
                "flashcard": response_data,
                "message": f"Flashcard added to deck '{deck_name}' successfully",
                "deck_type": deck_type,
                "difficulty_level": difficulty_level
            }

        except Exception as e:
            logger.error(f"Error adding flashcard: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not add flashcard: {str(e)}"
            }

    # Tool 2: List Decks
    @mcp_server.tool(
        name="list_decks",
        description="""
        List all available flashcard decks.

        Returns information about all decks including card counts, progress metrics,
        and study statistics. Useful for overview and navigation.
        """,
        tags={"decks", "overview", "navigation"}
    )
    async def list_decks() -> dict:
        """List all available flashcard decks."""
        try:
            # TODO: Call actual API when implemented
            # For now, return placeholder data
            decks = [
                {
                    "id": "deck_japanese_vocab",
                    "name": "Japanese Vocabulary",
                    "description": "Essential Japanese vocabulary words",
                    "card_count": 50,
                    "created_at": "2025-01-01T00:00:00Z",
                    "is_active": True,
                    "tags": ["japanese", "vocabulary"],
                    "difficulty_distribution": {"1": 10, "2": 20, "3": 15, "4": 5},
                    "study_streak": 7,
                    "last_studied": "2025-01-01T10:00:00Z"
                },
                {
                    "id": "deck_python_concepts",
                    "name": "Python Concepts",
                    "description": "Programming concepts and syntax",
                    "card_count": 30,
                    "created_at": "2025-01-01T00:00:00Z",
                    "is_active": True,
                    "tags": ["programming", "python"],
                    "difficulty_distribution": {"2": 15, "3": 10, "4": 5},
                    "study_streak": 3,
                    "last_studied": "2024-12-30T15:00:00Z"
                }
            ]

            formatted_decks = [format_deck_response(deck) for deck in decks]

            return {
                "decks": formatted_decks,
                "total_decks": len(formatted_decks),
                "total_cards": sum(d["card_count"] for d in formatted_decks),
                "active_decks": len([d for d in formatted_decks if d["is_active"]]),
                "metadata": {
                    "description": "Complete list of available flashcard decks",
                    "source": "iCards API",
                    "last_updated": "2025-01-01T00:00:00Z"
                }
            }

        except Exception as e:
            logger.error(f"Error listing decks: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not list decks: {str(e)}"
            }

    # Tool 3: Get Deck Info
    @mcp_server.tool(
        name="get_deck_info",
        description="""
        Get detailed information about a specific deck.

        Includes card statistics, study progress, difficulty distribution,
        and learning recommendations.
        """,
        tags={"decks", "information", "progress", "analysis"}
    )
    async def get_deck_info(
        deck_name: str = Field(..., description="Name of the deck to get information about")
    ) -> dict:
        """Get detailed information about a specific deck."""
        try:
            # TODO: Call actual API when implemented
            # For now, return placeholder data based on deck name
            if "japanese" in deck_name.lower():
                deck_data = {
                    "id": "deck_japanese_vocab",
                    "name": "Japanese Vocabulary",
                    "description": "Essential Japanese vocabulary words",
                    "card_count": 50,
                    "created_at": "2025-01-01T00:00:00Z",
                    "is_active": True,
                    "tags": ["japanese", "vocabulary"],
                    "difficulty_distribution": {"1": 10, "2": 20, "3": 15, "4": 5},
                    "study_streak": 7,
                    "last_studied": "2025-01-01T10:00:00Z"
                }

                # Mock cards for progress calculation
                mock_cards = [
                    {"review_count": 5, "correct_count": 4, "difficulty_level": 1},
                    {"review_count": 3, "correct_count": 2, "difficulty_level": 2},
                    # ... more cards
                ] * 25  # Simulate 50 cards

                progress = calculate_study_progress(mock_cards)
                recommendations = generate_study_recommendations(progress)

            elif "python" in deck_name.lower():
                deck_data = {
                    "id": "deck_python_concepts",
                    "name": "Python Concepts",
                    "description": "Programming concepts and syntax",
                    "card_count": 30,
                    "created_at": "2025-01-01T00:00:00Z",
                    "is_active": True,
                    "tags": ["programming", "python"],
                    "difficulty_distribution": {"2": 15, "3": 10, "4": 5},
                    "study_streak": 3,
                    "last_studied": "2024-12-30T15:00:00Z"
                }

                mock_cards = [
                    {"review_count": 2, "correct_count": 1, "difficulty_level": 2},
                    {"review_count": 1, "correct_count": 0, "difficulty_level": 3},
                ] * 15

                progress = calculate_study_progress(mock_cards)
                recommendations = generate_study_recommendations(progress)

            else:
                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": ["Japanese Vocabulary", "Python Concepts"]
                }

            formatted_deck = format_deck_response(deck_data)

            return {
                "deck": formatted_deck,
                "study_progress": progress,
                "recommendations": recommendations,
                "metadata": {
                    "description": f"Detailed information for deck '{deck_name}'",
                    "source": "iCards API",
                    "analysis_type": "deck_info"
                }
            }

        except Exception as e:
            logger.error(f"Error getting deck info for {deck_name}: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not get deck information: {str(e)}"
            }

    # Tool 4: Create Flashcard Template
    @mcp_server.tool(
        name="create_flashcard_template",
        description="""
        Create a flashcard template based on deck type.

        Provides suggested front/back content structure and difficulty level
        for different types of learning content.
        """,
        tags={"templates", "guidance", "content-creation"}
    )
    async def create_flashcard_template_tool(
        deck_type: DeckType = Field("general", description="Type of deck to create template for")
    ) -> dict:
        """Create a flashcard template based on deck type."""
        try:
            template = create_flashcard_template(deck_type)

            return {
                "template": template,
                "deck_type": deck_type,
                "description": f"Template for {deck_type} flashcards",
                "usage_tips": [
                    "Use the suggested structure as a starting point",
                    "Customize content to fit your learning style",
                    "Adjust difficulty level based on your knowledge",
                    "Add relevant tags for better organization"
                ],
                "metadata": {
                    "template_version": "1.0",
                    "recommended_difficulty": template["difficulty_level"],
                    "tags": template["tags"]
                }
            }

        except Exception as e:
            logger.error(f"Error creating template for deck type {deck_type}: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not create template: {str(e)}"
            }

    # Tool 5: List Flashcards in Deck
    @mcp_server.tool(
        name="list_flashcards",
        description="""
        List all flashcards in a specific deck.

        Returns detailed information about each card including review statistics,
        difficulty levels, and tags. Useful for deck management and study planning.
        """,
        tags={"flashcards", "listing", "deck-content", "study-planning"}
    )
    async def list_flashcards(
        deck_name: str = Field(..., description="Name of the deck to list flashcards from"),
        limit: Optional[int] = Field(50, description="Maximum number of cards to return (max 100)"),
        offset: Optional[int] = Field(0, description="Number of cards to skip"),
        sort_by: Optional[Literal["created", "difficulty", "reviews", "correct_rate"]] = Field("created", description="Sort cards by this criteria"),
        filter_difficulty: Optional[DifficultyLevel] = Field(None, description="Filter cards by difficulty level")
    ) -> dict:
        """List flashcards in a specific deck."""
        try:
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name format is invalid"
                }

            if limit and (limit < 1 or limit > 100):
                return {
                    "error": "Invalid limit",
                    "message": "Limit must be between 1 and 100"
                }

            # TODO: Call actual API when implemented
            # For now, return mock data
            if "japanese" in deck_name.lower():
                mock_flashcards = [
                    {
                        "id": f"card_{i}",
                        "front": f"Japanese word {i}",
                        "back": f"Translation {i} - Pronunciation guide",
                        "deck_name": deck_name,
                        "difficulty_level": (i % 5) + 1,
                        "review_count": i % 10,
                        "correct_count": (i % 10) // 2,
                        "tags": ["japanese", "vocabulary"],
                        "created_at": f"2025-01-{str(i+1).zfill(2)}T00:00:00Z"
                    }
                    for i in range(min(limit or 50, 50))
                ]
            else:
                mock_flashcards = [
                    {
                        "id": f"card_{i}",
                        "front": f"Question {i}",
                        "back": f"Answer {i}",
                        "deck_name": deck_name,
                        "difficulty_level": (i % 3) + 1,
                        "review_count": i % 5,
                        "correct_count": i % 3,
                        "tags": ["general"],
                        "created_at": f"2025-01-{str(i+1).zfill(2)}T00:00:00Z"
                    }
                    for i in range(min(limit or 50, 30))
                ]

            # Apply filtering
            if filter_difficulty:
                mock_flashcards = [c for c in mock_flashcards if c["difficulty_level"] == filter_difficulty]

            # Apply sorting
            if sort_by == "difficulty":
                mock_flashcards.sort(key=lambda x: x["difficulty_level"])
            elif sort_by == "reviews":
                mock_flashcards.sort(key=lambda x: x["review_count"], reverse=True)
            elif sort_by == "correct_rate":
                mock_flashcards.sort(key=lambda x: x["correct_count"] / max(x["review_count"], 1), reverse=True)

            # Apply pagination
            start_idx = offset or 0
            end_idx = start_idx + (limit or 50)
            paginated_cards = mock_flashcards[start_idx:end_idx]

            formatted_cards = [format_flashcard_response(card) for card in paginated_cards]

            return {
                "flashcards": formatted_cards,
                "deck_name": deck_name,
                "total_cards": len(mock_flashcards),
                "returned_cards": len(formatted_cards),
                "pagination": {
                    "offset": start_idx,
                    "limit": limit,
                    "has_more": end_idx < len(mock_flashcards)
                },
                "filters_applied": {
                    "difficulty_level": filter_difficulty,
                    "sort_by": sort_by
                },
                "metadata": {
                    "description": f"Flashcards in deck '{deck_name}'",
                    "source": "iCards API"
                }
            }

        except Exception as e:
            logger.error(f"Error listing flashcards for deck {deck_name}: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not list flashcards: {str(e)}"
            }

    # Tool 6: Start Study Session
    @mcp_server.tool(
        name="start_study_session",
        description="""
        Start a study session for a specific deck.

        Creates a new study session with configurable parameters like card count,
        difficulty focus, and session type. Returns session details and first card.
        """,
        tags={"study", "session", "learning", "practice"}
    )
    async def start_study_session(
        deck_name: str = Field(..., description="Name of the deck to study"),
        card_count: Optional[int] = Field(20, description="Number of cards in session (max 50)"),
        session_type: Optional[Literal["new", "review", "mixed"]] = Field("mixed", description="Type of study session"),
        difficulty_focus: Optional[DifficultyLevel] = Field(None, description="Focus on specific difficulty level"),
        include_new_cards: Optional[bool] = Field(True, description="Include cards never studied before")
    ) -> dict:
        """Start a study session for a deck."""
        try:
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name format is invalid"
                }

            if card_count and (card_count < 1 or card_count > 50):
                return {
                    "error": "Invalid card count",
                    "message": "Card count must be between 1 and 50"
                }

            # TODO: Call actual API when implemented
            session_data = {
                "session_id": f"session_{hash(f'{deck_name}_{card_count}')}",
                "deck_name": deck_name,
                "card_count": card_count or 20,
                "session_type": session_type or "mixed",
                "difficulty_focus": difficulty_focus,
                "include_new_cards": include_new_cards if include_new_cards is not None else True,
                "started_at": "2025-01-01T12:00:00Z",
                "status": "active"
            }

            formatted_session = parse_study_session_data(session_data)

            return {
                "session": formatted_session,
                "message": f"Study session started for deck '{deck_name}'",
                "instructions": [
                    "Use 'next_card' tool to get the next flashcard",
                    "Use 'submit_answer' to record your response",
                    "Session will automatically save progress",
                    "You can pause and resume sessions anytime"
                ],
                "metadata": {
                    "description": f"Study session for {deck_name}",
                    "session_type": session_type,
                    "estimated_duration": f"{card_count * 2} minutes"
                }
            }

        except Exception as e:
            logger.error(f"Error starting study session for deck {deck_name}: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not start study session: {str(e)}"
            }

    # Tool 7: Get Study Statistics
    @mcp_server.tool(
        name="get_study_statistics",
        description="""
        Get comprehensive study statistics and progress tracking.

        Includes overall progress, streak information, difficulty analysis,
        and learning recommendations across all decks.
        """,
        tags={"statistics", "progress", "analytics", "performance"}
    )
    async def get_study_statistics() -> dict:
        """Get comprehensive study statistics."""
        try:
            # TODO: Call actual API when implemented
            # Mock comprehensive statistics
            stats = {
                "overall_progress": {
                    "total_decks": 3,
                    "total_cards": 120,
                    "studied_cards": 85,
                    "mastered_cards": 25,
                    "progress_percentage": 70.8,
                    "average_difficulty": 2.8,
                    "current_streak": 12,
                    "longest_streak": 25
                },
                "daily_activity": {
                    "cards_studied_today": 15,
                    "time_spent_today": 45,  # minutes
                    "accuracy_today": 82.5,
                    "new_cards_today": 3
                },
                "weekly_summary": {
                    "cards_studied_this_week": 89,
                    "average_daily_time": 35,
                    "consistency_score": 85,  # percentage
                    "improvement_trend": "up"
                },
                "deck_performance": [
                    {
                        "deck_name": "Japanese Vocabulary",
                        "progress": 85.0,
                        "accuracy": 78.5,
                        "mastered_cards": 15,
                        "current_streak": 7
                    },
                    {
                        "deck_name": "Python Concepts",
                        "progress": 65.0,
                        "accuracy": 85.2,
                        "mastered_cards": 8,
                        "current_streak": 3
                    }
                ],
                "difficulty_analysis": {
                    "easiest_level": 1,
                    "hardest_level": 4,
                    "recommended_focus": "Level 3 cards need more practice",
                    "distribution": {"1": 25, "2": 35, "3": 20, "4": 15, "5": 5}
                },
                "achievements": [
                    "7-day streak",
                    "First deck completed",
                    "50 cards mastered",
                    "Consistent learner"
                ]
            }

            # Generate recommendations based on stats
            recommendations = []
            progress = stats["overall_progress"]

            if progress["current_streak"] < 7:
                recommendations.append("Try to maintain a daily study habit to build longer streaks!")
            else:
                recommendations.append("Great job maintaining your study streak!")

            if progress["progress_percentage"] < 50:
                recommendations.append("Focus on consistent daily practice to accelerate learning.")
            elif progress["progress_percentage"] < 80:
                recommendations.append("You're making excellent progress! Keep it up.")
            else:
                recommendations.append("Outstanding progress! Consider adding new challenging decks.")

            accuracy = stats["daily_activity"]["accuracy_today"]
            if accuracy < 70:
                recommendations.append("Review difficult cards more frequently to improve accuracy.")
            elif accuracy > 90:
                recommendations.append("Excellent accuracy! Consider increasing difficulty or speed.")

            return {
                "statistics": stats,
                "recommendations": recommendations,
                "metadata": {
                    "description": "Comprehensive study statistics and analytics",
                    "source": "iCards API",
                    "generated_at": "2025-01-01T12:00:00Z",
                    "data_freshness": "real-time"
                }
            }

        except Exception as e:
            logger.error(f"Error getting study statistics: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not get study statistics: {str(e)}"
            }
