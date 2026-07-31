# Parallax Card

A card with CSS perspective and a mousemove JavaScript handler that rotates the card along both axes in response to cursor position, creating a 3D parallax tilt effect. Text layers use translateZ to create depth separation. Requires a minimal inline script.

## Surfaces

web, google-apps-script-side-panel, mcp-apps

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
