# Third-Party Software Notices

This repository (`curtiskrygier/a2ui`) derives atoms from open-source
component libraries. No vendor source files are stored here — adaptations are
documented in `vendors/<vendor>/MANIFEST.md` and the rendering logic is
recompiled from scratch into `renderers/web_article.py`. Each atom carries a
`source` field in `atoms/schema.yaml` identifying its origin.

**Seven declared exceptions: PDF.js, QR-Code-generator, Three.js, and the four
self-hosted type families (IBM Plex, Noto Sans, Arimo, Lato)** (below) are
vendored WHOLESALE, unmodified, not recompiled — a real
binary-format parser, a Reed-Solomon-error-correction-coded matrix encoder,
a WebGL rendering engine, and a font's actual glyph outlines are all out of
scope to reimplement (a
subtly-wrong hand-rolled QR encoder would produce codes that *look* right but
don't scan — not a visually-catchable bug, unlike this policy's other
adaptations, which are simple CSS/HTML patterns). PDF.js ships only inside
the MCP Apps bundle (`file_upload` atom's PDF branch), never fetched at
runtime, so the CSP-clean/self-contained invariant (`mcpUiCsp()`,
`resourceDomains: []`) holds even though this policy's general rule does not.
QR-Code-generator ships inline with every atom render (Python for static
surfaces, the same vendored algorithm ported to JS for GAS/MCP Apps) with no
network calls either. Three.js is vendored the same way for the same reason —
a static same-origin asset, never a CDN — but it ships only inside the
standalone render-appearance proof-of-concept demo
(`public/bricksdemo/threejs-demo/`); it is not part of, and does not touch,
the live production renderer (`atoms_brick.gs`'s existing WebGL/Canvas-2D
path). **The four type families are the exceptions that DO
introduce a runtime network fetch** (a `@font-face src: url(...)` against
`a2uicatalog.ai`'s own `/fonts/` path, same-origin, opt-in per atom via
`use_plex_fonts`/`use_noto_fonts`) — on any surface whose CSP blocks that
fetch (e.g. a strict MCP Apps `resourceDomains` policy), the font-family
fallback stack degrades silently to system fonts; nothing breaks, the atom
just looks plainer.

---

## Material Symbols (Google)

- **Project:** Material Symbols / Material Design Icons — SVG path data for 59 icons
- **Website:** https://github.com/google/material-design-icons
- **License:** Apache License 2.0
- **Copyright:** Copyright Google LLC
- **Vendored as:** `atoms/basic-catalog-icons.json` (path data only, outlined style, 24px;
  `symbol` records which file each of the A2UI Basic Catalog Icon's built-in names uses),
  regenerated into `apps-script-surface/gas-wired-renderer/atoms_v1_icons.gs` by
  `scripts/gen_basic_icons.py` and copied into the Android library's assets.

---

## gifenc, mp4-muxer, webm-muxer (film export)

- **Projects:** gifenc 1.0.3 (Matt DesLauriers, https://github.com/mattdesl/gifenc);
  mp4-muxer 5.2.2 and webm-muxer 5.1.4 (Vanilagy, https://github.com/Vanilagy/mp4-muxer,
  https://github.com/Vanilagy/webm-muxer)
- **License:** MIT License (all three)
- **Vendored as:** bundled into `public/vendors/client-export/client_export.min.js` (minified,
  unmodified), with each project's licence text in `public/vendors/client-export/LICENSES.md`
- **Used by:** the film export page (`/surfaces/mcp-apps/export/`), which encodes a
  `motion_timeline` to GIF, MP4 or WebM in the visitor's browser. Loaded only when an export starts.

---

## PDF.js (Mozilla)

- **Project:** PDF.js — client-side PDF rendering and text extraction
- **Website:** https://mozilla.github.io/pdf.js/
- **License:** Apache License 2.0
- **Copyright:** Copyright 2026 Mozilla Foundation
- **Vendored as:** `apps-script-surface/gas-wired-renderer/vendor/pdfjs/pdf.min.mjs`
  (legacy build, unmodified, main-thread mode — no separate worker file
  inlined; see `LICENSE` alongside it)
- **Used by:** the `file_upload` atom's PDF branch (MCP Apps surface only)

---

## QR-Code-generator (Project Nayuki)

- **Project:** QR-Code-generator — QR Code matrix encoder (Reed-Solomon error
  correction, mask pattern scoring, full symbol construction)
- **Website:** https://www.nayuki.io/page/qr-code-generator-library
- **License:** MIT License
- **Copyright:** Copyright (c) Project Nayuki
- **Vendored as:** `renderers/vendor/qrcodegen.py` (Python, native
  implementation, used server-side for the static SVG render on every
  surface) and `apps-script-surface/gas-wired-renderer/vendor/qrcodegen/qrcodegen.js`
  (official compiled-from-TypeScript ES6 release build, unmodified, used
  client-side for the `schema_qr` atom's interactive mode; see `LICENSE`
  alongside it)
- **Used by:** the `schema_qr` atom (all surfaces for the static render;
  `web`/`google-apps-script-web`/`mcp-apps` additionally for
  `is_interactive: true`)

---

## Studio typefaces: Recursive, Anybody, Nabla, Fraunces

- **Projects:** Recursive (https://github.com/arrowtype/recursive), Anybody (https://github.com/Etcetera-Type-Co/Anybody),
  Nabla (https://github.com/justvanrossum/nabla), Fraunces (https://github.com/undercasetype/Fraunces)
- **License:** SIL Open Font License 1.1 (each font's licence text is vendored verbatim beside it as `<name>-OFL.txt`)
- **Copyright:** Copyright 2020 The Recursive Project Authors; Copyright 2020 The Anybody Project Authors; Copyright 2022 The
  Nabla Project Authors; Copyright 2018 The Fraunces Project Authors
- **Vendored as:** `public/vendors/fonts/{recursive,anybody,nabla,fraunces}.woff2`, the unmodified Google Fonts latin subsets
  (all variable axes kept), fetched from pinned versioned fonts.gstatic.com URLs and sha256-verified by
  `scripts/fetch_studio_fonts.py` (pinned 2026-10-03). The fonts are used under their own names only as fallbacks; the
  catalogue's @font-face rules name them "A2UI Recursive" etc. No Reserved Font Name is used for a modified font (none are
  modified).
- **Used by:** the studio pack (preview): `motion_text` `font` + `vary` (animated variable-font axes) and `motion_object3d`
  3D type. See `apps-script-surface/gas-wired-renderer/atoms_studio.gs` (`_MO_VFONTS`).

---

## Three.js (three.js authors)

- **Project:** Three.js — WebGL 3D rendering engine
- **Website:** https://threejs.org/
- **Repository:** https://github.com/mrdoob/three.js
- **License:** MIT License
- **Copyright:** Copyright © 2010-2026 three.js authors
- **Version:** 0.186.1 (npm `latest` dist-tag as pinned 2026-09-29; published 2026-09-24)
- **Vendored as:** `public/vendors/threejs/three.module.js` + `public/vendors/threejs/three.core.js` (the core
  WebGL build, unmodified — this release splits the build across two files, both required),
  `public/vendors/threejs/addons/controls/OrbitControls.js` (official orbit-camera add-on, unmodified),
  `public/vendors/threejs/addons/environments/RoomEnvironment.js` (official procedural studio-lighting
  environment, unmodified — used as `PMREMGenerator` input for real reflections/refraction; builds its scene
  from primitives only, no external HDRI asset), `public/vendors/threejs/addons/postprocessing/` (official
  `EffectComposer`/`RenderPass`/`Pass`/`ShaderPass`/`MaskPass`/`OutputPass`/`GTAOPass`, unmodified — real-time
  ambient occlusion for the Brick Design Lab's Three.js viewer) with their own shader/math dependencies
  under `public/vendors/threejs/addons/shaders/` (`CopyShader`/`OutputShader`/`GTAOShader`/
  `PoissonDenoiseShader`) and `public/vendors/threejs/addons/math/SimplexNoise.js`, and
  `public/vendors/threejs/LICENSE` (verbatim, alongside the source) — fetched, sha256/sha1/sha512-verified and
  extracted by `scripts/fetch_threejs.py` from the pinned
  npm tarball (`https://registry.npmjs.org/three/-/three-0.186.1.tgz`,
  sha256 `8cd068708ea44f2c73c944b1cead2ba2f0d5c15c8fc194e5700f4e4f4a033fe7`), same fetch/verify/vendor discipline
  as `scripts/ldraw/fetch_library.py`.
- **Used by:** (1) the render-appearance proof-of-concept demo at `public/bricksdemo/threejs-demo/` — a
  standalone, additive page demonstrating a material-appearance axis (trans-clear vs. opaque matte finish on the
  same real LDraw part geometry) that the live production renderer's hand-rolled WebGL shader doesn't model; and
  (2) the Brick Design Lab's "View in Three.js" toggle (`public/bricksdemo/design/`,
  `scripts/brick_models/build_design_page.py` + `scripts/brick_models/threejs_view_math.js`), which renders the
  user's actual current build with real per-part material appearance (trans-clear/chrome/metal/pearlescent/
  rubber, from `public/bricksdemo/ldraw_colours_full.json`'s real LDConfig.ldr parse) and a build-step/continuous
  animate view, added 2026-09-29. **Neither use replaces or is used by the existing `atoms_brick.gs` renderer**
  (`rotLDU`/`worldBoxes`/`boxesOverlap`/`_brickKit`/`genBrick`, etc. are untouched) — Three.js is an additional,
  optional view of the same real declarative `partsModel` data, not a replacement renderer.

---

## IBM Plex (IBM Corp.)

- **Project:** IBM Plex — the IBM Plex Mono and IBM Plex Serif type families
- **Website:** https://github.com/IBM/plex
- **License:** SIL Open Font License, Version 1.1
- **Copyright:** Copyright © 2017 IBM Corp. with Reserved Font Name "Plex"
- **Vendored as:** `public/fonts/ibm-plex/ibm-plex-{mono,serif}-<weight>[-italic].woff2`
  (7 static WOFF2 files: Mono 400/500/600/700, Serif 400/400-italic/600,
  Latin subset, unmodified Google Fonts release builds; see `LICENSE.txt`
  alongside them)
- **Used by:** ComponentId/ChildList atoms opting into `use_plex_fonts: true`
  (default) — an inline `@font-face` block referencing
  these files by same-origin URL (`https://a2uicatalog.ai/fonts/ibm-plex/...`).
  See the exceptions note above for the CSP fallback behaviour.

---

## Noto Sans / Noto Sans Mono (Google)

- **Project:** Noto — the Noto Sans and Noto Sans Mono type families
- **Website:** https://fonts.google.com/noto, https://github.com/notofonts
- **License:** SIL Open Font License, Version 1.1
- **Copyright:** Copyright 2022 The Noto Project Authors
- **Vendored as:** `public/fonts/noto/noto-sans-{400,700}.woff2`,
  `public/fonts/noto/noto-sans-mono-{400,700}.woff2` (4 static WOFF2 files,
  Latin subset re-encoded via `pyftsubset` from the upstream Google Fonts
  release builds — glyph outlines unmodified, only the character set
  reduced; see `LICENSE.txt` alongside them, permitted under OFL §2)
- **Used by:** the `promo_carousel_card` atom opting into
  `use_noto_fonts: true` (default) — an inline `@font-face` block referencing
  these files by same-origin URL (`https://a2uicatalog.ai/fonts/noto/...`).
  See the exceptions note above for the CSP fallback behaviour.

---

## Arimo (Google / croscore)

- **Project:** Arimo — a sans-serif metric-compatible with Arial
- **Website:** https://fonts.google.com/specimen/Arimo
- **License:** Apache License 2.0
- **Copyright:** Copyright The Arimo Project Authors
- **Vendored as:** `public/fonts/arimo/arimo-{400,700}.woff2` (2 static WOFF2
  files, Latin subset re-encoded via `pyftsubset` from the upstream release
  builds — glyph outlines unmodified, only the character set reduced; see
  `LICENSE.txt` alongside them)
- **Used by:** the `promo_carousel_card` atom's `font: "arimo"` option (the
  default) — same same-origin `@font-face` mechanism as the other families.

---

## Lato (tyPoland / Łukasz Dziedzic)

- **Project:** Lato — a humanist sans-serif, used here for its true Black (900)
  weight
- **Website:** https://www.latofonts.com/
- **License:** SIL Open Font License, Version 1.1
- **Copyright:** Copyright (c) 2010-2015 by tyPoland Lukasz Dziedzic with
  Reserved Font Name "Lato"
- **Vendored as:** `public/fonts/lato/lato-{400,900}.woff2` (2 static WOFF2
  files, Latin subset re-encoded via `pyftsubset`, glyph outlines unmodified;
  see `LICENSE.txt` alongside them, permitted under OFL §2)
- **Used by:** the `promo_carousel_card` atom's `font: "lato"` option.

---

## UIverse.io community

- **Project:** UIverse — Open-source UI elements
- **Website:** https://uiverse.io
- **License:** MIT License
- **Copyright:** Copyright (c) UIverse contributors

**Adapted atoms (31):**
`stat_card`, `progress_bar`, `badge_group`, `sparkline`, `heatmap`,
`donut_stat`, `css_modal`, `alert_banner`, `toast_notification`,
`loading_skeleton`, `spinner`, `status_pill`, `rating_stars`,
`progress_circle`, `toggle_switch`, `flip_card`, `image_hotspots`,
`css_dropdown_menu`, `star_rating_input`, `segmented_control`,
`zoomable_image`, `custom_checkbox_group`, `css_slide_panel`,
`star_rating_display`, `avatar_group`, `social_proof_banner`,
`cli_command`, `copy_code_button`, `social_share_bar`,
`reaction_group`, `follow_button`

**Modifications made:**
Visual CSS patterns from the UIverse community library were translated into
A2UI's field-based schema. Rendering logic is rewritten in Python
(`renderers/web_article.py`) — no original CSS is distributed. The visual
intent (colours, layout proportions, animation timing) is preserved.
All design credit belongs to the respective UIverse community contributors.

See `vendors/uiverse/MANIFEST.md` for the full pattern-to-atom mapping.

---

## Flowbite

- **Project:** Flowbite — Tailwind CSS Component Library
- **Website:** https://flowbite.com
- **Repository:** https://github.com/themesberg/flowbite
- **License:** MIT License
- **Copyright:** Copyright (c) 2021 Bergside Inc.

**Adapted atoms (16):**
`http_request_block`, `prerequisite_checklist`, `keyboard_shortcut`,
`version_badge`, `experimental_banner`, `key_takeaways`,
`learning_objectives`, `release_notes`, `resources_list`,
`difficulty_badge`, `checklist_interactive`, `time_estimate`,
`newsletter_cta`, `author_bio_card`, `share_quote`, `follow_cta`

**Modifications made:**
Content and documentation component patterns from Flowbite were adapted into
A2UI's surface-agnostic field schema. Tailwind CSS class-driven styling and
Alpine.js interactivity are replaced by self-contained HTML/CSS rendered by
`web_article.py`. No Flowbite source files are distributed.

See `vendors/flowbite/MANIFEST.md` for the full component-to-atom mapping.

---

## shadcn/ui

- **Project:** shadcn/ui — Beautifully designed components
- **Website:** https://ui.shadcn.com
- **Repository:** https://github.com/shadcn-ui/ui
- **License:** MIT License
- **Copyright:** Copyright (c) 2023 shadcn

**Adapted atoms (12):**
`file_tree`, `tabbed_code`, `api_param_table`, `deprecation_notice`,
`json_tree_viewer`, `summary_box`, `changelog_entry`, `sidebar_note`,
`caution_block`, `glossary_inline`, `progress_checkpoint`,
`series_overview_card`

**Modifications made:**
Developer-documentation component patterns from shadcn/ui were translated
from Radix UI / Tailwind CSS React components into A2UI's field schema.
Rendering is recompiled into `web_article.py` with no dependency on React,
Radix UI, or Tailwind. No shadcn/ui source files are distributed.

See `vendors/shadcn/MANIFEST.md` for the full component-to-atom mapping.

---

## OpenUI / Thesys

- **Project:** OpenUI — The Open Standard for Generative UI
- **Repository:** https://github.com/thesysdev/openui
- **License:** MIT License
- **Copyright:** Copyright (c) 2024 Thesys, Inc.

**Adapted atoms (10):**
`form`, `form_input`, `form_select`, `form_radio_group`,
`form_checkbox_group`, `form_switch_group`, `form_slider`,
`form_date_picker`, `modal`, `follow_up_chips`

**Modifications made:**
Component prop schemas are derived from Zod definitions in OpenUI's standard
library (`packages/react-ui/src/genui-lib`, each component's `schema.ts`).
The following adaptations were made:

- React/Zod prop schemas re-expressed as A2UI YAML field definitions
- Field names converted from camelCase to snake_case per A2UI conventions
- `reactive()` wrapper fields (live state bindings) expressed as static
  default values
- Validation rule arrays (`rulesSchema`) preserved as `rules: string[]`
  accepting `"required"`, `"email"`, `"minLength:N"`, `"maxLength:N"`
- `FollowUpBlock` / `FollowUpItem` merged into a single `follow_up_chips`
  atom with `items: string[]`, matching A2UI's flat-field convention
- Rendering recompiled into `web_article.py` — no React, Zod, or runtime
  dependency on the original library

See `vendors/openui/MANIFEST.md` for the full component-to-atom mapping.

---

## ExtendLabs UI

- **Project:** ExtendLabs UI
- **Repository:** https://github.com/extend-labs/ui
- **License:** MIT License
- **Copyright:** Copyright (c) 2024 extendui

**Ported components (11 Lit Web Components):**
`ext-button`, `ext-badge`, `ext-alert`, `ext-card`, `ext-checkbox`,
`ext-input`, `ext-label`, `ext-switch`, `ext-textarea`, `ext-table`,
`ext-tabs`

Located in `components/extendlabs/`. These are derived works — React
components ported to Lit Web Components for the A2UI stateless canvas
framework. Each file carries an in-source attribution comment.

**Modifications made:**
- React state (`useState`, `useReducer`) removed; all visual states are
  prop-driven
- Radix UI, CVA, and lucide-react dependencies replaced with Lit/CSS
  equivalents
- `onClick`/`onChange`/`onBlur` handlers replaced with the A2UI action
  protocol (`a2ui-action` CustomEvent dispatch)
- Tailwind CSS keyframe animations re-implemented as shadow DOM `@keyframes`
  CSS
- Compound React components (e.g. `Card`/`CardHeader`/`CardContent`) collapsed
  into single Lit elements with prop-driven slots

Note: no catalogue atoms were adapted from ExtendLabs UI — these are stage
components, not vocabulary atoms. `inline_alert` is a candidate for future
catalogue adaptation.

See `vendors/extendlabs-ui/MANIFEST.md` for the full component review and
`scripts/vendor_manifests/extendlabs-ui.yaml` for the port mapping.

---

## Deck tools: python-pptx and its dependencies (`tools/deck/`)

- **Used by:** `tools/deck/` (the typed-scene-list and A2UI-payload to PPTX converter). Installed with `pip`, never vendored or
  redistributed here: the packages are listed in `requirements.txt` and fetched by the user.
- **python-pptx** (Steve Canny and contributors): MIT License. https://github.com/scanny/python-pptx
- **lxml**: BSD-3-Clause. https://github.com/lxml/lxml
- **Pillow** (Jeffrey A. Clark and contributors): the PIL Software License (HPND), a permissive licence. https://github.com/python-pillow/Pillow
- **XlsxWriter** (John McNamara; a python-pptx dependency): BSD-2-Clause. https://github.com/jmcnamara/XlsxWriter
- **defusedxml** (Christian Heimes): Python Software Foundation License. Reads the XML deck language and refuses entities.
- **Roboto** (Google): Apache License 2.0. Not vendored and not embedded in generated decks, which only name the font. `tools/deck` reads a
  local copy of the font file to measure text widths when fitting a layout.
- **PPTX format**: the open ECMA-376 / ISO 29500 standard. "PowerPoint" and "Google Slides" are named only to say which programs open the files.
- Parts of the recipe library in `tools/deck/recipes_more.py` were drafted by Gemini 2.5 Pro from each atom's field description and then
  reviewed and tested here.

---

## Diagram Studio view (`public/surfaces/diagram-studio/`, vendored wholesale, unmodified except where noted)

The full per-file notice is `public/surfaces/diagram-studio/NOTICE.md`. In short:

- **draw.io** (JGraph): Apache License 2.0, with the mxGraph viewer it embeds. The viewer has one change (its start-up call that
  fetched MathJax from diagrams.net is replaced by a hook); the self-hosted editor is an unmodified, trimmed copy. The names "draw.io" and
  "diagrams.net" and their logos are trademarks and are not licensed by Apache 2.0: this catalog says "draw.io-compatible" and uses no branding.
- **draw.io icon sets and stencil libraries** (shipped inside the editor as `js/stencils.min.js` and `images/`): the upstream `LICENSE` files in
  the stencil, shape and image folders add a restriction. These sets, and anything derived from them, **may not be used as software assets in, distributed
  for use with, or incorporated into Atlassian products or products distributed through the Atlassian marketplace or plugin ecosystem
  without explicit written permission**. Diagrams and exported images that people make with the editor are not affected. Do not package this
  view, or the stencil bundle, into an Atlassian app.
- **Data mined from draw.io's AWS sidebar** (`tools/diagram/styles/aws.catalogue.json` and the worker's generated `aws-catalogue.js`): service names, stencil ids,
  category colours and group style strings read from draw.io's `Sidebar-AWS4.js` (Apache License 2.0). No artwork is copied; the icons themselves are drawn by draw.io
  from its own library. "AWS-style" in this project means these conventions; it is not affiliated with or endorsed by Amazon, and AWS and the service names are trademarks of Amazon.
- Not shipped here, and so not covered by a licence in this repository: draw.io's `templates/` folder (CC BY 4.0) and its `libavoid-js`
  routing library (LGPL 2.1). If either is ever added to what is served, its licence text and attribution (and, for LGPL, a link to its source and
  a replaceable build) must be added at the same time.
- **Mermaid**: MIT License. **D2** and **@d2lang/d2**: Mozilla Public License 2.0, source at the upstream repository, build unmodified.

---

## MIT License

The MIT License applies to seven vendor projects listed above (QR-Code-
generator, Three.js, UIverse.io community, Flowbite, shadcn/ui, OpenUI /
Thesys and ExtendLabs UI). The full
text is reproduced once here as it is identical across all of them (with
copyright holders as noted per vendor above):

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
