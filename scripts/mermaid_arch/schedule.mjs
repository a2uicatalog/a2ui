// Pacing: how long each step of the film stays on screen. Timing only, derived from the content.
//
//   dwell(step) = max(1.8 s, words in the step's sentence / 4 per second + 0.5 s)
//                 x 1.1 when the diagram has more than 6 steps, x 1.1 again above 9 steps
//                 x pace (slow 1.4, normal 1.0, fast 0.75)
//   a step with several message chips is stretched so every chip rides inside its own step
//   total = LEAD_IN (1 s: groups and nodes pop) + sum of dwells + HOLD (2 s on the finished diagram)
//   (a 10-step diagram plays in about 30 s at the normal pace)
//
// `duration` (seconds) overrides the total: the dwells are scaled to fit, with a warning when that is
// shorter than the fast-pace reading time.
import { PACES } from './graph.mjs';

export const LEAD_IN = 1, HOLD = 2, MIN_DWELL = 1.8, WORDS_PER_SECOND = 4, READ_PAD = 0.5, CHIP_GAP = 0.15, CHIP_START = 0.55, CHIP_TAIL = 0.3;

// Message chips move at one apparent speed: CHIP_SPEED is the share of the diagram's long side covered per second.
// A chip's ride is clamp(path / (CHIP_SPEED x long side), minRide, maxRide); minRide keeps its text readable while it moves.
// Pace multiplies the ride (slow 1.4, normal 1, fast 0.75) but never below RIDE_FLOOR x minRide.
export const CHIP_SPEED = 0.14, CHIP_MAX_RIDE = 5.0, RIDE_FLOOR = 0.75;
export const chipMinRide = (chars) => Math.max(1.8, 0.8 + 0.07 * chars);
export function chipRide(pathLen, longSide, chars) {
  const min = chipMinRide(chars), max = Math.max(CHIP_MAX_RIDE, min);
  return { r: Math.min(max, Math.max(min, pathLen / (CHIP_SPEED * Math.max(1, longSide)))), min };
}
// the ride at a pace multiplier m (chip = {r, min} from chipRide)
export const paceRide = (chip, m) => Math.max(RIDE_FLOOR * chip.min, chip.r * m);

export const words = (t) => (String(t || '').trim() ? String(t).trim().split(/\s+/).length : 0);

// steps: [{words, chips, rides}] in playing order (words = words in the step's sentence; chips = number of message chips;
// rides = [{r, min}] per chip from chipRide)
export function buildSchedule(steps, { pace = 'normal', duration } = {}) {
  const warnings = [];
  if (!Object.hasOwn(PACES, pace)) throw Object.assign(new Error(`pace "${String(pace)}" is not one of ${Object.keys(PACES).join(', ')}`), { archMessage: true });
  const mult = PACES[pace];
  const n = steps.length;
  const crowd = n > 9 ? 1.1 * 1.1 : n > 6 ? 1.1 : 1;
  const base = (st, m) => {
    let d = Math.max(MIN_DWELL, st.words / WORDS_PER_SECOND + READ_PAD) * crowd * m;
    const need = CHIP_START + (st.rides || []).reduce((a, c) => a + paceRide(c, m), 0) + Math.max(0, st.chips - 1) * CHIP_GAP + CHIP_TAIL;
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
