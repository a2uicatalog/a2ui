// The steps table's `Activity` column: one plain-English sentence per edge, built from the two node labels and
// the edge label by a fixed template. No model, no randomness: the same graph gives the same sentences.
//
//   edge label      sentence
//   (none)          "<From> calls the <to>"
//   noun phrase     "<From> sends the <label> to the <to>"   ("the" only before a lower-case plain word)
//   a reply         "<From> returns the <label> to the <to>" (a sync edge whose reverse edge is in the diagram too)
//   verb phrase     "<From> <verb> <rest> <preposition> the <to>" for a known leading verb ("types prompt" -> "... types prompt into the client app")
//   single verb     "<From> <verb> the <to>"                  ("asks" -> "User asks the orchestrator")
//   both ways       "<From> and the <to> exchange <label>"
//   async / optional edges end in " (async)" / " (optional)"
// Node names inside a sentence are lower-case except acronyms and camelCase (ADK, A2UI, postMessage); the first word
// is capitalised; no colons or arrows (a "ui://" in a name loses its colon).
//
// A row of the film is one line of at most 60 characters: rowText() tries the full sentence, then the sentence
// without "the", and only then cuts it with an ellipsis. The standalone `table`
// atom always carries the full sentence.

// third-person verbs the template recognises at the start of an edge label, with the preposition that links the rest to the target
export const LEAD_VERBS = Object.freeze({
  'looks up': 'in', types: 'into', asks: '', answers: '', creates: 'in', discovers: 'from', reads: 'from', writes: 'to', mounts: 'in',
  dispatches: 'to', streams: 'to', sends: 'to', posts: 'to', calls: '', fetches: 'from', renders: 'in', returns: 'to', lists: 'from',
  saves: 'in', stores: 'in', loads: 'from', requests: 'from', checks: '', validates: '', notifies: '', hands: 'to', forwards: 'to',
  publishes: 'to', subscribes: 'to', queries: '', updates: '', deletes: 'from', opens: '', pushes: 'to', pulls: 'from', resolves: '',
  verifies: '', signs: '', receives: 'from', reports: 'to', triggers: '', invokes: '', runs: 'on', executes: '',
});

// plain text only: no colons ("ui://" loses its colon and slashes, "events: x" becomes "events, x"), no arrows
const plain = (t) => String(t).replace(/:\/\//g, ' ').replace(/\s*:\s*/g, ', ').replace(/\s*(?:->|-->|=>|→)\s*/g, ' to ').replace(/\s+/g, ' ').trim();
// a node label inside a sentence: lower-case words, except acronyms and camelCase names (ADK, A2UI, AG-UI, postMessage)
const keep = (w) => /[A-Z]/.test(w.slice(1)) || /^[A-Z0-9]{2,}/.test(w);
const dangling = (t) => String(t).replace(/[\s,;:&\-–—]+$/, '');   // a label cut at a <br/> can end in a comma or an ampersand
const inSentence = (label) => plain(dangling(label)).split(' ').map((w) => (keep(w) ? w : w.toLowerCase())).join(' ');

// forward: ("X sends <what> to Y"), a reply to an earlier edge in the other direction ("X returns <what> to Y"),
// a verb phrase ("X types prompt into the Y"), both ways ("X and Y exchange <what>")
export function activity(fromLabel, toLabel, label, { style, both, reply } = {}) {
  const F = inSentence(fromLabel), T = 'the ' + inSentence(toLabel), L = inSentence(label || '');
  let s;
  if (!L) {
    s = both ? `${F} and ${T} talk to each other` : `${F} calls ${T}`;
  } else {
    const verb = Object.keys(LEAD_VERBS).find((v) => L === v || L.startsWith(v + ' '));
    if (verb) {
      const rest = L.slice(verb.length).trim();
      const prep = LEAD_VERBS[verb];
      if (!rest) s = `${F} ${verb} ${T}`;
      else if (/^(and|or)\b/i.test(rest) || both) s = `${F} ${verb} ${rest} ${T}`;
      else s = `${F} ${verb} ${rest} ${prep || 'with'} ${T}`;
    } else if (both) {
      s = `${F} and ${T} exchange ${/^[a-z][a-z ]*$/.test(L) && !/^(a|an|the)\b/.test(L) ? 'the ' : ''}${L}`;
    } else {
      const article = /^[a-z][a-z ,+-]*$/.test(L) && !/^(a|an|the|\d)\b/i.test(L) ? 'the ' : '';   // lower-case plain words only: not "A2UI JSON", "tools/call", "POST run"
      s = `${F} ${reply && style !== 'async' && style !== 'optional' ? 'returns' : 'sends'} ${article}${L} to ${T}`;
    }
  }
  if (style === 'async') s += ' (async)';
  else if (style === 'optional') s += ' (optional)';
  return s[0].toUpperCase() + s.slice(1);
}

// a row of the film's table: "*N*  sentence", at most `max` characters: the sentence, then without "the", then cut with an ellipsis
export function rowText(step, sentence, max = 60) {
  const pre = `*${step}*  `;
  for (const t of [sentence, sentence.replace(/ the /g, ' ')]) if ((pre + t).length <= max) return pre + t;
  const t = sentence.replace(/ the /g, ' '), room = max - pre.length;
  return pre + t.slice(0, room - 1).trimEnd() + '…';
}
