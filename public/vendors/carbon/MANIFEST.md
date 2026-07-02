# Vendor: IBM Carbon Design System

**Source:** https://github.com/carbon-design-system/carbon (`packages/react/src/components`)
**License:** Apache-2.0
**Atom count:** 3
**Attribution:** Atoms adapt IBM Carbon component prop schemas and data visualisation conventions. Rendering is recompiled into `web_article.py` — no `@carbon/react` runtime dependency.

## Why

Enterprise data-heavy presentations (financial dashboards, infrastructure status, org charts) are a primary Meet-stage use case. Existing atoms `table` and `data_table_sortable` cannot represent Carbon's enterprise grid capabilities. The IBM Carbon benchmark scenario exposed three gaps not covered by any existing atom.

## Component → atom mapping

| Carbon component | A2UI atom | Adaptation notes |
|---|---|---|
| `DataTable` with selection + pagination | `data_grid` | Typed columns (string/number/status/tag), row-selection checkboxes, sortable column indicators, zebra-stripe rows, pagination footer. More capable than `data_table_sortable` |
| `TreeView` | `tree_view` | Recursive hierarchical tree with per-node expand/collapse state, optional icon, optional meta label. Semantically broader than `file_tree` which is file-system specific |
| Carbon AI Applications calendar heatmap | `heatmap_calendar` | Calendar-month grid (months × weeks × days) with date→count data. Distinct from `heatmap` (arbitrary x/y grid) and `github_activity_grid` (year-spanning GitHub format) |

## Surface notes

All three atoms work on `web`, `meet-stage`, and `pdf`. Email degrades (no selection, no sort). Google Chat degrades to plain text for all three. `data_grid` row selection is visual only (CSS checkbox) — data capture requires routing.

## Carbon design language

Carbon uses a distinctive dark-header / light-grid pattern. `data_grid` implements this with a `#161616` title bar when `title` is set, matching Carbon's DataTable toolbar aesthetic. Typography and border values match Carbon's default theme:
- `#161616` — text primary
- `#525252` — text secondary
- `#e0e0e0` — border subtle
- `#f4f4f4` — layer 01 (alternate row background)
- `#0043ce` — interactive (Blue 70)

## tree_view vs file_tree

Use `file_tree` when the hierarchy represents a file system (paths, extensions, directory structure). Use `tree_view` when the hierarchy represents any other recursive structure: org charts, permission trees, category taxonomies, JSON object exploration, BOM hierarchies.
