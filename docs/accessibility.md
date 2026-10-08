# Accessibility in the catalogue

Started 2026-10-08. Accessibility was an afterthought; this is the first measured baseline, the fixes it drove, and the
plan to build it in.

## What is measured, and what it cannot tell you

`a2ui-private/a11y/a11y_audit.py` renders every atom's example payload with the JavaScript renderer (what MCP Apps, the
Worker and the Android WebView bridge run) and runs axe-core 4.x (WCAG 2.0 to 2.2, levels A and AA) on each in headless
Chromium, **inside the real host stylesheet** (the first `<style>` of the MCP Apps bundle, which defines the theme
tokens `--muted`, `--text`, `--bg`, `--accent`... as a host paints them). Light page, and a dark page with
`asw-dark-theme`. It is a ratchet, like `security/xss-fuzz`:

- `a11y_audit.py` fails on anything new. A new atom must start with no violations; a baselined atom may not get worse.
- `--update` rewrites the baseline after a fixing batch and prints what it locks in and anything worse than before.
  `--theme dark` audits the dark page (`baseline-dark.json`). `--report` prints the breakdown and the top failing
  colour pairs.
- Two static flags axe cannot raise: `loop_no_reduced_motion` (an infinite CSS animation with no
  `prefers-reduced-motion` rule in the atom's own markup, WCAG 2.2.2 and 2.3.3) and `canvas_no_text_alt` (a canvas with
  no `aria-label`, `role="img"` or `aria-hidden`, WCAG 1.1.1).

**A lesson the harness taught on day one.** The first version audited on a bare white page and overstated contrast
failures: atoms that read `var(--muted, #9ca3af)` fell back to the literal grey because the page had none of the host's
tokens. Audit in the host's real theme, or the numbers describe a host that does not exist.

Automated checks find roughly a third to a half of real WCAG issues. They say nothing about keyboard order, focus, or
what a screen reader announces. The examples are generic and the page has no network. axe cannot evaluate text over a
gradient or an image, so some contrast hits on dark-stage atoms (the `motion_*` family) are noise. A clean atom means
"no automated violations", never "accessible". The layers still to build:

1. Behaviour tests in the same browser harness: keyboard operability, visible focus, no traps, 320 px reflow, target size.
2. Assistive technology by hand: TalkBack on the Pixel, VoiceOver, NVDA.
3. Content: an agent writes the alt text, labels and heading order, so a renderer cannot make output accessible alone.
   This is the catalogue's unique problem and needs a contract (see "Next").

## What the first measurement found

650 atoms audited. Colour contrast dominates; the rest is small (missing form labels in 7 atoms, unnamed selects in 4,
and a handful of one-off name or target-size issues). Static flags: 35 atoms loop an animation forever with no
reduced-motion rule in their own markup, and 15 canvas atoms have no text alternative.

## Fixes made (and the numbers, on the real host stylesheet)

| | atoms with an axe violation | failing contrast nodes |
|---|---|---|
| light page, before the host-token and muted fixes | 172 | |
| light page, now (baseline.json) | 137 | 265 |
| dark page, before | 245 | |
| dark page, now (baseline-dark.json) | 196 | 373 |

1. **Default accent.** `#6366f1` is 4.46:1 on white, a hair under the 4.5:1 AA threshold: white text on it and indigo
   text on white both failed. Now `#4f46e5` (6.3:1) in every renderer default and in the documented schema defaults.
   `tests/test_a11y_tokens.py` holds it in CI, where the axe ratchet does not run.
   *Known cost:* no single colour passes AA on both white and a dark host, and `#4f46e5` is 2.7:1 on the dark host
   (the old one was 4.35:1, also failing). The proper fix is a theme-aware default accent (see "Next").
2. **Host tokens that failed on their own surfaces** (`AtomStyles.html`, shared by the GAS shell and the MCP Apps bundle).
   Dark `--muted` `#8e8e93` was 4.27:1 on the host's own `--surface` and 3.48:1 on `--surface2` (about 75 failing nodes
   in 40 atoms): now `#a8a8ad`. Light `--accent` `#1a73e8` was 4.27:1 on `--surface`: now `#1967d2`. Dark `--accent`
   `#0a84ff` was 3.82:1 on `--surface`: now `#5aa9ff`. Three lines, the largest single gain.
3. **Muted text follows the theme.** `color:#9ca3af|#94a3b8|#6b7280|#64748b` in atoms with no surface of their own became
   `color:var(--muted,#5f6368)` (169 occurrences in the GAS atoms, 363 in the Python renderer), which flips per theme.
   Done only for `color:` declarations, and only in renderers that paint no dark surface, take no colours from a theme
   object and draw on no canvas (`a2ui-private/a11y/migrate_muted.py`; run from a2ui-catalogue, dry run by default,
   `--write` to apply).

**Tried and reverted: a blind grey swap.** Replacing those greys with darker ones everywhere was net-neutral to harmful:
atoms with their own dark surface got worse (`motion_tokens` +38 nodes), and on a dark host every atom with no surface
of its own lost contrast. The right grey depends on the surface behind it.

**The rule this taught, found again by the ratchet on the first migration:** an atom that paints its own surface keeps
its own explicit text colours, light surface or dark. Four atoms with their own light card (`big_reveal`,
`chat_sequence`, `share_quote`, `star_rating_display`) regressed under the theme-aware token on a dark host and were
restored. Only an atom that inherits the host's surface should inherit the host's text colour.

## Next, in the order I would do it

1. A theme-aware default accent. Atoms build tints by appending hex alpha (`color + '18'`), so a `var()` default breaks
   them; they need a computed tint first. This is the one real structural item left in contrast.
2. An accessible-name contract: schema fields marked as the atom's accessible name (alt, label, title), validated by the
   payload guard like URLs and ids. Missing or empty gets a visible, logged degrade.
3. A text-alternative contract for canvas and WebGL atoms (a `describe` field becoming `role="img"` plus `aria-label`).
4. Decorative loops: respect reduced motion by default and offer a pause control (WCAG 2.2.2). The motion policy
   (`palette` `reduced_motion`) is where it plugs in; an author must never be able to turn motion on for a viewer who
   asked for less.
5. Per-atom accessibility metadata beside `works_on` (keyboard, screen reader, reduced motion, last audited), generated
   into a matrix like the compatibility one. That is also the raw material for a conformance statement.
6. `menu`: it declares `role="menu"` but has no arrow-key handling. Either add the keyboard pattern or drop the role.
7. A palette-level accessibility policy next to the motion one: contrast, text size, `prefers-contrast`, forced colors.
8. Package the method as a skill for any declarative-UI schema: render every component's example, audit in the host's
   real theme, hold it in a ratchet, and handle the accessible-name contract. The harness needs an adapter for "give me
   the HTML of component X" so it is not coupled to this renderer.
