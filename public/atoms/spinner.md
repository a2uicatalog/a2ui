# Spinner

A simple rotating animation indicating that content is loading or an operation is in progress.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| size | string The size of the spinner (e.g., "small", "medium", "large"). |
| color | string The color of the spinner (e.g., "primary", "gray"). |

## Example payload

```json
{
  "type": "spinner",
  "size": "md",
  "color": "#6366f1"
}
```

Live page: https://a2uicatalog.ai/atoms/spinner/
Full field contract: https://a2uicatalog.ai/spec.json
