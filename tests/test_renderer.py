"""Renderer tests — one test per atom, plus surface compatibility assertions."""

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def r(renderer, *blocks):
    return renderer(list(blocks))

def rd(renderer, *blocks):
    return renderer(list(blocks), theme="dark")


# ── Text atoms ────────────────────────────────────────────────────────────────

def test_body(renderer):
    html = r(renderer, {"type": "body", "text": "Hello **world**."})
    assert "<p>" in html
    assert "<strong>world</strong>" in html


def test_heading(renderer):
    html = r(renderer, {"type": "heading", "text": "My Section"})
    assert "<h2>" in html
    assert "My Section" in html


def test_subheading(renderer):
    html = r(renderer, {"type": "subheading", "text": "Sub"})
    assert "<h3>" in html


def test_quote(renderer):
    html = r(renderer, {"type": "quote", "text": "The substrate is what compounds.", "attribution": "Curtis"})
    assert "<blockquote>" in html
    assert "Curtis" in html


def test_code(renderer):
    html = r(renderer, {"type": "code", "language": "python", "content": "x = 1"})
    assert "<pre>" in html
    assert 'class="language-python"' in html
    assert "x = 1" in html


def test_pipeline(renderer):
    html = r(renderer, {"type": "pipeline", "steps": ["build", "deploy", "run"]})
    assert "build" in html
    assert "──►" in html


def test_bullet_list(renderer):
    html = r(renderer, {"type": "bullet_list", "items": [
        {"label": "Key", "text": "value"},
        {"text": "plain item"},
    ]})
    assert "<ul>" in html
    assert "<strong>Key</strong>" in html


def test_divider(renderer):
    html = r(renderer, {"type": "divider"})
    assert "<hr" in html


def test_intro(renderer):
    html = r(renderer, {"type": "intro", "series_label": "the first article",
                         "series_url": "https://example.com", "continuation": "picks up here."})
    assert "<em>" in html
    assert "the first article" in html


def test_closing(renderer):
    html = r(renderer, {"type": "closing", "text": "Final thought.", "tags": ["AI", "A2UI"]})
    assert "Final thought." in html
    assert "#AI" in html


# ── Media atoms ───────────────────────────────────────────────────────────────

def test_youtube(renderer):
    html = r(renderer, {"type": "youtube", "url": "https://youtu.be/DnGvNgftRGQ", "caption": "Demo"})
    assert "DnGvNgftRGQ" in html
    assert "iframe" in html
    assert "Demo" in html


def test_image(renderer):
    html = r(renderer, {"type": "image", "url": "https://example.com/img.png", "alt": "test"})
    assert "<img" in html
    assert "example.com/img.png" in html


def test_image_pair(renderer):
    html = r(renderer, {"type": "image_pair",
                         "left": {"url": "https://example.com/a.png", "alt": "a", "caption": "Left"},
                         "right": {"url": "https://example.com/b.png", "alt": "b", "caption": "Right"}})
    assert "a.png" in html
    assert "b.png" in html
    assert "Left" in html
    assert "Right" in html


def test_repo_links(renderer):
    html = r(renderer, {"type": "repo_links", "links": [
        {"label": "Catalogue", "url": "https://github.com/curtiskrygier/a2ui-catalogue"}
    ]})
    assert "Catalogue" in html
    assert "github.com/curtiskrygier/a2ui-catalogue" in html


# ── Enhanced atoms ────────────────────────────────────────────────────────────

def test_callout_kinds(renderer):
    for kind in ["info", "warning", "tip", "danger"]:
        html = r(renderer, {"type": "callout", "kind": kind, "title": kind.title(), "text": "test"})
        assert kind.title() in html


def test_steps(renderer):
    html = r(renderer, {"type": "steps", "items": [
        {"label": "First", "text": "do this"},
        {"label": "Second", "text": "then this"},
    ]})
    assert "First" in html
    assert "Second" in html
    # Blue circle indicators
    assert "border-radius:50%" in html


def test_table(renderer):
    html = r(renderer, {"type": "table",
                         "headers": ["A", "B", "C"],
                         "rows": [["1", "2", "3"], ["4", "5", "6"]]})
    assert "<table" in html
    assert "<th" in html
    assert "A" in html and "B" in html


def test_tabs(renderer):
    html = r(renderer, {"type": "tabs", "tabs": [
        {"label": "Python", "language": "python", "content": "x = 1"},
        {"label": "bash",   "language": "bash",   "content": "echo hi"},
    ]})
    assert 'type="radio"' in html
    assert "tm-tab-label" in html
    assert "Python" in html
    assert "bash" in html
    assert "x = 1" in html


def test_key_value(renderer):
    html = r(renderer, {"type": "key_value", "items": [
        {"key": "GEMINI_PROJECT", "description": "GCP project", "required": True},
        {"key": "REGION", "description": "Region", "default": "us-central1"},
    ]})
    assert "GEMINI_PROJECT" in html
    assert "Required" in html
    assert "us-central1" in html


def test_before_after(renderer):
    html = r(renderer, {"type": "before_after", "language": "python",
                         "before": "old code", "after": "new code"})
    assert "old code" in html
    assert "new code" in html
    assert "#c5221f" in html  # red for before
    assert "#137333" in html  # green for after


def test_api_reference(renderer):
    html = r(renderer, {"type": "api_reference",
                         "name": "my_function", "kind": "function",
                         "description": "Does something useful.",
                         "parameters": [
                             {"name": "x", "type": "str", "required": True, "description": "input"}
                         ],
                         "returns": "str"})
    assert "my_function" in html
    assert "Does something useful" in html
    assert "✓" in html  # required checkmark indicator


def test_timeline(renderer):
    html = r(renderer, {"type": "timeline", "events": [
        {"date": "Jan 2026", "label": "Start", "text": "began"},
        {"date": "Feb 2026", "label": "End",   "text": "done"},
    ]})
    assert "Jan 2026" in html
    assert "Start" in html
    assert "border-radius:50%" in html  # dot indicators


def test_annotated_code(renderer):
    html = r(renderer, {"type": "annotated_code", "language": "python",
                         "code": "x = 1\ny = 2\nz = 3",
                         "annotations": [
                             {"line": 1, "text": "assigns x"},
                             {"line": 3, "text": "assigns z"},
                         ]})
    assert "assigns x" in html
    assert "assigns z" in html
    assert "f9ab00" in html  # yellow callout badge


def test_gallery(renderer):
    html = r(renderer, {"type": "gallery", "cols": 2, "images": [
        {"url": "https://example.com/a.png", "alt": "a", "caption": "A"},
        {"url": "https://example.com/b.png", "alt": "b", "caption": "B"},
    ]})
    assert "a.png" in html
    assert "b.png" in html
    assert "grid-template-columns" in html


def test_video_pair(renderer):
    html = r(renderer, {"type": "video_pair",
                         "left":  {"url": "https://youtu.be/AAA1111111A", "label": "Left"},
                         "right": {"url": "https://youtu.be/BBB2222222B", "label": "Right"}})
    assert "AAA1111111A" in html
    assert "BBB2222222B" in html
    assert "Left" in html


def test_carousel(renderer):
    html = r(renderer, {"type": "carousel", "slides": [
        {"url": "https://example.com/a.png", "label": "Slide 1"},
        {"url": "https://example.com/b.png", "label": "Slide 2"},
    ]})
    assert 'type="radio"' in html
    assert "Slide 1" in html
    assert "cubic-bezier" in html  # smooth transition


# ── Dark theme ────────────────────────────────────────────────────────────────

def test_dark_theme_injects_overrides(renderer):
    html = rd(renderer, {"type": "body", "text": "test"})
    assert "meet-stage dark theme" in html
    assert "#00f2ff" in html
def test_light_theme_no_overrides(renderer):
    html = r(renderer, {"type": "body", "text": "test"})
    assert "meet-stage dark theme" not in html


# ── New atoms ─────────────────────────────────────────────────────────────────

def test_post_metadata_bar(renderer):
    html = r(renderer, {"type": "post_metadata_bar", "author": "Curtis", "date": "2026-06-01", "readTime": 5})
    assert "Curtis" in html
    assert "2026-06-01" in html
    assert "5 min read" in html

def test_conversion_funnel(renderer):
    html = r(renderer, {"type": "conversion_funnel", "title": "Onboarding", "steps": [{"stage": "Visits", "value": 100}, {"stage": "Signups", "value": 50}]})
    assert "Onboarding" in html
    assert "Visits" in html
    assert "Signups" in html

def test_gauge_sla(renderer):
    html = r(renderer, {"type": "gauge_sla", "title": "API SLA", "value": 99.4, "max_value": 100, "unit": "%", "label": "Uptime"})
    assert "API SLA" in html
    assert "99.4" in html

def test_stacked_area(renderer):
    html = r(renderer, {"type": "stacked_area", "title": "MRR", "labels": ["Jan", "Feb"], "series": [{"label": "SaaS", "data": [10, 20], "color": "#00f2ff"}]})
    assert "MRR" in html
    assert "SaaS" in html

def test_scatter_trend(renderer):
    html = r(renderer, {"type": "scatter_trend", "title": "CSAT", "data_points": [[1, 2], [2, 4]], "label_x": "Time", "label_y": "Score"})
    assert "CSAT" in html
    assert "TIME" in html

def test_notification_badge(renderer):
    html = r(renderer, {"type": "notification_badge", "text": "5", "color": "#ef4444"})
    assert "5" in html
    assert "ef4444" in html

def test_expandable_list(renderer):
    html = r(renderer, {"type": "expandable_list", "items": [{"text": "Root", "children": [{"text": "Child"}]}]})
    assert "Root" in html
    assert "Child" in html

def test_poll_block(renderer):
    html = r(renderer, {"type": "poll_block", "question": "Favorite framework?", "options": [{"text": "React", "votes": 40}, {"text": "Vue", "votes": 10}]})
    assert "Favorite framework?" in html
    assert "React" in html
    assert "40 votes" in html

def test_abbr_tooltip(renderer):
    html = r(renderer, {"type": "abbr_tooltip", "text": "API", "title": "Application Programming Interface"})
    assert "API" in html
    assert "Application Programming Interface" in html

def test_copy_to_clipboard(renderer):
    html = r(renderer, {"type": "copy_to_clipboard", "text": "npm install", "value": "npm i"})
    assert "npm install" in html
    assert "npm i" in html


def test_call_mood_board(renderer):
    html = r(renderer, {
        "type": "call_mood_board",
        "title": "Discussion Atmosphere",
        "moods": [{"mood": "Collaborative", "intensity": 85, "color": "#10b981"}],
        "themes": [{"term": "Scaling", "weight": 70, "sentiment": "neutral"}],
        "summary": "Great alignment on goals."
    })
    assert "Discussion Atmosphere" in html
    assert "Collaborative" in html
    assert "85%" in html
    assert "Scaling" in html
    assert "Great alignment" in html


def test_github_activity_grid(renderer):
    html = r(renderer, {
        "type": "github_activity_grid",
        "title": "Repo commits",
        "username": "curtiskrygier",
        "total_contributions": 150,
        "streak_days": 12,
        "activity": [0, 1, 2, 3, 4]
    })
    assert "Repo commits" in html
    assert "curtiskrygier" in html
    assert "150" in html
    assert "12" in html
    assert "<rect" in html



# ── OpenUI atoms (10 new — form suite + modal + follow_up_chips) ──────────────

def test_form(renderer):
    html = r(renderer, {"component": "form", "title": "Sign up", "submit_label": "Submit",
                        "fields": [{"label": "Name", "name": "name", "type": "text",
                                    "placeholder": "Your name", "rules": ["required"]}]})
    assert "Sign up" in html
    assert 'name="name"' in html
    assert "Submit" in html


def test_form_input(renderer):
    html = r(renderer, {"component": "form_input", "label": "Email", "name": "email",
                        "type": "email", "placeholder": "you@example.com"})
    assert 'type="email"' in html
    assert "Email" in html


def test_form_select(renderer):
    html = r(renderer, {"component": "form_select", "label": "Plan", "name": "plan",
                        "options": [{"value": "basic", "label": "Basic"},
                                    {"value": "pro", "label": "Pro"}]})
    assert "<select" in html
    assert "Basic" in html
    assert "Pro" in html


def test_form_radio_group(renderer):
    html = r(renderer, {"component": "form_radio_group", "label": "Size", "name": "size",
                        "default_value": "md",
                        "options": [{"value": "sm", "label": "Small"},
                                    {"value": "md", "label": "Medium"}]})
    assert 'type="radio"' in html
    assert "checked" in html
    assert "Medium" in html


def test_form_checkbox_group(renderer):
    html = r(renderer, {"component": "form_checkbox_group", "label": "Perms", "name": "perms",
                        "options": [{"name": "read", "label": "Read", "default_checked": True},
                                    {"name": "write", "label": "Write"}]})
    assert 'type="checkbox"' in html
    assert "checked" in html
    assert "Write" in html


def test_form_switch_group(renderer):
    html = r(renderer, {"component": "form_switch_group", "label": "Notifs", "name": "notif",
                        "items": [{"name": "email", "label": "Email", "default_checked": True},
                                  {"name": "sms", "label": "SMS"}]})
    assert 'type="checkbox"' in html
    assert "Email" in html
    assert "SMS" in html


def test_form_slider(renderer):
    html = r(renderer, {"component": "form_slider", "label": "Budget", "name": "budget",
                        "min": 0, "max": 1000, "step": 50, "value": 400, "unit": "$"})
    assert 'type="range"' in html
    assert "400" in html
    assert "$" in html


def test_form_date_picker_single(renderer):
    html = r(renderer, {"component": "form_date_picker", "label": "Start", "name": "start",
                        "mode": "single", "value": "2026-07-01"})
    assert 'type="date"' in html
    assert "2026-07-01" in html


def test_form_date_picker_range(renderer):
    html = r(renderer, {"component": "form_date_picker", "label": "Period", "name": "period",
                        "mode": "range"})
    assert "From" in html
    assert "To" in html


def test_modal(renderer):
    html = r(renderer, {"component": "modal", "title": "Confirm delete",
                        "description": "This cannot be undone.",
                        "trigger_label": "Delete", "confirm_label": "Yes", "cancel_label": "No"})
    assert "Confirm delete" in html
    assert "cannot be undone" in html
    assert ":checked" in html
    assert "Yes" in html and "No" in html


def test_modal_with_nested_block(renderer):
    html = r(renderer, {"component": "modal", "title": "Transfer", "trigger_label": "Transfer",
                        "confirm_label": "OK", "cancel_label": "Cancel",
                        "blocks": [{"component": "form_select", "label": "Owner", "name": "owner",
                                    "options": [{"value": "alice", "label": "Alice"}]}]})
    assert "Transfer" in html
    assert "<select" in html
    assert "Alice" in html


def test_follow_up_chips(renderer):
    html = r(renderer, {"component": "follow_up_chips", "accent": "#38bdf8",
                        "label": "Continue", "items": ["More detail", "Show example"]})
    assert "More detail" in html
    assert "Show example" in html
    assert "rgba(56,189,248" in html


def test_openui_atoms_work_on_meet_stage(atoms):
    for t in ["form", "form_input", "form_select", "form_radio_group", "form_checkbox_group",
              "form_switch_group", "form_slider", "form_date_picker", "modal", "follow_up_chips"]:
        works_on = atoms[t]["surfaces"]["works_on"]
        assert "google-meet-stage" in works_on, f"{t} missing meet-stage in works_on"


def test_modal_works_on_meet_stage(atoms):
    assert "google-meet-stage" in atoms["modal"]["surfaces"]["works_on"]
    incompatible = [e["surface"] for e in atoms["modal"]["surfaces"].get("incompatible_on", [])]
    assert "google-meet-stage" not in incompatible


# ── Surface compatibility via schema ──────────────────────────────────────────

def test_tabs_incompatible_googlechat(atoms):
    surfaces = atoms["tabs"]["surfaces"]
    incompatible = [e["surface"] for e in surfaces.get("incompatible_on", [])]
    assert "google-chat" in incompatible


def test_youtube_incompatible_email(atoms):
    surfaces = atoms["youtube"]["surfaces"]
    incompatible = [e["surface"] for e in surfaces.get("incompatible_on", [])]
    assert "email" in incompatible


def test_carousel_works_on_meet_stage(atoms):
    works_on = atoms["carousel"]["surfaces"]["works_on"]
    assert "google-meet-stage" in works_on


def test_body_works_everywhere(atoms):
    works_on = atoms["body"]["surfaces"]["works_on"]
    assert set(works_on) == {"web", "google-meet-stage", "google-chat", "email", "pdf", "google-apps-script-web"}


# ── Vercel Geist-inspired atoms ───────────────────────────────────────────────

def test_choicebox_group_radio(renderer):
    html = r(renderer, {"component": "choicebox_group", "name": "plan",
                        "label": "Choose a plan",
                        "items": [
                            {"value": "free", "title": "Free", "description": "Up to 3 projects", "icon": "🆓"},
                            {"value": "pro",  "title": "Pro",  "description": "Unlimited projects", "icon": "⚡"},
                        ]})
    assert "Choose a plan" in html
    assert "Free" in html and "Pro" in html
    assert "Up to 3 projects" in html
    assert 'type="radio"' in html
    assert ":has(input:checked)" in html


def test_choicebox_group_multiple(renderer):
    html = r(renderer, {"component": "choicebox_group", "name": "features",
                        "multiple": True,
                        "items": [
                            {"value": "analytics", "title": "Analytics"},
                            {"value": "sso",       "title": "SSO"},
                        ]})
    assert 'type="checkbox"' in html
    assert "Analytics" in html and "SSO" in html


def test_choicebox_group_with_submit(renderer):
    html = r(renderer, {"component": "choicebox_group", "name": "framework",
                        "submit_label": "Continue",
                        "items": [{"value": "next", "title": "Next.js"}]})
    assert "Continue" in html
    assert 'type="submit"' in html


def test_choicebox_group_disabled_item(renderer):
    html = r(renderer, {"component": "choicebox_group", "name": "tier",
                        "items": [
                            {"value": "active",   "title": "Active"},
                            {"value": "inactive", "title": "Inactive", "disabled": True},
                        ]})
    assert "disabled" in html
    assert "opacity" in html


def test_choicebox_group_accent(renderer):
    html = r(renderer, {"component": "choicebox_group", "name": "color",
                        "accent": "#8b5cf6",
                        "items": [{"value": "a", "title": "Option A"}]})
    assert "rgba(139,92,246" in html


def test_choicebox_group_works_on_meet_stage(atoms):
    works_on = atoms["choicebox_group"]["surfaces"]["works_on"]
    assert "google-meet-stage" in works_on
    incompatible = [e["surface"] for e in atoms["choicebox_group"]["surfaces"].get("incompatible_on", [])]
    assert "google-meet-stage" not in incompatible


def test_feedback_prompt_thumbs(renderer):
    html = r(renderer, {"component": "feedback_prompt",
                        "question": "Was this helpful?",
                        "style": "thumbs"})
    assert "Was this helpful?" in html
    assert "👍" in html and "👎" in html
    assert 'value="up"' in html and 'value="down"' in html
    assert ":has(input:checked)" in html


def test_feedback_prompt_stars(renderer):
    html = r(renderer, {"component": "feedback_prompt",
                        "question": "Rate this article",
                        "style": "stars"})
    assert "Rate this article" in html
    assert "★" in html
    assert "row-reverse" in html
    assert "input:checked~label" in html


def test_feedback_prompt_with_followup(renderer):
    html = r(renderer, {"component": "feedback_prompt",
                        "style": "thumbs",
                        "placeholder": "Tell us more"})
    assert "<textarea" in html
    assert "Tell us more" in html


def test_feedback_prompt_with_action_url(renderer):
    html = r(renderer, {"component": "feedback_prompt",
                        "action_url": "https://example.com/feedback"})
    assert "<form" in html
    assert "https://example.com/feedback" in html
    assert 'type="submit"' in html


def test_feedback_prompt_works_on_meet_stage(atoms):
    works_on = atoms["feedback_prompt"]["surfaces"]["works_on"]
    assert "google-meet-stage" in works_on


# ── Aceternity UI-inspired atoms ──────────────────────────────────────────────

def test_marquee_strip_basic(renderer):
    html = r(renderer, {"component": "marquee_strip",
                        "items": ["React", "Python", "TypeScript", "Tailwind"]})
    assert "@keyframes" in html
    assert "React" in html
    assert "Python" in html
    # items duplicated for seamless loop
    assert html.count("React") == 2


def test_marquee_strip_with_label_and_image(renderer):
    html = r(renderer, {"component": "marquee_strip",
                        "label": "Trusted by",
                        "items": [{"text": "Acme Corp", "image_url": "/logo.png"}]})
    assert "Trusted by" in html
    assert "Acme Corp" in html
    assert 'src="/logo.png"' in html


def test_marquee_strip_direction_right(renderer):
    html = r(renderer, {"component": "marquee_strip",
                        "items": ["A", "B"],
                        "direction": "right"})
    assert "reverse" in html


def test_marquee_strip_works_on_meet_stage(atoms):
    works_on = atoms["marquee_strip"]["surfaces"]["works_on"]
    assert "google-meet-stage" in works_on


def test_typewriter_text_basic(renderer):
    html = r(renderer, {"component": "typewriter_text", "text": "Hello world"})
    assert "@keyframes" in html
    assert "Hello world" in html
    assert "steps(11" in html  # 11 chars


def test_typewriter_text_no_cursor(renderer):
    html = r(renderer, {"component": "typewriter_text",
                        "text": "No cursor", "cursor": False})
    assert "blink" not in html
    assert "|" not in html


def test_typewriter_text_custom_style(renderer):
    html = r(renderer, {"component": "typewriter_text",
                        "text": "Big text", "size": "48px",
                        "color": "#38bdf8", "weight": "900"})
    assert "48px" in html
    assert "#38bdf8" in html
    assert "900" in html


def test_typewriter_text_works_on_meet_stage(atoms):
    works_on = atoms["typewriter_text"]["surfaces"]["works_on"]
    assert "google-meet-stage" in works_on


def test_animated_border_card_basic(renderer):
    html = r(renderer, {"component": "animated_border_card",
                        "title": "Featured", "body": "This card has a moving border."})
    assert "conic-gradient" in html
    assert "@keyframes" in html
    assert "Featured" in html
    assert "moving border" in html


def test_animated_border_card_custom_accent(renderer):
    html = r(renderer, {"component": "animated_border_card",
                        "body": "Custom colours",
                        "accent": "#f59e0b", "accent2": "#ef4444"})
    assert "#f59e0b" in html
    assert "#ef4444" in html


def test_animated_border_card_dark_bg(renderer):
    html = r(renderer, {"component": "animated_border_card",
                        "body": "Dark card", "background": "#0d1525"})
    assert "#0d1525" in html


def test_animated_border_card_works_on_meet_stage(atoms):
    works_on = atoms["animated_border_card"]["surfaces"]["works_on"]
    assert "google-meet-stage" in works_on


# ── Aceternity UI-inspired atoms (batch 2) ────────────────────────────────────

def test_aurora_background_basic(renderer):
    html = r(renderer, {"component": "aurora_background",
                        "title": "Aurora", "body": "Background effect."})
    assert "radial-gradient" in html
    assert "@keyframes" in html
    assert "Aurora" in html

def test_aurora_background_custom_colors(renderer):
    html = r(renderer, {"component": "aurora_background",
                        "colors": ["#ef4444", "#f59e0b", "#10b981"]})
    assert "#ef4444" in html
    assert "#f59e0b" in html
    assert "#10b981" in html

def test_aurora_background_works_on_meet_stage(atoms):
    assert "google-meet-stage" in atoms["aurora_background"]["surfaces"]["works_on"]

def test_dot_grid_background_dots(renderer):
    html = r(renderer, {"component": "dot_grid_background", "variant": "dots",
                        "title": "Dot grid", "body": "Pattern."})
    assert "radial-gradient" in html
    assert "Dot grid" in html

def test_dot_grid_background_grid_variant(renderer):
    html = r(renderer, {"component": "dot_grid_background", "variant": "grid"})
    assert "linear-gradient" in html

def test_dot_grid_background_works_on_meet_stage(atoms):
    assert "google-meet-stage" in atoms["dot_grid_background"]["surfaces"]["works_on"]

def test_shimmer_button_basic(renderer):
    html = r(renderer, {"component": "shimmer_button", "label": "Deploy now"})
    assert "@keyframes" in html
    assert "background-position" in html
    assert "Deploy now" in html

def test_shimmer_button_as_link(renderer):
    html = r(renderer, {"component": "shimmer_button",
                        "label": "Open repo", "href": "https://github.com"})
    assert '<a ' in html
    assert 'href="https://github.com"' in html

def test_shimmer_button_works_on_meet_stage(atoms):
    assert "google-meet-stage" in atoms["shimmer_button"]["surfaces"]["works_on"]

def test_card_stack_basic(renderer):
    html = r(renderer, {"component": "card_stack", "cards": [
        {"title": "Card A", "body": "First card.", "accent": "#38bdf8"},
        {"title": "Card B", "body": "Second card.", "accent": "#818cf8"},
    ]})
    assert "rotate" in html
    assert "Card A" in html   # front card content shown
    assert "Card B" not in html  # back card content hidden

def test_card_stack_four_cards(renderer):
    html = r(renderer, {"component": "card_stack", "cards": [
        {"title": f"Card {i}", "body": f"Body {i}."} for i in range(4)
    ]})
    assert html.count("rotate") == 4

def test_card_stack_works_on_meet_stage(atoms):
    assert "google-meet-stage" in atoms["card_stack"]["surfaces"]["works_on"]

def test_meteor_shower_basic(renderer):
    html = r(renderer, {"component": "meteor_shower", "count": 10})
    assert "@keyframes" in html
    assert html.count("<span") == 10

def test_meteor_shower_with_content(renderer):
    html = r(renderer, {"component": "meteor_shower",
                        "title": "Launching soon", "body": "Watch this space."})
    assert "Launching soon" in html
    assert "Watch this space" in html

def test_meteor_shower_works_on_meet_stage(atoms):
    assert "google-meet-stage" in atoms["meteor_shower"]["surfaces"]["works_on"]

def test_source_inspiration_on_all_aceternity_atoms(atoms):
    aceternity = ['marquee_strip', 'typewriter_text', 'animated_border_card',
                  'aurora_background', 'dot_grid_background', 'shimmer_button',
                  'card_stack', 'meteor_shower']
    for name in aceternity:
        assert 'source_inspiration' in atoms[name], f"{name} missing source_inspiration"

# ── blur_fade_in ──────────────────────────────────────────────────────────────

def test_blur_fade_in_basic(renderer):
    html = r(renderer, {"component": "blur_fade_in", "title": "Hello", "body": "World"})
    assert "@keyframes" in html
    assert "blur(" in html
    assert "Hello" in html

def test_blur_fade_in_direction(renderer):
    html = r(renderer, {"component": "blur_fade_in", "direction": "left"})
    assert "translateX(16px)" in html

def test_blur_fade_in_delay(renderer):
    html = r(renderer, {"component": "blur_fade_in", "delay": "0.5s", "title": "Delayed"})
    assert "0.5s" in html

def test_blur_fade_in_works_on_meet_stage(atoms):
    assert "google-meet-stage" in atoms["blur_fade_in"]["surfaces"]["works_on"]

def test_blur_fade_in_source_inspiration(atoms):
    assert "Magic UI" in atoms["blur_fade_in"]["source_inspiration"]["name"]

# ── glow_button ───────────────────────────────────────────────────────────────

def test_glow_button_ready_state(renderer):
    html = r(renderer, {"component": "glow_button", "label": "Deploy", "state": "ready"})
    assert "Deploy" in html
    assert "box-shadow" in html
    assert "@keyframes" in html

def test_glow_button_disabled_state(renderer):
    html = r(renderer, {"component": "glow_button", "label": "Locked", "state": "disabled"})
    assert "not-allowed" in html
    assert "#374151" in html

def test_glow_button_fired_state(renderer):
    html = r(renderer, {"component": "glow_button", "label": "Sent!", "state": "fired"})
    assert "34d399" in html  # default fired colour

def test_glow_button_as_anchor(renderer):
    html = r(renderer, {"component": "glow_button", "label": "Open", "href": "#demo"})
    assert "<a " in html
    assert 'href="#demo"' in html

def test_glow_button_works_on_meet_stage(atoms):
    assert "google-meet-stage" in atoms["glow_button"]["surfaces"]["works_on"]

# ── animated_beam ─────────────────────────────────────────────────────────────

def test_animated_beam_basic(renderer):
    html = r(renderer, {"component": "animated_beam",
                        "from_label": "Agent", "to_label": "Stage"})
    assert "<svg" in html
    assert "Agent" in html
    assert "Stage" in html
    assert "@keyframes" in html

def test_animated_beam_inactive(renderer):
    html = r(renderer, {"component": "animated_beam",
                        "from_label": "A", "to_label": "B", "active": False})
    assert "@keyframes" not in html
    assert "<svg" in html

def test_animated_beam_curved_path(renderer):
    html = r(renderer, {"component": "animated_beam",
                        "from_label": "X", "to_label": "Y", "curved": True})
    assert " C" in html  # cubic bezier control point

def test_animated_beam_straight_path(renderer):
    html = r(renderer, {"component": "animated_beam",
                        "from_label": "X", "to_label": "Y", "curved": False})
    assert " L" in html

def test_animated_beam_works_on_meet_stage(atoms):
    assert "google-meet-stage" in atoms["animated_beam"]["surfaces"]["works_on"]

def test_animated_beam_source_inspiration(atoms):
    assert "Magic UI" in atoms["animated_beam"]["source_inspiration"]["name"]

# ── encrypted_reveal ──────────────────────────────────────────────────────────

def test_encrypted_reveal_basic(renderer):
    html = r(renderer, {"component": "encrypted_reveal", "text": "HELLO"})
    assert "@keyframes" in html
    assert "HELLO" in html
    assert "steps(1" in html

def test_encrypted_reveal_final_frame_is_text(renderer):
    html = r(renderer, {"component": "encrypted_reveal", "text": "LOCKED"})
    assert '100%{content:"LOCKED"' in html

def test_encrypted_reveal_scramble_colour(renderer):
    html = r(renderer, {"component": "encrypted_reveal",
                        "text": "X", "scramble_color": "#ff00ff"})
    assert "#ff00ff" in html

def test_encrypted_reveal_frames_clamped(renderer):
    html = r(renderer, {"component": "encrypted_reveal", "text": "A", "frames": 50})
    # 20 frames max — count keyframe stops (each ends with %;)
    assert html.count("%;") <= 21

def test_encrypted_reveal_works_on_meet_stage(atoms):
    assert "google-meet-stage" in atoms["encrypted_reveal"]["surfaces"]["works_on"]

def test_encrypted_reveal_source_inspiration(atoms):
    assert "Magic UI" in atoms["encrypted_reveal"]["source_inspiration"]["name"]

# ── word_flip ─────────────────────────────────────────────────────────────────

def test_word_flip_basic(renderer):
    html = r(renderer, {"component": "word_flip",
                        "words": ["Retention", "Revenue", "Signups"]})
    assert "@keyframes" in html
    assert "Retention" in html
    assert "Revenue" in html
    assert "Signups" in html

def test_word_flip_cycles_n_plus_one_spans(renderer):
    html = r(renderer, {"component": "word_flip", "words": ["A", "B", "C"]})
    # N+1 spans for seamless loop: A, B, C, A
    assert html.count(">A<") == 2  # first word duplicated at end

def test_word_flip_prefix_suffix(renderer):
    html = r(renderer, {"component": "word_flip",
                        "words": ["X", "Y"], "prefix": "Scale your ", "suffix": " today"})
    assert "Scale your " in html
    assert " today" in html

def test_word_flip_steps_timing(renderer):
    html = r(renderer, {"component": "word_flip", "words": ["A", "B"]})
    assert "steps(2,end)" in html

def test_word_flip_gas_sidebar_surface(atoms):
    assert "google-apps-script-side-panel" in atoms["word_flip"]["surfaces"]["works_on"]

def test_word_flip_source_inspiration(atoms):
    assert "Magic UI" in atoms["word_flip"]["source_inspiration"]["name"]

# ── sonar_pulse ───────────────────────────────────────────────────────────────

def test_sonar_pulse_basic(renderer):
    html = r(renderer, {"component": "sonar_pulse"})
    assert "@keyframes" in html
    assert "border-radius:50%" in html

def test_sonar_pulse_three_rings(renderer):
    html = r(renderer, {"component": "sonar_pulse", "variant": "info"})
    assert html.count("animation-delay" if "animation-delay" in html else "infinite") >= 1
    # Three rings with staggered delays 0s, 1s, 2s
    assert "0s infinite" in html
    assert "1s infinite" in html
    assert "2s infinite" in html

def test_sonar_pulse_variants(renderer):
    for variant, expected in [("critical", "ef4444"), ("success", "34d399"),
                               ("info", "38bdf8"), ("warning", "f59e0b")]:
        html = r(renderer, {"component": "sonar_pulse", "variant": variant})
        assert expected in html, f"{variant} colour missing"

def test_sonar_pulse_inactive(renderer):
    html = r(renderer, {"component": "sonar_pulse", "active": False})
    assert "@keyframes" not in html

def test_sonar_pulse_label(renderer):
    html = r(renderer, {"component": "sonar_pulse", "label": "LIVE", "active": True})
    assert "LIVE" in html

def test_sonar_pulse_gas_sidebar_surface(atoms):
    assert "google-apps-script-side-panel" in atoms["sonar_pulse"]["surfaces"]["works_on"]

# ── progress_circle (proper SVG implementation) ───────────────────────────────

def test_progress_circle_renders_svg(renderer):
    html = r(renderer, {"component": "progress_circle", "value": 75})
    assert "<svg" in html
    assert "stroke-dashoffset" in html
    assert "75%" in html

def test_progress_circle_animates_on_mount(renderer):
    html = r(renderer, {"component": "progress_circle", "value": 50})
    assert "@keyframes" in html
    assert "ease-out" in html

def test_progress_circle_value_clamped(renderer):
    html_over = r(renderer, {"component": "progress_circle", "value": 150})
    assert "100%" in html_over
    html_under = r(renderer, {"component": "progress_circle", "value": -10})
    assert "0%" in html_under

def test_progress_circle_label(renderer):
    html = r(renderer, {"component": "progress_circle", "value": 60, "label": "Syncing"})
    assert "Syncing" in html

def test_progress_circle_custom_color(renderer):
    html = r(renderer, {"component": "progress_circle", "value": 40, "color": "#f59e0b"})
    assert "#f59e0b" in html

def test_progress_circle_gas_sidebar_surface(atoms):
    assert "google-apps-script-side-panel" in atoms["progress_circle"]["surfaces"]["works_on"]

# ── gas-sidebar surface backfill ──────────────────────────────────────────────

def test_blur_fade_in_gas_sidebar_degraded(atoms):
    surfaces = atoms["blur_fade_in"]["surfaces"]
    degraded_surfaces = [d["surface"] for d in surfaces.get("degraded_on", [])]
    assert "google-apps-script-side-panel" in degraded_surfaces

def test_glow_button_gas_sidebar_works(atoms):
    assert "google-apps-script-side-panel" in atoms["glow_button"]["surfaces"]["works_on"]

def test_animated_beam_gas_sidebar_degraded(atoms):
    surfaces = atoms["animated_beam"]["surfaces"]
    degraded_surfaces = [d["surface"] for d in surfaces.get("degraded_on", [])]
    assert "google-apps-script-side-panel" in degraded_surfaces

def test_typewriter_text_gas_sidebar_works(atoms):
    assert "google-apps-script-side-panel" in atoms["typewriter_text"]["surfaces"]["works_on"]

# ── stepper ───────────────────────────────────────────────────────────────────

def test_stepper_basic(renderer):
    html = r(renderer, {"component": "stepper",
                        "steps": ["Parse", "Validate", "Publish"],
                        "active_index": 1})
    assert "Parse" in html
    assert "Validate" in html
    assert "Publish" in html

def test_stepper_completed_draws_checkmark(renderer):
    html = r(renderer, {"component": "stepper",
                        "steps": ["Done", "Active", "Next"],
                        "active_index": 1})
    # Completed step gets SVG check path animation
    assert "M4,10 L8,14 L16,6" in html

def test_stepper_active_pulses(renderer):
    html = r(renderer, {"component": "stepper",
                        "steps": ["A", "B", "C"],
                        "active_index": 1})
    # Active step gets sonar-style keyframe
    assert "@keyframes asp_" in html

def test_stepper_pending_no_animation(renderer):
    html = r(renderer, {"component": "stepper",
                        "steps": ["A", "B", "C"],
                        "active_index": 0})
    # Only one completed step possible; pending steps have muted dot
    assert "475569" in html  # pending indicator colour

def test_stepper_legacy_contract(renderer):
    html = r(renderer, {"component": "stepper", "steps": [
        {"label": "Step 1", "is_completed": True,  "is_current": False},
        {"label": "Step 2", "is_completed": False, "is_current": True},
        {"label": "Step 3", "is_completed": False, "is_current": False},
    ]})
    assert "Step 1" in html
    assert "Step 2" in html
    assert "@keyframes asp_" in html  # active pulse present

def test_stepper_heading(renderer):
    html = r(renderer, {"component": "stepper",
                        "steps": ["A"], "label": "Pipeline"})
    assert "Pipeline" in html

def test_stepper_gas_sidebar_surface(atoms):
    assert "google-apps-script-side-panel" in atoms["stepper"]["surfaces"]["works_on"]

# ── code_diff ─────────────────────────────────────────────────────────────────

def test_code_diff_basic(renderer):
    html = r(renderer, {"component": "code_diff",
                        "old_code": "x = 1\ny = 2",
                        "new_code": "x = 1\ny = 3"})
    assert "6ee7b7" in html   # addition colour
    assert "fca5a5" in html   # removal colour

def test_code_diff_added_line_marker(renderer):
    html = r(renderer, {"component": "code_diff",
                        "old_code": "a", "new_code": "a\nb"})
    assert "+ b" in html

def test_code_diff_removed_line_marker(renderer):
    html = r(renderer, {"component": "code_diff",
                        "old_code": "a\nb", "new_code": "a"})
    assert "- b" in html

def test_code_diff_label_and_language(renderer):
    html = r(renderer, {"component": "code_diff",
                        "old_code": "", "new_code": "",
                        "label": "schema.py", "language": "python"})
    assert "schema.py" in html
    assert "python" in html

def test_code_diff_no_line_numbers(renderer):
    html = r(renderer, {"component": "code_diff",
                        "old_code": "a", "new_code": "b",
                        "show_line_numbers": False})
    # line number spans use user-select:none — absent when disabled
    assert "user-select:none" not in html

def test_code_diff_old_text_alias(renderer):
    # old_text / new_text are aliases for old_code / new_code
    html = r(renderer, {"component": "code_diff",
                        "old_text": "foo", "new_text": "bar"})
    assert "fca5a5" in html or "6ee7b7" in html  # some diff rendered

def test_code_diff_gas_sidebar_surface(atoms):
    assert "google-apps-script-side-panel" in atoms["code_diff"]["surfaces"]["works_on"]
