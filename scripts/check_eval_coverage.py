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
    if uncovered:
        print(f"❌ {len(uncovered)} of {len(all_types)} published atoms have ZERO eval coverage "
              f"(invisible to the routing gap-finder):", file=sys.stderr)
        for t in uncovered:
            print(f"   {t}", file=sys.stderr)
        print("\nFix: node test/generate-eval-prompts.mjs --append (from a2ui-private/mcp-worker, "
              "needs a local ai-proxy-scratch wrangler dev on :8798 — see test/ai-proxy-scratch/), "
              "or run ops.py run atom-multirep-onboard.", file=sys.stderr)
        sys.exit(1)

    print(f"✅ eval-coverage-check: all {len(all_types)} published atoms have ≥1 eval-set entry")


if __name__ == "__main__":
    main()
