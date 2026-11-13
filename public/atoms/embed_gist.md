# Embed Gist

Displays an inline styled snippet view of remote code from GitHub Gists.

## Surfaces

web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| gist_id | string. Hexadecimal identifier for target file fragments. |

## Example payload

```json
{
  "type": "embed_gist",
  "gist_id": "Gist id"
}
```

Live page: https://a2uicatalog.ai/atoms/embed_gist/
Full field contract: https://a2uicatalog.ai/spec.json
