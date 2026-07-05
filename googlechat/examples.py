"""Google Chat molecules — example usage."""

from molecules import flight_card, flight_table, arrivals_board

# Sample flight data
SAMPLE_FLIGHTS = [
    {
        "callsign": "AFR6129",
        "company": "Air France",
        "origin": "ORY",
        "destination": "TLS",
        "aircraft": "A320",
        "altitude": 3500,
        "speed": 250,
        "status": "Descending",
        "dep_time": "19:40",
        "eta_time": "20:51"
    },
    {
        "callsign": "BAW373",
        "company": "British Airways",
        "origin": "LHR",
        "destination": "TLS",
        "aircraft": "B777",
        "altitude": 5000,
        "speed": 350,
        "status": "Approach",
        "dep_time": "18:15",
        "eta_time": "20:53"
    },
    {
        "callsign": "EZY4218",
        "company": "EasyJet",
        "origin": "LGW",
        "destination": "TLS",
        "aircraft": "A320",
        "altitude": 8000,
        "speed": 400,
        "status": "Final",
        "dep_time": "18:45",
        "eta_time": "20:55"
    },
    {
        "callsign": "RYR109B",
        "company": "Ryanair",
        "origin": "STN",
        "destination": "TLS",
        "aircraft": "B737",
        "altitude": 12000,
        "speed": 450,
        "status": "Holding",
        "dep_time": "18:30",
        "eta_time": "21:03"
    },
    {
        "callsign": "DLH11A",
        "company": "Lufthansa",
        "origin": "FRA",
        "destination": "TLS",
        "aircraft": "A330",
        "altitude": 15000,
        "speed": 480,
        "status": "En Route",
        "dep_time": "19:25",
        "eta_time": "21:05"
    }
]


def example_single_flight_card():
    """Example: Single flight card."""
    widget = flight_card(SAMPLE_FLIGHTS[0])
    print("Flight Card Widget:")
    print(widget)


def example_flight_table():
    """Example: Arrivals table."""
    widget = flight_table(SAMPLE_FLIGHTS, title="ARRIVALS BOARD")
    print("Flight Table Widget:")
    print(widget)


def example_arrivals_board():
    """Example: Complete arrivals board card."""
    message = arrivals_board(SAMPLE_FLIGHTS)
    print("Arrivals Board Message (cardsV2):")
    print(message)


if __name__ == "__main__":
    print("=== Google Chat Molecules Examples ===\n")
    example_single_flight_card()
    print("\n" + "="*50 + "\n")
    example_flight_table()
    print("\n" + "="*50 + "\n")
    example_arrivals_board()
