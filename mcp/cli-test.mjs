// cli-test.mjs — the CLI must agree with the server it fronts.
//
// The interesting failure is not "does it run" but "does it tell the truth":
// validate reads the BUNDLED vocabulary snapshot while render asks the live
// endpoint, so the two drift apart the moment data/ goes stale. That happened
// on the first run of this CLI — validate reported a payload clean that the
// server correctly refused — which is why the agreement is asserted here
// rather than assumed.
import { execFileSync } from 'node:child_process';
import { writeFileSync, unlinkSync } from 'node:fs';

const run = (args, ok = [0]) => {
  try { return { out: execFileSync('node', ['cli.mjs', ...args], { encoding: 'utf8' }), code: 0 }; }
  catch (e) {
    if (!ok.includes(e.status)) throw new Error(`a2ui ${args.join(' ')} exited ${e.status}\n${e.stderr}`);
    return { out: (e.stdout || '') + (e.stderr || ''), code: e.status };
  }
};
let n = 0;
const t = (name, fn) => { fn(); n++; console.log(`  ok  ${name}`); };

const f = '/tmp/a2ui-cli-test.json';
writeFileSync(f, JSON.stringify({ blocks: [{ type: 'heading', text: 'x' }, { type: 'quiz_set', questions: [] }] }));

t('help lists every command', () => {
  const { out } = run(['help']);
  for (const c of ['render', 'validate', 'atoms', 'surfaces'])
    if (!out.includes(c)) throw new Error(`help omits ${c}`);
});
t('validate passes a clean payload', () => {
  writeFileSync(f, JSON.stringify({ blocks: [{ type: 'heading', text: 'x' }] }));
  if (run(['validate', f]).code !== 0) throw new Error('clean payload rejected');
});
t('validate rejects an unknown atom', () => {
  writeFileSync(f, JSON.stringify({ blocks: [{ type: 'not_an_atom' }] }));
  if (run(['validate', f], [0, 1]).code !== 1) throw new Error('unknown atom accepted');
});
t('validate honours the surface declaration', () => {
  writeFileSync(f, JSON.stringify({ blocks: [{ type: 'quiz_set', questions: [] }] }));
  const r = run(['validate', f, '--surface', 'web'], [0, 1]);
  if (r.code !== 1 || !r.out.includes('incompatible'))
    throw new Error('quiz_set accepted on web — bundled vocabulary is stale (npm run sync-data)');
});
t('surfaces reports declared incompatibility', () => {
  if (!run(['surfaces', 'quiz_set']).out.includes('incompatible'))
    throw new Error('surfaces omits incompatible_on');
});
t('atoms filters by surface', () => {
  const all = run(['atoms']).out.split('\n').length;
  const email = run(['atoms', '--surface', 'email']).out.split('\n').length;
  if (!(email < all)) throw new Error('--surface did not narrow the list');
});
unlinkSync(f);
console.log(`\n${n} CLI checks passed`);
