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
`--pace slow|normal|fast`, `--duration SECONDS`, `--d2` (read stdin as D2).

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
a checkout, or pass `?bundle=<url>`). Rebuild it after code changes with
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

The library returns `steps` (`{step, from, to, label, style}`, in order). The payload carries the same
table:

- **standalone** (`film: false`): the finished `motion_arch` followed by the repo's existing `table` atom
  (Step, From, To, What, Kind);
- **film** (`film: true`): ONE `motion_timeline` holds the diagram and the table, so both run on one
  clock. Each row is a `motion_text` that fades in when its step's edge starts drawing, a translucent
  `motion_shape` bar steps to the row of the step that is playing, and the poster frame is the finished
  table. Rows are one line of at most 60 characters, so a long row is cut with an ellipsis (the `table`
  atom has the full text). Twelve steps is the most a film carries (the timeline holds 24 children).

**Pacing** (timing only; no atom change). Every step gets reading time:

```
dwell(step) = max(2.5 s, (words in the edge label + words in its table row) / 3 + 0.8 s)
              x 1.15 above 6 steps, x 1.15 again above 9 steps, x pace (slow 1.4, normal 1.0, fast 0.75)
total       = 1.5 s lead-in (groups and nodes pop) + sum of the dwells + 3 s hold on the finished diagram
```

Edges draw and message chips ride inside their own step, one after another (a step with several chips is
stretched to fit them); row n appears at the instant edge n starts. `--pace`, `opts.pace` or
`%% pace: slow` pick the multiplier; `%% duration: 40` (or `--duration`) fixes the total and scales the
dwells to fit, with a warning if it is under the time the steps need at the fast pace. The result carries
`schedule` (`[{step, start, end}]` in seconds) and `durationSeconds`. The film never exceeds the atom's
120 s timeline limit. The atom keeps every window at 1% of the film or longer, so a very long film cannot
have very short pops. Without `numbered` the film uses the same schedule (edges in flow order) and has no
table.

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
| `:::kind`, `class a,b kind` | kind hint (see below). Other class names and `classDef`, `style`, `linkStyle` are styling and ignored |
| `%% comment`, `;` between statements, front matter `title:` | accepted |

Not supported (clear error with the line number): other diagram types (`sequenceDiagram` and the
rest), edge ids (`e1@-->`), `--x`/`--o` arrow ends, parallelogram/trapezoid/asymmetric shapes, double
circles, edges that point at a whole subgraph.

### Directives (ordinary comments to Mermaid, so the file stays valid Mermaid)

```
%% title: AG-UI: streaming an agent run into an app
%% msg: client->agent "run input"
%% msg: agent->client "STATE_DELTA" back
```

`title` becomes the accessible name. Also: `%% numbered: on|off`, `%% step: from->to N`,
`%% pace: slow|normal|fast`, `%% duration: SECONDS`.

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

Mermaid ids are case-sensitive; the atom's are `^[a-z][a-z0-9_-]{0,31}$`. The converter lower-cases,
replaces other characters with `_`, prefixes `n` if the id starts with a digit, cuts to 32, and adds
`_2`, `_3` on a collision, in order of first appearance. The same input always gives the same ids.

## Limits and what is checked

The atom's own limits: 12 nodes, 16 edges, 4 groups, 12 messages; labels 40 characters, sub-labels 40,
edge labels 48, message text 40, group labels 40 (drawn in capitals), title 80. **Nothing is dropped
silently.** Over a cap is an error that says how to split (it names the groups and their sizes). Text
over a limit is cut with an ellipsis and a warning.

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

The atom draws one curved line per edge with no routing. The converter picks each edge's `curve`
(bend) to keep lines off other boxes, edge labels off boxes and off each other, and group titles
clear. That step is one function (`routeCurves` in `layout.mjs`); a real router can replace it.

**Direction.** The direction in the file is kept unless the text would be under 7 px in a 343 px phone
column and the other axis is at least 30% better without a messier drawing; then the converter draws
it the other way and says so (warning). Force the written direction with `--direction`.

**Frame and text size.** The frame (`w`, `h`) is the layout's natural size, aimed at about 1000 wide
and no more than about 1100 tall; `size` (label px) is chosen with it. What matters on a phone is
`size x 343 / w`. All sizes are single-line labels (the atom does not wrap text), so wide labels and
many ranks make small text. The five example diagrams measure 4.3 to 8.2 px (the flat left-to-right ones are the worst);
a diagram with short labels, or a vertical one, reads better.

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

Operators must have spaces around them. Not supported: markdown/code blocks, `classes`, `vars`, layers,
scenarios, sql_table/class shapes, edges to a whole container, icons, globs.

## Honest limitations

- Edges are single curves. They can cross boxes and each other, and two labelled edges that run
  parallel in a vertical corridor can have their labels on top of each other (the atom centres every
  label on its curve). A router with label placement would fix this; it needs an atom change or a
  separate waypoint field.
- Long labels make small text on phones; see above.
- Fonts: widths are estimates. A different system font can make a label touch its box edge.
- No orthogonal edges, no dotted style (`optional` is drawn dashed), no thick lines, no nested boxes,
  no icons beyond the eight kinds.
- Over 12 nodes is refused, not folded into an overview.
- Text is not wrapped and is cut at the atom's limits.

## Tests

`node scripts/test_mermaid_arch.mjs` (parser tables for Mermaid and D2, error messages, numbering and pacing, layout invariants on the example
diagrams in `scripts/mermaid_arch/examples/` and on synthetic graphs, compile checks, golden payloads,
and the Python web renderer drawing every golden payload). After an intended change:
`UPDATE_GOLDEN=1 node scripts/test_mermaid_arch.mjs`.
