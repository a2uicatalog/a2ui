---
category: content
title: Content & Typography
atom_count: 27
platform_support:
  web: 27/27
  meet-stage: 0/27
  googlechat: 0/27
  google-apps-script-web: 27/27
  email: 0/27
  pdf: 0/27
maturity: stable
source: atoms/schema.yaml
---

# Content & Typography

> 27 atoms · `*` = degraded (limited support) · Bold surface = full support

| Atom type | Description | Surfaces | Key fields |
|-----------|-------------|----------|------------|
| `intro` | series link or transparency note at article top | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `series_label` — string<br>`series_url` — url<br>`continuation` — string (optional)<br>`note` — string (optional) |
| `body` | prose paragraph block | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `text` — string |
| `heading` | H2 section title | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `text` — string |
| `subheading` | H3 subsection title | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `text` — string |
| `quote` | pull quote or blockquote with attribution | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `text` — string<br>`attribution` — string (optional) |
| `callout` | coloured tip info warning or danger highlight box | **Web/Blog** · **GAS Web App** · **PDF** | `kind` — info | warning | tip | danger<br>`title` — string (optional)<br>`text` — string |
| `alert_banner` | full-width status alert strip optional action. | **Web/Blog** · **GAS Web App** | `message` — string The main message to display in the banner.<br>`type` — string The type of alert (e.g., "info", "warning", "error", "success").<br>`icon` — string Optional icon name to display next to the message.<br>`action_label` — string Optional text for an action button.<br>`action_url` — string Optional URL for the action button. |
| `blockquote_with_avatar` | testimonial quote with avatar and attribution | **Web/Blog** · **GAS Web App** · **PDF** | `quote` — string (the quoted text)<br>`author_name` — string (name of the person quoted)<br>`author_title` — optional string (title or role of the person)<br>`avatar_url` — optional string (URL to the author's avatar image) |
| `pull_stat` | large display number pulled from prose for emphasis descriptive label. | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `value` — string (the prominent number/statistic, e.g., "99%", "1.2M")<br>`label` — string (descriptive text for the stat, e.g., "customer satisfaction")<br>`unit` — optional string (e.g., "%", "users", "USD")<br>`color` — optional string (hex code or named color for the value) |
| `footnote` | numbered footnote reference at the bottom of a section or page. | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `number` — integer (the footnote number)<br>`text` — string (the footnote content)<br>`id` — string (unique identifier for linking, e.g., "fn1") |
| `glossary_term` | definition term with explanation more details. | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `term` — string (the term itself)<br>`definition` — string (the explanation)<br>`link_text` — optional string (e.g., "Learn more")<br>`link_url` — optional string (URL for more details) |
| `glossary_inline` | inline hover tooltips for complex technical term definitions | **Web/Blog** · **GAS Web App** | `term` — string. The technical phrase needing definition.<br>`definition` — string. Explanation displayed when term is activated. |
| `text_callout` | lightweight tinted inline tip or note block no icon | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `variant` — string. Display variant — "info", "success", "warning", "neutral".<br>`title` — string. Short bold label (e.g. "Tip", "Note", "Good to know").<br>`description` — string. Body text. |
| `source_citation` | numbered RAG source card with title excerpt and URL | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `sources` — List of {number, title, url?, excerpt?, author?, date?} citation objects.<br>`heading` — string (optional). Section heading above the list, e.g. "Sources". |
| `sidebar_note` | off-axis container for peripheral notes or caveats | **Web/Blog** · **GAS Web App** | `title` — string. The headline for the side note.<br>`content` — string. The note content. |
| `caution_block` | highlight dangerous pitfalls or critical destructive actions | **Web/Blog** · **GAS Web App** | `message` — string. The warning content. |
| `key_takeaways` | highlighted summary of main conclusions and critical takeaways | **Web/Blog** · **GAS Web App** | `points` — array. Core sentences highlighting the key learnings. |
| `summary_box` | condensed introductory panel with article overview | **Web/Blog** · **GAS Web App** | `text` — string. The summary narrative block. |
| `learning_objectives` | checklist of educational goals and competencies gained post-reading | **Web/Blog** · **GAS Web App** | `objectives` — array. Statements describing individual knowledge achievements. |
| `difficulty_badge` | label technical complexity level of blog content | **Web/Blog** · **GAS Web App** | `level` — string: beginner | intermediate | advanced. The target audience expertise tier. |
| `time_estimate` | estimated reading duration badge for article content | **Web/Blog** · **GAS Web App** | `minutes` — integer. The estimated reading time in minutes. |
| `highlighted_text` | highlighted text passage with optional hover margin annotation note | **Web/Blog** · **GAS Web App** · **PDF** | `text` — string. The passage to highlight.<br>`annotation` — string (optional). Margin note revealed on hover.<br>`color` — string (optional). Highlight background colour. Default "#fef08a" (yellow).<br>`annotation_color` — string (optional). Annotation pill background. Default "#fbbf24". |
| `abbr_tooltip` | inline abbreviation with hover tooltip full form | **Web/Blog** · **GAS Web App** | `text` — string. The abbreviation to display.<br>`title` — string. The expanded full form. |
| `inline_alert` | inline icon-plus-text alert embedded in content flow | **Web/Blog** · **GAS Web App** | `type` — string. Severity level — "info", "warning", "error", or "success".<br>`message` — string. The alert text.<br>`detail` — string (optional). A secondary line of smaller detail text.<br>`icon` — string (optional). Override the default icon for the severity type. |
| `lozenge` | Atlassian-semantic status pill with defined appearance variants | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `text` — string. The lozenge label (single lozenge mode).<br>`appearance` — string (optional). One of default | success | removed | inprogress | moved | new. Default default.<br>`items` — array (optional). List of {text, appearance} for a row of multiple lozenges. Overrides single text/appearance fields. |
| `closing` | article closing paragraph with hashtags | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `text` — string<br>`tags` — list[string] (optional) |
| `divider` | horizontal visual section break | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | — |
