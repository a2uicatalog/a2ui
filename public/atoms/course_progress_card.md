# Course Progress Card

Overall course completion card showing a list of modules with individual progress bars and a top-level aggregate progress ring. Each module row shows its title, lesson count, and percentage complete. Suitable for a course sidebar or dashboard widget.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android

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
| course_title | string. Course name shown at the top of the card. |
| modules | list[{title: string, lessons_total: integer, lessons_done: integer}]. |
| accent | string (optional). Progress fill colour. Default "#4f46e5". |

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
