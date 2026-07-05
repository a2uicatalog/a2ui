"""Flight card molecule — styled flight display for Google Chat."""

from typing import Dict, Any


def flight_card(flight: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flight card molecule — displays a single flight with status, route, and metrics.
    Google Chat Card v2 textParagraph widget with rich formatting.

    Args:
        flight: Dict with callsign, company, origin, destination, aircraft, altitude, speed, status

    Returns:
        Google Chat textParagraph widget dict
    """
    callsign = flight.get("callsign", "—")
    company = flight.get("company", "—")
    origin = flight.get("origin", "—")
    dest = flight.get("destination", "—")
    aircraft = flight.get("aircraft", "—")
    alt = int((flight.get("altitude", 0) or 0) / 100)
    speed = int(flight.get("speed", 0) or 0)
    status = flight.get("status", "—")

    status_emoji = {
        "Descending": "🔻",
        "Approach": "📍",
        "Final": "🎯",
        "Landing": "🛬",
        "Holding": "⏳",
        "En Route": "✈️",
    }.get(status, "✈️")

    text = f"""<b>{status_emoji} {callsign}</b> • {company}
{origin} ➔ {dest} ({aircraft})
Alt: {alt}00m | Speed: {speed}kt | {status}"""

    return {"textParagraph": {"text": text}}
