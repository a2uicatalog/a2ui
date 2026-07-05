"""Arrivals board molecule — complete Google Chat Card v2 with header and flight cards."""

from typing import List, Dict, Any
from .flight_card import flight_card


class ArrivalsBoard:
    """Builder for complete arrivals board Google Chat cards."""

    def __init__(self, airport_name: str = "TOULOUSE BLAGNAC (TLS)", emoji: str = "🛬"):
        """
        Initialize arrivals board.

        Args:
            airport_name: Display name for airport (default "TOULOUSE BLAGNAC (TLS)")
            emoji: Header emoji (default 🛬)
        """
        self.airport_name = airport_name
        self.emoji = emoji
        self.sections = []

    def add_flight_cards(self, flights: List[Dict[str, Any]]) -> "ArrivalsBoard":
        """Add flight card widgets (one per flight, limit 5)."""
        for flight in flights[:5]:
            card_widget = flight_card(flight)
            self.sections.append({"widgets": [card_widget]})
        return self

    def to_card(self) -> Dict[str, Any]:
        """Convert to Google Chat Card v2 format."""
        return {
            "header": {
                "title": f"{self.emoji} {self.airport_name}",
                "subtitle": "Real-time flight tracking • Updates every 10s"
            },
            "sections": self.sections if self.sections else [{"widgets": []}]
        }

    def to_message(self) -> Dict[str, Any]:
        """Build complete Google Chat message with cardsV2."""
        return {
            "cardsV2": [{"cardId": "1", "card": self.to_card()}]
        }


def arrivals_board(flights: List[Dict[str, Any]],
                   airport_name: str = "TOULOUSE BLAGNAC (TLS)") -> Dict[str, Any]:
    """
    Arrivals board molecule — shorthand for building a complete arrivals card.

    Args:
        flights: List of flight dicts
        airport_name: Airport display name

    Returns:
        Google Chat message dict with cardsV2 format
    """
    board = ArrivalsBoard(airport_name=airport_name)
    board.add_flight_cards(flights)
    return board.to_message()
