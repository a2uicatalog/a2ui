#!/usr/bin/env python3
"""Generate web/substrate catalogue from schema.yaml.

Splits atoms by category into browseable sections with realistic demo data.
Outputs as a dict ready for Firestore publishing.

Usage:
    python3 scripts/generate_web_catalogue.py
"""
import sys
import yaml
from pathlib import Path

CATALOGUE_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = CATALOGUE_ROOT / "atoms" / "schema.yaml"

with open(SCHEMA_PATH) as f:
    schema = yaml.safe_load(f)
    ALL_ATOMS = schema["blocks"]

# Categories from catalogue_stage_deck.py
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

def atom_demo_data(atom_type: str) -> dict:
    """Return demo data for an atom type."""
    demos = {
        "stat_card": {"stats": [{"label": "Users", "value": "1.2k", "delta": "+12%"}]},
        "key_takeaways": {"items": [{"text": "Key insight about this atom type"}]},
        "chartjs_line": {"labels": ["Jan", "Feb", "Mar"], "datasets": [{"label": "Data", "data": [10, 20, 30]}]},
        "chartjs_bar": {"labels": ["A", "B", "C"], "datasets": [{"label": "Count", "data": [5, 10, 15]}]},
        "badge_group": {"badges": [{"text": "Example", "color": "#3b82f6"}]},
        "callout": {"style": "info", "text": "This is an example callout"},
        "code": {"language": "python", "text": "def example():\n    return 'Hello'"},
        "author_bio_card": {"name": "Example Author", "bio": "Demo biography", "image": "https://picsum.photos/60/60?random=1"},
        "carousel": {"slides": [{"url": "https://picsum.photos/600/300?random=1", "label": "Slide 1"}]},
        "table": {"headers": ["Name", "Value"], "rows": [["Example", "Demo"]]},
        "before_after": {"before_url": "https://picsum.photos/300/200?random=1", "after_url": "https://picsum.photos/300/200?random=2", "alt": "Comparison"},
        "metric_comparison_card": {"label": "Metric", "value": 42, "previous": 30},
        "mini_sparkline_set": {"series": [{"label": "Trend", "data": [1, 2, 3, 4, 5]}]},
        "uptime_timeline": {"uptime": 99.9, "days": 30},
        "prerequisite_checklist": {"items": [{"text": "Step 1", "completed": True}]},
        "cli_command": {"command": "example --flag value", "description": "An example command"},
        "keyboard_shortcut": {"keys": ["⌘", "K"]},
        "http_request_block": {"method": "GET", "url": "/api/example", "description": "Example endpoint"},
        "api_param_table": {"params": [{"name": "param", "type": "string", "required": True, "description": "Description"}]},
    }
    return demos.get(atom_type, {})

def generate_catalogue() -> dict:
    """Generate full catalogue structure."""
    atoms_by_type = {a["type"]: a for a in ALL_ATOMS}

    sections = {}
    for category, atom_types in CATEGORIES.items():
        atoms_in_category = [atoms_by_type[t] for t in atom_types if t in atoms_by_type]
        if not atoms_in_category:
            continue

        blocks = [
            {"type": "heading", "level": 2, "text": category},
            {"type": "key_takeaways", "items": [
                {"text": f"{len(atoms_in_category)} atoms in this category covering {category.lower()}."}
            ]},
        ]

        # Add 2-3 atom examples per category
        for atom in atoms_in_category[:3]:
            blocks.append({
                "type": "heading",
                "level": 3,
                "text": f"`{atom['type']}`"
            })
            if atom.get("description"):
                blocks.append({"type": "callout", "style": "info", "text": atom["description"]})

            demo = atom_demo_data(atom["type"])
            if demo:
                demo["type"] = atom["type"]
                blocks.append(demo)

        sections[category] = blocks

    return sections

def build_catalogue_body(sections: dict) -> str:
    """Convert sections to HTML body for Firestore."""
    # Build as simple HTML for now - actual rendering happens on blog
    html_parts = [
        '<article>',
        '<h1>A2UI Atom Catalogue</h1>',
        '<p>Complete reference of all A2UI atoms across 22 categories, with examples and surface compatibility.</p>',
    ]

    for category, blocks in sections.items():
        html_parts.append(f'<h2>{category}</h2>')
        # In real implementation, render each block via web_article renderer

    html_parts.append('</article>')
    return '\n'.join(html_parts)

if __name__ == "__main__":
    sections = generate_catalogue()
    print(f"Generated {len(sections)} category sections")
    print(f"Total atoms: {len(ALL_ATOMS)}")

    # Output as JSON for consumption by publish script
    import json
    output = {
        "title": "A2UI Atom Catalogue",
        "description": f"Complete reference of {len(ALL_ATOMS)} atoms across {len(sections)} categories",
        "sections": {k: len(v) for k, v in sections.items()},
        "timestamp": __import__('datetime').datetime.now().isoformat(),
    }
    print(json.dumps(output, indent=2))
