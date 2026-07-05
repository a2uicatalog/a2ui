# A2UI-State Specification v1.0
**Status:** Pilot — 10-atom reference implementation  
**Surface target:** `google-apps-script-web` (GAS sidebar)  
**Schema version:** `1.0`

---

## 1. What This Is

A2UI-State extends the declarative atom catalog with **behavioral state atoms** — invisible primitives that hold, validate, filter, and route data. An AI agent assembles both visual and behavioral atoms into a single JSON payload; the client runtime wires them together and executes all state transitions locally, without a server round-trip.

The core value: a GAS sidebar that reacts to user input instantly. No `google.script.run` call until final submission.

**Architecture (two atom types, one wire layer):**

```
Agent emits JSON payload
         │
         ▼
┌─────────────────────────────────────────┐
│         A2UI State Engine               │
│  ┌─────────────────┐  ┌──────────────┐ │
│  │ Behavioral Atoms│◄─►│ Visual Atoms │ │
│  │ (state graph)   │   │ (DOM layer)  │ │
│  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────┘
```

Behavioral atoms form a reactive graph. Visual atoms read from and write to that graph via **wires**. The rendering client resolves theme tokens at paint time — state primitives carry no visual concerns.

---

## 2. Wire Contract

### 2.1 Syntax

A wire expression is a string starting with `#` that resolves to a node output:

```
#<nodeId>.<outputProperty>
```

Examples: `#amount_mem.value`, `#amount_check.isInvalid`, `#wizard.activeIndex`

### 2.2 Direction

| Direction | Applied to | Effect |
|---|---|---|
| **Input wire** | Visual atom prop | State output → atom prop, reactive |
| **Output wire** | Visual atom event | User event → state node input trigger |
| **Primitive wire** | Behavioral atom input | State output → primitive input, reactive |

### 2.3 Error Behaviour (required engine behaviour)

| Condition | Engine behaviour |
|---|---|
| Wire target node not found | `console.warn('[A2UI] Wire target "<id>" not found')` then no-op |
| Wire target property not found | `console.warn('[A2UI] Node "<id>" has no property "<prop>"')` then no-op |
| Malformed wire expression (no `#`, no `.`) | `console.warn('[A2UI] Malformed wire: "<expr>"')` then skip |
| Node ID contains invalid characters | `throw new Error('[A2UI] Invalid node ID: "<id>"')` at init |

Wire failures are never silent. No exception should crash the engine — warn and continue.

### 2.4 Type System

| Type | Description |
|---|---|
| `boolean` | `true` / `false` |
| `string` | UTF-8 text |
| `number` | Integer or float |
| `array[object]` | Ordered list of key-value objects |
| `object` | Key-value dictionary |
| `event` | Trigger pulse — value may be `null` or carry a payload |

### 2.5 Security Requirements

**Engines must enforce these before accepting a payload:**

1. **Node ID format:** Only `[a-zA-Z0-9_-]` allowed. Reject anything else at init. Prevents prototype pollution via `Map` key injection.
2. **String output sanitization:** Before writing a `string` wire output to a DOM text prop, engines must use `textContent` assignment or equivalent sanitization — never raw `innerHTML`. Prevents agent-injected XSS via `ValueStore → display atom`.
3. **Regex pattern length cap:** `StringValidator.pattern` values longer than 200 characters must be rejected with a fallback to passthrough (`.*`). Prevents ReDoS from agent-supplied pathological patterns.
4. **Payload source trust:** Payloads are treated as untrusted input (an AI agent produced them). The engine runs in the same JS context as `google.script.run` — a compromised atom cannot be permitted to execute arbitrary code.

---

## 3. The 10-Atom Pilot Registry

All 10 atoms appear in the Budget Request Wizard reference implementation (Section 4). No atom is in the registry without a working demo.

### 3.1 Visual Atoms

#### `text_input`
Two-way binding: feeds user keystrokes into state, reflects state back to the field.

| Hook | Direction | Type | Description |
|---|---|---|---|
| `value` | Input | `string` | Sets the current field value |
| `disabled` | Input | `boolean` | Prevents user interaction |
| `onChange` | Output | `string` | Fires on each keystroke with current field value |

#### `data_table`
Reactive grid. Rows are wired from state; row selection emits the full row object.

| Hook | Direction | Type | Description |
|---|---|---|---|
| `rows` | Input | `array[object]` | Data to render |
| `loading` | Input | `boolean` | Shows shimmer skeleton |
| `onRowClick` | Output | `object` | Emits the full row object on selection |

#### `inline_feedback_message`
Conditional alert strip. Shown or hidden by a boolean wire.

| Hook | Direction | Type | Description |
|---|---|---|---|
| `visible` | Input | `boolean` | Shows the element when true |
| `text` | Input | `string` | Alert copy (sanitized before render) |
| `type` | Input | `string` (enum: `error`, `warning`, `success`) | Controls colour token |

#### `toggle_switch`
Binary switch with two-way binding.

| Hook | Direction | Type | Description |
|---|---|---|---|
| `checked` | Input | `boolean` | Sets switch state |
| `disabled` | Input | `boolean` | Prevents interaction |
| `onToggle` | Output | `boolean` | Emits new state on flip |

#### `ripple_button`
Action trigger. Can be gated by a boolean state condition.

| Hook | Direction | Type | Description |
|---|---|---|---|
| `disabled` | Input | `boolean` | Prevents activation |
| `onClick` | Output | `event` | Fires on click (payload: `null`) |

---

### 3.2 Behavioral State Atoms

Behavioral atoms never render. They process data and emit reactive outputs.

#### `ValueStore`
In-memory slot. Holds any value; emits on every mutation.

| Hook | Direction | Type | Description |
|---|---|---|---|
| `setValue` | Input (trigger) | `any` | Replaces stored value |
| `value` | Output | `any` | Current stored value — fires on change |

#### `ArrayFilter`
Client-side search. Filters a static or wired array by a string query.

| Hook | Direction | Type | Description |
|---|---|---|---|
| `source` (prop or wire) | Input | `array[object]` | Master dataset |
| `query` (wire) | Input | `string` | Filter string — case-insensitive substring match |
| `filterKey` (prop) | Config | `string` | Object property to match against |
| `output` | Output | `array[object]` | Filtered result — fires on every query or source change |

When `query` is empty, `output` equals `source` unmodified.

#### `StringValidator`
Pattern validator. Watches a string state output and emits validity.

| Hook | Direction | Type | Description |
|---|---|---|---|
| `source` (prop, wire expr) | Input | `string` | State path to watch (e.g. `#amount_mem.value`) |
| `pattern` (prop) | Config | `string` | Regex pattern — max 200 chars |
| `errorMessage` (prop) | Config | `string` | Message to emit on failure |
| `isValid` | Output | `boolean` | `true` when source matches pattern |
| `isInvalid` | Output | `boolean` | Complement of `isValid` (convenience for wiring `visible`) |
| `errorMessage` | Output | `string` | Empty when valid; configured message when invalid |

#### `NumericThreshold`
Boundary comparator. Evaluates a numeric state value against a threshold.

| Hook | Direction | Type | Description |
|---|---|---|---|
| `source` (prop, wire expr) | Input | `number\|string` | State path to watch — coerced to `Number` |
| `threshold` (prop) | Config | `number` | Comparison boundary |
| `operator` (prop) | Config | `string` (enum: `gt`, `gte`, `lt`, `lte`, `eq`) | Comparison direction |
| `isTriggered` | Output | `boolean` | `true` when comparison passes |
| `isNotTriggered` | Output | `boolean` | Complement — convenience for gating submit buttons |

#### `StepNavigator`
Step index tracker. Drives multi-step wizard flows.

| Hook | Direction | Type | Description |
|---|---|---|---|
| `totalSteps` (prop) | Config | `number` | Number of steps (clamps index to `[0, totalSteps-1]`) |
| `next` | Input (trigger) | `event` | Advances index by 1 |
| `prev` | Input (trigger) | `event` | Decrements index by 1 |
| `jumpTo` | Input (trigger) | `number` | Sets index directly |
| `activeIndex` | Output | `number` | Current step — fires on change |

---

## 4. Payload Schema

```json
{
  "schemaVersion": "1.0",
  "type": "a2ui_wired_surface",
  "surfaceId": "string — unique identifier",
  "surfaceCompatibility": "google-apps-script-web | web | meet-stage",
  "stepBinding": "#<navigatorId>.activeIndex",
  "state_primitives": [
    {
      "primitive": "ValueStore | ArrayFilter | StringValidator | NumericThreshold | StepNavigator",
      "id": "string — [a-zA-Z0-9_-] only",
      "props": {},
      "wire": {}
    }
  ],
  "layout": [
    {
      "atom": "string — atom type",
      "id": "string — [a-zA-Z0-9_-] only",
      "step": "number — optional; if set, element only renders when stepBinding matches",
      "props": {},
      "wire": {}
    }
  ]
}
```

The `stepBinding` field is a wire expression pointing to a `StepNavigator.activeIndex`. Layout elements with a `step` property are shown only when `activeIndex === step`. Elements without `step` are always visible.

---

## 5. Reference Implementation

**Budget Request Wizard** — 2-step GAS sidebar using all 10 pilot atoms.

**Step 0:** Search budget lines and select one (`text_input`, `data_table`, `ripple_button`)  
**Step 1:** Enter amount, confirm, submit (`text_input`, `inline_feedback_message` ×2, `toggle_switch`, `ripple_button`)  
**State:** `ValueStore` ×2, `ArrayFilter`, `StringValidator`, `NumericThreshold`, `StepNavigator`

See `payloads/budget-wizard.json` for the full payload.

**What it demonstrates:**

| Atom | Wire demonstrated |
|---|---|
| `text_input` (search) | `onChange` → `ValueStore.setValue`; `value` ← `ValueStore.value` |
| `text_input` (amount) | `onChange` → `ValueStore.setValue`; `value` ← `ValueStore.value` |
| `data_table` | `rows` ← `ArrayFilter.output`; `onRowClick` → `ValueStore.setValue` |
| `inline_feedback_message` (format) | `visible` ← `StringValidator.isInvalid`; `text` ← `StringValidator.errorMessage` |
| `inline_feedback_message` (approval) | `visible` ← `NumericThreshold.isTriggered` |
| `toggle_switch` | `onToggle` → `ValueStore.setValue`; `checked` ← `ValueStore.value` |
| `ripple_button` (Next) | `onClick` → `StepNavigator.next` |
| `ripple_button` (Back) | `onClick` → `StepNavigator.prev` |
| `ripple_button` (Submit) | `disabled` ← `StringValidator.isInvalid` |
| `ValueStore` (search_mem) | Feeds query into `ArrayFilter` |
| `ValueStore` (amount_mem) | Feeds value into `StringValidator` + `NumericThreshold` |
| `ArrayFilter` | `wire.query` ← `#search_mem.value` |
| `StringValidator` | `props.source` → `#amount_mem.value` |
| `NumericThreshold` | `props.source` → `#amount_mem.value`, threshold 500 |
| `StepNavigator` | Drives step visibility via `stepBinding` |

---

## 6. Engine Implementation

See `spec/a2ui-state-engine.js` for the complete, runnable implementation.

The engine contract:
- `new A2UIStateEngine(spec)` — initialises all primitives, resolves all source wires
- `engine.compileWires(layoutElement, domBridge)` — binds visual atom props to state outputs
- `engine.bindOutput(outputWireExpr, eventValue)` — routes a user event into the state graph
- `engine.registerListener(nodeId, property, callback)` — subscribe to reactive output (fires immediately with current value)
- `engine.trigger(nodeId, inputName, value)` — invoke a primitive input handler

The `domBridge` interface required by the engine:
```javascript
{
  setProp(elementId, propName, value) { /* update DOM */ },
  getText(elementId) { /* read current text value */ }
}
```
