# Tabbed Code

Renders multiple code snippets organized inside an interactive, multi-tab container component.

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
| tabs | array. Collection of objects containing the language identifier, tab label, and code string. |

## Example payload

```json
{
  "type": "tabbed_code",
  "tabs": [
    {
      "label": "Tab 1",
      "content": "Content one."
    },
    {
      "label": "Tab 2",
      "content": "Content two."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/tabbed_code/
Full field contract: https://a2uicatalog.ai/spec.json
