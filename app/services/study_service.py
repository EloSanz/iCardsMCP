"""Study service for iCards MCP server."""

import logging
from typing import Dict, Any, List, Optional

from .base_service import BaseService

logger = logging.getLogger(__name__)


class StudyService(BaseService):
    """Service for study session operations using iCards REST API."""

    _instance = None

    def __init__(self):
        """Initialize the study service."""
        super().__init__()

    @classmethod
    def get_instance(cls):
        """Get singleton instance of StudyService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start_study_session(
        self,
        deck_id: int,
        card_count: int = 20,
        session_type: str = "mixed",
        difficulty_focus: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Start a new study session.

        Args:
            deck_id: The deck ID to study.
            card_count: Number of cards in the session.
            session_type: Type of session (new, review, mixed).
            difficulty_focus: Focus on specific difficulty level.

        Returns:
            Session data including session ID and first card.
        """
        logger.debug(f"Starting study session for deck {deck_id}")
        try:
            data = {
                "deck_id": deck_id,
                "card_count": card_count,
                "session_type": session_type
            }
            if difficulty_focus:
                data["difficulty_focus"] = difficulty_focus

            return await self._post("/api/study/start", data)
        except Exception as e:
            logger.error(f"Error starting study session: {str(e)}")
            raise

    async def get_next_card(self, session_id: str) -> Dict[str, Any]:
        """
        Get the next card in a study session.

        Args:
            session_id: The study session ID.

        Returns:
            Next flashcard data.
        """
        logger.debug(f"Getting next card for session {session_id}")
        try:
            return await self._get(f"/api/study/{session_id}/next")
        except Exception as e:
            logger.error(f"Error getting next card for session {session_id}: {str(e)}")
            raise

    async def submit_answer(
        self,
        session_id: str,
        card_id: int,
        answer_quality: int,
        time_spent: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Submit an answer for a flashcard.

        Args:
            session_id: The study session ID.
            card_id: The flashcard ID.
            answer_quality: Quality of the answer (1-5 scale).
            time_spent: Time spent on the card in seconds.

        Returns:
            Review result and next card info.
        """
        logger.debug(f"Submitting answer for card {card_id} in session {session_id}")
        try:
            data = {
                "card_id": card_id,
                "answer_quality": answer_quality
            }
            if time_spent:
                data["time_spent"] = time_spent

            return await self._post(f"/api/study/{session_id}/answer", data)
        except Exception as e:
            logger.error(f"Error submitting answer: {str(e)}")
            raise

    async def end_study_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a study session.

        Args:
            session_id: The study session ID.

        Returns:
            Session summary and statistics.
        """
        logger.debug(f"Ending study session {session_id}")
        try:
            return await self._post(f"/api/study/{session_id}/end")
        except Exception as e:
            logger.error(f"Error ending study session {session_id}: {str(e)}")
            raise

    async def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """
        Get progress information for a study session.

        Args:
            session_id: The study session ID.

        Returns:
            Progress data including cards studied, accuracy, etc.
        """
        logger.debug(f"Getting progress for session {session_id}")
        try:
            return await self._get(f"/api/study/{session_id}/progress")
        except Exception as e:
            logger.error(f"Error getting session progress: {str(e)}")
            raise

    async def pause_study_session(self, session_id: str) -> Dict[str, Any]:
        """
        Pause a study session.

        Args:
            session_id: The study session ID.

        Returns:
            Pause confirmation.
        """
        logger.debug(f"Pausing study session {session_id}")
        try:
            return await self._post(f"/api/study/{session_id}/pause")
        except Exception as e:
            logger.error(f"Error pausing study session: {str(e)}")
            raise

    async def resume_study_session(self, session_id: str) -> Dict[str, Any]:
        """
        Resume a paused study session.

        Args:
            session_id: The study session ID.

        Returns:
            Resume confirmation and current card.
        """
        logger.debug(f"Resuming study session {session_id}")
        try:
            return await self._post(f"/api/study/{session_id}/resume")
        except Exception as e:
            logger.error(f"Error resuming study session: {str(e)}")
            raise

    async def get_study_statistics(self, deck_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive study statistics.

        Args:
            deck_id: Optional deck filter.

        Returns:
            Study statistics including progress, streaks, etc.
        """
        logger.debug(f"Getting study statistics for deck: {deck_id}")
        try:
            params = {}
            if deck_id:
                params["deck_id"] = deck_id

            return await self._get("/api/study/statistics", params)
        except Exception as e:
            logger.error(f"Error getting study statistics: {str(e)}")
            raise

    async def get_due_cards(self, deck_id: Optional[int] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Get cards that are due for review.

        Args:
            deck_id: Optional deck filter.
            limit: Maximum number of cards to return.

        Returns:
            List of due cards.
        """
        logger.debug(f"Getting due cards for deck: {deck_id}, limit: {limit}")
        try:
            params = {"limit": limit}
            if deck_id:
                params["deck_id"] = deck_id

            return await self._get("/api/study/due", params)
        except Exception as e:
            logger.error(f"Error getting due cards: {str(e)}")
            raise

    async def generate_study_plan(
        self,
        deck_id: int,
        days: int = 7,
        daily_cards: int = 20
    ) -> Dict[str, Any]:
        """
        Generate a study plan for a deck.

        Args:
            deck_id: The deck ID.
            days: Number of days for the plan.
            daily_cards: Cards to study per day.

        Returns:
            Generated study plan.
        """
        logger.debug(f"Generating study plan for deck {deck_id}")
        try:
            data = {
                "deck_id": deck_id,
                "days": days,
                "daily_cards": daily_cards
            }
            return await self._post("/api/study/plan", data)
        except Exception as e:
            logger.error(f"Error generating study plan: {str(e)}")
            raise
