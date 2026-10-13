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
