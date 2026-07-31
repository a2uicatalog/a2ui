# Course Progress Card

Overall course completion card showing a list of modules with individual progress bars and a top-level aggregate progress ring. Each module row shows its title, lesson count, and percentage complete. Suitable for a course sidebar or dashboard widget.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| course_title | string. Course name shown at the top of the card. |
| modules | list[{title: string, lessons_total: integer, lessons_done: integer}]. |
| accent | string (optional). Progress fill colour. Default "#6366f1". |

## Example payload

```json
{
  "type": "course_progress_card",
  "course_title": "Course title",
  "modules": 75
}
```

Live page: https://a2uicatalog.ai/atoms/course_progress_card/
Full field contract: https://a2uicatalog.ai/spec.json
