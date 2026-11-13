# Sidebar Note

Displays an off-axis callout block containing peripheral thoughts, caveats, or fun facts.

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
| title | string. The headline for the side note. |
| content | string. The note content. |

## Example payload

```json
{
  "type": "sidebar_note",
  "title": "Sidebar Note",
  "content": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/sidebar_note/
Full field contract: https://a2uicatalog.ai/spec.json
