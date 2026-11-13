# Parallax Card

A card with CSS perspective and a mousemove JavaScript handler that rotates the card along both axes in response to cursor position, creating a 3D parallax tilt effect. Text layers use translateZ to create depth separation. Requires a minimal inline script.

## Surfaces

web, google-apps-script-side-panel, mcp-apps, android

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
| title | string (optional). Card heading. |
| body | string (optional). Card body text. |
| badge | string (optional). Small pill badge above the title. |
| accent | string (optional). Badge background colour. Default "#4f46e5". |
| background | string (optional). Card background. Default "#0f172a". |
| depth | integer (optional). Maximum tilt angle in degrees. Default 15. |

## Example payload

```json
{
  "type": "parallax_card"
}
```

Live page: https://a2uicatalog.ai/atoms/parallax_card/
Full field contract: https://a2uicatalog.ai/spec.json
