# Swimlane

Rows are roles, columns are phases. Each task is a card with a number that gives the order, placed in its role and phase. At most two tasks share a cell. Motion-ready: every moving value reads --p (build progress 0 to 1, default 1) through a per-item --k, so a motion_timeline track on p builds it item by item and the standalone render is the finished picture; reduced motion shows the end state.

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
| roles | array (required, 2 to 4 strings, max 24 each). |
| phases | array (required, 2 to 5 strings, max 24 each). |
| tasks | array (required, up to 12) of {role, phase, task (max 60)}. role and phase must be listed in roles and phases. The list order is the order of the steps and gives the numbers. |

## Example payload

```json
{
  "type": "swimlane",
  "title": "Vulnerability lifecycle",
  "phases": [
    "Triage",
    "Remediation",
    "Verification"
  ],
  "roles": [
    "Security team",
    "Engineering lead",
    "QA"
  ],
  "tasks": [
    {
      "role": "Security team",
      "phase": "Triage",
      "task": "Validate severity and reproduce"
    },
    {
      "role": "Engineering lead",
      "phase": "Remediation",
      "task": "Patch in a feature branch"
    },
    {
      "role": "QA",
      "phase": "Verification",
      "task": "Run regression and fuzz suites"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/swimlane/
Full field contract: https://a2uicatalog.ai/spec.json
