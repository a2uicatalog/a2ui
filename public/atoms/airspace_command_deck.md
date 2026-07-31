# Airspace Command Deck

Full-viewport Toulouse TMA airspace radar display — canvas radar with animated simulated flights, rotating sweep, VOR beacons, and approach paths. HTML/CSS overlay for crisp chyron title, weather panel, flight list HUD, and scrolling ticker. Driven by the toulouse_airspace.yaml playbook via the ?slide= URL parameter. For the Toulouse demo, prefer routing through Code.js _renderAirspaceSlide() which handles live METAR interpolation.

## Surfaces

google-apps-script-web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| chyron_title | string (optional). Top-left headline overlay. |
| chyron_subtitle | string (optional). Top-left subtitle — supports interpolated METAR tags. |
| ticker_text | string (optional). Scrolling bottom bar text. |
| ticker_speed | integer (optional). Ticker scroll speed px/s. Default 45. |
| panel_type | string (optional). supervisor | target | (empty). Controls HUD flight list panel. |
| panel_title | string (optional). HUD panel heading. |
| lockedCallsign | string (optional). Highlight and add targeting reticle to this callsign. |
| zoom | integer (optional). TMA radius shown in nm. Default 35. |
| height | integer (optional). Canvas height px. Default 520. |
| show_slate | boolean (optional). Render calibration boot slate instead of radar. |
| slate_title | string (optional). Slate heading. |
| slate_description | string (optional). Slate body text. |
| poll_question | string (optional). If set, renders a vote overlay with bar chart. |
| poll_options | array (optional). Array of option strings for the poll. |
| poll_values | array (optional). Array of integer vote counts for each option. |

## Example payload

```json
{
  "type": "airspace_command_deck"
}
```

Live page: https://a2uicatalog.ai/atoms/airspace_command_deck/
Full field contract: https://a2uicatalog.ai/spec.json
