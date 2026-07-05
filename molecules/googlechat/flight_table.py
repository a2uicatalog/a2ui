"""Flight table molecule — formatted arrivals/departures table for Google Chat."""

from typing import List, Dict, Any


def flight_table(flights: List[Dict[str, Any]], title: str = "ARRIVALS BOARD") -> Dict[str, Any]:
    """
    Flight table molecule — ASCII formatted table of flights with box-drawing characters.
    Google Chat Card v2 textParagraph widget.

    Args:
        flights: List of flight dicts (callsign, company, origin, destination, status, etc.)
        title: Table title (e.g., "ARRIVALS BOARD", "DEPARTURES")

    Returns:
        Google Chat textParagraph widget with formatted ASCII table
    """
    lines = [f"🛬 TOULOUSE BLAGNAC (TLS) — {title}\n"]
    lines.append("╔════════════════════════════════════════════════════════════════════╗")
    lines.append("║ AIRLINE              FLT#      ROUTE        DEP      ETA      STATUS ║")
    lines.append("╠════════════════════════════════════════════════════════════════════╣")

    for flight in flights[:5]:
        airline = flight.get("company", "?")[:18].ljust(18)
        callsign = flight.get("callsign", "?")[:8].ljust(8)
        origin = flight.get("origin", "?")
        dest = flight.get("destination", "?")
        route = f"{origin}→{dest}".ljust(12)
        dep = flight.get("dep_time", "?")[:5]
        eta = flight.get("eta_time", "?")[:5] if flight.get("eta_time") else "—:—"
        status = flight.get("status", "?")[:8].ljust(8)

        line = f"║ {airline} {callsign} {route} {dep}   {eta}   {status}║"
        lines.append(line)

    lines.append("╚════════════════════════════════════════════════════════════════════╝")

    return {"textParagraph": {"text": "\n".join(lines)}}
