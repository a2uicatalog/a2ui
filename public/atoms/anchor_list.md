# Anchor List

A list of links that navigate to specific sections within the current

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
| anchors | list of {label: string, url: string, target_id: string (optional, for in-document navigation on web/pdf)} |

## Example payload

```json
{
  "type": "anchor_list"
}
```

Live page: https://a2uicatalog.ai/atoms/anchor_list/
Full field contract: https://a2uicatalog.ai/spec.json
