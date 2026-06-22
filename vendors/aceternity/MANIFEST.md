# Vendor: Aceternity UI

| | |
|---|---|
| **Source** | https://ui.aceternity.com |
| **License** | MIT |
| **Atom count** | 0 (pattern inspiration — atoms are a2ui originals) |
| **Coverage audit** | 2026-06-13 |

Aceternity UI is a collection of ~60 React + Tailwind CSS copy-paste components, almost all of them animation-first. The components fall into three categories for A2UI purposes: already covered by existing atoms, JS-dependent (cannot be expressed in pure CSS without a runtime), and genuine CSS-achievable gaps.

---

## Already covered by existing A2UI atoms

| Aceternity component | A2UI atom | A2UI source | Notes |
|---|---|---|---|
| Animated Modal | `css_modal`, `modal` | a2ui | Full coverage |
| Animated Tooltip | `tooltip`, `hover_card` | a2ui | Full coverage |
| Bento Grid | `bento_grid` | a2ui | Full coverage |
| Carousel | `carousel` | Flowbite | Full coverage |
| Compare (before/after slider) | `before_after` | a2ui | Full coverage |
| Input | `form_input` | OpenUI / Thesys | Full coverage |
| Multi-Step Loader | `stepper` | a2ui | Structural coverage; no animation |
| Navbar Menu | `navigation_menu` | a2ui | Full coverage |
| Number Ticker | `animated_counter` | a2ui | Full coverage |
| Skeleton | `loading_skeleton`, `skeleton_stage_card` | a2ui | Full coverage |
| Tabs | `tabs`, `tab_bar` | shadcn/ui | Full coverage |
| Timeline | `timeline` | a2ui | Full coverage |

---

## JS-dependent — not implementable as pure CSS atoms

These require JavaScript event listeners (mousemove, scroll, drag) or canvas/WebGL and are incompatible with the A2UI server-side HTML renderer.

| Aceternity component | Dependency | Why skipped |
|---|---|---|
| 3D Pin | Three.js / perspective JS | mousemove transform |
| Background Beams | SVG + JS animation | Path interpolation |
| Background Boxes | JS canvas | Canvas rendering |
| Card Spotlight | JS `mousemove` | Radial gradient tracks cursor |
| Container Scroll Animation | Scroll event JS | Parallax on scroll |
| Cover | JS mousemove | Text reveal on cursor position |
| Direction Aware Hover | JS `mouseenter` direction detect | Edge detection |
| Evervault Card | JS canvas / shader | Procedural noise |
| Follow Pointer | JS `mousemove` | Element follows cursor |
| Glare Card | JS `mousemove` | Glare tracks cursor |
| Globe | Three.js / Globe.gl | 3D WebGL scene |
| Google Gemini Effect | JS SVG path animation | Path-following beams |
| Hero Parallax | Scroll event JS | Parallax layer offset |
| Lens | JS `mousemove` | Magnifier follows cursor |
| Macbook Scroll | Scroll event JS | Scroll-driven animation |
| Parallax Scroll | Scroll event JS | Parallax image grid |
| Placeholders and Vanish Input | JS canvas | Particle dissolve effect |
| Resizable Navbar | JS resize observer | Dynamic size on scroll |
| Scroll Based Velocity | JS scroll velocity | Speed-based transforms |
| Sparkles | JS canvas | Random particle positions |
| Spotlight (background) | JS `mousemove` | Spotlight follows cursor |
| Sticky Scroll Reveal | Intersection Observer JS | Scroll-driven reveal |
| SVG Mask Effect | JS `mousemove` | Mask follows cursor |
| Tracing Beam | Scroll event JS | Beam tracks scroll position |
| Vortex | JS canvas / shader | Procedural vortex |
| World Map | JS SVG + data | Interactive SVG map |

---

## Genuine CSS gaps — Priority 1 (implemented)

### `marquee_strip`
Infinite horizontally-scrolling strip of text or logo items. Implemented with CSS `@keyframes` — no JavaScript required.

```yaml
- type: marquee_strip
  fields:
    items: array of strings or {text, image_url} objects to scroll
    speed: '"slow" | "normal" | "fast"  default "normal"'
    direction: '"left" | "right"  default "left"'
    pause_on_hover: 'bool  default true'
    label: string (optional). Small label above the strip.
    gap: string (optional). Gap between items, e.g. "48px". Default "40px".
```

Inspiration: Aceternity UI "Infinite Moving Cards"

---

### `typewriter_text`
Text that types itself out using a CSS `steps()` width animation. Works with any font via `ch` units on a `pre`/`span`.

```yaml
- type: typewriter_text
  fields:
    text: string. The text to type out.
    size: string (optional). Font size e.g. "32px". Default "28px".
    weight: string (optional). Font weight. Default "700".
    color: string (optional). Text colour. Default "#1a1a1a".
    speed: '"slow" | "normal" | "fast"  default "normal"'
    cursor: 'bool (optional). Show blinking cursor. Default true.'
    delay: string (optional). CSS delay before typing starts, e.g. "0.5s". Default "0s".
```

Inspiration: Aceternity UI "Typewriter Effect" / "Text Generate Effect"

---

### `animated_border_card`
Card with an animated rotating gradient border. Uses a spinning `::before` pseudo-element with `conic-gradient` — no JavaScript.

```yaml
- type: animated_border_card
  fields:
    title: string (optional). Card heading.
    body: string. Card content (markdown supported).
    accent: string (optional). Border gradient colour. Default "#38bdf8".
    accent2: string (optional). Second gradient colour. Default "#818cf8".
    background: string (optional). Card inner background. Default "#ffffff".
    speed: '"slow" | "normal" | "fast"  default "normal"'
    border_width: integer (optional). Border thickness in px. Default 2.
```

Inspiration: Aceternity UI "Moving Border"

---

## Genuine CSS gaps — Priority 2 (implemented)

### `aurora_background`
Animated radial gradient blobs drifting independently on a dark panel. See `atoms/schema.yaml` for full field reference.

### `dot_grid_background`
Repeating dot, grid, or cross pattern via CSS `background-image`. Variants: `dots`, `grid`, `cross`.

### `shimmer_button`
CSS `background-position` sweep animation on a button or anchor. Configurable accent, size, and speed.

### `card_stack`
2–4 cards stacked with progressive CSS `rotate` + `translateY`. First card in array is front (fully visible); back cards faded and rotated.

### `meteor_shower`
Diagonal falling streaks via staggered `@keyframes` on `<span>` elements. Count, colour, and speed configurable; optional title/body overlay.

---

## Attribution note

No Aceternity UI source code is distributed in this repository. The atoms above are original Python implementations inspired by the visual patterns of Aceternity UI's components. Aceternity UI is licensed MIT; the `source: *a2ui` anchor in `schema.yaml` reflects that these atoms are catalogue originals, not derived works.
