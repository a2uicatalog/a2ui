// A2UI STATE & EXPR VOCABULARY SNAPSHOT
// Surface: apps-script-web (gas-wired-renderer)
// Update this file when adding primitives, exprs, ops, column types, or action types.
// Injected into the agent builder system prompt alongside _ATOM_SCHEMA_SNAPSHOT.

var _EXPR_SCHEMA_SNAPSHOT = `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A2UI STATE & COMPUTATION VOCABULARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Payloads have three sections: state_primitives, actions, layout.
Atoms in layout use "wire" to subscribe to primitive/action output fields.
Wire syntax: "#nodeId.field" — the # prefix is required.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. STATE PRIMITIVES  (state_primitives array)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ValueStore — mutable named value; holds user input or transient state
  props: defaultValue: any (optional)
  readable fields: value
  action target: setValue (pass new value as payload)
  example: { "id": "search_mem", "primitive": "ValueStore", "props": { "defaultValue": "" } }

Timer — fires a tick on a fixed interval; triggers queries or actions
  props: interval: integer (milliseconds, default 10000)
  readable fields: tick (integer, increments each fire)
  wire target: wire.tick → "#timer_id.tick" on the downstream action
  example: { "id": "refresh_5s", "primitive": "Timer", "props": { "interval": 5000 } }

DerivedStore — computes augmented data from a source store client-side; no server call
  props:
    from: string — source reference e.g. "#incidents_query.result"
    expr: "augment_rows" — maps over source array, adds computed columns per row
    interval: integer (ms, optional) — re-run on tick; required for time-dependent ops
    add: array of op definitions (see DerivedStore ops below)
  readable fields: result (enriched array)
  note: interval only needed when derived value changes with time (elapsed_seconds etc.)
        omit interval for value-relative derivations (ratio_pct, threshold etc.)

Computed — evaluates a math expression over named numeric inputs
  props:
    expr: string — JS-safe math expression using named vars e.g. "a + b"
    inputs: object — { varName: "#nodeId.field" } wire map
    format: string (optional) — "0,0" / "0.0%" / "HH:mm:ss" etc.
  readable fields: value (number), display (formatted string)

ArrayFilter — filters a source array by a field value predicate
  props:
    source: string — "#nodeId.result"
    field: string — field name to filter on
    match: any — value to match (or "#nodeId.value" reference)
  readable fields: result (filtered array)

StringValidator — validates a string value against rules
  props:
    source: string — "#nodeId.value"
    rules: object — { minLength, maxLength, pattern, required }
  readable fields: valid (boolean), error (string)

NumericThreshold — classifies a number as ok / warn / breach
  props:
    source: string — "#nodeId.value"
    warn: number, breach: number
  readable fields: state ("ok" | "warn" | "breach")

StepNavigator — tracks current step in a multi-step flow
  props:
    steps: integer — total step count
    initial: integer (optional, default 0)
  readable fields: current (integer), total (integer)
  action targets: next, prev, goto

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. DERIVEDSTORE OPS  (within augment_rows add array)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Each op entry: { "col": "output_column_name", "op": "op_name", ...op-specific props }
Ops run in order — later ops can reference columns added by earlier ops via "src".

elapsed_seconds — seconds elapsed since a timestamp field in each row
  props: field: string — row field containing ISO timestamp (e.g. "opened_at")
  output: integer (seconds, 0 if field missing or unparseable)
  requires interval on DerivedStore to update with time

format_duration — human-readable duration from a seconds column
  props: src: string — column name holding seconds (from a prior op or row field)
  output: string e.g. "1h 23m", "45m 12s", "8s"
  requires interval if src is time-dependent

threshold_by_field — ok/warn/breach classification using per-row-key threshold sets
  props:
    src: string — column name holding numeric value to threshold
    key: string — row field whose value selects the threshold set (e.g. "severity")
    thresholds: object — { "KEY_VALUE": { "warn": number, "breach": number }, ... }
  output: "ok" | "warn" | "breach"
  example:
    { "col": "sla_state", "op": "threshold_by_field", "src": "elapsed_sec",
      "key": "severity",
      "thresholds": { "P1": { "warn": 900, "breach": 7200 },
                      "P2": { "warn": 1800, "breach": 14400 } } }

ratio_pct — percentage from two numeric row fields
  props:
    numerator: string — row field for the current value
    denominator: string — row field for the total/target value
  output: number (0–100, or 0 if denominator is 0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. COLUMN RENDER HINTS  (data_table columns array)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Column definitions in data_table: { "key": "field", "label": "Header", "type": "hint" }
Absence of "type" renders plain text. Presence delegates to named cell renderer.

(plain text) — default; no type needed; renders String(value)

badge — coloured pill from a value→colour map
  extra props: colors: { "VALUE": "#hexcolor", ... }
  example: { "key": "status", "label": "Status", "type": "badge",
             "colors": { "New": "#6366f1", "Resolved": "#22c55e" } }

sla_badge — ok/warn/breach coloured pill with elapsed time alongside
  extra props: time_key: string — column name holding formatted duration string
  renders: green OK / amber WARN / red BREACH pill + elapsed time text
  example: { "key": "sla_state", "label": "SLA", "type": "sla_badge", "time_key": "elapsed_fmt" }

_claim — owner avatar with claim/transfer button; wire to a claim action
  extra props: claim_key, email_key, name_key, action_node, key_mem_node
  behaviour: shows avatar+name when owned; shows Claim button when unclaimed

_resolve — resolve button; hides when status is already Resolved
  extra props: resolve_key, status_key, action_node, key_mem_node

_delete — delete row button (red trash icon)
  extra props: delete_key, action_node, key_mem_node

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. ACTION TYPES  (actions array) — gas-wired-renderer surface
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Actions run server-side. Result stored at "#actionId.result". Status at "#actionId.status".
Common props on all actions: trigger ("onLoad" | "manual"), collect (field→wire map for inputs).

gas:sheet_query — queries a Google Sheet; returns rows as array
  props: sheet: string, filters: object (optional), order_by: array (optional)
  result: array of row objects keyed by column header
  trigger onLoad: auto-runs on page load; re-runs when Timer tick fires via wire

gas:sheet_write — writes or updates a row in a Google Sheet
  props: sheet: string, collect: { field: "#nodeId.value" }
  result: { ok: boolean }

gas:sheet_delete — deletes a row from a Google Sheet by key
  props: sheet: string, key_column: string, collect: { key: "#nodeId.value" }

gas:save_property — persists a key/value to ScriptProperties (survives deploys)
  props: key: string, collect: { value: "#nodeId.value" }
  use for: webhook URLs, config values, user preferences
  result: { ok: boolean }

gas:send_email — sends email via the script owner's Gmail
  props: collect: { to, subject, body }

gas:chat_message — sends to Google Chat via webhook URL or SA bot
  props: collect: { message, webhook_url (optional) }
  format: tries cardsV2 first, falls back to plain text

gas:directory_search — searches Google Workspace directory
  props: collect: { query: "#nodeId.value" }
  result: array of { name, email, jobTitle, department, photoUrl }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. WIRING PATTERNS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Atom input wire:
  "wire": { "atomProp": "#nodeId.field" }
  e.g. data_table rows: { "wire": { "rows": "#incidents_enriched.result" } }

Action input collect:
  "collect": { "actionProp": "#nodeId.value" }
  e.g. { "collect": { "value": "#webhook_url_mem.value" } }

Timer → action (auto-refresh):
  Add Timer primitive; wire action: { "wire": { "trigger": "#refresh_5s.tick" } }

User input → ValueStore → action:
  form_input wire.setValue → "#mem_id.setValue"
  action collect → { "field": "#mem_id.value" }

DerivedStore SLA pattern:
  1. gas:sheet_query returns rows with opened_at timestamp
  2. DerivedStore augment_rows adds elapsed_sec, elapsed_fmt, sla_state columns
  3. data_table wires rows to #enriched.result; sla_state column uses type: sla_badge
`;
