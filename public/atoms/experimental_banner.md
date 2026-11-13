# Experimental Banner

Renders a callout box identifying a feature or code path as experimental or unstable.

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| message | string. Context or feedback links for the unstable feature. |

## Example payload

```json
{
  "type": "experimental_banner",
  "message": "Your action was completed successfully."
}
```

Live page: https://a2uicatalog.ai/atoms/experimental_banner/
Full field contract: https://a2uicatalog.ai/spec.json
