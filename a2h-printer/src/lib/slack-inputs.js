// src/slack-inputs.js — A2UI form/input atom -> Slack modal `input` blocks
// (Bucket C, mapping.json). This is what finally PROVES Bucket C's 23 atoms:
// they only render inside a modal (Slack's `input` block is illegal in a
// message), and a modal needs a real `trigger_id` from a live user
// interaction — no script can manufacture one, so nothing about this file
// could be verified the way slack-blocks.js's Bucket A was (post to a real
// channel). It IS verified against `blocks.validate`'s `view` param, which
// is the strongest check available without a live click — see
// slack-compiler/validate_targets.py's own INPUT_SPECIMENS, which already
// proved every element name below is real and legal inside a view.
//
// Pure functions only, same posture as slack-blocks.js: no network, no
// Worker globals.
//
// FOUR ATOMS HAVE NO NATIVE SLACK ELEMENT (mapping.json's C-degraded,
// verified live 2026-08-06 — slack-compiler/slack-targets.json
// input_elements_NOT_available):
//   form_slider      -> number_input (no slider exists)
//   star_rating_input -> radio_buttons 1..max_stars (no star-rating exists)
//   toggle_switch    -> checkboxes, single option (no toggle exists)
//   otp_input        -> plain_text_input (no OTP element exists)
// Each substitution is functionally equivalent (the value round-trips) but
// visually different — flagged in the returned `degraded` array, same
// {atom, from, to, why} shape slack-blocks.js's chart-overflow path uses,
// so callers have ONE place to look for "this isn't quite what you asked
// for" across both files.

const TXT = (s) => ({ type: 'plain_text', text: String(s ?? '').slice(0, 150) || '—' });
const isPlainObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

let _autoId = 0;
function actionId(hint) {
  _autoId += 1;
  return `${hint || 'field'}_${_autoId}`;
}

function inputBlock(label, element, opts = {}) {
  const b = { type: 'input', label: TXT(label || 'Field'), element };
  if (opts.optional) b.optional = true;
  if (opts.hint) b.hint = TXT(opts.hint);
  return b;
}

function optionsFrom(list, { valueKey = 'value', labelKey = 'label' } = {}) {
  return (list || []).map((o) => ({
    text: TXT(isPlainObject(o) ? (o[labelKey] || o[valueKey] || 'Option') : String(o)),
    value: String(isPlainObject(o) ? (o[valueKey] ?? o[labelKey] ?? '') : o).slice(0, 75) || 'value',
  }));
}

// ── one-atom-to-one-element mappers ─────────────────────────────────────────
// Each returns { blocks: [input_block], degraded: [] }.
const SIMPLE = {
  form_input: (p) => {
    const type = p.type || p.field_type || 'text';
    const el = type === 'number'
      ? { type: 'number_input', action_id: actionId(p.name), is_decimal_allowed: false }
      : { type: 'plain_text_input', action_id: actionId(p.name) };
    if (p.placeholder) el.placeholder = TXT(p.placeholder);
    return { blocks: [inputBlock(p.label, el)], degraded: [] };
  },
  form_field: (p) => SIMPLE.form_input(p),
  form_textarea: (p) => {
    const el = { type: 'plain_text_input', multiline: true, action_id: actionId(p.name || 'text') };
    if (p.placeholder) el.placeholder = TXT(p.placeholder);
    return { blocks: [inputBlock(p.label, el)], degraded: [] };
  },
  reflection_prompt: (p) => {
    const el = { type: 'plain_text_input', multiline: true, action_id: actionId(p.prompt_id || 'reflection') };
    if (p.placeholder) el.placeholder = TXT(p.placeholder);
    return { blocks: [inputBlock(p.prompt, el)], degraded: [] };
  },
  form_select: (p) => ({
    blocks: [inputBlock(p.label, {
      type: 'static_select', action_id: actionId(p.name),
      options: optionsFrom(p.options),
      ...(p.placeholder ? { placeholder: TXT(p.placeholder) } : {}),
    })],
    degraded: [],
  }),
  // No true autocomplete combobox without a backend options endpoint
  // (external_select needs one this compiler has no way to provide) —
  // static_select is a fair, functionally-equivalent degrade: the value
  // still round-trips, only free-typing to filter is lost.
  combobox: (p) => ({
    blocks: [inputBlock(p.label, {
      type: 'static_select', action_id: actionId(p.name),
      options: optionsFrom(p.options),
      ...(p.placeholder ? { placeholder: TXT(p.placeholder) } : {}),
    })],
    degraded: [{ atom: 'combobox', from: 'combobox', to: 'static_select',
                 why: 'no native autocomplete element without a backend options endpoint' }],
  }),
  multi_select_input: (p) => ({
    blocks: [inputBlock(p.label, {
      type: 'multi_static_select', action_id: actionId(p.name),
      options: optionsFrom(p.options),
      ...(p.placeholder ? { placeholder: TXT(p.placeholder) } : {}),
    })],
    degraded: [],
  }),
  form_radio_group: (p) => ({
    blocks: [inputBlock(p.label, {
      type: 'radio_buttons', action_id: actionId(p.name), options: optionsFrom(p.options),
    })],
    degraded: [],
  }),
  variant_selector: (p) => ({
    blocks: [inputBlock(p.label, {
      type: 'radio_buttons', action_id: actionId(p.name),
      options: optionsFrom(p.items, { valueKey: 'value', labelKey: 'title' }),
    })],
    degraded: [],
  }),
  learning_path_selector: (p) => ({
    blocks: [inputBlock(p.title || 'Choose Your Path', {
      type: 'radio_buttons', action_id: actionId('path'),
      options: optionsFrom(p.paths, { valueKey: 'id', labelKey: 'label' }),
    })],
    degraded: [],
  }),
  form_checkbox_group: (p) => ({
    blocks: [inputBlock(p.label, {
      type: 'checkboxes', action_id: actionId(p.name),
      options: optionsFrom(p.items, { valueKey: 'name', labelKey: 'label' }),
    })],
    degraded: [],
  }),
  // Added during the needs_review pass (2026-08-07): form_switch_group was
  // correctly classified Bucket C but had no emitter — exactly the
  // "classified but doesn't compile" gap this session's whole discipline is
  // about catching. Same shape as form_checkbox_group; checkboxes is a
  // functionally-equivalent degrade for a switch group same as
  // toggle_switch's own single-switch case above, just multiple items.
  form_switch_group: (p) => ({
    blocks: [inputBlock(p.label, {
      type: 'checkboxes', action_id: actionId(p.name),
      options: optionsFrom(p.items, { valueKey: 'name', labelKey: 'label' }),
    })],
    degraded: [{ atom: 'form_switch_group', from: 'switch group', to: 'checkboxes',
                 why: 'no toggle element in Slack' }],
  }),
  custom_checkbox_group: (p) => ({
    blocks: [inputBlock(p.group_label, {
      type: 'checkboxes', action_id: actionId(p.name),
      options: optionsFrom(p.options),
    })],
    degraded: [],
  }),
  choicebox_group: (p) => ({
    blocks: [inputBlock(p.label, {
      type: p.multiple ? 'checkboxes' : 'radio_buttons', action_id: actionId(p.name),
      options: optionsFrom(p.items, { valueKey: 'value', labelKey: 'title' }),
    })],
    degraded: [],
  }),
  form_date_picker: (p) => ({
    blocks: [inputBlock(p.label, {
      type: 'datepicker', action_id: actionId(p.name),
      ...(p.placeholder ? { placeholder: TXT(p.placeholder) } : {}),
    })],
    // mode:"range" (two dates) has no single native element — this
    // captures only the first date. Noted rather than silently dropping
    // the second half of the range.
    degraded: p.mode === 'range'
      ? [{ atom: 'form_date_picker', from: 'date range', to: 'single datepicker',
           why: 'no native date-range element — captures the start date only' }]
      : [],
  }),
  file_upload: (p) => ({
    blocks: [inputBlock(p.label, { type: 'file_input', action_id: actionId('file') })],
    degraded: [],
  }),
  // No native fit — domain_picker is a stateful pill+free-text hybrid tied
  // to a client-side ValueStore, which has no modal-input analogue at all.
  // Degrading to a plain text field is honest (the reader can still type a
  // domain) rather than silently dropping the field.
  domain_picker: (p) => ({
    blocks: [inputBlock('Domain', {
      type: 'plain_text_input', action_id: actionId('domain'),
      ...((p.free_entry || {}).placeholder ? { placeholder: TXT(p.free_entry.placeholder) } : {}),
    })],
    degraded: [{ atom: 'domain_picker', from: 'domain_picker', to: 'plain_text_input',
                 why: 'no modal-input analogue for a client-side pill+free-text picker' }],
  }),

  // ── C-degraded: no native element exists at all (verified live) ──────────
  form_slider: (p) => ({
    blocks: [inputBlock(p.label, {
      type: 'number_input', action_id: actionId(p.name), is_decimal_allowed: !!p.step && p.step % 1 !== 0,
    }, { hint: `Range ${p.min ?? '?'}–${p.max ?? '?'}` })],
    degraded: [{ atom: 'form_slider', from: 'slider', to: 'number_input',
                 why: 'no slider element in Slack' }],
  }),
  star_rating_input: (p) => {
    const max = Math.max(1, Math.min(10, p.max_stars || 5));
    return {
      blocks: [inputBlock(p.name || 'Rating', {
        type: 'radio_buttons', action_id: actionId('rating'),
        options: Array.from({ length: max }, (_, i) => ({
          text: TXT('★'.repeat(i + 1)), value: String(i + 1),
        })),
      })],
      degraded: [{ atom: 'star_rating_input', from: 'star rating', to: 'radio_buttons',
                   why: 'no star-rating element in Slack' }],
    };
  },
  toggle_switch: (p) => ({
    blocks: [inputBlock(p.label, {
      type: 'checkboxes', action_id: actionId(p.name),
      options: [{ text: TXT(p.label || 'Enabled'), value: 'on' }],
    }, { optional: true })],
    degraded: [{ atom: 'toggle_switch', from: 'toggle', to: 'checkboxes',
                 why: 'no toggle element in Slack' }],
  }),
  otp_input: (p) => ({
    blocks: [inputBlock(p.label || 'Code', {
      type: 'plain_text_input', action_id: actionId('otp'),
    }, { hint: `${p.length || 6} digits` })],
    degraded: [{ atom: 'otp_input', from: 'OTP boxes', to: 'plain_text_input',
                 why: 'no OTP element in Slack' }],
  }),
};

// ── field-descriptor mapper (form.fields[] / sheet_form_submit.fields[]) ───
// Both atoms carry a flat array of {label, name, type, placeholder, options}
// descriptors rather than being ONE input themselves — each entry becomes
// its own `input` block. `type` here is the descriptor's own vocabulary
// (text/email/password/number/url/textarea/select/radio/checkbox/switch/
// slider/date), a DIFFERENT and SMALLER set than the top-level atom types
// SIMPLE above dispatches on — deliberately not reusing SIMPLE's keys for
// this switch, to avoid a collision between "an atom named form_select" and
// "a field whose type happens to be the string 'select'".
function fieldToBlock(f) {
  const ft = f.type || 'text';
  const label = f.label || f.name || 'Field';
  switch (ft) {
    case 'email': case 'password': case 'url': case 'text':
      return { blocks: [inputBlock(label, {
        type: 'plain_text_input', action_id: actionId(f.name),
        ...(f.placeholder ? { placeholder: TXT(f.placeholder) } : {}),
      })], degraded: [] };
    case 'number':
      return { blocks: [inputBlock(label, {
        type: 'number_input', action_id: actionId(f.name), is_decimal_allowed: false,
      })], degraded: [] };
    case 'textarea':
      return { blocks: [inputBlock(label, {
        type: 'plain_text_input', multiline: true, action_id: actionId(f.name),
        ...(f.placeholder ? { placeholder: TXT(f.placeholder) } : {}),
      })], degraded: [] };
    case 'select':
      return { blocks: [inputBlock(label, {
        type: 'static_select', action_id: actionId(f.name), options: optionsFrom(f.options),
      })], degraded: [] };
    case 'radio':
      return { blocks: [inputBlock(label, {
        type: 'radio_buttons', action_id: actionId(f.name), options: optionsFrom(f.options),
      })], degraded: [] };
    case 'checkbox':
      return { blocks: [inputBlock(label, {
        type: 'checkboxes', action_id: actionId(f.name), options: optionsFrom(f.options),
      })], degraded: [] };
    case 'switch':
      return { blocks: [inputBlock(label, {
        type: 'checkboxes', action_id: actionId(f.name),
        options: [{ text: TXT(label), value: 'on' }],
      }, { optional: true })],
      degraded: [{ atom: 'form.field', from: 'switch', to: 'checkboxes', why: 'no toggle element in Slack' }] };
    case 'slider':
      return { blocks: [inputBlock(label, {
        type: 'number_input', action_id: actionId(f.name),
      })], degraded: [{ atom: 'form.field', from: 'slider', to: 'number_input', why: 'no slider element in Slack' }] };
    case 'date':
      return { blocks: [inputBlock(label, { type: 'datepicker', action_id: actionId(f.name) })], degraded: [] };
    default:
      return { blocks: [inputBlock(label, {
        type: 'plain_text_input', action_id: actionId(f.name),
      })], degraded: [{ atom: 'form.field', from: ft, to: 'plain_text_input',
                        why: `unrecognised field type "${ft}" — fell back to plain text` }] };
  }
}

// ── composite atoms: `fields[]` (form, sheet_form_submit) — one input
// block per field ────────────────────────────────────────────────────────
function compileFieldsArray(fields) {
  const blocks = [];
  const degraded = [];
  for (const f of (fields || [])) {
    const r = fieldToBlock(isPlainObject(f) ? f : { label: String(f) });
    blocks.push(...r.blocks);
    degraded.push(...r.degraded);
  }
  return { blocks, degraded };
}

// ── modal: `children[]` — ARBITRARY content atoms, not field descriptors.
// Each child whose own `type` matches a Bucket C atom becomes a real input;
// anything else degrades to a plain-text input carrying its own title/label,
// since a view's blocks array cannot mix in most non-input block types
// (validated: only input, section, divider, context, image, and a few
// others are legal inside a view — see slack-targets.json's block-level
// notes) and this compiler does not attempt full recursive rendering of
// arbitrary content atoms inside a modal for v1. ─────────────────────────
function compileModalChildren(children) {
  const blocks = [];
  const degraded = [];
  for (const child of (children || [])) {
    if (!isPlainObject(child) || !child.type) continue;
    if (SIMPLE[child.type]) {
      const r = SIMPLE[child.type](child);
      blocks.push(...r.blocks);
      degraded.push(...r.degraded);
    } else {
      const label = child.title || child.label || child.type;
      blocks.push(inputBlock(label, { type: 'plain_text_input', action_id: actionId(child.type) }));
      degraded.push({ atom: 'modal.child', from: child.type, to: 'plain_text_input',
                       why: 'non-input child atom inside a modal — v1 does not recursively render arbitrary content' });
    }
  }
  return { blocks, degraded };
}

/**
 * Compile one Bucket C (or C-degraded) atom to Slack `input` blocks.
 * Returns { blocks, degraded } — `blocks` is an ARRAY because form/modal/
 * sheet_form_submit legitimately expand to multiple input blocks; simple
 * atoms return a single-element array. Same "declared outcome, never a
 * crash" contract as slack-blocks.js's compileAtom.
 */
export function compileInput(atomType, props) {
  const p = props || {};
  if (atomType === 'form' || atomType === 'sheet_form_submit') {
    return compileFieldsArray(p.fields);
  }
  if (atomType === 'modal') {
    return compileModalChildren(p.children);
  }
  if (SIMPLE[atomType]) return SIMPLE[atomType](p);
  throw new Error(`no input emitter for atom type "${atomType}"`);
}

/**
 * Wrap compiled input blocks into a full Slack `views.open` payload.
 *
 * `submit` is ALWAYS set, never left optional: `blocks.validate` accepts a
 * modal with `input` blocks and no `submit` (confirmed live, ok:true either
 * way) but Slack's real `views.open` rejects that combination at publish
 * time — a business rule `blocks.validate`'s shape check doesn't cover, and
 * one this compiler cannot test directly (that needs a live `trigger_id`
 * from a real click, same limitation Bucket C has throughout). Defaulting
 * here is cheaper than discovering the gap live.
 */
export function buildModalView({ title, blocks, callbackId, submitLabel, closeLabel }) {
  const view = {
    type: 'modal',
    title: TXT((title || 'A2UI Form').slice(0, 24)),
    blocks: blocks && blocks.length ? blocks : [inputBlock('—', { type: 'plain_text_input', action_id: 'noop' })],
    submit: TXT(submitLabel || 'Submit'),
  };
  if (callbackId) view.callback_id = String(callbackId).slice(0, 255);
  if (closeLabel) view.close = TXT(closeLabel);
  return view;
}
