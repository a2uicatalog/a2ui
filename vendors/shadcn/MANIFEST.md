# Vendor: shadcn/ui

**Source:** https://ui.shadcn.com / https://github.com/shadcn-ui/ui  
**License:** MIT  
**Atom count:** 12  
**Attribution:** Atoms in this set are adapted from shadcn/ui component patterns. shadcn/ui provides unstyled, composable React components built on Radix UI primitives. Adaptations extract the semantic content model from each component's props and convert to A2UI's field schema; rendering is recompiled from scratch into `web_article.py` (no Radix, no Tailwind, no React required).

## Why

shadcn/ui's component set includes several developer-documentation patterns — file trees, tabbed code blocks, API tables, JSON viewers — that are first-class in technical writing but absent from general-purpose UI libraries. These atoms target the code/reference section of technical articles and stage demos.

## Component → atom mapping

| shadcn/ui component | A2UI atom | Adaptation notes |
|---|---|---|
| File-tree (custom / community) | `file_tree` | nodes array with nesting; dirs vs files distinguished |
| Tabs + CodeBlock | `tabbed_code` | tabs array of (label, language, content); CSS tab switch |
| Table (param / reference variant) | `api_param_table` | params: name + type + required + default + description |
| Alert (variant: destructive) | `deprecation_notice` | feature + since version + replacement hint |
| Collapsible + JSON renderer | `json_tree_viewer` | data object; expandable nested tree |
| Card (summary / overview) | `summary_box` | title + bullets; article intro panel |
| Timeline item | `changelog_entry` | version + date + change groups (added/changed/fixed) |
| Aside / callout (neutral) | `sidebar_note` | body text; rendered as off-margin aside |
| Alert (variant: warning + icon) | `caution_block` | title + body; destructive/irreversible-action warning |
| HoverCard (term definition) | `glossary_inline` | term + definition; inline with hover reveal |
| Progress (step variant) | `progress_checkpoint` | steps array + current index |
| Card (series / index variant) | `series_overview_card` | series_title + parts array (title + url + status) |

## Surface notes

`tabbed_code` uses CSS `:checked` tab switching — works on `web` and `meet-stage`, not in email or PDF. `glossary_inline` hover reveal is `web`-only (`:hover` not available in other surfaces; falls back to inline definition text). All other atoms are static and multi-surface compatible.
