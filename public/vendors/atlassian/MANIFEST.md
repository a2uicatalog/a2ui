# Vendor: Atlassian Design System

**Source:** https://atlassian.design (`@atlaskit/` component packages)
**License:** Apache-2.0
**Atom count:** 3
**Attribution:** Atoms adapt Atlassian Design System component schemas and Jira-specific visual conventions. Rendering is recompiled into `web_article.py` — no `@atlaskit` runtime dependency.

## Why

Project management is one of the highest-frequency Meet/Teams use cases. The sprint review runbook existed, but its atoms (`prerequisite_checklist`, `badge_group`) were poor approximations of Jira vocabulary. The benchmark sprint-review scenario exposed three concrete gaps.

## Component → atom mapping

| Atlassian component | A2UI atom | Adaptation notes |
|---|---|---|
| `Card` + `Lozenge` (issue context) | `jira_ticket` | Issue key, type icon (bug/story/task/epic/subtask), summary, status lozenge, priority dot, assignee, description, labels |
| Board view (Jira Software) | `sprint_board` | Kanban columns with name, ticket-count badge, and compact issue cards. Multi-column flex layout; email degrades to stacked lists |
| `Lozenge` | `lozenge` | Atlassian's six semantic appearance variants: default (grey), success (green), removed (red), inprogress (blue), moved (yellow), new (teal). Distinct from A2UI `badge_group` which uses arbitrary colours |

## Surface notes

`jira_ticket` and `lozenge` work on all surfaces (degraded text on Google Chat). `sprint_board` is incompatible with Google Chat and degrades in email (multi-column collapses to sequential column headings + bullet lists).

## Atlassian design tokens used

Colours hardcoded from Atlassian's colour system:
- `#172b4d` — text primary (N800)
- `#5e6c84` — text subdued (N500)
- `#dfe1e6` — border (N30)
- `#f4f5f7` — background (N20)
- `#0052cc` — interactive blue (B400)
- Lozenge backgrounds: exact Atlassian status palette values

## Sprint board runbook

The `sprint_board` atom is the primary atom for the existing sprint review runbook pattern. Replace `prerequisite_checklist` with `sprint_board` for accurate Jira-vocabulary slides. Combine with `jira_ticket` for a selected-issue deep-dive slide and `lozenge` for inline status references in narrative text slides.
