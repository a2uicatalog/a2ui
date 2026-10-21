"""Python twins of atoms that used to exist only in the GAS renderer (2026-10-12).

Rule (Curtis): an atom may be GAS-only only if it is technically possible or relevant only on Apps Script. Everything else needs a Python twin in
renderers/web_article.py that matches the GAS output byte for byte. This file holds that line:

* TWINNED: each atom here renders the same HTML in both renderers for its example AND for a fuzz of that example, where every leaf field in turn is
  replaced by null, numbers, booleans, empty and huge strings, arrays, objects and attack text (so JavaScript's truthiness and coercion rules are matched).
* GAS_ONLY: the atoms that stay GAS-only, each with the reason. A new GAS-only atom has to be added here with a reason, or the ratchet test fails.
"""
from __future__ import annotations

import copy
import glob
import re
from pathlib import Path

import pytest

from test_motion_atoms import _node, _norm, _py, core_js  # noqa: F401  (core_js is a fixture)
import generate_atom_pages as g
import web_article as _wa
_if_s = _wa._gx_esc

ROOT = Path(__file__).parent.parent
def _gas_batch(core_js, blocks):
    """The GAS renderer without its accessibility post-pass (_a11yFix): the web renderer has no twin of that cross-cutting step yet, so atoms are compared before it."""
    import json
    return _node(core_js, "_a11yFix = function(h) { return h; }; var B = " + json.dumps(blocks) + "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")


ATTACK = '"><img src=x onerror=alert(1)><script>alert(2)</script>\'`${x}'

# Random element ids the GAS renderers mint (Math.random) or the Python twins derive; both are replaced by a fixed word before comparing.
UID8 = ("hub", "hrail", "fcd", "txa", "btl", "bau", "cpv", "dbr")                       # prefix + 8 characters
UID6 = ("tg", "mt", "mo", "fl", "ta", "lg", "ql", "tl", "tt", "pg", "ps", "dp", "stw", "sc_", "cs_")   # prefix + 6 characters


# take_away_card is styled differently in the web renderer and in GAS (an older, separate difference); atoms that embed it are compared around it
_CARD_RE = re.compile(r'(<div style="margin-bottom:14px;">).*?(?=<div style="(?:border-left:3px solid|font-size:0.78rem;font-style:italic))', re.S)


def _norm_ids(h: str, around_cards: bool = False) -> str:
    h = _norm(h)
    if around_cards:
        h = _CARD_RE.sub(r'\1[CARD]', h)
    h = re.sub(r'\b(' + '|'.join(UID8) + r')[a-z0-9]{8}', r'\1UID', h)
    return re.sub(r'\b(' + '|'.join(UID6) + r')[a-z0-9]{6}', r'\1UID', h)


# atoms with no Python (web article) twin, each with the reason: technically possible or relevant only on Apps Script, or declared not served on `web` in the schema
GAS_ONLY = {
    "atc_vectoring": "a real-time canvas game has no static-article rendering; schema declares no `web` surface; served on mcp-apps and android through the bundle",
    "csv_import": "writes the file into a Google Sheet through google.script.run",
    "sheet_badge": "opens the backing Google Sheet through google.script.run",
    "live_refresh": "re-runs a server action on an interval through google.script.run",
    "presence_surface": "presence heartbeat to the Apps Script server",
    "presence_bar": "shell filled by the Apps Script presence heartbeat (data-a2ui-presence)",
    "me": "shows the signed-in Workspace user; the shell fills it from Session",
    "meet_button": "creates a Google Meet through the Calendar service",
    "chat_space_button": "creates a Google Chat space through the Chat service",
    "chat_send_button": "posts to a Chat webhook held in Script Properties",
    "chat_card": "body and footer are filled by the Apps Script shell (data-cc-body, data-cc-foot)",
    "people_picker": "searches the Workspace directory through google.script.run",
    "file_upload": "uploads to the Apps Script endpoint and extracts text server-side",
    "photo_upload": "multipart upload to the Apps Script endpoint",
    "fids_board": "live airport feed fetched through google.script.run",
    "gemini_handoff": "fetches the published prompt with UrlFetch and encodes it with Utilities at render time",
}


def _gas_renderer_names() -> set:
    names = set()
    for f in glob.glob(str(ROOT / "apps-script-surface/gas-wired-renderer/*.gs")):
        names |= set(re.findall(r"_RENDERERS\['([a-z0-9_]+)'\]\s*=", Path(f).read_text()))
    return names


def test_every_gas_only_atom_is_named_with_a_reason():
    import web_article as w
    only = sorted(_gas_renderer_names() - set(w._RENDERERS))
    unexplained = [t for t in only if t not in GAS_ONLY]
    assert not unexplained, f"GAS-only atoms with no reason (give them a Python twin, or add them to GAS_ONLY here): {unexplained}"
    stale = [t for t in GAS_ONLY if t not in only]
    assert not stale, f"listed as GAS-only but a Python twin exists now: {stale}"


def _leaves(v, path=()):
    if isinstance(v, dict):
        for k, x in v.items():
            if k != "type":
                yield from _leaves(x, path + (k,))
    elif isinstance(v, list):
        for i, x in enumerate(v[:3]):
            yield from _leaves(x, path + (i,))
    else:
        yield path


def _set(v, path, val):
    v = copy.deepcopy(v)
    cur = v
    for p in path[:-1]:
        cur = cur[p]
    cur[path[-1]] = val
    return v


ALTS = [None, 0, 1, -1, 1.5, True, False, "", " ", "x", "x" * 300, ATTACK, [], ["a", 1, None], {}, {"k": "v"}, "javascript:alert(1)", "#fff", 99999999999, "12"]


def variants(block, limit=400):
    out = [block, {"type": block["type"]}]
    for path in _leaves(block):
        for alt in ALTS:
            out.append(_set(block, path, alt))
    # top-level fields removed one at a time
    for k in list(block):
        if k != "type":
            b = copy.deepcopy(block)
            del b[k]
            out.append(b)
    return out[:limit]


def _t(**kw):
    return kw


EXAMPLES: dict = {
    "headline_list": [{"type": "headline_list", "title": "Top", "accent": "#4f46e5", "items": [{"rank": 1, "title": "A", "source": "S", "time": "1h", "tag": "T", "url": "https://x.y"}, {"title": "B"}]}],
    "breaking_banner": [{"type": "breaking_banner", "label": "BREAKING", "title": "T", "summary": "s", "source": "S", "time": "now", "accent": "#ef4444"}],
    "news_digest": [{"type": "news_digest", "title": "Digest", "accent": "#4f46e5", "items": [{"title": "a", "body": "b", "tag": "t", "source": "s"}, {"title": "c"}]}],
    "cert_disclaimer": [{"type": "cert_disclaimer", "cert": "TOGAF", "holder": "The Open Group", "url": "https://x.y"}],
    "command_step": [{"type": "command_step", "command": "npm i", "label": "Install", "hint": "h", "done": False}, {"type": "command_step", "command": "x", "done": True}],
    "jump_nav": [{"type": "jump_nav", "links": [{"label": "A", "target": "a"}, {"label": "B", "target": "b"}]}],
    "scenario_case": [{"type": "scenario_case", "id": "s1", "domain": "D", "difficulty": "hard", "scenario": "S", "question": "Q", "options": [{"id": "a", "text": "x", "score": 2}, {"text": "y", "score": 1}, {"text": "z", "score": 0}], "rationale": "R"}],
    "sla_timer_display": [{"type": "sla_timer_display", "title": "T", "severity": "P1", "sla_label": "3 min", "elapsed_fmt": "1m", "sla_state": "warn", "pct": 42.5}],
    "lens_quotes": [{"type": "lens_quotes", "items": [{"quote": "**bold** and [l](https://x.y) *i*", "context": "c"}]}],
    "lens_structure": [{"type": "lens_structure", "items": [{"heading": "H", "quote": "q *i*"}]}],
    "lens_themes": [{"type": "lens_themes", "source_excerpt": "alpha beta gamma", "items": [{"label": "a", "weight": 0.2, "evidence": "alpha"}, {"label": "b", "weight": 0.9, "evidence": "zzz"}, {"label": "c"}]}],
    "lens_eli5": [{"type": "lens_eli5", "source_excerpt": "alpha beta", "text": "t **b**", "evidence": ["alpha", "nope"]}],
    "toulmin_argument": [{"type": "toulmin_argument", "title": "Why: extend the trial", "source_excerpt": "In the pilot, teams that switched to a four-day week shipped 12 of 14 planned releases. Two teams missed deadlines during the first month while handovers settled. Results may not hold for teams that carry on-call duty.", "claim": "Extend the four-day week to every product team", "qualifier": "probably", "grounds": [{"quote": "teams that switched to a four-day week shipped 12 of 14 planned releases", "text": "Delivery held up in the pilot", "source": "Pilot memo, results"}, {"quote": "Two teams missed deadlines during the first month", "text": "The cost came early and passed"}], "warrant": "a pilot that kept delivery steady for most teams predicts the same for the rest", "backing": "One pilot, 14 planned releases, no comparison group", "rebuttals": [{"text": "the team carries on-call duty, where the memo says results may not hold", "applies": False}]}, {"type": "toulmin_argument", "claim": "c", "grounds": [{"quote": "not in it"}, None, 5, "s", {"text": "t"}], "rebuttals": [{"text": "r", "applies": True}, None, {"applies": 1}]}, {"type": "toulmin_argument"}, {"type": "toulmin_argument", "claim": "c", "source_excerpt": "abc", "grounds": [{"quote": "b"}], "warrant": "w", "backing": "k", "qualifier": "q", "rebuttals": []}],
    "lens_synthesis": [{"type": "lens_synthesis", "source_excerpt": "alpha", "points": [{"point": "p", "evidence": "alpha"}, {"point": "q"}]}],
    "lens_freeform": [{"type": "lens_freeform", "tier": "extracted", "source_excerpt": "alpha", "label": "L", "text": "t", "evidence": ["alpha"]}],
    "lens_similar": [{"type": "lens_similar", "verified": False, "items": [{"title": "t", "why": "w", "retrieved": True, "url": "https://x.y"}, {"title": "u", "why": "v"}]}],
    "lens_context": [{"type": "lens_context", "items": [{"label": "l", "note": "n", "retrieved": True, "url": "https://x.y"}, {"label": "m"}]}],
    "quiet_link": [{"type": "quiet_link", "text": "Skip"}],
    "tool_tile": [{"type": "tool_tile", "icon": "bolt", "label": "Go", "count": 3, "variant": "violet_magenta", "badge": "New"}, {"type": "tool_tile", "icon": "x", "label": "G"}],
    "theme_toggle": [{"type": "theme_toggle", "initial": "dark", "position": "top-right", "label_dark": "D", "label_light": "L", "dark_bg": "#000", "persist_to": "x", "persist_action": "y"}],
    "tab_group": [{"type": "tab_group", "options": [{"value": "a", "label": "A"}, {"value": "b", "label": "B", "selected": True}], "panels": {"a": "pa", "b": "pb", "2": "p2", "1": "p1"}, "target": "t"}],
    "lens_grid": [{"type": "lens_grid", "options": [{"value": "a", "label": "A", "caption": "c"}, {"value": "b", "label": "B"}], "target": "t", "columns": 2, "gap": 8, "selected": "b"}],
    "domain_picker": [{"type": "domain_picker", "target": "t", "default_option": {"label": "Mine"}, "free_entry": {"placeholder": "ph"}, "default_domains": "a,b"}],
    "standings_table": [{"type": "standings_table", "primary_label": "PTS", "columns": ["W", "L"], "rows": [{"name": "A", "played": 3, "primary": 9, "values": [3, 0], "highlight": "leader"}, {"name": "B", "primary": 4, "values": [1]}]}, {"type": "standings_table", "wired": True}],
    "match_schedule": [{"type": "match_schedule", "layout": "cards", "rounds": [{"label": "R1", "matches": [{"court": "C1", "team_a": ["a", "b"], "team_b": ["c", "d"], "score_a": 3, "score_b": 2}, {"team_a": ["e"], "team_b": ["f"]}]}]},
                       {"type": "match_schedule", "rounds": [{"label": "R1", "matches": [{"court": "C1", "team_a": ["a", "b"], "team_b": ["c", "d"], "score_a": 3, "score_b": 2}, {"team_a": ["e"], "team_b": ["f"]}]}, {"matches": [{"court": "C2", "team_a": ["x"], "team_b": ["y"]}]}]}],
    "domain_brief": [{"type": "domain_brief", "title": "T", "badge": "b", "accent": "#4f46e5", "description": "d\nd2", "key_facts": ["f", {"icon": "x", "text": "g"}], "areas": [{"label": "l", "color": "#00ff00", "detail": "d"}], "areas_label": "A", "context": "c", "image_url": "https://x.y/i.png"}],
    "brevet_timeline": [{"type": "brevet_timeline", "title": "T", "accent": "#3b82f6", "events": [{"date": "1914", "title": "t", "desc": "d\ne"}]}],
    "text_analysis": [{"type": "text_analysis", "passage": "The quick brown fox.\nSecond", "source": "S", "highlights": [{"text": "quick", "analysis": "a<b>"}, {"text": "fox", "analysis": "b"}]}],
    "brevet_automatismes": [{"type": "brevet_automatismes", "questions": [{"question": "1+1", "answer": "2"}, {"question": "2+2", "answer": 4}], "duration": 600}],
    "catalogue_provenance": [{"type": "catalogue_provenance", "label": "L", "sources": [{"icon": "x", "what": "w", "catalogue": "a2ui", "target": "t"}, {"what": "x", "catalogue": "zz", "color": "#123456"}]}],
    "hub": [{"type": "hub", "background": "#0f172a", "nav_background": "#111111", "header": {"url": "https://x.y", "author": "A", "published": "2026"}, "subjects": [{"label": "S1", "color": "#4f46e5", "slides": [{"label": "a", "blocks": [{"type": "quiet_link", "text": "x"}]}, {"label": "b", "blocks": []}]}, {"label": "S2", "slides": [{"blocks": [{"type": "cert_disclaimer", "cert": "C", "holder": "H"}]}]}]}],
    "hub_rail": [{"type": "hub_rail", "background": "#0f172a", "header": {"url": "https://x.y", "author": "A"}, "subjects": [{"label": "S1", "color": "#4f46e5", "slides": [{"label": "a", "blocks": [{"type": "quiet_link", "text": "x"}]}, {"label": "b", "blocks": []}]}, {"label": "S2", "slides": [{"blocks": [{"type": "cert_disclaimer", "cert": "C", "holder": "H"}]}]}]}],
    "flashcard_deck": [{"type": "flashcard_deck", "cards": [{"front": "f\n1", "back": "b"}, {"front": "f2", "back": "b2"}], "accent": "#4f46e5", "label_front": "Q", "label_back": "A"}],
    "filterable_list": [{"type": "filterable_list", "title": "T", "items": [{"title": "a", "detail": "d", "status": "Open", "icon": "x", "meta": "m"}, {"name": "b", "status": "Done"}, {"title": "c", "status": "open"}], "filters": [{"value": "open", "label": "Open", "color": "#ffffff"}, "Done"], "colors": {"Done": "#00aa00"}, "empty_text": "none"},
                        {"type": "filterable_list", "filter_field": "kind", "show_counts": False, "items": [{"title": "a", "kind": "x"}, {"title": "b", "kind": "y"}]}],
    "photo_grid": [{"type": "photo_grid", "cols": 3, "images": [{"id": 1, "url": "https://x.y/a.jpg", "alt": "a", "caption": "c", "badge": "b", "active": True}, {"id": 2}]}],
    "photo_stepper": [{"type": "photo_stepper", "accent": "#0f766e", "trigger_label": "Browse", "images": [{"id": "1", "url": "https://x.y/a.jpg", "name": "n", "price_display": "1", "starred_by_display": "A", "source_url": "https://x.y", "active": True, "badge": "b"}, {"id": "2", "alt": "a"}]}],
    "sortable_list": [{"type": "sortable_list", "label": "L", "items": [{"id": "a", "label": "A", "note": "n", "group": "g", "order": 2}, {"id": "b"}, {"label": "c"}], "emptyMessage": "e"}],
    "preview_frame": [{"type": "preview_frame", "src": "https://x.y", "height": 200, "label": "L", "emptyMessage": "e"}],
    "motion_capsule": [{"type": "motion_capsule", "text": "don't have resources", "style": "outline", "resolve": "blur"}, {"type": "motion_capsule", "text": "We ship fast today", "style": "glass", "resolve": "scramble", "size": 30, "tone": "dark", "seed": 9}, {"type": "motion_capsule", "style": "solid", "color": "#ff0000", "resolve": "fade"}],
    "motion_arrow": [{"type": "motion_arrow", "angles": [0, 90, 180], "size": 80, "weight": 4, "color": "#34e0c3", "inline": True, "label": "Next"}, {"type": "motion_arrow", "style": "solid"}],
    "motion_swatches": [{"type": "motion_swatches", "swatches": [{"name": "Indigo", "hex": "#475eff"}, {"name": "Mellow", "hex": "#f6cf77"}, {"name": "White", "hex": "#ffffff"}, {"name": "Black", "hex": "#111111"}], "layout": "grid", "gap": 2, "radius": 8}, {"type": "motion_swatches", "layout": "row", "swatches": [{"name": "A", "hex": "#ff0000"}, {"hex": "nope"}, {"name": "C"}]}],
    "motion_glass": [{"type": "motion_glass", "blur": 24, "tint": "#ffffff", "strength": 0.3, "radius": 20, "padding": 16, "edge": False, "blocks": [{"type": "quiet_link", "text": "x"}]}, {"type": "motion_glass", "blocks": [{"type": "cert_disclaimer", "holder": "H"}]}],
    "motion_wall": [{"type": "motion_wall", "cols": 4, "rows": 2, "seed": 11, "gap": 4, "radius": 6, "images": ["https://x.y/a.jpg", {"url": "https://x.y/b.jpg"}, "data:image/png;base64,AAAA", "http://bad"], "label": "Wall"}, {"type": "motion_wall"}],
    "motion_tag": [{"type": "motion_tag", "text": "tools", "from": {"x": 10, "y": 20}, "to": {"x": 60, "y": 55}, "tone": "accent", "accent": "#34e0c3", "size": 24}, {"type": "motion_tag", "tone": "light"}],
    "motion_ring": [{"type": "motion_ring", "text": "Reel 2026", "size": 400, "turns": 2, "disc": 50, "fill": "#2f7d63", "color": "#ffffff", "weight": "black", "font_size": 14, "image": "https://x.y/a.jpg"}, {"type": "motion_ring", "text": "NO OK"}],
    "motion_highlight": [{"type": "motion_highlight", "text": "made tidy", "style": "marker", "color": "#ffe94a", "size": 56}, {"type": "motion_highlight", "text": "x", "style": "underline", "ink": "#111111"}, {"type": "motion_highlight", "style": "strike"}],
    "motion_meters": [{"type": "motion_meters", "bars": 10, "rows": 8, "seed": 5, "cycles": 3, "gap": 4, "height": 160, "colors": ["#ff5ea8", "#34e0c3", "bad"], "label": "Level", "blocks": [{"type": "quiet_link", "text": "LOGO"}]}, {"type": "motion_meters", "layout": "row"}],
    "motion_discs": [{"type": "motion_discs", "discs": [{"color": "#f4d21f", "r": 26}, {"color": "#2e6fbd", "r": 22}, {"color": "#e63950"}], "overlap": 14, "aspect": 2, "label": "Discs"}, {"type": "motion_discs", "blend": False}],
    "motion_dotgrid": [{"type": "motion_dotgrid", "cols": 5, "rows": 4, "seed": 4}, {"type": "motion_dotgrid", "cols": 6, "rows": 3, "hops": [[0, 0], [2, 2], [4, 0], [5, 2]], "accent": "#2563eb", "color": "#d9e2ff", "dot": 60, "aspect": 2, "label": "Grid"}],
    "motion_blade": [{"type": "motion_blade", "text": "the neutral smart kitchen", "size": 40}, {"type": "motion_blade", "text": "any recipe", "shape": "bar", "color": "#e11d48", "ink": "#111111"}, {"type": "motion_blade", "text": "x", "shape": "disc"}],
    "motion_blueprint": [{"type": "motion_blueprint", "text": "atelier", "size": 120, "guide": "#7c3aed", "weight": "black"}, {"type": "motion_blueprint", "text": "north", "lines": False, "color": "#2563eb"}],
    "motion_tracking": [{"type": "motion_tracking", "text": "Engineered for control", "size": 40, "from": 0, "to": 0.4}, {"type": "motion_tracking", "text": "COMPRESS", "from": 0.6, "to": 0, "weight": "black"}],
    "motion_tabs": [{"type": "motion_tabs", "items": ["Storyboarding", "Progress", "Animation", "Delivery"], "size": 20}, {"type": "motion_tabs", "items": ["Brief", "Cut", "Ship"], "accent": "#e11d48", "color": "#111111"}],
    "motion_foil": [{"type": "motion_foil", "text": "GOLD STANDARD"}, {"type": "motion_foil", "text": "Chrome", "look": "holo", "direction": "diagonal", "bands": 3, "width": 20, "sheen": "#ffeeaa", "size": 90, "font": "serif", "align": "start"}, {"type": "motion_foil", "text": "up", "look": "oil", "direction": "up", "bands": 2}],
    "motion_wrap": [{"type": "motion_wrap", "text": "Around the world"}, {"type": "motion_wrap", "text": "WHEEL", "form": "wheel", "radius": 180, "turns": -2}, {"type": "motion_wrap", "text": "helix", "form": "helix", "arc": 200, "lean": 20}, {"type": "motion_wrap", "text": "ribbon", "form": "ribbon", "arc": 120, "size": 40}],
    "motion_drop": [{"type": "motion_drop", "text": "Bounce"}, {"type": "motion_drop", "text": "spring", "mode": "spring", "order": "centre", "bounces": 5}, {"type": "motion_drop", "text": "rain it", "mode": "rain", "order": "random", "seed": 9}, {"type": "motion_drop", "text": "pile", "mode": "pile", "order": "reverse"}, {"type": "motion_drop", "text": "rise", "mode": "rise"}, {"type": "motion_drop", "text": "swing", "mode": "swing", "height": 40}],
    "motion_flag": [{"type": "motion_flag", "text": "Wave the flag"}, {"type": "motion_flag", "text": "ripple", "mode": "ripple", "amp": 30, "waves": 4, "shade": False}, {"type": "motion_flag", "text": "ribbon", "mode": "ribbon", "pin": "right"}, {"type": "motion_flag", "text": "breeze", "mode": "breeze", "cycles": 5}],
    "motion_disperse": [{"type": "motion_disperse", "text": "Goodbye"}, {"type": "motion_disperse", "text": "shatter", "mode": "shatter", "order": "random"}, {"type": "motion_disperse", "text": "rise", "mode": "rise"}, {"type": "motion_disperse", "text": "sink", "mode": "sink"}, {"type": "motion_disperse", "text": "implode", "mode": "implode", "order": "centre"}, {"type": "motion_disperse", "text": "explode", "mode": "explode", "distance": 200}, {"type": "motion_disperse", "text": "wind", "mode": "wind"}, {"type": "motion_disperse", "text": "evap", "mode": "evaporate", "order": "reverse"}],
    "motion_reveal": [{"type": "motion_reveal", "text": "Blinds"}, {"type": "motion_reveal", "text": "slats\nand lines", "mode": "slats", "slats": 12}, {"type": "motion_reveal", "text": "iris", "mode": "iris", "feather": 30}, {"type": "motion_reveal", "text": "diamond", "mode": "diamond"}, {"type": "motion_reveal", "text": "clock", "mode": "clock"}, {"type": "motion_reveal", "text": "halftone", "mode": "halftone", "slats": 14}, {"type": "motion_reveal", "text": "light", "mode": "searchlight"}, {"type": "motion_reveal", "text": "laser", "mode": "laser", "line": "#ff3366"}, {"type": "motion_reveal", "text": "soft", "mode": "soft", "feather": 0}, {"type": "motion_reveal", "text": "diag", "mode": "diagonal"}],
    "motion_streak": [{"type": "motion_streak", "text": "WHIP IN"}, {"type": "motion_streak", "text": "right", "direction": "right", "ghosts": 9, "distance": 3.5, "tint": "#34e0c3"}, {"type": "motion_streak", "text": "up", "direction": "up"}, {"type": "motion_streak", "text": "down", "direction": "down", "ghosts": 2}, {"type": "motion_streak", "text": "diag", "direction": "diagonal", "distance": 12.25}],
    "motion_selection": [{"type": "motion_selection", "text": "Your headline here."}, {"type": "motion_selection", "text": "x", "toolbar": ["B", "Link"], "handles": False, "tint": False, "color": "#e11d48"}, {"type": "motion_selection", "blocks": [{"type": "motion_pill", "text": "Go"}], "toolbar": []}],
    "form_textarea": [{"type": "form_textarea", "label": "L", "placeholder": "p", "value": "v", "rows": 6}, {"type": "form_textarea", "placeholder": "only"}],
}


def _examples(t):
    out = [copy.deepcopy(e) for e in EXAMPLES.get(t, [])]
    if t in g._EXAMPLE_BLOCKS and t not in ('hub', 'hub_rail'):   # their schema examples nest a heading, which the two renderers style differently (a separate, older difference)
        out.append(copy.deepcopy(g._EXAMPLE_BLOCKS[t]))
    return out


TWINNED = set(EXAMPLES)


@pytest.mark.parametrize("atom", sorted(TWINNED))
def test_twin_matches_gas_for_the_examples_and_a_fuzz_of_them(core_js, atom):
    cases = [c for ex in _examples(atom) for c in variants(ex)]
    if atom == 'text_analysis':   # GAS replaces the first match inside markup it has already built, so a highlight like 'x' or '1' lands in a generated class name
        probe = '<span class="txahl" data-idx="0" style="background:rgba(217,119,6,0.18);border-bottom:2px solid #d97706;cursor:pointer;padding:0 2px;border-radius:2px;transition:background 0.15s;">'
        cases = [c for c in cases if not any(_if_s(h.get('text') if isinstance(h, dict) else '') in probe for h in (c.get('highlights') if isinstance(c.get('highlights'), list) else [])  if (h.get('text') if isinstance(h, dict) else None) not in (None, ''))]
    got = _gas_batch(core_js, cases)
    bad = []
    for i, (c, gh) in enumerate(zip(cases, got)):
        if "Error rendering <strong>" in gh:
            try:
                _py(c)
            except Exception:  # noqa: BLE001 - the twin must fail where GAS fails; the message text is V8's
                continue
            bad.append((i, "GAS threw, the twin did not", str(c)[:140]))
            continue
        try:
            mine = _py(c)
        except Exception as e:  # noqa: BLE001
            bad.append((i, "the twin threw: %r" % (e,), str(c)[:140]))
            continue
        if _norm_ids(mine, atom == 'lens_synthesis') != _norm_ids(gh, atom == 'lens_synthesis'):
            bad.append((i, "differs", str(c)[:140]))
    assert not bad, (atom, len(bad), bad[:3])


def test_text_analysis_notes_are_text_not_markup(core_js):
    """The note shown when an excerpt is tapped used to be inserted as raw HTML in both renderers."""
    att = '<img src=x onerror=alert(1)><script>alert(2)</script>'
    block = {"type": "text_analysis", "passage": "quick fox", "highlights": [{"text": "quick", "analysis": att + "\nsecond"}]}
    for html in (_py(block), _gas_batch(core_js, [block])[0]):
        assert "<img" not in html and "<script>alert" not in html, html[:300]
        assert "&lt;img src=x onerror=alert(1)&gt;" in html and "<br>second" in html
