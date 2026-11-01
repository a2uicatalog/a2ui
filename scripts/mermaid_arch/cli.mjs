#!/usr/bin/env node
// node scripts/mermaid_arch/cli.mjs file.mmd [--direction LR|RL|TB|BT] [--json-graph] [--check] [--film] [--fit wide] [--size N] [--title T]
import { readFileSync } from 'fs';
import { graphToArch, parseMermaid, parseD2, validateGraph, ArchError } from './index.mjs';

const HELP = `usage: node cli.mjs <file.mmd | file.d2 | file.json | -> [options]
  --direction LR|RL|TB|BT  force the flow direction (otherwise the one written in the file, switched
                           to the other axis only when that makes the text much bigger)
  --json-graph             print the canonical graph instead of the payload
  --check                  validate only; print warnings, exit 1 on errors
  --film                   wrap in a motion_timeline so the diagram (and the steps table) plays
  --numbered               prefix every edge label with its step number and add the steps table
  --relation-column        add a third column (Relation) to the steps table, filled from %% rel: directives
  --relation-name TEXT     header of that column (default Relation)
  --pace slow|normal|fast  reading pace of the film (1.4x / 1.0x / 0.75x per-step time); default normal
  --duration SECONDS       fix the total film length (warns when shorter than the fast reading time)
  --routing orthogonal|curve  how edges are drawn: routed right-angle lines with placed labels (default) or the atom's single curve
  --fit wide               tune the layout for a wide screen instead of a phone column
  --size N                 label size in px (8-40); default is chosen from the diagram
  --title TEXT             override the title
  --graph                  the input is a canonical graph in JSON, not Mermaid
Warnings go to stderr.`;

function main(argv) {
  const opts = {}; let file; let jsonGraph = false, check = false, asGraph = false;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') { console.log(HELP); return 0; }
    else if (a === '--direction') { opts.direction = (argv[++i] || '').toUpperCase().replace('TD', 'TB'); }
    else if (a === '--json-graph') jsonGraph = true;
    else if (a === '--check') check = true;
    else if (a === '--film') opts.film = true;
    else if (a === '--numbered') opts.numbered = true;
    else if (a === '--relation-column') opts.relationColumn = true;
    else if (a === '--relation-name') opts.relationName = argv[++i];
    else if (a === '--pace') opts.pace = argv[++i];
    else if (a === '--duration') opts.duration = Number(argv[++i]);
    else if (a === '--graph') asGraph = true;
    else if (a === '--d2') opts.syntax = 'd2';
    else if (a === '--fit') opts.fit = argv[++i];
    else if (a === '--routing') opts.routing = argv[++i];
    else if (a === '--size') opts.size = Number(argv[++i]);
    else if (a === '--title') opts.title = argv[++i];
    else if (a.startsWith('--')) { console.error(`unknown option ${a}\n${HELP}`); return 2; }
    else file = a;
  }
  if (!file) { console.error(HELP); return 2; }
  if (opts.routing && !['orthogonal', 'curve'].includes(opts.routing)) { console.error('--routing must be orthogonal or curve'); return 2; }
  if (opts.pace && !['slow', 'normal', 'fast'].includes(opts.pace)) { console.error('--pace must be slow, normal or fast'); return 2; }
  if (opts.duration !== undefined && !(opts.duration >= 2 && opts.duration <= 120)) { console.error('--duration must be 2 to 120 seconds'); return 2; }
  if (opts.direction && !['LR', 'RL', 'TB', 'BT'].includes(opts.direction)) { console.error('--direction must be LR, RL, TB (or TD) or BT'); return 2; }
  let text;
  try { text = file === '-' ? readFileSync(0, 'utf8') : readFileSync(file, 'utf8'); }
  catch (e) { console.error(`cannot read ${file}: ${e.message}`); return 2; }
  try {
    let graph, warnings = [];
    if (asGraph || file.endsWith('.json')) {
      graph = JSON.parse(text);
      const v = validateGraph(graph);
      if (v.errors.length) throw new ArchError(v.errors, v.warnings);
      warnings = v.warnings;
    } else {
      const p = (file.endsWith('.d2') || opts.syntax === 'd2') ? parseD2(text, opts) : parseMermaid(text, opts); graph = p.graph; warnings = p.warnings;
      const v = validateGraph(graph);
      warnings = [...warnings, ...v.warnings];
      if (v.errors.length) throw new ArchError(v.errors, warnings);
    }
    if (jsonGraph) { console.log(JSON.stringify(graph, null, 2)); warnings.forEach((w) => console.error('warning: ' + w)); return 0; }
    if (check) { warnings.forEach((w) => console.error('warning: ' + w)); console.error(`ok: ${graph.nodes.length} nodes, ${graph.edges.length} edges, ${graph.groups.length} groups, ${graph.messages.length} messages`); return 0; }
    const r = graphToArch(graph, opts);
    [...warnings, ...r.warnings.filter((w) => !warnings.includes(w))].forEach((w) => console.error('warning: ' + w));
    console.error(`info: film ${r.durationSeconds} s at ${r.pace} pace, ${r.schedule.length} steps`);
    console.log(JSON.stringify(r.payload));
    return 0;
  } catch (e) {
    if (e instanceof ArchError) { (e.errors).forEach((m) => console.error('error: ' + m)); return 1; }
    if (e instanceof SyntaxError) { console.error('error: not valid JSON: ' + e.message); return 1; }
    console.error('internal error: ' + e.message); return 3;
  }
}
process.exitCode = main(process.argv.slice(2));
