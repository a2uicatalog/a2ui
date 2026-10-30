# Content check v2: 72 cells, 12 run sets, briefs T1-T6

First reviewer, 2026-10-29. Sources: `briefs.json`, the visible-text file and screenshot per cell (`visible-text/`, `screenshots/`), the raw payloads in `../payloads/<set>/<Tn>.json`, the raw replies in `../results/slice-runs/<set>/<Tn>.json`, the test harness renderer (origin/main of 27 Oct 2026) and the atom documentation. No API or network calls. The first reviewer ran local code offline only to re-validate three Direct JSON replies with the same SDK (see H5). Set names in this file are the plain names used in this export (old short codes are listed in the legend at the end).

**How to read the verdicts.** Each cell gets two grades:

- **Rendered**: what a viewer sees on the review page.
- **Payload**: the model's own output judged against the brief, as if the harness, catalogue and renderer had no defects. A reply the validator rejected by mistake is graded on its reply text. A structural model error (unreachable components, invalid syntax) still counts against the model, because a correct A2UI client would not show those components either.

Grades: good = everything the brief asks for is there and correct; minor = complete, with a cosmetic or small content flaw; major = an explicit requirement is missing or wrong; fail = blank, did not compile, or mostly unusable.

Causes: MODEL = wrong or missing content, or a structure or field name the client cannot use. RENDERER = an atom drops or mangles valid input. HARNESS = the test setup (catalogue conversion, the SDK validator or compiler, payload saving, render_payloads.py, or the layout80 pipeline design). When a cell has more than one cause, the first one listed is the main one.

Screenshots were taken at 640 px wide. Five T3 cells have no screenshot (the headless browser hung): oracle-slice-3types__express__gemini-3.5-flash-lite__first-run-timing-invalid__run1, oracle-slice-3types__express__haiku-5-5__run1, oracle-slice-3types__express__haiku-4-5__temp0__hints-v2__run1, oracle-slice-3types__express__sonnet-5-5__temp0__run1 and oracle-slice-3types__elemental__sonnet-5-5__run1. I judged them from the `.txt` file and the payload only; they are marked "(no shot)". All five include a testimonial with an external avatar URL, which fits an image-fetch hang. I did not confirm that.

## 1. Per-cell verdicts (72)

| # | Set | Format / model | Task | Rendered | Payload | Cause | Note |
|---|---|---|---|---|---|---|---|
| 1 | jev-layout-pipeline__run1 | Pipeline / Jev + Flash-Lite | T1 | major | major | HARNESS (pipeline design) | 3 concept sections + worked example present and correct; no quiz: the fixed "lesson" layout has no quiz slot. |
| 2 | jev-layout-pipeline__run1 | Pipeline / Jev + Flash-Lite | T2 | good | good | - | 4 KPI tiles (value, label, arrow, delta) + bar chart; chart is a single series (Mon-Thu), a weak "comparison". |
| 3 | jev-layout-pipeline__run1 | Pipeline / Jev + Flash-Lite | T3 | major | major | HARNESS (pipeline design); MODEL | Hero + headline/subhead + CTA ok; 4 feature columns (Jev picked count 4, brief says 3); no testimonial (layout has no slot). |
| 4 | jev-layout-pipeline__run1 | Pipeline / Jev + Flash-Lite | T4 | fail | fail | HARNESS (pipeline design); MODEL | Renders a KPI dashboard ("System Diagnostics"), not a list of 8 items; there is no list layout, Jev chose "dashboard". |
| 5 | jev-layout-pipeline__run1 | Pipeline / Jev + Flash-Lite | T5 | fail | fail | HARNESS (pipeline design) | Three tiers as feature cards: no prices, no per-tier feature lists, no recommended mark. |
| 6 | jev-layout-pipeline__run1 | Pipeline / Jev + Flash-Lite | T6 | fail | fail | HARNESS (pipeline design) | 4 of 10 cards (counts capped at 4) as heading+body text, no flip; "Reviewed: 0 of 10" is static subtitle text. |
| 7 | oracle-slice-3types__express__haiku-4-5__temp0__hints-v2__run1 | Express / Haiku 4.5 (hints v2, t=0) | T1 | fail | fail | MODEL | Did not compile: `root = [ ... ]` list instead of one root component (Express rule 2). |
| 8 | oracle-slice-3types__express__haiku-4-5__temp0__hints-v2__run1 | Express / Haiku 4.5 (hints v2, t=0) | T2 | major | minor | RENDERER; MODEL | 4 stat_card tiles overlap and clip at 640 px (values cut, 3 deltas hidden); model put the chart as a 5th item in a 4-col grid, so it renders narrow; chart has no title/units. |
| 9 | oracle-slice-3types__express__haiku-4-5__temp0__hints-v2__run1 | Express / Haiku 4.5 (hints v2, t=0) | T3 (no shot) | good | good | - | Text only (no screenshot). Hero+CTA, 3 features, 5-star testimonial, cta_section with 2 buttons. |
| 10 | oracle-slice-3types__express__haiku-4-5__temp0__hints-v2__run1 | Express / Haiku 4.5 (hints v2, t=0) | T4 | fail | fail | MODEL | Did not compile: data binding ($/filterStatus) on static `selected_value` (Express rule 13). |
| 11 | oracle-slice-3types__express__haiku-4-5__temp0__hints-v2__run1 | Express / Haiku 4.5 (hints v2, t=0) | T5 | major | good | RENDERER | 3 tiers + feature lists; `recommended: true` on Professional not shown; price "Custom" renders "$Custom"; CTA labels dropped. |
| 12 | oracle-slice-3types__express__haiku-4-5__temp0__hints-v2__run1 | Express / Haiku 4.5 (hints v2, t=0) | T6 | good | good | - | 10 distinct words with correct definitions, flip deck (1/10), progress bar 0%. |
| 13 | oracle-slice-3types__express__haiku-5-5__run1 | Express / Haiku 5.5 | T1 | fail | fail | MODEL | Did not compile: `root = [header, c1, c2, c3, ex, quiz]` (Express rule 2). |
| 14 | oracle-slice-3types__express__haiku-5-5__run1 | Express / Haiku 5.5 | T2 | major | minor | RENDERER; MODEL | Model chose 2 cols (KPIs \| chart); metric_row clips at half width, 4th tile not visible at 640 px. Deltas carry no numbers ("vs. last month" only). |
| 15 | oracle-slice-3types__express__haiku-5-5__run1 | Express / Haiku 5.5 | T3 (no shot) | good | good | - | Text only (no screenshot). Hero+CTA, 3 features, testimonial (blockquote_with_avatar), CTA button. |
| 16 | oracle-slice-3types__express__haiku-5-5__run1 | Express / Haiku 5.5 | T4 | minor | good | RENDERER; MODEL | 8 items with title, status, detail, team; filter in a narrow left column clips the last option ("Done"). |
| 17 | oracle-slice-3types__express__haiku-5-5__run1 | Express / Haiku 5.5 | T5 | major | good | RENDERER | Tiers + features fine; `recommended: true` on Pro not rendered. |
| 18 | oracle-slice-3types__express__haiku-5-5__run1 | Express / Haiku 5.5 | T6 | good | good | - | 10 cards, flip, progress 0 of 10. |
| 19 | oracle-slice-3types__express__sonnet-5-5__temp0__run1 | Express / Sonnet 5.5 | T1 | good | good | - | 3 concepts with callouts, case-study worked example with model answer, 3-question quiz; facts correct. |
| 20 | oracle-slice-3types__express__sonnet-5-5__temp0__run1 | Express / Sonnet 5.5 | T2 | good | good | - | 4 KPI tiles with deltas and arrows; revenue-vs-target bar chart by quarter, consistent with tile ($128.4K / Q4 128). |
| 21 | oracle-slice-3types__express__sonnet-5-5__temp0__run1 | Express / Sonnet 5.5 | T3 (no shot) | good | good | - | Text only (no screenshot). Model emitted two drafts (duplicate ids in payload); last draft rendered; all 4 parts present. |
| 22 | oracle-slice-3types__express__sonnet-5-5__temp0__run1 | Express / Sonnet 5.5 | T4 | minor | good | RENDERER; MODEL | 8 items, 4 statuses, filter; filter clipped ("Done") in the 2-col layout. |
| 23 | oracle-slice-3types__express__sonnet-5-5__temp0__run1 | Express / Sonnet 5.5 | T5 | major | good | RENDERER | `recommended: true` + badge "Recommended" on Pro not rendered; period/CTA dropped. |
| 24 | oracle-slice-3types__express__sonnet-5-5__temp0__run1 | Express / Sonnet 5.5 | T6 | good | good | - | 10 cards, flip, progress 0%. Copy mentions "rate your confidence" though no rating control exists (trivial). |
| 25 | oracle-slice-3types__express__opus-5-5__run1 | Express / Opus 5.5 | T1 | good | good | - | 3 concepts, timed worked example, 3-question quiz, summary chips; facts correct. |
| 26 | oracle-slice-3types__express__opus-5-5__run1 | Express / Opus 5.5 | T2 | minor | minor | MODEL | Tiles fine; comparison chart mixes $K, K users and % on one axis, so churn/conversion bars are near zero. |
| 27 | oracle-slice-3types__express__opus-5-5__run1 | Express / Opus 5.5 | T3 | fail | fail | MODEL; HARNESS | `root = [hero, features, ...]` list. Compiler marked it valid but emitted no root (same construct is rejected in CTH2/C_haiku T1); harness fell back to the first component: hero only. Features/testimonial/CTA exist but unreachable. |
| 28 | oracle-slice-3types__express__opus-5-5__run1 | Express / Opus 5.5 | T4 | minor | good | RENDERER; MODEL | 8 workstreams, status count chips, meta line; filter clipped ("Done"). |
| 29 | oracle-slice-3types__express__opus-5-5__run1 | Express / Opus 5.5 | T5 | major | good | RENDERER | `recommended` + badge on Pro not rendered. |
| 30 | oracle-slice-3types__express__opus-5-5__run1 | Express / Opus 5.5 | T6 | minor | minor | MODEL; RENDERER | 10 cards with example sentences; progress hard-coded to 30% / "3 of 10 reviewed" while deck is at 1/10; progress_circle value text invisible. |
| 31 | oracle-slice-3types__express__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Express / Gemini 3.5 Flash-Lite | T1 | good | good | - | 3 phases, 4-step worked example, 3-question quiz; facts correct. |
| 32 | oracle-slice-3types__express__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Express / Gemini 3.5 Flash-Lite | T2 | major | good | RENDERER | 4 stat_card tiles in a 4-col grid overlap, values truncated ("12,48", "$48,2"). "Avg Latency ▲ -4.5%" uses up = good. |
| 33 | oracle-slice-3types__express__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Express / Gemini 3.5 Flash-Lite | T3 (no shot) | good | good | - | Text only (no screenshot). Hero+CTA, 3 features, testimonial, cta_section. |
| 34 | oracle-slice-3types__express__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Express / Gemini 3.5 Flash-Lite | T4 | good | good | - | 8 items, title/status/detail/meta, filter with all options visible. |
| 35 | oracle-slice-3types__express__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Express / Gemini 3.5 Flash-Lite | T5 | major | minor | MODEL; RENDERER | Model set root columns cols:3 with one column, so heading + tiers squeeze into 1/3 width and stack vertically (not side by side); `recommended` not rendered. |
| 36 | oracle-slice-3types__express__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Express / Gemini 3.5 Flash-Lite | T6 | good | good | - | 10 CS terms (technical, not general vocabulary), definitions accurate; flip; 0/10 progress. |
| 37 | oracle-slice-3types__elemental__sonnet-5-5__run1 | Elemental / Sonnet 5.5 | T1 | minor | good | HARNESS | All required parts. Worked example body lost: Elemental catalogue renamed concept_rung `body` to `Body`, renderer reads `body`. |
| 38 | oracle-slice-3types__elemental__sonnet-5-5__run1 | Elemental / Sonnet 5.5 | T2 | minor | minor | MODEL | Churn shown ↓ with "+0.4%" (2.8 -> 3.2 is a rise); chart mixes units via ad-hoc scaling ("hundreds", "x10"). |
| 39 | oracle-slice-3types__elemental__sonnet-5-5__run1 | Elemental / Sonnet 5.5 | T3 (no shot) | minor | good | HARNESS | Text only (no screenshot). Hero badge and feature-grid heading lost (`Badge`/`Heading`/`Columns` renamed by catalogue copy). Hero has no button; separate CTA button present. |
| 40 | oracle-slice-3types__elemental__sonnet-5-5__run1 | Elemental / Sonnet 5.5 | T4 | minor | good | RENDERER; MODEL | 8 items, 4 statuses; filter clipped; no page heading (not required). |
| 41 | oracle-slice-3types__elemental__sonnet-5-5__run1 | Elemental / Sonnet 5.5 | T5 | major | good | RENDERER | `recommended`/`highlighted`/badge on Pro not rendered. |
| 42 | oracle-slice-3types__elemental__sonnet-5-5__run1 | Elemental / Sonnet 5.5 | T6 | good | good | - | 10 cards, flip, 0 of 10, tip. |
| 43 | oracle-slice-3types__elemental__haiku-5-5__run1 | Elemental / Haiku 5.5 | T1 | good | good | - | 3 sections (grouped evap+cond / precip+collection / infiltration+runoff+transpiration), worked example, 3 questions; correct. |
| 44 | oracle-slice-3types__elemental__haiku-5-5__run1 | Elemental / Haiku 5.5 | T2 | minor | minor | MODEL | Tiles have arrows but no change numbers; chart values (820-1,330) carry no units next to a $1.24M tile. |
| 45 | oracle-slice-3types__elemental__haiku-5-5__run1 | Elemental / Haiku 5.5 | T3 | minor | good | HARNESS | Hero badge and feature heading lost (catalogue rename); rest complete. |
| 46 | oracle-slice-3types__elemental__haiku-5-5__run1 | Elemental / Haiku 5.5 | T4 | minor | minor | MODEL | Status values shown raw ("in_progress"); "Webhook retry logic - resolved - Failed deliveries are not retried" reads as an open bug. |
| 47 | oracle-slice-3types__elemental__haiku-5-5__run1 | Elemental / Haiku 5.5 | T5 | major | good | RENDERER | `recommended: true` on Pro not rendered. |
| 48 | oracle-slice-3types__elemental__haiku-5-5__run1 | Elemental / Haiku 5.5 | T6 | good | good | - | 10 cards, flip, 0 of 10. |
| 49 | oracle-slice-3types__elemental__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Elemental / Gemini 3.5 Flash-Lite | T1 | major | good | HARNESS | All 3 concepts and the example render with title + takeaway only: explanations sit in `Body`, the field name the Elemental catalogue copy gave the model. Quiz (3) fine. |
| 50 | oracle-slice-3types__elemental__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Elemental / Gemini 3.5 Flash-Lite | T2 | major | minor | RENDERER; MODEL | stat_card overlap/truncation; model omitted `is_up`, renderer defaults to ▲ so "Retention ▲ -0.8%"; benchmark bars Q1-Q3 vs "Q4 Target", no units. |
| 51 | oracle-slice-3types__elemental__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Elemental / Gemini 3.5 Flash-Lite | T3 | fail | fail | MODEL | Did not compile: single-quoted object literal in an attribute (`primary_cta="{ 'label': ... }"`). |
| 52 | oracle-slice-3types__elemental__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Elemental / Gemini 3.5 Flash-Lite | T4 | minor | minor | MODEL | 8 items, filter works visually; odd status set (success/new/moved/removed) shown raw; "Billing Service Bug - removed - Resolved race condition". |
| 53 | oracle-slice-3types__elemental__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Elemental / Gemini 3.5 Flash-Lite | T5 | major | good | RENDERER | Tiers via data binding render; `recommended` not rendered. |
| 54 | oracle-slice-3types__elemental__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | Elemental / Gemini 3.5 Flash-Lite | T6 | minor | minor | MODEL | 10 cards correct; progress hard-coded to 40% / "4 of 10 reviewed" at start. |
| 55 | oracle-slice-3types__json__haiku-4-5__temp0__run1 | JSON / Haiku 4.5 (t=0) | T1 | fail | fail | MODEL | Root is a leaf page_header; intro, 3 concept rungs + worked example, knowledge check and 3-question quiz are siblings nothing references (validator accepted it). |
| 56 | oracle-slice-3types__json__haiku-4-5__temp0__run1 | JSON / Haiku 4.5 (t=0) | T2 | major | major | MODEL | 4 KPI tiles fine; chart heading + chart left outside the root, so no chart. |
| 57 | oracle-slice-3types__json__haiku-4-5__temp0__run1 | JSON / Haiku 4.5 (t=0) | T3 | fail | fail | MODEL | Root is the hero; features, testimonial, CTA unreachable. |
| 58 | oracle-slice-3types__json__haiku-4-5__temp0__run1 | JSON / Haiku 4.5 (t=0) | T4 | fail | good | HARNESS | Filter renders as one segment per character: catalogue typed `options` as string, model sent a JSON string. Item list blank: harness ignores update_data_model at path "/items". Payload has 8 good items. |
| 59 | oracle-slice-3types__json__haiku-4-5__temp0__run1 | JSON / Haiku 4.5 (t=0) | T5 | major | good | RENDERER | `recommended` + badge "Most Popular" not rendered; "Custom" renders "$Custom". |
| 60 | oracle-slice-3types__json__haiku-4-5__temp0__run1 | JSON / Haiku 4.5 (t=0) | T6 | minor | minor | MODEL | Ten one-card flashcard_decks (each "1 / 1") instead of one 10-card deck; progress bar 0%. |
| 61 | oracle-slice-3types__json__opus-5-5__run1 | JSON / Opus 5.5 | T1 | major | minor | HARNESS; MODEL | Model sent six surfaces, each with id "root"; harness flattens surfaces and keeps the last id, so only the quiz renders. Hero, 3 concepts and a correct residence-time worked example (1.338e9/413,000 = 3,240 yr) are in the payload. |
| 62 | oracle-slice-3types__json__opus-5-5__run1 | JSON / Opus 5.5 | T2 | good | good | - | Tiles and chart internally consistent (Apr-Jun 2025 = 482 = tile; +12.4% vs Q1 429). |
| 63 | oracle-slice-3types__json__opus-5-5__run1 | JSON / Opus 5.5 | T3 | fail | good | HARNESS | Validator false positive "cta not reachable": root columns lists all four blocks by id. Re-parsed offline: same reply split into one block per message is VALID. |
| 64 | oracle-slice-3types__json__opus-5-5__run1 | JSON / Opus 5.5 | T4 | fail | good | HARNESS | Validator false positive: `name: "status_filter"` equal to own id flagged as self-reference; after renaming it, the same false "not reachable" error. Reply: heading, filter, 8-row table (options also a JSON string, would garble). |
| 65 | oracle-slice-3types__json__opus-5-5__run1 | JSON / Opus 5.5 | T5 | major | good | RENDERER | `recommended`/`highlighted`/badge on Pro not rendered. |
| 66 | oracle-slice-3types__json__opus-5-5__run1 | JSON / Opus 5.5 | T6 | minor | minor | MODEL; RENDERER | 10 cards with examples; progress hard-coded 60% / "6 of 10"; progress_circle value text invisible. |
| 67 | oracle-slice-3types__json__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | JSON / Gemini 3.5 Flash-Lite | T1 | fail | fail | MODEL | Root is a leaf page_header; 3 concept rungs, worked example and quiz unreachable. |
| 68 | oracle-slice-3types__json__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | JSON / Gemini 3.5 Flash-Lite | T2 | major | major | MODEL; HARNESS | benchmark chart outside root (no chart). "Conversion ▲ -0.8%": catalogue typed `is_up` as string, model sent "false", renderer treats the string as true. |
| 69 | oracle-slice-3types__json__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | JSON / Gemini 3.5 Flash-Lite | T3 | fail | fail | MODEL | Root is the hero; features, testimonial, cta_section unreachable. |
| 70 | oracle-slice-3types__json__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | JSON / Gemini 3.5 Flash-Lite | T4 | major | good | HARNESS | 8-row table (title/status/detail) fine; filter garbled into characters (options string, catalogue mistype). |
| 71 | oracle-slice-3types__json__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | JSON / Gemini 3.5 Flash-Lite | T5 | fail | fail | MODEL | Root is the hero; pricing_tier_group unreachable, no tiers shown. |
| 72 | oracle-slice-3types__json__gemini-3.5-flash-lite__first-run-timing-invalid__run1 | JSON / Gemini 3.5 Flash-Lite | T6 | fail | fail | MODEL | Root is a leaf page_header; 10-card deck and progress bar unreachable. |

## 2. Summary counts

Counts are good / minor / major / fail, from one repeat (r1) of six briefs per set.

**By format**

| Group | n | Rendered g/mi/ma/f | Payload g/mi/ma/f | Good or minor (rendered -> payload) |
|---|---|---|---|---|
| Express | 30 | 13/5/8/4 | 21/5/0/4 | 18 -> 26 |
| Elemental | 18 | 3/9/5/1 | 11/6/0/1 | 12 -> 17 |
| JSON | 18 | 1/2/6/9 | 7/3/2/6 | 3 -> 10 |
| Pipeline | 6 | 1/0/2/3 | 1/0/2/3 | 1 -> 1 |

**By format and model**

| Group | n | Rendered g/mi/ma/f | Payload g/mi/ma/f | Good or minor (rendered -> payload) |
|---|---|---|---|---|
| Express / Haiku 4.5 (hints v2, t=0) | 6 | 2/0/2/2 | 3/1/0/2 | 2 -> 4 |
| Express / Haiku 5.5 | 6 | 2/1/2/1 | 4/1/0/1 | 3 -> 5 |
| Express / Sonnet 5.5 | 6 | 4/1/1/0 | 6/0/0/0 | 5 -> 6 |
| Express / Opus 5.5 | 6 | 1/3/1/1 | 3/2/0/1 | 4 -> 5 |
| Express / Gemini 3.5 Flash-Lite | 6 | 4/0/2/0 | 5/1/0/0 | 4 -> 6 |
| Elemental / Sonnet 5.5 | 6 | 1/4/1/0 | 5/1/0/0 | 5 -> 6 |
| Elemental / Haiku 5.5 | 6 | 2/3/1/0 | 4/2/0/0 | 5 -> 6 |
| Elemental / Gemini 3.5 Flash-Lite | 6 | 0/2/3/1 | 2/3/0/1 | 2 -> 5 |
| JSON / Haiku 4.5 (t=0) | 6 | 0/1/2/3 | 2/1/1/2 | 1 -> 3 |
| JSON / Opus 5.5 | 6 | 1/1/2/2 | 4/2/0/0 | 2 -> 6 |
| JSON / Gemini 3.5 Flash-Lite | 6 | 0/0/2/4 | 1/0/1/4 | 0 -> 1 |
| Pipeline / Jev + Flash-Lite | 6 | 1/0/2/3 | 1/0/2/3 | 1 -> 1 |

**By model, all formats pooled**

| Group | n | Rendered g/mi/ma/f | Payload g/mi/ma/f | Good or minor (rendered -> payload) |
|---|---|---|---|---|
| Haiku 4.5 | 12 | 2/1/4/5 | 5/2/1/4 | 3 -> 7 |
| Haiku 5.5 | 12 | 4/4/3/1 | 8/3/0/1 | 8 -> 11 |
| Sonnet 5.5 | 12 | 5/5/2/0 | 11/1/0/0 | 10 -> 12 |
| Opus 5.5 | 12 | 2/4/3/3 | 7/4/0/1 | 6 -> 11 |
| Gemini 3.5 Flash-Lite | 18 | 4/2/7/5 | 8/4/1/5 | 6 -> 12 |
| Jev + Flash-Lite | 6 | 1/0/2/3 | 1/0/2/3 | 1 -> 1 |

**By task**

| Group | n | Rendered g/mi/ma/f | Payload g/mi/ma/f | Good or minor (rendered -> payload) |
|---|---|---|---|---|
| T1 | 12 | 4/1/3/4 | 6/1/1/4 | 5 -> 7 |
| T2 | 12 | 3/3/6/0 | 4/6/2/0 | 6 -> 10 |
| T3 | 12 | 4/2/1/5 | 7/0/1/4 | 6 -> 7 |
| T4 | 12 | 1/6/1/4 | 8/2/0/2 | 7 -> 10 |
| T5 | 12 | 0/0/10/2 | 9/1/0/2 | 0 -> 10 |
| T6 | 12 | 6/4/0/2 | 6/4/0/2 | 10 -> 10 |

**Causes of the 54 non-good rendered cells.** Main cause: MODEL 23, RENDERER 17, HARNESS 14. Any cause named: MODEL 33, RENDERER 20, HARNESS 16. In 27 cells the rendered grade is worse than the payload grade. In 17 of those the main cause is RENDERER and in 9 it is HARNESS; in 1 (C_gemini T5) the model's layout and R1 both played a part.

Failure modes by format (payload level):

- **Express (30 cells):** 4 payload fails. 3 are a list assigned to `root` (`root = [a, b, ...]`): CTH2 T1, C_haiku T1 and C_opus T3. 1 is a data binding on a static property (CTH2 T4). Every other Express payload is good or minor.
- **Elemental (18):** 1 payload fail (CX_gemini T3, a syntax error). The visible Elemental defects are mostly HARNESS: the catalogue copy renamed some fields (H2).
- **Direct JSON (18):** 6 payload fails and 2 majors. 8 cells use the same structural error: a leaf `root` with every other component left as an unreferenced sibling. These are CTN T1, T2 and T3, and CN_gemini T1, T2, T3, T5 and T6. The Opus 5.5 replies never do this. Another 4 JSON cells lose content to HARNESS defects: CN_opus T1, T3 and T4, and CTN T4.
- **Pipeline (layout80):** 5 of 6 briefs cannot be built with its 3 fixed layouts and its 2-4 item counts.
- **T5:** all 11 model payloads with tiers mark one tier as recommended. In the 10 cells where tiers render, the marker is never shown. This is a renderer/atom-contract issue (R1), not a model one.

## 3. Renderer / atom defects

Each item gives the atom, the evidence and a minimal repro payload. Renderer: the web article renderer at origin/main of 27 Oct 2026 (commit 447ae2c36).

- **R1 pricing_tier_group / pricing_tier_card.** The renderer marks a tier only through the card field `is_highlighted`, and only shows a CTA through `call_to_action_label`/`_url` and a period through `frequency`. The group atom documents `tiers` only as `array`, with no item shape, and pricing_tier_card was not in the C catalogues. So the models wrote `recommended: true`, `badge`, `highlighted`, `cta_label`, `period` and `description`, and all of them are silently dropped. All 11 model payloads with tiers set a recommended tier. In the 10 cells where tiers render, none shows it. Fix: alias these fields in the card renderer, or document the item shape on the group atom (or both). Repro: `payloads/oracle-slice-3types__express__opus-5-5__run1/T5.json`.
- **R2 pricing_tier_card.** `currency` defaults to "$" and is prepended to any price, so price "Custom" renders "$Custom". The harness patch (`norm_price`) only strips a leading symbol. Repro: `payloads/oracle-slice-3types__express__haiku-4-5__temp0__hints-v2__run1/T5.json, payloads/oracle-slice-3types__json__haiku-4-5__temp0__run1/T5.json`.
- **R3 stat_card.** `min-width:200px`, 24/32 px padding and a 2.8rem monospace value, with no wrapping or overflow handling. In a 4-column `columns` grid under about 900 px, the tiles overlap their neighbours and the values are cut off. Repro: `payloads/oracle-slice-3types__express__gemini-3.5-flash-lite__first-run-timing-invalid__run1/T2.json (also oracle-slice-3types__express__haiku-4-5__temp0__hints-v2__run1/T2, oracle-slice-3types__elemental__gemini-3.5-flash-lite__first-run-timing-invalid__run1/T2)`.
- **R4 stat_card.** `is_up` is read with Python truthiness and defaults to True. A string "false" (which the mistyped catalogue invites, see H1) and an omitted flag both render ▲ green, even for negative deltas. Repro: `payloads/oracle-slice-3types__json__gemini-3.5-flash-lite__first-run-timing-invalid__run1/T2.json (string), payloads/oracle-slice-3types__elemental__gemini-3.5-flash-lite__first-run-timing-invalid__run1/T2.json (omitted)`.
- **R5 metric_row.** The grid is fixed at `repeat(cols,1fr)` with `overflow:hidden` and 32 px values, and never wraps. In a half-width column, 4 tiles are clipped and the 4th is not visible. Repro: `payloads/oracle-slice-3types__express__haiku-5-5__run1/T2.json`.
- **R6 progress_circle.** The centre value text is `color:#f1f5f9` on a transparent background, so it is invisible on the light theme. The value is only readable from the ring. Repro: `payloads/oracle-slice-3types__express__opus-5-5__run1/T6.json, payloads/oracle-slice-3types__json__opus-5-5__run1/T6.json`.
- **R7 segmented_control.** The strip does not wrap or scroll, so in a narrow column the last options are clipped ("Done" is cut off). Minor. Repro: `payloads/oracle-slice-3types__express__sonnet-5-5__temp0__run1/T4.json`.
- **R8 pricing_tier_group.** The cards use `flex:1` with an auto basis, so at 640 px the third tier wraps onto its own row and the tiers are no longer side by side. Minor, and it depends on width. Repro: `payloads/oracle-slice-3types__express__sonnet-5-5__temp0__run1/T5.json`.

### Harness defects (not renderer; listed because they decide several verdicts)

- **H1.** The catalogue build script `prop()` maps only `array...`/`boolean...` descriptions to array/boolean. Fields described as `list ...`, `[...]` or `bool ...` become `type: string`. That is 18 fields in the C catalogues, including segmented_control.options, stat_card.is_up, table.headers/rows, quiz_question.options and progress_bar.show_percent. JSON models follow the schema and send a JSON-encoded string. The renderer then iterates the string one character at a time (the garbled filter strip) or reads "false" as true. Cells: CTN T4, CN_gemini T4, CN_gemini T2 (is_up); CN_opus T4 reply as well.
- **H2.** The Elemental catalogue-copy script capitalises component names with a global string replace. That also renames field keys that match a component name: concept_rung.body becomes `Body`, and feature_grid.heading/columns, gradient_hero.badge and cta_section.heading/body are renamed the same way. The models used the names they were given. the payload saver maps the component names back but not the fields, so the renderer ignores those fields. Cells: CX_gemini T1 (all concept text), CX_sonnet T1, CX_sonnet T3, CX_haiku T3.
- **H3.** the render harness merges `update_data_model` only when the path is "/" and the value is a dict. A model message at `path: "/items"` with a list value is ignored, so the `{"path": "/items"}` binding stays unresolved and the list renders blank. Cells: CTN T4.
- **H4.** The payloads flatten every surface's components into one list keyed by id. CN_opus T1 sent six surfaces, each with its own `root`, so the last one (the quiz) overwrites the other five. A real client would show all six surfaces. Cells: CN_opus T1.
- **H5.** SDK Direct JSON validator (`a2ui.utils.renderer_state` topology check). (a) It does not count ids listed in `columns.items[].blocks` as children, so a correct tree fails with "not reachable". (b) The check only runs when all messages arrive in one JSON array. Sent one block per message, the same CN_opus T3 reply is VALID, while CN_gemini T3 (whose siblings really are unreachable) becomes invalid when merged into one array. (c) A string field equal to the component's own id (`name: "status_filter"`) is reported as a self-reference. I verified this offline by re-parsing the saved replies with the same SDK in a local environment (the throwaway script is not included). Effect: 2 valid Opus replies were rejected, and 8 orphaned JSON payloads were accepted without a warning. Cells: CN_opus T3, CN_opus T4 (false rejections); CTN T1-T3, CN_gemini T1-T3/T5/T6 (missed).
- **H6.** Express compiler: `root = [a, b, ...]` (a contract violation, rule 2) is rejected in CTH2 T1 and C_haiku T1 ("Root target 'root' is not defined") but accepted as valid in C_opus T3, where no root component is emitted. the render harness then falls back to the first component (the hero). This is the same model error with two different outcomes. Cells: C_opus T3.
- **H7.** layout80 pipeline design (the pipeline layouts file): there are 3 fixed layouts (lesson, dashboard, landing) and counts of 2-4. It cannot express a quiz, a testimonial, a list of 8, priced tiers with feature lists, or 10 flashcards. Cells: layout80 T1, T3-T6.
- **H8.** Headless screenshot hang on the 5 T3 cells listed above. Not a content defect, and the cause is unverified. Cells: 5 T3 cells.

The harness fixes made before this run (renderer swap, root-only rendering for Express/JSON, types copied onto nested JSON blocks, the 1-column patch, the `$$` fix, flashcard_deck rendering, child-id list resolution) all show up as working in this run. No `$$`, every flashcard_deck renders, and nested JSON blocks render. Root-only rendering for Express and JSON is correct per the spec, and it is what makes the JSON orphan errors visible.

## 4. What the data supports and what it does not

Basis: **one repeat (r1), six briefs, one reviewer, n = 6 per set** (12 to 18 per format). There are no confidence intervals. One cell changes a set's count by 17 points. Temperature and hints differ between sets (CTH2 and CTN are Haiku 4.5 at t=0, CTH2 with hints v2; the other sets use API defaults), so differences between sets mix model, format and settings.

Supported, as observations on this sample:

- With harness and renderer defects factored out, the models' content is mostly sound. 40 of 72 payloads are good and 54 of 72 are good or minor (53 of the 66 non-pipeline cells). I found no factual errors in the water-cycle lessons or the vocabulary definitions. The numeric checks I ran (CN_opus T2 sums and percentage; CN_opus T1 residence time of 3,240 years) are correct.
- The rendered grades understate content quality by a large margin. In 27 of 72 cells the rendered grade is worse than the payload grade, in all but one mainly because of RENDERER or HARNESS defects. The single biggest item is R1, which affects all 10 cells where tiers render.
- Direct JSON had the most structural payload failures in this sample: 8 of 18 cells left components unreachable from `root`, all from Haiku 4.5 and Flash-Lite and none from the Opus 5.5 replies. Express had 4 of 30 structural fails and Elemental 1 of 18. This is one repeat, so it is a pattern to test, not a ranking.
- `root = [list]` occurred 3 times in Express (Haiku 4.5, Haiku 5.5 and Opus). A compiler that wrapped a list root in a column would turn 3 of the 4 Express fails into renders. Rejecting it consistently would at least make the outcome predictable.
- The layout80 pipeline cannot meet 5 of the 6 briefs as designed. Its results say nothing about Jev's or Flash-Lite's content ability beyond the text they wrote, which is fluent and correct.

Not supported:

- Any ranking of formats or models by quality. The differences are a few cells, the settings are not matched, there is one repeat, and HARNESS defects hit formats unevenly: H2 hits only Elemental, while the effects of H1, H3, H4 and H5 show up only in JSON cells.
- Any claim about interactivity. In the payloads I read, no filter (T4) or progress indicator (T6) is wired to its list or deck. The Opus 5.5 writer says so in its own T4 JSON reply, and static progress values (30%, 40% and 60% at start) are model-invented state. Flip and next work only inside flashcard_deck. The first reviewer did not click through the pages.
- Claims about the 5 T3 cells with no screenshot beyond what their text and payload show.
- Claims about wide-screen layout: every visual verdict is at 640 px, and R3, R5, R7 and R8 depend on width.
- Claims about stability across repeats. r2 and r3 exist for some sets but were not reviewed.


## Legend: old short codes used in the notes above

| Short code | Set name in this export (run 1) |
|---|---|
| layout80 | `jev-layout-pipeline__run1` |
| CTH2 | `oracle-slice-3types__express__haiku-4-5__temp0__hints-v2__run1` |
| C_haiku | `oracle-slice-3types__express__haiku-5-5__run1` |
| CT_sonnet | `oracle-slice-3types__express__sonnet-5-5__temp0__run1` |
| C_opus | `oracle-slice-3types__express__opus-5-5__run1` |
| C_gemini | `oracle-slice-3types__express__gemini-3.5-flash-lite__first-run-timing-invalid__run1` |
| CX_sonnet | `oracle-slice-3types__elemental__sonnet-5-5__run1` |
| CX_haiku | `oracle-slice-3types__elemental__haiku-5-5__run1` |
| CX_gemini | `oracle-slice-3types__elemental__gemini-3.5-flash-lite__first-run-timing-invalid__run1` |
| CTN | `oracle-slice-3types__json__haiku-4-5__temp0__run1` |
| CN_opus | `oracle-slice-3types__json__opus-5-5__run1` |
| CN_gemini | `oracle-slice-3types__json__gemini-3.5-flash-lite__first-run-timing-invalid__run1` |

R1 to R8 are renderer defects and H1 to H8 are test-harness defects, as numbered in section 3 of this file.
