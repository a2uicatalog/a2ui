# Vendor: ExtendLabs UI

**Source:** https://github.com/extendlabs/ui
**License:** MIT — Copyright (c) 2024 extendui
**Stage components:** 12 (Lit Web Components in `components/extendlabs/`)
**Schema atoms:** 0 (coverage handled by existing a2ui / OpenUI atoms — see table below)

## Status

All 12 ExtendLabs UI components have been ported to Lit Web Components under
`components/extendlabs/`. These ship as `ext-*` custom elements on the meet-stage
surface — they are **not** schema atoms and do not go through `web_article.py`.

Components are ported with:
- React state removed; props mapped 1-to-1 where possible
- `onClick` / `onChange` → A2UI action protocol (`functionCall` | `event`)
- Tailwind/CVA animations reproduced in Lit `static styles = css\`...\``
- `color` prop added to every component for hex accent override (default: `#00f2ff` cyan)

## Stage components

| Custom element | Source file | Variants / key props | Surface |
|---|---|---|---|
| `ext-button` | `button.tsx` | default · outline · ghost · ringHover · glowingRing · shimmer · perimeterShimmer · bouncing; sizes: sm/md/lg/hero | stage |
| `ext-badge` | `badge.tsx` | default · secondary · destructive · outline | both |
| `ext-alert` | `alert.tsx` | default · destructive | both |
| `ext-card` | `card.tsx` | title · description · content · footer | both |
| `ext-checkbox` | `checkbox.tsx` | checked · disabled · label · action | both |
| `ext-input` | `input.tsx` | default · filled · flushed; type: text/email/number/password/search | both |
| `ext-label` | `label.tsx` | text · for | both |
| `ext-switch` | `switch.tsx` | checked · disabled · label · action | both |
| `ext-textarea` | `textarea.tsx` | rows · maxLength · disabled · action | both |
| `ext-table` | `table.tsx` | headers (JSON) · rows (JSON) · caption · fontSize: sm/md/lg | stage |
| `ext-tabs` | `tabs.tsx` | tabs (JSON: [{id,label,content}]) · value · action | both |

## A2UI atom coverage mapping

| ExtendLabs component | Covered by atom | Notes |
|---|---|---|
| `ext-button` | — | No button atom — layout primitive; stage uses `gdm-button` or `ext-button` |
| `ext-badge` | `badge_group` (UIverse) | Schema atom preferred for web/email/pdf |
| `ext-alert` | `inline_alert` (a2ui) | Schema atom added; ext-alert for stage use |
| `ext-card` | `stat_card`, `hover_card` | Layout handled by renderer internals |
| `ext-checkbox` | `form_checkbox_group` (OpenUI) | Schema atom preferred |
| `ext-input` | `form_input` (OpenUI) | Schema atom preferred |
| `ext-label` | — | Internal to form renderers |
| `ext-switch` | `form_switch_group` (OpenUI) | Schema atom preferred |
| `ext-textarea` | `form_input` type=textarea (OpenUI) | Schema atom preferred |
| `ext-table` | `table` (a2ui), `data_grid` (Carbon) | Schema atoms preferred; ext-table for stage |
| `ext-tabs` | `tabs` (a2ui), `tab_bar` (a2ui) | Schema atoms preferred; ext-tabs for stage |

## Design tokens used

| Token | Value | Usage |
|---|---|---|
| Accent (default) | `#00f2ff` | Button fill, border, glow |
| Dark bg | `#0a0f1e` | Button text on filled variants |
| Border radius | `8px` (md), `6px` (sm), `10px` (lg) | All components |
| Font | JetBrains Mono / Fira Code / monospace | Button label |
| Transition | `all 0.2s cubic-bezier(0.4, 0, 0.2, 1)` | All interactive states |

## Animations

| Name | Keyframes | Used by variant |
|---|---|---|
| `ext-shimmer` | background-position 200% → -200% | shimmer |
| `ext-glow` | box-shadow pulse 0→3px | glowingRing |
| `ext-perimeter` | gradient walks border | perimeterShimmer |
| `ext-bounce` | translateY 0 → -5px | bouncing |

## Usage (stage fiber)

```yaml
# In a playbook builder — ext-button
{"id": "btn", "component": "ext-button",
 "text": "Fire Slide", "variant": "glowingRing", "size": "md",
 "color": "#818cf8",
 "action": {"functionCall": {"call": "fireEndpoint", "args": {"endpoint": "/api/playbook/fire/demo/next/default"}}}}

# ext-badge (inside gdm-html-panel)
<ext-badge text="Active" variant="default" color="#10b981"></ext-badge>
```
