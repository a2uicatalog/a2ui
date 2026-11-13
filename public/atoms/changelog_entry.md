# Changelog Entry

Renders a single timeline entry documenting additions, fixes, or modifications in a software release.

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
| version | string. The release tag or identifier. |
| date | string. The publication date of the changes. |
| changes | array. Objects outlining specific features modified, categorised by type. |

## Example payload

```json
{
  "type": "changelog_entry",
  "version": "1.2.0",
  "date": "2026-06-28",
  "changes": [
    {
      "type": "added",
      "text": "New feature added"
    },
    {
      "type": "fixed",
      "text": "Bug fix applied"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/changelog_entry/
Full field contract: https://a2uicatalog.ai/spec.json
