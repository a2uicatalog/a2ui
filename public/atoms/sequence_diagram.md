# Sequence Diagram

Multi-actor message sequence diagram — participant boxes with dashed lifelines, per-message arrow rows in order, note bands, and labelled alt/opt/loop/par frames. Feature-parity with the mermaid sequenceDiagram / Google-A2A convention (solid arrow = call, dashed = return/async; optional autonumber) but fully declarative for an LLM (it describes actors + messages structurally, never mermaid syntax) and self-contained (pure HTML/CSS, no client-side JS — renders on every surface, not just web). General-purpose protocol/architecture diagram; not limited to 2-role chat threads the way chat_sequence is.

## Surfaces

web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| accent | string (optional, hex, default "#4f46e5") |
| theme | string (optional, "light"|"dark"|"site", default "light"). "site" follows the host page's light/dark theme (its CSS custom properties) instead of baking a fixed one — for embedding in a themed site. |
| autonumber | boolean (optional, default false) — prefix each message with a sequential number badge (mermaid's autonumber). |
| animate | boolean (optional, default false) — draw the messages in one by one, in order, as a CSS-only opacity reveal with no JS. Omitted or false renders exactly as before. Actor boxes, lifelines and frame borders and labels are visible from the start; each message (arrow, label and autonumber badge) and each note fades in at its turn, so nothing shifts. The content is in the DOM from the start, so assistive tech reads the whole diagram. Honours prefers-reduced-motion by showing the finished diagram at once. Animates on web and mcp-apps; the android lane cannot animate and ignores the flag, drawing the finished diagram. |
| animate_step_ms | integer (optional, default 600) — delay in milliseconds between successive reveals when animate is true. Allowed range 100 to 2000; out-of-range falls back to 600. The step is shortened if needed so the last item starts within 20 s, so the longest possible animation is about 20.5 s. |
| actors | required array of participants, left→right. Each is a plain string (used as both id and label) OR an object {id, label} for a mermaid-style alias (messages/notes may reference the short id while the box shows the friendly label). |
| messages | array; each item is one of — MESSAGE {from, to, text, kind?} where from/to are actor ids or labels; kind="return" (aliases reply=true / dashed=true) renders a DASHED arrow (a return or async/stream) vs the default solid arrow (a call/request), the mermaid -->> / ->> distinction; NOTE {note=true, text, over?} where over (an actor, or [a,b] pair) anchors the note box over that lifeline / across that span (mermaid's Note over X / Note over X,Y); omit over for a full-width band; FRAME {frame="alt"|"opt"|"loop"|"par"|"group", label, messages=[...], else?=[{label, messages}]} a labelled bordered box grouping nested messages (mermaid's alt/opt/loop/par control-flow frame; alt/par use the optional else branches for alternatives; frames nest). |

## Example payload

```json
{
  "type": "sequence_diagram",
  "actors": []
}
```

Live page: https://a2uicatalog.ai/atoms/sequence_diagram/
Full field contract: https://a2uicatalog.ai/spec.json
