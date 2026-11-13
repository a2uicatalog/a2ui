# Stat Pulse

Three hero stat tiles (value, label, delta with tone) above a small trend bar chart with rounded tops and one emphasized "current" bar. A closing figure for any status or activity digest.

## Surfaces

google-chat-chromium-render

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Angular | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., '30-DAY PULSE') |
| stamp | string (optional, e.g., '20 Jun – 19 Jul') |
| stats | list of exactly 3 dicts: [{value: string, label: string, delta: string, tone: one of good|bad|flat}, ...] |
| trend | dict: {bars: list of numbers (max 6), labels: list of strings matching bars length, hot_index: integer index of the bar to emphasize} |

## Example payload

```json
{
  "type": "stat_pulse",
  "stats": [
    {
      "label": "Views",
      "value": "1.2M"
    },
    {
      "label": "Clicks",
      "value": "42K"
    },
    {
      "label": "CTR",
      "value": "3.5%"
    }
  ],
  "trend": 1
}
```

Live page: https://a2uicatalog.ai/atoms/stat_pulse/
Full field contract: https://a2uicatalog.ai/spec.json
