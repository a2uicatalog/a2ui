# Vendor: UIverse.io community

**Source:** https://uiverse.io  
**License:** MIT  
**Atom count:** 31  
**Attribution:** Atoms in this set are adapted from CSS/HTML component patterns published by the UIverse community. UIverse is an open-source library of community-contributed CSS components; each pattern is tagged by type (card, button, loader, etc.). Adaptations translate the visual pattern into A2UI's field-based schema — the CSS rendering logic is recompiled into `web_article.py`; no original CSS is shipped.

## Why

UIverse filled two gaps the original a2ui didn't cover: (1) visual micro-components — spinners, skeletons, pills, rating stars — that appear in live product UIs but not in document-style article atoms; (2) interactive CSS-only patterns (toggle, dropdown, slide panel, flip card) where the interactivity is pure CSS and therefore works across surfaces without JS.

## Pattern → atom mapping

| UIverse pattern type | A2UI atom | Adaptation notes |
|---|---|---|
| Stat / KPI card | `stat_card` | label + value + delta + accent colour |
| Progress bar | `progress_bar` | label + value + max; percentage computed |
| Badge / label chip | `badge_group` | array of label strings, colour variants |
| Sparkline / mini chart | `sparkline` | inline SVG path from data array |
| Calendar heatmap | `heatmap` | 2-D grid of (date, intensity) cells |
| Donut / ring stat | `donut_stat` | single value + ring; CSS only, no chart lib |
| CSS modal (checkbox trick) | `css_modal` | trigger text + title + body; display:none toggle |
| Alert / notification banner | `alert_banner` | kind (info/success/warning/error) + message + optional action |
| Toast notification | `toast_notification` | message + kind + optional duration hint |
| Skeleton loader | `loading_skeleton` | lines + optional avatar placeholder |
| Spinner | `spinner` | size + colour; purely decorative |
| Status pill | `status_pill` | label + status (active/pending/error/…) |
| Star rating display | `rating_stars` | value (0–5) + count |
| Circular progress ring | `progress_circle` | value + max + label |
| Toggle switch | `toggle_switch` | label + name + default_checked |
| Flip card | `flip_card` | front (title + body) + back (title + body) |
| Image hotspot overlay | `image_hotspots` | image src + array of (x, y, label, detail) |
| CSS dropdown menu | `css_dropdown_menu` | trigger label + items array |
| Interactive star input | `star_rating_input` | name + max + default_value |
| Segmented control | `segmented_control` | name + options array; radio-group display |
| Zoomable image | `zoomable_image` | src + alt; click-to-zoom via CSS |
| Styled checkbox group | `custom_checkbox_group` | label + options; CSS-styled checkboxes |
| Slide-in panel / drawer | `css_slide_panel` | trigger label + title + body |
| Read-only star rating | `star_rating_display` | value + count; no input |
| Stacked avatar group | `avatar_group` | images array + overflow_count |
| Social proof strip | `social_proof_banner` | stats array + logo URLs |
| Copyable CLI command | `cli_command` | command string + optional prompt prefix |
| Copy-to-clipboard button | `copy_code_button` | text to copy + button label |
| Social share bar | `social_share_bar` | url + title + platforms array |
| Emoji reaction row | `reaction_group` | reactions array (emoji + count) |
| Follow / subscribe button | `follow_button` | platform + handle + label |

## Surface notes

CSS-only interactive patterns (`css_modal`, `toggle_switch`, `css_dropdown_menu`, `css_slide_panel`, `flip_card`, `zoomable_image`) work on `web` and in `gdm-html-panel` `srcdoc` iframes (`meet-stage`) because they require no JavaScript — all interactivity is `:checked`/`:hover`/`:focus` CSS state. They are incompatible with Google Chat cards, email clients, and PDF renderers.
