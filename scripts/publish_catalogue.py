#!/usr/bin/env python3
"""Publish A2UI catalogue pages to Firestore with rich visual demos.

Compiles high-fidelity visual references for all A2UI atoms, grouped across
the Hub, Reading & Documentation, and Media, Data & Social pages.
All rendering uses the standard web_article engine.

Usage:
    python3 scripts/publish_catalogue.py
"""
import json
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Add project root to path for local imports
CATALOGUE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CATALOGUE_ROOT))

from renderers import web_article

# Mock out image base64 conversion during publish to prevent network calls and keep run times instantaneous
web_article._img_src = lambda url: url

FIREBASE_PROJECT = "optical-highway-493012-a1"
FIRESTORE_API = "https://firestore.googleapis.com/v1"

# Existing catalogue posts
CATALOGUE_POSTS = {
    "a2ui-catalogue-hub": "My A2UI Catalogue",
    "a2ui-catalogue-reading": "A2UI Catalogue: Reading & Documentation",
    "a2ui-catalogue-media": "A2UI Catalogue: Media, Data & Social",
}

# Mapping of categories from schema
READING_CATEGORIES = [
    "Foundations",
    "Reading Experience",
    "Documentation",
    "Navigation & Structure",
    "Content Structure",
    "Text & Quotes",
    "Containers & Modals",
    "Cards & Components",
    "Code & Technical",
    "Design Tools",
    "Commerce & Pricing",
    "Comparison & Analysis",
    "Inline Tools",
    "Technical Reference",
    "Warnings & Status",
    "UI Utilities",
    "Utilities & Links",
    "Animation"
]

MEDIA_CATEGORIES = [
    "Media",
    "Data Visualization",
    "Social & Engagement",
    "Video & Audio",
    "External Embeds",
    "Google Workspace"
]

CATEGORIES_MAP = {
    "Foundations": ["body", "closing", "heading", "intro", "subheading"],
    "Reading Experience": ["article_hero", "article_series_nav", "post_metadata_bar", "reading_progress_bar", "scroll_to_top", "table_of_contents", "time_estimate", "related_posts_grid", "series_overview_card"],
    "Documentation": ["changelog_entry", "difficulty_badge", "footnote", "footnote_group", "further_reading", "glossary_term", "release_notes", "resources_list", "table", "tabs", "timeline"],
    "Navigation & Structure": ["anchor_list", "breadcrumb", "faq_accordion", "pagination", "stepper", "tab_bar"],
    "Content Structure": ["bullet_list", "callout", "caution_block", "checklist_interactive", "divider", "key_takeaways", "key_value", "learning_objectives", "pipeline", "progress_checkpoint", "sidebar_note", "steps", "summary_box"],
    "Text & Quotes": ["blockquote_with_avatar", "pull_stat", "quote"],
    "Containers & Modals": ["accordion_item", "collapsible_panel", "css_modal", "css_slide_panel", "flip_card", "hover_card", "tooltip"],
    "Cards & Components": ["badge_group", "notification_badge", "rating_stars", "star_rating_display", "stat_card", "toggle_switch"],
    "Code & Technical": ["annotated_code", "api_param_table", "api_reference", "before_after", "code", "code_diff", "code_snippet_pair", "http_request_block", "tabbed_code", "terminal_block", "file_tree"],
    "Design Tools": ["css_dropdown_menu", "custom_checkbox_group", "expandable_list", "poll_block", "segmented_control", "star_rating_input"],
    "Commerce & Pricing": ["pricing_tier_card", "pricing_tier_group"],
    "Comparison & Analysis": ["capability_checklist", "comparison_grid", "feature_matrix", "pros_cons_list", "product_spec_table", "rating_comparison", "side_by_side_spec", "versus_block"],
    "Inline Tools": ["abbr_tooltip", "copy_to_clipboard", "expandable_text", "glossary_inline"],
    "Technical Reference": ["cli_command", "copy_code_button", "env_var_list", "json_tree_viewer", "keyboard_shortcut", "log_output", "prerequisite_checklist"],
    "Warnings & Status": ["action_required_card", "alert_banner", "deprecation_notice", "experimental_banner", "status_pill", "version_badge"],
    "Media": ["carousel", "color_swatch_grid", "diagram", "framed_screenshot", "gallery", "image", "image_hotspots", "image_pair", "image_with_caption", "pdf_preview", "video_card", "video_pair", "video_thumbnail", "zoomable_image"],
    "Data Visualization": ["benchmark_comparison", "chartjs_bar", "chartjs_line", "data_table_sortable", "donut_stat", "heatmap", "task_list", "sentiment_summary", "metric_comparison_card", "metric_delta", "mini_sparkline_set", "progress_bar", "progress_circle", "sparkline", "status_dashboard", "trend_indicator", "uptime_timeline", "conversion_funnel", "gauge_sla", "stacked_area", "scatter_trend", "call_mood_board", "github_activity_grid", "punch_card", "sankey_flow", "cohort_retention"],
    "Social & Engagement": ["author_bio_card", "avatar_group", "contributor_list", "customer_logo_grid", "expert_endorsement", "follow_button", "follow_cta", "media_mention_card", "newsletter_cta", "reaction_group", "review_callout", "share_quote", "social_feed_embed", "social_share_bar", "social_proof_banner", "testimonial_card"],
    "UI Utilities": ["command_palette", "empty_state", "inline_feedback_message", "loading_skeleton", "search_result_card", "spinner", "toast_notification"],
    "Utilities & Links": ["document_link", "github_repo_card", "repo_links"],
    "Animation": ["typewriter", "number_odometer", "typing_indicator", "countdown_timer",
                  "gradient_text", "reveal_on_scroll", "word_scramble", "svg_path_draw",
                  "toast_notification", "parallax_card"],
    "Video & Audio": ["audio_link", "audio_player", "youtube"],
    "External Embeds": ["embed_codepen", "embed_gist", "embed_google_slides", "embed_stackblitz", "embed_tweet", "figma_embed", "lottie_animation", "live_demo_embed"],
    "Google Workspace": ["gmail_inbox", "gmail_unread_count", "user_profile_card", "drive_storage_usage", "tasks_today", "sheet_form_submit"],
}

ATOM_DEMOS = {
    "intro": {"type": "intro", "series_label": "the first article", "series_url": "#", "continuation": "picks up here.", "note": "All components are rendered server-side as standard clean HTML with zero inline JS requirements."},
    "body": {"type": "body", "text": "This is a standard prose body block demonstrating inline **bold**, *italics*, and standard `code` blocks. It is fully optimized for readability and responsive layout scaling across all modern web browsers."},
    "heading": {"type": "heading", "text": "Interactive Element Reference"},
    "subheading": {"type": "subheading", "text": "Subsection Highlights"},
    "quote": {"type": "quote", "text": "The details are not the details. They make the design.", "attribution": "Charles Eames"},
    "code": {"type": "code", "language": "python", "content": "def render_svg_surface(atom_type, data):\n    # Compiles high-fidelity SVG templates directly on server\n    return render_web_article_block(atom_type, data)"},
    "pipeline": {"type": "pipeline", "steps": ["Local Sandbox", "Commit Hook", "Firestore Sync", "Nginx Serve"]},
    "bullet_list": {"type": "bullet_list", "items": [{"label": "Server-Side SVG", "text": "No rendering cost on client browser"}, {"label": "Pure CSS Interactions", "text": "Tabs, modally expandable panels, and lightboxes require zero Javascript"}, {"label": "High Surface Portability", "text": "Full compatibility guarantees with GWS Add-ons"}]},
    "divider": {"type": "divider"},
    "youtube": {"type": "youtube", "url": "https://youtu.be/DnGvNgftRGQ", "caption": "Google Meet Add-on interactive stage showcase"},
    "image": {"type": "image", "url": "https://picsum.photos/800/400?random=1", "alt": "A random beautiful design setup", "caption": "Interactive design mockup preview"},
    "image_pair": {"type": "image_pair", "left": {"url": "https://picsum.photos/400/300?random=2", "alt": "left side", "caption": "Light Theme View"}, "right": {"url": "https://picsum.photos/400/300?random=3", "alt": "right side", "caption": "Dark Theme Overrides"}},
    "diagram": {"type": "diagram", "url": "https://picsum.photos/600/300?random=4", "caption": "Component Synchronization and Publish Pipeline Flowchart"},
    "repo_links": {"type": "repo_links", "links": [{"label": "A2UI Core Repository", "url": "https://github.com/curtiskrygier/a2ui-catalogue"}]},
    "github_repo_card": {"type": "github_repo_card", "repo": "curtiskrygier/a2ui-catalogue", "label": "A2UI Core Reference Library", "description": "universal visual block components and SVG renderings compatible across multiple web and GWS surfaces."},
    "terminal_block": {"type": "terminal_block", "command": "./sync-catalogue.sh --release \"sync: integrate new visual atoms\"", "output": "🔄 Synchronizing local developments to submodule...\n  [1/4] Running tests...\n  ✅ All tests passed!\n  [3/4] Resetting and pulling submodule...\n  ✅ Submodule staged and committed successfully!"},
    "file_tree": {"type": "file_tree", "title": "Catalogue Project Structure", "tree": "atoms/\n  schema.yaml\nrenderers/\n  web_article.py\n  meet_stage.py\nscripts/\n  publish_catalogue.py\n  push_catalogue_stage.py\ntests/\n  test_renderer.py"},
    "tabbed_code": {"type": "tabbed_code", "tabs": [{"label": "main.py", "code": "print('Initializing A2UI engine...')", "language": "python"}]},
    "http_request_block": {"type": "http_request_block", "method": "PATCH", "url": f"{FIRESTORE_API}/projects/{FIREBASE_PROJECT}/databases/(default)/documents/posts/a2ui-catalogue-media", "description": "Publishes updated visual catalogue data directly to the Firestore collection"},
    "env_var_list": {"type": "env_var_list", "vars": [{"name": "FIREBASE_PROJECT", "value": "optical-highway-493012-a1", "description": "Shared Google Firebase/Firestore target project ID"}, {"name": "STAGE_API_KEY", "value": "••••••••••••", "description": "Authentication token for Google Meet preview stage"}]},
    "prerequisite_checklist": {"type": "prerequisite_checklist", "items": [{"text": "Python 3.10+ installed", "completed": True}, {"text": "Google Cloud CLI authenticated", "completed": True}, {"text": "Submodule clean without untracked changes", "completed": False}]},
    "keyboard_shortcut": {"type": "keyboard_shortcut", "keys": ["Ctrl", "Alt", "U"]},
    "api_param_table": {"type": "api_param_table", "params": [{"name": "post_id", "type": "str", "required": True, "description": "Target blog post document slug/identifier"}, {"name": "title", "type": "str", "required": True, "description": "Display title of the post"}, {"name": "body_html", "type": "str", "required": True, "description": "Rendered high-fidelity HTML content"}]},
    "version_badge": {"type": "version_badge", "version": "v2.1.0", "status": "stable"},
    "deprecation_notice": {"type": "deprecation_notice", "text": "The legacy manual FTP publish script is deprecated and has been superseded by publish_catalogue.py."},
    "experimental_banner": {"type": "experimental_banner", "text": "This page displays living components. Some items are experimental and subject to CSS layout modifications."},
    "cli_command": {"type": "cli_command", "command": "python3 scripts/publish_catalogue.py", "description": "Triggers deterministic compilation and pushes reference pages to the live blog"},
    "copy_code_button": {"type": "copy_code_button", "text": "git submodule update --init --recursive"},
    "log_output": {"type": "log_output", "lines": ["2026-06-01 22:15:00 [INFO] Fetching access token from gcloud CLI...", "2026-06-01 22:15:01 [SUCCESS] Retrieved active token. Publishing 3 pages to Firestore...", "2026-06-01 22:15:02 [SUCCESS] a2ui-catalogue-hub updated successfully!"]},
    "json_tree_viewer": {"type": "json_tree_viewer", "json_string": "{\"active_pages\": [\"hub\", \"reading\", \"media\"], \"project\": \"optical-highway-493012-a1\", \"last_build\": \"2026-06-01\"}"},
    "key_takeaways": {"type": "key_takeaways", "items": [{"text": "A2UI separates components into explicit Reading Experience vs Media and Visualization groups."}, {"text": "Zero clientside JavaScript ensures flawless compatibility with Google Meet's strict Content Security Policies."}]},
    "summary_box": {"type": "summary_box", "text": "This reference represents the absolute source of truth for the A2UI design system, automatically compiled from the vocabulary schema definition."},
    "learning_objectives": {"type": "learning_objectives", "items": [{"text": "Analyze surface compatibility patterns for each visual block type"}, {"text": "Understand the interactive CSS target strategies utilized for widgets"}]},
    "changelog_entry": {"type": "changelog_entry", "version": "2.1.0", "date": "2026-06-01", "changes": [{"type": "added", "text": "Added premium call_mood_board theme and sentiment analyzer block"}, {"type": "added", "text": "Added github_activity_grid visual block with streak metrics"}, {"type": "changed", "text": "Disabled sequential image base64 downloads during Firestore publishing"}, {"type": "fixed", "text": "Optimized CSS carousel layout dots mapping"}]},
    "release_notes": {"type": "release_notes", "title": "Release v2.1.0 Notes", "added": ["Premium call_mood_board theme and sentiment analyzer block", "Github_activity_grid visual block with streak metrics"], "fixed": ["CSS carousel layout dots mapping"], "changed": ["Disabled sequential image base64 downloads during Firestore publishing"]},
    "further_reading": {"type": "further_reading", "links": [{"title": "CSS-Only State Machine Patterns", "url": "#", "annotation": "Explores interactive widgets without JS"}, {"title": "Designing for Google Meet Stage Constraints", "url": "#", "annotation": "Figma-to-Meet design methodologies"}]},
    "resources_list": {"type": "resources_list", "items": [{"title": "A2UI Sketch & Figma Toolkit", "url": "#", "size": "14.2 MB", "type": "figma"}, {"title": "SVG Icon System Assets", "url": "#", "size": "1.8 MB", "type": "zip"}]},
    "sidebar_note": {"type": "sidebar_note", "title": "Architect Tip", "content": "Keep blocks short and leverage bullet lists or grids to present dense technical specs. It significantly improves readability on narrow panels."},
    "difficulty_badge": {"type": "difficulty_badge", "level": "advanced"},
    "caution_block": {"type": "caution_block", "message": "Never attempt to load external UI scripts. Google Meet sandbox will immediately block and suppress them."},
    "checklist_interactive": {"type": "checklist_interactive", "items": ["Ensure gcloud is logged in and configured", "Verify all tests pass with pytest", "Run publish_catalogue.py to sync live pages"]},
    "glossary_inline": {"type": "glossary_inline", "term": "CSP", "definition": "Content Security Policy — browser level restrictions enforcing script and style injection boundaries."},
    "time_estimate": {"type": "time_estimate", "minutes": 8},
    "progress_checkpoint": {"type": "progress_checkpoint", "current_step": 1, "total_steps": 3},
    "social_share_bar": {"type": "social_share_bar", "title": "A2UI Visual Reference Guide", "url": "https://techmusings.krygier.fr/post/a2ui-catalogue-hub"},
    "newsletter_cta": {"type": "newsletter_cta", "title": "Subscribe to techmusings updates", "placeholder": "your.email@krygier.fr", "button_text": "Keep Updated"},
    "author_bio_card": {"type": "author_bio_card", "name": "Curtis Krygier", "bio": "Systems Architect and full-stack software crafter. Specialized in Google Workspace automations, Home Assistant integrations, and elegant UI design systems.", "image": "https://picsum.photos/120/120?random=10"},
    "related_posts_grid": {"type": "related_posts_grid", "posts": [{"title": "Setting Up GWS Addon Sandboxes", "url": "#"}, {"title": "Configuring Shelly EM Power Trackers", "url": "#"}]},
    "series_overview_card": {"type": "series_overview_card", "title": "A2UI Catalogue Trilogy", "current_part": 1, "parts": [{"title": "Main Reference Hub", "url": "/post/a2ui-catalogue-hub"}, {"title": "Reading & Documentation Reference", "url": "/post/a2ui-catalogue-reading"}, {"title": "Media, Data & Social Reference", "url": "/post/a2ui-catalogue-media"}]},
    "reaction_group": {"type": "reaction_group", "reactions": [{"emoji": "👍", "count": 24}, {"emoji": "🔥", "count": 18}, {"emoji": "💡", "count": 14}]},
    "share_quote": {"type": "share_quote", "text": "Highly optimized SVG components published directly to Firestore are incredibly responsive on the blog stage.", "author": "curtis@krygier.fr"},
    "follow_cta": {"type": "follow_cta", "text": "Follow techmusings development progress"},
    "follow_button": {"type": "follow_button", "platform": "github", "username": "curtiskrygier"},
    "reading_progress_bar": {"type": "reading_progress_bar"},
    "table_of_contents": {"type": "table_of_contents", "items": [{"text": "Foundations", "anchor": "#foundations"}, {"text": "Reading Experience", "anchor": "#reading_experience"}, {"text": "Documentation Blocks", "anchor": "#documentation"}]},
    "article_hero": {"type": "article_hero", "title": "A2UI Block Catalogue", "subtitle": "High-Fidelity Component Reference Library", "image_url": "https://picsum.photos/1200/500?random=12"},
    "scroll_to_top": {"type": "scroll_to_top"},
    "article_series_nav": {"type": "article_series_nav", "prev_url": "/post/a2ui-catalogue-reading", "next_url": "/post/a2ui-catalogue-media"},
    "post_metadata_bar": {"type": "post_metadata_bar", "author": "Curtis Krygier", "date": "2026-06-01", "readTime": 6},
    "embed_codepen": {"type": "embed_codepen", "pen_id": "vYyYQvZ", "user_handle": "curtiskrygier"},
    "embed_stackblitz": {"type": "embed_stackblitz", "project_id": "vitejs-vite-z6nrmg"},
    "embed_gist": {"type": "embed_gist", "gist_id": "curtiskrygier/1234567"},
    "embed_tweet": {"type": "embed_tweet", "tweet_id": "1801234567890123456"},
    "embed_google_slides": {"type": "embed_google_slides", "presentation_id": "1_A_B_C_D_slides_example_id"},
    "lottie_animation": {"type": "lottie_animation", "src_url": "https://assets5.lottiefiles.com/packages/lf20_96b7l7s4.json"},
    "figma_embed": {"type": "figma_embed", "embed_url": "https://www.figma.com/embed?embed_host=techmusings&url=https://www.figma.com/file/123456"},
    "closing": {"type": "closing", "text": "That concludes the core Reading & Documentation reference. Proceed to the Media & Visual page to explore rich visualization blocks.", "tags": ["A2UI", "DesignSystem", "WebRef"]},
    "callout": {"type": "callout", "kind": "tip", "title": "Zero-JS Tooltips", "text": "Our tooltip blocks utilize modern CSS anchor positioning and hover selectors to render beautifully without importing heavyweight widget scripts."},
    "steps": {"type": "steps", "items": [{"label": "Import", "text": "Include the A2UI web stylesheet inside your page head"}, {"label": "Compile", "text": "Feed block dictionaries into the Python web_article.render() function"}, {"label": "Inject", "text": "Inject the compiled safe HTML output directly into your article body container"}]},
    "table": {"type": "table", "headers": ["Surface", "Works", "Caveats", "Status"], "rows": [["Web / Blog", "✅ Yes", "None", "Production"], ["Meet Preview", "✅ Yes", "CSP overrides applied", "Production"], ["Google Chat", "⚠️ Partial", "Iframes stripped", "Stable"], ["Email Clients", "⚠️ Partial", "Backgrounds limited", "Beta"]], "caption": "Multi-Surface Compatibility Matrix Overview"},
    "tabs": {"type": "tabs", "tabs": [{"label": "requirements.txt", "language": "text", "content": "httpx>=0.24.0\npyyaml>=6.0\npytest>=7.3"}, {"label": "setup.py", "language": "python", "content": "from setuptools import setup, find_packages\nsetup(name='a2ui', version='2.1.0')"}]},
    "key_value": {"type": "key_value", "title": "Default Global Parameters", "items": [{"key": "A2UI_THEME_DEFAULT", "description": "Default visual presentation theme", "default": "light"}, {"key": "A2UI_BASE64_EMBED", "description": "Auto-convert image URLs to Base64 data URIs", "default": "true"}]},
    "before_after": {"type": "before_after", "language": "python", "before": "# Legacy block loop\nfor b in blocks:\n    html += render_block_v1(b)\n", "after": "# Optimized registry lookup\nhtml = '\\n\\n'.join(_RENDERERS[b['type']](b) for b in blocks if b['type'] in _RENDERERS)\n", "caption": "Comparison of block iteration and dispatch overhead"},
    "api_reference": {"type": "api_reference", "name": "web_article.render", "kind": "function", "description": "Translates a list of A2UI block vocabularies into a single, cohesive, self-contained HTML block string. It dynamically injects light or dark theme overrides depending on target environment.", "parameters": [{"name": "blocks", "type": "List[dict]", "required": True, "description": "Sequence of structured dictionaries conforming to schema.yaml specification"}, {"name": "theme", "type": "str", "required": False, "description": "Visual presentation theme, supports 'light' or 'dark'", "default": "light"}], "returns": "str — Clean, safe, standard HTML string ready to store in Firebase Firestore or render in a CMS"},
    "timeline": {"type": "timeline", "events": [{"date": "Jan 2026", "label": "Project Conception", "text": "A2UI concept defined to address rigid iframe limits inside Google Meet widgets"}, {"date": "Mar 2026", "label": "Alpha Launch", "text": "First 40 text, documentation, and layout elements successfully compiled"}, {"date": "Jun 2026", "label": "v2.1.0 Release", "text": "Full 100+ block catalogue fully integrated, including SVG-styled premium charts and data tracers"}]},
    "annotated_code": {"type": "annotated_code", "language": "python", "code": "def publish_post(post_id, title, body_html):\n    token = get_auth_token()\n    doc = {\n        \"fields\": {\n            \"title\": {\"stringValue\": title},\n            \"body\": {\"stringValue\": body_html},\n            \"topic\": {\"stringValue\": \"a2ui\"}\n        }\n    }\n    return patch_firestore_document(post_id, doc, token)", "annotations": [{"line": 1, "text": "Accepts post identifier slug, post title, and compiled safe HTML"}, {"line": 2, "text": "Fetches authorized access credentials using gcloud print-access-token"}, {"line": 10, "text": "Executes HTTP PATCH to push payload directly to Google Firestore REST endpoint"}]},
    "gallery": {"type": "gallery", "cols": 3, "caption": "Zero-dependency CSS Lightbox Grid demonstration", "images": [{"url": "https://picsum.photos/600/400?random=15", "alt": "Scenic 1", "caption": "Mockup Design Layout"}, {"url": "https://picsum.photos/600/400?random=16", "alt": "Scenic 2", "caption": "Meet Stage Integration"}, {"url": "https://picsum.photos/600/400?random=17", "alt": "Scenic 3", "caption": "Universal Block Tracing"}]},
    "video_pair": {"type": "video_pair", "left": {"url": "https://youtu.be/DnGvNgftRGQ", "label": "A2UI Installation Tutorial"}, "right": {"url": "https://youtu.be/DnGvNgftRGQ", "label": "Advanced Component Styling Guide"}},
    "carousel": {"type": "carousel", "caption": "Pure CSS Responsive Sliding Carousel Component", "slides": [{"url": "https://picsum.photos/1000/500?random=20", "label": "Premium Layout", "subtitle": "Elegant dark mode themes and glassmorphic panels built-in"}, {"url": "https://picsum.photos/1000/500?random=21", "label": "Lightning Performance", "subtitle": "Zero client-side JS overhead, compiles into static optimized assets"}]},
    "stat_card": {"type": "stat_card", "title": "Core Performance Metrics", "stats": [{"label": "Server Compile Time", "value": "1.4ms", "delta": "-12%"}, {"label": "Core CSS Size (Min)", "value": "18.2 KB", "delta": "-2%"}, {"label": "Browser Paint Delay", "value": "0.15ms", "delta": "-45%"}]},
    "progress_bar": {"type": "progress_bar", "percentage": 94, "label": "Production Build Validation Success"},
    "badge_group": {"type": "badge_group", "badges": [{"text": "Universal", "color": "#1a73e8"}, {"text": "Premium", "color": "#8430ce"}, {"text": "Verified", "color": "#137333"}]},
    "sparkline": {"type": "sparkline", "title": "API Request Volume Trend (Last 24 Hours)", "data": [120, 145, 130, 110, 95, 115, 140, 175, 210, 190, 185, 230, 245, 260, 220, 205, 240, 285, 310, 340, 295, 280, 315, 330], "height": 45},
    "heatmap": {"type": "heatmap", "title": "Hourly Component Render Load", "data": [[5, 12, 18, 15, 8], [8, 22, 35, 28, 14], [12, 45, 68, 52, 20], [15, 58, 92, 74, 25], [10, 32, 48, 40, 18]], "cols_labels": ["Mon", "Tue", "Wed", "Thu", "Fri"], "rows_labels": ["9-11am", "11-1pm", "1-3pm", "3-5pm", "5-7pm"]},
    "donut_stat": {"type": "donut_stat", "value": 88, "max_value": 100, "label": "Server Cache Hit Rate", "unit": "%", "color": "#10b981"},
    "abbr_tooltip": {"type": "abbr_tooltip", "text": "GDM", "title": "Gemini Dynamic Modules"},
    "command_palette": {"type": "command_palette"},
    "copy_to_clipboard": {"type": "copy_to_clipboard", "text": "npm i @a2ui/core", "value": "npm install @a2ui/core"},
    "expandable_list": {
        "type": "expandable_list",
        "items": [
            {
                "text": "System Hardware",
                "children": [
                    {"text": "Daikin AC Multi-Split (5 zones)"},
                    {"text": "Shelly Pro 3EM Whole-Home Meter"}
                ]
            },
            {
                "text": "Core Software",
                "children": [
                    {"text": "Home Assistant OS"},
                    {"text": "A2UI Deterministic Compiler v2.1.0"}
                ]
            }
        ]
    },
    "metric_comparison_card": {"type": "metric_comparison_card", "label": "API Endpoint Response Latency", "value": 118, "previous": 145},
    "mini_sparkline_set": {
        "type": "mini_sparkline_set",
        "series": [
            {"label": "CPU Load", "data": [24, 28, 35, 22, 19, 45, 30]},
            {"label": "Memory", "data": [4.2, 4.3, 4.5, 4.4, 4.6, 4.8, 4.7]},
            {"label": "Network I/O", "data": [120, 140, 180, 110, 95, 210, 130]}
        ]
    },
    "notification_badge": {"type": "notification_badge", "text": "3", "color": "#7c3aed"},
    "poll_block": {
        "type": "poll_block",
        "question": "Which A2UI surface do you use most frequently?",
        "options": [
            {"text": "Web Blog (krygier.fr)", "votes": 42},
            {"text": "Google Meet Add-on Stage", "votes": 28},
            {"text": "Google Chat Interactive Cards", "votes": 15}
        ]
    },
    "search_result_card": {"type": "search_result_card"},
    "status_dashboard": {"type": "status_dashboard"},
    "uptime_timeline": {"type": "uptime_timeline", "uptime": 99.95, "days": 30},
    "metric_delta": {"type": "metric_delta", "label": "Database Query Overhead", "value": "2.4ms", "delta_value": "0.8ms", "direction": "down", "color": "#137333"},
    "trend_indicator": {"type": "trend_indicator", "direction": "up", "color": "#137333", "text": "CSAT developer satisfaction up 8.4% this quarter"},
    "breadcrumb": {"type": "breadcrumb", "items": [{"text": "Reference Hub", "url": "/post/a2ui-catalogue-hub"}, {"text": "Reading & Documentation", "url": "/post/a2ui-catalogue-reading"}, {"text": "Current Page", "url": "#"}]},
    "pagination": {"type": "pagination", "current_page": 2, "total_pages": 3, "base_url": "/post/a2ui-catalogue-"},
    "stepper": {"type": "stepper", "current_step": 2, "steps": ["Main Hub Guide", "Reading & Docs Reference", "Media & Visual Reference"]},
    "tab_bar": {"type": "tab_bar", "tabs": [{"text": "Overview", "url": "#", "active": True}, {"text": "Detailed Specs", "url": "#", "active": False}, {"text": "Subsurface Trace", "url": "#", "active": False}]},
    "anchor_list": {"type": "anchor_list", "items": [{"text": "Foundations", "anchor": "#foundations"}, {"text": "Reading Experience", "anchor": "#reading_experience"}, {"text": "Documentation Blocks", "anchor": "#documentation"}, {"text": "Navigation & Structure", "anchor": "#navigation_structure"}]},
    "faq_accordion": {"type": "faq_accordion", "items": [{"question": "Does A2UI require any runtime Javascript?", "answer": "No. The entire library is built specifically to render into safe, standard HTML and SVGs on the server side, ensuring perfect performance and security compliance with zero runtime JS dependencies."}, {"question": "Can I style the visual elements with custom CSS?", "answer": "Yes, elements are equipped with distinct class names. You can modify brand coloring and fonts inside your global stylesheets."}]},
    "glossary_term": {"type": "glossary_term", "term": "A2UI Block", "definition": "A self-contained structured representation of a single content element, compiled deterministically from schema.yaml definitions."},
    "footnote": {"type": "footnote", "number": 1, "text": "Multi-surface compatibility is verified automatically on each check-in by running the pytest suite against target schemas."},
    "blockquote_with_avatar": {"type": "blockquote_with_avatar", "avatar_url": "https://picsum.photos/60/60?random=25", "text": "Transitioning our internal engineering tutorials to A2UI has completely solved our cross-platform layout breakage. It compiles flawlessly into static pages.", "name": "Marcus Aurelius", "title": "Lead Developer, techmusings"},
    "pull_stat": {"type": "pull_stat", "value": "99.98%", "label": "Verified Production Layout Stability"},
    "accordion_item": {"type": "accordion_item", "title": "Expand Advanced Rendering Parameters", "content": "Advanced parameters include caching layers, local assets override bindings, and automated SVG optimization tags."},
    "tooltip": {"type": "tooltip", "text": "Hover over this indicator", "tooltip_text": "A2UI tooltip renders entirely with zero client-side JS!"},
    "hover_card": {"type": "hover_card", "trigger": "Hover for Team Details", "card_html": "<p style='margin:0;font-size:0.82rem;'><strong>A2UI Core Team</strong><br/>GDM and SVG Compilation Group<br/>Project project optical-highway-493012-a1</p>"},
    "collapsible_panel": {"type": "collapsible_panel", "title": "Review Component License", "content": "Licensed under standard MIT open-source terms. Safe for use across all enterprise surfaces."},
    "css_modal": {"type": "css_modal", "title": "Pure CSS Dialog Demonstration", "trigger_text": "Click to Display Dialog", "body_html": "<p style='margin-bottom:12px;'>This dialog renders beautifully without any clientside JavaScript, utilizing CSS :target triggers.</p><p>It is perfectly safe for strict sandboxed environments!</p>"},
    "audio_player": {"type": "audio_player", "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", "title": "Developer Q&A Session Recording"},
    "audio_link": {"type": "audio_link", "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", "label": "Download Podcast Audio Clip (MP3)"},
    "pdf_preview": {"type": "pdf_preview", "url": "https://pdfobject.com/pdf/sample.pdf", "title": "A2UI Architecture Dossier (PDF Preview)"},
    "document_link": {"type": "document_link", "url": "#", "title": "Download complete PDF developer guide"},
    "video_thumbnail": {"type": "video_thumbnail", "url": "https://youtu.be/DnGvNgftRGQ", "thumbnail_url": "https://picsum.photos/480/270?random=30", "title": "Overview Tutorial Video Preview"},
    "video_card": {"type": "video_card", "url": "https://youtu.be/DnGvNgftRGQ", "title": "Automating Multi-Surface SVG Publication", "duration": "8:45"},
    "code_diff": {"type": "code_diff", "language": "python", "diff": "- print \"Publishing raw payload\"\n+ print(f\"Publishing payload {post_id} directly to Firestore...\")"},
    "code_snippet_pair": {"type": "code_snippet_pair", "language_left": "python", "code_left": "# Standard approach\nhtml = render(blocks)\n", "label_left": "Standard", "language_right": "python", "code_right": "# Theme overridden\nhtml = render(blocks, theme='dark')\n", "label_right": "Meet Stage"},
    "framed_screenshot": {"type": "framed_screenshot", "url": "https://picsum.photos/800/450?random=35", "caption": "Interactive Google Meet preview panel"},
    "image_with_caption": {"type": "image_with_caption", "url": "https://picsum.photos/800/450?random=36", "caption": "Beautiful responsive captioned design block integration"},
    "alert_banner": {"type": "alert_banner", "text": "Important Notice: Submodule staging configurations have been updated inside sync-catalogue.sh.", "style": "warning"},
    "toast_notification": {"type": "toast_notification", "text": "Firestore synchronization completed successfully!"},
    "loading_skeleton": {"type": "loading_skeleton"},
    "empty_state": {"type": "empty_state", "title": "No pending submodule conflicts", "description": "Local workspace branch main is fully clean and in sync with upstream origin."},
    "spinner": {"type": "spinner"},
    "status_pill": {"type": "status_pill", "text": "Active / Verified", "color": "#137333"},
    "inline_feedback_message": {"type": "inline_feedback_message", "text": "Changes applied to Firestore", "style": "success"},
    "rating_stars": {"type": "rating_stars", "rating": 4.8, "max_stars": 5},
    "progress_circle": {"type": "progress_circle", "percentage": 76, "label": "Build Speed Target"},
    "action_required_card": {"type": "action_required_card", "title": "Approve Release v2.1.0", "text": "Please verify that the visual presentation of call_mood_board and github_activity_grid looks flawless on techmusings blog, then approve this release."},
    "feature_matrix": {"type": "feature_matrix", "features": [{"name": "Responsive Columns", "web": True, "chat": False, "meet": True}, {"name": "Inline SVGs", "web": True, "chat": True, "meet": True}, {"name": "Audio Players", "web": True, "chat": False, "meet": False}]},
    "pricing_tier_card": {"type": "pricing_tier_card", "title": "Enterprise Tier", "price": "$149 / mo", "features": ["Guaranteed 99.99% compilation SLA", "Dedicated SVG visual design consulting", "Custom surface layout mappings"]},
    "pricing_tier_group": {"type": "pricing_tier_group", "tiers": [{"title": "Community", "price": "$0"}, {"title": "Professional", "price": "$49"}]},
    "pros_cons_list": {"type": "pros_cons_list", "pros": ["Spectacular vector rendering", "Super fast page loads", "Zero security/CSP risk"], "cons": ["High structural nesting requires clean JSON builders"]},
    "side_by_side_spec": {"type": "side_by_side_spec", "title": "Core Compiler Variants Comparison", "left": {"label": "Development Sandbox", "items": ["Hot reloading enabled", "Comprehensive debug stacktraces", "Console rendering metrics log"]}, "right": {"label": "Production Live Pushes", "items": ["Nginx asset caching", "Image URL checks", "Access tokens retrieval via gcloud"]}},
    "product_spec_table": {"type": "product_spec_table", "title": "A2UI Engine Specifications", "specs": [{"label": "Standard Compliance", "value": "HTML5 / SVG 1.1"}, {"label": "Framework Dependency", "value": "None (Zero)"}, {"label": "Storage Backend", "value": "Google Cloud Firestore"}]},
    "comparison_grid": {"type": "comparison_grid", "title": "Framework Visual Performance Index", "headers": ["Feature Spec", "A2UI Compiler", "React / Canvas CSR"], "rows": [["Initial Load Speed", "🚀 Instant (Pre-rendered)", "🐌 Delayed (Bundle downloads)"], ["Layout Shift (CLS)", "0 (Stable)", "0.15 (Hydration shifting)"], ["Memory Footprint", "Minimal (Static elements)", "Significant (Client-side VM)"]]},
    "versus_block": {"type": "versus_block", "left": {"title": "Server-Compiled Vector Atoms", "text": "Spectacular pre-rendered SVG assets that paint instantaneously inside sandboxes."}, "right": {"title": "Clientside Hydrated Canvas", "text": "Heavy script bundle downloads that delay execution and trigger performance alerts."}},
    "rating_comparison": {"type": "rating_comparison", "title": "Developer CSAT Ratings", "ratings": [{"label": "Page Load Performance", "rating": 4.9}, {"label": "Surface Portability", "rating": 4.8}, {"label": "Code Clarity & Schemas", "rating": 4.7}]},
    "capability_checklist": {"type": "capability_checklist", "title": "Interactive Widget Surface Readiness", "items": [{"name": "Zero-JS Accordion Panels", "capable": True}, {"name": "CSS-Only Sliding Carousels", "capable": True}, {"name": "Dynamic Map Layers", "capable": False}]},
    "toggle_switch": {"type": "toggle_switch", "label": "Enable performance tracing", "checked": True},
    "expandable_text": {"type": "expandable_text", "summary": "Read more about AST block mapping", "details": "AST (Abstract Syntax Tree) block mapping parses our schema configurations into highly robust representations, matching block inputs to their target pythonic generator methods without any structural mapping gaps."},
    "flip_card": {"type": "flip_card", "front_html": "<h4>Hover Me to Flip</h4><p>Reveal architecture details</p>", "back_html": "<h4>Premium SVGs!</h4><p>Renders perfectly clean, standard-compliant vector designs</p>"},
    "image_hotspots": {"type": "image_hotspots", "image_url": "https://picsum.photos/800/400?random=40", "hotspots": [{"x": 25, "y": 35, "text": "Feature Badge: Compact visual tags"}, {"x": 60, "y": 55, "text": "Visual SVG Panel: Precompiled on server"}]},
    "css_dropdown_menu": {"type": "css_dropdown_menu", "label": "Explore Page Reference Docs", "items": [{"text": "Reading & Docs Reference", "url": "/post/a2ui-catalogue-reading"}, {"text": "Media & Data Visual Reference", "url": "/post/a2ui-catalogue-media"}]},
    "star_rating_input": {"type": "star_rating_input", "name": "post-rating-selector"},
    "segmented_control": {"type": "segmented_control", "name": "render-theme-mode", "options": [{"label": "Light Theme", "value": "light", "checked": True}, {"label": "Meet Stage Theme", "value": "dark"}]},
    "zoomable_image": {"type": "zoomable_image", "url": "https://picsum.photos/800/400?random=45"},
    "custom_checkbox_group": {"type": "custom_checkbox_group", "name": "select-modules", "items": [{"label": "Core Foundations", "value": "foundations", "checked": True}, {"label": "Data Visuals", "value": "visuals", "checked": True}, {"label": "Social Embeds", "value": "socials"}]},
    "css_slide_panel": {"type": "css_slide_panel", "title": "Developer Logs Panel", "trigger_text": "Slide Developer Logs Panel Out", "body_html": "<p>Logs initialized at 22:15:00. Firestore published successfully. Status: 200 OK.</p>"},
    "testimonial_card": {"type": "testimonial_card", "quote": "Transitioning our entire reference catalog to the A2UI design system has completely solved our cross-platform broken styles. It is responsive, elegant, and blazing fast.", "author": "John von Neumann", "role": "Principal Systems Analyst", "avatar_url": "https://picsum.photos/80/80?random=48"},
    "star_rating_display": {"type": "star_rating_display", "rating": 4.9},
    "avatar_group": {"type": "avatar_group", "avatars": [{"url": "https://picsum.photos/40/40?random=50"}, {"url": "https://picsum.photos/40/40?random=51"}, {"url": "https://picsum.photos/40/40?random=52"}, {"url": "https://picsum.photos/40/40?random=53"}]},
    "contributor_list": {"type": "contributor_list", "contributors": [{"name": "Curtis Krygier", "avatar_url": "https://picsum.photos/40/40?random=55"}, {"name": "Gemini Copilot", "avatar_url": "https://picsum.photos/40/40?random=56"}]},
    "customer_logo_grid": {"type": "customer_logo_grid", "logos": [{"url": "https://picsum.photos/140/70?random=70", "alt": "techmusings Partner"}, {"url": "https://picsum.photos/140/70?random=71", "alt": "MeetStudio Platform"}]},
    "social_proof_banner": {"type": "social_proof_banner", "text": "Powering over 1,500 active high-impact visual meeting sessions daily"},
    "media_mention_card": {"type": "media_mention_card", "source": "Wired Magazine", "quote": "A2UI establishes a secure, zero-JS vector block standard that bypasses rigid sandboxing barriers.", "url": "#"},
    "expert_endorsement": {"type": "expert_endorsement", "expert_name": "Ada Lovelace", "expert_avatar": "https://picsum.photos/80/80?random=78", "quote": "The precompiled SVG layouts demonstrate superb server-side synthesis. It is a work of pure logical art."},
    "review_callout": {"type": "review_callout", "stars": 5, "reviewer": "Frameworks Weekly", "text": "Spectacular performance, bulletproof security. The ultimate component library for GWS surfaces."},
    "social_feed_embed": {"type": "social_feed_embed", "title": "Developer Feedback", "posts": [{"author": "curtis_k", "text": "The premium call_mood_board and github_activity_grid visual blocks look absolutely amazing! Clean vector render on techmusings blog!"}, {"author": "meet_dev", "text": "CSS tabs and modals are incredibly fast inside the Google Meet preview iframe! Safe, lightweight, zero dependencies."}]},
    "footnote_group": {"type": "footnote_group", "footnotes": [{"number": 1, "text": "Compatibility verified against current Chrome and Google Meet sandboxed browser runtimes."}]},
    "color_swatch_grid": {"type": "color_swatch_grid", "title": "A2UI Core Design System Swatches", "colors": [{"label": "Primary Accent Cyan", "hex": "#00f2ff"}, {"label": "Clean Emerald Green", "hex": "#137333"}, {"label": "Vibrant Royal Purple", "hex": "#8430ce"}, {"label": "Premium Dark Slate", "hex": "#0f1117"}]},
    "live_demo_embed": {"type": "live_demo_embed", "url": "https://techmusings.krygier.fr", "caption": "Live preview of the techmusings portal"},
    "benchmark_comparison": {"type": "benchmark_comparison", "title": "Vector Elements Page Compiles Overhead", "items": [{"label": "Pre-compiled HTML Cache", "value": 0.2, "unit": "ms"}, {"label": "A2UI Python Compiler", "value": 1.4, "unit": "ms"}, {"label": "Heavy Clientside CSR", "value": 140.0, "unit": "ms"}]},
    "chartjs_bar": {"type": "chartjs_bar", "title": "MeetStudio Meeting Traces (Last 3 Quarters)", "labels": ["Q4 2025", "Q1 2026", "Q2 2026"], "datasets": [{"label": "Active Sessions", "data": [450, 820, 1540]}]},
    "chartjs_line": {"type": "chartjs_line", "title": "Shelly EM Whole-Home Power Monitoring (kW)", "labels": ["9:00am", "12:00pm", "3:00pm", "6:00pm", "9:00pm"], "datasets": [{"label": "Power Usage", "data": [1.4, 2.8, 1.2, 3.4, 2.1]}]},
    "data_table_sortable": {"type": "data_table_sortable", "title": "Circuit Performance Logs", "headers": ["Device Node", "Active Watts", "SLA Status"], "rows": [["Daikin Multi AC Zone 1", "450W", "✅ Optimal"], ["Shelly Pro 3EM", "24W", "✅ Active"], ["manual_samba", "12W", "✅ Active"]]},
    "punch_card": {
        "type": "punch_card",
        "title": "Weekly Developer Sync Commits",
        "labels_days": ["Mon", "Wed", "Fri"],
        "data": [[0, 1, 14], [1, 2, 28], [2, 3, 42]]
    },
    "sankey_flow": {
        "type": "sankey_flow",
        "title": "Visitor Conversion Flowchart",
        "nodes": [
            {"id": "main_blog", "label": "Main Blog Portal", "column": 0, "color": "#38bdf8"},
            {"id": "a2ui_hub", "label": "A2UI Hub", "column": 0, "color": "#818cf8"},
            {"id": "sub_catalogue", "label": "Sub Catalogue Pages", "column": 1, "color": "#fb7185"},
            {"id": "repo_sync", "label": "Repository Sync", "column": 1, "color": "#34d399"}
        ],
        "links": [
            {"source": "main_blog", "target": "a2ui_hub", "value": 1200},
            {"source": "a2ui_hub", "target": "sub_catalogue", "value": 650},
            {"source": "sub_catalogue", "target": "repo_sync", "value": 250}
        ]
    },
    "cohort_retention": {
        "type": "cohort_retention",
        "title": "A2UI Core Developer Retention Matrix",
        "periods": ["Month 0", "Month 1", "Month 2", "Month 3"],
        "cohorts": [
            {"cohort_name": "Q1 Cohort", "original_size": 850, "retention_rates": [100.0, 92.4, 84.1, 78.5]},
            {"cohort_name": "Q2 Cohort", "original_size": 1200, "retention_rates": [100.0, 95.2, 89.0, 0.0]}
        ]
    },
    "task_list": {"type": "task_list", "title": "MeetStudio Engineering Roadmap Backlog", "tasks": [{"task": "Integrate premium call_mood_board SVG component", "status": "completed"}, {"task": "Integrate premium github_activity_grid tracer component", "status": "completed"}, {"task": "Deploy hardcoded blog overwrite fix (deterministic python publisher)", "status": "completed"}, {"task": "Add configurable display of images (carousel/gallery component)", "status": "pending"}]},
    "sentiment_summary": {"type": "sentiment_summary", "title": "Daikin Multi Split AC Discussion Mood", "positive": 78, "neutral": 15, "negative": 7},
    "conversion_funnel": {"type": "conversion_funnel", "title": "Developer Compilation Funnel", "steps": [{"stage": "YAML Schema Loaded", "value": 1000}, {"stage": "Pytest Validated", "value": 940}, {"stage": "Compiled to Web Article HTML", "value": 940}, {"stage": "Published to Google Firestore", "value": 940}]},
    "gauge_sla": {"type": "gauge_sla", "title": "Shelly EM Meter Connection SLA Uptime", "value": 99.98, "max_value": 100, "unit": "%", "label": "Active Connector"},
    "stacked_area": {"type": "stacked_area", "title": "MeetStudio MRR Growth Projections", "labels": ["Jan 2026", "Mar 2026", "May 2026"], "series": [{"label": "Basic Tier", "data": [1200, 2400, 4800], "color": "#00f2ff"}, {"label": "Pro Multi Split Tier", "data": [400, 1200, 3200], "color": "#8430ce"}]},
    "scatter_trend": {"type": "scatter_trend", "title": "Compile Latency vs Component Count Correlation", "data_points": [[5, 1.1], [15, 1.4], [40, 1.8], [80, 2.2], [105, 2.6]], "label_x": "Component Count", "label_y": "Latency (ms)"},
    "call_mood_board": {
        "type": "call_mood_board",
        "title": "Meeting Atmosphere & Emotional Sentiment summary",
        "moods": [
            {"mood": "Collaborative", "intensity": 85, "color": "#10b981"},
            {"mood": "Focused", "intensity": 68, "color": "#3b82f6"},
            {"mood": "Vibrant", "intensity": 55, "color": "#f59e0b"}
        ],
        "themes": [
            {"term": "Daikin AC Multi-Split Automation", "weight": 85, "sentiment": "positive"},
            {"term": "Shelly Whole-Home Power metering", "weight": 70, "sentiment": "neutral"},
            {"term": "Premium SVG Vector compilation", "weight": 65, "sentiment": "positive"},
            {"term": "Google Workspace CSP overrides", "weight": 40, "sentiment": "negative"}
        ],
        "summary": "Superb collaborative alignment on the custom Daikin automation system and GWS Add-on architectures. Excellent progress verified on Home Assistant dashboard monitoring integrations. Brief discussion regarding Workspace sandbox network overrides."
    },
    "github_activity_grid": {
        "type": "github_activity_grid",
        "title": "A2UI Core Repository Activity Tracer",
        "username": "curtiskrygier",
        "total_contributions": 182,
        "streak_days": 15,
        "activity": [
            0, 1, 2, 4, 3, 2, 0, 1, 1, 2, 4, 0, 0, 1, 2, 3, 4, 1, 0, 2, 
            3, 4, 2, 1, 0, 1, 2, 3, 4, 3, 2, 1, 0, 0, 1, 2, 4, 4, 3, 2,
            1, 0, 0, 1, 1, 2, 3, 4, 4, 3, 2, 1, 0, 1, 2, 3, 4, 3, 2, 1
        ]
    },
    # Animation atoms
    "typewriter":         {"type": "typewriter", "text": "The catalogue is the substrate.", "speed": "normal", "cursor": True},
    "number_odometer":    {"type": "number_odometer", "value": "2026", "label": "Year of the agent", "accent": "#4f46e5"},
    "typing_indicator":   {"type": "typing_indicator", "name": "Agent", "variant": "dark"},
    "countdown_timer":    {"type": "countdown_timer", "hours": 0, "minutes": 4, "seconds": 59, "label": "Until next deploy", "variant": "dark"},
    "gradient_text":      {"type": "gradient_text", "text": "Build something beautiful.", "from": "#4f46e5", "to": "#06b6d4", "size": "2rem"},
    "reveal_on_scroll":   {"type": "reveal_on_scroll", "title": "Revealed on scroll", "body": "Content fades in as you scroll into view.", "direction": "up"},
    "word_scramble":      {"type": "word_scramble", "text": "A2UI", "duration": 2.0},
    "svg_path_draw":      {"type": "svg_path_draw", "shape": "check", "color": "#22c55e", "label": "All atoms rendered"},
    "toast_notification": {"type": "toast_notification", "title": "Atoms published", "message": "Synced to Firestore.", "variant": "success"},
    "parallax_card":      {"type": "parallax_card", "title": "Parallax Card", "body": "Hover to see 3D tilt.", "badge": "Animation"},
    # ── Google Workspace atoms (GAS-only — catalogue shows schema reference) ──
    "gmail_inbox":        {"type": "callout", "icon": "✉️", "color": "indigo", "title": "gmail_inbox", "body": "**GAS-only atom.** Horizontal swipeable carousel of the last N Gmail inbox threads. Each card shows a coloured sender avatar, name, subject (bold if unread), snippet, and relative timestamp. Clicking a card opens the thread in Gmail web. Fields: `title`, `count` (default 10, max 20), `accent` (hex colour)."},
    "gmail_unread_count": {"type": "callout", "icon": "✉️", "color": "indigo", "title": "gmail_unread_count", "body": "**GAS-only atom.** Unread count badges for one or more Gmail labels. Fields: `labels` (array, default `['INBOX']`), `title`, `accent` (hex)."},
    "user_profile_card":  {"type": "callout", "icon": "👤", "color": "blue", "title": "user_profile_card", "body": "**GAS-only atom.** Signed-in user card — avatar initial, display name derived from email, domain, and locale. Fields: `accent` (hex)."},
    "drive_storage_usage":{"type": "callout", "icon": "📁", "color": "green", "title": "drive_storage_usage", "body": "**GAS-only atom.** Google Drive storage usage bar — used vs total quota with percentage. No fields required."},
    "tasks_today":        {"type": "callout", "icon": "✅", "color": "green", "title": "tasks_today", "body": "**GAS-only atom.** Google Tasks due today from the default task list. Fields: `title`, `max_results` (default 10), `list_name` (optional — targets a named task list)."},
    "sheet_form_submit":  {"type": "callout", "icon": "📊", "color": "green", "title": "sheet_form_submit", "body": "**GAS-only atom.** A form that appends a row to a Google Sheet on submit. Fields: `spreadsheet_id`, `sheet_name`, `title`, `fields` (array of `{name, label, type, placeholder}`), `submit_label`, `accent`."},
}

def get_auth_token():
    """Get active gcloud token."""
    errors = []
    for args in [
        ["gcloud", "auth", "print-access-token"],
        ["gcloud", "auth", "application-default", "print-access-token"]
    ]:
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                errors.append(f"{' '.join(args)} returned exit code {result.returncode}. Stderr: {result.stderr.strip()}")
        except Exception as e:
            errors.append(f"{' '.join(args)} failed with exception: {e}")
    
    print(f"  ⚠️ get_auth_token failed: {'; '.join(errors)}", file=sys.stderr)
    return None

def delete_post(post_id: str) -> bool:
    """Deletes a document cleanly from Firestore to ensure a fresh republish."""
    token = get_auth_token()
    if not token:
        print(f"  ❌ No auth token found via gcloud CLI to delete {post_id}", file=sys.stderr)
        return False

    url = f"{FIRESTORE_API}/projects/{FIREBASE_PROJECT}/databases/(default)/documents/posts/{post_id}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}"
        },
        method="DELETE"
    )
    try:
        with urllib.request.urlopen(req) as response:
            return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return True
        print(f"  ❌ HTTP Error deleting {post_id}: {e.code} - {e.reason}", file=sys.stderr)
        try:
            print(e.read().decode("utf-8", errors="ignore"), file=sys.stderr)
        except Exception:
            pass
    except Exception as e:
        print(f"  ❌ Error deleting {post_id}: {e}", file=sys.stderr)
    return False

def publish_post(post_id: str, title: str, body_html: str, topic: str = "a2ui", summary: str = "") -> bool:
    """Publishes a document cleanly to Firestore with explicit routing slug."""
    token = get_auth_token()
    if not token:
        print("  ❌ No auth token found via gcloud CLI", file=sys.stderr)
        return False

    now = datetime.now().isoformat() + "Z"
    doc = {
        "fields": {
            "title": {"stringValue": title},
            "slug": {"stringValue": post_id},
            "body": {"stringValue": body_html},
            "summary": {"stringValue": summary or title},
            "topic": {"stringValue": topic},
            "type": {"stringValue": "reference"},
            "status": {"stringValue": "published"},
            "date": {"stringValue": datetime.now().strftime("%Y-%m-%d")},
            "readTime": {"integerValue": "8"},
            "format": {"stringValue": "html"},
            "updatedAt": {"timestampValue": now},
        }
    }

    url = f"{FIRESTORE_API}/projects/{FIREBASE_PROJECT}/databases/(default)/documents/posts/{post_id}"
    req = urllib.request.Request(
        url,
        data=json.dumps(doc).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            if "name" in res_json or "error" not in res_json:
                return True
            print(f"  ❌ Unexpected response payload: {res_body}", file=sys.stderr)
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP Error publishing {post_id}: {e.code} - {e.reason}", file=sys.stderr)
        try:
            print(e.read().decode("utf-8", errors="ignore"), file=sys.stderr)
        except Exception:
            pass
    except Exception as e:
        print(f"  ❌ Request Error publishing {post_id}: {e}", file=sys.stderr)
    return False

def generate_hub_html() -> str:
    """Compiles the Hub page HTML."""
    blocks = [
        {"type": "article_hero", "title": "A2UI Visual Atom Catalogue", "subtitle": "Universal block reference library and GDM visualization tracer", "image_url": "https://picsum.photos/1200/500?random=1"},
        {"type": "post_metadata_bar", "author": "Curtis Krygier", "date": datetime.now().strftime("%Y-%m-%d"), "readTime": 5},
        {"type": "intro", "series_label": "A2UI Hub", "series_url": "/post/a2ui-catalogue-hub", "note": "Welcome to techmusings A2UI core design system. This multi-part reference compiles 100+ components precompiled into optimized serverside HTML and SVGs."},
        {"type": "body", "text": "A2UI separates components into explicit Reading Experience versus Media and Data Visualization groups. By precompiling these blocks server-side, we bypass rigid sandbox constraints, making elements instantaneous, light, and perfectly responsive."},
        {"type": "heading", "text": "Catalogue Organization & Reference Links"},
        {"type": "body", "text": "Explore the complete component catalogue split deterministically across two dedicated, high-fidelity tracer articles:"},
        {"type": "bullet_list", "items": [
            {"label": "Part 1: Reading & Documentation Reference", "text": "Foundations, lists, code cards, API specifications, and structural UI elements. [View Part 1](/post/a2ui-catalogue-reading)"},
            {"label": "Part 2: Media, Data & Social Reference", "text": "Vector charts, SVG activity trackers, CSS carousels, audio players, and engagement CTA cards. [View Part 2](/post/a2ui-catalogue-media)"}
        ]},
        {"type": "divider"},
        {"type": "heading", "text": "Automated Multi-Surface Testing & Validation"},
        {"type": "body", "text": "Every atom's surface compatibility is validated automatically on each commit, ensuring standard rendering boundaries across 4 distinct GWS surfaces:"},
        {"type": "table", "headers": ["Atom Group", "Works On", "Degraded On", "Status"], "rows": [
            ["Reading Foundations", "Web, Meet Stage, Chat, Email, PDF", "None", "Stable"],
            ["Code & Reference Blocks", "Web, Meet Stage, PDF", "Chat Cards, Email", "Production Ready"],
            ["Media & SVG Charts", "Web, Meet Stage", "Chat Cards, Email, PDF", "Verified Live"],
            ["External Embeds", "Web", "Meet, Chat, Email, PDF", "Partial Support"]
        ], "caption": "Cross-Surface Capability Scorecard"},
        {"type": "divider"},
        {"type": "heading", "text": "MeetStudio Backlog & Roadmaps"},
        {"type": "task_list", "title": "MeetStudio Roadmap Tracing", "tasks": [
            {"task": "Integrate premium call_mood_board SVG component", "status": "completed"},
            {"task": "Integrate premium github_activity_grid tracer component", "status": "completed"},
            {"task": "Deploy hardcoded blog overwrite fix (deterministic python publisher)", "status": "completed"},
            {"task": "Add configurable display of images (carousel/gallery component)", "status": "pending"}
        ]},
        {"type": "closing", "text": "The entire system automatically regenerates and synchronizes to Google Firestore upon running the deployment sync hooks. Happy system architecture tracing!", "tags": ["A2UI", "DesignSystem", "Techmusings", "MeetStudio"]}
    ]
    return web_article.render(blocks)

def compile_and_render_catalogue_page(categories: list) -> str:
    """Compiles list of categories into a single, cohesive article HTML."""
    blocks = []
    
    # Header Hero
    blocks.append({"type": "article_hero", "title": "A2UI Block Catalogue Reference", "subtitle": "High-Fidelity Element Tracing & Live Visual Demonstrations", "image_url": "https://picsum.photos/1200/500?random=15"})
    blocks.append({"type": "post_metadata_bar", "author": "Curtis Krygier", "date": datetime.now().strftime("%Y-%m-%d"), "readTime": 15})
    
    for category_name in categories:
        atom_types = CATEGORIES_MAP.get(category_name, [])
        if not atom_types:
            continue
            
        blocks.append({"type": "heading", "text": f"Category: {category_name}"})
        blocks.append({"type": "body", "text": f"This section compiles and showcases the **{len(atom_types)} core atoms** defined under the *{category_name}* vocabulary in our universal system schema."})
        
        for atom_type in atom_types:
            demo_payload = ATOM_DEMOS.get(atom_type)
            if not demo_payload:
                # Fallback to keep script completely safe
                demo_payload = {"type": atom_type, "text": f"Demo of `{atom_type}` elements."}
                
            blocks.append({"type": "subheading", "text": f"Atom: <code>{atom_type}</code>"})
            blocks.append({"type": "body", "text": f"The `\"{atom_type}\"` component rendering demonstration on the live blog stage is displayed below:"})
            
            # Append the actual premium demo block
            blocks.append(demo_payload)
            blocks.append({"type": "divider"})
            
    blocks.append({"type": "closing", "text": "Tracer compilation hook complete. All elements successfully traced.", "tags": ["A2UI", "ComponentLibrary", "Techmusings", "Deterministic"]})
    return web_article.render(blocks)

if __name__ == "__main__":
    print("🚀 Running robust deterministic A2UI Catalogue Firestore Publisher...")
    
    # 0. Clean slate - Delete existing documents to ensure no field residuals remain
    print("\n🧹 Deleting existing catalogue pages from Firestore...")
    for pid in CATALOGUE_POSTS.keys():
        print(f"  Deleting {pid}...")
        delete_post(pid)
    
    # 1. Compile Hub
    print("\n  [1/3] Compiling Hub Page...")
    hub_html = generate_hub_html()
    
    # 2. Compile Reading & Docs
    print("  [2/3] Compiling Reading & Documentation Page...")
    reading_html = compile_and_render_catalogue_page(READING_CATEGORIES)
    
    # 3. Compile Media, Data & Social
    print("  [3/3] Compiling Media, Data & Social Page...")
    media_html = compile_and_render_catalogue_page(MEDIA_CATEGORIES)
    
    # 4. Push updates
    print("\n📬 Syncing compiled HTMLs directly to Firestore...")
    
    success = True
    
    print("  Publishing a2ui-catalogue-hub...")
    if publish_post("a2ui-catalogue-hub", "My A2UI Catalogue", hub_html, topic="A2UI", summary="A2UI Visual Reference Main Hub"):
        print("    ✅ Hub Page Updated successfully!")
    else:
        print("    ❌ Hub Page Update failed.")
        success = False
        
    print("  Publishing a2ui-catalogue-reading...")
    if publish_post("a2ui-catalogue-reading", "A2UI Catalogue: Reading & Documentation", reading_html, topic="A2UI", summary="Foundations, code, navigation, and structural UI elements reference"):
        print("    ✅ Reading Page Updated successfully!")
    else:
        print("    ❌ Reading Page Update failed.")
        success = False
        
    print("  Publishing a2ui-catalogue-media...")
    if publish_post("a2ui-catalogue-media", "A2UI Catalogue: Media, Data & Social", media_html, topic="A2UI", summary="Vector charts, SVG activity trackers, carousels, audio, and engagement blocks"):
        print("    ✅ Media Page Updated successfully!")
    else:
        print("    ❌ Media Page Update failed.")
        success = False
        
    if success:
        print("\n✨ Spectacular Success! All 3 pages cleanly synchronized to Firestore.")
        print("  - Hub Link:      https://techmusings.krygier.fr/post/a2ui-catalogue-hub")
        print("  - Reading Link:  https://techmusings.krygier.fr/post/a2ui-catalogue-reading")
        print("  - Media Link:    https://techmusings.krygier.fr/post/a2ui-catalogue-media")
    else:
        print("\n⚠️ Publishing encountered some failures. Please inspect the logs above.", file=sys.stderr)
        sys.exit(1)
