# Back Button

Styled back navigation button. Links to a URL, a named page slug, or browser history. Three visual styles.

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
| label | string (optional, default "← Back") |
| url | string (optional, href) |
| nav_slug | string (optional, resolves to ?nav=<slug>) |
| style | string (optional, "ghost"|"outline"|"text", default "ghost") |
| accent | string (optional, hex, default "#4f46e5") |

## Example payload

```json
{
  "type": "back_button"
}
```

Live page: https://a2uicatalog.ai/atoms/back_button/
Full field contract: https://a2uicatalog.ai/spec.json
