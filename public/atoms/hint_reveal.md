# Hint Reveal

A "Show hint" disclosure button that expands to reveal help text. Built on the HTML details/summary element — no JavaScript required. The summary label toggles between "Show hint" and "Hide hint". Styled with a subtle left-border accent and muted background to visually separate it from body content.

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
| hint | string. The hint text revealed on expand. |
| label | string (optional). Button label. Default "Show hint". |
| accent | string (optional). Left-border and icon colour. Default "#4f46e5". |

## Example payload

```json
{
  "type": "hint_reveal",
  "hint": 1
}
```

Live page: https://a2uicatalog.ai/atoms/hint_reveal/
Full field contract: https://a2uicatalog.ai/spec.json
