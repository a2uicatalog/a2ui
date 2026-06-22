# Perplexity Batch Prompt — Blog Premium Atoms (Batch 2+)

## Status

| Batch | Atoms | Done |
|---|---|---|
| Original catalogue | 101 | ✅ |
| Batch 2 — Code Part A | +8 | ✅ |
| Batch 3 — Code Part B + Content Structure | +15 | ✅ |
| Batch 4 — Content Structure + Social | +15 | ✅ |
| **Total so far** | **139** | |
| Batch 5 — Embeds + Data Viz + Interactive (35 atoms) | +35 | ⬜ |
| Batch 6 — Reach 200 (~26 atoms) | +26 | ⬜ |
| **Target** | **200** | |

---

## How to use

Paste the prompt below into Perplexity with a batch list substituted for `[BATCH]`.
Paste output back to Claude — validation, renderers, and tests run automatically.

---

## The Prompt

```
I am building a YAML atom catalogue for a tech blog renderer.
Each atom is a typed content block an AI agent can emit to build rich articles.

Search UIverse.io and common design systems (Tailwind UI, Flowbite, shadcn/ui)
for visual implementations of these atom types: [BATCH]

For EACH atom, return ONLY a YAML block in exactly this format — no prose, no explanation:

- type: [snake_case_name]
  description: [One sentence. What it renders. Not how.]
  compact_description: [MAXIMUM 10 tokens. Intent-focused. Cut articles and prepositions if needed.]
  surfaces:
    works_on:
      - web
    degraded_on:
      - surface: meet-stage
        note: [why it degrades, or omit block entirely if it works fine]
      - surface: googlechat
        note: [reason]
      - surface: email
        note: [reason]
  fields:
    [field_name]: [type and short description]
  source:
    name: [UIverse.io community | a2ui | shadcn/ui | Flowbite]
    url: [IMPORTANT: only use a UIverse/shadcn/Flowbite URL if you found the ACTUAL component page — if you cannot find a specific component URL on that platform, set name to a2ui and url to https://github.com/curtiskrygier/a2ui]
    license: MIT

Rules:
- works_on must always include "web"
- If a field accepts an enum, list options inline: e.g. "string: low | medium | high"
- compact_description is 10 tokens MAX — semantic intent only, no CSS or implementation detail
- Source URL must be a real direct link to the component — never use a platform homepage as the URL if you don't have the specific component link; fall back to a2ui instead
- Output YAML only — no markdown fences, no prose, no explanations between atoms
- Process all atoms in the batch — do not stop early
```

---

## Batch Lists

### Batch 2 — Code Part A ✅ DONE
```
terminal_block, file_tree, tabbed_code, http_request_block,
env_var_list, prerequisite_checklist, keyboard_shortcut, api_param_table
```

### Batch 3 — Code Part B + Content Structure ✅ DONE
```
version_badge, deprecation_notice, experimental_banner, cli_command,
copy_code_button, log_output, json_tree_viewer,
key_takeaways, summary_box, learning_objectives, changelog_entry,
release_notes, further_reading, resources_list, sidebar_note
```

### Batch 4 — Content Structure + Social ✅ DONE
```
difficulty_badge, caution_block, checklist_interactive, glossary_inline,
time_estimate, progress_checkpoint,
social_share_bar, newsletter_cta, author_bio_card, related_posts_grid,
series_overview_card, reaction_group, share_quote, follow_cta, follow_button
```

### Batch 5 — Embeds + Data Viz + Interactive (35 atoms) ⬜ NEXT
```
embed_codepen, embed_stackblitz, embed_gist, embed_tweet,
embed_google_slides, lottie_animation, figma_embed,
chartjs_bar, chartjs_line, mini_sparkline_set, data_table_sortable,
benchmark_comparison, uptime_timeline, metric_comparison_card, status_dashboard,
image_comparison_slider, color_swatch_grid, copy_to_clipboard,
notification_badge, expandable_list, poll_block,
inline_code_annotation, step_counter, word_count_badge, highlight_reel,
footnote_group, abbr_tooltip, reading_level_badge, dark_mode_toggle,
command_palette, search_result_card, live_demo_embed,
post_metadata_bar, reading_progress_bar, table_of_contents
```

### Batch 6 — Reach 200 (~26 atoms) ⬜
```
article_hero, scroll_to_top, updated_timestamp, reading_time_badge,
article_series_nav, print_button, save_to_pocket, rss_subscribe_button,
sponsor_card, buy_me_a_coffee, toc_floating, back_to_top_fab,
code_playground, output_preview, diff_viewer, git_blame_strip,
dependency_badge, build_status_badge, license_badge, npm_badge,
open_graph_preview, schema_org_snippet, seo_meta_preview,
breadcrumb_with_meta, site_search_bar, tag_filter_bar
```

---

## After running Perplexity

1. Paste raw output directly into the chat with Claude
2. Claude validates, normalises, checks for duplicates, adds renderers, runs tests
3. Clean commit per batch

---

## Quality checks (Claude runs automatically)

- `compact_description` ≤ 10 tokens, intent-focused, no CSS
- All atoms have `works_on: [web]`
- No duplicate `type` names vs existing schema
- Source URL is a real component link, not a platform homepage
- Renderer stub added to `web_article.py` for every new atom
- All tests passing before commit
