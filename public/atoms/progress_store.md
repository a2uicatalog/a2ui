# Progress Store

Invisible state connector atom — no visual output. Initialises window._A2UI_STORE and dispatches "a2ui:store" CustomEvent. On GAS reads initial state from a Google Sheet at render time and writes back async via google.script.run. On web reads/writes localStorage keyed by course_id. All other LMS atoms read from and write to this shared store. Must appear before any stateful atom on the page.

## Surfaces

google-apps-script-web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| course_id | string (required). Unique course identifier — scopes the Sheet and localStorage key. |

## Example payload

```json
{
  "type": "progress_store",
  "course_id": "course-101"
}
```

Live page: https://a2uicatalog.ai/atoms/progress_store/
Full field contract: https://a2uicatalog.ai/spec.json
