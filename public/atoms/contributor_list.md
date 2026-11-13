# Contributor List

Renders a list of individuals who have contributed to a project or community, with their avatars and roles.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
| contributors | list |
| title | string |

## Example payload

```json
{
  "type": "contributor_list",
  "contributors": [
    {
      "name": "Alice",
      "role": "Developer"
    },
    {
      "name": "Bob",
      "role": "Designer"
    }
  ],
  "title": "Contributor List"
}
```

Live page: https://a2uicatalog.ai/atoms/contributor_list/
Full field contract: https://a2uicatalog.ai/spec.json
