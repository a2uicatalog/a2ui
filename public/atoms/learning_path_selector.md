# Learning Path Selector

Path chooser presented at course entry. Shows 2-4 role or level path cards (icon, title, description, duration). Learner clicks to select — selection is stored in progress_store via setPath() and optionally navigates to a path-specific url. Selected path can drive personalised module_map content.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

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
| title | string (optional). Chooser heading. Default "Choose Your Path". |
| intro | string (optional). Introductory text below the heading. |
| paths | array (required). Array of {id, label, description, icon, accent, duration, url?} objects. |

## Example payload

```json
{
  "type": "learning_path_selector",
  "paths": [
    {
      "label": "Beginner Path",
      "steps": []
    },
    {
      "label": "Advanced Path",
      "steps": []
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/learning_path_selector/
Full field contract: https://a2uicatalog.ai/spec.json
