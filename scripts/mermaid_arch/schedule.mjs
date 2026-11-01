// Pacing: how long each step of the film stays on screen. Timing only, derived from the content.
//
//   dwell(step) = max(2.5 s, (words in the edge label + words in its table row) / 3 + 0.8 s)
//                 x 1.15 when the diagram has more than 6 steps, x 1.15 again above 9 steps
//                 x pace (slow 1.4, normal 1.0, fast 0.75)
//   a step with several message chips is stretched so every chip rides inside its own step
//   total = LEAD_IN (1.5 s: groups and nodes pop) + sum of dwells + HOLD (3 s on the finished diagram)
//
// `duration` (seconds) overrides the total: the dwells are scaled to fit, with a warning when that is
// shorter than the fast-pace reading time.
import { PACES } from './graph.mjs';

export const LEAD_IN = 1.5, HOLD = 3, MIN_DWELL = 2.5, WORDS_PER_SECOND = 3, CHIP_SECONDS = 1.2, CHIP_GAP = 0.15, CHIP_START = 0.55, CHIP_TAIL = 0.3;

export const words = (t) => (String(t || '').trim() ? String(t).trim().split(/\s+/).length : 0);

// steps: [{labelWords, rowWords, chips}] in playing order
export function buildSchedule(steps, { pace = 'normal', duration } = {}) {
  const warnings = [];
  const mult = PACES[pace];
  const n = steps.length;
  const crowd = n > 9 ? 1.15 * 1.15 : n > 6 ? 1.15 : 1;
  const base = (st, m) => {
    let d = Math.max(MIN_DWELL, (st.labelWords + st.rowWords) / WORDS_PER_SECOND + 0.8) * crowd * m;
    const need = CHIP_START + st.chips * CHIP_SECONDS + Math.max(0, st.chips - 1) * CHIP_GAP + CHIP_TAIL;
    return Math.max(d, need);
  };
  let dwell = steps.map((st) => base(st, mult));
  const fast = LEAD_IN + HOLD + steps.reduce((a, st) => a + base(st, PACES.fast), 0);
  if (duration !== undefined) {
    const room = duration - LEAD_IN - HOLD;
    const sum = dwell.reduce((a, b) => a + b, 0);
    if (room <= 0 || (n && room < 0.3 * n)) {
      throw Object.assign(new Error(`duration ${duration} s leaves no time for ${n} steps after the ${LEAD_IN} s lead-in and ${HOLD} s hold`), { archMessage: true });
    }
    if (duration < fast - 1e-9) warnings.push(`duration ${duration} s is shorter than the ${fast.toFixed(1)} s the steps need at the fast pace; readers will not have time to take each step in. Raise it or drop %% duration.`);
    const k = n ? room / sum : 1;
    dwell = dwell.map((d) => d * k);
  }
  const schedule = [];
  let t = LEAD_IN;
  dwell.forEach((d, i) => { schedule.push({ step: i + 1, start: round(t), end: round(t + d) }); t += d; });
  const total = duration !== undefined ? duration : round(t + HOLD);
  return { schedule, durationSeconds: round(total), warnings, minimumSeconds: round(fast) };
}
const round = (x) => Math.round(x * 1000) / 1000;
