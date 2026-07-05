# roadmap.md — Domain Spec v0.1

**Status:** Draft v0.1 (2026-07-03)
**Domain selector:** `roadmap`
**Consumers:** deterministic MD→payload parser (`scripts/parse_roadmap_md.py`) → A2UI wired-surface payload → GAS renderer
**Reference output:** the a2uicatalog capabilities roadmap (private tier)

Second instance of the intermediate-MD-spec class (training.md was the
first). A `roadmap.md` captures a backlog/roadmap document: phased
capability plans with the iceberg split (below-surface plumbing vs
above-surface user-noticeable), a delivery timeline, a consolidation
backlog, and risks. It is designed to be handed to an LLM *together with*
the source material (a planning session, a strategy doc, a matrix), or
authored by hand. Everything after "Model Instructions" is normative.

---

## Model Instructions

You are transforming a source document (planning notes, capabilities
matrix, strategy discussion) into a compliant `roadmap.md` file.

1. **Omit any section the source document does not support. Do not invent
   content to satisfy the template.** A sparse output is compliant; a
   fabricated one is not. If the source names no risks, there is no
   `# Risks` section in your output.
2. Preserve the source's phase structure and item wording. Do not merge,
   reorder, or pad phases or items.
3. `status:` must reflect what the source actually claims — never upgrade
   a `planned` item to `in-progress` to make the roadmap look healthier.
4. The `below:`/`above:`/`unlocks:` keys encode the iceberg split: `below`
   is the plumbing primitive, `above` is what an end user notices,
   `unlocks` is the dependency line (what this item is a prerequisite
   for). Omit any key the source does not support — an item may be pure
   plumbing with no `above:` yet; that absence is a finding, not an error.
5. Output the **entire file wrapped in exactly one fenced code block**
   (open with ```markdown, close with ```). Nothing outside the fence.
   The parser strips it on intake.

---

## File Structure

A compliant file is: YAML frontmatter, then body sections in the order
listed below. `# Phases` is the **only required body section** — a
roadmap without phases is non-compliant. All other sections are optional
and appear only when the source supports them.

```
---
<frontmatter>
---
<intro paragraph>    (optional)
# Phases             (REQUIRED)
# Timeline           (optional)
# Backlog            (optional)
# Risks              (optional)
```

## Frontmatter

Required keys: `id`, `domain` (must be `roadmap`), `name`, `source`,
`license`. Optional keys: `horizon` (free text, e.g. "July–Sept 2026"),
`velocity_basis` (one line: what the timeline estimates are calibrated
against), `as_of` (ISO date the statuses were true).

Forbidden keys (presentation lives in the parser, never in the document):
`render`, `layout`, `atoms`, `theme`, `accent`.

`license: private` marks the document as private-tier content: the parser
emits a `private: true` flag in the payload and downstream tooling must
refuse to publish it to a public surface.

## `# Phases` (required)

Each phase is a `## ` heading. An optional trailing attribute block may
carry a status class:

```
## 1 · Compilation era {.status-shipped}
```

Recognised classes: `.status-shipped`, `.status-active`,
`.status-designed`, `.status-planned`. Unknown class = lint warning W02 +
fallback to `planned` (never a failure). An optional paragraph directly
under the heading is the phase summary.

Phase items are a numbered list; each item is a key-value block in the
training.md step idiom — the item title on the number line, indented
`key: value` lines beneath:

```
1. Atom vocabulary (467 atoms)
   status: done
   below: schema.yaml is the single source of truth
   above: browsable vocabulary at a2uicatalog.ai
   unlocks: everything — the instruction set
```

Item keys (all optional except `status`):

| key       | meaning                                              |
|-----------|------------------------------------------------------|
| `status`  | REQUIRED. `done` \| `in-progress` \| `planned`       |
| `below`   | below-surface primitive (the plumbing)               |
| `above`   | above-surface capability (what the user notices)     |
| `unlocks` | dependency line — what this is a prerequisite for    |
| `note`    | free-text caveat                                     |

Unknown item key = lint error E05. Missing `status` = lint error E06.

## `# Timeline` (optional)

Separator bullets, `when :: milestone :: basis`:

```
- mid-July 2026 :: Era 2 consolidation :: 2–3 focused days; debt, not invention
```

`basis` optional (two-field bullets are valid).

## `# Backlog` (optional)

Checkbox bullets; checked = already done (kept for the record):

```
- [ ] document the {ok, data, total, error} action contract
- [x] redact secrets from the ops audit log
```

## `# Risks` (optional)

Separator bullets, `level :: title :: description :: mitigation`:

```
- high :: consolidation loses to invention :: … :: close Era-2 rows before Era-3 build
```

`level` must be one of `critical | high | medium | low` (E07 otherwise).
`description` and `mitigation` optional.

---

## Derivation rules (parser-owned, never authorable)

The document carries **content only**. The parser derives all machinery:

- `jump_nav` from phase headings (same rule as training.md).
- One `roadmap_card` overview: periods = phases (label = phase title,
  status class → period annotation), items = `{text: item title, status}`.
- One `data_table_sortable` per phase: headers
  `[Item, Below the surface, Above the surface, Status, Unlocks]`, rows
  from item key-value blocks (absent key = empty cell — visible sparseness).
- `# Timeline` → `brevet_timeline` events `{date: when, title: milestone,
  desc: basis}`.
- `# Backlog` → `checklist_interactive` (checked state from `[x]`).
- `# Risks` → `risk_flag` risks `{level, title, description, mitigation}`.
- Intro paragraph → `body` atom. Dividers between sections.

Payload envelope: `a2ui_wired_surface` with empty `state_primitives` and
`actions` in v0.1 (static page; done-state persistence is an Era-2 item —
the roadmap will eventually track itself).

## Lint codes

| code | class   | meaning                                        |
|------|---------|------------------------------------------------|
| E01  | error   | missing/invalid frontmatter key                |
| E02  | error   | forbidden frontmatter key present              |
| E03  | error   | `# Phases` missing or empty                    |
| E04  | error   | unknown section heading                        |
| E05  | error   | unknown item key                               |
| E06  | error   | item missing `status` / invalid status value   |
| E07  | error   | invalid risk level                             |
| W01  | warning | unknown atom hint in heading attributes        |
| W02  | warning | unknown status class on phase heading          |
| W03  | warning | optional section absent (coverage note only)   |

Missing optional = fine (W03 coverage note); missing required = error;
present-but-malformed = error. Only errors block payload emission.
