# Atom Anatomy

Side-by-side panel showing a rendered atom alongside its raw JSON schema

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
| label | string (optional, panel header) |
| schema | object (atom block JSON to render and display) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "atom_anatomy",
  "schema": "{\"type\": \"example\", \"value\": \"1,234\"}"
}
```

Live page: https://a2uicatalog.ai/atoms/atom_anatomy/
Full field contract: https://a2uicatalog.ai/spec.json
