# Geo Iso Takeoff

Full-viewport isometric 3D canvas animation of an A321neo (or other narrowbody) departing from Toulouse Blagnac (LFBO). Shows rolling takeoff run, rotation, gear retraction, and climb-out against a night-sky grid. HUD overlay shows airline code, aircraft type, and runway. Accent colour auto-selected from airline ICAO (AIB=Airbus blue, EZY=orange, AFR=Air France blue, BAW=British Airways red, DLH=Lufthansa navy, RYR=Ryanair blue). Includes a LIVE RADAR button that opens the airspace_command_deck for LFBO.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). HUD title line. Default "LFBO RWY 32L — A321neo DEPARTURE". |
| airline | string (optional). ICAO airline code for accent colour — AIB, EZY, AFR, BAW, DLH, RYR. Default AIB. |
| aircraft_type | string (optional). ICAO aircraft type code — A21N (A321neo), A320, B738. Default A21N. |

## Example payload

```json
{
  "type": "geo_iso_takeoff"
}
```

Live page: https://a2uicatalog.ai/atoms/geo_iso_takeoff/
Full field contract: https://a2uicatalog.ai/spec.json
