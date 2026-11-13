# Footnote Group

Renders a numbered list of footnotes at the bottom of an article or section.

## Surfaces

web, email, google-apps-script-web, mcp-apps, android

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
| footnotes | array of {id, text}. Footnote entries. |

## Example payload

```json
{
  "type": "footnote_group",
  "footnotes": [
    {
      "id": 1,
      "text": "Source: Example Report, 2026."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/footnote_group/
Full field contract: https://a2uicatalog.ai/spec.json
