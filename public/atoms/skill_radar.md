# Skill Radar

SVG spider/radar chart plotting learner competency levels across multiple skill dimensions. Optional before values render as a dashed polygon overlay for before/after growth comparison. Values are 0-100 per skill.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Chart heading. Default "Skill Profile". |
| accent | string (optional). Fill/stroke colour for current polygon. Default |
| skills | array (required). Array of {label, value (0-100), before? (0-100)} objects. |

## Example payload

```json
{
  "type": "skill_radar",
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

Live page: https://a2uicatalog.ai/atoms/skill_radar/
Full field contract: https://a2uicatalog.ai/spec.json
