# Vendor: OpenUI / Thesys

**Source:** https://github.com/thesysdev/openui (`packages/react-ui/src/genui-lib`)  
**License:** MIT  
**Atom count:** 15  
**Attribution:** Atoms in this set are derived from OpenUI's standard React component library. Prop schemas are translated from Zod definitions in each component's `schema.ts`. Field names are mapped to A2UI snake_case conventions; rendering is recompiled into `web_article.py` — no React, no Zod, no runtime dependency on the original library.

## Why

The [A2UI vs OpenUI benchmark](../../benchmarks/BENCHMARK.md) (2026-06-12) identified 9 components in OpenUI's standard library with no native A2UI equivalent. These are predominantly interactive/form patterns — the gap exposed when the benchmark ran `contact-form` and `settings-panel` scenarios.

## Component → atom mapping

| OpenUI component | A2UI atom | Adaptation notes |
|---|---|---|
| `Form` + `FormControl` | `form` | Field list + submit wired as a single atom |
| `Input` | `form_input` | text / email / password / url / number |
| `Select` + `SelectItem` | `form_select` | Dropdown with labelled options |
| `RadioGroup` + `RadioItem` | `form_radio_group` | Single-select radio group |
| `CheckBoxGroup` + `CheckBoxItem` | `form_checkbox_group` | Multi-select checkbox group |
| `SwitchGroup` + `SwitchItem` | `form_switch_group` | Named toggle switches |
| `Slider` | `form_slider` | Continuous or discrete numeric range |
| `DatePicker` | `form_date_picker` | Single date or date-range picker |
| `Modal` | `modal` | Dialog overlay, content-agnostic |
| `FollowUpBlock` + `FollowUpItem` | `follow_up_chips` | Conversation follow-up suggestion chips |

### From OUI benchmark samples (OpenUI Lang format — MIT)

Source: `github.com/thesysdev/openui/benchmarks/samples`. Patterns identified while mapping the 7 benchmark scenarios to A2UI atoms.

| OUI pattern | A2UI atom | Adaptation notes |
|---|---|---|
| `TagBlock(tagList)` | `tag_block` | Horizontal chip wrap; neutral styling; distinct from status-coloured badge_group |
| `RadioGroup` + `RadioItem(value, title, description)` | `variant_selector` | CSS `:has(input:checked)` card picker; supports label + description per option |
| `MarkDownRenderer(content)` | `markdown_block` | GFM markdown → HTML via Python `markdown` library; tables + fenced code supported |
| `PieChart(slices, variant)` + `Slice(label, value)` | `chartjs_pie` | Inline SVG pie/donut; multi-slice with auto-colour legend; `donut_stat` covers single-value rings only |
| `TextCallout(variant, title, description)` | `text_callout` | Lightweight tinted tip block; no left-border accent or icon; used inline inside cards/forms |

## Surface notes

Form atoms render on `web` and `meet-stage` (CSS-only rendering). Submit actions on `meet-stage` are `degraded` — inputs are interactive but data capture requires stage-level routing. `modal` is fully interactive on both surfaces via CSS `:checked` toggle. `follow_up_chips` render correctly on both; click actions require routing wired up to produce AI responses. Google Chat, email, and PDF are incompatible with all interactive atoms in this set.

## Prop schema source

Validation rule arrays are adapted from Zod's `rulesSchema` — exposed as optional `rules: string[]` accepting `"required"`, `"email"`, `"minLength:N"`, `"maxLength:N"`. Type values (`text`, `email`, `password`, `url`, `number`, `textarea`, `select`) are preserved from the original `InputType` enum.
