#!/usr/bin/env python3
"""
Fail loudly if any published atom has ZERO entries in the private mcp-worker's
compose-routing eval set — the ground-truth prompt->atom fixture the
free-tier /api/compose routing pipeline is measured against (see
a2ui-private/mcp-worker/test/find-routing-gaps.mjs and
scripts/gen_atom_embeddings.py's MULTI_REP docstring for the full pipeline).

Why this matters: an atom that's never a TARGET in the eval set can never be
flagged as a routing miss no matter how bad its routing is — the gap-finder
is blind to it by construction. This bit us mid-session on 2026-07-14 (412 of
468 atoms silently uncovered, discovered only by accident). This check is the
cheap, free, deterministic half of that incident's fix — no network calls, no
model, just set arithmetic — chained into atom-change so a newly-added atom
can't ship invisible to routing-quality measurement again. The EXPENSIVE half
(actually fixing weak routing — candidate generation + bake-off + human-
reviewed merge) is intentionally a SEPARATE process (atom-multirep-onboard),
never auto-run here.

Soft-skips (exit 0) if the private sibling repo isn't present — this check is
an internal-estate convenience, not a requirement for the public repo to
build standalone.

Run:
  python3 scripts/check_eval_coverage.py
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
SPEC = os.path.join(ROOT, "public", "spec.json")
EVAL_PATH = os.path.join(ROOT, "..", "a2ui-private", "mcp-worker", "test", "compose-routing-eval.json")

# KNOWN, TRACKED, TEMPORARY exceptions -- a ratchet, not a permanent allowlist.
# Reviewable exactly like pre_push_audit.py's secret_hygiene content_allowlist:
# add an entry (with a reason + date) ONLY in the same commit that promotes
# the atom, remove it once `ops.py run atom-multirep-onboard` picks the atom
# up for real. This gate BLOCKS any uncovered atom NOT listed here, so
# nothing new can join the backlog silently -- but it can't be a hard
# zero-tolerance gate, because the one tool that fixes coverage
# (mcp-worker/test/generate-eval-prompts.mjs) fetches ground truth from the
# LIVE deployed a2uicatalog.ai/spec.json, not local state. A just-promoted
# atom is structurally uncoverable until its OWN promoting push has already
# gone live -- discovered 2026-09-13 promoting agent_sketchpad: running the
# full onboarding pipeline beforehand fixed 24 OTHER long-uncovered atoms
# (real pre-existing debt) but silently no-opped on agent_sketchpad itself
# ("0 to generate for") because the live site didn't know about it yet.
KNOWN_UNCOVERED_BASELINE = frozenset({
    "agent_sketchpad",  # promoted 2026-09-13; rerun atom-multirep-onboard
                        # after this push deploys, then remove this line.
    # Canvas hero / typography sprint, promoted 2026-09-19. Same rule: rerun
    # atom-multirep-onboard after this push deploys, then remove these lines.
    "weighted_words",
    "stance",
    "receipt",
    "changed_mind",
    "particle_type",
    "light_type",
    "living_type",
    "flow_field",
    "orbit_mark",
    "halftone_wave",
    "message_lanes",
    "signal_tunnel",
    "gradient_mesh_live",
    "wave_terrain",
    "orbit_rings",
    "type_scale",
    "readability_card",
    "drop_cap",
    "contrast_audit",
})


def main():
    if not os.path.isfile(EVAL_PATH):
        print(f"eval-coverage-check: skipped (private sibling repo not found at {EVAL_PATH})")
        return

    if not os.path.isfile(SPEC):
        print(f"❌ missing {SPEC} — run scripts/gen_public_catalog.py (or ops.py run catalog-rebuild) first", file=sys.stderr)
        sys.exit(1)

    with open(SPEC) as f:
        spec = json.load(f)
    all_types = {a["type"] for a in spec.get("atoms", [])}

    with open(EVAL_PATH) as f:
        eval_doc = json.load(f)
    covered = set()
    for entry in eval_doc.get("entries", []):
        for group in entry.get("acceptable", []):
            covered.update(group)

    uncovered = sorted(all_types - covered)
    new_uncovered = [t for t in uncovered if t not in KNOWN_UNCOVERED_BASELINE]
    stale_baseline = sorted(KNOWN_UNCOVERED_BASELINE - set(uncovered))

    if new_uncovered:
        print(f"❌ {len(new_uncovered)} of {len(all_types)} published atoms have ZERO eval coverage "
              f"and are NOT in KNOWN_UNCOVERED_BASELINE (invisible to the routing gap-finder):", file=sys.stderr)
        for t in new_uncovered:
            print(f"   {t}", file=sys.stderr)
        print("\nFix: node test/generate-eval-prompts.mjs --append (from a2ui-private/mcp-worker, "
              "needs a local ai-proxy-scratch wrangler dev on :8798 — see test/ai-proxy-scratch/), "
              "or run ops.py run atom-multirep-onboard.\n\nJust promoted this atom and the fix above "
              "reports \"0 to generate for\"? That tool reads the LIVE deployed spec.json, not local "
              "state -- it can't cover an atom before ITS OWN promoting push is already live. Add the "
              "atom to KNOWN_UNCOVERED_BASELINE in THIS commit instead, with a comment naming when to "
              "remove it (after this push deploys and atom-multirep-onboard is rerun).", file=sys.stderr)
        sys.exit(1)

    if stale_baseline:
        print(f"⚠️  {len(stale_baseline)} atom(s) in KNOWN_UNCOVERED_BASELINE now have real coverage -- "
              f"remove from the baseline (it's a ratchet, not a permanent exemption): {stale_baseline}")
    if uncovered:
        print(f"⚠️  {len(uncovered)} atom(s) still uncovered but tracked in KNOWN_UNCOVERED_BASELINE "
              f"(not blocking, not forgotten): {uncovered}")
    print(f"✅ eval-coverage-check: no NEW uncovered atoms outside the tracked baseline "
          f"({len(all_types) - len(uncovered)} of {len(all_types)} have real eval-set entries)")


if __name__ == "__main__":
    main()
