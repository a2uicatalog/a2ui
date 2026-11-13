# Skill Bars

List of labeled horizontal progress bars — each with a fill percentage, optional sublabel, and per-bar color. Use for competency profiles, CV pages, feature comparison.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps, android, slides, pptx

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
| title | string (optional) |
| accent | string (optional, default hex for all bars) |
| style | string (optional, "rounded"|"square", default "rounded") |
| height | integer (optional, bar height in px, default 10) |
| show_percent | bool (optional, default true) |
| skills | array (required, alias items). Each: {label, value (0–100, alias percent), color?, sublabel?} |

## Example payload

```json
{
  "type": "skill_bars",
  "skills": [
    {
      "label": "Python",
      "value": 85
    },
    {
      "label": "JavaScript",
      "value": 70
    },
    {
      "label": "TypeScript",
      "value": 65
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/skill_bars/
Full field contract: https://a2uicatalog.ai/spec.json
