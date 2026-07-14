#!/usr/bin/env python3
"""
Regenerate public/catalogue/atoms-embeddings.json — a 384-dim embedding vector
per published atom (via Cloudflare Workers AI's @cf/baai/bge-small-en-v1.5),
used by mcp-worker's /api/compose to route a natural-language request to
relevant atoms WITHOUT a chat-completion call (cosine similarity in JS instead).

Why this exists: measured live (2026-07-13) that the chat-based routing call
ate ~95% of the neuron cost of a full /api/compose request (~31 of ~33-41
neurons), because it stuffs the full 468-atom vocabulary into the prompt just
to pick 1-3 relevant types. An embedding-based router does the same job for a
fraction of the cost (~0.1 neurons per request to embed the incoming prompt;
the 468 atom vectors are precomputed once, here, not per-request) while
understanding semantic similarity a plain keyword match would miss.

Multi-representation atoms (2026-07-14): a handful of atoms get SEVERAL short
example-phrase vectors instead of one description-derived anchor, matched by
MAX similarity at query time (see MULTI_REP below and compose.js's
scoreAtomsMultiRep). Why: single-anchor embedding has a real, hard-to-fix
vocabulary gap — e.g. stat_card's real compact_description never contains the
word "card", so "show a card with our registrations" always routed to the
person_card family. Bake-off on a 10-target calibration set, live
(2026-07-14): single-vector routing scores 7/10; multi-rep scores 8/10 (the
best result found across every routing variant tried this session) once
tuned — an early cut caused a NEW regression (cohort_retention's vague
"performance chart" phrase out-scored metric_delta, which had no
representations of its own, by a 0.0002 margin — noise-level) that giving
metric_delta its own representations and tightening cohort_retention's
phrasing fixed. Add entries to MULTI_REP sparingly and re-run the bake-off
after any change — this list is hand-curated, not automatically generated,
and a careless addition can just as easily cause a new collision as fix one.

Companion, explicitly REJECTED after live testing (2026-07-14): a
prompt-decomposition step (split a multi-intent request into sub-intents via
a 3B chat call before routing each independently). Reliably dropped the
earlier clause in "X, then Y" prompts in 5 of 5 repeated runs against the
exact case it was meant to fix. Do not re-add without a fundamentally
different mechanism, not a reworded system prompt for the same approach.

NOT wired into CI (unlike gen_atom_json_schemas.py) — Workers AI's env.AI
binding only exists inside a deployed Worker's runtime, and GitHub Actions
can't call it directly. This script instead talks to Workers AI through a
throwaway local `wrangler dev` Worker with an [ai] binding, which requires an
authenticated wrangler session on the account (same one used to deploy).

Run manually whenever atoms/schema.yaml's published atom set changes
meaningfully (a new atom, a renamed one, a materially reworded
compact_description), or MULTI_REP below is edited — not on every commit:

  1. python3 scripts/gen_public_catalog.py     # refresh spec.json first if schema.yaml changed
  2. mkdir /tmp/embed-gen && cd /tmp/embed-gen
     cat > wrangler.toml <<'EOF'
     name = "atom-embed-gen-scratch"
     main = "worker.js"
     compatibility_date = "2024-09-23"
     account_id = "<see mcp-worker/wrangler.toml or blog-worker/wrangler.toml>"
     [ai]
     binding = "AI"
     EOF
     cat > worker.js <<'EOF'
     export default { async fetch(request, env) {
       const body = await request.json();
       const result = await env.AI.run(body.model, body.opts);
       return Response.json(result);
     }};
     EOF
     npx wrangler dev --port 8798 &
  3. python3 scripts/gen_atom_embeddings.py --endpoint http://localhost:8798/

Commit the resulting public/catalogue/atoms-embeddings.json like any other
generated artifact.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib import request as urlreq

ROOT = Path(__file__).parent.parent
SPEC = ROOT / "public" / "spec.json"
OUTPUT = ROOT / "public" / "catalogue" / "atoms-embeddings.json"
MODEL = "@cf/baai/bge-small-en-v1.5"

# Hand-curated, live-bake-off-verified (2026-07-14). Every atom type here MUST
# be a real published atom — check against public/spec.json before adding.
MULTI_REP = {
    "stat_card": [
        "single KPI value with label delta and accent colour indicator",
        "stat card dashboard",
        "display a key metric or big number",
        "high-impact business indicator card",
        "KPI summary block with change percentages",
    ],
    "metric_delta": [
        "big number metric with directional change indicator or percentage",
        "revenue or KPI up or down percent change",
        "quarterly growth figure with trend arrow",
        "metric card showing increase or decrease versus prior period",
        "percentage change indicator block",
    ],
    "inventory_table": [
        "multi-column detailed list representing data rows and actions",
        "spreadsheet grid with columns",
        "tabular list of records",
        "data inventory table overview",
        "searchable paginated table list",
    ],
    "icon_checklist": [
        "checklist with icons",
        "Material Design to-do list",
        "icon-based task list",
        "list with customizable icons",
        "checklist items with visual indicators",
    ],
    "user_profile_card": [
        "compact biographical overview card of an individual with photo placeholder",
        "user info profile block",
        "employee directory card avatar",
        "person profile layout",
        "biography card widget",
    ],
    "form": [
        "structured grouping of form inputs with a clear action button",
        "user submission form panel",
        "registration dialog box collecting credentials to build a membership",
        "newsletter sign up field email subscribe",
        "onboarding input card block",
    ],
    "cohort_retention": [
        "matrix tracking user retention performance patterns across multiple periods",
        "heatmap cohort retention grid",
        "customer retention matrix table by signup week or month",
        "triangular retention decay grid across cohorts",
        "churn rate grid",
    ],
    "sankey_flow": [
        "flow chart visualizing system distribution volumes across sequential nodes",
        "sankey flow diagram path",
        "resource distribution allocation visualizer",
        "directed flow quantity chart",
        "input output channel chart",
    ],
    "heatmap": [
        "matrix displaying numerical intensity as varying color gradients",
        "correlation matrix visualizer",
        "activity grid calendar chart",
        "color graded density map",
        "activity heatmap metric graph",
    ],
    "code": [
        "formatted code box with syntax highlighting and action interactions",
        "programming code block syntax",
        "developer script copy window",
        "raw source viewer component",
        "JSON configuration example",
    ],
    "changelog_entry": [
        "historical logs timeline listing software version updates sequentially",
        "product changelog timeline log",
        "historical release list chronological",
        "version release history track list",
        "updates timeline milestone list",
    ],
    "testimonial_card": [
        "horizontal slider transitioning social proof statements from clients",
        "customer review sliding quotes carousel",
        "rotating client testimonial cards",
        "interactive feedback slider quote",
        "happy client references",
    ],
    "customer_logo_grid": [
        "clean container showcasing brand badges of integrated partners",
        "trusted by logo grid display",
        "partner corporate badge icons",
        "sponsor graphic grid container",
        "enterprise customer logos group",
    ],
    "article_hero": [
        "dynamic landing area visualizer utilizing interactive canvas particles",
        "kinetic text motion headline",
        "interactive layout canvas intro",
        "modern dynamic splash screen",
        "eye-catching main page section",
    ],
    # Added via the onboarding pipeline (mcp-worker/test/find-routing-gaps.mjs ->
    # generate-multirep-candidates.mjs -> verify-multirep-candidates.mjs), 2026-07-14.
    # 3 of 23 evidence-flagged candidates passed the collision bake-off (real hit-rate
    # improvement, zero regressions on the 48-prompt eval set) — the other 20 either made
    # no measurable difference or actively regressed a different prompt; see
    # a2ui-private/mcp-worker/test/ for the full pipeline and rejected-candidate detail.
    "star_rating_display": [
        "show customer review ratings",
        "display product score and reviews",
        "star rating viewer with total reviews",
        "read-only review score display",
        "component to show rating and review count",
    ],
    "chartjs_pie": [
        "Circular graph with multiple sections",
        "Donut chart with customizable colors",
        "Pie chart with interactive legend",
        "Multi-part circle diagram with labels",
        "Segmented pie graph with data visualization",
    ],
    "chartjs_line": [
        "line graph for showing trends",
        "interactive trend chart",
        "displaying data over time",
        "line chart for analytics",
        "visualizing trend data",
    ],
    # Second onboarding-pipeline pass, 2026-07-14, run against the expanded 460-prompt
    # eval set (test/compose-routing-eval.json, grown from 48 to cover all 468 atoms).
    # 50 atoms flagged by find-routing-gaps.mjs; 13 passed the collision bake-off (real
    # improvement, zero regressions) — icon_checklist's entry above was REPLACED (its new
    # phrases outscored the original hand-curated set); the other 12 below are new
    # additions. 37 rejected candidates are not merged; see verify-multirep-candidates.mjs
    # output in a2ui-private for the full rejected/regression detail.
    "reveal": [
        "animation wrapper for my content",
        "entrance effect for child elements",
        "delayed animation container",
        "staggered animation for blocks",
        "animated intro for page sections",
    ],
    "sidebar_note": [
        "a box to hold extra information",
        "off to the side notes section",
        "where I can add some side comments",
        "a peripheral info container",
        "an aside box for additional context",
    ],
    "embed_stackblitz": [
        "live code editor for my project",
        "embed a StackBlitz sandbox",
        "dynamic coding environment",
        "add interactive code demo",
        "live IDE for web development examples",
    ],
    "lottie_animation": [
        "animated vector graphics player",
        "high performance animation renderer",
        "vector animation loader",
        "looping animation component",
        "lightweight motion graphics viewer",
    ],
    "lozenge": [
        "status indicator badge",
        "colored label for task status",
        "pill-shaped status component",
        "visual status indicator with text",
        "dynamic status badge with customizable appearance",
    ],
    "animated_beam": [
        "animated line between two points",
        "dynamic connector with labels",
        "SVG beam with animation effect",
        "curved link between nodes with animation",
        "animated path with customizable speed and color",
    ],
    "adsb_feed": [
        "live flight tracker for a specific area",
        "real-time aircraft positions in a bounding box",
        "ADS-B feed for a geographic region",
        "flight tracking data within a defined boundary",
        "air traffic updates for a particular zone",
    ],
    "badge": [
        "small label indicator",
        "colorful pill-shaped tag",
        "inline notification badge",
        "text-based status indicator",
        "colored marker pill",
    ],
    "cta_button": [
        "button to take action",
        "link with a prompt",
        "clickable call to action",
        "action trigger element",
        "interactive prompt button",
    ],
    "progress_store": [
        "Store student progress",
        "Where is my course data stored",
        "How to save learning state",
        "Connect to learning management system",
        "Save user progress in the background",
    ],
    "accordion_item": [
        "collapsible content box",
        "toggleable section",
        "click to expand panel",
        "folding header section",
        "expandable info block",
    ],
    "onboarding_stepper": [
        "Setup wizard for new users",
        "Guided tour for first time users",
        "Onboarding process with multiple steps",
        "Interactive tutorial for getting started",
        "Step-by-step introduction to the application",
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True,
                         help="throwaway wrangler-dev Worker URL exposing env.AI.run(model, opts) as {model, opts} -> AI response")
    args = parser.parse_args()

    spec = json.loads(SPEC.read_text())
    atoms = spec["atoms"]
    real_types = {a["type"] for a in atoms}
    bad = [t for t in MULTI_REP if t not in real_types]
    if bad:
        print(f"MULTI_REP references non-existent atom types: {bad}", file=sys.stderr)
        sys.exit(1)

    # One batched call: legacy anchor text for every atom, plus every multi-rep
    # phrase, in one request (proven to work up to 468 inputs in a single call).
    legacy_texts = [f"{a['type']}: {a.get('compact_description', '')}" for a in atoms]
    multirep_texts = []
    multirep_index = []  # (atom_type, phrase_position) per multirep_texts entry
    for atype, phrases in MULTI_REP.items():
        for p in phrases:
            multirep_texts.append(p)
            multirep_index.append(atype)

    all_texts = legacy_texts + multirep_texts
    body = json.dumps({"model": MODEL, "opts": {"text": all_texts}}).encode()
    req = urlreq.Request(args.endpoint, data=body, headers={"Content-Type": "application/json"})
    with urlreq.urlopen(req, timeout=90) as resp:
        result = json.loads(resp.read())

    if "error" in result:
        print(f"embedding call failed: {result['error']}", file=sys.stderr)
        sys.exit(1)

    vectors = result["data"]
    if len(vectors) != len(all_texts):
        print(f"mismatch: sent {len(all_texts)} texts but got {len(vectors)} vectors", file=sys.stderr)
        sys.exit(1)

    legacy_vecs = vectors[:len(legacy_texts)]
    multirep_vecs = vectors[len(legacy_texts):]

    reps_by_type = {}
    for atype, vec in zip(multirep_index, multirep_vecs):
        reps_by_type.setdefault(atype, []).append([round(x, 5) for x in vec])

    atoms_out = []
    for a, vec in zip(atoms, legacy_vecs):
        t = a["type"]
        if t in reps_by_type:
            atoms_out.append({"type": t, "representations": [{"vector": v} for v in reps_by_type[t]]})
        else:
            atoms_out.append({"type": t, "vector": [round(x, 5) for x in vec]})

    out = {
        "model": MODEL,
        "dim": result["shape"][1],
        "atoms": atoms_out,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"✓ {len(atoms_out)} atom embeddings ({len(reps_by_type)} multi-rep) → {OUTPUT}")


if __name__ == "__main__":
    main()
