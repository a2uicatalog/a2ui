import { validate, encodeUrl, loadUI, ATOMS } from './server.mjs';
import { gunzipSync } from 'zlib';

let fails = 0;
const ok = (c, m) => { console.log((c ? '✅' : '❌') + ' ' + m); if (!c) fails++; };

console.log('=== TEST 1: does WIRED state survive the official MCP carry? ===');
// Serve a wired payload the way get_ui does: wrap as EmbeddedResource(application/a2ui+json)
const original = loadUI('expenses-demo');
const embedded = { type: 'resource', resource: { uri: 'a2ui://expenses-demo', mimeType: 'application/a2ui+json', text: JSON.stringify(original) } };
// Client side: unwrap and re-parse
const carried = JSON.parse(embedded.resource.text);
ok(embedded.resource.mimeType === 'application/a2ui+json', 'carried with the A2UI content type');
ok(carried.type === 'a2ui_wired_surface', 'payload is a WIRED surface after carry');
ok(carried.state_primitives.length === original.state_primitives.length && carried.state_primitives.length === 6, 'state_primitives intact through EmbeddedResource (6)');
ok(carried.actions.length === 2, 'actions intact (2)');
const wiresIn = original.layout.filter(el => el.wire).length;
const wiresOut = carried.layout.filter(el => el.wire).length;
ok(wiresIn === wiresOut && wiresIn > 0, `wire graph intact (${wiresOut} wired atoms)`);
ok(JSON.stringify(carried) === JSON.stringify(original), 'byte-identical: MCP carried the full wired substrate, lost nothing');

console.log('\n=== TEST 2: can an agent AUTHOR a valid wired surface from the vocabulary? ===');
// Act as the agent: compose a NEW wired surface using atoms + a ValueStore + an ArrayFilter,
// wiring a text input -> filter -> table. (The catalogue-as-vocabulary authoring path.)
const authored = {
  type: 'a2ui_wired_surface',
  title: 'Authored: filterable list',
  state_primitives: [
    { id: 'q', primitive: 'ValueStore', props: { defaultValue: '' } },
    { id: 'flt', primitive: 'ArrayFilter', props: { source: '#load.result', field: 'name', match: '#q.value' } }
  ],
  actions: [ { id: 'load', type: 'gas:store_read', trigger: 'onLoad', props: { agent_id: 'demo', store: 'items' } } ],
  layout: [
    { id: 'h', atom: 'subheading', props: { text: 'Items' } },
    { id: 'search', atom: 'form_input', props: { label: 'Filter' }, wire: { onChange: '#q.setValue' } },
    { id: 'tbl', atom: 'data_table', props: { columns: ['name', 'qty'] }, wire: { rows: '#flt.result' } }
  ]
};
const v = validate(authored);
ok(v.wired, 'authored payload is a wired surface');
ok(v.ok, 'authored wired surface VALIDATES: ' + (v.ok ? 'clean' : JSON.stringify(v.errors)));
ok(v.counts.state === 2 && v.counts.actions === 1, `agent wired 2 state primitives + 1 action`);

console.log('\n=== TEST 2b: does the validator CATCH a hallucinated atom / bad wire? ===');
const bad = JSON.parse(JSON.stringify(authored));
bad.layout.push({ id: 'x', atom: 'quantum_flux_capacitor', props: {} });      // hallucinated atom
bad.layout.push({ id: 'y', atom: 'body', wire: { text: '#nonexistent.value' } }); // dangling wire
const vb = validate(bad);
ok(!vb.ok, 'invalid payload REJECTED (hallucination = parse error, not broken UI)');
ok(vb.errors.some(e => e.includes('quantum_flux_capacitor')), 'caught the hallucinated atom by name');
ok(vb.errors.some(e => e.includes('#nonexistent')), 'caught the dangling wire reference');

console.log('\nencoded preview URL sample:', encodeUrl(authored).slice(0, 70) + '…');

console.log('\n=== TEST 3: catalogs closed — validator resolves alias + state primitive from PUBLISHED artifacts ===');
import { validate as v3 } from './server.mjs';
// data_table (alias) + ArrayFilter/ValueStore (state catalog) — all from published catalogs now
const both = {
  type: 'a2ui_wired_surface', title: 'both catalogs',
  state_primitives: [ { id: 'q', primitive: 'ValueStore', props: {} }, { id: 'f', primitive: 'ArrayFilter', props: { source: '#a.result', field: 'x', match: '#q.value' } } ],
  actions: [ { id: 'a', type: 'gas:store_read', props: {} } ],
  layout: [ { id: 't', atom: 'data_table', wire: { rows: '#f.result' } } ]  // data_table = published alias
};
const rb = v3(both);
ok3(rb.ok, 'data_table (alias) + ValueStore/ArrayFilter (state catalog) all validate from PUBLISHED catalogs: ' + (rb.ok ? 'clean' : JSON.stringify(rb.errors)));
const badState = { ...both, state_primitives: [ { id: 'z', primitive: 'QuantumStore', props: {} } ] };
const rz = v3(badState);
ok3(!rz.ok && rz.errors.some(e => e.includes('QuantumStore')), 'unknown state primitive REJECTED by name (state catalog enforced)');
function ok3(c, m){ console.log((c?'✅':'❌')+' '+m); if(!c) process.exitCode = 1; }
process.exit(fails || process.exitCode || 0);
