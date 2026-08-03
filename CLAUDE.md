# a2ui-catalogue — Working Rules

Declarative-first repo. State, policy, and **processes** are declared in
`project.yaml`; `ops/ops.py` executes them. Read `project.yaml` before
operating — it is the inventory (deployments, script IDs, properties,
staging policy, declared debt). Never carry identifiers in conversation
memory when the manifest declares them.

## Operations discipline

- **Every operation goes through a declared process:**
  `python3 ops/ops.py list` → `python3 ops/ops.py run <process>`.
  If the operation you need isn't declared, DECLARE IT in `project.yaml`
  `processes:` first, then run it. Improvised command sequences
  (raw `clasp push`/`clasp deploy`, ad-hoc regeneration chains) are the
  failure mode this system exists to prevent.
- After editing `atoms/schema.yaml` → `ops.py run atom-change`.
- After editing `spec/` or prompt contracts → `ops.py run prompt-update`
  (it bakes in the gemini_handoff cache bump — do not skip it).
- Renderer code changes → `ops.py run renderer-release` (deploys in place
  to the public deployment from the manifest inventory).
- Commits: `python3 ops/ops.py commit "<message>"` — stamps per the
  sync-window time mapping (09:00-11:59→08:00, 14:00-17:59→13:30,
  otherwise 13:00, Europe/Paris). Push: `ops.py run repo-publish`.
- Every run logs to `ops/log.jsonl` (local tier) — check it before
  re-diagnosing something a previous run already recorded.

## Publication boundaries (hard rules)

- **Nothing new is published to a2uicatalog.ai or any public surface
  without explicit per-artifact opt-in from Curtis.** Publication is
  declared in `project.yaml` (`policy.published`, `published_prompts`)
  and enforced by `tests/test_project_manifest.py`.
- Atoms carry `stage: preview | stable` (stable = default). Preview atoms
  are repo-only; all publication pipelines filter on the field
  (`tests/test_staging.py` enforces). Promotion = delete the stage line
  + `ops.py run atom-change`. New dev-first atoms START as preview.
- Private tier (`ops/`, `**/Code.private.gs`, `.clasp.json`) must never
  be tracked — the manifest audit fails the build if it is.
- Secrets live in Script Properties only (key names declared in
  `project.yaml`); never in code, payloads, or tracked files.

## Verification norms

- `python3 -m pytest tests/ -q` before any push; CI runs the manifest +
  staging audits before deploying the site.
- Encoded payload URLs are never hand-typed or hand-copied between
  surfaces — emit them from tool output (`scripts/make_url.py`) only.
- The stable /exec URL is server knowledge: inject `_getWebAppUrl()`
  via template at serve time; `window.location` only as gas-fakes
  fallback (see a2uithoughts.md for the incident history).

## Deploy discipline: deployed ≠ reachable

This system's characteristic failure is not a broken build — it is a
CORRECT build that never became true at the surface a user touches.
Six instances to date: the `ui://` template cache, a lost deploy race,
a clasp identity clobber, a Worker serving a stale compiled renderer,
a parity gate that blocked the deploy that would have satisfied it, and
a live capability three hosts could not discover. Assume this class
first, not last.

- **Never trust "I deployed it". Ask the live surface what it is
  running.** `worker-verify`, `gas-verify`, `check_ui_view_version`,
  `check_worker_renderer` each interrogate reality rather than a state
  file. After any deploy, run the ones that cover what you changed.
- **A change that is committed and pushed but not observable live is a
  DEPLOY problem until proven otherwise.** Check the CI run before
  re-reading the code — and before re-pushing.
- **Two failures on the same symptom: STOP.** Report what you observed,
  what you ruled out, and what you need. Do not attempt a third fix.
  (Adapted from `ops/improve.yaml` `budget.stop_when`, which had this
  rule while four consecutive pushes chased one misdiagnosed cause.)
- **Distinguish "appeared then reverted" from "never appeared".** The
  first is a race; the second is a gate or a trigger. They look
  identical in a single snapshot and different in a timeline — poll
  before concluding.
- **Any deliberate `tools/list` change needs the parity suite updated in
  the same commit** — the gate compares local to live, so an intended
  difference deadlocks the deploy that would resolve it.

## Improvement work is measured, not asserted

`ops/improve.yaml` (private tier) declares the benchmark. When the work
is improvement-shaped — "make X better", picking up backlog, or any
session likely to touch a scored dimension:

- **Score first.** A session is judged on the index delta it moved, not
  the work it appeared to do. Without a baseline there is no delta.
- **Report the delta at the end**, including when it is zero.
- **If the session's real work fitted no dimension, say so** — that is
  the declared trigger to revisit the benchmark, not a reason to skip it.

## Key references

- `project.yaml` — inventory, policy, processes (the lifecycle catalogue)
- `a2uithoughts.md` — design rationale and incident lessons (gitignored)
- `spec/training-md-v0.1.md` — training domain contract; prompts are
  GENERATED from it (`gen_training_prompt.py`) — edit the spec, not
  the prompt files
- Parser parity: `scripts/parse_training_md.py` is the reference;
  `training_parser.gs` must stay deep-equal (parity harness in pytest)
