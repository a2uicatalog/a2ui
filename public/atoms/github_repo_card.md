# Github Repo Card

GitHub repo card — fetches live star/fork/language/push data from GitHub API at render time and embeds as self-contained HTML

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
| repo | string |
| label | string |
| description | string |

## Example payload

```json
{
  "type": "github_repo_card",
  "repo": "a2uicatalog/a2ui",
  "label": "Github Repo Card",
  "description": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/github_repo_card/
Full field contract: https://a2uicatalog.ai/spec.json
