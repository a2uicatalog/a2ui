---
category: ai_and_agent
title: AI & Agent Components
atom_count: 9
platform_support:
  web: 7/9
  meet-stage: 0/9
  googlechat: 0/9
  google-apps-script-web: 9/9
  email: 0/9
  pdf: 0/9
maturity: stable
source: atoms/schema.yaml
---

# AI & Agent Components

> 9 atoms · `*` = degraded (limited support) · Bold surface = full support

| Atom type | Description | Surfaces | Key fields |
|-----------|-------------|----------|------------|
| `model_card` | AI model spec card with context window, pricing, and capability badges | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `name` — string. Model display name, e.g. "Claude Sonnet 4.6".<br>`provider` — string (optional). Provider name, e.g. "Anthropic".<br>`context_window` — string (optional). e.g. "200 k tokens".<br>`pricing` — string (optional). e.g. "$3 / M tokens in".<br>`capabilities` — List of short capability badge strings, e.g. ["tool use", "vision", "streaming"].<br>`accent` — string (optional, default #7c3aed). Accent colour for provider label and badges. |
| `conversation_snippet` | user prompt and AI response as chat bubbles | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `user_label` — string (optional, default "You"). Label above the user bubble.<br>`user` — string. The user prompt text.<br>`ai_label` — string (optional, default "Assistant"). Label above the AI bubble.<br>`response` — string. The AI response text.<br>`accent` — string (optional, default |
| `llm_comparison_table` | side-by-side multi-model output comparison table | **Web/Blog** · **GAS Web App** · **PDF** | `prompt` — string (optional). The shared input prompt shown above the comparison.<br>`models` — List of {name, output, latency_ms?, cost_usd?, tokens?} model result objects.<br>`show_meta` — boolean (optional). Show latency/cost/token row below each output. Default true if any model provides meta fields. |
| `confidence_bar` | labelled probability bar with colour-coded confidence fill | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `label` — string. What is being measured, e.g. Positive Sentiment or Retrieval Relevance.<br>`value` — number. Confidence percentage 0-100.<br>`items` — array (optional). List of {label, value} for multi-row display instead of single bar.<br>`color` — string (optional). Override bar fill colour. Auto-assigned green/amber/red by value band if omitted. |
| `token_budget_meter` | context window token usage meter with capacity warning colours | **Web/Blog** · **GAS Web App** · **PDF** | `used` — integer. Tokens consumed so far.<br>`total` — integer. Model context window size, e.g. 200000.<br>`model` — string (optional). Model name shown as subtitle, e.g. "claude-sonnet-4-6".<br>`label` — string (optional). Override the default "Context window" heading.<br>`warn_at` — number (optional). Percentage threshold to shift to amber. Default 70.<br>`critical_at` — number (optional). Percentage threshold to shift to red. Default 90.<br>`animate` — boolean (optional). Count up from 0 to `used` using CSS @property animation. Bar grows in sync. Uses dark styling suited to Meet stage. Default false (static).<br>`duration` — number (optional). Animation duration in seconds when animate is true. Default 2.0. |
| `feedback_prompt` | thumbs or star rating feedback collection widget | **Web/Blog** · **GAS Web App** | `question` — string (optional). Label text above the widget. e.g. "Was this helpful?"<br>`style` — string (optional). One of: thumbs | stars. Default: thumbs.<br>`placeholder` — string (optional). Follow-up textarea placeholder shown after the rating buttons.<br>`action_url` — string (optional). Endpoint for form POST on submit. |
| `markdown_block` | GFM markdown string rendered to HTML inline | **Web/Blog** · **GAS Web App** · **Email** · **PDF** | `content` — string. The Markdown source string to render.<br>`variant` — string (optional). "default" (standard margins) or "compact" (tight spacing for dense layouts). Default is "default". |
| `doc_ai_summary` | AI-powered Google Doc summary via Vertex AI Gemini | **GAS Web App** | `doc_id` — string. Google Doc ID to summarise.<br>`prompt` — string (optional). Instruction sent to Gemini before the doc text.<br>`title` — string (optional). Override card title. Defaults to the doc name.<br>`model` — string (optional). Gemini model override. Defaults to VERTEX_MODEL property.<br>`max_chars` — integer (optional). Max doc characters sent to Gemini. Default 12000.<br>`accent` — string (optional). Accent colour.<br>`show_meta` — boolean (optional). Show word count and doc link. Default true. |
| `multi_doc_ai_brief` | multi-doc briefing pack — one Gemini summary card per Google Doc | **GAS Web App** | `docs` — array. Array of {doc_id, title?, prompt?} objects.<br>`default_prompt` — string (optional). Fallback prompt for docs without their own.<br>`accent` — string (optional). Accent colour for doc links.<br>`model` — string (optional). Gemini model override. |
