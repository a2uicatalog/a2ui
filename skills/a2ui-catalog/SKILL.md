---
name: a2ui-catalog
description: Pick the right A2UI atoms and read their real field contracts before composing a UI payload. Use when deciding WHAT to render — searching the A2UI Atomic Catalog's 480 typed UI atoms (charts, gauges, steppers, dashboards, decision trees) for a task, or when a previous attempt to render a payload failed because a field name or atom type was guessed wrong. Not for the render step itself (see the a2ui-compose skill) or for MCP connection setup (see a2ui-mcp).
license: MIT
metadata:
  author: a2uicatalog
  version: "1.0.0"
---

# Picking A2UI atoms

The catalog is deliberately not loaded all at once: 480 atoms is too much context for
most tasks, and the wrong field name is a validation error, not a broken render — so
this skill is about narrowing down to the right slice and reading its real contract,
not guessing.

## 1. Narrow to a catalog slice

`list_catalogs` (MCP tool) or `GET /catalogue/index.json` (REST) returns every catalog
with a one-line when-to-use, e.g. `a2ui-atoms-v1` (the base vocabulary, always
resolved), `a2ui-learning-v1` (quizzes, flashcards, course UI), state/data-source
extension catalogs. Pick the slice the task actually needs — do not pull the whole
vocabulary into context for a one-chart request.

## 2. Read the real field contract

`get_catalog(catalog)` returns that slice's atoms with type + a one-line description —
enough to confirm an atom EXISTS and roughly what it does, not enough to fill it in.

Before authoring any atom you haven't used before, call `get_atom_schema(types)` (MCP)
or fetch `/catalogue/atoms-json-schema.json` (REST, strict per-atom JSON Schema — also
useful as a `response_format`/grammar constraint so a model literally cannot emit an
invalid atom). This is the step that prevents the single most common failure: guessing
a prop name that doesn't exist, which either renders empty or gets silently normalised
away.

`required_catalogs(payload)` is the reverse lookup — given a payload you already have,
it returns exactly which catalog URIs it needs, deterministically (pure function of the
atoms used, not a guess).

## 3. Common mistakes this skill exists to prevent

- **Inventing a generic block type.** There is no `text` or `button` atom. Every block
  names a real, typed atom from the vocabulary — check `get_catalog` first.
- **Guessing a field name instead of calling `get_atom_schema`.** An unrecognised or
  malformed field doesn't error loudly; it's caught and the block renders as a visible
  "unknown atom" notice, or the field is just dropped. Silent-wrong is worse than a hard
  error, so don't skip this step.
- **Loading the full 480-atom vocabulary for a small task.** Pick the catalog slice via
  `list_catalogs` first; it costs nothing and keeps the working context small.
- **Assuming every atom renders everywhere.** Per-surface support (web, Google Meet
  stage, Apps Script, Google Chat, MCP Apps, email, PDF) is declared PER ATOM. An atom
  that can't work on a target surface says so rather than degrading silently — check
  `works_on` / `degraded_on` / `incompatible_on` in the catalog entry before assuming
  portability.

## Reference

| Document | URL |
|---|---|
| Full atom vocabulary | https://a2uicatalog.ai/spec.json |
| Strict per-atom JSON Schema | https://a2uicatalog.ai/catalogue/atoms-json-schema.json |
| Catalog selection menu | https://a2uicatalog.ai/catalogue/index.json |
| Agent overview | https://a2uicatalog.ai/llms.txt |

Once the right atoms and their contracts are known, hand off to the **a2ui-compose**
skill to actually build and render the payload.

Free, MIT licensed, no signup. Independent, unofficial project — not affiliated with,
endorsed by, or sponsored by Google or Anthropic. A2UI is Google's protocol; MCP is
Anthropic's. Source: https://github.com/a2uicatalog/a2ui
