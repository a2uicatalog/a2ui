#!/usr/bin/env python3
"""gen_catalog_index — the agent's deterministic catalog SELECTION menu.

`required_catalogs()` answers "given the atoms, which catalogs?" (payload -> catalogs,
a pure lookup). This answers the OTHER direction — "given a NEED, which catalog should I
reach into?" — by publishing a machine-readable index: every catalog's id, title, a
declared when-to-use, and its atoms (with one-line descriptions). The agent reads this to
pick catalogs by capability, so selection is grounded in declared metadata, not recall.

Emits public/catalogue/index.json. Wired into catalog-rebuild. Fails if any catalog in
atoms/atom-packs.yaml lacks a when-to-use here (no silent gaps in the menu).

Also carries each atom's `processing` block (spec/atom-processing-contract-v0.1.md, Tracks B/C)
straight through from schema.yaml when declared — pagination safety (e.g. module_map's
hub_aggregating) and required_scope. This is the artifact a2ui-private/gas-mcp/sync_embeds.py
copies into mcp-worker/src/catalog-data.js, so declaring it here is what makes it reach the
MCP layer without hand-maintained, drift-prone MCP-side copies.

Also carries each atom's `children` block (spec/childlist-migration-v0.1.md, Phase 0) — the
shape-aware, per-field declaration of which properties hold nested atom content (simple/
single/wrapper_list/wrapper_single + inner_path), when declared. Replaces name-based guessing
(MCP_CHILD_KEYS) with a fact read from the schema, same propagation path as `processing`.
"""
import json
import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACKS = os.path.join(ROOT, "atoms", "atom-packs.yaml")
SCHEMA = os.path.join(ROOT, "atoms", "schema.yaml")
OUT = os.path.join(ROOT, "public", "catalogue", "index.json")

BASE_URL = "https://a2uicatalog.ai"
BASE_SLUG = "a2ui-atoms-v1"

# Declared title + when-to-use per catalog. The when-to-use is the agent's selection
# signal — keep it about the NEED the catalog serves, not the atom list.
CATALOG_META = {
    "a2ui-atoms-v1": ("A2UI base atoms",
        "The standard catalog — structure, text, data display, inputs, actions and the "
        "wired state connectors. ALWAYS resolved; every surface uses it."),
    "a2ui-google-workspace-live-v1": ("Google Workspace (live data)",
        "Use when the surface shows the signed-in user's OWN live Google Workspace data — "
        "Gmail, Drive, Calendar, Sheets, Tasks, Chat, Meet. Server-fetched, per-user."),
    "a2ui-aviation-v1": ("Aviation, ATC & geo",
        "Use for air-traffic / geospatial surfaces — radar, ADS-B feeds, airspace maps, "
        "isometric fleet and 3-D geo views."),
    "a2ui-learning-v1": ("Learning & assessment",
        "Use for education/LMS surfaces — quizzes, flashcards, cohorts, progress tracking, "
        "rubrics, scenarios, certificates."),
    "a2ui-charts-v1": ("Data visualisation",
        "Use when the surface needs charts — bar/line/pie, sankey, heatmap, sparklines, "
        "gauges, funnels, trend viz."),
    "a2ui-competition-v1": ("Competition & tournaments",
        "Use for ranked competition surfaces — league/tournament standings with semantic "
        "highlights, round-by-round match schedules (table or courtside cards)."),
    "a2ui-marketing-v1": ("Marketing & landing",
        "Use for landing/marketing pages — pricing tables, testimonials, hero banners, "
        "feature grids, ratings, social proof."),
    "a2ui-editorial-v1": ("Editorial & long-form",
        "Use for articles/blog posts — intros, footnotes, table of contents, series "
        "navigation, further reading, social share."),
    "a2ui-embeds-v1": ("Third-party embeds",
        "Use to embed external content — YouTube, Figma, CodePen, StackBlitz, Maps, "
        "Slides, Lottie, social posts."),
    "a2ui-effects-v1": ("Motion & decorative",
        "Use for animation and decorative flourish — reveals, gradients, cursor effects, "
        "meteors/confetti, kinetic text. Presentation polish, not data."),
    "a2ui-meta-v1": ("Catalog & AI meta",
        "Use for surfaces ABOUT the catalog or AI tooling — atom anatomy, schema reveal, "
        "prompt-to-schema, Gemini handoff, model cards."),
    "a2ui-ops-v1": ("Status & ops",
        "Use for operational dashboards — status/SLA, Jira, sprint boards, notifications, "
        "changelogs, live polls and votes."),
    "a2ui-presentation-v1": ("Presentation",
        "Use for fullscreen multi-slide presentation surfaces (playbook)."),
    "a2ui-display-v1": ("General UI & content",
        "Use for general content/UI beyond the base primitives — richer cards, media, "
        "tags, comparison and steppers not in core."),
}


def _atom_descriptions():
    d = yaml.safe_load(open(SCHEMA))
    return {b["type"]: (b.get("compact_description") or b.get("description") or "")
            for b in d["blocks"] if isinstance(b, dict) and b.get("type")}


def _stable_atoms():
    """Staging filter — same rule as gen_public_catalog.py: only stable atoms
    are published; preview stays repo-only. Without this the index advertises
    catalogId files gen_public_catalog never writes (found 2026-07-10 when the
    first preview-only catalog, a2ui-competition-v1, produced a dangling ref)."""
    d = yaml.safe_load(open(SCHEMA))
    if os.environ.get("A2UI_CATALOG_FULL") == "1":
        return {b["type"] for b in d["blocks"] if isinstance(b, dict) and b.get("type")}
    return {b["type"] for b in d["blocks"]
            if isinstance(b, dict) and b.get("type") and b.get("stage", "stable") == "stable"
            and b.get("visibility") != "private"}


def _atom_processing():
    """type -> declared `processing` block (Track B/C), only for atoms that declare one."""
    d = yaml.safe_load(open(SCHEMA))
    return {b["type"]: b["processing"]
            for b in d["blocks"] if isinstance(b, dict) and b.get("type") and b.get("processing")}


def _atom_children():
    """type -> declared `children` block (Phase 0), only for atoms that declare one."""
    d = yaml.safe_load(open(SCHEMA))
    return {b["type"]: b["children"]
            for b in d["blocks"] if isinstance(b, dict) and b.get("type") and b.get("children")}


def _atom_entry(atom_type, desc, processing, children):
    entry = {"type": atom_type, "description": desc.get(atom_type, "")}
    if atom_type in processing:
        entry["processing"] = processing[atom_type]
    if atom_type in children:
        entry["children"] = children[atom_type]
    return entry


def main():
    part = yaml.safe_load(open(PACKS))
    desc = _atom_descriptions()
    processing = _atom_processing()
    children = _atom_children()

    missing = [c for c in part if c not in CATALOG_META]
    if missing:
        raise SystemExit(f"✗ no when-to-use declared for catalog(s): {', '.join(missing)} "
                         f"(add to CATALOG_META in scripts/gen_catalog_index.py)")

    stable = _stable_atoms()
    catalogs = []
    order = [BASE_SLUG] + sorted(c for c in part if c != BASE_SLUG)
    for slug in order:
        title, when = CATALOG_META[slug]
        atoms = sorted(a for a in part[slug] if a in stable)
        if not atoms:
            continue  # preview-only catalog: repo-only until an atom promotes
        catalogs.append({
            "catalogId": f"{BASE_URL}/catalogue/{slug}.json",
            "slug": slug,
            "title": title,
            "alwaysResolved": slug == BASE_SLUG,
            "whenToUse": when,
            "atomCount": len(atoms),
            "atoms": [_atom_entry(a, desc, processing, children) for a in atoms],
        })

    index = {
        "title": "A2UI catalogue index",
        "description": "The deterministic catalog selection menu — read whenToUse to pick "
                       "extension catalogs for a need; the base catalog is always resolved.",
        "baseCatalog": f"{BASE_URL}/catalogue/{BASE_SLUG}.json",
        "catalogCount": len(catalogs),
        "catalogs": catalogs,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write("\n")

    total = sum(c["atomCount"] for c in catalogs)
    print(f"wrote {OUT} — {len(catalogs)} catalogs, {total} atoms indexed")


if __name__ == "__main__":
    main()
