# Skeleton

CSS shimmer loading placeholder. skeleton_type choices: text, card, avatar_row, image, list, table.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | no visible text in the example |
| Angular | Not verified | 2026-11-13 | no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | no visible text in the example |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| skeleton_type | text (default), card, avatar_row, image, list, table |
| rows | number of placeholder rows (default 3) |
| cols | number of columns for table type (default 3) |
| height | height for image type (default 200px) |

## Example payload

```json
{
  "type": "skeleton"
}
```

Live page: https://a2uicatalog.ai/atoms/skeleton/
Full field contract: https://a2uicatalog.ai/spec.json
