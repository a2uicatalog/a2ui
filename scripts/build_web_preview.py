#!/usr/bin/env python3
"""Generate a self-contained HTML preview of all A2UI atoms rendered in web_article format.

Output: catalogue_web_preview.html (in repo root)

Usage:
    python3 scripts/build_web_preview.py
"""
import sys
import html as _html
import yaml
from pathlib import Path
from datetime import date, timedelta
import random

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from renderers.web_article import render as wa_render, _RENDERERS

with open(ROOT / "atoms" / "schema.yaml") as f:
    ALL_ATOMS = yaml.safe_load(f)["blocks"]

ATOMS_BY_TYPE = {a["type"]: a for a in ALL_ATOMS}

# ── Categories ─────────────────────────────────────────────────────────────────

CATEGORIES = {
    "Foundations":           ["body", "closing", "heading", "intro", "subheading"],
    "Reading Experience":    ["article_hero", "article_series_nav", "post_metadata_bar",
                              "reading_progress_bar", "scroll_to_top", "table_of_contents"],
    "Documentation":         ["changelog_entry", "footnote", "footnote_group", "further_reading",
                              "glossary_term", "release_notes", "resources_list", "table", "tabs", "timeline"],
    "Navigation & Structure":["anchor_list", "breadcrumb", "faq_accordion", "pagination",
                              "stepper", "tab_bar"],
    "Content Structure":     ["bullet_list", "callout", "caution_block", "checklist_interactive",
                              "divider", "key_takeaways", "key_value", "learning_objectives",
                              "pipeline", "sidebar_note", "steps", "summary_box"],
    "Text & Quotes":         ["blockquote_with_avatar", "pull_stat", "quote"],
    "Containers & Panels":   ["accordion_item", "collapsible_panel", "css_modal",
                              "css_slide_panel", "flip_card", "hover_card", "tooltip"],
    "Cards & Components":    ["badge_group", "notification_badge", "rating_stars",
                              "star_rating_display", "stat_card", "toggle_switch"],
    "Code & Technical":      ["annotated_code", "api_param_table", "api_reference",
                              "before_after", "code", "code_diff", "code_snippet_pair",
                              "http_request_block", "tabbed_code", "terminal_block", "file_tree"],
    "Design Tools":          ["color_swatch_grid", "css_dropdown_menu", "custom_checkbox_group",
                              "expandable_list", "poll_block", "segmented_control"],
    "Charts & Data Viz":     ["chartjs_bar", "chartjs_line", "chartjs_pie", "cohort_retention",
                              "donut_stat", "heatmap", "mini_sparkline_set",
                              "punch_card", "sankey_flow", "sparkline"],
    "Metrics & Status":      ["alert_banner", "data_table_sortable", "metric_comparison_card",
                              "metric_grid", "progress_bar", "progress_checkpoint",
                              "progress_circle", "rating_summary_bar", "stat_row",
                              "status_dashboard", "uptime_timeline"],
    "Timeline & Progress":   ["milestone_tracker", "progress_circle", "roadmap_card",
                              "stepper", "steps", "timeline"],
    "Media & Embeds":        ["audio_player", "carousel", "diagram", "gallery",
                              "image_pair", "lottie_animation", "video_pair", "youtube"],
    "External Embeds":       ["embed_codepen", "embed_gist", "embed_google_slides",
                              "embed_stackblitz", "embed_tweet", "figma_embed",
                              "live_demo_embed"],
    "Social & People":       ["author_bio_card", "blockquote_with_avatar",
                              "contributor_list", "social_proof_bar", "testimonial_card"],
    "Interactive & Forms":   ["checklist_interactive", "choicebox_group",
                              "feedback_prompt", "follow_up_chips", "form", "form_checkbox_group",
                              "form_date_picker", "form_input", "form_radio_group",
                              "form_select", "form_slider", "form_switch_group",
                              "modal", "poll_block", "variant_selector"],
    "Notifications & Alerts":["alert_banner", "call_mood_board", "inline_alert",
                              "notification_stack", "toast_notification"],
    "Tags & Taxonomy":       ["badge_group", "lozenge", "tag_block"],
    "AI-Native":             ["confidence_bar", "conversation_snippet", "llm_comparison_table",
                              "model_card", "prompt_template", "source_citation",
                              "token_budget_meter"],
    "Shopify Polaris":       ["inventory_table", "order_status_card", "product_thumbnail"],
    "Atlassian Design":      ["jira_ticket", "lozenge", "sprint_board"],
    "IBM Carbon":            ["data_grid", "heatmap_calendar", "tree_view"],
    "React / Tailwind":      ["combobox", "feature_grid", "navigation_menu",
                              "multi_select_input", "otp_input", "bento_grid",
                              "cta_section", "animated_counter"],
    "Stage-First":           ["media_stream_card", "live_aggregator", "vote_button_group",
                              "effect_overlay", "skeleton_stage_card"],
    "Enterprise & Ops":      ["api_reference", "capability_checklist", "cli_command",
                              "command_palette", "data_grid", "data_table_sortable",
                              "entity_list", "env_var_list", "file_tree",
                              "github_activity_grid", "keyboard_shortcut", "shortcut_legend",
                              "status_dashboard"],
    "OpenUI / Forms":        ["form", "form_checkbox_group", "form_date_picker", "form_input",
                              "form_radio_group", "form_select", "form_slider",
                              "form_switch_group", "modal", "follow_up_chips"],
    "Markdown & Content":    ["markdown_block", "tag_block", "text_callout", "variant_selector"],
    "Animation":             ["typewriter", "number_odometer", "typing_indicator",
                              "countdown_timer", "gradient_text", "reveal_on_scroll",
                              "word_scramble", "svg_path_draw", "toast_notification",
                              "parallax_card"],
}

# Flatten to catch anything not in a named category
_listed = {t for ts in CATEGORIES.values() for t in ts}
_unlisted = [a["type"] for a in ALL_ATOMS if a["type"] not in _listed]
if _unlisted:
    CATEGORIES["Uncategorised"] = _unlisted

# ── Demo data ──────────────────────────────────────────────────────────────────

def _days(n):
    today = date.today()
    return [{"date": (today - timedelta(days=n-i)).strftime("%Y-%m-%d"), "count": random.randint(0,8)} for i in range(n)]

DEMO = {
    # Foundations
    "heading":          {"level": 2, "text": "A2UI Atom Catalogue"},
    "subheading":       {"text": "Your AI-native UI layer for every surface"},
    "intro":            {"text": "A2UI delivers 220 atoms across web, Meet stage, Google Chat, email, and PDF."},
    "body":             {"text": "Each atom is a self-contained rendering unit. The renderer converts a JSON block into surface-appropriate HTML — no framework, no runtime dependency."},
    "closing":          {"text": "Questions? See the README or fire a playbook on the stage."},

    # Reading Experience
    "article_hero":     {"title": "A2UI Atom Catalogue", "subtitle": "220 atoms · 5 surfaces · MIT",
                         "image_url": "https://picsum.photos/900/300?random=99"},
    "article_series_nav": {"series": "A2UI Deep Dives", "parts": [
                            {"label": "Part 1: Foundations", "url": "#"},
                            {"label": "Part 2: Charts", "url": "#", "current": True},
                            {"label": "Part 3: AI-Native", "url": "#"}]},
    "post_metadata_bar": {"author": "Curtis K.", "date": "13 Jun 2026", "read_time": "8 min",
                          "tags": ["a2ui", "atoms", "ai"]},
    "reading_progress_bar": {"color": "#3b82f6"},
    "scroll_to_top":    {},
    "table_of_contents": {"items": [{"text": "Foundations", "anchor": "#foundations"},
                                     {"text": "Charts", "anchor": "#charts"},
                                     {"text": "AI-Native", "anchor": "#ai"}]},

    # Documentation
    "changelog_entry":  {"version": "v2.0.0", "date": "2026-06-13",
                          "changes": [{"type": "added", "text": "9 Tier-2 vendor atoms"},
                                      {"type": "added", "text": "CSS-tab pagination in data_grid"},
                                      {"type": "fixed", "text": "jira_ticket issue_type field conflict"}]},
    "footnote":         {"number": 1, "text": "Atom counts include all vendor-sourced and original atoms."},
    "footnote_group":   {"footnotes": [{"number": 1, "text": "MIT licensed"},
                                        {"number": 2, "text": "Apache-2.0 licensed"}]},
    "further_reading":  {"items": [{"title": "A2UI Schema Reference", "url": "#", "description": "Full field definitions"},
                                    {"title": "Playbook Creator Skill", "url": "#", "description": "Generate stage playbooks"}]},
    "glossary_term":    {"term": "Fiber", "definition": "A JSON payload delivered over WebSocket that the stage renderer converts to live UI components."},
    "release_notes":    {"version": "2.0", "date": "2026-06-13",
                          "sections": [{"title": "New Atoms", "items": ["data_grid", "jira_ticket", "sprint_board", "product_thumbnail"]},
                                        {"title": "Improvements", "items": ["CSS-tab pagination", "heatmap_calendar", "tree_view"]}]},
    "resources_list":   {"items": [{"title": "GitHub", "url": "#", "icon": "🐙"},
                                    {"title": "Docs", "url": "#", "icon": "📚"},
                                    {"title": "Playbooks", "url": "#", "icon": "🎭"}]},
    "table":            {"headers": ["Atom", "Vendor", "Surfaces"],
                          "rows": [["data_grid", "IBM Carbon", "web, stage, pdf"],
                                   ["sprint_board", "Atlassian", "web, stage, pdf"],
                                   ["product_thumbnail", "Polaris", "web, stage, email, pdf"]]},
    "tabs":             {"tabs": [{"label": "Web", "blocks": [{"type": "callout", "style": "success",
                                    "text": "Full rendering on web surface"}]},
                                   {"label": "Stage", "blocks": [{"type": "callout", "style": "info",
                                    "text": "Full rendering on meet-stage"}]}]},
    "timeline":         {"events": [{"date": "2026-01", "title": "v1.0 — 100 atoms"},
                                     {"date": "2026-04", "title": "v1.5 — OpenUI benchmark"},
                                     {"date": "2026-06", "title": "v2.0 — 220 atoms"}]},

    # Navigation
    "anchor_list":      {"items": [{"text": "Foundations", "anchor": "#foundations"},
                                    {"text": "Charts", "anchor": "#charts"},
                                    {"text": "AI-Native", "anchor": "#ai-native"}]},
    "breadcrumb":       {"items": [{"text": "A2UI", "url": "#"}, {"text": "Catalogue", "url": "#"}, {"text": "Carbon"}]},
    "faq_accordion":    {"items": [{"question": "What is an atom?", "answer": "A self-contained JSON block that renders to HTML on any A2UI surface."},
                                    {"question": "How many surfaces are there?", "answer": "Five: web, meet-stage, googlechat, email, and pdf."}]},
    "pagination":       {"current": 2, "total": 22, "base_url": "#"},
    "stepper":          {"steps": [{"label": "Schema", "status": "done"},
                                    {"label": "Renderer", "status": "done"},
                                    {"label": "Playbook", "status": "active"},
                                    {"label": "Publish", "status": "pending"}]},
    "tab_bar":          {"tabs": [{"label": "Web"}, {"label": "Stage", "active": True}, {"label": "Email"}]},

    # Content Structure
    "bullet_list":      {"items": [{"text": "220 atoms across 5 surfaces"},
                                    {"text": "MIT and Apache-2.0 licensed vendors"},
                                    {"text": "CSS-only interactivity on meet-stage"}]},
    "callout":          {"style": "info", "text": "A2UI atoms render consistently across web, stage, and email without any JavaScript runtime."},
    "caution_block":    {"text": "Never edit atom-enhanced blog posts via the admin UI — patch Firestore directly."},
    "checklist_interactive": {"items": [{"text": "Define atom schema", "completed": True},
                                          {"text": "Implement renderer", "completed": True},
                                          {"text": "Write playbook", "completed": False}]},
    "divider":          {},
    "key_takeaways":    {"items": [{"text": "All 220 atoms render in the browser with zero JS dependencies"},
                                    {"text": "CSS :checked enables tab and pagination interactions on meet-stage"},
                                    {"text": "Tier-2 vendors add e-commerce, project management, and enterprise patterns"}]},
    "key_value":        {"pairs": [{"key": "Total atoms", "value": "220"},
                                    {"key": "Surfaces", "value": "5"},
                                    {"key": "License", "value": "MIT + Apache-2.0"}]},
    "learning_objectives": {"items": ["Understand the A2UI atom taxonomy",
                                       "Fire a playbook to the meet-stage",
                                       "Extend the catalogue with new vendors"]},
    "pipeline":         {"stages": [{"label": "Prompt"}, {"label": "Fiber"}, {"label": "Render"}, {"label": "Stage"}]},
    "sidebar_note":     {"text": "The meet-stage surface supports CSS-only interactivity via :checked pseudo-classes."},
    "steps":            {"items": [{"text": "Read SKILL.md"},
                                    {"text": "Pick a runbook pattern"},
                                    {"text": "Fire the playbook"}]},
    "summary_box":      {"title": "Key Facts", "points": ["220 atoms", "5 surfaces", "MIT/Apache-2.0"]},

    # Text & Quotes
    "blockquote_with_avatar": {"quote": "A2UI is the UI protocol layer that AI-first meetings have been waiting for.",
                                "author": "Curtis K.", "role": "techmusings.krygier.fr",
                                "avatar": "https://picsum.photos/48/48?random=5"},
    "pull_stat":        {"value": "220", "label": "atoms in the catalogue"},
    "quote":            {"text": "Design systems are vocabularies. A2UI is the vocabulary for AI-native interfaces.",
                          "attribution": "A2UI Catalogue README"},

    # Containers
    "accordion_item":   {"title": "What is the meet-stage surface?", "content": "An HTML panel inside Google Meet or Microsoft Teams that receives A2UI fiber over WebSocket."},
    "collapsible_panel":{"title": "Advanced Options", "content": "Configure warn_at and critical_at thresholds for the token_budget_meter atom."},
    "css_modal":        {"trigger_text": "Open Example Modal", "title": "Modal Title",
                          "body": "This modal uses CSS :checked to open and close without JavaScript."},
    "css_slide_panel":  {"trigger_text": "Open Slide Panel", "title": "Settings",
                          "content": "Slide panels use CSS transitions on meet-stage."},
    "flip_card":        {"front": "Click to flip", "back": "CSS transform — no JS needed"},
    "hover_card":       {"trigger": "Hover over me", "content": "Appears on hover using CSS :hover"},
    "tooltip":          {"text": "atom", "tip": "A self-contained JSON block that renders to HTML"},

    # Cards
    "badge_group":      {"badges": [{"text": "web", "color": "#3b82f6"}, {"text": "meet-stage", "color": "#8b5cf6"},
                                     {"text": "email", "color": "#10b981"}, {"text": "pdf", "color": "#f59e0b"}]},
    "notification_badge": {"count": 7, "label": "New atoms"},
    "rating_stars":        {"value": 4.5, "max": 5, "label": "Developer experience"},
    "star_rating_display": {"value": 4.2, "count": 312},
    "star_rating_input":   {"name": "quality", "max_stars": 5, "initial_rating": 4,
                             "label": "Rate your experience"},
    "zoomable_image":      {"image_url": "https://picsum.photos/600/280?random=42",
                             "alt_text": "Architecture diagram", "zoom_factor": 1.6},
    "stat_card":        {"stats": [{"label": "Total Atoms", "value": "220", "delta": "+9", "is_up": True},
                                    {"label": "Surfaces", "value": "5"},
                                    {"label": "Vendors", "value": "8"}]},
    "toggle_switch":    {"label": "Dark mode", "checked": True},

    # Code & Technical
    "annotated_code":   {"language": "python", "lines": [
                            {"code": "from renderers.web_article import render"},
                            {"code": "html = render([{\"type\": \"data_grid\", ...}])", "note": "renders atom to HTML"}]},
    "api_param_table":  {"params": [{"name": "type", "type": "string", "required": True, "description": "Atom type identifier"},
                                     {"name": "title", "type": "string", "required": False, "description": "Optional heading"},
                                     {"name": "rows", "type": "array", "required": True, "description": "Row data objects"}]},
    "api_reference":    {"endpoints": [{"method": "POST", "path": "/api/playbook/fire/{name}/{slide}/{space}",
                                         "description": "Fire a playbook slide to a space"},
                                        {"method": "GET", "path": "/api/playbooks",
                                         "description": "List all registered playbooks"}]},
    "before_after":     {"before_url": "https://picsum.photos/300/180?random=10",
                          "after_url": "https://picsum.photos/300/180?random=11", "alt": "Before / After comparison"},
    "code":             {"language": "yaml", "text": "- type: data_grid\n  title: Atom Performance\n  columns:\n    - {header: Atom, key: name}\n    - {header: Renders, key: n, type: number}"},
    "code_diff":        {"before": "pagination: {page, per_page, total}", "after": "pagination: {per_page}",
                          "language": "yaml"},
    "code_snippet_pair": {"snippets": [{"label": "Python", "language": "python",
                                          "code": "html = render([{\"type\": \"callout\", \"text\": \"Hello\"}])"},
                                         {"label": "YAML", "language": "yaml",
                                          "code": "- type: callout\n  text: Hello"}]},
    "http_request_block": {"method": "POST", "url": "/api/playbook/fire/tier2_atoms/carbon/default",
                             "description": "Fire the Carbon atoms showcase slide"},
    "tabbed_code":      {"tabs": [{"label": "Python", "language": "python",
                                    "code": "from renderers.web_article import render"},
                                   {"label": "YAML", "language": "yaml",
                                    "code": "- type: heading\n  level: 2\n  text: Hello"}]},
    "terminal_block":   {"lines": [{"prompt": "$", "command": "python3 scripts/build_web_preview.py"},
                                    {"output": "Generated catalogue_web_preview.html — 220 atoms"}]},
    "file_tree":        {"nodes": [{"name": "a2ui-catalogue/", "children": [
                                      {"name": "atoms/schema.yaml"},
                                      {"name": "renderers/web_article.py"},
                                      {"name": "vendors/", "children": [
                                          {"name": "polaris/MANIFEST.md"},
                                          {"name": "atlassian/MANIFEST.md"},
                                          {"name": "carbon/MANIFEST.md"}]}]}]},

    # Design Tools
    "color_swatch_grid": {"colors": [{"name": "Indigo", "hex": "#6366f1"},
                                       {"name": "Blue", "hex": "#3b82f6"},
                                       {"name": "Green", "hex": "#10b981"},
                                       {"name": "Amber", "hex": "#f59e0b"},
                                       {"name": "Red", "hex": "#ef4444"}]},
    "css_dropdown_menu": {"trigger": "Select surface", "items": [{"label": "web"}, {"label": "meet-stage"}, {"label": "email"}]},
    "custom_checkbox_group": {"items": [{"label": "web", "checked": True}, {"label": "meet-stage", "checked": True},
                                          {"label": "email", "checked": False}]},
    "expandable_list":  {"items": [{"title": "Shopify Polaris", "content": "product_thumbnail, order_status_card, inventory_table"},
                                    {"title": "Atlassian ADS", "content": "jira_ticket, sprint_board, lozenge"},
                                    {"title": "IBM Carbon", "content": "data_grid, tree_view, heatmap_calendar"}]},
    "poll_block":       {"question": "Which surface do you use most?",
                          "options": [{"text": "web", "votes": 142}, {"text": "meet-stage", "votes": 89},
                                       {"text": "email", "votes": 34}]},
    "segmented_control": {"options": ["Day", "Week", "Month", "Year"], "selected": "Week"},

    # Charts
    "chartjs_bar":      {"title": "Atoms by Vendor", "labels": ["a2ui", "UIverse", "OpenUI", "Flowbite", "shadcn", "Polaris", "Atlassian", "Carbon"],
                          "datasets": [{"label": "Atoms", "data": [137, 31, 15, 16, 12, 3, 3, 3], "color": "#6366f1"}]},
    "chartjs_line":     {"title": "Atom Count Growth", "labels": ["v1.0", "v1.2", "v1.5", "v1.8", "v2.0"],
                          "datasets": [{"label": "Atoms", "data": [100, 145, 180, 201, 220], "color": "#3b82f6"}]},
    "chartjs_pie":      {"title": "Atoms by Surface Coverage",
                          "slices": [{"label": "web", "value": 220}, {"label": "meet-stage", "value": 148},
                                      {"label": "googlechat", "value": 80}, {"label": "email", "value": 95},
                                      {"label": "pdf", "value": 110}]},
    "cohort_retention": {"title": "Sprint Completion Cohorts",
                          "periods": ["Sprint 0", "Sprint 1", "Sprint 2", "Sprint 3"],
                          "cohorts": [{"cohort_name": "Q1 Teams", "original_size": 120, "retention_rates": [100, 88, 74, 68]},
                                       {"cohort_name": "Q2 Teams", "original_size": 145, "retention_rates": [100, 91, 79]}]},
    "donut_stat":       {"label": "Context Used", "value": 71, "max_value": 100, "unit": "%", "color": "#f59e0b"},
    "heatmap":          {"labels_x": ["W1","W2","W3","W4","W5","W6"],
                          "labels_y": ["Mon","Tue","Wed","Thu","Fri"],
                          "data": [[2,5,3,8,1,4],[4,1,7,2,9,3],[6,8,2,5,4,7],[1,3,9,4,6,2],[0,2,1,3,0,1]]},
    "mini_sparkline_set": {"series": [{"label": "Web renders", "data": [12,18,14,22,19,31]},
                                       {"label": "Stage fires", "data": [5,8,6,9,11,14]},
                                       {"label": "Errors", "data": [1,0,1,0,0,0]}]},
    "punch_card":       {"data": [[0,0,2,8,12,15,14,10,8,5,2,0,0,0,0,0,0,0,0,0,0,0,0,0]]*5 +
                                   [[0,0,0,1,2,3,4,3,2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]*2},
    "sankey_flow":      {"nodes": [{"id": "atoms", "label": "220 Atoms", "column": 0, "color": "#6366f1"},
                                    {"id": "web",   "label": "Web",       "column": 1, "color": "#3b82f6"},
                                    {"id": "stage", "label": "Stage",     "column": 1, "color": "#8b5cf6"},
                                    {"id": "email", "label": "Email",     "column": 1, "color": "#10b981"}],
                          "links": [{"source": "atoms", "target": "web",   "value": 220},
                                    {"source": "atoms", "target": "stage", "value": 148},
                                    {"source": "atoms", "target": "email", "value": 95}]},
    "sparkline":        {"data": [5, 8, 6, 12, 9, 14, 11, 18, 15, 22], "label": "Renders/day", "color": "#6366f1"},

    # Metrics & Status
    "alert_banner":     {"style": "warning", "message": "The tier2_atoms playbook requires server restart after adding new atoms."},
    "data_table_sortable": {"headers": ["Atom", "Category", "Works on"],
                             "rows": [["data_grid", "IBM Carbon", "web, stage, pdf"],
                                      ["sprint_board", "Atlassian", "web, stage, pdf"],
                                      ["product_thumbnail", "Polaris", "web, stage, email, pdf"]]},
    "metric_comparison_card": {"label": "Atom Count", "value": 220, "previous": 211, "unit": "atoms"},
    "metric_grid":      {"metrics": [{"label": "Total Atoms", "value": "220", "delta": "+9"},
                                      {"label": "Vendors", "value": "8", "delta": "+3"},
                                      {"label": "Surfaces", "value": "5"}]},
    "progress_bar":     {"value": 71, "label": "Context window usage", "color": "#f59e0b"},
    "progress_checkpoint": {"checkpoints": [{"label": "Schema", "done": True}, {"label": "Renderer", "done": True},
                                              {"label": "Playbook", "done": True}, {"label": "Publish", "done": False}]},
    "progress_circle":  {"value": 84, "label": "Sprint completion", "color": "#10b981"},
    "rating_summary_bar": {"average": 4.3, "total": 312,
                            "breakdown": [{"stars": 5, "count": 148}, {"stars": 4, "count": 98},
                                           {"stars": 3, "count": 42}, {"stars": 2, "count": 18},
                                           {"stars": 1, "count": 6}]},
    "stat_row":         {"stats": [{"label": "Atoms", "value": "220"}, {"label": "Vendors", "value": "8"},
                                    {"label": "Surfaces", "value": "5"}, {"label": "Categories", "value": "23"}]},
    "status_dashboard": {"services": [{"name": "Stage Server", "status": "operational"},
                                       {"name": "WebSocket Fiber", "status": "operational"},
                                       {"name": "Renderer", "status": "operational"},
                                       {"name": "Firestore Sync", "status": "degraded"}]},
    "uptime_timeline":  {"uptime": 99.7, "days": 30},

    # Timeline & Progress
    "milestone_tracker": {"milestones": [{"label": "v1.0 — 100 atoms", "done": True},
                                          {"label": "v1.5 — OpenUI benchmark", "done": True},
                                          {"label": "v2.0 — 220 atoms", "done": True},
                                          {"label": "v2.5 — Fluent UI", "done": False}]},
    "roadmap_card":     {"title": "A2UI Catalogue Roadmap",
                          "periods": [{"label": "Q2 ✓", "items": [{"text": "AI-native atoms", "status": "done"},
                                                                     {"text": "Tier-2 vendors", "status": "done"}]},
                                       {"label": "Q3", "items": [{"text": "Fluent UI analysis", "status": "planned"},
                                                                   {"text": "DaisyUI scan", "status": "planned"}]}]},

    # Media
    "audio_player":     {"url": "#", "title": "A2UI Architecture Walkthrough", "duration": "12:34"},
    "carousel":         {"slides": [{"url": "https://picsum.photos/600/300?random=20", "label": "Polaris Atoms"},
                                     {"url": "https://picsum.photos/600/300?random=21", "label": "Atlassian Atoms"},
                                     {"url": "https://picsum.photos/600/300?random=22", "label": "Carbon Atoms"}]},
    "image":            {"url": "https://picsum.photos/600/300?random=30", "alt": "Architecture diagram"},
    "diagram":          {"url": "https://picsum.photos/600/300?random=30", "alt": "Architecture diagram"},
    "gallery":          {"images": [{"url": "https://picsum.photos/200/150?random=31", "alt": "1"},
                                     {"url": "https://picsum.photos/200/150?random=32", "alt": "2"},
                                     {"url": "https://picsum.photos/200/150?random=33", "alt": "3"}]},
    "image_pair":       {"left": {"url": "https://picsum.photos/300/200?random=40", "alt": "Before", "caption": "v1.0"},
                          "right": {"url": "https://picsum.photos/300/200?random=41", "alt": "After", "caption": "v2.0"}},
    "lottie_animation": {"url": "#", "alt": "Loading animation"},
    "video_pair":       {"left_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                          "right_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    "youtube":          {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},

    # External Embeds
    "embed_codepen":    {"url": "https://codepen.io/pen/"},
    "embed_gist":       {"url": "https://gist.github.com/"},
    "embed_google_slides": {"url": "https://docs.google.com/presentation/d/example/embed"},
    "embed_stackblitz": {"url": "https://stackblitz.com/"},
    "embed_tweet":      {"url": "https://twitter.com/"},
    "figma_embed":      {"url": "https://www.figma.com/embed"},
    "live_demo_embed":  {"url": "http://127.0.0.1:8085"},

    # Social & People
    "author_bio_card":  {"name": "Curtis K.", "bio": "Writing about AI, Google Cloud, and building with Claude at techmusings.krygier.fr",
                          "image": "https://picsum.photos/80/80?random=50"},
    "contributor_list": {"contributors": [{"name": "Curtis K.", "role": "Curator",
                                            "avatar": "https://picsum.photos/40/40?random=51"},
                                           {"name": "AI Assistant", "role": "Co-author",
                                            "avatar": "https://picsum.photos/40/40?random=52"}]},
    "social_proof_bar": {"count": 312, "label": "developers using A2UI",
                          "avatars": ["https://picsum.photos/32/32?random=60",
                                      "https://picsum.photos/32/32?random=61",
                                      "https://picsum.photos/32/32?random=62"]},
    "testimonial_card": {"quote": "A2UI transformed how our AI assistant communicates during meetings.",
                          "author": "Product Lead", "company": "TechCorp",
                          "avatar": "https://picsum.photos/48/48?random=70"},

    # Interactive & Forms
    "choicebox_group":  {"label": "Select your primary surface", "name": "surface",
                          "items": [{"value": "web", "title": "Web", "description": "Full rendering"},
                                     {"value": "stage", "title": "Meet Stage", "description": "CSS-only interactive"},
                                     {"value": "email", "title": "Email", "description": "Static HTML"}]},
    "feedback_prompt":  {"question": "Was this atom useful?"},
    "follow_up_chips":  {"chips": ["What atoms are new?", "Show me the sprint board", "Fire the AI demo"]},
    "form":             {"fields": [{"name": "atom_type", "label": "Atom Type", "type": "text", "placeholder": "e.g. data_grid"},
                                     {"name": "surface", "label": "Surface", "type": "select",
                                      "options": [{"value": "web", "label": "Web"},
                                                   {"value": "stage", "label": "Meet Stage"}]}],
                          "submit_label": "Render Atom"},
    "form_checkbox_group": {"label": "Select surfaces", "name": "surfaces",
                             "options": [{"value": "web", "label": "Web"},
                                          {"value": "stage", "label": "Meet Stage"},
                                          {"value": "email", "label": "Email"}]},
    "form_date_picker": {"label": "Select date", "name": "date"},
    "form_input":       {"label": "Atom Type", "name": "atom_type", "type": "text", "placeholder": "e.g. data_grid"},
    "form_radio_group": {"label": "Primary surface", "name": "surface",
                          "options": [{"value": "web", "label": "Web"},
                                       {"value": "stage", "label": "Meet Stage"},
                                       {"value": "email", "label": "Email"}]},
    "form_select":      {"label": "Vendor", "name": "vendor",
                          "options": [{"value": "a2ui", "label": "a2ui original"},
                                       {"value": "polaris", "label": "Shopify Polaris"},
                                       {"value": "atlassian", "label": "Atlassian ADS"},
                                       {"value": "carbon", "label": "IBM Carbon"}]},
    "form_slider":      {"label": "per_page rows", "name": "per_page", "min": 2, "max": 50, "value": 10},
    "form_switch_group": {"label": "Enable surfaces", "name": "surfaces",
                           "options": [{"value": "web", "label": "Web", "checked": True},
                                        {"value": "stage", "label": "Meet Stage", "checked": True},
                                        {"value": "email", "label": "Email", "checked": False}]},
    "modal":            {"trigger_text": "Preview Modal", "title": "Atom Preview",
                          "body": "This modal demonstrates CSS-only open/close on meet-stage."},
    "variant_selector": {"name": "surface", "label": "Choose rendering surface",
                          "items": [{"value": "web", "title": "Web", "description": "Full CSS + interactive"},
                                     {"value": "stage", "title": "Meet Stage", "description": "CSS :checked interactivity"},
                                     {"value": "email", "title": "Email", "description": "Static HTML, no interactivity"}]},

    # Notifications
    "call_mood_board":  {"sentiment_index": 82, "mood": "Engaged",
                          "themes": [{"theme": "Architecture", "score": 90}, {"theme": "Timeline", "score": 65}]},
    "inline_alert":     {"type": "info", "message": "This atom embeds inline in content flow without disrupting layout.",
                          "detail": "Distinct from alert_banner (full-width) and toast_notification (overlay)."},
    "notification_stack": {"title": "Recent Activity", "items": [
                             {"icon": "⚡", "title": "9 new atoms added", "body": "Polaris, Atlassian, Carbon", "time": "2m ago", "unread": True},
                             {"icon": "🔄", "title": "Server restarted", "body": "tier2_atoms playbook registered", "time": "5m ago"}]},
    "toast_notification": {"message": "Atom rendered successfully", "style": "success"},

    # Tags
    "lozenge":          {"items": [{"text": "Active", "appearance": "success"},
                                    {"text": "In Progress", "appearance": "inprogress"},
                                    {"text": "Blocked", "appearance": "removed"},
                                    {"text": "New", "appearance": "new"}]},
    "tag_block":        {"tags": ["atoms", "a2ui", "meet-stage", "AI-native", "MIT", "v2.0"]},

    # AI-Native
    "confidence_bar":   {"items": [{"label": "Answer Relevance", "value": 94},
                                    {"label": "Source Faithfulness", "value": 88},
                                    {"label": "Context Recall", "value": 71},
                                    {"label": "Hallucination Risk", "value": 12}]},
    "conversation_snippet": {"user_label": "You", "user": "How many atoms are in the catalogue?",
                               "ai_label": "Assistant", "response": "There are 220 atoms across 5 surfaces — web, meet-stage, googlechat, email, and pdf. The latest additions are 9 Tier-2 vendor atoms from Shopify Polaris, Atlassian ADS, and IBM Carbon."},
    "llm_comparison_table": {"prompt": "Summarise A2UI in one sentence.",
                              "models": [{"name": "Claude Sonnet 4.6",
                                          "output": "A2UI is a 220-atom catalogue that renders AI-generated UI consistently across web, meeting stages, email, and PDF using a WebSocket fiber delivery model.",
                                          "latency_ms": 820, "cost_usd": 0.0012},
                                          {"name": "GPT-4o",
                                          "output": "A2UI provides a surface-agnostic JSON atom vocabulary that AI systems use to render structured UI in real-time during meetings and across digital channels.",
                                          "latency_ms": 1140, "cost_usd": 0.0018}]},
    "model_card":       {"name": "Claude Sonnet 4.6", "provider": "Anthropic",
                          "context_window": "200 k tokens", "pricing": "$3 / M tokens in · $15 / M out",
                          "capabilities": ["tool use", "vision", "streaming", "extended thinking"],
                          "accent": "#7c3aed"},
    "prompt_template":  {"label": "RAG Answer Synthesis",
                          "template": "You are a {role} assistant. Answer using ONLY the provided sources.\n\nQuestion: {question}\n\nSources:\n{sources}\n\nCite sources using [N] notation.",
                          "accent": "#818cf8"},
    "source_citation":  {"heading": "Sources", "sources": [
                           {"number": 1, "title": "A2UI Atom Schema Reference", "url": "#",
                            "excerpt": "220 atoms across 5 surfaces. Each atom is defined by type, fields, surfaces, and source attribution."},
                           {"number": 2, "title": "vendors/LANDSCAPE.md", "url": "#",
                            "excerpt": "Tier-1 and Tier-2 library analysis with gap atoms and prioritised adaptation roadmap."}]},
    "token_budget_meter": {"used": 142800, "total": 200000, "model": "claude-sonnet-4-6"},

    # Polaris
    "product_thumbnail": {"title": "AirMax Pro Runners", "vendor": "NovaSport",
                           "sku": "NS-AMP-BLK-42", "price": "£129.00", "compare_at_price": "£159.00",
                           "status": "active", "tags": ["footwear", "running", "sale"]},
    "order_status_card": {"order_number": "#2847", "date": "13 Jun 2026", "status": "fulfilled",
                           "customer": "James Okafor",
                           "items": [{"title": "AirMax Pro Runners", "qty": 1, "price": "£129.00"},
                                      {"title": "Merino Crew Neck", "qty": 2, "price": "£79.00"}],
                           "total": "£287.00"},
    "inventory_table":  {"title": "Manchester FC",
                          "items": [{"sku": "NS-001", "product": "AirMax Pro / Black / EU42",
                                      "available": 4, "committed": 12, "location": "B-14", "threshold": 5},
                                     {"sku": "NS-002", "product": "AirMax Pro / White / EU42",
                                      "available": 18, "committed": 3, "location": "B-15"},
                                     {"sku": "WC-001", "product": "Merino Crew / Grey / M",
                                      "available": 2, "committed": 6, "location": "C-07", "threshold": 5}]},

    # Atlassian
    "jira_ticket":      {"key": "A2UI-312", "issue_type": "story",
                          "summary": "Implement Tier-2 vendor atoms (Polaris, Atlassian, Carbon)",
                          "status": "Done", "priority": "high", "assignee": "Curtis K.",
                          "labels": ["catalogue", "vendor", "v2.0"]},
    "sprint_board":     {"sprint_name": "Sprint 8 — Vendor Expansion",
                          "columns": [
                              {"name": "To Do", "items": [{"key": "A2UI-315", "summary": "Fluent UI analysis", "type": "task", "priority": "medium"}]},
                              {"name": "In Progress", "items": [{"key": "A2UI-316", "summary": "DaisyUI scan", "type": "task", "priority": "low"}]},
                              {"name": "Done", "items": [{"key": "A2UI-312", "summary": "Tier-2 vendor atoms", "type": "story", "priority": "high"},
                                                          {"key": "A2UI-309", "summary": "ms-teams cleanup", "type": "bug", "priority": "high"}]}]},

    # Carbon
    "data_grid":        {"title": "Atom Render Performance",
                          "selectable": True,
                          "columns": [{"header": "Atom", "key": "atom"},
                                       {"header": "Vendor", "key": "vendor", "type": "tag"},
                                       {"header": "Renders", "key": "n", "type": "number", "sortable": True},
                                       {"header": "Avg ms", "key": "ms", "type": "number", "sortable": True},
                                       {"header": "Status", "key": "status", "type": "status"}],
                          "rows": [{"atom": "sprint_board",       "vendor": "Atlassian", "n": 1204, "ms": 2.1, "status": "active"},
                                    {"atom": "heatmap_calendar",  "vendor": "Carbon",    "n": 847,  "ms": 4.8, "status": "active"},
                                    {"atom": "data_grid",         "vendor": "Carbon",    "n": 612,  "ms": 1.9, "status": "active"},
                                    {"atom": "product_thumbnail", "vendor": "Polaris",   "n": 389,  "ms": 1.2, "status": "active"},
                                    {"atom": "model_card",        "vendor": "a2ui",      "n": 201,  "ms": 0.9, "status": "active"},
                                    {"atom": "confidence_bar",    "vendor": "a2ui",      "n": 184,  "ms": 0.8, "status": "inactive"}],
                          "pagination": {"per_page": 3}},
    "tree_view":        {"title": "Vendor Hierarchy", "nodes": [
                           {"label": "a2ui-catalogue", "icon": "⚡", "expanded": True, "meta": "137 atoms",
                            "children": [{"label": "AI-native", "meta": "7"}, {"label": "Geist-inspired", "meta": "2"}]},
                           {"label": "Tier-2 Vendors", "icon": "▲", "expanded": True,
                            "children": [{"label": "Shopify Polaris", "meta": "3 · MIT"},
                                          {"label": "Atlassian ADS", "meta": "3 · Apache-2.0"},
                                          {"label": "IBM Carbon", "meta": "3 · Apache-2.0"}]}]},
    "heatmap_calendar": {"title": "Catalogue Deployment Activity", "data": _days(60), "months": 2, "unit": "deploys"},

    # React / Tailwind ecosystem (second wave)
    "multi_select_input": {"label": "Surfaces", "name": "surfaces", "placeholder": "Add surface…",
                            "selected": ["web", "meet-stage"],
                            "options": [{"value": "web",        "label": "web"},
                                        {"value": "meet-stage", "label": "meet-stage"},
                                        {"value": "googlechat", "label": "googlechat"},
                                        {"value": "email",      "label": "email"},
                                        {"value": "pdf",        "label": "pdf"}]},
    "otp_input":        {"label": "Verification code", "length": 6, "value": "4291"},
    "bento_grid":       {"heading": "A2UI in numbers",
                          "columns": 3,
                          "tiles": [
                            {"icon": "⚡", "title": "223 atoms", "subtitle": "Across 26 categories and 9 vendor sources",
                             "span": 2, "color": "#1a73e8"},
                            {"icon": "🌐", "title": "5 surfaces", "subtitle": "web · stage · chat · email · pdf",
                             "color": "#34a853"},
                            {"icon": "🤖", "title": "7 AI-native atoms", "subtitle": "model_card, confidence_bar, prompt_template…",
                             "color": "#9c27b0"},
                            {"icon": "🏪", "title": "MIT licensed", "subtitle": "All atoms open-source",
                             "color": "#fbbc04"},
                            {"icon": "📦", "title": "Zero runtime", "subtitle": "Pure Python → static HTML",
                             "color": "#ea4335"}]},
    "cta_section":      {"heading": "Start building with A2UI",
                          "body": "220 typed atoms, one Python renderer, every surface covered. Open source, MIT licensed.",
                          "primary_cta":   {"label": "Browse the catalogue →", "url": "#"},
                          "secondary_cta": {"label": "View on GitHub",          "url": "#"},
                          "background": "#1a73e8"},
    "animated_counter": {"duration": 2.5,
                          "counters": [
                            {"value": 223,  "label": "Atoms",    "color": "#1a73e8"},
                            {"value": 5,    "label": "Surfaces", "color": "#34a853"},
                            {"value": 9,    "label": "Vendors",  "color": "#9c27b0"},
                            {"value": 100,  "label": "MIT",      "suffix": "%", "color": "#fbbc04"}]},

    # React / Tailwind ecosystem (wave 1)
    "combobox":         {"label": "UI Framework", "name": "framework", "placeholder": "Search frameworks…",
                          "selected": "react",
                          "options": [{"value": "react",   "label": "React"},
                                      {"value": "vue",     "label": "Vue"},
                                      {"value": "svelte",  "label": "Svelte"},
                                      {"value": "angular", "label": "Angular"},
                                      {"value": "solid",   "label": "SolidJS"},
                                      {"value": "qwik",    "label": "Qwik"},
                                      {"value": "lit",     "label": "Lit"},
                                      {"value": "htmx",    "label": "HTMX"}]},
    "feature_grid":     {"heading": "Why A2UI atoms?",
                          "description": "A single vocabulary that renders correctly on every surface — no per-surface templating required.",
                          "columns": 3,
                          "features": [
                            {"icon": "⚡", "title": "Surface-agnostic",
                             "description": "One atom definition renders to web, Meet stage, Google Chat, email, and PDF without branching logic.", "badge": "core"},
                            {"icon": "🧩", "title": "Composable",
                             "description": "Atoms nest freely. A stat_row inside a callout inside a form is just an array of blocks."},
                            {"icon": "🤖", "title": "AI-native",
                             "description": "Seven atoms — model_card, confidence_bar, token_budget_meter — exist specifically because AI systems need structured UI."},
                            {"icon": "🏪", "title": "Vendor-sourced",
                             "description": "Polaris, Atlassian ADS, IBM Carbon, shadcn, and ExtendLabs components are first-class catalogue citizens.", "badge": "MIT"},
                            {"icon": "🔐", "title": "No runtime",
                             "description": "Pure HTML output. No React, no framework dependency, no hydration step — just a Python renderer."},
                            {"icon": "📐", "title": "Schema-first",
                             "description": "Every atom has a typed schema. An AI can generate valid blocks without hallucinating field names."}]},
    "navigation_menu":  {"brand": "techmusings", "brand_url": "#",
                          "items": [
                            {"label": "Atoms", "url": "#", "children": [
                              {"label": "Foundations",    "url": "#", "description": "body, heading, intro, closing"},
                              {"label": "Charts & Data",  "url": "#", "description": "chartjs_bar, heatmap, sankey_flow"},
                              {"label": "AI-Native",      "url": "#", "description": "model_card, confidence_bar, prompt_template"},
                              {"label": "Enterprise",     "url": "#", "description": "data_grid, sprint_board, jira_ticket"}]},
                            {"label": "Surfaces", "url": "#"},
                            {"label": "Vendors",  "url": "#"},
                            {"label": "Blog",     "url": "#"}],
                          "cta": {"label": "Open catalogue →", "url": "#"}},

    # Enterprise
    "capability_checklist": {"title": "Surface Compatibility", "items": [
                               {"text": "Web rendering", "supported": True},
                               {"text": "Meet Stage rendering", "supported": True},
                               {"text": "Google Chat", "supported": True},
                               {"text": "Email", "supported": True},
                               {"text": "PDF export", "supported": True}]},
    "cli_command":      {"command": "python3 scripts/build_web_preview.py",
                          "description": "Generates the self-contained atom catalogue preview HTML"},
    "command_palette":  {"items": [{"label": "Fire playbook", "shortcut": "⌘ P"},
                                    {"label": "Render atom", "shortcut": "⌘ R"},
                                    {"label": "Open catalogue", "shortcut": "⌘ K"}]},
    "entity_list":      {"items": [{"name": "Shopify Polaris", "subtitle": "3 atoms · MIT",
                                     "status": "active", "icon": "🛍"},
                                    {"name": "Atlassian ADS", "subtitle": "3 atoms · Apache-2.0",
                                     "status": "active", "icon": "🟦"},
                                    {"name": "IBM Carbon", "subtitle": "3 atoms · Apache-2.0",
                                     "status": "active", "icon": "🔷"}]},
    "env_var_list":     {"vars": [{"name": "STAGE_API_KEY", "description": "Bearer token for stage API"},
                                   {"name": "GEMINI_PROJECT", "description": "GCP project ID"},
                                   {"name": "CONCIERGE_API_URL", "description": "Stage server URL (default: http://127.0.0.1:8085)"}]},
    "github_activity_grid": {"title": "A2UI Catalogue Activity", "username": "curtiskrygier",
                              "total_contributions": 342, "streak_days": 18,
                              "activity": [random.randint(0,4) for _ in range(52*7)]},
    "keyboard_shortcut": {"keys": ["⌘", "Shift", "P"]},
    "shortcut_legend":  {"title": "Stage Shortcuts",
                          "items": [{"keys": ["⌘", "P"], "action": "Fire playbook"},
                                     {"keys": ["⌘", "K"], "action": "Open catalogue"},
                                     {"keys": ["→"], "action": "Next slide"}]},

    # Markdown & Content
    "markdown_block":   {"content": "## A2UI v2.0\n\nNew in this release:\n- **9 new atoms** from Tier-2 vendors\n- **CSS-tab pagination** in `data_grid`\n- `jira_ticket`, `sprint_board`, `lozenge` from Atlassian\n\n```yaml\n- type: data_grid\n  title: My Grid\n  pagination:\n    per_page: 5\n```"},
    "text_callout":     {"variant": "tip", "title": "Pro Tip", "description": "Use data_grid with pagination: {per_page: 5} to get CSS-tab page switching on the meet-stage."},

    # Misc that might be in schema
    "choicebox_group":  {"label": "Surface", "name": "surface",
                          "items": [{"value": "web", "title": "Web", "description": "Full rendering"},
                                     {"value": "stage", "title": "Stage", "description": "CSS interactive"},
                                     {"value": "email", "title": "Email", "description": "Static"}]},
    "abbr_tooltip":     {"abbreviations": [{"abbr": "A2UI", "title": "Atom-to-UI — the JSON atom rendering system"},
                                             {"abbr": "RAG", "title": "Retrieval-Augmented Generation"}],
                          "text": "A2UI uses RAG-grounded atoms to deliver live UI to the meet-stage."},
    "copy_to_clipboard": {"text": "python3 scripts/build_web_preview.py", "label": "Copy command"},
    "search_result_card": {"query": "data_grid atom", "results": [
                             {"title": "IBM Carbon: data_grid", "url": "#", "excerpt": "Enterprise data grid with CSS-tab pagination, typed columns, and row selection."},
                             {"title": "data_table_sortable", "url": "#", "excerpt": "Simpler sortable table — use data_grid for pagination and row selection."}]},
    "notification_badge": {"count": 9, "label": "New atoms"},
    "prompt_chain":     {"steps": [{"label": "Extract intent"}, {"label": "Retrieve context"}, {"label": "Synthesise answer"}, {"label": "Render atoms"}]},
    "before_after_code": {"before": "per_page, total, page", "after": "per_page", "label": "Simplified pagination field"},
    "diff_viewer":      {"hunks": [{"old": "page: 1\nper_page: 10\ntotal: 220", "new": "per_page: 10"}]},

    # Stage-first atoms
    "media_stream_card":    {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                              "title": "A2UI Meet Stage Demo", "height": "320px"},
    "live_aggregator":      {"title": "Which framework?",
                              "items": [{"label": "React",   "value": 42},
                                        {"label": "Vue",     "value": 28},
                                        {"label": "Svelte",  "value": 19},
                                        {"label": "SolidJS", "value": 11}]},
    "vote_button_group":    {"title": "Pick your stack", "style": "neon",
                              "options": [{"label": "React",   "value": "react"},
                                          {"label": "Vue",     "value": "vue", "selected": True},
                                          {"label": "Svelte",  "value": "svelte"},
                                          {"label": "SolidJS", "value": "solid"}]},
    "effect_overlay":       {"trigger": "trophy", "message": "Consensus reached!",
                              "status": "resolved"},
    "skeleton_stage_card":  {"variant": "card", "count": 2, "lines": 3},
    # Animation atoms
    "typewriter":           {"text": "The catalogue is the substrate.", "speed": "normal", "cursor": True},
    "number_odometer":      {"value": "2026", "label": "Year of the agent", "accent": "#4f46e5"},
    "typing_indicator":     {"name": "Agent", "variant": "dark"},
    "countdown_timer":      {"hours": 0, "minutes": 4, "seconds": 59, "label": "Until next deploy", "variant": "dark"},
    "gradient_text":        {"text": "Build something beautiful.", "from": "#4f46e5", "to": "#06b6d4", "size": "2rem"},
    "reveal_on_scroll":     {"title": "Revealed on scroll", "body": "Content fades in as you scroll into view using IntersectionObserver.", "direction": "up", "accent": "#4f46e5"},
    "word_scramble":        {"text": "A2UI", "duration": 2.0, "color": "#0f172a", "scramble_color": "#4f46e5"},
    "svg_path_draw":        {"shape": "check", "color": "#22c55e", "duration": 1.5, "label": "All atoms rendered"},
    "toast_notification":   {"title": "Atoms published", "message": "233 atoms synced to Firestore.", "variant": "success"},
    "parallax_card":        {"title": "Parallax Card", "body": "Hover to see 3D tilt.", "badge": "Animation", "accent": "#4f46e5"},
}

# ── ExtendLabs stage component facsimiles ──────────────────────────────────────

_EXT_CSS = """
<style>
@keyframes ext-shimmer{0%{background-position:200% center}100%{background-position:-200% center}}
@keyframes ext-glow{0%,100%{box-shadow:0 0 0 2px rgba(0,242,255,.3),0 0 14px rgba(0,242,255,.2)}50%{box-shadow:0 0 0 3px rgba(0,242,255,.7),0 0 28px rgba(0,242,255,.45)}}
@keyframes ext-perimeter{0%{background-position:100% 0%}25%{background-position:100% 100%}50%{background-position:0% 100%}75%{background-position:0% 0%}100%{background-position:100% 0%}}
@keyframes ext-bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes ext-spin{to{transform:rotate(360deg)}}
.ext-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;white-space:nowrap;border-radius:8px;font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase;letter-spacing:.04em;border:none;cursor:pointer;font-size:13px;padding:8px 18px;position:relative;overflow:hidden;box-sizing:border-box;transition:all .2s cubic-bezier(.4,0,.2,1);}
.ext-btn-default{background:#00f2ff;color:#0a0f1e;box-shadow:0 0 12px rgba(0,242,255,.25);}
.ext-btn-outline{background:transparent;color:#00f2ff;border:1px solid rgba(0,242,255,.45);}
.ext-btn-ghost{background:transparent;color:rgba(255,255,255,.65);border:1px solid transparent;}
.ext-btn-ringHover{background:#00f2ff;color:#0a0f1e;box-shadow:0 0 0 2px #0a0f1e,0 0 0 4px rgba(0,242,255,.8);}
.ext-btn-glowingRing{background:#00f2ff;color:#0a0f1e;animation:ext-glow 2s ease-in-out infinite;}
.ext-btn-shimmer{background:linear-gradient(90deg,#00f2ff 0%,rgba(0,242,255,.35) 40%,rgba(0,255,136,.6) 60%,#00f2ff 100%);background-size:200% 100%;color:#0a0f1e;animation:ext-shimmer 2.4s linear infinite;}
.ext-btn-perimeterShimmer{background:rgba(0,242,255,.12);color:#00f2ff;border:1px solid rgba(0,242,255,.3);}
.ext-btn-perimeterShimmer::before{content:'';position:absolute;inset:-1px;border-radius:inherit;background:linear-gradient(90deg,transparent,rgba(0,242,255,.9),transparent);background-size:200% 100%;animation:ext-perimeter 1.6s linear infinite;pointer-events:none;}
.ext-btn-bouncing{background:#00f2ff;color:#0a0f1e;animation:ext-bounce 1.1s ease-in-out infinite;}
.ext-badge{display:inline-flex;align-items:center;border-radius:9999px;font-size:11px;font-weight:600;padding:2px 10px;border:1px solid transparent;}
.ext-badge-default{background:rgba(0,242,255,.15);color:#00f2ff;border-color:rgba(0,242,255,.3);}
.ext-badge-secondary{background:rgba(255,255,255,.08);color:rgba(255,255,255,.7);border-color:rgba(255,255,255,.15);}
.ext-badge-destructive{background:rgba(239,68,68,.15);color:#f87171;border-color:rgba(239,68,68,.3);}
.ext-badge-outline{background:transparent;color:rgba(255,255,255,.65);border-color:rgba(255,255,255,.3);}
</style>
"""

def _ext_row(*items: str) -> str:
    cells = "".join(f'<div style="display:flex;flex-direction:column;gap:8px;align-items:flex-start;">{i}</div>' for i in items)
    return f'<div style="display:flex;gap:24px;flex-wrap:wrap;align-items:flex-end;">{cells}</div>'

def _ext_label(text: str) -> str:
    return f'<div style="font-size:10px;color:#64748b;font-family:monospace;margin-bottom:4px;">{text}</div>'

def build_extendlabs_section() -> str:
    bg = "background:#0f1117;border-radius:10px;padding:20px;"
    card_style = f"background:#1e2433;border:1px solid #2d3748;border-radius:8px;margin-bottom:16px;overflow:hidden;"
    hdr_style  = "padding:10px 14px;background:#161b27;border-bottom:1px solid #2d3748;display:flex;align-items:center;gap:10px;flex-wrap:wrap;"
    tag_style  = "font-size:12px;font-weight:700;color:#00f2ff;background:rgba(0,242,255,.1);padding:2px 8px;border-radius:4px;font-family:monospace;"
    desc_style = "font-size:12px;color:#64748b;flex:1;"
    pill_stage = '<span style="font-size:10px;padding:1px 7px;border-radius:20px;background:#ede9fe;color:#6d28d9;white-space:nowrap;">meet-stage</span>'
    pill_both  = pill_stage + ' <span style="font-size:10px;padding:1px 7px;border-radius:20px;background:#dbeafe;color:#1d4ed8;white-space:nowrap;">web</span>'

    # Individual component facsimiles
    components = []

    # ext-button
    btns = _ext_row(
        _ext_label("default")          + f'<button class="ext-btn ext-btn-default">Fire Slide</button>',
        _ext_label("outline")          + f'<button class="ext-btn ext-btn-outline">Outline</button>',
        _ext_label("ghost")            + f'<button class="ext-btn ext-btn-ghost">Ghost</button>',
        _ext_label("ringHover")        + f'<button class="ext-btn ext-btn-ringHover">Ring Hover</button>',
        _ext_label("glowingRing")      + f'<button class="ext-btn ext-btn-glowingRing">Glow Ring</button>',
        _ext_label("shimmer")          + f'<button class="ext-btn ext-btn-shimmer">Shimmer</button>',
        _ext_label("perimeterShimmer") + f'<button class="ext-btn ext-btn-perimeterShimmer"><span>Perimeter</span></button>',
        _ext_label("bouncing")         + f'<button class="ext-btn ext-btn-bouncing">Bounce</button>',
    )
    components.append(("ext-button", "Animated button — 8 variants, 4 sizes, A2UI action protocol", pill_stage,
        f'<div style="{bg}">{_EXT_CSS}{btns}</div>'))

    # ext-badge
    badges = _ext_row(
        _ext_label("default")     + '<span class="ext-badge ext-badge-default">Active</span>',
        _ext_label("secondary")   + '<span class="ext-badge ext-badge-secondary">Draft</span>',
        _ext_label("destructive") + '<span class="ext-badge ext-badge-destructive">Error</span>',
        _ext_label("outline")     + '<span class="ext-badge ext-badge-outline">Archived</span>',
    )
    components.append(("ext-badge", "Inline status badge — 4 variants, hex color override", pill_both,
        f'<div style="{bg}">{badges}</div>'))

    # ext-alert
    alert_css = """<style>
.ext-alert{display:flex;gap:12px;align-items:flex-start;border-radius:8px;padding:14px 16px;border:1px solid;}
.ext-alert-default{background:rgba(0,242,255,.07);border-color:rgba(0,242,255,.25);color:#e2e8f0;}
.ext-alert-destructive{background:rgba(239,68,68,.07);border-color:rgba(239,68,68,.3);color:#fca5a5;}
.ext-alert-icon{font-size:16px;flex-shrink:0;margin-top:1px;}
.ext-alert-title{font-weight:700;font-size:13px;margin-bottom:3px;}
.ext-alert-desc{font-size:12px;opacity:.75;}
</style>"""
    alerts = f"""
<div style="display:flex;flex-direction:column;gap:10px;">
  <div class="ext-alert ext-alert-default"><div class="ext-alert-icon">ℹ</div><div><div class="ext-alert-title">Stage connected</div><div class="ext-alert-desc">WebSocket fiber ready — fire a playbook to begin.</div></div></div>
  <div class="ext-alert ext-alert-destructive"><div class="ext-alert-icon">✕</div><div><div class="ext-alert-title">Renderer error</div><div class="ext-alert-desc">No renderer registered for atom type 'unknown'.</div></div></div>
</div>"""
    components.append(("ext-alert", "Status alert — default · destructive variants; collapses Alert/AlertTitle/AlertDescription", pill_both,
        f'<div style="{bg}">{alert_css}{alerts}</div>'))

    # ext-card
    card_css = """<style>
.ext-card{background:#1a2035;border:1px solid #2d3748;border-radius:10px;overflow:hidden;max-width:340px;}
.ext-card-header{padding:16px 16px 8px;border-bottom:1px solid #2d3748;}
.ext-card-title{font-weight:700;font-size:15px;color:#f1f5f9;}
.ext-card-description{font-size:12px;color:#64748b;margin-top:3px;}
.ext-card-content{padding:16px;font-size:13px;color:#cbd5e1;line-height:1.55;}
.ext-card-footer{padding:10px 16px;border-top:1px solid #2d3748;font-size:11px;color:#475569;}
</style>"""
    card_html = """<div class="ext-card">
  <div class="ext-card-header"><div class="ext-card-title">Atom Render Performance</div><div class="ext-card-description">Last 30 days — 220 atoms tracked</div></div>
  <div class="ext-card-content">Average render time: <strong style="color:#00f2ff;">1.8 ms</strong>. Peak load: 1,204 renders/hr (sprint_board). Zero renderer errors this sprint.</div>
  <div class="ext-card-footer">Updated 2 min ago · Source: stage metrics</div>
</div>"""
    components.append(("ext-card", "Content card — title, description, content, footer; collapses Card/CardHeader/CardContent/CardFooter", pill_both,
        f'<div style="{bg}">{card_css}{card_html}</div>'))

    # ext-checkbox
    cb_css = """<style>
.ext-cb-wrap{display:flex;align-items:center;gap:10px;cursor:pointer;font-size:13px;color:#cbd5e1;}
.ext-cb{width:16px;height:16px;border-radius:4px;border:2px solid #4b5563;background:transparent;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.ext-cb.checked{background:#00f2ff;border-color:#00f2ff;}
.ext-cb.checked::after{content:'✓';font-size:10px;font-weight:900;color:#0a0f1e;}
.ext-cb-disabled{opacity:.4;cursor:not-allowed;}
</style>"""
    cb_html = """<div style="display:flex;flex-direction:column;gap:10px;">
  <label class="ext-cb-wrap"><div class="ext-cb checked"></div>Enable web surface rendering</label>
  <label class="ext-cb-wrap"><div class="ext-cb checked"></div>Enable meet-stage rendering</label>
  <label class="ext-cb-wrap"><div class="ext-cb"></div>Enable email rendering</label>
  <label class="ext-cb-wrap ext-cb-disabled"><div class="ext-cb"></div>Enable PDF (disabled)</label>
</div>"""
    components.append(("ext-checkbox", "Accessible checkbox — checked/disabled states, A2UI action on change", pill_both,
        f'<div style="{bg}">{cb_css}{cb_html}</div>'))

    # ext-input
    inp_css = """<style>
.ext-inp-wrap{display:flex;flex-direction:column;gap:4px;min-width:200px;}
.ext-inp-label{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;}
.ext-inp{background:#0f1117;border:1px solid #334155;border-radius:6px;padding:8px 12px;font-size:13px;color:#f1f5f9;font-family:inherit;outline:none;width:100%;}
.ext-inp-filled{background:#1e2a3a;border-color:transparent;border-bottom:2px solid #00f2ff;}
.ext-inp-flushed{background:transparent;border:none;border-bottom:1px solid #334155;border-radius:0;padding-left:0;padding-right:0;}
.ext-inp-error{border-color:#ef4444;}
.ext-inp-errmsg{font-size:11px;color:#f87171;margin-top:2px;}
</style>"""
    inp_html = """<div style="display:flex;gap:20px;flex-wrap:wrap;">
  <div class="ext-inp-wrap"><div class="ext-inp-label">Default</div><input class="ext-inp" placeholder="Atom type…" value="data_grid"></div>
  <div class="ext-inp-wrap"><div class="ext-inp-label">Filled</div><input class="ext-inp ext-inp-filled" placeholder="Search atoms…"></div>
  <div class="ext-inp-wrap"><div class="ext-inp-label">Flushed</div><input class="ext-inp ext-inp-flushed" placeholder="Enter value…"></div>
  <div class="ext-inp-wrap"><div class="ext-inp-label">Error</div><input class="ext-inp ext-inp-error" value="unknown_atom"><div class="ext-inp-errmsg">No renderer registered for this type.</div></div>
</div>"""
    components.append(("ext-input", "Text input — default/filled/flushed variants; A2UI action on Enter/blur", pill_both,
        f'<div style="{bg}">{inp_css}{inp_html}</div>'))

    # ext-switch
    sw_css = """<style>
.ext-sw-wrap{display:flex;align-items:center;gap:10px;font-size:13px;color:#cbd5e1;}
.ext-sw-track{width:36px;height:20px;border-radius:10px;background:#1e2a3a;border:2px solid #334155;position:relative;cursor:pointer;transition:background .2s;}
.ext-sw-track.on{background:#00f2ff;border-color:#00f2ff;}
.ext-sw-thumb{width:12px;height:12px;border-radius:50%;background:#64748b;position:absolute;top:2px;left:2px;transition:all .2s;}
.ext-sw-track.on .ext-sw-thumb{background:#0a0f1e;left:18px;}
.ext-sw-disabled{opacity:.4;}
</style>"""
    sw_html = """<div style="display:flex;flex-direction:column;gap:12px;">
  <div class="ext-sw-wrap"><div class="ext-sw-track on"><div class="ext-sw-thumb"></div></div>Web surface rendering</div>
  <div class="ext-sw-wrap"><div class="ext-sw-track on"><div class="ext-sw-thumb"></div></div>Meet-stage rendering</div>
  <div class="ext-sw-wrap"><div class="ext-sw-track"><div class="ext-sw-thumb"></div></div>Email rendering</div>
  <div class="ext-sw-wrap ext-sw-disabled"><div class="ext-sw-track"><div class="ext-sw-thumb"></div></div>PDF export (disabled)</div>
</div>"""
    components.append(("ext-switch", "Toggle switch — checked/disabled, A2UI action on toggle", pill_both,
        f'<div style="{bg}">{sw_css}{sw_html}</div>'))

    # ext-textarea
    ta_css = """<style>
.ext-ta-wrap{display:flex;flex-direction:column;gap:4px;max-width:400px;}
.ext-ta-label{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;}
.ext-ta{background:#0f1117;border:1px solid #334155;border-radius:6px;padding:10px 12px;font-size:13px;color:#f1f5f9;font-family:inherit;resize:vertical;min-height:80px;width:100%;}
.ext-ta-count{font-size:10px;color:#475569;text-align:right;}
</style>"""
    ta_html = """<div class="ext-ta-wrap">
  <div class="ext-ta-label">Playbook note</div>
  <textarea class="ext-ta" rows="3">Summarise A2UI in one sentence — use the token_budget_meter atom to track context usage.</textarea>
  <div class="ext-ta-count">86 / 500</div>
</div>"""
    components.append(("ext-textarea", "Multi-line text input — maxLength, A2UI action on blur / Ctrl+Enter", pill_both,
        f'<div style="{bg}">{ta_css}{ta_html}</div>'))

    # ext-table
    tbl_css = """<style>
.ext-tbl{width:100%;border-collapse:collapse;font-size:13px;}
.ext-tbl th{text-align:left;padding:8px 12px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#64748b;border-bottom:1px solid #2d3748;}
.ext-tbl td{padding:10px 12px;color:#cbd5e1;border-bottom:1px solid #1e2433;}
.ext-tbl tr:last-child td{border-bottom:none;}
.ext-tbl tr:hover td{background:rgba(0,242,255,.04);}
</style>"""
    tbl_html = """<table class="ext-tbl">
  <thead><tr><th>Component</th><th>Variant</th><th>Surface</th></tr></thead>
  <tbody>
    <tr><td>ext-button</td><td>shimmer · glowingRing · bouncing</td><td>stage</td></tr>
    <tr><td>ext-badge</td><td>default · secondary · destructive · outline</td><td>both</td></tr>
    <tr><td>ext-alert</td><td>default · destructive</td><td>both</td></tr>
    <tr><td>ext-card</td><td>—</td><td>both</td></tr>
    <tr><td>ext-input</td><td>default · filled · flushed</td><td>both</td></tr>
  </tbody>
</table>"""
    components.append(("ext-table", "Data table — headers/rows as JSON strings; stage-only for complex layouts", pill_stage,
        f'<div style="{bg}">{tbl_css}{tbl_html}</div>'))

    # ext-tabs
    tabs_css = """<style>
.ext-tabs-list{display:flex;gap:2px;background:#0f1117;border-radius:8px;padding:4px;margin-bottom:16px;}
.ext-tabs-trigger{flex:1;padding:6px 12px;border-radius:6px;font-size:12px;font-weight:600;border:none;cursor:pointer;background:transparent;color:#64748b;transition:all .15s;}
.ext-tabs-trigger.active{background:#00f2ff;color:#0a0f1e;}
.ext-tabs-content{font-size:13px;color:#cbd5e1;padding:2px 4px;}
</style>"""
    tabs_html = """<div>
  <div class="ext-tabs-list">
    <button class="ext-tabs-trigger active">Web</button>
    <button class="ext-tabs-trigger">Stage</button>
    <button class="ext-tabs-trigger">Email</button>
  </div>
  <div class="ext-tabs-content">Full rendering — all 220 atoms, interactive CSS, web fonts, chart.js.</div>
</div>"""
    components.append(("ext-tabs", "Tab navigation — tabs as JSON [{id,label,content}]; A2UI action on tab change", pill_both,
        f'<div style="{bg}">{tabs_css}{tabs_html}</div>'))

    # ext-label (simple, last)
    lbl_html = """<div style="display:flex;flex-direction:column;gap:6px;">
  <label style="font-size:12px;font-weight:600;color:#94a3b8;letter-spacing:.04em;">Atom type</label>
  <label style="font-size:12px;font-weight:600;color:#94a3b8;letter-spacing:.04em;">Surface</label>
  <label style="font-size:12px;font-weight:600;color:#94a3b8;letter-spacing:.04em;">Vendor</label>
</div>"""
    components.append(("ext-label", "Accessible form label — associates with input via for prop", pill_both,
        f'<div style="{bg}">{lbl_html}</div>'))

    # Build cards
    cards_html = ""
    for tag, desc, pills, body in components:
        cards_html += f"""
<div style="{card_style}">
  <div style="{hdr_style}">
    <code style="{tag_style}">{tag}</code>
    <span style="{desc_style}">{desc}</span>
    <div style="display:flex;gap:4px;">{pills}</div>
    <span style="font-size:10px;color:#475569;white-space:nowrap;">ExtendLabs UI · MIT</span>
  </div>
  <div style="padding:16px;background:#0f1117;">{body}</div>
</div>"""

    return f"""
<section id="extendlabs-ui" style="margin-bottom:56px;">
  <h2 style="font-size:20px;font-weight:800;color:#0f172a;border-bottom:2px solid #e2e8f0;padding-bottom:8px;margin-bottom:4px;">ExtendLabs UI <span style="font-size:13px;font-weight:400;color:#94a3b8;">(12 stage components)</span></h2>
  <p style="font-size:12px;color:#64748b;margin-bottom:20px;">Lit Web Components ported from <a href="https://github.com/extendlabs/ui" style="color:#6366f1;">github.com/extendlabs/ui</a> · MIT.
  These are <code style="background:#f1f5f9;padding:1px 5px;border-radius:3px;font-size:11px;">ext-*</code> custom elements registered on the meet-stage surface —
  not schema atoms. Rendered here as CSS facsimiles on a dark stage background.</p>
  {cards_html}
</section>"""


# ── Render ──────────────────────────────────────────────────────────────────────

def render_atom(atom_type: str) -> tuple[str, str | None]:
    """Returns (html, error_or_None)."""
    if atom_type not in _RENDERERS:
        return "", f"No renderer registered for '{atom_type}'"
    data = dict(DEMO.get(atom_type, {}))
    data["type"] = atom_type
    try:
        return wa_render([data]), None
    except Exception as e:
        # Try with empty data as fallback
        try:
            return wa_render([{"type": atom_type}]), f"(used empty data: {e})"
        except Exception as e2:
            return "", str(e2)

# ── Build HTML ─────────────────────────────────────────────────────────────────

def slug(s: str) -> str:
    return s.lower().replace(" ", "-").replace("&", "and").replace("/", "-")

def surface_pills(atom: dict) -> str:
    surfaces = atom.get("surfaces", {}).get("works_on", [])
    colors   = {"web": "#dbeafe:#1d4ed8", "meet-stage": "#ede9fe:#6d28d9",
                 "googlechat": "#d1fae5:#065f46", "email": "#fef3c7:#92400e", "pdf": "#f3f4f6:#374151"}
    pills = ""
    for s in surfaces:
        bg, fg = colors.get(s, "#f3f4f6:#374151").split(":")
        pills += f'<span style="font-size:10px;padding:1px 7px;border-radius:20px;background:{bg};color:{fg};white-space:nowrap;">{s}</span>'
    return pills

def build_html() -> str:
    # Deduplicate atoms across categories while keeping order
    seen: set[str] = set()
    ordered_cats: list[tuple[str, list[str]]] = []
    for cat, types in CATEGORIES.items():
        unique = [t for t in types if t in ATOMS_BY_TYPE and t not in seen]
        for t in unique:
            seen.add(t)
        if unique:
            ordered_cats.append((cat, unique))
    # Catch anything still not listed
    remainder = [a["type"] for a in ALL_ATOMS if a["type"] not in seen]
    if remainder:
        ordered_cats.append(("Remaining Atoms", remainder))

    # Sidebar
    sidebar_items = ""
    for cat, _ in ordered_cats:
        sid = slug(cat)
        sidebar_items += f'<a href="#{sid}" style="display:block;color:#94a3b8;text-decoration:none;padding:3px 0;font-size:12px;">{cat}</a>'
    sidebar_items += '<a href="#extendlabs-ui" style="display:block;color:#00f2ff;text-decoration:none;padding:3px 0;font-size:12px;margin-top:8px;font-weight:600;">ExtendLabs UI ⚡</a>'

    # Main content
    content_parts = []
    total_rendered = 0
    total_errors   = 0

    for cat, types in ordered_cats:
        sid = slug(cat)
        cards = ""
        for atom_type in types:
            atom   = ATOMS_BY_TYPE.get(atom_type, {"type": atom_type})
            desc   = atom.get("compact_description", atom.get("description", "")[:120])
            source = atom.get("source", {})
            src_name = source.get("name", "a2ui") if isinstance(source, dict) else "a2ui"
            surfaces_html = surface_pills(atom)
            rendered_html, err = render_atom(atom_type)

            if err and not rendered_html:
                total_errors += 1
                body = f'<div style="color:#ef4444;font-size:12px;font-family:monospace;padding:12px;">⚠ {_html.escape(err)}</div>'
            else:
                total_rendered += 1
                body = f'<div style="padding:16px;">{rendered_html}</div>'
                if err:
                    body += f'<div style="color:#f59e0b;font-size:11px;font-family:monospace;padding:0 16px 8px;">⚠ {_html.escape(err)}</div>'

            cards += f'''
<div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:16px;overflow:hidden;">
  <div style="padding:10px 14px;background:#f8fafc;border-bottom:1px solid #e2e8f0;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
    <code style="font-size:12px;font-weight:700;color:#4f46e5;background:#ede9fe;padding:2px 8px;border-radius:4px;">{atom_type}</code>
    <span style="font-size:12px;color:#64748b;flex:1;min-width:0;">{_html.escape(desc)}</span>
    <div style="display:flex;gap:4px;flex-wrap:wrap;">{surfaces_html}</div>
    <span style="font-size:10px;color:#94a3b8;white-space:nowrap;">{_html.escape(src_name)}</span>
  </div>
  {body}
</div>'''

        content_parts.append(f'''
<section id="{sid}" style="margin-bottom:56px;">
  <h2 style="font-size:20px;font-weight:800;color:#0f172a;border-bottom:2px solid #e2e8f0;padding-bottom:8px;margin-bottom:20px;">{cat} <span style="font-size:13px;font-weight:400;color:#94a3b8;">({len(types)} atoms)</span></h2>
  {cards}
</section>''')

    extendlabs_html = build_extendlabs_section()
    content = "\n".join(content_parts) + extendlabs_html
    total = len(ALL_ATOMS)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>A2UI Catalogue — {total} Atoms Web Preview</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f8fafc; color: #1e293b; line-height: 1.5; }}
  .layout {{ display: flex; min-height: 100vh; }}
  .sidebar {{ width: 220px; min-width: 220px; background: #0f172a; color: #e2e8f0;
             position: sticky; top: 0; height: 100vh; overflow-y: auto;
             padding: 20px 16px; flex-shrink: 0; }}
  .sidebar::-webkit-scrollbar {{ width: 4px; }}
  .sidebar::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 2px; }}
  .sidebar a:hover {{ color: #f1f5f9 !important; }}
  .main {{ flex: 1; padding: 40px 48px; max-width: 1000px; overflow-x: hidden; }}
  @media (max-width: 768px) {{
    .sidebar {{ display: none; }}
    .main {{ padding: 20px; }}
  }}
</style>
</head>
<body>
<div class="layout">
  <div class="sidebar">
    <div style="font-size:15px;font-weight:800;color:#f1f5f9;margin-bottom:4px;">A2UI Catalogue</div>
    <div style="font-size:11px;color:#64748b;margin-bottom:20px;">{total} atoms · {total_rendered} rendered</div>
    {sidebar_items}
  </div>
  <div class="main">
    <div style="margin-bottom:40px;">
      <h1 style="font-size:32px;font-weight:900;color:#0f172a;letter-spacing:-0.5px;margin-bottom:8px;">A2UI Atom Catalogue</h1>
      <p style="color:#64748b;font-size:15px;">All {total} atoms rendered in <code style="background:#f1f5f9;padding:1px 6px;border-radius:4px;">web_article</code> format.
      {total_rendered} rendered · {total_errors} errors.</p>
    </div>
    {content}
  </div>
</div>
</body>
</html>'''

if __name__ == "__main__":
    random.seed(42)
    out = ROOT / "catalogue_web_preview.html"
    html = build_html()
    out.write_text(html, encoding="utf-8")
    size_kb = len(html) // 1024
    print(f"Written {out} — {size_kb} KB")
