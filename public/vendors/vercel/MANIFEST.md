# Vendor: Vercel Geist Design System

**Source:** https://vercel.com/geist/introduction  
**License:** Internal design system — patterns adapted by reference (not source code distribution)  
**Atom count:** 0 (candidate analysis — no atoms adapted yet)  
**Note:** Geist components are documented publicly at vercel.com/geist but are not published as an open-source package. Adaptation follows the same pattern-translation approach used for shadcn/ui — field schemas derived from documented props, rendering recompiled into `web_article.py`.

## Coverage audit (2026-06-12)

Geist has 70 components. 56 already map to existing A2UI atoms; 11 are layout primitives not exposed as atoms; 6 are genuine gaps.

### Layout primitives (not A2UI atoms)

| Geist component | Reason |
|---|---|
| `Button` | Layout primitive; A2UI doesn't expose standalone buttons |
| `Card` | Layout primitive; card styling is baked into renderer atoms |
| `Grid` | Layout primitive |
| `Label` | Part of form atom internals |
| `Menu` | Covered by `css_dropdown_menu` or layout context |
| `Dots Menu` | Layout primitive (kebab trigger) |
| `Scroller` | Layout primitive |
| `MiddleTruncate` | Text utility; no standalone atom value |
| `Browser` | Decorative frame only |
| `Book` | Navigation wrapper |
| `Theme Switcher` | System UI; not a content atom |

### Already covered by existing atoms

| Geist component | A2UI atom |
|---|---|
| `Avatar` | `avatar_group` |
| `Badge` | `badge_group`, `status_pill`, `version_badge` |
| `Banner` | `alert_banner` |
| `Breadcrumbs` | `breadcrumb` |
| `Calendar` | `form_date_picker` |
| `Checkbox` | `form_checkbox_group` |
| `Clearable Input` | `form_input` |
| `Code` | `code`, `code_snippet_pair` |
| `Code Block` | `annotated_code`, `tabbed_code` |
| `Collapse` | `collapsible_panel`, `faq_accordion` |
| `Combobox` | `form_select` |
| `Command Menu` | `command_palette` |
| `Context Card` | `hover_card` |
| `Context Menu` | `css_dropdown_menu` |
| `Copy Button` | `copy_code_button`, `copy_to_clipboard` |
| `Deployment Status` | `status_dashboard` (partial) |
| `Description` | `body` |
| `Destructive Action Modal` | `modal` |
| `Drawer` | `css_slide_panel` |
| `Empty State` | `empty_state` |
| `Error` / `Error Card` | `callout` (warning variant) |
| `Fieldset` | `form` |
| `File Tree` | `file_tree` |
| `Gauge` | `gauge_sla` |
| `Input` | `form_input` |
| `Keyboard Input` | `keyboard_shortcut` |
| `Loading Dots` | `spinner`, `loading_skeleton` |
| `Modal` | `modal` |
| `Multi Select` | `form_checkbox_group` |
| `Note` | `sidebar_note`, `callout` |
| `Pagination` | `pagination` |
| `Phone` | `form_input` (text type) |
| `Pill` | `status_pill` |
| `Progress` | `progress_bar`, `progress_circle` |
| `Project Banner` | `article_hero` |
| `Radio` | `form_radio_group` |
| `Search Input` | `form_input` |
| `Select` | `form_select` |
| `Separator` | `divider` |
| `Sheet` | `css_slide_panel` |
| `Show more` | `expandable_text` |
| `Skeleton` | `loading_skeleton` |
| `Slider` | `form_slider` |
| `Snippet` | `cli_command`, `copy_code_button` |
| `Spinner` | `spinner` |
| `Status Dot` | `status_pill` |
| `Switch` | `toggle_switch`, `form_switch_group` |
| `Table` | `table`, `data_table_sortable` |
| `Tabs` | `tabs`, `tab_bar` |
| `Text With Copy Button` | `copy_to_clipboard` |
| `Textarea` | `form_input` (textarea type) |
| `Toast` | `toast_notification` |
| `Toggle` | `toggle_switch` |
| `Tooltip` | `tooltip`, `abbr_tooltip` |
| `Video` | `video_card`, `youtube` |

---

## Candidate atoms (genuine gaps)

### Priority 1 — High value

#### `choicebox_group`
**Geist component:** `Choicebox`  
**Pattern:** Card-style option selector where each option renders as a full card (icon + title + description) rather than a radio button label. The entire card is the click target. Used for plan selection, framework choice, setup wizards.

Distinct from `form_radio_group`: radio buttons are compact label-value pairs; choicebox cards carry rich descriptive content and work well in AI-generated onboarding flows.

Proposed schema:
```yaml
type: choicebox_group
fields:
  name: string          # form field name
  label: string         # group label (optional)
  multiple: boolean     # false = single select (radio), true = multi (checkbox)
  submit_label: string  # optional inline submit button
  items:
    - value: string
      title: string
      description: string
      icon: string      # optional emoji or icon name
      disabled: boolean
```

#### `feedback_prompt`
**Geist component:** `Feedback`  
**Pattern:** In-context feedback collection widget — thumbs up/down or 1–5 stars, with optional follow-up text input after selection. Used for AI response quality rating, content helpfulness, feature satisfaction.

Distinct from `inline_feedback_message` (which is a notification *to* the user); this collects feedback *from* the user. Very AI-native — natural fit for appending to any AI-generated article or slide.

Proposed schema:
```yaml
type: feedback_prompt
fields:
  question: string      # e.g. "Was this helpful?"
  style: string         # thumbs | stars | nps
  placeholder: string   # optional follow-up text placeholder
  action_url: string    # endpoint for POST
```

---

### Priority 2 — Medium value

#### `entity_card`
**Geist component:** `Entity`  
**Pattern:** Named resource row with avatar/icon, title, subtitle, and a status badge. Vercel uses it to represent projects, deployments, teams. Useful for infra dashboards, CI/CD pipeline lists, user/team rosters.

Partially covered by `status_dashboard` but that's a full table of named metrics. `entity_card` is a single named resource with richer metadata. Could also be expressed as a list of items.

Proposed schema:
```yaml
type: entity_list
fields:
  items:
    - name: string
      subtitle: string
      icon: string      # optional emoji or URL
      status: string    # active | inactive | error | pending
      meta: string      # optional trailing metadata (e.g. "3 members", "2h ago")
```

---

### Priority 3 — Low value (not recommended)

| Geist component | Gap description | Reason not to add |
|---|---|---|
| `Load More Button` | Styled pagination trigger | Not enough content to warrant its own atom; `pagination` covers the use case |
| `Split Button` | Primary action + dropdown | Buttons are layout primitives in A2UI; no standalone button atoms exist |
| `Relative Time Card` | "2 days ago" inline timestamp | Too small; a `key_value` or `body` atom covers this pattern |

---

## Recommendation

Implement `choicebox_group` and `feedback_prompt` as the first Geist-sourced atoms. Both fill real gaps in the interactive vocabulary — `choicebox_group` for richer form flows, `feedback_prompt` for AI-native quality signals. `entity_list` is worth adding if the catalogue expands into infrastructure/ops use cases.

Note: Geist is not MIT — no license block needed in `THIRD-PARTY-NOTICES.md` since we're adapting patterns by reference, not distributing derived source files. If this position changes, add a section noting pattern reference under fair use with attribution to Vercel.
