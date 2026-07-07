# KB renderer — structure YAML → interactive HTML

Renders a KCS-shaped knowledge-article YAML into modern, **interactive,
zero-JavaScript** HTML. Decision trees work via CSS-only hidden radio/checkbox
inputs, so the output survives paste into CMS/knowledge-base rich-text fields.

```
pip install pyyaml

# full pipeline: existing article HTML in → two interactive HTML files out
python3 lift.py your-article.html > article.yaml   # deterministic HTML→YAML (no LLM)
python3 compose.py article.yaml -o out/article     # 2 files out:
#   out/article-description.html   (scope hero · issue · environment · cause)
#   out/article-resolution.html    (resolution · action buttons)

# or author/edit the YAML directly and render (demo of the bundled example):
python3 render_kb.py sample.yaml > sample-preview.html
```

## The lift (HTML → YAML)
`lift.py` parses messy article HTML mechanically: KCS section headings
(Summary/Issue/Environment/Cause/Resolution + synonyms), "Step N" procedures,
platform sections → tabs, note/warning boxes → callouts, tables, code blocks,
links (kept), escalation sentences → `actions`, record chrome → `meta`.
It **never fabricates**: anything ambiguous lands in `review_flags`
(`BRANCH_CANDIDATE`, `MULTI_ISSUE`, `SECTIONS_INFERRED`, `NO_RESOLUTION`, …)
— review those YAMLs (by hand or with an LLM) before rendering. The YAML is
the human checkpoint: readable, editable, and the single source the renderer
trusts.

Each output file is fully self-contained (one `<style>` block, inline markup,
no external resources, no JS).

## Structure YAML contract

```yaml
article:
  title: str
  layout: linear | diagnostic | reference-dense
  features: { questions: 0, tables: 0, platforms: 0, steps: 0 }   # optional
  meta: { article_id: "412", modified: "..." }                    # optional provenance
  actions: [ { label: "Contact the Service Desk", url: "..." } ]  # optional, data-driven
  issue:        { source: str, blocks: [...] }    # the problem, requestor's words
  environment:  { source: str, blocks: [...] }    # platforms / scope / prerequisites
  cause:        { source: str, blocks: [...] }    # root cause (omit if unstated)
  cause_test:   { source: str, blocks: [...] }    # "confirm this is your issue"
  resolution:   { source: str, blocks: [...] }
```

### Blocks
| Block | Shape |
|---|---|
| `body` | markdown-lite string (`**bold**`, `` `code` ``) |
| `list` | `[str]` — unordered (symptoms, facts) |
| `key_value` | `[{key, value}]` — description-side pairs render as hero chips |
| `steps` | `[str]` — numbered step cards |
| `callout` | `{kind: info\|tip\|warning\|caution, title?, text}` |
| `table` | `{headers: [..], rows: [[..]]}` — renders terminal-styled |
| `code_block` | string — dark mono block |
| `tabs` | `[{label, content: [blocks]}]` — CSS-only tabs (per-platform variants) |
| `branch` | see below — the interactive decision node |

### Decision branches (Guided-Decisions pattern)
```yaml
branch:
  question: "What do you see when trying to connect?"
  kind: is | what | check        # is = binary · what = multi-way · check = inline confirm
  choices:
    - answer: "Stuck on 'Connecting' with a lock icon"
      guidance: [ ...blocks, or a nested branch... ]
```
`is`/`what` render as exclusive choice pills (hidden radio group — one visible
path at a time). `check` renders as an inline expandable confirm (hidden
checkbox) so it opens without collapsing its parent choice. Branches nest;
loops are not supported by design (decision *trees*).

## Two-field compose
`compose.py` targets knowledge bases that store articles in two rich-text
fields (description / resolution):
- `compose.py article.yaml -o out/x` — one whole-article YAML, split into the
  two payload files.
- `compose.py desc.yaml res.yaml -o out/x` — two already-separate payloads,
  rendered one file each.

## Notes for CMS embedding
- Interactivity requires the `<style>` block to survive the editor. The hidden
  inputs are inline-hidden-safe, but the `:checked` reveal rules live in the
  style block — test one paste in your target CMS first.
- Wide tables scroll inside their own container; the page never scrolls
  sideways.
