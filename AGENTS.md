# a2ui-catalogue — Agent Entry Point

**This file exists so that ANY coding agent (Gemini, Antigravity, Codex, Claude, …)
finds the working rules.** The canonical rules live in `CLAUDE.md` — read it in full
before doing anything. `project.yaml` is the inventory (deployments, script IDs,
policy, declared processes); never carry identifiers from conversation memory when
the manifest declares them.

## Non-negotiables (summary — CLAUDE.md is authoritative)

1. **Every operation goes through a declared process.**
   `python3 ops/ops.py list` → `python3 ops/ops.py run <process>`.
   If the operation you need is not declared, declare it in `project.yaml`
   `processes:` first, then run it. **Raw `clasp push` / `clasp deploy` or ad-hoc
   command chains are forbidden** — improvisation is the failure mode this system
   exists to prevent. "ops.py run X *or* standard clasp push" is not a plan; it is
   the bug.
2. **Nothing new is published** to a2uicatalog.ai or any public surface without
   explicit per-artifact opt-in from Curtis (`policy.published` in `project.yaml`,
   enforced by tests). Never `git add -A`. Commits go through
   `python3 ops/ops.py commit "<msg>"`; push through `ops.py run repo-publish`.
3. **Renderer source is ground truth.** When `atoms/schema.yaml` prose and a
   renderer `.gs` file disagree about a field shape, the renderer wins
   (known case: `spring_nodes` edges are `{from, to}` node IDs, not the
   documented `{a, b}` index pairs).
4. **Verify before shipping:** `python3 -m pytest tests/ -q`. Check
   `ops/log.jsonl` before re-diagnosing anything — a previous run may have
   already recorded it.
5. Encoded `?p=` URLs are emitted by `scripts/make_url.py` only — never
   hand-typed or copied between surfaces.

Private-side operations (clasp identities, deploy mechanics, GAS gotchas) are
documented in the **a2ui-private** repo's `AGENTS.md` — read that too before any
deployment work.

If you take actions in this repo, log what you did and why in your own scratch
file under `/home/curtis/a2ui-private/` (agent logs never go in this public tree).
