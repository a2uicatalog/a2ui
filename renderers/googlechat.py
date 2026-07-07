"""Google Chat cardsV2 renderer — block list → cardsV2 JSON.

Takes a list of typed block dicts (conforming to atoms/schema.yaml) and returns
a complete Google Chat message dict with cardsV2 format, ready to POST to a webhook.

Only renders atoms tagged works_on: googlechat in the schema.
Atoms tagged degraded_on: googlechat get best-effort cardsV2 approximations.
Atoms tagged incompatible_on: googlechat are skipped with a comment widget.
"""

from typing import List, Dict, Any
import re


# ── Helpers ───────────────────────────────────────────────────────────────────

def _md_to_chat(text: str) -> str:
    """Convert basic markdown to Google Chat textParagraph HTML subset.
    Chat supports: <b>, <i>, <s>, <u>, <a href>, <font color>, <br>.
    """
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`',       r'<font color="#1a73e8">\1</font>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def _text(text: str) -> Dict:
    return {"textParagraph": {"text": _md_to_chat(text)}}


def _divider() -> Dict:
    return {"divider": {}}


def _button(label: str, url: str = "", color: str = "") -> Dict:
    btn = {"text": label}
    if url:
        btn["onClick"] = {"openLink": {"url": url}}
    if color:
        btn["color"] = _hex_to_color(color)
    return btn


def _hex_to_color(hex_color: str) -> Dict:
    """Convert hex color to Google Chat RGBA dict."""
    h = hex_color.lstrip('#')
    if len(h) == 6:
        r, g, b = int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255
        return {"red": round(r, 3), "green": round(g, 3), "blue": round(b, 3), "alpha": 1.0}
    return {"red": 0, "green": 0, "blue": 0, "alpha": 1.0}


# ── Atom renderers ────────────────────────────────────────────────────────────

def _render_intro(b: dict) -> List[Dict]:
    parts = []
    if b.get("series_label") and b.get("series_url"):
        text = f'<i>In <a href="{b["series_url"]}">{b["series_label"]}</a>, {_md_to_chat(b.get("continuation", ""))}</i>'
        parts.append(_text(text))
    if b.get("note"):
        parts.append(_text(f'<i>{_md_to_chat(b["note"])}</i>'))
    return parts


def _render_body(b: dict) -> List[Dict]:
    paragraphs = b.get("text", "").strip().split("\n\n")
    return [_text(_md_to_chat(p.strip())) for p in paragraphs if p.strip()]


def _render_heading(b: dict) -> List[Dict]:
    return [_text(f'<b>{_md_to_chat(b.get("text", ""))}</b>')]


def _render_subheading(b: dict) -> List[Dict]:
    return [_text(f'<b>{_md_to_chat(b.get("text", ""))}</b>')]


def _render_quote(b: dict) -> List[Dict]:
    # Degraded: no blockquote in Chat — use italic with dash prefix
    text = f'<i>"{_md_to_chat(b.get("text", ""))}"</i>'
    if b.get("attribution"):
        text += f'<br/>— <b>{b["attribution"]}</b>'
    return [_text(text)]


def _render_code(b: dict) -> List[Dict]:
    # Degraded: no syntax highlighting — monospace via font tag
    lang = b.get("language", "")
    content = b.get("content", "").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
    label = f'<b><font color="#1a73e8">{lang}</font></b><br/>' if lang else ""
    return [_text(f'{label}<font color="#666">{content}</font>')]


def _render_bullet_list(b: dict) -> List[Dict]:
    items = b.get("items", [])
    lines = []
    for item in items:
        if item.get("label"):
            lines.append(f'• <b>{_md_to_chat(item["label"])}</b> {_md_to_chat(item.get("text", ""))}')
        else:
            lines.append(f'• {_md_to_chat(item.get("text", ""))}')
    return [_text("<br/>".join(lines))]


def _render_divider(b: dict) -> List[Dict]:
    return [_divider()]


def _render_image(b: dict) -> List[Dict]:
    widgets = [{"image": {"imageUrl": b.get("url", ""), "altText": b.get("alt", "")}}]
    if b.get("caption"):
        widgets.append(_text(f'<font color="#999"><i>{b["caption"]}</i></font>'))
    return widgets


def _render_image_pair(b: dict) -> List[Dict]:
    # Degraded: use columns widget for side-by-side
    left  = b.get("left",  {})
    right = b.get("right", {})
    widgets = [{
        "columns": {
            "columnItems": [
                {
                    "horizontalSizeStyle": "FILL_AVAILABLE_SPACE",
                    "widgets": [
                        {"image": {"imageUrl": left.get("url", ""), "altText": left.get("alt", "")}},
                        *([_text(f'<font color="#999"><i>{left["caption"]}</i></font>')] if left.get("caption") else [])
                    ]
                },
                {
                    "horizontalSizeStyle": "FILL_AVAILABLE_SPACE",
                    "widgets": [
                        {"image": {"imageUrl": right.get("url", ""), "altText": right.get("alt", "")}},
                        *([_text(f'<font color="#999"><i>{right["caption"]}</i></font>')] if right.get("caption") else [])
                    ]
                }
            ]
        }
    }]
    return widgets


def _render_repo_links(b: dict) -> List[Dict]:
    buttons = [_button(l["label"], l.get("url", "")) for l in b.get("links", [])]
    return [{"buttonList": {"buttons": buttons}}]


def _render_closing(b: dict) -> List[Dict]:
    widgets = [_text(_md_to_chat(b.get("text", "")))]
    tags = b.get("tags", [])
    if tags:
        widgets.append(_text(f'<font color="#999">{" ".join("#" + t for t in tags)}</font>'))
    return widgets


def _render_callout(b: dict) -> List[Dict]:
    # Degraded: emoji prefix per kind. NOT knownIcon — the Cards v2 enum has no
    # INFO/WARNING/ERROR, so startIcon would 400 for info/warning/danger.
    emoji_map = {"info": "ℹ️", "warning": "⚠️", "tip": "💡", "danger": "🛑"}
    color_map = {"info": "#1a73e8", "warning": "#f9ab00", "tip": "#34a853", "danger": "#ea4335"}
    kind  = b.get("kind", "info")
    emoji = emoji_map.get(kind, "ℹ️")
    color = color_map.get(kind, "#1a73e8")
    title = b.get("title", "")
    text  = _md_to_chat(b.get("text", ""))
    content = f'<b><font color="{color}">{title}</font></b><br/>{text}' if title else f'<font color="{color}">{text}</font>'
    return [{
        "decoratedText": {
            "text": f'{emoji} {content}',
            "wrapText": True
        }
    }]


def _render_table(b: dict) -> List[Dict]:
    # Degraded: render as formatted textParagraph rows
    headers = b.get("headers", [])
    rows    = b.get("rows", [])
    caption = b.get("caption", "")
    lines   = []
    if caption:
        lines.append(f'<i><font color="#999">{caption}</font></i>')
    if headers:
        lines.append("<b>" + " | ".join(headers) + "</b>")
        lines.append("—" * 30)
    for row in rows:
        lines.append(" | ".join(str(c) for c in row))
    return [_text("<br/>".join(lines))]


def _render_key_value(b: dict) -> List[Dict]:
    items   = b.get("items", [])
    title   = b.get("title", "")
    widgets = []
    if title:
        widgets.append(_text(f'<b>{title}</b>'))
    for item in items:
        req = " <font color=\"#ea4335\">*required</font>" if item.get("required") else ""
        default = f' <font color="#34a853">default: {item["default"]}</font>' if "default" in item else ""
        widgets.append({
            "decoratedText": {
                "topLabel": item.get("key", ""),
                "text": _md_to_chat(item.get("description", "")) + req + default,
                "wrapText": True
            }
        })
    return widgets


def _render_stat_card(b: dict) -> List[Dict]:
    value  = b.get("value", "—")
    label  = b.get("label", "")
    delta  = b.get("delta", "")
    is_up  = b.get("is_up", True)
    arrow  = "▲" if is_up else "▼"
    color  = "#34a853" if is_up else "#ea4335"
    delta_html = f' <font color="{color}">{arrow} {delta}</font>' if delta else ""
    return [{
        "decoratedText": {
            "topLabel": label.upper(),
            "text": f'<b>{value}</b>{delta_html}',
            "wrapText": False
        }
    }]


def _render_badge_group(b: dict) -> List[Dict]:
    badges  = b.get("badges", [])
    title   = b.get("title", "")
    COLOR_HEX = {
        "green": "#34a853", "cyan": "#00acc1", "blue": "#4285f4",
        "yellow": "#f9ab00", "red": "#ea4335", "purple": "#8430ce", "grey": "#9aa0a6"
    }
    chips = []
    for badge in badges:
        color = COLOR_HEX.get(badge.get("color", "grey"), "#9aa0a6")
        chips.append({"label": badge.get("text", "")})
    widgets = []
    if title:
        widgets.append(_text(f'<font color="#999"><i>{title}</i></font>'))
    if chips:
        widgets.append({"chipList": {"chips": chips}})
    return widgets


def _render_gallery(b: dict) -> List[Dict]:
    images  = b.get("images", [])
    caption = b.get("caption", "")
    # Use cardsV2 grid widget
    items   = []
    for img in images[:4]:  # grid supports up to 4 cleanly
        item = {"image": {"imageUri": img.get("url", ""), "altText": img.get("alt", "")}}
        if img.get("caption"):
            item["title"] = img["caption"]
        items.append(item)
    widgets = [{"grid": {"columnCount": min(len(items), 3), "items": items}}]
    if caption:
        widgets.append(_text(f'<font color="#999"><i>{caption}</i></font>'))
    return widgets


def _render_divider_fallback(b: dict) -> List[Dict]:
    return [_divider()]


# ── chat_thread router → cardsV2 sections ─────────────────────────────────────
#
# Google Chat is a native chat surface, so the router maps onto cardsV2 directly:
#   user/assistant/system messages → textParagraph widgets in a transcript section
#   kind=tool_call                 → its own NATIVE collapsible section
#   composer                       → no-op (Chat's message box IS the composer);
#                                    rendered as a faint hint line only
#   suggestions                    → chipList
# Returns a list of section dicts (not widgets) — the builder splices them in.

_TOOL_STATUS = {"running": "⏳", "ok": "✅", "error": "⛔"}


def _chat_meta_line(meta: dict) -> str:
    parts = []
    if meta.get("model"):
        parts.append(str(meta["model"]))
    if meta.get("tokens") is not None:
        parts.append(f'{meta["tokens"]} tok')
    if meta.get("latency_ms") is not None:
        parts.append(f'{meta["latency_ms"]} ms')
    if meta.get("timestamp"):
        parts.append(str(meta["timestamp"]))
    return " · ".join(parts)


def _chat_message_widget(m: dict) -> Dict:
    role = m.get("role", "assistant")
    text = _md_to_chat(m.get("text", ""))
    if role == "system":
        return _text(f'<font color="#9aa0a6"><i>— {text} —</i></font>')
    icon = "🧑" if role == "user" else "🤖"
    name = m.get("name") or ("You" if role == "user" else "Assistant")
    body = f'{icon} <b>{name}</b>'
    if text:
        body += f'<br/>{text}'
    meta = _chat_meta_line(m.get("meta", {})) if m.get("meta") else ""
    if meta:
        body += f'<br/><font color="#9aa0a6">{meta}</font>'
    return _text(body)


def _chat_tool_section(m: dict) -> Dict:
    tool = m.get("tool", {})
    name = tool.get("name", "tool")
    status = tool.get("status", "running")
    emoji = _TOOL_STATUS.get(status, "🔧")
    # First widget stays visible; the rest collapse behind the section header.
    widgets = [_text(f'🔧 <b>{name}</b> {emoji} <font color="#9aa0a6">{status}</font>')]
    args = tool.get("args")
    if args is not None:
        args_str = args if isinstance(args, str) else ", ".join(
            f"{k}={v}" for k, v in args.items()) if isinstance(args, dict) else str(args)
        widgets.append(_text(f'<font color="#9aa0a6">args:</font> <font color="#1a73e8">{args_str}</font>'))
    if tool.get("result") is not None:
        widgets.append(_text(f'<font color="#9aa0a6">→</font> {_md_to_chat(str(tool["result"]))}'))
    collapsed = tool.get("collapsed", True)
    section = {"header": f'🔧 {name} · {emoji}', "widgets": widgets}
    # Only make it collapsible when there's something to hide.
    if collapsed and len(widgets) > 1:
        section["collapsible"] = True
        section["uncollapsibleWidgetsCount"] = 1
    return section


def _render_chat_thread_sections(b: dict) -> List[Dict]:
    sections: List[Dict] = []
    transcript: List[Dict] = []

    def flush():
        if transcript:
            sections.append({"widgets": list(transcript)})
            transcript.clear()

    header = b.get("title", "")
    for m in b.get("messages", []):
        kind = m.get("kind")
        if kind == "tool_call":
            flush()
            sections.append(_chat_tool_section(m))
        elif kind == "atom":
            # role header line, then the embedded (surface-gated) block
            role = m.get("role", "assistant")
            icon = "🧑" if role == "user" else "🤖"
            name = m.get("name") or ("You" if role == "user" else "Assistant")
            head = f'{icon} <b>{name}</b>'
            if m.get("text"):
                head += f'<br/>{_md_to_chat(m["text"])}'
            transcript.append(_text(head))
            transcript.extend(_degrade_for_chat(m.get("block") or {}))
        else:
            transcript.append(_chat_message_widget(m))
    if b.get("typing"):
        transcript.append(_text('🤖 <font color="#9aa0a6"><i>typing…</i></font>'))
    flush()

    # composer is a no-op on Chat — the platform owns the input box.
    footer: List[Dict] = []
    if b.get("composer"):
        ph = b["composer"].get("placeholder", "Reply in the message box below")
        footer.append(_text(f'<font color="#9aa0a6"><i>💬 {ph}</i></font>'))
    suggestions = b.get("suggestions", [])
    if suggestions:
        footer.append({"chipList": {"chips": [{"label": s} for s in suggestions]}})
    if footer:
        sections.append({"widgets": footer})

    if header and sections:
        sections[0] = {"header": header, **sections[0]}
    return sections


# ── kind: atom — embed any catalogue atom in a message, surface-gated ─────────
#
# Web/GAS render all 498 atoms; Google Chat cardsV2 renders ~44 (no canvas/JS).
# So an embedded block is DEGRADED ON PURPOSE for Chat — charts → tables, data-viz
# → its numbers, decorative atoms → their text — never a red "not supported" line.

_CHART_TYPES = {"chartjs_bar", "chartjs_line", "chartjs_pie", "sparkline",
                "data_table_sortable", "metric_comparison_card"}
_TEXT_FIELDS = ("title", "heading", "label", "name", "headline")
_BODY_FIELDS = ("text", "content", "subtitle", "description", "body")


def _chart_to_table_widgets(b: dict) -> List[Dict]:
    t = b.get("type")
    if t in ("chartjs_bar", "chartjs_line"):
        labels = b.get("labels", [])
        datasets = b.get("datasets", [])
        headers = ["Category", *[d.get("label", f"series {i+1}") for i, d in enumerate(datasets)]]
        rows = []
        for i, lab in enumerate(labels):
            row = [str(lab)]
            for d in datasets:
                data = d.get("data", [])
                row.append(str(data[i]) if i < len(data) else "")
            rows.append(row)
        return _render_table({"headers": headers, "rows": rows, "caption": b.get("title", "")})
    if t == "chartjs_pie":
        rows = [[str(d.get("label", "")), str(d.get("value", ""))] for d in b.get("data", [])]
        return _render_table({"headers": ["Segment", "Value"], "rows": rows, "caption": b.get("title", "")})
    if t == "sparkline":
        nums = [x for x in b.get("data", []) if isinstance(x, (int, float))]
        bars = "▁▂▃▄▅▆▇█"
        spark = ""
        if nums:
            lo, hi = min(nums), max(nums)
            rng = (hi - lo) or 1
            spark = "".join(bars[min(len(bars) - 1, int((x - lo) / rng * (len(bars) - 1)))] for x in nums)
        span = f'({nums[0]} → {nums[-1]})' if nums else ''
        return [_text(f'<font color="#1a73e8">{spark}</font>  <font color="#9aa0a6">{span}</font>')]
    if t == "data_table_sortable":
        return _render_table({"headers": b.get("headers", []), "rows": b.get("rows", [])})
    if t == "metric_comparison_card":
        prev = b.get("previous")
        tail = f' <font color="#9aa0a6">(was {prev})</font>' if prev is not None else ""
        return [_text(f'<b>{b.get("label", "")}:</b> {b.get("value", "")}{tail}')]
    return []


def _generic_text_widgets(b: dict) -> List[Dict]:
    head = next((b[f] for f in _TEXT_FIELDS if b.get(f)), "")
    body = next((b[f] for f in _BODY_FIELDS if b.get(f)), "")
    parts = []
    if head:
        parts.append(f"<b>{head}</b>")
    if body:
        parts.append(_md_to_chat(str(body)))
    return [_text("<br/>".join(parts))] if parts else []


# ── Family mapper: shape-based dispatch for atoms with no native renderer ─────
# Keys on the block's DATA SHAPE (field names/structure), not its type name —
# one rule covers a whole family. Ordered; first non-empty result wins. Every
# emitted widget uses only contract-validated fields (see verify_chat_surface).

def _fm_str(x, *keys):
    if isinstance(x, str): return x
    if isinstance(x, dict):
        for k in keys:
            if x.get(k): return str(x[k])
    return ""

def _fm_table(b):
    hdrs, rows = b.get("headers"), b.get("rows")
    if isinstance(rows, list) and rows and isinstance(rows[0], (list, tuple)):
        return _render_table({"headers": hdrs or [], "rows": rows, "caption": b.get("title") or b.get("caption", "")})
    return None

def _fm_tabs(b):
    tabs = b.get("tabs")
    if isinstance(tabs, list) and tabs and isinstance(tabs[0], dict) and "label" in tabs[0]:
        out = []
        for t in tabs:
            out.append(_text(f'<b><font color="#1a73e8">▸ {t.get("label","")}</font></b>'))
            for bl in (t.get("content") or t.get("blocks") or []):
                out.extend(_degrade_for_chat(bl) if isinstance(bl, dict) else [_text(str(bl))])
        return out or None
    return None

def _fm_columns(b):
    left, right = b.get("left"), b.get("right")
    if isinstance(left, dict) and isinstance(right, dict):
        def col(d):
            ws = _generic_text_widgets(d) or [_text("")]
            return {"horizontalSizeStyle": "FILL_AVAILABLE_SPACE", "widgets": ws}
        return [{"columns": {"columnItems": [col(left), col(right)]}}]
    return None

def _fm_chips(b):
    src = b.get("badges") or b.get("tags") or b.get("chips") or b.get("keywords")
    if isinstance(src, list) and src:
        chips = [{"label": _fm_str(i, "text", "label", "tag")} for i in src]
        chips = [c for c in chips if c["label"]]
        if chips:
            head = [_text(f'<b>{b["title"]}</b>')] if b.get("title") else []
            return head + [{"chipList": {"chips": chips[:20]}}]
    return None

def _fm_buttons(b):
    src = b.get("links") or b.get("buttons") or b.get("actions") or b.get("resources")
    if isinstance(src, list) and src:
        btns = []
        for i in src:
            if isinstance(i, dict) and str(i.get("url", "")).startswith("http"):
                btns.append(_button(_fm_str(i, "label", "text", "title") or i["url"], i["url"]))
        if btns:
            head = [_text(f'<b>{b["title"]}</b>')] if b.get("title") else []
            return head + [{"buttonList": {"buttons": btns[:10]}}]
    return None

def _fm_image(b):
    url = b.get("url") or b.get("image") or b.get("src") or b.get("thumbnail")
    looks_img = isinstance(url, str) and url.startswith("http") and (
        re.search(r'\.(png|jpe?g|gif|webp|svg)(\?|$)', url, re.I) or b.get("alt") or b.get("caption"))
    if looks_img:
        w = [{"image": {"imageUrl": url, "altText": str(b.get("alt") or b.get("title") or "")}}]
        if b.get("caption"): w.append(_text(f'<font color="#9aa0a6"><i>{b["caption"]}</i></font>'))
        return w
    return None

def _fm_kv(b):
    items = b.get("items") or b.get("pairs") or b.get("entries")
    if isinstance(items, list) and items and isinstance(items[0], dict):
        pairs = []
        for i in items:
            k = _fm_str(i, "key", "label", "term", "name", "date")
            v = _fm_str(i, "value", "definition", "description", "text", "desc", "subtitle", "action")
            if k and v: pairs.append((k, v))
        if pairs and len(pairs) >= max(1, len(items) - 1):     # mostly kv-shaped
            head = [_text(f'<b>{b["title"]}</b>')] if b.get("title") else []
            return head + [{"decoratedText": {"topLabel": k, "text": _md_to_chat(v), "wrapText": True}}
                           for k, v in pairs[:15]]
    return None

def _fm_stat(b):
    if b.get("value") is not None and (b.get("label") or b.get("unit") or b.get("title")):
        lab = str(b.get("label") or b.get("title") or "")
        unit = str(b.get("unit") or "")
        return [{"decoratedText": {"topLabel": lab.upper(),
                                   "text": f'<b>{b["value"]}{unit}</b>', "wrapText": False}}]
    return None

def _fm_listy(b):
    src = b.get("items") or b.get("steps") or b.get("entries") or b.get("list") or b.get("events")
    if isinstance(src, list) and src:
        numbered = "steps" in b
        lines = []
        for n, i in enumerate(src[:20], 1):
            txt = _fm_str(i, "text", "label", "title", "name", "question", "desc", "description")
            if isinstance(i, dict):
                extra = _fm_str(i, "desc", "description", "subtitle", "detail") if txt != _fm_str(i, "desc", "description", "subtitle", "detail") else ""
                date = _fm_str(i, "date", "time")
                if date: txt = f'<b><font color="#1a73e8">{date}</font></b> {txt}'
                if extra and extra != txt: txt = f'<b>{txt}</b> — {extra}'
            if txt: lines.append((f'{n}. ' if numbered else '• ') + _md_to_chat(txt))
        if lines:
            head = [_text(f'<b>{b["title"]}</b>')] if b.get("title") else []
            return head + [_text("<br/>".join(lines))]
    return None

_FAMILY_RULES = (_fm_table, _fm_tabs, _fm_columns, _fm_chips, _fm_buttons,
                 _fm_image, _fm_kv, _fm_stat, _fm_listy)

def _family_map(b: dict) -> List[Dict]:
    for rule in _FAMILY_RULES:
        try:
            w = rule(b)
        except Exception:
            w = None                                   # a mapper must never crash the render
        if w: return w
    return []

def _degrade_for_chat(b: dict) -> List[Dict]:
    """Render any atom on Google Chat: native → chart-degrade → family shape-map
    → text extraction → honest reduced note. Degrades on purpose, never errors."""
    t = b.get("type", "")
    if t in RENDERERS:                       # 1. natively supported on Chat
        return RENDERERS[t](b)
    if t in _CHART_TYPES:                     # 2. data-viz → table / sparkline text
        try:
            w = _chart_to_table_widgets(b)
        except Exception:
            w = None                          # malformed chart data → fall through, never crash
        if w:
            return w
    w = _family_map(b)                        # 3. shape-based family mapping
    if w:
        title = b.get("title") or b.get("heading")
        lead = b.get("text") or b.get("subtitle") or ""
        head = []
        if title and not any("decoratedText" in x or f'<b>{title}</b>' in str(x) for x in w[:1]):
            head = [_text(f'<b>{_md_to_chat(str(title))}</b>' + (f'<br/>{_md_to_chat(str(lead))}' if lead else ''))]
        return head + w
    w = _generic_text_widgets(b)             # 4. any atom carrying text-ish fields
    if w:
        return w
    return [_text(f'<font color="#9aa0a6"><i>↓ {t} — reduced (no Chat visual)</i></font>')]


# ── Incompatible fallback ─────────────────────────────────────────────────────

def _incompatible(atom_type: str) -> List[Dict]:
    return [_text(f'<font color="#ea4335"><i>[{atom_type} not supported in Google Chat]</i></font>')]


# ── Registry ─────────────────────────────────────────────────────────────────

RENDERERS: Dict[str, Any] = {
    # works_on: googlechat
    "intro":        _render_intro,
    "body":         _render_body,
    "heading":      _render_heading,
    "subheading":   _render_subheading,
    "bullet_list":  _render_bullet_list,
    "closing":      _render_closing,
    "divider":      _render_divider,
    "image":        _render_image,
    "repo_links":   _render_repo_links,
    # degraded_on: googlechat (best-effort)
    "quote":        _render_quote,
    "code":         _render_code,
    "pipeline":     lambda b: [_text(" ──► ".join(b.get("steps", [])))],
    "image_pair":   _render_image_pair,
    "diagram":      lambda b: _render_image(b),
    "table":        _render_table,
    "key_value":    _render_key_value,
    "callout":      _render_callout,
    "steps":        lambda b: [_text("<br/>".join(
                        f'<b>{i+1}.</b> {"<b>" + s["label"] + "</b> " if s.get("label") else ""}{_md_to_chat(s.get("text",""))}'
                        for i, s in enumerate(b.get("items", []))))],
    "api_reference": lambda b: _render_key_value({
                        "title": b.get("name", ""),
                        "items": b.get("parameters", [])
                    }),
    "timeline":     lambda b: [_text("<br/>".join(
                        f'<b><font color="#1a73e8">{e.get("date","")}</font></b> {e.get("label","")} — {_md_to_chat(e.get("text",""))}'
                        for e in b.get("events", [])))],
    "gallery":      _render_gallery,
    "stat_card":    _render_stat_card,
    "badge_group":  _render_badge_group,
    "metric_delta": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "metric_delta")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "trend_indicator": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "trend_indicator")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "glossary_term": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "glossary_term")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "footnote": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "footnote")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "pull_stat": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "pull_stat")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "audio_link": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "audio_link")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "document_link": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "document_link")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "image_with_caption": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "image_with_caption")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "action_required_card": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "action_required_card")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "pricing_tier_card": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "pricing_tier_card")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "pros_cons_list": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "pros_cons_list")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "rating_comparison": lambda b: [{"textParagraph": {"text": "<b>" + b.get("label", b.get("title", "rating_comparison")) + "</b><br/>" + b.get("text", b.get("content", ""))}}],
    "entity_list": lambda b: [_text("<br/>".join(
        "<b>" + e.get("name", "") + "</b>"
        + (" — " + e.get("subtitle", "") if e.get("subtitle") else "")
        + (" [" + e.get("status", "") + "]" if e.get("status") else "")
        for e in b.get("items", [])
    ))],
    "model_card": lambda b: [_text(
        "<b>" + b.get("name", "") + "</b>"
        + (" · " + b.get("provider", "") if b.get("provider") else "")
        + ("<br/>" + b.get("description", "") if b.get("description") else "")
    )],
    "conversation_snippet": lambda b: [_text(
        "<b>" + b.get("user_label", "You") + ":</b> " + b.get("user", "")
        + "<br/><b>" + b.get("ai_label", "Assistant") + ":</b> " + b.get("response", "")
    )],
    "shortcut_legend": lambda b: [_text(
        ("<b>" + b.get("title", "") + "</b><br/>" if b.get("title") else "")
        + "<br/>".join(
            " + ".join(i.get("keys", [])) + " — " + i.get("action", "")
            for i in b.get("items", [])
        )
    )],
    "rating_summary_bar": lambda b: [_text(
        "⭐ <b>" + str(b.get("average", "")) + "</b>"
        + (" / " + str(b.get("total", "")) + " ratings" if b.get("total") else "")
    )],
    "roadmap_card": lambda b: [_text(
        "<b>" + b.get("title", b.get("name", "Roadmap")) + "</b>"
        + ("<br/>" + b.get("description", b.get("text", "")) if b.get("description") or b.get("text") else "")
    )],
    "notification_stack": lambda b: [_text(
        "<br/>".join(
            "🔔 <b>" + n.get("title", "") + "</b>"
            + (" — " + n.get("body", "") if n.get("body") else "")
            for n in b.get("notifications", [])[:3]
        ) or "🔔 " + b.get("title", "notification_stack")
    )],
    "text_callout": lambda b: [_text(b.get("text", b.get("content", "")))],
    # chat_thread's primary path is the sectioned splice in render() (native
    # collapsible tool calls). This map entry is a flat-widget fallback for any
    # caller that dispatches through RENDERERS directly.
    "chat_thread": lambda b: [w for s in _render_chat_thread_sections(b) for w in s.get("widgets", [])],
}


# ── Builder ───────────────────────────────────────────────────────────────────

def render(blocks: List[Dict[str, Any]],
           title: str = "",
           subtitle: str = "") -> Dict[str, Any]:
    """Render a list of blocks to a Google Chat cardsV2 message.

    Args:
        blocks:   List of block dicts conforming to atoms/schema.yaml
        title:    Optional card header title
        subtitle: Optional card header subtitle

    Returns:
        Google Chat message dict with cardsV2 format — POST to webhook directly
    """
    sections = []
    current_widgets = []

    for block in blocks:
        btype = block.get("type", "")

        # chat_thread emits whole sections (incl. native collapsible tool calls),
        # so it can't go through the widget-list contract — splice it in directly.
        if btype == "chat_thread":
            if current_widgets:
                sections.append({"widgets": current_widgets})
                current_widgets = []
            sections.extend(_render_chat_thread_sections(block))
            continue

        fn = RENDERERS.get(btype)

        if fn is None:
            # no native renderer — family-map / degrade on purpose (never a red error)
            current_widgets.extend(_degrade_for_chat(block))
            continue

        widgets = fn(block)

        # Headings start a new section
        if btype in ("heading",) and current_widgets:
            sections.append({"widgets": current_widgets})
            current_widgets = []

        current_widgets.extend(widgets)

    if current_widgets:
        sections.append({"widgets": current_widgets})

    card = {"sections": sections if sections else [{"widgets": []}]}
    if title:
        card["header"] = {
            "title": title,
            "subtitle": subtitle or "",
        }

    return {"cardsV2": [{"cardId": "1", "card": card}]}


def post(blocks: List[Dict[str, Any]], webhook_url: str,
         title: str = "", subtitle: str = "") -> Dict:
    """Render blocks and POST to a Google Chat webhook."""
    import requests as req
    message = render(blocks, title=title, subtitle=subtitle)
    resp = req.post(webhook_url, json=message)
    return {"status": resp.status_code, "response": resp.json() if resp.ok else resp.text}
