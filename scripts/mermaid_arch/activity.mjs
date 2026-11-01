// The steps table's `Activity` column: one plain-English sentence per edge, built from the two node labels and
// the edge label by a fixed template. No model, no randomness: the same graph gives the same sentences.
//
//   edge label      sentence
//   (none)          "<From> calls <To>"
//   noun phrase     "<From> sends the <label> to <To>"      ("the" only before a lower-case plain word)
//   verb phrase     "<From> <verb> <rest> <preposition> <To>" for a known leading verb ("types prompt" -> "... types prompt into <To>")
//   single verb     "<From> <verb> <To>"                     ("asks" -> "User asks Orchestrator")
//   both ways       "<From> and <To> exchange <label>"       (a verb phrase like "reads and writes": "<From> reads and writes <To>")
//   async / optional edges end in " (async)" / " (optional)"
//
// A row of the film is one line of at most 60 characters: rowText() tries the full sentence, then the sentence
// without "the", then "<From> -> <To>: <label>", and only then cuts it with an ellipsis. The standalone `table`
// atom always carries the full sentence.

// third-person verbs the template recognises at the start of an edge label, with the preposition that links the rest to the target
export const LEAD_VERBS = Object.freeze({
  'looks up': 'in', types: 'into', asks: '', answers: '', creates: 'in', discovers: 'from', reads: 'from', writes: 'to', mounts: 'in',
  dispatches: 'to', streams: 'to', sends: 'to', posts: 'to', calls: '', fetches: 'from', renders: 'in', returns: 'to', lists: 'from',
  saves: 'in', stores: 'in', loads: 'from', requests: 'from', checks: '', validates: '', notifies: '', hands: 'to', forwards: 'to',
  publishes: 'to', subscribes: 'to', queries: '', updates: '', deletes: 'from', opens: '', pushes: 'to', pulls: 'from', resolves: '',
  verifies: '', signs: '', receives: 'from', reports: 'to', triggers: '', invokes: '', runs: 'on', executes: '',
});

export function activity(fromLabel, toLabel, label, { style, both } = {}) {
  const F = String(fromLabel).trim(), T = String(toLabel).trim(), L = String(label || '').trim();
  let s;
  if (!L) {
    s = both ? `${F} and ${T} talk to each other` : `${F} calls ${T}`;
  } else {
    const lower = L.toLowerCase();
    const verb = Object.keys(LEAD_VERBS).find((v) => lower === v || lower.startsWith(v + ' '));
    if (verb) {
      const rest = L.slice(verb.length).trim();
      const prep = LEAD_VERBS[verb];
      if (!rest) s = `${F} ${verb} ${T}`;
      else if (/^(and|or)\b/i.test(rest) || both) s = `${F} ${verb} ${rest} ${T}`;
      else s = `${F} ${verb} ${rest} ${prep || 'with'} ${T}`;
    } else if (both) {
      s = `${F} and ${T} exchange ${/^[a-z][a-z ]*$/.test(L) ? 'the ' : ''}${L}`;
    } else {
      const article = /^[a-z][a-z ,+-]*$/.test(L) ? 'the ' : '';   // lower-case plain words only: not "A2UI JSON", "tools/call", "POST run"
      s = `${F} sends ${article}${L} to ${T}`;
    }
  }
  if (style === 'async') s += ' (async)';
  else if (style === 'optional') s += ' (optional)';
  return s[0].toUpperCase() + s.slice(1);
}

// a row of the film's table: "*N*  sentence", at most `max` characters
export function rowText(step, sentence, fromLabel, toLabel, label, style, max = 60) {
  const pre = `*${step}*  `;
  const suffix = style === 'async' ? ' (async)' : style === 'optional' ? ' (optional)' : '';
  const tries = [
    sentence,
    sentence.replace(/ the /, ' '),
    `${fromLabel} → ${toLabel}${label ? ': ' + label : ''}${suffix}`,
  ];
  for (const t of tries) if ((pre + t).length <= max) return pre + t;
  const t = tries[2], room = max - pre.length;
  return pre + t.slice(0, room - 1).trimEnd() + '…';
}
