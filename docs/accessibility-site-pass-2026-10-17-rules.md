# Hidden rules, a Lighthouse cross-check and a corrected score (2026-10-17)

Cross-checking against Lighthouse showed that our axe run was missing four WCAG rules. axe tags `td-has-header`, `table-fake-caption`, `p-as-heading` and `css-orientation-lock` as experimental, so a tag-only run never executes them. They are now enabled explicitly in the skill (`audit.mjs`) and in the Worker (`scan-job.js`).

## Score impacts, in order

Same pages each time (39 sampled from the home page), light theme, same scorer unless stated.

| Step | Score | Pages with a serious or critical failure | What changed |
|---|---|---|---|
| Live site, 17 Oct, rules as before | 94 (A) | 10 | the published figure |
| Scorer: static checks count only where the element exists | 94 (A) | 10 | no change on the site; page averages moved by 0.1; the free points matter on small pages only |
| Same live pages, four hidden rules on | **69 (C)** | 23 | `td-has-header` on 15 atom pages (critical), `p-as-heading` on 1 |
| Fix: empty `<th></th>` in the fields table, FAQ questions as headings (local rebuild) | 96 (A) | 9 | one shared template caused all 15 pages |
| Fix: contrast across the surface pages, hidden-radio tabs made focusable, code-block keyboard stop (local rebuild) | **99 (A)** | 1 | 38 of 39 pages scanned |

Reading the table:

- The 94 was correct for the rule set we ran, and wrong as a measure of the site, because the rule set was incomplete. A cross-check with a second tool found it.
- One template defect moved the score by 27 points because of the site cap (more than 10 percent of pages with a critical failure holds the site at 69). The cap is doing its job, and it is why a single shared defect matters so much.
- The home page and `/surfaces/android` timed out when scanned locally (very large pages), so 99 covers 38 of 39 pages. Android had 91 failing contrast elements on the earlier live scan and is the page most likely to lower the figure.
- The live site will read 69 until the fixes are deployed.

## Lighthouse comparison (Lighthouse 12.8.2, desktop)

| | Pages | Lighthouse mean | Our site score |
|---|---|---|---|
| W3C BAD, before | 20 | 78 | 69 |
| W3C BAD, after | 15 | 93.6 | 84 |
| a2uicatalog.ai (before this fix) | 39 | 98.7 | 94 |

- Ranking agrees: Spearman 0.94 across the W3C "before" pages, 0.79 across the catalogue pages.
- W3C pages were measured from captured source served locally. Run live, W3C served a redirect page and a 403 and every score came back as 93.
- Lighthouse flagged `td-has-header` on 14 pages that our run reported nothing for. That is how the missing rules were found.
- Lighthouse gives 100 to some pages built to be inaccessible, so a high Lighthouse score is not evidence of accessibility.

## Still open

`p-as-heading` on `/what-is-a2ui` could not be reproduced in a direct axe run, so its source is unknown; `svg_no_name` on 2 pages and `canvas_no_text_alt` on 1; the home page and Android still need a scan that completes.
