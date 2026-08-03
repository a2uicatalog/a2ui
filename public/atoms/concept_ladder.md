# Concept Ladder

A layered-depth concept explainer — an opening hook line, a hero "mental model" card carrying the one-line analogy, then depth rungs down a connected rail, each rung one level deeper into the concept, terminating in a worked-example rung. Shares article_journey's warm palette token system (paper/ink/accent/mono-* etc. via the palette field) and IBM Plex fonts so the article atoms read as one design system. renderers/web_article.py is the reference implementation; apps-script-surface/gas-wired-renderer/atoms_concept.gs is the port that carries it to every other surface (GAS ?p= URLs, the MCP Apps bundle and the Worker's /api/render all compile from the .gs sources), verified at parity against the reference.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Main heading. |
| eyebrow | string (optional). Small uppercase label above the title. |
| dek | string (optional). Italic one-line subtitle under the title. |
| source | object (optional) — {title, url, author?, publication?, published?, read_minutes?, label? (default "Analysis of"), steered_by?}. Set this whenever the ladder explains SOMEONE ELSE'S work: it renders an attribution bar ABOVE the eyebrow and headline, with the source title as a real link, so the artifact reads at first glance as a piece ABOUT that piece rather than a standalone article that could be mistaken for — or stand in for — the original. Provenance is structural here, not a phrasing convention: a derivative reading that hides its source is the copyright-and-honesty failure this field exists to make impossible. Omit for original work. `steered_by` (string or array of strings, optional) records what the reader asked this reading to look for, rendered under a READING STEERED BY rule inside the same bar — a steered reading is a different object from a neutral one, and which one you are looking at should never have to be inferred. Backtick spans render as inline code. |
| hook | string (optional). The opening grabber — rendered as a large accent-barred paragraph before the model card. Backtick spans render as inline code. |
| model | string (optional). The one-line mental-model analogy ("think of it as...") — rendered as a hero card labelled THE MODEL. Backtick spans render as inline code. |
| model_note | string (optional). One short elaboration line under the analogy inside the model card. |
| rungs | array (required). Each item is a concept_rung atom object (see that type) — also independently addressable by ComponentId when emitted in the A2UI v1.0 ChildList wire format, so a live agent can deepen or patch one level without resending the whole surface. |
| closing_note | string (optional). Italic closing line under the rungs. Backtick spans render as inline code. |
| theme | string (optional). 'light' (default) or 'dark' — selects the base palette before any per-token overrides. |
| palette | object (optional). Same token set as article_journey: paper, paper_raised, ink, ink_soft, line, accent, accent_soft, blocked, blocked_soft, cleared, cleared_soft, mono_bg, mono_fg, mono_accent — each a CSS colour string. Unset tokens keep the theme default. |
| use_plex_fonts | boolean (optional, default true). Loads IBM Plex Mono and IBM Plex Serif via same-origin @font-face — see THIRD-PARTY-NOTICES.md. Set false for system font stacks only. |

## Example payload

```json
{
  "type": "concept_ladder",
  "rungs": []
}
```

Live page: https://a2uicatalog.ai/atoms/concept_ladder/
Full field contract: https://a2uicatalog.ai/spec.json
