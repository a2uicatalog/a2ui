# Live Vote

Live audience voting: buttons to vote, bar chart results, optional Google Sheets backend

## Surfaces

google-apps-script-web, mcp-apps, android

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
| question | string |
| options | array of strings (vote choices) |
| sheet_url | string (optional, Google Sheet CSV for live tallies) |
| write_url | string (optional, GAS doGet URL to record votes) |
| poll | number (optional, poll interval ms, default 5000) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "live_vote",
  "question": "Which option do you prefer?",
  "options": [
    {
      "label": "Option A",
      "value": "a"
    },
    {
      "label": "Option B",
      "value": "b"
    },
    {
      "label": "Option C",
      "value": "c"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/live_vote/
Full field contract: https://a2uicatalog.ai/spec.json
