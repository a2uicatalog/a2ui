# Site accessibility pass, 2026-10-13: baseline, fixes, rescan

What was measured on a2uicatalog.ai, what was changed, and what moved. Scanner: the private hosted scanner (Browser Run, axe-core 4.14 plus five static checks) for the live baseline; the same checks from the local skill for the rescans of the rebuilt local copy. 40 pages from the home page, crawl depth 2, `robots.txt` followed, light and dark. Automated checks only: roughly a third to half of real issues. No screen-reader or disabled-user testing.

## Baseline (live site)

Score 69 (C), light and dark. All 40 pages carried a serious failure. Colour contrast 40 pages (2,958 elements light, 1,871 dark); links told apart by colour only 39 pages; image alt 5 pages (critical); unlabelled fields 2 (critical); `dt`/`dd` outside `dl` 6; iframes with no title 3; scroll regions with no keyboard access 4; plus static flags (hidden radio widgets 4 pages, clickable non-controls 3, unnamed SVGs 5, canvases with no alternative 3). Fix order predicted: contrast, image alt, links, `dl`, taking the site from 69 to 95.

## Changes made (committed locally, not pushed or deployed)

1. **Brand tokens** (`atoms/brand-tokens.yaml`, then `gen_brand.py`): light accent 58% to 51% lightness (5.1 to 6.1:1 on the page surfaces; was 3.8 to 4.55); new `accent-2-text` (deeper teal, for text) while `accent-2` is unchanged for graphics; dark soft tint 38% to 33% (accent on it 3.90 to 4.74:1). Options and ratios were shown in `Downloads/brand-colour-before-after.html` and chosen there.
2. **Site stylesheet** (`scripts/generate_atom_pages.py`): footer, breadcrumb and sub-heading links use `accent-2-text`; links in running text and the footer are underlined (WCAG 1.4.1).
3. **A dark-mode bug the scan led to:** the atom preview stage (cards) and the preview box (surface pages) are white at all times, but the atoms drawn inside took the dark theme's pale text colours: `#eaeff5` on white is 1.15:1, nearly invisible. Both now keep the light tokens when the site is dark, built from the brand file so it cannot drift.
4. Two brick demo pages carry a hand-pasted brand block; restamped.

## Rescan (rebuilt local copy, same 40 pages)

| | Baseline | After |
|---|---|---|
| Score, light | 69 C | 69 C |
| Pages with a serious or critical failure (light) | 40 | 21 |
| Colour contrast, light | 40 pages, 2,958 elements | 13 pages, 505 elements |
| Links told apart by colour only | 39 pages, 56 elements | 14 pages, 16 elements |
| Points lost to the severity caps (per page) | 9.6 | 6.2 |
| Pages with a serious failure (dark) | 40 | 20 |
| Colour contrast, dark | 40 pages, 1,871 elements | 12 pages, 3,453 elements |

The score did not move. The cap rules (more than a tenth of pages held at 69 or below caps the site at 69) mean the site score only changes when the number of pages with a serious failure falls far enough; 21 pages still hold a serious failure. The underlying measures improved a lot. A score that does not move while the evidence does is a finding about the scorer as well: see `references/lessons.md` in the skill.

## Still open

- Image alt on 5 pages (critical); `dl` structure on 6; iframe titles on 3; the hidden-radio, clickable-span and unnamed-SVG components on a few pages; links in running text still failing on 14 pages (16 elements: not yet traced).
- Remaining contrast is mostly inside atom example content (for example a gold badge `#c69600` on `#ffeced` at 2.37:1, a gold-on-pink pair, `#10b981` on `#d1fae5`), which belongs to those atoms' own baselines.
- Dark contrast is higher in elements (3,453 vs 1,871) on fewer pages: the dark preview boxes still need tracing.
- Next measured step: fix image alt, `dl` and the 14-page links, rescan, and see whether the page count with a serious failure drops under the cap thresholds.

## Round 2 (generator fixes, same 40 pages)

Fixed in `generate_atom_pages.py`: breadcrumb links underlined; the decorative atom cards on the home page marked `inert` (they were `aria-hidden` yet focusable); carousel dots given a 24px hit area; code blocks made keyboard-scrollable.

| | Baseline | Round 1 | Round 2 |
|---|---|---|---|
| Score (light / dark) | 69 / 69 | 69 / 69 | 69 / 69 |
| Pages with a serious or critical failure (light / dark) | 40 / 40 | 21 / 20 | 15 / 14 |
| Links told apart by colour only | 39 pages | 14 | gone |
| Contrast, light | 40 pages, 2,958 elements | 13, 505 | 13, 453 |
| Points lost to severity caps (light) | 9.6 | 6.2 | 5.0 |

Gone from the site list: links-by-colour, aria-hidden-focus, target-size, unlabelled fields on site pages. The site-level findings are now all inside atom example content, which the atom renderers own.

**The one fix that moves the score:** image alt on 5 pages is critical and alone is worth +15 (69 to 84); then contrast (93), `dl` structure (95). All three are atom-level (an icon-row atom's images, the atoms' own example colours, the glossary atom). They go in the same `atom-change` batch as the `motion_tabs`, `motion_glass`, `motion_highlight` and `venn_diagram` contrast fixes, together with: iframe titles (YouTube and embed atoms), unlabelled radio, slider, date and code-digit inputs, empty link text in two list atoms.

## Round 3 (atom batch, same 40 pages): the score moves

Fixed in the atoms (GAS source and the site renderer): decorative icon alt in `social_proof_banner` (the one critical finding), `dl` wrapper in `glossary_term`, iframe titles (`youtube`, `embed_stackblitz`, `media_stream_card`, CodePen, Slides), the `file_upload` label, date-picker and variant-selector names, `motion_tabs` / `motion_glass` / `motion_highlight` contrast, theme-following text in `further_reading` and `checklist_interactive`.

| | Baseline | Round 1 | Round 2 | Round 3 |
|---|---|---|---|---|
| Score (light / dark) | 69 / 69 | 69 / 69 | 69 / 69 | **84 / 84 (B)** |
| Pages with a serious or critical failure (light / dark) | 40 / 40 | 21 / 20 | 15 / 14 | 14 / 13 |
| Image alt, `dl`, links by colour | 5 / 6 / 39 pages | 5 / 6 / 14 | 5 / 6 / 0 | 0 / 0 / 0 |
| Points lost to severity caps (light) | 9.6 | 6.2 | 5.0 | 3.5 |

The last critical failure on the site was the five-page image-alt finding. With it gone, fewer than a tenth of pages are held at 69 or below, so the site cap lifts from 69 to 84. That single fix was worth +15, as the fix order had said. The next step is colour contrast on 13 pages (453 elements light, 3,401 dark, mostly inside atom example colours): worth +11 on its own, to 95.

Still open: contrast inside atom examples, the hidden-radio, clickable-span and unnamed-SVG components, `venn_diagram`, the GAS `variant_selector` radios, `resources_list` empty link text, 14 unlabelled inputs on 2 pages, 6 iframes. Test status of the batch: 2,231 passed; failures are the known `test_brand` and the pending LDraw rebake; `test_schema_fields_read` needed a baseline entry for the showpiece pack's shared text options.

## Round 4 (generator: scoped preview CSS, degraded badge)

Two generator fixes: atoms rendered for standalone pages ship `<style>` rules aimed at the page (`body{background:#fff}`, `html:has(.asw-page) body{background:#0b0d12!important}`); embedded in a preview card they repainted the whole surfaces page (white in dark mode). The generator now drops rules whose selector starts at `html` or `body` from embedded previews. The "degraded" badge used the warn amber as text on its own tint (2.37:1); the text now mixes toward the text colour.

| | Round 3 | Round 4 |
|---|---|---|
| Score (light / dark) | 84 / 84 | 84 / 84 |
| Contrast, light | 13 pages, 453 elements | 12 pages, 380 |
| Contrast, dark | 12 pages, 3,401 elements | 11 pages, 1,829 |
| Pages with a serious failure (light / dark) | 14 / 13 | 13 / 12 |

The score holds at 84: contrast is on 12 pages, each of which also carries a few other findings. The remaining contrast is a long tail of fixed colours inside atom examples, about 30 distinct pairs across many atoms (greys `#999`, `#9ca3af`, `#94a3b8`, `#8f8f8f`; `#10b981` on `#d1fae5`; white on `#eab308`, `#4285f4`; `#f87171` on `#fafafa`). Those are per-atom colour decisions, not site CSS; the fix order says clearing all contrast takes the site to 96. One page (probably the home page, which carries hundreds of previews) timed out in axe and was reported as not audited; the score covers 39 of 40.

## Round 5 (accessible example data; no renderer change)

Generator only: every colour value in the example payloads that fails AA as text or under white text (`#6366f1`, `#10b981`, `#f59e0b`, `#4285f4`, `#ef4444` and 20 more) is mapped to a darker equivalent that passes, so the previews, and the examples agents copy, are accessible by default; motion text atoms get a dark default ink on the white preview surfaces.

| | Round 4 | Round 5 |
|---|---|---|
| Score (light / dark) | 84 / 84 | 84 / 84 |
| Contrast, light | 12 pages, 380 elements | 13 pages, 359 |
| Contrast, dark | 11 pages, 1,829 | 10 pages, 1,644 |

A small gain. The tracer shows where the rest is: the all-atoms surface pages. `/surfaces/android` (140 failing elements) and `/surfaces/web` (132) preview every atom, so they carry the renderers' own fixed colours: greys `#8f8f8f`, `#999`, `#9ca3af`, `#94a3b8`; `#10b981` on its own `#d1fae5` tint; white on `#4285f4` and `#eab308`; `#f87171` on `#fafafa`. These are renderer defaults and derived tints, not example data; each fix is an atom change with twin tests and a view restamp, about 30 distinct pairs in about 50 atoms. Stopping the site pass at 84 (B) here is reasonable: the remaining findings are concentrated in a few pages that exist to show every atom.

## Round 6 (atom contrast pass, 2026-10-14): 94 (A)

Per-atom audit of every atom example (GAS and site renderers): 299 failing contrast elements in 129 items. A script planned a darker colour for each failing pair (text darkened on light fills, fills darkened under white text), applied 174 swaps to about 50 atoms in both renderers (the twin-parity suite stayed green), plus the concept palette accent (`#6267e7` to `#4f46e5`), the shared `faint` design token (`#8f8f8f` to `#757575`, in `design-tokens.yaml`), and three small page fixes (renderer page tab labels and button/link colours, the motion timeline clock). Re-audit of the examples: 299 to 129 elements, 129 to 68 items.

| | Round 5 | Round 6 |
|---|---|---|
| Score (light / dark) | 84 / 84 | **94 / 94 (A)** |
| Pages with a serious or critical failure | 14 / 13 | 10 / 10 |
| Contrast, light | 13 pages, 359 elements | 9 pages, 236 |
| Points lost to severity caps | 3.5 | 2.5 |

The jump from 84 to 94 is the site cap lifting: it holds a site at 84 while more than a quarter of pages carry a serious failure, and the count fell to exactly 10 of 40, which is not more than a quarter. **That is a threshold effect, so 94 is fragile**: one more failing page returns the site to 84. The ten pages are the home page and the all-atoms surface pages (android, web, email, pdf, pptx, slides, chromium-render, mcp-apps), which show every atom, and `/atoms/tabs` (hidden radio inputs).

Two of my own edits regressed in this round and were caught only by rescanning: a page-wide link colour overrode a button colour (teal on indigo, 1.12:1), and taking the timeline clock colour from the film theme put near-white text on a light page.

Open: the contrast long tail in about 68 atoms; hidden radios (tabs and others) need a designed focus style, not just a different hide; clickable spans; unnamed SVGs. The full `atom-change` test run covered the main contrast pass (2,226 passed; failures were the known `test_brand` and LDraw rebake, five browser tests that pass alone, and the design-token check fixed at its source); the last small edits ran only the twin, design-token and schema-field tests, so one more full run is owed before any push.

## Round 7 (atoms found by scanning the infographic): site holds at 94

Converting the accessibility infographic into an A2UI payload and scanning the rendered page with the same scanner scored it 84, not 100, which exposed defects in shared atoms: `callout` titles (info blue 3.93:1, warning orange 2.89:1), `before_after` code (no text colour, black on `#1e1e1e`), the translucent dark chart cards (18 of them: grey text on mid-grey on a white page) and unnamed chart SVGs. Fixed in the site renderer (and the Apps Script `before_after` and `chartjs_line`); the infographic then scored 100. Full `atom-change` run: 2,232 passed; failures only the known `test_brand` and LDraw rebake.

Site rescan: 94 / 94 (A), unchanged; contrast in light 236 to 222 elements. The score is held by the same ten pages (home, the all-atoms surface pages, `/atoms/tabs`). Further movement now needs those ten pages cleared, not more single-atom fixes.
