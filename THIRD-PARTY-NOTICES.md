# Third-Party Software Notices

This repository (`curtiskrygier/a2ui`) derives atoms from open-source
component libraries. No vendor source files are stored here — adaptations are
documented in `vendors/<vendor>/MANIFEST.md` and the rendering logic is
recompiled from scratch into `renderers/web_article.py`. Each atom carries a
`source` field in `atoms/schema.yaml` identifying its origin.

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

## MIT License

The MIT License applies to all five vendor projects listed above. The full
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
