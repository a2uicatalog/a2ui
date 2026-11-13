# Accordion Item

Renders a single section of content that can be expanded or collapsed

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
| header | string The title or label for the collapsible section. |
| content | string The main content to be shown or hidden. |

## Example payload

```json
{
  "type": "accordion_item",
  "header": "Section Header",
  "content": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/accordion_item/
Full field contract: https://a2uicatalog.ai/spec.json
