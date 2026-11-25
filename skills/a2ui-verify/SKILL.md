---
name: a2ui-verify
description: Check that an A2UI payload rendered what was intended, before showing it to anyone. Use after composing a payload and before handing over the HTML or link, when a render "succeeded" but something looks missing or wrong, or when targeting a surface other than the plain web (Google Meet stage, Apps Script, MCP Apps). Covers offline validation, the X-A2UI-* report headers, the markers left in the HTML, the hidden data table on charts, and per-renderer status. Not for picking atoms (a2ui-catalog), building the payload (a2ui-compose) or HTTP plumbing and quotas (a2ui-rest).
license: MIT
metadata:
  author: a2uicatalog
  version: "1.0.0"
---

# Verifying an A2UI render

A `200` from `/api/render` does not mean the page shows what you meant. A misspelt atom
type, an atom the target surface cannot show, and bad values inside a chart all still
return `200` with HTML. The server tells you about each of them, but in headers and HTML
comments that nobody sees unless they look. This skill is the looking.

## 1. Validate offline first (free, no quota)

The examples below all use this `page.json` (a heading, a bar chart with one bad value, a
misspelt atom and a navigation menu):

```json
{"title": "t", "blocks": [
  {"type": "heading", "text": "Hi"},
  {"type": "chartjs_bar", "labels": ["Q1", "Q2"], "datasets": [{"label": "EUR", "data": [12, "n/a"]}]},
  {"type": "headng", "text": "x"},
  {"type": "navigation_menu", "items": []}]}
```

Node 18+, no install:

```bash
npx -p @a2uicatalog/mcp a2ui validate page.json --surface google-meet-stage
```

```
  degraded      chartjs_bar on google-meet-stage
  unknown atom  headng
  incompatible  navigation_menu on google-meet-stage
4 atom(s) checked for google-meet-stage: 2 problem(s)
```

Exit code is 1 when any atom is unknown or incompatible (degraded is reported, not
counted). `a2ui surfaces <atom>` prints where one atom works, degrades or cannot go. The
vocabulary ships inside the package, so it can lag the live `/spec.json`; when they
disagree, the live file wins.

Python (`pip install a2uicatalog`) checks field contracts too, and suggests near names:

```python
from a2uicatalog import Client
Client().check(payload, strict=False)
# ["blocks[2]: unknown atom type 'headng' (did you mean heading, subheading?)", ...]
```

The published JSON Schema behind `check` is stricter than the renderer. If it reports a
"missing required field" that the atom's `fields` text in `/spec.json` calls optional,
trust `/spec.json` and the rendered result.

## 2. Render in the sandbox and read the headers

```bash
curl -s -D headers.txt -o page.html -X POST \
  'https://a2uicatalog.ai/api/sandbox/api/render?surface=google-meet-stage' \
  -H 'Content-Type: application/json' -d @page.json
```

Real response headers for the payload above (status `200`):

```
x-a2ui-sandbox: true
x-a2ui-surface: google-meet-stage
x-a2ui-unpublished: headng
x-a2ui-degraded: chartjs_bar
x-a2ui-incompatible: navigation_menu
ratelimit-remaining: 18
```

| Header | Meaning | What to do |
|---|---|---|
| `X-A2UI-Unpublished` | Type is unknown or preview-stage. Nothing visible was drawn. | Fix the type name; check `/spec.json`. |
| `X-A2UI-Incompatible` | The atom's declaration rules out this surface. A visible note replaced it. | Swap to an atom whose `works_on` lists the surface. |
| `X-A2UI-Degraded` | Rendered, with a known loss on this surface. | Read the atom's `degraded_on` note and decide if the loss matters. |

Without `?surface=` there is no policy, so `Degraded` and `Incompatible` never appear.
Always pass the surface you will actually ship to. Accepted values are `web`,
`mcp-apps`, `google-apps-script-web` and `google-meet-stage`.

A refused payload is a `400` with a JSON body naming what was refused, and it still
spends one request of the allowance:

```json
{"ok": false,
 "error": "these atoms perform a render-time server fetch and are not available on the public endpoint: data_source",
 "refused": ["data_source"],
 "hint": "Deploy your own renderer to use server-fetching atoms."}
```

## 3. Read the HTML, not just the status

Search the returned page for these markers:

- `<!-- a2ui: unknown or unsupported atom "unpublished:headng" -->` is all that is left of
  an unknown atom. It is a comment, so the page simply has a gap.
- An incompatible atom becomes a callout reading, for example, "navigation_menu is not
  available on the google-meet-stage surface — its declaration says so."
- Charts report dropped values in the page itself: `chartjs_bar` given `"data": [12, "n/a"]` in a dataset
  prints "1 entry was not a usable number and was skipped."

A quick gate an agent can run:

```bash
grep -c 'a2ui: unknown or unsupported atom' page.html   # must be 0
grep -i '^x-a2ui-\(unpublished\|incompatible\)' headers.txt   # must print nothing
```

## 4. Check what a screen reader and a stripped client get

Chart atoms carry a text summary and a visually hidden table. For the bar chart above:

```html
<div role="img" aria-label="bar chart of 2 categories. Highest value 12 (Q1), lowest 12 (Q1). Value axis from 0 to 12.">
<table style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);...">
  <thead><tr><th scope="col">Category</th><th scope="col">EUR</th></tr></thead>
  <tbody><tr><th scope="row">Q1</th><td>12</td></tr><tr><th scope="row">Q2</th><td></td></tr></tbody>
</table>
```

Read both. They are built from your data, so a wrong `aria-label` or an empty cell is
the fastest sign of a wrong field or a non-numeric value. The table also matters
beyond accessibility: `chartjs_bar` declares that a stage iframe dropping its layout
"shows the hidden table only", and that in email "the table is what survives". On those
surfaces the table is the chart, so it has to be right.

## 5. When it renders wrong in someone else's renderer

Each atom in `/spec.json` has `x-renderers`, its measured status per stock renderer
(`react`, `lit`, `angular`, `copilotkit`, `a2ui-vue`, `flutter`, `compose`). Web
renderers report `drawn`, `drawn_with_differences`, `not_verified` or `not_supported`;
Flutter reports `native`, `degraded` (lowered to Basic components), `not_measured` or
`not_supported`. The rules for each status are in
https://a2uicatalog.ai/catalogue/renderer-matrix-v1.json. If an atom marked `drawn`
renders wrong, reduce it to the smallest payload that shows the problem and open an
issue at https://github.com/a2uicatalog/a2ui/issues with that payload and the
`X-A2UI-*` headers.

## When not to use this

- Choosing which atom to use: a2ui-catalog.
- Writing the payload or choosing `render_surface` vs `preview_url`: a2ui-compose.
- Quotas, async jobs, idempotency and API versions: a2ui-rest.
- Proving a page is accessible. The hidden table and labels help, but a clean render
  says nothing about keyboard order, focus or what a screen reader announces. That
  still needs a human pass.

Free, MIT licensed, no signup. Independent, unofficial project, not affiliated with,
endorsed by, or sponsored by Google or Anthropic. Source: https://github.com/a2uicatalog/a2ui
