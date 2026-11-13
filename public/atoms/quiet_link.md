# Quiet Link

A secondary action with no button chrome — centered, small, muted, underlined text — so a screen's ONE primary action (a full-chrome button) stays visually singular. Still a real button underneath, so the standard onClick wire every other clickable atom uses works unchanged.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| text | string (required). |

## Example payload

```json
{
  "type": "quiet_link",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/quiet_link/
Full field contract: https://a2uicatalog.ai/spec.json
