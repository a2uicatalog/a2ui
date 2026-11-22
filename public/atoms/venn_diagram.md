# Venn Diagram

Two circles with the first set, the shared items and the second set, up to four items each; or, when set_c_name is given, three fixed circles with items in all seven regions (each set alone, each pair, all three). Motion-ready: every moving value reads --p (build progress 0 to 1, default 1) through a per-item --k, so a motion_timeline track on p builds it item by item and the standalone render is the finished picture; reduced motion shows the end state.

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
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not measured | 2026-11-13 | no example payload in the gate data |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| set_a_name | string (required, max 28). |
| set_b_name | string (required, max 28). |
| set_a_exclusive | array (up to 4 strings, max 28) only in A. |
| set_b_exclusive | array (up to 4 strings, max 28) only in B. |
| intersection | array (up to 4 strings, max 28) in A and B. With a third set it means A and B only, not C. |
| set_c_name | string (optional, max 28). Giving it switches to the three-set drawing; without it the two-set drawing is unchanged. |
| set_c_exclusive | array (optional, three-set only) of strings, only in C. |
| intersection_ac | array (optional, three-set only) of strings, in A and C but not B. |
| intersection_bc | array (optional, three-set only) of strings, in B and C but not A. |
| intersection_abc | array (optional, three-set only) of strings, in all three. |
| version | integer (optional, default 1). Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "venn_diagram",
  "title": "Core competencies",
  "set_a_name": "Product management",
  "set_b_name": "Technical leadership",
  "set_a_exclusive": [
    "Market research",
    "Roadmap priorities"
  ],
  "set_b_exclusive": [
    "System design",
    "Code review"
  ],
  "intersection": [
    "Sprint planning",
    "Feature scoping"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/venn_diagram/
Full field contract: https://a2uicatalog.ai/spec.json
