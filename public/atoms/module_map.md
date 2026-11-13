# Module Map

Visual curriculum grid showing all modules in a course. Each card displays module icon, title, description, duration, and a live status badge (locked/Start/Done) driven by progress_store. Locked modules are greyed out. Completed modules turn green. Cards navigate to module url on click.

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
| Flutter | Not measured | 2026-11-13 | example payload invalid, atom untested |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional). Section heading. Default "Course Modules". |
| columns | integer (optional). Grid columns, max 4. Default 3. |
| modules | array (required). Array of module objects. Each module supports: id (string, required), title, description, icon, duration, lessons, required[] (array of module ids that must be complete to unlock), and either: page (array of atom blocks, PREFERRED — auto-encoded into a self-contained URL at render time, no separate save needed) or url (string — only for external URLs or pre-saved nav pages). Always use page for inline module content. |

## Example payload

```json
{
  "type": "module_map",
  "modules": 1
}
```

Live page: https://a2uicatalog.ai/atoms/module_map/
Full field contract: https://a2uicatalog.ai/spec.json
