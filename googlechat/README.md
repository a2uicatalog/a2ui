# Google Chat Molecules

Reusable patterns for formatting structured data in Google Chat cards (cardsV2 format).

## Molecules

### `flight_card(flight)` — Single Flight

Displays a single flight with status emoji, route, altitude, and speed.

```python
from googlechat import flight_card

flight = {
    "callsign": "AFR6129",
    "company": "Air France",
    "origin": "ORY",
    "destination": "TLS",
    "aircraft": "A320",
    "altitude": 3500,
    "speed": 250,
    "status": "Descending"
}

widget = flight_card(flight)  # Returns textParagraph widget
```

Status emojis: 🔻 Descending | 📍 Approach | 🎯 Final | 🛬 Landing | ⏳ Holding | ✈️ En Route

### `flight_table(flights, title)` — Arrivals/Departures Table

Formatted ASCII table with box-drawing characters (╔═╗║╚╝).

```python
from googlechat import flight_table

flights = [...]  # List of flight dicts
widget = flight_table(flights, title="ARRIVALS BOARD")
```

Table shows: Airline | Flight# | Route | Departure | ETA | Status (up to 5 flights)

### `arrivals_board(flights, airport_name)` — Complete Card

Full Google Chat Card v2 with header and flight cards.

```python
from googlechat import arrivals_board

flights = [...]
message = arrivals_board(flights, airport_name="TOULOUSE BLAGNAC (TLS)")

# Send to Google Chat webhook
requests.post(webhook_url, json=message)
```

Or use the `ArrivalsBoard` class for more control:

```python
from googlechat import ArrivalsBoard

board = ArrivalsBoard()
board.add_flight_cards(flights)
message = board.to_message()
```

## Integration

These molecules return standard Google Chat widget/message structures that can be posted directly to Google Chat webhooks:

```python
import requests

webhook_url = "https://chat.googleapis.com/v1/spaces/.../messages?key=...&token=..."
message = arrivals_board(flights)
resp = requests.post(webhook_url, json=message)
```

## Flight Data Format

Each flight dict should contain:

- `callsign` (str): Flight callsign (e.g., "AFR6129")
- `company` (str): Airline name (e.g., "Air France")
- `origin` (str): Departure airport code (e.g., "ORY")
- `destination` (str): Arrival airport code (e.g., "TLS")
- `aircraft` (str): Aircraft type (e.g., "A320")
- `altitude` (float): Current altitude in feet
- `speed` (float): Current speed in knots
- `status` (str): Flight status ("Descending", "Approach", "Final", "Landing", "Holding", "En Route")
- `dep_time` (str, optional): Departure time (e.g., "19:40")
- `eta_time` (str, optional): Estimated arrival time (e.g., "20:51")
