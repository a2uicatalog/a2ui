# Mermaid to motion_arch

`scripts/mermaid_arch/` turns a Mermaid flowchart (or a small D2 file) into a ready-to-render
`motion_arch` payload, the architecture diagram that draws itself. You write the boxes and arrows;
the converter does the layout, the timing and the checking. MIT, plain JavaScript, no dependencies,
no network, no model calls.

The converter runs **before** the payload exists. The `motion_arch` atom, its schema and its
renderers are unchanged.

## Use it

```
node scripts/mermaid_arch/cli.mjs diagram.mmd              # payload JSON on stdout, warnings on stderr
node scripts/mermaid_arch/cli.mjs diagram.mmd --film       # wrapped in a motion_timeline so it plays
node scripts/mermaid_arch/cli.mjs diagram.mmd --check      # validate only
node scripts/mermaid_arch/cli.mjs diagram.mmd --json-graph # the canonical graph
node scripts/mermaid_arch/cli.mjs diagram.d2               # D2 subset (see below)
```

Options: `--direction LR|RL|TB|BT` (force the flow direction), `--size N` (label px, 8-40),
`--title TEXT`, `--fit wide`, `--graph` (input is a canonical graph in JSON), `--numbered`,
`--pace slow|normal|fast`, `--duration SECONDS`, `--d2` (read stdin as D2), `--routing orthogonal|curve`
(routed right-angle edges, the default, or the atom's single curves), `--relation-column`, `--relation-name TEXT`.

```js
import { mermaidToArch } from './scripts/mermaid_arch/index.mjs';
const r = mermaidToArch(text, { film: false, numbered: false, pace: 'normal' });
// r = { payload, graph, warnings, block, steps, schedule, durationSeconds, pace, numbered }
// errors throw ArchError with .errors (array of plain sentences) and .warnings
```
`d2ToArch(text, opts)` does the same for D2.

`payload` is `{"theme":"dark","blocks":[{"type":"motion_arch", ...}]}`: standalone it is the finished
diagram. With `film: true` it is a `motion_timeline` that plays the diagram in: groups, then nodes in
flow order, then edges, then the message chips.

Try it live: open `scripts/mermaid_arch/playground.html` (one file, no external scripts; it loads the
renderer bundle from `public/surfaces/mcp-apps/renderer-bundle.html` by relative path, so open it from
a checkout, or pass `?bundle=<url>` when it is served over http(s); the URL must be on the same origin, anything else is ignored). Input is capped at 20,000 characters and 500 per line, for both Mermaid and D2 (D2 also allows at most 8 nested braces and 8 parts in a dotted path, and stops reading after 20 errors). Rebuild it after code changes with
`node scripts/mermaid_arch/build_playground.mjs`.

## Numbered flows, the steps table and pacing

Turn on `numbered` (`--numbered`, `opts.numbered`, or `%% numbered: on`; off by default in the library,
on in the review page and the playground). Every edge label gets its step number ("1 prompt", an
unlabelled edge just "1"). Steps follow the order of the edges in the source. To change it:

```
%% step: agent->client 3
```

That edge becomes step 3 and the other edges take the lowest free numbers in source order. A number used
twice, a number above the edge count (a gap) or an edge that does not exist is a plain error. If the
number pushes a label over the atom's 48 characters you get a warning and the label is cut with an
ellipsis.

The library returns `steps` (`{step, from, to, label, style}`, in order; empty unless numbered) and `textSteps` / `textMessages`
(always filled). **Every payload carries a full text alternative** for screen-reader users, using the repo's existing `table`
atom (the `motion_arch` atom is unchanged; its SVG still has only the `label` as its accessible name):

- a `table` captioned `Steps` with the columns `Step | Activity` (and Relation when asked for): one row per edge, the
  full sentence, never cut (see "The Activity sentence" below). Unnumbered diagrams get it too; the step numbers are then the
  order the diagram draws the edges, and are not printed on the diagram;
- when the diagram has messages, a second `table` captioned `Messages` with `Step | Message | Direction`, the full payload text
  and the nodes it travels between.

Where they sit:

- **standalone** (`film: false`): the finished `motion_arch`, then those tables;
- **film** (`film: true`): ONE `motion_timeline` (the diagram and, when numbered, the on-film step rows) followed by the same tables, so the
  tables are the accessible text of the film. When numbered, each on-film row is a `motion_text` that fades in when its step's edge starts
  drawing, a translucent `motion_shape` bar steps to the row of the step that is playing, and the poster frame is the finished
  table. Film rows are one line of at most 60 characters (the sentence, then the sentence without "the", then
  `From -> To: label`, and only then cut with an ellipsis; the tables below the film have the full sentence). The stage
  is chosen by how big the diagram is shown relative to the stage WIDTH (the player is displayed at its column's
  width), with the table text kept at 1.65% of the width or more; the table text may shrink to about 1.95% of the
  width when that makes a tall diagram bigger, so the diagram is the same size with the Relation column on or off. Twelve steps is the most a film carries (the timeline holds 24 children).

**Pacing** (timing only; no atom change). Every step gets reading time:

```
dwell(step) = max(1.8 s, words in the step's sentence / 4 per second + 0.5 s)
              x 1.1 above 6 steps, x 1.1 again above 9 steps, x pace (slow 1.4, normal 1.0, fast 0.75)
total       = 1 s lead-in (groups and nodes pop) + sum of the dwells + 2 s hold on the finished diagram
```

Edges draw and message chips ride inside their own step, one after another (a step with several chips is
stretched to fit them). A chip moves at a constant apparent speed, 14% of the diagram's long side per second, so
its ride is the route length over that speed, at least max(1.8 s, 0.8 s + 0.07 s per character of its text) and at
most 5 s; pace multiplies the ride (never below 0.75 x the minimum). Row n appears at the instant edge n starts. `--pace`, `opts.pace` or
`%% pace: slow` pick the multiplier; `%% duration: 40` (or `--duration`) fixes the total and scales the
dwells to fit, with a warning if it is under the time the steps need at the fast pace. The result carries
`schedule` (`[{step, start, end}]` in seconds) and `durationSeconds`. The film never exceeds the atom's
120 s timeline limit. The atom keeps every window at 1% of the film or longer, so a very long film cannot
have very short pops. Without `numbered` the film uses the same schedule (edges in flow order) and has no
table.

**The Activity sentence** is built from the two node labels and the edge label by a fixed template
(`scripts/mermaid_arch/activity.mjs`; no model, same input gives the same text): "Chat host sends the tool call to
the LLM"; a reply to an earlier edge in the other direction says "returns" ("LLM returns A2UI JSON to the ADK
agent"); a label that starts with a known verb reads as a verb phrase ("types prompt" gives "User types prompt into
the client app", "asks" gives "User asks the orchestrator"); `<->` edges and "reads and writes" give "Agent reads and
writes the shared state"; async and optional edges end in "(async)" / "(optional)". Node names inside a sentence are
lower-case except acronyms and camelCase (ADK, A2UI, postMessage), and the target gets "the". There are no colons
or arrows ("ui://" loses its colon). "the" is only added before a lower-case plain label. A film row is at most 60
characters: the sentence, then without "the", then cut with an ellipsis; the table atom keeps the full sentence. The
template is crude on purpose; a wrong-sounding sentence is fixed by rewording the edge label.

**The optional Relation column.** Off by default. Turn it on with `opts.relationColumn`, `--relation-column`,
or `%% relation-column: on` (an explicit option beats the directive); the review page and the playground have
a "Show relation column" checkbox next to the numbers toggle. The cell is a short verb type from an optional
directive, free text of at most 20 characters; an edge without one has an empty cell:

```
%% rel: orch->card calls
%% rel: remote->orch reports back
%% relation-name: Interaction     (renames the column header; default Relation, at most 20 characters)
```

In the film the column is a third text block per row that fades in with its row. D2 uses `# rel:`,
`# relation-column:` and `# relation-name:`.

A proper number badge on the edge would need a small additive change to the `motion_arch` atom; today
the number is part of the label text.

## Supported Mermaid

| Syntax | Result |
|---|---|
| `flowchart LR` / `graph TD` (LR, RL, TB, TD, BT) | flow direction; missing direction means TB |
| `id`, `id[t]`, `id(t)`, `id([t])`, `id[[t]]`, `id[(t)]`, `id((t))`, `id{t}`, `id{{t}}`, `id["quoted"]` | node; quotes allow brackets in the text |
| `id@{ shape: cyl, label: "x" }` | Mermaid 11 node form, common shape names only |
| `<br/>` in a label | first line is the label, the rest becomes the muted sub-label |
| `-->`, `---`, `==>`, `-.->`, `-.-`, `<-->`, `<-.->` | edges. Dotted is drawn dashed ("async"); solid and thick are solid; `<-->` gets two arrowheads. `---` and `-.-` still get an arrowhead (the atom always draws one; you get a warning once) |
| `-->\|label\|`, `-- label -->`, `-. label .->`, `== label ==>` | edge label |
| `A --> B --> C`, `A & B --> C & D` | chains and fan-in/fan-out |
| `subgraph id[Title] ... end` | a group box. Nested subgraphs are flattened into the outermost one (warning) |
| `:::kind`, `class a,b kind` | kind hint (see below). `classDef`, `style`, `linkStyle` and other class names are not drawn: one warning per diagram, "Colours and styles (classDef, style, linkStyle) are not drawn; the diagram uses its own colours by node kind." (a `click` line is ignored and mentioned in the same line) |
| `id>text]`, `id[/text/]`, `id[\text\]`, `id[/text\]`, `id(((text)))` | **degraded, not refused**: drawn as a rectangle (asymmetric, parallelogram, trapezoid) or a circle (double circle), with the warning `Node "X" uses a shape the atom cannot draw (asymmetric); drawn as a rectangle.` |
| markdown string (quoted text wrapped in backquotes) with `**bold**`, `__bold__`, `*italic*`, `_italic_` | the `**`, `__`, `*`, `_` markers are removed; the text stays |
| `#amp; #lt; #gt; #quot; #apos; #nbsp;`, `#35;` (also `&amp;` and `&#35;` forms) | decoded in labels. Tags are stripped; a tag formed by decoding is stripped too, so none survives |
| `<b>`, `<script>` and other HTML tags in a label | removed (`<br/>` is a line break); one warning per diagram, `HTML tags were removed from a label.`; a label left empty falls back to the node id |
| `%% comment`, `;` between statements, front matter `title:` | accepted |

Degraded with a warning instead of an error (the try-it is forgiving): the shapes above, `classDef`/`style`/
`linkStyle`/`click`, HTML tags, nested subgraphs, `direction` inside a subgraph, `---` arrowheads, groups
beyond 4.

Not supported (clear error with the line number): other diagram types (`sequenceDiagram` and the
rest), edge ids (`e1@-->`), invisible links (`A ~~~ B`: "invisible links (~~~) are not supported; remove the
line or use a normal arrow."), cross and circle arrow ends (`--x`, `--o`, `x--x`, `o--o`), edges that point
at a whole subgraph. Errors raised by the graph checks (self loop, unknown endpoint) also say `line N` when the
node or edge came from a source line.

### Directives (ordinary comments to Mermaid, so the file stays valid Mermaid)

```
%% title: AG-UI: streaming an agent run into an app
%% msg: client->agent "run input"
%% msg: agent->client "STATE_DELTA" back
```

`title` becomes the accessible name. Also: `%% numbered: on|off`, `%% step: from->to N`,
`%% pace: slow|normal|fast`, `%% duration: SECONDS`, `%% rel: from->to TEXT`, `%% relation-column: on|off`,
`%% relation-name: TEXT`.

`title` becomes the accessible name. `msg` adds a payload chip that rides the first edge from `from`
to `to` (ids as written in the Mermaid file; case-insensitive). Add `back` to send it from the end to
the start. If only the reverse edge exists the chip rides it backwards (warning). Several messages on
one edge are staggered in time. At most 12.

### Kinds

Resolved in this order: explicit `:::kind` or `class` (one of `device app server tool model store
surface user`, or an alias), else the shape default.

| Shape | Default kind | | Alias | Kind |
|---|---|---|---|---|
| `[text]`, bare id | server | | client, browser, phone | device |
| `(text)`, `{{text}}` | app | | db, database, cache, bucket, storage | store |
| `([text])` | device | | queue, mcp, auth | tool |
| `[[text]]`, `{text}` | tool | | gateway, cdn, proxy, backend, worker | server |
| `[(text)]` | store | | service, agent, frontend | app |
| `((text))` | model | | llm, ai | model |
| | | | external, ui, renderer, screen | surface |
| | | | person, actor, human | user |

### Ids

Mermaid ids are case-sensitive and may use any Unicode letter or digit (`café`, `日本`); the atom's are
`^[a-z][a-z0-9_-]{0,31}$`. The converter drops accents (`é` becomes `e`), lower-cases,
replaces other characters with `_`, prefixes `n` if the id starts with a digit, cuts to 32, and adds
`_2`, `_3` on a collision, in order of first appearance. The same input always gives the same ids.

## Limits and what is checked

The atom's own limits: 12 nodes, 16 edges, 4 groups, 12 messages; labels 40 characters, sub-labels 40,
edge labels 48, message text 40, group labels 40 (drawn in capitals), title 80. **Nothing is dropped
silently.** Over a cap is an error that says how to split (it names the groups and their sizes), with one
exception: **groups beyond 4 are folded, not refused.** The converter (Mermaid, D2 and graph JSON alike, after
nested groups are flattened) turns the smallest groups into plain nodes, fewest members first and, on a tie,
the later one in the source first, until 4 remain. A folded group loses its box and title; its nodes stay. Its
title is added as the sub-label of each member that has none, when the title fits 40 characters. One warning
says what happened, for example `Drew 4 of 5 groups: "5. Mail" was shown without its box (the diagram can draw at
most 4).` Text over a limit is cut with an ellipsis and a warning. The layout warning (drawn top-to-bottom
instead of the written direction, given only when the other axis makes the text at least 25% bigger) ends with the CLI hint by default; `hint: 'web'` swaps it for "You can switch
the Layout menu to the written direction." (the playground passes it).

Checks and their wording (numbers are 1-based):

```
edge 6: "wrker" is not a node id (did you mean "worker"?)
the graph has 13 nodes; the atom draws at most 12 (1 over). Split it by group: "Big tier" has 9 nodes, ...
edge 3: "a" points at itself; the atom cannot draw self-loops. Remove the edge or add a second node.
node "lonely" has no edges; it will sit on its own in the layout. Connect it or remove it.
line 7: node "a": missing closing "]"; if the text contains brackets or parentheses, wrap it in quotes: a["text (like this)"]
line 1: "sequenceDiagram" diagrams are not supported; only flowcharts are. Draw each participant as a node ...
```

## Layout

Deterministic (same input, byte-identical output). Each group is laid out as a block and the blocks are
laid out in ranks (longest path, cycles broken in input order, barycentre ordering), so group boxes
never overlap and never contain a node that is not a member. Edges that skip a rank get a reserved lane in the ranks they cross, so they are not drawn through the boxes in between. Inside a group the converter tries
running the members across or along the flow and keeps the tidier result. Ungrouped nodes are placed
between and beside the groups. Box sizes come from label lengths (calibrated against the atom's fonts
on one machine; other fonts may differ by some percent, the boxes carry slack for that).

**Edge routing** (`scripts/mermaid_arch/route.mjs`, the default; `routing: 'curve'` / `--routing curve` gives the
stage-1 single curves, byte for byte). The atom only draws what it is told: per edge `points` (a polyline with rounded
corners, `radius` top-level) and `label_at` (where the label's centre goes), and messages ride the polyline. The
router is a public JS module in the converter, not in the Python or Apps Script twins.

- A grid (cell about 0.55 x the text size) lies over the drawing. Cells near a box or on a group title are blocked.
- Each edge is an A* search over (cell, heading): distance, a cost per bend, a heavy cost for running along a lane
  another edge uses, a medium one for crossing it, a cost for passing through a group the edge does not belong to
  or running along a group border. Edges are routed shortest first, ties by input order, so the output is byte-stable.
- An edge leaves and enters a box at a port (a cell 15+ px out from one of the four sides, away from the rounded
  corners), so its first and last stretch are at right angles to the box and long enough for the arrowhead. A
  request/response pair takes two neighbouring lanes. At most 10 points per edge; an edge that cannot be routed
  within that is drawn as a curve and a warning says so.
- Every channel between ranks grows with the number of edges (and, top to bottom, the labels) that run through it.
  If some label still has no free place, all gaps are widened and the diagram is routed again (twice at most).
- The atom draws a routed edge's label above the message chips, so a chip passing a label never hides it.
- Labels go on the longest free stretch: above or below a horizontal one, left or right of a vertical one, or on the
  line, checked against boxes, group titles, other labels and other edges. A label is never shortened here; when
  nothing is free it is placed where it collides least and a warning says so.

**Direction and shape.** With routing on, the converter lays the diagram out both ways (and several group
arrangements), routes each, and keeps the one with the best score: text size on a 343 px phone column (every px
under 9 costs), not more than about 1.7 times taller than wide, then crossings, label collisions, bends and length.
It picks the other axis only when that scores better and the text is at least 25% larger on a phone column; otherwise the written direction stays and nothing is said. When it does flip it says so (warning, informational). Force the written direction with `--direction`.

**Frame and text size.** The frame (`w`, `h`) is the layout's natural size, aimed at about 1000 wide
and no more than about 1100 tall; `size` (label px) is chosen with it. What matters on a phone is
`size x 343 / w`. All sizes are single-line labels (the atom does not wrap text), so wide labels and
many ranks make small text. The five example diagrams measured 2.0 to 6.7 px as curves and 5.2 to 8.6 px routed (see the numbers in the
review page); a diagram with short labels, or a vertical one, reads better.

## D2 (subset)

`node scripts/mermaid_arch/cli.mjs file.d2` (or `d2ToArch`) reads a small subset of D2 and produces the same
canonical graph, so everything above applies. The parser is written from the D2 syntax documentation and
shares no code with D2 (MPL-2.0). The same 9-node example written in Mermaid and in D2
(`scripts/mermaid_arch/examples/equiv/`) gives an identical canonical graph and identical payload; a test
checks it.

| D2 | Result |
|---|---|
| `a`, `a: Label`, `a: { label: X }` | shape; `\n` in a quoted label gives label + sub-label |
| `shape: cylinder` / `queue` / `person` / `circle` / `hexagon` / `cloud` / `rectangle` | kind store / tool / user / model / app / surface / server |
| `kind: store` or `class: db` | explicit kind (same names and aliases as Mermaid); wins over `shape` |
| `g: Title { a; b }`, `g.a` | container = group box (nested containers flattened, warning) |
| `a -> b`, `<-`, `<->`, `--`, chains, `: label` | edges (`--` still draws an arrowhead; warning) |
| `style.stroke-dash: 3` (inline, or in `style: { ... }`, on an edge) | dashed = async |
| `direction: right/left/down/up` | LR / RL / TB / BT |
| `# title:`, `# msg:`, `# numbered:`, `# step:`, `# pace:`, `# duration:` | the same directives as `%%` in Mermaid |

Operators must have spaces around them (`a->b` is an error). `g.label: X`, `b.shape: person` and `a.style.fill: red` set properties of the
object. Not supported, each an error naming the line: markdown/code blocks, `"""` block comments, `classes`, `vars`, layers,
scenarios, sql_table/class shapes, edges to a whole container, `(a -> b)[0]` references, imports (`...@file`, `a: @file`), icons, globs.
HTML tags in labels are dropped, as in Mermaid.

## Honest limitations

- Routed edges can still cross each other (the router prefers a detour of up to about 7 lanes to a crossing, no more)
  and a label may sit across a neighbouring edge's line when the channel is crowded (a label is penalised for being
  closer to another edge than to its own); the counts are measured and
  reported, and the review page shows them. Two edges next to each other can make it unclear which label belongs to
  which line; labels sit right against their own line to keep that readable.
- Converting takes from about 0.05 s (small diagrams) to about 0.7 s (the largest examples) in Node on a 2009-era Xeon, and the code uses no DOM, window or storage, so it can run in a Web Worker.
- Long labels make small text on phones; see above.
- Fonts: widths are estimates. A different system font can make a label touch its box edge.
- No dotted style (`optional` is drawn dashed), no thick lines, no nested boxes,
  no icons beyond the eight kinds.
- Over 12 nodes is refused, not folded into an overview.
- Text is not wrapped and is cut at the atom's limits.

## Tests

`node scripts/test_mermaid_arch.mjs` (parser tables for Mermaid and D2, error messages, numbering and pacing, layout invariants on the example
diagrams in `scripts/mermaid_arch/examples/` and on synthetic graphs, compile checks, golden payloads,
and the Python web renderer drawing every golden payload). After an intended change:
`UPDATE_GOLDEN=1 node scripts/test_mermaid_arch.mjs`. The default goldens are the routed drawing; the `*.curve.golden.json` files keep the stage-1 curve drawing. `tests/test_motion_arch_routing.py` covers the atom's `points`, `label_at` and `radius` (Python and Apps Script renderers byte for byte).
