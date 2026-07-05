#!/usr/bin/env python3
"""verify_chat_surface.py — independent Level-1 oracle for the google-chat surface.

The renderer is NOT allowed to be its own judge. This module encodes Google's
Cards v2 contract (allowed widgets, allowed fields per widget, required fields,
the knownIcon enum) from the public API reference — independent of anything in
renderers/googlechat.py — and validates our rendered output against it.

It catches the class of bug the "44" claim hid:
  - unknown fields on a widget/chip/button   (e.g. badge_group's `labelType`)
  - invalid knownIcon values                 (e.g. callout's INFO/WARNING/ERROR)
  - unknown widget types, missing required fields

Run:  python3 scripts/verify_chat_surface.py            # full report
      python3 scripts/verify_chat_surface.py --json     # machine-readable truth column
Exit non-zero if any atom's rendered output violates the contract.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'renderers'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from renderers import googlechat  # noqa: E402

# ── Google Cards v2 contract (from developers.google.com/chat/api/reference/rest/v1/cards) ──
# Field sets are the union of documented properties; we flag anything outside them.

KNOWN_ICONS = {
    "AIRPLANE", "BOOKMARK", "BUS", "CAR", "CLOCK", "CONFIRMATION_NUMBER_ICON",
    "DOLLAR", "DESCRIPTION", "EMAIL", "EVENT_SEAT", "FLIGHT_ARRIVAL",
    "FLIGHT_DEPARTURE", "HOTEL", "HOTEL_ROOM_TYPE", "INVITE", "MAP_PIN",
    "MEMBERSHIP", "MULTIPLE_PEOPLE", "OFFER", "PERSON", "PHONE",
    "RESTAURANT_ICON", "SHOPPING_CART", "STAR", "STORE", "TICKET", "TRAIN",
    "VIDEO_CAMERA", "VIDEO_PLAY",
}

WIDGETS = {
    "textParagraph": {"text", "maxLines"},
    "decoratedText": {"text", "topLabel", "bottomLabel", "startIcon", "endIcon",
                      "wrapText", "button", "switchControl", "onClick", "icon"},
    "image":         {"imageUrl", "altText", "onClick"},
    "divider":       set(),
    "buttonList":    {"buttons"},
    "chipList":      {"chips", "layout"},
    "grid":          {"title", "columnCount", "items", "borderStyle", "onClick"},
    "columns":       {"columnItems"},
}
REQUIRED = {
    "textParagraph": {"text"}, "decoratedText": {"text"}, "image": {"imageUrl"},
    "buttonList": {"buttons"}, "chipList": {"chips"}, "grid": {"items"},
    "columns": {"columnItems"}, "divider": set(),
}
CHIP_FIELDS   = {"label", "icon", "onClick", "enabled", "disabled", "altText"}
BUTTON_FIELDS = {"text", "icon", "color", "onClick", "disabled", "altText", "type"}
ICON_FIELDS   = {"knownIcon", "iconUrl", "materialIcon", "altText", "imageType"}
SECTION_FIELDS = {"header", "widgets", "collapsible", "uncollapsibleWidgetsCount"}
COLUMN_ITEM_FIELDS = {"horizontalSizeStyle", "horizontalAlignment",
                      "verticalAlignment", "widgets"}


def _v(cond, msg, out):
    if not cond:
        out.append(msg)


def _check_icon(icon, where, out):
    extra = set(icon) - ICON_FIELDS
    _v(not extra, f"{where}: unknown icon field(s) {sorted(extra)}", out)
    if "knownIcon" in icon:
        _v(icon["knownIcon"] in KNOWN_ICONS,
           f"{where}: invalid knownIcon '{icon['knownIcon']}' (not in enum)", out)


def _check_widget(w, where, out):
    if not isinstance(w, dict) or len(w) != 1:
        _v(False, f"{where}: widget must be a single-key object, got {list(w)}", out)
        return
    wtype, body = next(iter(w.items()))
    if wtype not in WIDGETS:
        _v(False, f"{where}: unknown widget type '{wtype}'", out)
        return
    body = body or {}
    extra = set(body) - WIDGETS[wtype]
    _v(not extra, f"{where}.{wtype}: unknown field(s) {sorted(extra)}", out)
    missing = REQUIRED.get(wtype, set()) - set(body)
    _v(not missing, f"{where}.{wtype}: missing required {sorted(missing)}", out)
    # nested contracts
    for icf in ("startIcon", "endIcon", "icon"):
        if isinstance(body.get(icf), dict):
            _check_icon(body[icf], f"{where}.{wtype}.{icf}", out)
    for chip in body.get("chips", []) if wtype == "chipList" else []:
        ex = set(chip) - CHIP_FIELDS
        _v(not ex, f"{where}.chipList.chip: unknown field(s) {sorted(ex)}", out)
    for btn in body.get("buttons", []) if wtype == "buttonList" else []:
        ex = set(btn) - BUTTON_FIELDS
        _v(not ex, f"{where}.buttonList.button: unknown field(s) {sorted(ex)}", out)
    for ci in body.get("columnItems", []) if wtype == "columns" else []:
        ex = set(ci) - COLUMN_ITEM_FIELDS
        _v(not ex, f"{where}.columns.item: unknown field(s) {sorted(ex)}", out)
        for j, sw in enumerate(ci.get("widgets", [])):
            _check_widget(sw, f"{where}.columns.item.w[{j}]", out)


def validate_message(msg) -> list:
    """Return a list of contract violations for a Cards v2 message dict."""
    out = []
    cards = msg.get("cardsV2", [])
    _v(isinstance(cards, list) and cards, "message: cardsV2 missing/empty", out)
    for ci, entry in enumerate(cards):
        _v(set(entry) <= {"cardId", "card"}, f"cardsV2[{ci}]: unexpected keys", out)
        card = entry.get("card", {})
        for si, sec in enumerate(card.get("sections", [])):
            ex = set(sec) - SECTION_FIELDS
            _v(not ex, f"section[{si}]: unknown field(s) {sorted(ex)}", out)
            for wi, w in enumerate(sec.get("widgets", [])):
                _check_widget(w, f"s[{si}].w[{wi}]", out)
    return out


# ── Representative sample per Chat-native atom (the probe fixture) ─────────────
IMG = "https://picsum.photos/seed/a2ui/400/180"
SAMPLES = {
    "intro": {"series_label": "A2UI", "series_url": "https://a2uicatalog.ai", "continuation": "x.", "note": "n"},
    "body": {"text": "para **b** `c`"}, "heading": {"text": "H"}, "subheading": {"text": "S"},
    "quote": {"text": "q", "attribution": "a"}, "code": {"language": "py", "content": "x=1"},
    "bullet_list": {"items": [{"label": "L", "text": "t"}, {"text": "u"}]}, "divider": {},
    "image": {"url": IMG, "alt": "a", "caption": "c"},
    "image_pair": {"left": {"url": IMG, "caption": "b"}, "right": {"url": IMG, "caption": "a"}},
    "diagram": {"url": IMG, "alt": "d"},
    "repo_links": {"links": [{"label": "GH", "url": "https://x"}]},
    "closing": {"text": "end", "tags": ["a"]},
    "callout": {"kind": "info", "title": "T", "text": "x"},      # <- exercises info/warning/danger icons
    "table": {"headers": ["A", "B"], "rows": [[1, 2]], "caption": "c"},
    "key_value": {"title": "T", "items": [{"key": "k", "description": "d", "required": True}]},
    "steps": {"items": [{"label": "L", "text": "t"}]},
    "api_reference": {"name": "f()", "parameters": [{"key": "p", "description": "d"}]},
    "timeline": {"events": [{"date": "Jul", "label": "L", "text": "t"}]},
    "gallery": {"caption": "c", "images": [{"url": IMG, "caption": "one"}]},
    "pipeline": {"steps": ["a", "b"]},
    "stat_card": {"value": "9", "label": "L", "delta": "2", "is_up": True},
    "badge_group": {"title": "T", "badges": [{"text": "x", "color": "green"}]},
    "metric_delta": {"label": "L", "text": "t"}, "trend_indicator": {"label": "L", "text": "t"},
    "glossary_term": {"label": "L", "text": "t"}, "footnote": {"label": "1", "text": "t"},
    "pull_stat": {"label": "L", "text": "t"}, "audio_link": {"label": "L", "text": "t"},
    "document_link": {"label": "L", "text": "t"}, "image_with_caption": {"label": "L", "text": "t"},
    "action_required_card": {"label": "L", "text": "t"}, "pricing_tier_card": {"label": "L", "text": "t"},
    "pros_cons_list": {"label": "L", "text": "t"}, "rating_comparison": {"label": "L", "text": "t"},
    "entity_list": {"items": [{"name": "n", "subtitle": "s", "status": "st"}]},
    "model_card": {"name": "M", "provider": "P", "description": "d"},
    "conversation_snippet": {"user_label": "You", "user": "u", "ai_label": "AI", "response": "r"},
    "shortcut_legend": {"title": "T", "items": [{"keys": ["Cmd", "K"], "action": "a"}]},
    "rating_summary_bar": {"average": 4.7, "total": 12},
    "roadmap_card": {"title": "T", "description": "d"},
    "notification_stack": {"notifications": [{"title": "t", "body": "b"}]},
    "text_callout": {"text": "t"},
    "chat_thread": {"messages": [{"role": "user", "text": "u"},
                                 {"role": "assistant", "kind": "tool_call",
                                  "tool": {"name": "x", "status": "ok", "result": "r"}}]},
}


def run():
    from renderers.googlechat import RENDERERS
    results = {}
    for atom in RENDERERS:
        sample = dict(SAMPLES.get(atom, {}))
        sample["type"] = atom
        try:
            msg = googlechat.render([sample])
            violations = validate_message(msg)
        except Exception as e:  # a crash is itself a Level-1 failure
            violations = [f"renderer raised {type(e).__name__}: {e}"]
        results[atom] = violations
    return results


if __name__ == "__main__":
    results = run()
    valid = [a for a, v in results.items() if not v]
    invalid = {a: v for a, v in results.items() if v}
    if "--json" in sys.argv:
        print(json.dumps({"surface": "google-chat", "level": 1,
                          "valid": sorted(valid), "invalid": invalid}, indent=2))
    else:
        print(f"google-chat · Level-1 contract check · {len(results)} atoms probed\n")
        for atom in sorted(invalid):
            print(f"  ✗ {atom}")
            for msg in invalid[atom]:
                print(f"      {msg}")
        print(f"\n  VALID: {len(valid)}   INVALID: {len(invalid)}")
        if invalid:
            print(f"  → NOT honestly google-chat-compatible until fixed: {sorted(invalid)}")
    sys.exit(1 if invalid else 0)
