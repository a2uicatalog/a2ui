---
category: lists_and_structure
title: Lists, Tables & Structure
atom_count: 28
platform_support:
  web: 28/28
  meet-stage: 0/28
  googlechat: 0/28
  google-apps-script-web: 28/28
  email: 0/28
  pdf: 0/28
maturity: stable
source: atoms/schema.yaml
---

# Lists, Tables & Structure

> 28 atoms · `*` = degraded (limited support) · Bold surface = full support

| Atom type | Description | Surfaces | Key fields |
|-----------|-------------|----------|------------|
| `bullet_list` | unordered list with optional bold label per item | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `items` |
| `steps` | numbered step-by-step instruction sequence | **Web/Blog** · **GAS Web App** · **PDF** | `items` |
| `pipeline` | left-to-right step flow diagram | **Web/Blog** · **GAS Web App** · **PDF** | `steps` — list[string] |
| `timeline` | chronological event timeline | **Web/Blog** · **GAS Web App** · **PDF** | `title` — string (optional)<br>`accent` — string (optional)<br>`events` |
| `checklist_interactive` | interactive task tracking checklist for article milestones | **Web/Blog** · **GAS Web App** | `items` — array. Individual checkpoint task strings. |
| `task_list` | glassmorphic structured checklist with priority and assignee badges | **Web/Blog** · **GAS Web App** | `title` — string (optional, e.g., 'Google Tasks & Action Items')<br>`tasks` — list of dictionaries representing tasks, where each dictionary contains: {'id': string, 'text': string, 'completed': boolean, 'priority': string (high|medium|low), 'due_date': string (optional), 'assignee': string (optional, initials e.g. 'CK')} |
| `prerequisite_checklist` | highlight prerequisite knowledge and system requirements before | **Web/Blog** · **GAS Web App** | `title` — string. Custom header text for the prerequisite warning block.<br>`items` — array. Strings containing descriptions of individual setup requirements. |
| `changelog_entry` | timeline entry documenting product modifications per release | **Web/Blog** · **GAS Web App** | `version` — string. The release tag or identifier.<br>`date` — string. The publication date of the changes.<br>`changes` — array. Objects outlining specific features modified, categorised by type. |
| `release_notes` | grouped product release documentation by change category | **Web/Blog** · **GAS Web App** | `title` — string. Header name for the release notice.<br>`added` — array. Optional new features added in this release.<br>`fixed` — array. Optional bugs resolved in this release.<br>`changed` — array. Optional modifications to existing behaviour. |
| `further_reading` | curated references for extending topic research | **Web/Blog** · **GAS Web App** | `links` — array. Objects containing resource titles, URLs, and brief annotations. |
| `resources_list` | downloadable project assets and attached resource links | **Web/Blog** · **GAS Web App** | `items` — array. Download assets containing title, size, type, and url. |
| `key_value` | label and value pairs in a compact grid | **Web/Blog** · **GAS Web App** · **PDF** | `title` — string (optional)<br>`items` |
| `table` | data table with header row on mobile | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `caption` — string (optional)<br>`headers` — list[string]<br>`rows` — list[list[string]] |
| `table_of_contents` | navigate article sections using structured heading directory links | **Web/Blog** · **GAS Web App** | `headings` — array. Structured items detailing section names and anchor tags. |
| `breadcrumb` | navigation breadcrumb trail structure. | **Web/Blog** · **GAS Web App** | `items` — list of {label: string, url: string, is_current: boolean} |
| `pagination` | page number controls | **Web/Blog** · **GAS Web App** | `current_page` — integer<br>`total_pages` — integer<br>`base_url` — string (the URL prefix for all page links)<br>`page_param` — string (e.g., 'page', the query parameter name for the page number) |
| `anchor_list` | in-page anchor navigation links document or to external URLs. | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `anchors` — list of {label: string, url: string, target_id: string (optional, for in-document navigation on web/pdf)} |
| `accordion_item` | single collapsible section with toggle by clicking its header, using only CSS. | **Web/Blog** · **GAS Web App** | `header` — string The title or label for the collapsible section.<br>`content` — string The main content to be shown or hidden. |
| `faq_accordion` | collapsible FAQ question and answer list the question is clicked. | **Web/Blog** · **GAS Web App** · **PDF** | `items` — list of objects, each with 'question' (string) and 'answer' (string) |
| `collapsible_panel` | expandable content panel with header toggle visible and hidden states by clicking a control, using only CSS. | **Web/Blog** · **GAS Web App** | `toggle_label` — string The text for the control that expands/collapses the content.<br>`initial_state` — string, default "collapsed" The initial state of the panel ("expanded" or "collapsed").<br>`content` — string The main content to be shown or hidden. |
| `expandable_text` | truncated text with read more expand toggle more content. | **Web/Blog** · **GAS Web App** | `summary` — string<br>`details` — string<br>`initial_state_expanded` — boolean |
| `expandable_list` | nested expandable tree list with collapsible children | **Web/Blog** · **GAS Web App** | `items` — array of {text, children}. Tree nodes. |
| `footnote_group` | numbered footnote list at section or article end | **Web/Blog** · **GAS Web App** · **Email** | `footnotes` — array of {id, text}. Footnote entries. |
| `tag_block` | horizontal wrap of neutral content chip labels | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `tags` — array of strings. The tag labels.<br>`color` — string (optional). Override chip accent — hex or CSS colour. Default is neutral gray. |
| `badge_group` | row of coloured label badges | **Web/Blog** · **GAS Web App** | `title` — string (optional)<br>`badges` |
| `status_pill` | coloured status pill badge an item. | **Web/Blog** · **GAS Web App** | `label` — string The text label for the status.<br>`color` — string The semantic color of the pill (e.g., "success", "warning", "error", "info", "neutral").<br>`icon` — string Optional icon to display within the pill. |
| `carousel` | horizontally scrollable card carousel | **Web/Blog** · **GAS Web App** | `accent` — string (optional)<br>`caption` — string (optional)<br>`slides` |
| `tree_view` | recursive hierarchical tree with expand/collapse per node | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `title` — string (optional). Label above the tree panel.<br>`nodes` — array. Recursive list of {label, icon?, expanded?, meta?, children?[]} node objects. |
