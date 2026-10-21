# core-bar (`chartjs_bar`): what changes for existing payloads (I85) and what round 2 fixed

Measured base vs tip on the 7 existing payloads from tests/scripts, both twins (review of 2026-10-21, finding CB-4):

1. Whole renderer replaced: SVG (`viewBox 500x200`, 9-unit text, dark card, gradients, glow filter) -> positioned HTML, 12 px text, theme
   tokens, no SVG.
2. Axis. Python ran from max down to min, not from zero (`[42,65,88]` -> ticks 88/76.5/65/53.5/42); now d3-nice ticks from zero (0..100).
   GAS rounded ticks (0,1,1,2,2); now 0..4.
3. Heading: Python showed `datasets[0].label`; now `title` (series names move to the legend, the table and the aria-label).
4. All series are drawn (GAS drew only the first); a hidden table lists every value; the aria-label is a gist.
5. Empty payloads: Python returned `""`, GAS "No data"; both now say "No numbers to draw as bars."
6. Legacy GAS fields no longer read (and not noted): `bar_color`, per-row `data[].color`, `height`, `width`.
7. Numeric strings (`"3.5"`) in the legacy `data` shape are skipped with a note (GAS used `parseFloat`). Kept on purpose: a string is not a
   number in `datasets[].data` either, and both twins agree.
8. The GAS renderer moved from `atoms_charts.gs` to `atoms_infographic.gs`.
9. Python and GAS are now byte-identical (they never were at base).

Round 2 (this branch, `cloud/plotly-core-bar-r2`):

- CB-1 `_if_fixed` quantizes in an 80-digit decimal context: `.20f` / `.18%` on |v| up to 1e12 no longer raise in Python. The d3 golden
  generator now includes `.20f .16f .20% .18%`; fixture regenerated with the real d3 (every earlier entry unchanged).
- CB-2 The caps note counts what was given: "The first 40 of 500 categories are drawn; the table has the first 200." (reads cap at 200
  categories and 24 series).
- CB-5 `degraded_on` notes describe the HTML renderer, not canvas.
- CB-7 an unusable `y_range` says "y_range was not two different numbers; it was ignored."
- Not fixed: CB-3 (item 7 above, listed instead), CB-6 (see the final message), CB-8 (generator file, PM's call).
