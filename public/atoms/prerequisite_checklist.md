# Prerequisite Checklist

Renders a callout box highlighting required tools, knowledge, or setups needed before starting a guide.

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
| title | string. Custom header text for the prerequisite warning block. |
| items | array. Strings containing descriptions of individual setup requirements. |

## Example payload

```json
{
  "type": "prerequisite_checklist",
  "title": "Prerequisite Checklist",
  "items": [
    {
      "label": "First item"
    },
    {
      "label": "Second item"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/prerequisite_checklist/
Full field contract: https://a2uicatalog.ai/spec.json
