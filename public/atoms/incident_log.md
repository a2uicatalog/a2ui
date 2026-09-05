# Incident Log

Recent-history companion to service_status_board — a 7-cell week strip (count + severity tint per day) above a short list of incident rows (service, one-line summary, severity stripe, duration, ongoing state).

## Surfaces

google-chat-chromium-render

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'LAST 7 DAYS — INCIDENT LOG') |
| stamp | string (optional, e.g., '13 – 19 Jul') |
| week | list of exactly 7 dicts, oldest to newest: [{label: string (e.g. "Mon"), count: integer, severity: one of none|low|medium}, ...] |
| incidents | list of up to 4 dicts, most recent first: [{service: string, summary: string, severity: one of low|medium|high, duration: string (e.g. "3h 10m"), when: string (e.g. "Sun 19"), ongoing: boolean}, ...] |

## Example payload

```json
{
  "type": "incident_log",
  "week": 1,
  "incidents": true
}
```

Live page: https://a2uicatalog.ai/atoms/incident_log/
Full field contract: https://a2uicatalog.ai/spec.json
