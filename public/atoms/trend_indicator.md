# Trend Indicator

Renders a simple visual indicator (e.g., arrow, icon) representing

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| trend_direction | enum (up, down, stable) - determines the icon or arrow direction |
| label | string (descriptive text for the trend, e.g., 'Improving', 'Declining', 'Steady') |
| context | string (optional, additional context, e.g., 'over last 30 days') |
| color | string (optional, hex or named color for the indicator, e.g., 'green' for 'up', 'red' for 'down') |

## Example payload

```json
{
  "type": "trend_indicator",
  "trend_direction": "up",
  "label": "Trend Indicator"
}
```

Live page: https://a2uicatalog.ai/atoms/trend_indicator/
Full field contract: https://a2uicatalog.ai/spec.json
