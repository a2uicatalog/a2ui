#!/usr/bin/env python3
"""Push A2UI catalogue slides to a local Meet stage.

Usage:
    export STAGE_API_KEY=<key>
    export CONCIERGE_API_URL=http://127.0.0.1:8085  # default
    export CAPTURE_SPACE=spaces/local-preview         # default

    python scripts/push_catalogue_stage.py            # push slide 0 (cover)
    python scripts/push_catalogue_stage.py --slide 3  # push specific slide
    python scripts/push_catalogue_stage.py --list     # list all slides

Arrow through slides interactively:
    python scripts/push_catalogue_stage.py --interactive
"""
import argparse, asyncio, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import yaml

from renderers.meet_stage import render, LAYOUTS

# ── Config ────────────────────────────────────────────────────────────────────

API   = os.environ.get("CONCIERGE_API_URL", "http://127.0.0.1:8085")
KEY   = os.environ.get("STAGE_API_KEY", "")
SPACE = os.environ.get("CAPTURE_SPACE", "spaces/local-preview")

HEADERS = {"Content-Type": "application/json", **({"Authorization": f"Bearer {KEY}"} if KEY else {})}

# ── Schema ────────────────────────────────────────────────────────────────────

with open(Path(__file__).parent.parent / "atoms" / "schema.yaml") as f:
    atoms = yaml.safe_load(f)["blocks"]
    atoms_by_type = {a["type"]: a for a in atoms}

CATEGORIES = {
    "Foundations": ["body", "closing", "heading", "intro", "subheading"],
    "Reading Experience": ["article_hero", "article_series_nav", "post_metadata_bar", "reading_progress_bar", "scroll_to_top", "table_of_contents"],
    "Documentation": ["changelog_entry", "footnote", "footnote_group", "further_reading", "glossary_term", "release_notes", "resources_list", "table", "tabs", "timeline"],
    "Navigation & Structure": ["anchor_list", "breadcrumb", "faq_accordion", "pagination", "stepper", "tab_bar"],
    "Content Structure": ["bullet_list", "callout", "caution_block", "checklist_interactive", "divider", "key_takeaways", "key_value", "learning_objectives", "pipeline", "sidebar_note", "steps", "summary_box"],
    "Text & Quotes": ["blockquote_with_avatar", "pull_stat", "quote"],
    "Containers & Modals": ["accordion_item", "collapsible_panel", "css_modal", "css_slide_panel", "flip_card", "hover_card", "tooltip"],
    "Cards & Components": ["badge_group", "notification_badge", "rating_stars", "star_rating_display", "stat_card", "toggle_switch"],
    "Code & Technical": ["annotated_code", "api_param_table", "api_reference", "before_after", "code", "code_diff", "code_snippet_pair", "http_request_block", "tabbed_code", "terminal_block", "file_tree"],
    "Design Tools": ["css_dropdown_menu", "custom_checkbox_group", "expandable_list", "poll_block", "segmented_control"],
    "Commerce & Pricing": ["pricing_tier_card", "pricing_tier_group"],
    "Comparison & Analysis": ["capability_checklist", "comparison_grid", "feature_matrix", "pros_cons_list", "product_spec_table", "rating_comparison", "side_by_side_spec", "versus_block"],
    "Inline Tools": ["abbr_tooltip", "copy_to_clipboard", "expandable_text", "glossary_inline"],
    "Technical Reference": ["cli_command", "copy_code_button", "env_var_list", "json_tree_viewer", "keyboard_shortcut", "log_output", "prerequisite_checklist"],
    "Warnings & Status": ["alert_banner", "deprecation_notice", "experimental_banner", "status_pill", "version_badge"],
    "Media": ["carousel", "color_swatch_grid", "diagram", "framed_screenshot", "gallery", "image", "image_hotspots", "image_pair", "image_with_caption", "pdf_preview", "video_card", "video_pair", "video_thumbnail", "zoomable_image"],
    "Data Visualization": ["benchmark_comparison", "chartjs_bar", "chartjs_line", "data_table_sortable", "donut_stat", "heatmap", "task_list", "sentiment_summary", "metric_comparison_card", "metric_delta", "mini_sparkline_set", "progress_bar", "progress_circle", "sparkline", "status_dashboard", "trend_indicator", "uptime_timeline", "conversion_funnel", "gauge_sla", "stacked_area", "scatter_trend", "call_mood_board", "github_activity_grid"],
    "Social & Engagement": ["author_bio_card", "avatar_group", "contributor_list", "customer_logo_grid", "expert_endorsement", "follow_button", "follow_cta", "media_mention_card", "newsletter_cta", "reaction_group", "review_callout", "share_quote", "social_feed_embed", "social_share_bar", "testimonial_card"],
    "UI Utilities": ["command_palette", "empty_state", "inline_feedback_message", "loading_skeleton", "search_result_card", "spinner", "toast_notification"],
    "Utilities & Links": ["document_link", "github_repo_card", "repo_links"],
    "Video & Audio": ["audio_link", "audio_player", "youtube"],
    "External Embeds": ["embed_codepen", "embed_gist", "embed_google_slides", "embed_stackblitz", "embed_tweet", "figma_embed", "lottie_animation", "live_demo_embed"],
}

# ── Slide builders ────────────────────────────────────────────────────────────

def _atom_grid(cat_atoms: list) -> str:
    items = ""
    for atom in cat_atoms:
        compact = atom.get("compact_description", atom.get("description", ""))[:70]
        items += (
            f'<div style="padding:8px 10px;background:rgba(255,255,255,0.05);border-radius:6px;'
            f'border:1px solid rgba(0,242,255,0.15);overflow:hidden;">'
            f'<div style="font-family:monospace;font-size:0.72rem;color:#00f2ff;margin-bottom:3px;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{atom["type"]}</div>'
            f'<div style="font-size:0.6rem;color:rgba(255,255,255,0.5);line-height:1.3;'
            f'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">'
            f'{compact}</div>'
            f'</div>'
        )
    return (
        f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));'
        f'gap:8px;overflow:hidden;">{items}</div>'
    )

def build_cover() -> str:
    stat_blocks = "".join(
        f'<div style="text-align:center;padding:16px 24px;background:rgba(0,242,255,0.08);'
        f'border:1px solid rgba(0,242,255,0.2);border-radius:10px;">'
        f'<div style="font-size:2rem;font-weight:700;color:#00f2ff;">{v}</div>'
        f'<div style="font-size:0.75rem;color:rgba(255,255,255,0.5);margin-top:4px;">{l}</div>'
        f'</div>'
        for l, v in [("Atoms", str(len(atoms))), ("Categories", str(len(CATEGORIES))), ("Surfaces", "4")]
    )
    return (
        f'<div style="width:100%;height:100%;display:flex;flex-direction:column;align-items:center;'
        f'justify-content:center;gap:24px;padding:40px;">'
        f'<h1 style="font-size:2.5rem;font-weight:800;color:#00f2ff;letter-spacing:-0.02em;">A2UI Atom Catalogue</h1>'
        f'<p style="font-size:1rem;color:rgba(255,255,255,0.55);">'
        f'{len(atoms)} atoms · {len(CATEGORIES)} categories · 4 surfaces</p>'
        f'<div style="display:flex;gap:20px;">{stat_blocks}</div>'
        f'<p style="font-size:0.78rem;color:rgba(255,255,255,0.3);margin-top:4px;">'
        f'Slide 1 of {len(CATEGORIES)+1} — use script --slide N to navigate</p>'
        f'</div>'
    )

def build_category_slide(cat_name: str, atom_types: list, slide_num: int, total: int) -> str:
    cat_atoms = [atoms_by_type[t] for t in sorted(atom_types) if t in atoms_by_type]
    grid = _atom_grid(cat_atoms)
    return (
        f'<div style="width:100%;height:100%;display:flex;flex-direction:column;padding:20px;gap:14px;overflow:hidden;">'
        f'<div style="display:flex;align-items:baseline;gap:10px;flex-shrink:0;">'
        f'<h2 style="font-size:1.3rem;font-weight:700;color:#00f2ff;">{cat_name}</h2>'
        f'<span style="font-size:0.78rem;color:rgba(255,255,255,0.35);">{len(cat_atoms)} atoms</span>'
        f'<span style="margin-left:auto;font-size:0.7rem;color:rgba(255,255,255,0.25);">{slide_num}/{total}</span>'
        f'</div>'
        f'<div style="flex:1;min-height:0;overflow:hidden;">{grid}</div>'
        f'</div>'
    )

def all_slides() -> list[tuple[str, str]]:
    """Returns list of (label, body_html) for every slide."""
    slides = [("Cover", build_cover())]
    total = len(CATEGORIES) + 1
    for i, (cat_name, atom_types) in enumerate(CATEGORIES.items(), start=2):
        body = build_category_slide(cat_name, atom_types, i, total)
        slides.append((cat_name, body))
    return slides

def wrap_dark(body_html: str) -> str:
    return (
        f'<style>*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}'
        f'html,body{{width:100vw;height:100vh;background:#0f1117;color:#e8eaed;'
        f'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;overflow:hidden;}}'
        f'</style>{body_html}'
    )

# ── Push ──────────────────────────────────────────────────────────────────────

async def push_slide(body_html: str, version: int = 1):
    html = wrap_dark(body_html)
    payload = {
        "surfaceUpdate": {
            "components": [{
                "id": "root",
                "component": "gdm-html-panel",
                "html": html,
                "version": version,
            }]
        },
        "root": "root",
    }
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API}/api/render-stage/{SPACE}", headers=HEADERS, json=payload, timeout=10)
        return r.status_code, r.text

# ── CLI ───────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Push A2UI catalogue to Meet stage")
    parser.add_argument("--slide", type=int, default=0, help="Slide index (0 = cover)")
    parser.add_argument("--list", action="store_true", help="List all slides and exit")
    parser.add_argument("--interactive", action="store_true", help="Push slides interactively via stdin")
    args = parser.parse_args()

    slides = all_slides()

    if args.list:
        for i, (label, _) in enumerate(slides):
            print(f"  {i:2d}  {label}")
        return

    if args.interactive:
        print(f"  {len(slides)} slides. Enter slide number (or q to quit, Enter for next):")
        cur = 0
        while True:
            label, body = slides[cur]
            status, _ = await push_slide(body, version=cur + 1)
            print(f"  ✅ [{status}] Pushed slide {cur}: {label}")
            try:
                raw = input(f"  Next [{cur+1}] or enter number (q=quit): ").strip()
                if raw == "q":
                    break
                elif raw == "":
                    cur = min(cur + 1, len(slides) - 1)
                else:
                    cur = int(raw) % len(slides)
            except (EOFError, KeyboardInterrupt):
                break
        return

    idx = args.slide % len(slides)
    label, body = slides[idx]
    status, resp = await push_slide(body, version=idx + 1)
    icon = "✅" if status in (200, 204) else "❌"
    print(f"{icon} [{status}] Pushed slide {idx}: {label}  →  {API}/api/render-stage/{SPACE}")
    if status not in (200, 204):
        print(f"   {resp[:200]}")

if __name__ == "__main__":
    asyncio.run(main())
