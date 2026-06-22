"""web-article renderer — block list → clean HTML.

Takes a list of typed block dicts (conforming to schema.yaml) and returns
a single HTML string ready to store in Firestore or any web CMS.

No markdown conversion. No Quill. No stripping surprises.
"""

from typing import List, Dict, Any
import re, base64, urllib.request, urllib.error, json as _json
from datetime import datetime, timezone
import markdown as _md


_DARK_OVERRIDES = """
<style>
  /* meet-stage dark theme overrides */
  body { background: transparent !important; color: #e8eaed !important; }
  h2, h3 { color: #00f2ff !important; }
  p, li, td, th, span { color: #e8eaed !important; }
  pre, code { background: #0d1117 !important; color: #cdd6f4 !important; }
  blockquote { border-color: #00f2ff !important; color: #9aa0a6 !important; }
  table { background: transparent !important; }
  th { background: rgba(0,242,255,0.1) !important; color: #00f2ff !important; border-color: rgba(255,255,255,0.1) !important; }
  td { background: transparent !important; color: #e8eaed !important; border-color: rgba(255,255,255,0.08) !important; }
  tr:nth-child(even) td { background: rgba(255,255,255,0.03) !important; }
  .tm-tabs { border-color: rgba(255,255,255,0.1) !important; }
  .tm-tab-labels { background: #0d1117 !important; border-color: rgba(255,255,255,0.08) !important; }
  .tm-tab-label { color: #9aa0a6 !important; border-color: rgba(255,255,255,0.06) !important; }
  .tm-tab-panels { background: #0d1117 !important; }
</style>
"""

def render(blocks: List[Dict[str, Any]], theme: str = "light") -> str:
    """Render a list of blocks to HTML.

    Args:
        blocks: List of block dicts conforming to atoms/schema.yaml
        theme: 'light' (default, web/blog) or 'dark' (meet-stage)
    """
    parts = []
    for block in blocks:
        btype = block.get("component") or block.get("type")
        fn = _RENDERERS.get(btype)
        if fn:
            parts.append(fn(block))
        else:
            parts.append(f'<!-- unknown block type: {btype} -->')
    html = "\n\n".join(parts)
    if theme == "dark":
        html = _DARK_OVERRIDES + html
    # Ensure all external links open in a new tab
    html = re.sub(
        r'<a (href="https?://[^"]+")(?![^>]*target=)',
        r'<a \1 target="_blank" rel="noopener noreferrer"',
        html,
    )
    return html


# ── Helpers ──────────────────────────────────────────────────────────────────

_ABBR_STYLE = (
    'border-bottom:2px dotted #7c3aed;cursor:help;'
    'text-decoration:none;font-weight:600;color:inherit;'
)

def _md_inline(text: str) -> str:
    """Convert **bold**, *italic*, `code`, links, and [term](def:...) abbr tooltips to HTML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # [term](def:definition) → abbr tooltip with dotted purple underline
    def _abbr(m):
        term, defn = m.group(1), m.group(2)[4:]  # strip "def:"
        return f'<abbr title="{defn}" style="{_ABBR_STYLE}">{term}</abbr>'
    text = re.sub(r'\[([^\]]+)\]\((def:[^)]+)\)', _abbr, text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
    return text


def _youtube_id(url: str) -> str:
    """Extract YouTube video ID from any youtube.com or youtu.be URL."""
    m = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    return m.group(1) if m else url


# ── Block renderers ──────────────────────────────────────────────────────────

def _render_intro(b: dict) -> str:
    parts = []
    if b.get("series_label") and b.get("series_url"):
        parts.append(
            f'<p><em>In <a href="{b["series_url"]}">{b["series_label"]}</a>, '
            f'{_md_inline(b.get("continuation", "I covered the background. This article picks up from there."))}</em></p>'
        )
    if b.get("note"):
        parts.append(f'<p><em>{_md_inline(b["note"])}</em></p>')
    return "\n".join(parts)


def _render_body(b: dict) -> str:
    paragraphs = b.get("text", "").strip().split("\n\n")
    return "\n".join(f"<p>{_md_inline(p.strip())}</p>" for p in paragraphs if p.strip())


def _render_heading(b: dict) -> str:
    return f'<h2>{_md_inline(b.get("text", ""))}</h2>'


def _render_subheading(b: dict) -> str:
    return f'<h3>{_md_inline(b.get("text", ""))}</h3>'


def _render_quote(b: dict) -> str:
    html = f'<blockquote><p>{_md_inline(b.get("text", ""))}</p>'
    if b.get("attribution"):
        html += f'<footer>— {b["attribution"]}</footer>'
    html += '</blockquote>'
    return html


def _render_code(b: dict) -> str:
    lang = b.get("language", "")
    content = b.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
    return f'<pre><code class="language-{lang}">{content}</code></pre>'


def _render_pipeline(b: dict) -> str:
    steps = b.get("steps", [])
    flow = " ──► ".join(f"<code>{s}</code>" for s in steps)
    return f'<p style="font-family:monospace;background:#f4f4f4;padding:12px 16px;border-radius:6px;">{flow}</p>'


def _render_bullet_list(b: dict) -> str:
    items_html = []
    for item in b.get("items", []):
        if item.get("label"):
            items_html.append(f'<li><strong>{_md_inline(item["label"])}</strong> {_md_inline(item.get("text",""))}</li>')
        else:
            items_html.append(f'<li>{_md_inline(item.get("text",""))}</li>')
    return f'<ul>{"".join(items_html)}</ul>'


def _render_divider(b: dict) -> str:
    return '<hr style="border:none;border-top:1px solid rgba(0,0,0,0.1);margin:2rem 0;"/>'


def _render_youtube(b: dict) -> str:
    # Blog embed: user-controlled playback (controls visible), standard params.
    # allow="autoplay; encrypted-media" is required for any YouTube iframe.
    # Never add referrerpolicy="no-referrer" — YouTube uses Referer to validate
    # the embedding domain; suppressing it causes Error 153 even when embedding
    # is enabled by the video owner.
    vid_id = _youtube_id(b.get("url", ""))
    params = f"?rel=0&modestbranding=1"
    caption = f'<p style="font-size:0.8rem;opacity:0.6;margin-top:6px;text-align:center;">{b["caption"]}</p>' if b.get("caption") else ""
    return (
        f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin:1.2rem 0;border-radius:8px;">'
        f'<iframe src="https://www.youtube.com/embed/{vid_id}{params}" '
        f'style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" '
        f'allow="autoplay; encrypted-media" allowfullscreen></iframe>'
        f'</div>{caption}'
    )


EMBED_REMOTE_IMAGES = False  # set True to inline remote images as base64 data URIs

def _img_src(url: str) -> str:
    """Return a base64 data URI for local images; remote URLs pass through unless EMBED_REMOTE_IMAGES is set."""
    if not url or url.startswith("data:"):
        return url
    if url.startswith("http://") or url.startswith("https://"):
        if not EMBED_REMOTE_IMAGES:
            return url
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            mime = resp.headers.get_content_type() or "image/png"
            data = base64.b64encode(resp.read()).decode()
            return f"data:{mime};base64,{data}"
    except Exception:
        return url


def _render_image(b: dict) -> str:
    width = b.get("width", "100%")
    caption = f'<p style="font-size:0.8rem;opacity:0.6;margin-top:6px;text-align:center;">{b.get("caption","")}</p>' if b.get("caption") else ""
    src = _img_src(b["url"])
    return (
        f'<div style="margin:1.2rem 0;text-align:center;">'
        f'<img src="{src}" alt="{b.get("alt","")}" '
        f'style="width:{width};height:auto;border-radius:8px;display:block;margin:0 auto;"/>'
        f'{caption}</div>'
    )


def _render_image_pair(b: dict) -> str:
    def cell(side):
        caption = f'<p style="font-size:0.78rem;opacity:0.6;margin-top:6px;">{side.get("caption","")}</p>' if side.get("caption") else ""
        src = _img_src(side["url"])
        return (
            f'<td style="width:50%;padding:0 8px;vertical-align:top;text-align:center;">'
            f'<img src="{src}" alt="{side.get("alt","")}" '
            f'style="width:100%;height:auto;border-radius:8px;display:block;"/>'
            f'{caption}</td>'
        )
    left = b.get("left", {})
    right = b.get("right", {})
    return (
        f'<table style="width:100%;border-collapse:collapse;margin:1.2rem 0;">'
        f'<tr>{cell(left)}{cell(right)}</tr>'
        f'</table>'
    )


_DIAGRAM_CSS = (
    "<style>"
    ".tm-diagram{overflow:visible;}"
    ".tm-diagram img{"
    "transition:transform 0.35s cubic-bezier(0.34,1.56,0.64,1),box-shadow 0.35s ease;"
    "cursor:zoom-in;transform-origin:center top;border-radius:8px;}"
    ".tm-diagram img:hover{"
    "transform:scale(2.2);position:relative;z-index:100;"
    "box-shadow:0 12px 40px rgba(0,0,0,0.22);border-radius:8px;}"
    "</style>"
)

def _render_diagram(b: dict) -> str:
    caption = f'<p style="font-size:0.8rem;opacity:0.6;margin-top:8px;text-align:center;">Hover to zoom · {b["caption"]}</p>' if b.get("caption") else '<p style="font-size:0.78rem;opacity:0.5;margin-top:6px;text-align:center;">Hover to zoom</p>'
    return (
        f'{_DIAGRAM_CSS}'
        f'<div class="tm-diagram" style="margin:1.5rem 0;padding:20px;background:#f8f9fa;'
        f'border:1px solid #e0e0e0;border-radius:12px;text-align:center;overflow:visible;">'
        f'<img src="{b["url"]}" alt="diagram" style="max-width:100%;height:auto;" onclick="return false;"/>'
        f'{caption}</div>'
    )


def _render_github_repo_card(b: dict) -> str:
    """Fetch repo metadata from GitHub API and render a self-contained card."""
    repo = b.get("repo", "")          # e.g. "curtiskrygier/a2ui-catalogue"
    label = b.get("label", "")        # optional override label
    description_override = b.get("description", "")

    # Defaults for fallback
    name = repo.split("/")[-1] if "/" in repo else repo
    description = description_override or ""
    stars = forks = 0
    language = ""
    updated = ""
    url = f"https://github.com/{repo}" if repo else b.get("url", "#")

    if repo:
        try:
            api_req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}",
                headers={"User-Agent": "a2ui-renderer", "Accept": "application/vnd.github+json"}
            )
            with urllib.request.urlopen(api_req, timeout=8) as resp:
                data = _json.loads(resp.read())
                name        = data.get("name", name)
                description = description_override or data.get("description", "")
                stars       = data.get("stargazers_count", 0)
                forks       = data.get("forks_count", 0)
                language    = data.get("language", "")
                url         = data.get("html_url", url)
                pushed      = data.get("pushed_at", "")
                if pushed:
                    dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
                    updated = dt.strftime("Updated %b %Y")
        except Exception:
            pass

    display_label = label or name
    lang_html = (
        f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:0.78rem;color:#9aa0a6;">'
        f'<span style="width:10px;height:10px;border-radius:50%;background:#f9ab00;display:inline-block;"></span>'
        f'{language}</span>'
    ) if language else ""
    updated_html = f'<span style="font-size:0.78rem;color:#9aa0a6;">{updated}</span>' if updated else ""
    desc_html    = f'<p style="margin:6px 0 10px;font-size:0.85rem;color:#555;line-height:1.5;">{description}</p>' if description else ""

    return (
        f'<a href="{url}" target="_blank" rel="noopener" style="display:block;text-decoration:none;margin:0.8rem 0;">'
        f'<div style="border:1px solid #d0d7de;border-radius:10px;padding:16px 20px;'
        f'background:#fff;transition:box-shadow 0.15s;font-family:system-ui,sans-serif;" '
        f'onmouseover="this.style.boxShadow=\'0 4px 12px rgba(0,0,0,0.1)\'" '
        f'onmouseout="this.style.boxShadow=\'none\'">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">'
        f'<svg width="16" height="16" viewBox="0 0 16 16" fill="#555" style="flex-shrink:0;">'
        f'<path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8Z"/>'
        f'</svg>'
        f'<span style="font-size:0.9rem;font-weight:600;color:#0969da;">{display_label}</span>'
        f'</div>'
        f'{desc_html}'
        f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">'
        f'{lang_html}'
        f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:0.78rem;color:#9aa0a6;">'
        f'<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg>'
        f'{stars}</span>'
        f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:0.78rem;color:#9aa0a6;">'
        f'<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"/></svg>'
        f'{forks}</span>'
        f'{updated_html}'
        f'</div></div></a>'
    )


def _render_repo_links(b: dict) -> str:
    items = "".join(
        f'<li><strong>{l["label"]}:</strong> <a href="{l["url"]}">{l["url"].replace("https://","")}</a></li>'
        for l in b.get("links", [])
    )
    return f'<ul style="list-style:none;padding:0;">{items}</ul>'


def _render_before_after(b: dict) -> str:
    """Before/after code comparison — two panels side by side with clear visual distinction."""
    before_label = b.get("before_label", "Before")
    after_label  = b.get("after_label",  "After")
    language     = b.get("language", "")
    before_code  = b.get("before", "").replace("<", "&lt;").replace(">", "&gt;")
    after_code   = b.get("after",  "").replace("<", "&lt;").replace(">", "&gt;")
    caption      = b.get("caption", "")
    caption_html = f'<p style="font-size:0.82rem;opacity:0.6;margin-top:8px;text-align:center;">{caption}</p>' if caption else ""

    def panel(label, code, color, bg):
        return (
            f'<div style="flex:1;min-width:0;">'
            f'<div style="padding:6px 14px;background:{color};border-radius:6px 6px 0 0;display:flex;align-items:center;gap:8px;">'
            f'<span style="font-size:0.78rem;font-weight:700;color:#fff;font-family:monospace;letter-spacing:0.05em;">{label}</span>'
            f'</div>'
            f'<pre style="margin:0;padding:16px;background:{bg};border-radius:0 0 6px 6px;'
            f'overflow-x:auto;font-size:0.84rem;line-height:1.6;">'
            f'<code class="language-{language}">{code}</code>'
            f'</pre></div>'
        )

    return (
        f'<div style="display:flex;gap:12px;margin:1.5rem 0;align-items:flex-start;">'
        f'{panel(f"✗ {before_label}", before_code, "#c5221f", "#fff8f7")}'
        f'{panel(f"✓ {after_label}", after_code, "#137333", "#f0faf4")}'
        f'</div>'
        f'{caption_html}'
    )


def _render_api_reference(b: dict) -> str:
    """API / function reference block — name, description, parameters table, returns, example."""
    name        = b.get("name", "")
    kind        = b.get("kind", "function")   # function, endpoint, class, method
    description = b.get("description", "")
    params      = b.get("parameters", [])
    returns     = b.get("returns", "")
    example     = b.get("example", {})
    http_method = b.get("method", "")         # GET, POST etc. for endpoints
    deprecated  = b.get("deprecated", False)

    # Header badge
    kind_colors = {
        "function": ("#e8f0fe", "#1a73e8"),
        "endpoint": ("#e6f4ea", "#137333"),
        "class":    ("#fef7e0", "#e37400"),
        "method":   ("#f3e8fd", "#8430ce"),
    }
    bg, color = kind_colors.get(kind, kind_colors["function"])
    method_badge = f'<span style="background:#137333;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:700;margin-right:8px;">{http_method}</span>' if http_method else ""
    deprecated_html = '<span style="background:#c5221f;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;margin-left:8px;">DEPRECATED</span>' if deprecated else ""

    # Parameters table
    param_rows = ""
    if params:
        def _param_row(i, p):
            bg = "background:#f8f9fa;" if i % 2 else ""
            req = "✓" if p.get("required") else ""
            default_val = p.get("default")
            default_html = f'<br/><code style="color:#34a853;font-size:0.9em;">default: {default_val}</code>' if default_val is not None else ""
            return (
                f'<tr style="{bg}">'
                f'<td style="padding:8px 12px;font-family:monospace;font-size:0.82em;color:#1a73e8;white-space:nowrap;">{p.get("name","")}</td>'
                f'<td style="padding:8px 12px;font-family:monospace;font-size:0.82em;color:#e37400;">{p.get("type","")}</td>'
                f'<td style="padding:8px 12px;font-size:0.82em;color:#c5221f;text-align:center;">{req}</td>'
                f'<td style="padding:8px 12px;font-size:0.82em;color:#5f6368;">{_md_inline(p.get("description",""))}{default_html}</td>'
                f'</tr>'
            )
        rows = "".join(_param_row(i, p) for i, p in enumerate(params))
        param_rows = (
            f'<div style="margin-top:12px;">'
            f'<p style="font-size:0.8rem;font-weight:600;color:#5f6368;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em;">Parameters</p>'
            f'<div style="overflow-x:auto;border-radius:6px;border:1px solid #e0e0e0;">'
            f'<table style="border-collapse:collapse;width:100%;font-size:0.9em;">'
            f'<thead><tr style="background:#f1f3f4;">'
            f'<th style="padding:8px 12px;text-align:left;font-size:0.78rem;color:#5f6368;">Name</th>'
            f'<th style="padding:8px 12px;text-align:left;font-size:0.78rem;color:#5f6368;">Type</th>'
            f'<th style="padding:8px 12px;text-align:center;font-size:0.78rem;color:#5f6368;">Req</th>'
            f'<th style="padding:8px 12px;text-align:left;font-size:0.78rem;color:#5f6368;">Description</th>'
            f'</tr></thead>'
            f'<tbody>{rows}</tbody>'
            f'</table></div></div>'
        )

    # Returns
    returns_html = ""
    if returns:
        returns_html = (
            f'<div style="margin-top:12px;">'
            f'<p style="font-size:0.8rem;font-weight:600;color:#5f6368;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.05em;">Returns</p>'
            f'<p style="font-size:0.88em;color:#3c4043;">{_md_inline(returns)}</p>'
            f'</div>'
        )

    # Example
    example_html = ""
    if example:
        ex_code = example.get("code", "").replace("<", "&lt;").replace(">", "&gt;")
        ex_lang = example.get("language", "")
        ex_label = example.get("label", "Example")
        example_html = (
            f'<div style="margin-top:12px;">'
            f'<p style="font-size:0.8rem;font-weight:600;color:#5f6368;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em;">{ex_label}</p>'
            f'<pre style="margin:0;padding:14px;background:#f8f9fa;border-radius:6px;overflow-x:auto;font-size:0.84rem;line-height:1.6;">'
            f'<code class="language-{ex_lang}">{ex_code}</code>'
            f'</pre></div>'
        )

    return (
        f'<div style="border:1px solid #e0e0e0;border-radius:10px;overflow:hidden;margin:1.5rem 0;">'
        f'<div style="background:{bg};padding:14px 18px;border-bottom:1px solid #e0e0e0;">'
        f'{method_badge}'
        f'<code style="font-size:1rem;font-weight:700;color:{color};">{name}</code>'
        f'{deprecated_html}'
        f'<span style="font-size:0.78rem;color:#5f6368;margin-left:10px;text-transform:uppercase;letter-spacing:0.05em;">{kind}</span>'
        f'</div>'
        f'<div style="padding:14px 18px;">'
        f'<p style="color:#3c4043;margin-bottom:8px;">{_md_inline(description)}</p>'
        f'{param_rows}'
        f'{returns_html}'
        f'{example_html}'
        f'</div></div>'
    )


def _render_closing(b: dict) -> str:
    text = f'<p>{_md_inline(b.get("text", ""))}</p>'
    tags = b.get("tags", [])
    tag_html = ""
    if tags:
        tag_html = '<p style="opacity:0.5;font-size:0.85rem;">' + " ".join(f"#{t}" for t in tags) + "</p>"
    return text + tag_html


def _render_callout(b: dict) -> str:
    """Callout/alert box — info, warning, tip, note."""
    kind = b.get("kind", "info")
    styles = {
        "info":    ("ℹ️",  "#e8f0fe", "#1a73e8", "#1a73e8"),
        "warning": ("⚠️",  "#fef7e0", "#f9ab00", "#e37400"),
        "tip":     ("💡",  "#e6f4ea", "#34a853", "#137333"),
        "danger":  ("🚨",  "#fce8e6", "#ea4335", "#c5221f"),
    }
    emoji, bg, border, text_color = styles.get(kind, styles["info"])
    title = b.get("title", "")
    text = _md_inline(b.get("text", ""))
    title_html = f'<strong style="color:{text_color};display:block;margin-bottom:4px;">{emoji} {title}</strong>' if title else f'<strong style="color:{text_color};">{emoji} </strong>'
    return (
        f'<div style="background:{bg};border-left:4px solid {border};border-radius:0 8px 8px 0;'
        f'padding:16px 20px;margin:1.5rem 0;">'
        f'{title_html}'
        f'<span style="color:#3c4043;line-height:1.6;">{text}</span>'
        f'</div>'
    )


def _render_steps(b: dict) -> str:
    """Numbered sequential steps."""
    items = b.get("items", [])
    steps_html = []
    for i, item in enumerate(items, 1):
        label = f'<strong>{_md_inline(item["label"])}</strong><br/>' if item.get("label") else ""
        text = _md_inline(item.get("text", ""))
        steps_html.append(
            f'<li style="display:flex;gap:16px;margin-bottom:20px;align-items:flex-start;">'
            f'<span style="flex:0 0 28px;height:28px;background:#1a73e8;color:white;border-radius:50%;'
            f'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem;">{i}</span>'
            f'<div style="padding-top:3px;">{label}{text}</div>'
            f'</li>'
        )
    return (
        f'<ol style="list-style:none;padding:0;margin:1.5rem 0;">'
        f'{"".join(steps_html)}'
        f'</ol>'
    )


def _render_table(b: dict) -> str:
    """HTML table with optional caption."""
    headers = b.get("headers", [])
    rows = b.get("rows", [])
    caption = b.get("caption", "")

    caption_html = f'<caption style="font-size:0.85rem;opacity:0.6;margin-bottom:8px;text-align:left;">{caption}</caption>' if caption else ""
    th_cells = "".join(
        f'<th style="background:#f1f3f4;border:1px solid #dadce0;padding:10px 14px;text-align:left;font-weight:600;white-space:nowrap;">{h}</th>'
        for h in headers
    )
    rows_html = []
    for i, row in enumerate(rows):
        bg = 'background:#f8f9fa;' if i % 2 else ''
        cells = "".join(
            f'<td style="border:1px solid #dadce0;padding:9px 14px;vertical-align:top;line-height:1.5;{bg}">{_md_inline(str(c))}</td>'
            for c in row
        )
        rows_html.append(f'<tr>{cells}</tr>')

    return (
        f'<div style="overflow-x:auto;margin:1.5rem 0;">'
        f'<table style="border-collapse:collapse;width:100%;font-size:0.9em;">'
        f'{caption_html}'
        f'<thead><tr>{th_cells}</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        f'</table></div>'
    )


_TAB_CSS = """
<style>
.tm-tabs{margin:1.5rem 0;border-radius:10px;overflow:hidden;border:1px solid #e0e0e0;}
.tm-tabs input[type=radio]{display:none;}
.tm-tab-labels{display:flex;background:#f8f9fa;border-bottom:1px solid #e0e0e0;overflow-x:auto;}
.tm-tab-label{padding:10px 20px;cursor:pointer;font-size:0.85rem;font-weight:600;color:#5f6368;
  white-space:nowrap;border-right:1px solid #e0e0e0;transition:all 0.15s ease;user-select:none;
  border-bottom:3px solid transparent;margin-bottom:-1px;}
.tm-tab-label:hover{background:#fff;color:#1a73e8;}
.tm-tab-panels{background:#fff;}
.tm-tab-panel{display:none;padding:0;}
.tm-tab-panel pre{margin:0;border-radius:0;border:none;}
</style>
"""

def _render_tabs(b: dict, _tab_counter=[0]) -> str:
    """CSS-only tabbed panels — typically used for multi-language code examples."""
    _tab_counter[0] += 1
    group = f"tmtabs{_tab_counter[0]}"
    tabs = b.get("tabs", [])
    if not tabs:
        return ""

    accent = b.get("accent", "#1a73e8")

    # Dynamic CSS for this tab group's checked states
    checked_css = "".join(
        f'#{group}_t{i}:checked ~ .tm-tab-labels .tm-tab-label[for="{group}_t{i}"]'
        f'{{background:#fff;color:{accent};border-bottom-color:{accent};}}\n'
        f'#{group}_t{i}:checked ~ .tm-tab-panels .tm-tab-panel:nth-child({i})'
        f'{{display:block;}}\n'
        for i in range(1, len(tabs) + 1)
    )

    inputs = "".join(
        f'<input type="radio" id="{group}_t{i}" name="{group}" {"checked" if i == 1 else ""}>'
        for i, _ in enumerate(tabs, 1)
    )
    labels = "".join(
        f'<label class="tm-tab-label" for="{group}_t{i}">{tab.get("label","Tab")}</label>'
        for i, tab in enumerate(tabs, 1)
    )
    panels = "".join(
        f'<div class="tm-tab-panel">{_render_code(tab)}</div>'
        for tab in tabs
    )

    return (
        f'{_TAB_CSS}'
        f'<style>{checked_css}</style>'
        f'<div class="tm-tabs">'
        f'{inputs}'
        f'<div class="tm-tab-labels">{labels}</div>'
        f'<div class="tm-tab-panels">{panels}</div>'
        f'</div>'
    )


def _render_key_value(b: dict) -> str:
    """Key-value pairs — for env vars, config options, API fields."""
    items = b.get("items", [])
    title = b.get("title", "")
    title_html = f'<p style="font-weight:600;margin-bottom:8px;">{title}</p>' if title else ""
    def _kv_row(item):
        required_html = "<strong>Required</strong> — " if item.get("required") else ""
        default_val = item.get("default")
        default_html = f'<br/><code style="color:#34a853;">default: {default_val}</code>' if default_val is not None else ""
        return (
            f'<tr>'
            f'<td style="padding:8px 12px;font-family:monospace;font-size:0.85em;color:#1a73e8;white-space:nowrap;'
            f'border-bottom:1px solid #f0f0f0;vertical-align:top;font-weight:600;">{item.get("key","")}</td>'
            f'<td style="padding:8px 12px;color:#5f6368;font-size:0.85em;border-bottom:1px solid #f0f0f0;">'
            f'{required_html}{_md_inline(item.get("description",""))}{default_html}'
            f'</td></tr>'
        )
    rows = "".join(_kv_row(item) for item in items)
    return (
        f'{title_html}'
        f'<div style="overflow-x:auto;margin:1.2rem 0;">'
        f'<table style="border-collapse:collapse;width:100%;background:#fafafa;border-radius:8px;overflow:hidden;">'
        f'<tbody>{rows}</tbody>'
        f'</table></div>'
    )


def _render_gallery(b: dict) -> str:
    """Image gallery — responsive grid with CSS-only lightbox on click."""
    images  = b.get("images", [])
    cols    = b.get("cols", 3)
    caption = b.get("caption", "")
    caption_html = f'<p style="font-size:0.82rem;opacity:0.6;margin-top:10px;text-align:center;">{caption}</p>' if caption else ""

    # Unique ID per gallery instance
    import hashlib
    gid = "g" + hashlib.md5("".join(i.get("url","") for i in images).encode()).hexdigest()[:6]

    lightbox_css = f"""
<style>
.{gid}-wrap{{display:grid;grid-template-columns:repeat({cols},1fr);gap:10px;margin:1.5rem 0;}}
@media(max-width:600px){{.{gid}-wrap{{grid-template-columns:repeat(2,1fr);}}}}
.{gid}-item{{position:relative;overflow:hidden;border-radius:8px;cursor:zoom-in;aspect-ratio:16/10;background:#f1f3f4;}}
.{gid}-item img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.2s ease;}}
.{gid}-item:hover img{{transform:scale(1.04);}}
.{gid}-item figcaption{{position:absolute;bottom:0;left:0;right:0;padding:6px 10px;
  background:linear-gradient(transparent,rgba(0,0,0,0.6));color:#fff;font-size:0.75rem;
  opacity:0;transition:opacity 0.2s ease;}}
.{gid}-item:hover figcaption{{opacity:1;}}
.{gid}-lb{{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.92);z-index:9999;
  align-items:center;justify-content:center;padding:20px;}}
.{gid}-lb:target{{display:flex;}}
.{gid}-lb img{{max-width:90vw;max-height:88vh;border-radius:8px;box-shadow:0 20px 60px rgba(0,0,0,0.5);}}
.{gid}-lb-close{{position:absolute;top:16px;right:24px;color:#fff;font-size:2rem;
  text-decoration:none;line-height:1;opacity:0.7;}}
.{gid}-lb-close:hover{{opacity:1;}}
.{gid}-lb figcaption{{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);
  color:rgba(255,255,255,0.7);font-size:0.85rem;text-align:center;}}
</style>"""

    items_html = []
    lightboxes_html = []

    for i, img in enumerate(images):
        url     = img.get("url", "")
        alt     = img.get("alt", "")
        cap     = img.get("caption", "")
        lb_id   = f"{gid}-lb{i}"
        cap_html = f"<figcaption>{cap}</figcaption>" if cap else ""

        items_html.append(
            f'<figure class="{gid}-item">'
            f'<a href="#{lb_id}" style="display:block;height:100%;">'
            f'<img src="{url}" alt="{alt}" loading="lazy"/>'
            f'</a>'
            f'{cap_html}'
            f'</figure>'
        )
        lightboxes_html.append(
            f'<div id="{lb_id}" class="{gid}-lb">'
            f'<a href="#" class="{gid}-lb-close">✕</a>'
            f'<img src="{url}" alt="{alt}"/>'
            f'{"<figcaption>" + cap + "</figcaption>" if cap else ""}'
            f'</div>'
        )

    return (
        f'{lightbox_css}'
        f'<div class="{gid}-wrap">{"".join(items_html)}</div>'
        f'{caption_html}'
        f'{"".join(lightboxes_html)}'
    )


def _render_video_pair(b: dict) -> str:
    """Two YouTube videos side by side with captions."""
    left  = b.get("left",  {})
    right = b.get("right", {})
    caption = b.get("caption", "")
    caption_html = f'<p style="font-size:0.82rem;opacity:0.6;margin-top:8px;text-align:center;">{caption}</p>' if caption else ""

    def video_cell(v):
        vid_id  = _youtube_id(v.get("url", ""))
        label   = v.get("label", "")
        label_html = f'<p style="font-size:0.82rem;font-weight:600;margin-bottom:6px;color:#3c4043;">{label}</p>' if label else ""
        params = f"?rel=0&modestbranding=1"
        return (
            f'<div style="flex:1;min-width:0;">'
            f'{label_html}'
            f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;">'
            f'<iframe src="https://www.youtube.com/embed/{vid_id}{params}" '
            f'style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" '
            f'allow="autoplay; encrypted-media" allowfullscreen></iframe>'
            f'</div></div>'
        )

    return (
        f'<div style="display:flex;gap:14px;margin:1.5rem 0;align-items:flex-start;">'
        f'{video_cell(left)}{video_cell(right)}'
        f'</div>'
        f'{caption_html}'
    )


def _render_carousel(b: dict) -> str:
    """CSS-only image/content carousel with dot indicators and prev/next arrows."""
    slides  = b.get("slides", [])
    caption = b.get("caption", "")
    accent  = b.get("accent", "#1a73e8")
    if not slides:
        return ""

    import hashlib
    cid = "c" + hashlib.md5("".join(s.get("url", s.get("label","")) for s in slides).encode()).hexdigest()[:6]
    n   = len(slides)

    # CSS — scoped to this carousel instance
    css_parts = [f"""
<style>
.{cid}{{position:relative;overflow:hidden;border-radius:12px;background:#000;margin:1.5rem 0;
  box-shadow:0 4px 24px rgba(0,0,0,0.12);}}
.{cid} input[type=radio]{{display:none;}}
.{cid}-track{{display:flex;transition:transform 0.45s cubic-bezier(0.77,0,0.175,1);width:{n*100}%;}}
.{cid}-slide{{width:{100//n}%;flex:0 0 {100//n}%;position:relative;}}
.{cid}-slide img{{width:100%;display:block;max-height:480px;object-fit:cover;}}
.{cid}-caption{{position:absolute;bottom:0;left:0;right:0;padding:14px 18px;
  background:linear-gradient(transparent,rgba(0,0,0,0.72));color:#fff;}}
.{cid}-caption strong{{display:block;font-size:1rem;margin-bottom:2px;}}
.{cid}-caption span{{font-size:0.82rem;opacity:0.8;}}
.{cid}-dots{{display:flex;justify-content:center;gap:8px;padding:12px;background:#111;}}
.{cid}-dot{{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,0.3);
  cursor:pointer;transition:all 0.2s;display:block;border:none;}}
.{cid}-arrows{{position:absolute;top:50%;transform:translateY(-50%);width:100%;
  display:flex;justify-content:space-between;padding:0 12px;pointer-events:none;z-index:10;box-sizing:border-box;}}
.{cid}-arrow{{width:38px;height:38px;border-radius:50%;background:rgba(255,255,255,0.15);
  backdrop-filter:blur(4px);color:#fff;display:flex;align-items:center;justify-content:center;
  font-size:1.1rem;cursor:pointer;pointer-events:all;transition:background 0.2s;text-decoration:none;
  border:1px solid rgba(255,255,255,0.2);}}
.{cid}-arrow:hover{{background:rgba(255,255,255,0.28);}}
</style>"""]

    # Per-slide checked states — move track and highlight dot
    for i in range(1, n + 1):
        offset = (i - 1) * (100 // n)
        css_parts.append(
            f'<style>#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-track'
            f'{{transform:translateX(-{offset}%);}}\n'
            f'#{cid}_s{i}:checked ~ .{cid}-dots .{cid}-dot:nth-child({i})'
            f'{{background:{accent};transform:scale(1.25);}}</style>'
        )

    # Radio inputs
    inputs = "".join(
        f'<input type="radio" id="{cid}_s{i}" name="{cid}" {"checked" if i == 1 else ""}>'
        for i in range(1, n + 1)
    )

    # Slides
    slides_html = ""
    for slide in slides:
        url        = slide.get("url", "")
        label      = slide.get("label", "")
        sub        = slide.get("subtitle", "")
        label_html = (
            f'<div class="{cid}-caption"><strong>{label}</strong>'
            f'{"<span>" + sub + "</span>" if sub else ""}</div>'
        ) if label else ""
        slides_html += (
            f'<div class="{cid}-slide">'
            f'<img src="{url}" alt="{label}" loading="lazy"/>'
            f'{label_html}'
            f'</div>'
        )

    # Arrow nav — labels pointing to adjacent slides (wrapping)
    def arrow(direction, target_idx):
        symbol = "‹" if direction == "prev" else "›"
        return (
            f'<label for="{cid}_s{target_idx}" class="{cid}-arrow">'
            f'{symbol}</label>'
        )

    arrows_html = []
    for i in range(1, n + 1):
        prev_i = n if i == 1 else i - 1
        next_i = 1 if i == n else i + 1
        css_parts.append(
            f'<style>#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-arrows '
            f'.{cid}-prev{{display:flex;}} '
            f'#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-arrows '
            f'.{cid}-next{{display:flex;}}</style>'
        )
        arrows_html.append(
            f'<style>'
            f'#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-arrows '
            f'.{cid}-prev{{content:"";}} </style>'
        )

    # Build per-slide arrow labels via stacking — simpler: always show prev/next for checked
    prev_labels = "".join(
        f'<label for="{cid}_s{n if i==1 else i-1}" '
        f'class="{cid}-arrow" '
        f'style="display:{"flex" if True else "none"};">‹</label>'
        for i in range(1, n + 1)
    )

    # Simpler arrow approach — one prev, one next, update target via checked state CSS
    prev_arrows = "".join(
        f'<style>#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-ap '
        f'{{display:none;}} '
        f'#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-ap[data-t="{n if i==1 else i-1}"]'
        f'{{display:flex;}}</style>'
        for i in range(1, n + 1)
    )
    next_arrows = "".join(
        f'<style>#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-an '
        f'{{display:none;}} '
        f'#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-an[data-t="{1 if i==n else i+1}"]'
        f'{{display:flex;}}</style>'
        for i in range(1, n + 1)
    )

    all_prev = "".join(
        f'<label for="{cid}_s{i}" class="{cid}-arrow {cid}-ap" data-t="{i}">‹</label>'
        for i in range(1, n + 1)
    )
    all_next = "".join(
        f'<label for="{cid}_s{i}" class="{cid}-arrow {cid}-an" data-t="{i}">›</label>'
        for i in range(1, n + 1)
    )

    dots = "".join(
        f'<label for="{cid}_s{i}" class="{cid}-dot"></label>'
        for i in range(1, n + 1)
    )

    caption_html = f'<p style="font-size:0.82rem;opacity:0.6;margin-top:8px;text-align:center;">{caption}</p>' if caption else ""

    return (
        "".join(css_parts)
        + prev_arrows + next_arrows
        + f'<div class="{cid}">'
        + inputs
        + f'<div class="{cid}-inner">'
        + f'<div class="{cid}-track">{slides_html}</div>'
        + f'<div class="{cid}-arrows"><div style="display:flex;">{all_prev}</div>'
        + f'<div style="display:flex;">{all_next}</div></div>'
        + f'</div>'
        + f'<div class="{cid}-dots">{dots}</div>'
        + f'</div>'
        + caption_html
    )


def _render_stat_card(b: dict) -> str:
    """Glowing neon stat card — large value with label and optional delta.

    Inspired by UIverse.io neon card patterns (uiverse.io).
    Credit: UIverse.io community — MIT License
    """
    value   = b.get("value", "—")
    label   = b.get("label", "")
    delta   = b.get("delta", "")
    accent  = b.get("accent", "#00f2ff")
    is_up   = b.get("is_up", True)
    delta_color = "#00ff88" if is_up else "#ff4444"
    delta_arrow = "▲" if is_up else "▼"
    delta_html = (
        f'<span style="font-size:0.85rem;font-weight:700;color:{delta_color};margin-left:10px;">'
        f'{delta_arrow} {delta}</span>'
    ) if delta else ""

    return (
        f'<div style="display:inline-block;background:linear-gradient(135deg,#0d1117 0%,#1a1f2e 100%);'
        f'border:1px solid {accent}44;border-radius:12px;padding:24px 32px;margin:1rem 0;'
        f'box-shadow:0 0 20px {accent}22,inset 0 0 20px {accent}08;min-width:200px;text-align:center;">'
        f'<div style="font-size:0.75rem;font-weight:700;color:{accent};letter-spacing:0.12em;'
        f'text-transform:uppercase;margin-bottom:8px;">{label}</div>'
        f'<div style="font-size:2.8rem;font-weight:900;color:#ffffff;line-height:1;font-family:monospace;">'
        f'{value}{delta_html}'
        f'</div>'
        f'</div>'
    )


def _render_progress_bar(b: dict) -> str:
    """Animated CSS progress bar with glow effect.

    Inspired by UIverse.io animated loader patterns (uiverse.io).
    Credit: UIverse.io community — MIT License
    """
    import hashlib
    pid     = "p" + hashlib.md5(b.get("label","").encode()).hexdigest()[:6]
    value   = min(100, max(0, int(b.get("value", 0))))
    label   = b.get("label", "")
    accent  = b.get("accent", "#00f2ff")
    show_pct = b.get("show_percent", True)
    caption = b.get("caption", "")

    pct_html = f'<span style="font-size:0.8rem;font-weight:700;color:{accent};">{value}%</span>' if show_pct else ""
    caption_html = f'<p style="font-size:0.78rem;opacity:0.5;margin-top:4px;">{caption}</p>' if caption else ""

    return (
        f'<style>'
        f'@keyframes {pid}-glow{{0%,100%{{box-shadow:0 0 6px {accent}88;}}50%{{box-shadow:0 0 16px {accent};}} }}'
        f'</style>'
        f'<div style="margin:1rem 0;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        f'<span style="font-size:0.85rem;font-weight:600;">{label}</span>'
        f'{pct_html}'
        f'</div>'
        f'<div style="background:rgba(255,255,255,0.08);border-radius:100px;height:10px;overflow:hidden;">'
        f'<div style="width:{value}%;height:100%;border-radius:100px;background:linear-gradient(90deg,{accent},{accent}99);'
        f'animation:{pid}-glow 2s ease-in-out infinite;transition:width 0.8s ease;"></div>'
        f'</div>'
        f'{caption_html}'
        f'</div>'
    )


def _render_badge_group(b: dict) -> str:
    """Group of status badges with optional pulse animation.

    Inspired by UIverse.io badge and chip patterns (uiverse.io).
    Credit: UIverse.io community — MIT License
    """
    badges  = b.get("badges", [])
    title   = b.get("title", "")
    title_html = f'<p style="font-size:0.82rem;font-weight:600;margin-bottom:8px;opacity:0.7;">{title}</p>' if title else ""

    COLOR_MAP = {
        "green":  ("#00ff88", "#003322"),
        "cyan":   ("#00f2ff", "#002233"),
        "blue":   ("#4285f4", "#001a44"),
        "yellow": ("#f9ab00", "#332200"),
        "red":    ("#ff4444", "#330011"),
        "purple": ("#a855f7", "#1a0033"),
        "grey":   ("#9aa0a6", "#1a1a1a"),
    }

    badges_html = []
    for badge in badges:
        text   = badge.get("text", "")
        color  = badge.get("color", "grey")
        pulse  = badge.get("pulse", False)
        fg, bg = COLOR_MAP.get(color, COLOR_MAP["grey"])

        import hashlib
        bid = "b" + hashlib.md5(text.encode()).hexdigest()[:5]
        pulse_css = (
            f'<style>@keyframes {bid}-p{{0%,100%{{box-shadow:0 0 0 0 {fg}66;}}70%{{box-shadow:0 0 0 6px transparent;}} }}</style>'
            f'<style>.{bid}{{animation:{bid}-p 1.5s infinite;}}</style>'
        ) if pulse else ""
        dot = f'<span style="width:7px;height:7px;border-radius:50%;background:{fg};display:inline-block;margin-right:6px;"></span>' if pulse else ""

        badges_html.append(
            f'{pulse_css}'
            f'<span class="{bid}" style="display:inline-flex;align-items:center;background:{bg};color:{fg};'
            f'border:1px solid {fg}44;border-radius:100px;padding:4px 12px;font-size:0.78rem;'
            f'font-weight:700;letter-spacing:0.04em;margin:3px;">'
            f'{dot}{text}</span>'
        )

    return (
        f'<div style="margin:1rem 0;">'
        f'{title_html}'
        f'<div style="display:flex;flex-wrap:wrap;gap:4px;">{"".join(badges_html)}</div>'
        f'</div>'
    )


def _render_timeline(b: dict) -> str:
    """Vertical timeline — date, title, body per event. Good for changelogs, journeys, release notes."""
    events = b.get("events", [])
    accent = b.get("accent", "#1a73e8")
    title  = b.get("title", "")
    title_html = f'<p style="font-weight:700;font-size:1.05rem;margin-bottom:20px;">{title}</p>' if title else ""

    items_html = []
    for i, event in enumerate(events):
        is_last = i == len(events) - 1
        date    = event.get("date", "")
        label   = event.get("label", "")
        text    = _md_inline(event.get("text", ""))
        tag     = event.get("tag", "")
        tag_html = (
            f'<span style="background:{accent}18;color:{accent};font-size:0.72rem;font-weight:700;'
            f'padding:2px 8px;border-radius:10px;margin-left:8px;vertical-align:middle;">{tag}</span>'
        ) if tag else ""

        connector = "" if is_last else '<div style="width:2px;background:#e0e0e0;flex:1;min-height:24px;margin-top:4px;"></div>'
        items_html.append(
            f'<div style="display:flex;gap:0;position:relative;">'
            # Left column — dot + line
            f'<div style="display:flex;flex-direction:column;align-items:center;width:40px;flex:0 0 40px;">'
            f'<div style="width:14px;height:14px;border-radius:50%;background:{accent};'
            f'border:3px solid #fff;box-shadow:0 0 0 2px {accent};flex:0 0 14px;margin-top:3px;z-index:1;"></div>'
            f'{connector}'
            f'</div>'
            # Right column — content
            f'<div style="padding-bottom:28px;padding-left:12px;flex:1;min-width:0;">'
            f'<div style="display:flex;align-items:baseline;flex-wrap:wrap;gap:6px;margin-bottom:4px;">'
            f'<span style="font-size:0.78rem;font-weight:600;color:{accent};font-family:monospace;letter-spacing:0.04em;">{date}</span>'
            f'{tag_html}'
            f'</div>'
            f'<p style="font-weight:700;font-size:0.95rem;margin:0 0 4px;">{label}</p>'
            f'<p style="color:#5f6368;font-size:0.88rem;line-height:1.6;margin:0;">{text}</p>'
            f'</div>'
            f'</div>'
        )

    return (
        f'<div style="margin:1.5rem 0;padding:20px 20px 0;background:#fafafa;border-radius:10px;border:1px solid #e0e0e0;">'
        f'{title_html}'
        f'{"".join(items_html)}'
        f'</div>'
    )


def _render_annotated_code(b: dict) -> str:
    """Code block with numbered callout bubbles on specific lines, plus explanation list below."""
    language    = b.get("language", "")
    code_lines  = b.get("code", "").split("\n")
    annotations = b.get("annotations", [])  # [{line: 3, text: "explanation"}]
    caption     = b.get("caption", "")

    # Build line-number → annotation-number map
    line_map = {a["line"]: i + 1 for i, a in enumerate(annotations)}

    # Render code with inline callout badges
    rendered_lines = []
    for i, line in enumerate(code_lines, 1):
        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if i in line_map:
            num = line_map[i]
            badge = (
                f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                f'width:18px;height:18px;border-radius:50%;background:#f9ab00;color:#fff;'
                f'font-size:0.7rem;font-weight:800;margin-left:8px;vertical-align:middle;'
                f'flex-shrink:0;line-height:1;">{num}</span>'
            )
            rendered_lines.append(f'<span style="display:block;">{escaped}{badge}</span>')
        else:
            rendered_lines.append(f'<span style="display:block;">{escaped}</span>')

    code_html = "".join(rendered_lines)
    caption_html = f'<p style="font-size:0.8rem;opacity:0.6;margin:6px 0 0;text-align:center;">{caption}</p>' if caption else ""

    # Annotation explanations
    annotation_items = "".join(
        f'<li style="display:flex;gap:12px;margin-bottom:12px;align-items:flex-start;">'
        f'<span style="flex:0 0 22px;height:22px;border-radius:50%;background:#f9ab00;color:#fff;'
        f'font-size:0.72rem;font-weight:800;display:flex;align-items:center;justify-content:center;">{i+1}</span>'
        f'<span style="font-size:0.88rem;color:#3c4043;line-height:1.6;padding-top:2px;">{_md_inline(a.get("text",""))}</span>'
        f'</li>'
        for i, a in enumerate(annotations)
    )

    return (
        f'<div style="margin:1.5rem 0;">'
        f'<pre style="margin:0;padding:18px;background:#1e1e2e;border-radius:10px 10px 0 0;'
        f'overflow-x:auto;font-size:0.84rem;line-height:1.7;color:#cdd6f4;">'
        f'<code class="language-{language}">{code_html}</code>'
        f'</pre>'
        f'{caption_html}'
        f'<ol style="list-style:none;padding:16px 20px;margin:0;background:#fffbf0;'
        f'border:1px solid #f9ab0033;border-top:none;border-radius:0 0 10px 10px;">'
        f'{annotation_items}'
        f'</ol>'
        f'</div>'
    )


# ── Auto-generated stubs ─────────────────────────────────────────────────────

def _render_sparkline(b: dict) -> str:
    """TODO: Renders a small, simple line chart without axes or coordinates, showing general """
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ sparkline ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'



def _render_metric_delta(b: dict) -> str:
    """TODO: Renders a key performance indicator with its current value and a numerical or pe"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ metric_delta ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_trend_indicator(b: dict) -> str:
    """TODO: Renders a simple visual indicator (e.g., arrow, icon) representing the direction"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ trend_indicator ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_breadcrumb(b: dict) -> str:
    """TODO: A navigation aid indicating the user's current location within a hierarchical st"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ breadcrumb ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pagination(b: dict) -> str:
    """TODO: A control for navigating through a series of pages or results."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pagination ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_stepper(atom: dict) -> str:
    import hashlib
    uid        = hashlib.md5(str(atom).encode()).hexdigest()[:6]
    raw_steps  = atom.get("steps", [])
    active_idx = int(atom.get("active_index", 0))
    color      = atom.get("color", "#38bdf8")
    heading    = atom.get("label", atom.get("title", ""))
    # Normalise to {label, description}
    steps = []
    for s in raw_steps:
        if isinstance(s, str):
            steps.append({"label": s, "description": ""})
        elif isinstance(s, dict):
            # support both new (active_index) and legacy (is_current/is_completed) contracts
            if "is_current" in s or "is_completed" in s:
                steps.append({"label": s.get("label", ""), "description": s.get("description", ""),
                               "_legacy": s})
            else:
                steps.append({"label": s.get("label", s.get("title", "")),
                               "description": s.get("description", s.get("body", ""))})
    # For legacy steps derive active_idx from is_current
    if any("_legacy" in s for s in steps):
        for i, s in enumerate(steps):
            if s.get("_legacy", {}).get("is_current"):
                active_idx = i
                break
    check_len = 18  # approximate path length for M4,10 L8,14 L16,6 in 20×20 viewBox
    items_html = []
    for i, step in enumerate(steps):
        # Determine state
        legacy = step.get("_legacy", {})
        if legacy:
            completed = legacy.get("is_completed", False)
            active    = legacy.get("is_current", False)
        else:
            completed = i < active_idx
            active    = i == active_idx
        # Indicator
        if completed:
            indicator = (
                f'<div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;'
                f'background:{color}22;border:2px solid {color};display:flex;'
                f'align-items:center;justify-content:center;">'
                f'<svg width="14" height="14" viewBox="0 0 20 20" fill="none" '
                f'stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
                f'<style>@keyframes ck_{uid}_{i}{{to{{stroke-dashoffset:0;}}}}'
                f'.ck_{uid}_{i}{{stroke-dasharray:{check_len};stroke-dashoffset:{check_len};'
                f'animation:ck_{uid}_{i} 0.35s ease-out {i*0.08:.2f}s forwards;}}</style>'
                f'<path class="ck_{uid}_{i}" d="M4,10 L8,14 L16,6"/>'
                f'</svg></div>'
            )
            lc, dc = "#cbd5e1", "#475569"
        elif active:
            indicator = (
                f'<div style="position:relative;width:28px;height:28px;flex-shrink:0;">'
                f'<style>@keyframes asp_{uid}{{0%{{transform:scale(0.85);opacity:0.6;}}'
                f'100%{{transform:scale(1.9);opacity:0;}}}}'
                f'.asp_{uid}{{animation:asp_{uid} 1.8s ease-out infinite;}}</style>'
                f'<div class="asp_{uid}" style="position:absolute;inset:0;border-radius:50%;'
                f'border:2px solid {color};"></div>'
                f'<div style="position:absolute;inset:0;border-radius:50%;border:2px solid {color};'
                f'background:{color}22;display:flex;align-items:center;justify-content:center;">'
                f'<div style="width:8px;height:8px;border-radius:50%;background:{color};'
                f'box-shadow:0 0 6px {color};"></div></div></div>'
            )
            lc, dc = "#f1f5f9", "#94a3b8"
        else:  # pending
            indicator = (
                f'<div style="width:28px;height:28px;border-radius:50%;flex-shrink:0;'
                f'border:2px solid #334155;background:#1e293b;display:flex;'
                f'align-items:center;justify-content:center;">'
                f'<div style="width:6px;height:6px;border-radius:50%;background:#475569;"></div>'
                f'</div>'
            )
            lc, dc = "#64748b", "#374151"
        desc_html = (
            f'<div style="font-size:0.8rem;color:{dc};margin-top:2px;">{step["description"]}</div>'
        ) if step["description"] else ""
        # Connector line between steps
        connector = ""
        if i < len(steps) - 1:
            lc2 = color if completed else "#1e293b"
            connector = (
                f'<div style="width:2px;height:14px;margin:3px 0 3px 13px;'
                f'background:{lc2};border-radius:1px;"></div>'
            )
        items_html.append(
            f'<div>'
            f'<div style="display:flex;align-items:flex-start;gap:12px;">'
            f'{indicator}'
            f'<div style="padding-top:4px;">'
            f'<div style="font-size:0.95rem;font-weight:600;color:{lc};">{step["label"]}</div>'
            f'{desc_html}</div></div>'
            f'{connector}</div>'
        )
    heading_html = (
        f'<div style="font-size:0.85rem;font-weight:700;color:#64748b;letter-spacing:.07em;'
        f'text-transform:uppercase;margin-bottom:16px;">{heading}</div>'
    ) if heading else ""
    return (
        f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:14px;'
        f'padding:20px 24px;margin:1rem 0;">'
        f'{heading_html}{"".join(items_html)}</div>'
    )

def _render_tab_bar(b: dict) -> str:
    """TODO: A horizontal navigation component displaying a set of clickable tabs, typically """
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ tab_bar ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_anchor_list(b: dict) -> str:
    """TODO: A list of links that navigate to specific sections within the current document o"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ anchor_list ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_faq_accordion(b: dict) -> str:
    """TODO: Renders a list of questions and answers, where answers are hidden until the ques"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ faq_accordion ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_glossary_term(b: dict) -> str:
    """TODO: Renders a term with its definition, often with an optional link for more details"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ glossary_term ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_footnote(b: dict) -> str:
    fid  = b.get("id", "1")
    text = b.get("text", "")
    return (f'<div style="margin:0.5rem 0;font-size:0.78rem;color:#6b7280;padding-left:1.2rem;'
            f'border-left:2px solid #e5e7eb;">'
            f'<sup style="color:#7c3aed;font-weight:600;">[{fid}]</sup> {text}'
            f'</div>')

def _render_footnote_group(b: dict) -> str:
    footnotes = b.get("footnotes", [])
    rows = "".join(
        f'<div style="margin:4px 0;font-size:0.78rem;color:#6b7280;padding-left:1.2rem;">'
        f'<sup style="color:#7c3aed;font-weight:600;">[{fn.get("id","?")}]</sup> {fn.get("text","")}'
        f'</div>'
        for fn in footnotes
    )
    return (f'<div style="margin:1.5rem 0;padding:12px 16px;border-top:1px solid #e5e7eb;">'
            f'<div style="font-size:0.72rem;font-weight:600;color:#9ca3af;text-transform:uppercase;'
            f'letter-spacing:0.05em;margin-bottom:8px;">Footnotes</div>'
            f'{rows}</div>')

def _render_blockquote_with_avatar(b: dict) -> str:
    """TODO: Renders a blockquote with an associated avatar and attribution."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ blockquote_with_avatar ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pull_stat(b: dict) -> str:
    """TODO: Renders a prominent, large statistic or number, often with a brief descriptive l"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pull_stat ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_accordion_item(b: dict) -> str:
    """TODO: Renders a single section of content that can be expanded or collapsed by clickin"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ accordion_item ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_tooltip(b: dict) -> str:
    text   = b.get("text", "")
    target = b.get("target", "hover me")
    return (f'<div style="margin:1rem 0;display:inline-block;position:relative;">'
            f'<span style="border-bottom:1px dashed #7c3aed;cursor:help;color:#7c3aed;">{target}</span>'
            f'<div style="margin-top:6px;padding:6px 10px;background:#1f2937;color:#f9fafb;'
            f'border-radius:6px;font-size:0.78rem;max-width:240px;line-height:1.4;">{text}</div>'
            f'</div>')

def _render_hover_card(b: dict) -> str:
    trigger  = b.get("trigger", "Hover")
    blocks   = b.get("blocks", [])
    content  = render(blocks) if blocks else ""
    return (f'<div style="margin:1rem 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">'
            f'<div style="padding:10px 14px;background:#f3f4f6;font-size:0.85rem;font-weight:600;'
            f'color:#374151;border-bottom:1px solid #e5e7eb;">{trigger}</div>'
            f'<div style="padding:12px 14px;font-size:0.85rem;">{content}</div>'
            f'</div>')

def _render_collapsible_panel(b: dict) -> str:
    title  = b.get("title", "Panel")
    blocks = b.get("blocks", [])
    content = render(blocks) if blocks else ""
    return (f'<details style="margin:1rem 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">'
            f'<summary style="padding:10px 14px;background:#f3f4f6;font-weight:600;font-size:0.85rem;'
            f'color:#374151;cursor:pointer;list-style:none;">▶ {title}</summary>'
            f'<div style="padding:12px 14px;font-size:0.85rem;">{content}</div>'
            f'</details>')

def _render_css_modal(b: dict) -> str:
    trigger = b.get("trigger_text", "Open modal")
    blocks  = b.get("blocks", [])
    content = render(blocks) if blocks else ""
    return (f'<div style="margin:1rem 0;">'
            f'<button style="padding:8px 16px;background:#7c3aed;color:#fff;border:none;border-radius:6px;'
            f'font-size:0.85rem;cursor:pointer;">{trigger}</button>'
            f'<div style="margin-top:8px;padding:16px;border:1px solid #e5e7eb;border-radius:8px;'
            f'background:#fff;box-shadow:0 4px 12px rgba(0,0,0,0.08);font-size:0.85rem;">{content}</div>'
            f'</div>')

def _render_audio_player(b: dict) -> str:
    """TODO: Renders an embedded audio player for a given URL."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ audio_player ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_audio_link(b: dict) -> str:
    """TODO: Renders a clickable link to an audio file, often with an audio icon."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ audio_link ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pdf_preview(b: dict) -> str:
    """TODO: Renders an image thumbnail of a PDF document with a link to the full PDF."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pdf_preview ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_document_link(b: dict) -> str:
    """TODO: Renders a clickable link to a document (e.g., PDF, DOCX), often with a document """
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ document_link ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_video_thumbnail(b: dict) -> str:
    """TODO: Renders a static image thumbnail for a video, with a play icon overlay and a lin"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ video_thumbnail ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_video_card(b: dict) -> str:
    """TODO: Renders a card with a video thumbnail, title, and description, linking to the vi"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ video_card ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_code_diff(atom: dict) -> str:
    import difflib, html as _html
    old_code  = atom.get("old_code", atom.get("old_text", ""))
    new_code  = atom.get("new_code", atom.get("new_text", ""))
    label     = atom.get("label", "")
    language  = atom.get("language", "")
    show_ln   = atom.get("show_line_numbers", True)
    ctx       = int(atom.get("context_lines", 3))
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    # Build unified diff with context; fall back to ndiff for small inputs
    diff      = list(difflib.ndiff(old_lines, new_lines))
    rows      = []
    old_ln = new_ln = 0
    for line in diff:
        tag, text = line[:2], _html.escape(line[2:])
        if tag == "  ":
            old_ln += 1; new_ln += 1
            ln = f'<span style="min-width:28px;display:inline-block;color:#374151;user-select:none;padding-right:10px;">{new_ln}</span>' if show_ln else ""
            rows.append(f'<div style="padding:1px 14px;display:flex;">{ln}<span style="color:#94a3b8;white-space:pre;flex:1;">{text}</span></div>')
        elif tag == "- ":
            old_ln += 1
            ln = f'<span style="min-width:28px;display:inline-block;color:#7f1d1d;user-select:none;padding-right:10px;">{old_ln}</span>' if show_ln else ""
            rows.append(f'<div style="padding:1px 14px;display:flex;background:#7f1d1d2a;border-left:3px solid #ef4444;">{ln}<span style="color:#fca5a5;white-space:pre;flex:1;">- {text}</span></div>')
        elif tag == "+ ":
            new_ln += 1
            ln = f'<span style="min-width:28px;display:inline-block;color:#064e3b;user-select:none;padding-right:10px;">{new_ln}</span>' if show_ln else ""
            rows.append(f'<div style="padding:1px 14px;display:flex;background:#0640261f;border-left:3px solid #34d399;">{ln}<span style="color:#6ee7b7;white-space:pre;flex:1;">+ {text}</span></div>')
        # skip "? " hint lines
    header = ""
    if label or language:
        lbl  = f'<span style="font-size:13px;font-weight:600;color:#94a3b8;">{label}</span>' if label else ""
        lang = f'<span style="font-size:11px;color:#64748b;background:#1e293b;padding:2px 8px;border-radius:4px;">{language}</span>' if language else ""
        header = (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:10px 14px;border-bottom:1px solid #1e293b;">{lbl}{lang}</div>'
        )
    return (
        f'<div style="background:#0a0f1d;border:1px solid #1e293b;border-radius:12px;'
        f'margin:1rem 0;overflow:hidden;font-family:\'JetBrains Mono\',monospace;font-size:0.82rem;">'
        f'{header}<div style="padding:6px 0;">{"".join(rows)}</div></div>'
    )

def _render_code_snippet_pair(b: dict) -> str:
    """TODO: Renders two distinct code snippets side-by-side or stacked, without diff highlig"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ code_snippet_pair ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_framed_screenshot(b: dict) -> str:
    url     = b.get("url", "")
    caption = b.get("caption", "")
    alt     = b.get("alt", caption or "screenshot")
    # Browser chrome bar
    chrome = (
        '<div style="background:#e8eaed;border-radius:8px 8px 0 0;padding:8px 12px;'
        'display:flex;align-items:center;gap:6px;border-bottom:1px solid #dadce0;">'
        '<span style="width:10px;height:10px;border-radius:50%;background:#ea4335;display:inline-block;"></span>'
        '<span style="width:10px;height:10px;border-radius:50%;background:#fbbc04;display:inline-block;"></span>'
        '<span style="width:10px;height:10px;border-radius:50%;background:#34a853;display:inline-block;"></span>'
        '<span style="flex:1;background:#fff;border-radius:4px;height:18px;margin-left:6px;'
        'border:1px solid #dadce0;"></span>'
        '</div>'
    )
    caption_html = (
        f'<p style="font-size:0.78rem;color:#5f6368;margin:8px 0 0;text-align:center;">{caption}</p>'
        if caption else ""
    )
    return (
        f'<div style="margin:1.5rem 0;border:1px solid #dadce0;border-radius:10px;'
        f'overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">'
        f'{chrome}'
        f'<img src="{url}" alt="{alt}" style="width:100%;height:auto;display:block;"/>'
        f'</div>'
        f'{caption_html}'
    )

def _render_image_with_caption(b: dict) -> str:
    """TODO: Renders a single image with a descriptive caption below it."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ image_with_caption ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_alert_banner(b: dict) -> str:
    """TODO: A prominent banner displaying a message, often with an icon and an optional acti"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ alert_banner ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_toast_notification(b: dict) -> str:
    """TODO: A small, temporary, non-intrusive message that appears and disappears automatica"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ toast_notification ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_loading_skeleton(b: dict) -> str:
    """TODO: A placeholder UI that shows the structure of content while it's loading, indicat"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ loading_skeleton ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_empty_state(b: dict) -> str:
    """TODO: A UI pattern displayed when there is no data to show, often with an image, messa"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ empty_state ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_spinner(b: dict) -> str:
    """TODO: A simple rotating animation indicating that content is loading or an operation i"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ spinner ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_status_pill(b: dict) -> str:
    """TODO: A small, colored label or "pill" used to display a concise status for an item."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ status_pill ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_inline_feedback_message(b: dict) -> str:
    """TODO: A small, contextual message displayed inline with content, often used for valida"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ inline_feedback_message ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_rating_stars(b: dict) -> str:
    """TODO: A visual component allowing users to rate an item using a series of stars, or di"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ rating_stars ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_progress_circle(atom: dict) -> str:
    import hashlib, math
    uid   = hashlib.md5(str(atom).encode()).hexdigest()[:6]
    value = max(0, min(100, int(atom.get("value", 0))))
    label = atom.get("label", "")
    color = atom.get("color", "#38bdf8")
    size_map = {"sm": 80, "md": 120, "lg": 160}
    px    = size_map.get(str(atom.get("size", "md")), 120)
    r     = 36
    circ  = round(2 * math.pi * r, 2)
    offset = round(circ * (1 - value / 100), 2)
    fs    = max(11, px // 6)
    label_html = (
        f'<div style="font-size:{max(10,px//10)}px;color:#94a3b8;margin-top:6px;'
        f'text-align:center;max-width:{px}px;">{label}</div>'
    ) if label else ""
    return (
        f'<style>'
        f'.pc_{uid}{{stroke-dasharray:{circ};stroke-dashoffset:{circ};'
        f'animation:pc_{uid} 1.2s ease-out forwards;}}'
        f'@keyframes pc_{uid}{{to{{stroke-dashoffset:{offset};}}}}'
        f'</style>'
        f'<div style="display:inline-flex;flex-direction:column;align-items:center;margin:1rem 0;">'
        f'<div style="position:relative;width:{px}px;height:{px}px;">'
        f'<svg width="{px}" height="{px}" viewBox="0 0 100 100" '
        f'style="transform:rotate(-90deg);display:block;">'
        f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="#1e293b" stroke-width="9"/>'
        f'<circle class="pc_{uid}" cx="50" cy="50" r="{r}" fill="none" stroke="{color}" '
        f'stroke-width="9" stroke-linecap="round"/>'
        f'</svg>'
        f'<div style="position:absolute;inset:0;display:flex;align-items:center;'
        f'justify-content:center;font-size:{fs}px;font-weight:700;color:#f1f5f9;'
        f'font-family:monospace;">{value}%</div>'
        f'</div>{label_html}</div>'
    )

def _render_action_required_card(b: dict) -> str:
    """TODO: A card highlighting an important status or issue that requires immediate user at"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ action_required_card ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_feature_matrix(b: dict) -> str:
    """TODO: Renders a table comparing features across multiple products or versions."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ feature_matrix ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pricing_tier_card(b: dict) -> str:
    """TODO: Renders a single pricing plan with its name, price, key features, and an optiona"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pricing_tier_card ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pricing_tier_group(b: dict) -> str:
    """TODO: Renders a collection of pricing tier cards, typically for comparing different su"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pricing_tier_group ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pros_cons_list(b: dict) -> str:
    """TODO: Renders a two-column list itemizing advantages and disadvantages for a single su"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pros_cons_list ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_side_by_side_spec(b: dict) -> str:
    """TODO: Renders a detailed comparison of two items, displaying their attributes and valu"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ side_by_side_spec ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_product_spec_table(b: dict) -> str:
    """TODO: Renders a table detailing technical specifications or features for a single prod"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ product_spec_table ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_comparison_grid(b: dict) -> str:
    """TODO: Renders a grid comparing multiple products or services with features, often usin"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ comparison_grid ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_versus_block(b: dict) -> str:
    """TODO: Renders a block explicitly comparing two entities with a prominent "VS" separato"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ versus_block ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_rating_comparison(b: dict) -> str:
    """TODO: Renders a comparison of multiple items based on star ratings or numerical scores"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ rating_comparison ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_capability_checklist(b: dict) -> str:
    """TODO: Renders a list of capabilities, indicating which items possess each capability u"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ capability_checklist ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_toggle_switch(b: dict) -> str:
    """TODO: Renders a visual on/off switch."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ toggle_switch ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_expandable_text(b: dict) -> str:
    """TODO: Renders a block of text that can be expanded or collapsed to reveal more content"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ expandable_text ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_flip_card(b: dict) -> str:
    front = render(b.get("front_blocks", []))
    back  = render(b.get("back_blocks", []))
    return (f'<div style="margin:1rem 0;display:grid;grid-template-columns:1fr 1fr;gap:8px;">'
            f'<div style="padding:12px;border:2px solid #7c3aed;border-radius:8px;background:#faf5ff;">'
            f'<div style="font-size:0.7rem;font-weight:600;color:#7c3aed;margin-bottom:6px;text-transform:uppercase;">Front</div>'
            f'{front}</div>'
            f'<div style="padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#f9fafb;">'
            f'<div style="font-size:0.7rem;font-weight:600;color:#6b7280;margin-bottom:6px;text-transform:uppercase;">Back (flipped)</div>'
            f'{back}</div>'
            f'</div>')

def _render_image_hotspots(b: dict) -> str:
    """TODO: Renders an image with interactive points that display information on hover."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ image_hotspots ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_css_dropdown_menu(b: dict) -> str:
    """<details>-based dropdown menu — CSS-only, no JS."""
    trigger = b.get("trigger_text", b.get("trigger", b.get("label", "Menu")))
    items   = b.get("menu_items", b.get("items", []))
    items_html = "".join(
        f'<a href="{item.get("url","#")}" style="display:block;padding:8px 16px;'
        f'font-size:0.87rem;color:#3c4043;text-decoration:none;white-space:nowrap;'
        f'transition:background .1s;" onmouseover="this.style.background=\'#f8f9fa\'" '
        f'onmouseout="this.style.background=\'\';">{item.get("label","")}</a>'
        for item in items
    )
    return (
        f'<div style="margin:1rem 0;display:inline-block;">'
        f'<details style="position:relative;">'
        f'<summary style="list-style:none;display:inline-flex;align-items:center;gap:6px;'
        f'padding:8px 14px;background:#fff;border:1px solid #dadce0;border-radius:6px;'
        f'cursor:pointer;font-size:0.88rem;font-weight:500;color:#3c4043;user-select:none;">'
        f'{trigger}'
        f'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">'
        f'<path d="M6 9l6 6 6-6"/></svg></summary>'
        f'<div style="position:absolute;top:calc(100% + 4px);left:0;z-index:20;'
        f'background:#fff;border:1px solid #dadce0;border-radius:8px;'
        f'box-shadow:0 4px 16px rgba(0,0,0,0.12);min-width:160px;padding:4px 0;overflow:hidden;">'
        f'{items_html}</div>'
        f'</details></div>'
    )


def _render_star_rating_input(b: dict) -> str:
    """CSS-only interactive star rating via reversed radio buttons."""
    name    = b.get("name", "rating")
    max_s   = int(b.get("max_stars", 5))
    initial = int(b.get("initial_rating", 0))
    label   = b.get("label", "")
    uid     = abs(hash(name + str(max_s))) % 100000

    inputs_html = "".join(
        f'<input type="radio" id="sr{uid}_{i}" name="sr{uid}" value="{i}"'
        f'{" checked" if i == initial else ""} style="display:none;">'
        for i in range(max_s, 0, -1)
    )
    labels_html = "".join(
        f'<label for="sr{uid}_{i}" title="{i} star{"s" if i>1 else ""}" '
        f'style="font-size:1.7rem;cursor:pointer;color:#d1d5db;transition:color .1s;">★</label>'
        for i in range(max_s, 0, -1)
    )
    style = (
        f'<style>'
        f'.sr{uid} input:checked ~ label,'
        f'.sr{uid} label:hover,'
        f'.sr{uid} label:hover ~ label {{color:#facc15;}}'
        f'</style>'
    )
    label_html = (
        f'<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:6px;">{label}</div>'
    ) if label else ""
    return (
        f'{style}<div style="margin:1rem 0;">{label_html}'
        f'<div class="sr{uid}" style="display:flex;flex-direction:row-reverse;'
        f'justify-content:flex-end;gap:2px;">{inputs_html}{labels_html}</div></div>'
    )


def _render_segmented_control(b: dict) -> str:
    """Radio-button pill strip — single-option selector."""
    options  = b.get("options", [])
    selected = b.get("selected_value", b.get("selected", ""))
    name     = b.get("name", "seg")
    label    = b.get("label", "")
    uid      = abs(hash(str(options) + name)) % 100000

    norm = [{"value": o, "label": o} if isinstance(o, str) else o for o in options]
    if not selected and norm:
        selected = norm[0]["value"]

    style = (
        f'<style>'
        f'.sgc{uid} input{{display:none;}}'
        f'.sgc{uid} label{{padding:7px 16px;font-size:0.85rem;font-weight:500;cursor:pointer;'
        f'color:#5f6368;border-right:1px solid #dadce0;white-space:nowrap;'
        f'transition:background .1s,color .1s;}}'
        f'.sgc{uid} label:last-of-type{{border-right:none;}}'
        f'.sgc{uid} input:checked+label{{background:#e8f0fe;color:#1a73e8;font-weight:600;}}'
        f'</style>'
    )
    items_html = "".join(
        f'<input type="radio" id="sgc{uid}_{o["value"]}" name="{name}_{uid}" '
        f'value="{o["value"]}"{" checked" if o["value"]==selected else ""}>'
        f'<label for="sgc{uid}_{o["value"]}">{o["label"]}</label>'
        for o in norm
    )
    label_html = (
        f'<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:6px;">{label}</div>'
    ) if label else ""
    return (
        f'{style}<div style="margin:1rem 0;">{label_html}'
        f'<div class="sgc{uid}" style="display:inline-flex;border:1px solid #dadce0;'
        f'border-radius:8px;overflow:hidden;background:#fff;">{items_html}</div></div>'
    )


def _render_zoomable_image(b: dict) -> str:
    """CSS hover-zoom image — scale transform on hover."""
    import html as _h
    url    = b.get("image_url", b.get("url", ""))
    alt    = b.get("alt_text", b.get("alt", ""))
    factor = float(b.get("zoom_factor", 1.5))
    uid    = abs(hash(url)) % 100000
    style  = (
        f'<style>'
        f'.zi{uid}{{overflow:hidden;border-radius:10px;cursor:zoom-in;'
        f'border:1px solid #e5e7eb;}}'
        f'.zi{uid} img{{width:100%;display:block;transition:transform .4s ease;'
        f'transform-origin:center center;}}'
        f'.zi{uid}:hover img{{transform:scale({factor});}}'
        f'</style>'
    )
    caption = '<div style="font-size:0.75rem;color:#9ca3af;text-align:center;margin-top:4px;">Hover to zoom</div>'
    return (
        f'{style}<div style="margin:1rem 0;">'
        f'<div class="zi{uid}"><img src="{_h.escape(url)}" alt="{_h.escape(alt)}"></div>'
        f'{caption}</div>'
    )


def _render_custom_checkbox_group(b: dict) -> str:
    """Custom-styled checkbox group with animated checkmark SVG."""
    label   = b.get("group_label", b.get("label", ""))
    name    = b.get("name", "chk")
    options = b.get("options", b.get("items", []))
    uid     = abs(hash(str(options) + name)) % 100000

    check_svg = (
        '<svg width="11" height="9" viewBox="0 0 11 9" fill="none">'
        '<polyline points="1,4.5 4,8 10,1" stroke="white" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )
    style = (
        f'<style>'
        f'.ccg{uid} input{{display:none;}}'
        f'.ccg{uid} label{{display:flex;align-items:center;gap:10px;cursor:pointer;'
        f'padding:10px 14px;border:1px solid #e5e7eb;border-radius:8px;background:#fff;'
        f'font-size:0.88rem;color:#374151;transition:border-color .15s,background .15s;}}'
        f'.ccg{uid} input:checked+label{{border-color:#1a73e8;background:#f0f4ff;color:#1a73e8;}}'
        f'.ccg{uid} .box{{width:18px;height:18px;border:2px solid #dadce0;border-radius:4px;'
        f'flex-shrink:0;display:flex;align-items:center;justify-content:center;'
        f'transition:border-color .15s,background .15s;}}'
        f'.ccg{uid} input:checked+label .box{{border-color:#1a73e8;background:#1a73e8;}}'
        f'</style>'
    )
    items_html = ""
    for i, opt in enumerate(options):
        val     = opt.get("value", opt.get("label", ""))
        lbl     = opt.get("label", val)
        checked = " checked" if opt.get("is_checked", opt.get("checked", False)) else ""
        cid     = f"ccg{uid}_{i}"
        items_html += (
            f'<div><input type="checkbox" id="{cid}" name="{name}" value="{val}"{checked}>'
            f'<label for="{cid}"><span class="box">{check_svg}</span>{lbl}</label></div>'
        )

    label_html = (
        f'<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:8px;">{label}</div>'
    ) if label else ""
    return (
        f'{style}<div class="ccg{uid}" style="margin:1rem 0;">'
        f'{label_html}'
        f'<div style="display:flex;flex-direction:column;gap:6px;">{items_html}</div>'
        f'</div>'
    )

def _render_css_slide_panel(b: dict) -> str:
    trigger = b.get("trigger_text", "Open panel")
    blocks  = b.get("blocks", [])
    content = render(blocks) if blocks else ""
    return (f'<div style="margin:1rem 0;display:flex;gap:12px;align-items:flex-start;">'
            f'<button style="padding:8px 14px;background:#374151;color:#fff;border:none;border-radius:6px;'
            f'font-size:0.82rem;cursor:pointer;white-space:nowrap;">{trigger} →</button>'
            f'<div style="flex:1;padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#fff;'
            f'border-left:3px solid #374151;font-size:0.85rem;">{content}</div>'
            f'</div>')

def _render_testimonial_card(b: dict) -> str:
    """Customer testimonial with quote, star rating, avatar, author, and title."""
    import html as _h
    text         = b.get("text", b.get("quote", ""))
    author_name  = b.get("author_name", b.get("author", ""))
    author_title = b.get("author_title", b.get("company", b.get("role", "")))
    avatar_url   = b.get("author_avatar_url", b.get("avatar", ""))
    rating       = int(b.get("rating", 0))

    stars_html = (
        '<div style="margin-bottom:12px;">'
        + "".join('<span style="color:#facc15;font-size:1rem;">★</span>' for _ in range(rating))
        + "".join('<span style="color:#d1d5db;font-size:1rem;">★</span>' for _ in range(5 - rating))
        + '</div>'
    ) if rating else ""

    avatar_html = (
        f'<img src="{_h.escape(avatar_url)}" alt="{_h.escape(author_name)}" '
        f'style="width:40px;height:40px;border-radius:50%;object-fit:cover;flex-shrink:0;">'
    ) if avatar_url else (
        f'<div style="width:40px;height:40px;border-radius:50%;background:#e8f0fe;'
        f'display:flex;align-items:center;justify-content:center;font-size:1rem;'
        f'font-weight:700;color:#1a73e8;flex-shrink:0;">'
        f'{_h.escape(author_name[:1])}</div>'
    ) if author_name else ""

    return (
        f'<div style="margin:1rem 0;background:#fff;border:1px solid #e5e7eb;'
        f'border-radius:12px;padding:20px 22px;">'
        f'{stars_html}'
        f'<blockquote style="margin:0 0 16px;font-size:0.93rem;color:#374151;'
        f'line-height:1.65;font-style:italic;">&ldquo;{_h.escape(text)}&rdquo;</blockquote>'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'{avatar_html}'
        f'<div><div style="font-size:0.87rem;font-weight:700;color:#111827;">{_h.escape(author_name)}</div>'
        f'<div style="font-size:0.78rem;color:#6b7280;">{_h.escape(author_title)}</div></div>'
        f'</div></div>'
    )


def _render_star_rating_display(b: dict) -> str:
    """Read-only star rating with numeric score and optional review count."""
    rating       = float(b.get("rating", b.get("value", 0)))
    max_rating   = int(b.get("max_rating", 5))
    review_count = b.get("review_count", b.get("count", None))

    full  = int(rating)
    half  = 1 if (rating - full) >= 0.5 else 0
    empty = max_rating - full - half

    stars = (
        "".join('<span style="color:#facc15;font-size:1.2rem;">★</span>' for _ in range(full))
        + ('<span style="color:#facc15;font-size:1.2rem;opacity:0.55;">★</span>' if half else "")
        + "".join('<span style="color:#d1d5db;font-size:1.2rem;">★</span>' for _ in range(empty))
    )
    count_html = (
        f'<span style="font-size:0.82rem;color:#6b7280;margin-left:6px;">'
        f'({review_count:,} reviews)</span>'
    ) if review_count is not None else ""

    return (
        f'<div style="margin:0.5rem 0;display:flex;align-items:center;gap:4px;">'
        f'{stars}'
        f'<span style="font-size:0.93rem;font-weight:600;color:#374151;margin-left:4px;">{rating}</span>'
        f'{count_html}</div>'
    )

def _render_avatar_group(b: dict) -> str:
    """TODO: Renders a stack or row of small user avatars, often indicating a group or commun"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ avatar_group ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_contributor_list(b: dict) -> str:
    """TODO: Renders a list of individuals who have contributed to a project or community, wi"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ contributor_list ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_customer_logo_grid(b: dict) -> str:
    """TODO: Renders a grid or row of logos from featured customers or partners."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ customer_logo_grid ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_social_proof_banner(b: dict) -> str:
    """TODO: Renders a prominent banner highlighting a key social proof metric or achievement"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ social_proof_banner ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_media_mention_card(b: dict) -> str:
    """TODO: Renders a card showcasing a mention or feature in a media publication."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ media_mention_card ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_expert_endorsement(b: dict) -> str:
    """TODO: Renders an endorsement from an industry expert, including their quote, name, and"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ expert_endorsement ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_review_callout(b: dict) -> str:
    """TODO: Renders a short, impactful quote from a customer review, often accompanied by a """
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ review_callout ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_social_feed_embed(b: dict) -> str:
    """TODO: Renders an embedded snippet of a social media post, such as a tweet or Instagram"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ social_feed_embed ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'


def _render_terminal_block(b: dict) -> str:
    shell   = b.get("shell", "bash")
    command = b.get("command", "").replace("<", "&lt;").replace(">", "&gt;")
    output  = b.get("output",  "").replace("<", "&lt;").replace(">", "&gt;")
    prompt  = {"zsh": "%", "powershell": "PS>", "cmd": ">"}.get(shell, "$")
    out_html = f'<div style="color:#9ca3af;white-space:pre-wrap;margin-top:8px;">{output}</div>' if output else ""
    return (
        f'<div style="background:#1e1e2e;border-radius:10px;overflow:hidden;margin:1.2rem 0;'
        f'font-family:\'JetBrains Mono\',monospace;font-size:0.82rem;">'
        f'<div style="background:#2a2a3e;padding:8px 14px;display:flex;align-items:center;gap:6px;">'
        f'<span style="width:10px;height:10px;border-radius:50%;background:#ff5f56;display:inline-block;"></span>'
        f'<span style="width:10px;height:10px;border-radius:50%;background:#ffbd2e;display:inline-block;"></span>'
        f'<span style="width:10px;height:10px;border-radius:50%;background:#27c93f;display:inline-block;"></span>'
        f'<span style="margin-left:8px;color:#9ca3af;font-size:0.75rem;">{shell}</span>'
        f'</div>'
        f'<div style="padding:14px 18px;">'
        f'<span style="color:#a78bfa;">{prompt}</span> '
        f'<span style="color:#e2e8f0;">{command}</span>'
        f'{out_html}</div></div>'
    )


def _render_file_tree(b: dict) -> str:
    def _node(item, depth=0):
        indent  = "  " * depth
        icon    = "📁 " if item.get("type") == "dir" else "📄 "
        name    = item.get("name", "")
        color   = "#60a5fa" if item.get("type") == "dir" else "#e2e8f0"
        html    = f'<div style="padding:1px 0;color:{color};font-size:0.82rem;">{indent}{icon}{name}</div>'
        for child in item.get("children", []):
            html += _node(child, depth + 1)
        return html
    nodes    = b.get("nodes", [])
    title    = b.get("title", "")
    title_html = f'<div style="font-size:0.78rem;color:#9ca3af;margin-bottom:8px;">{title}</div>' if title else ""
    inner    = "".join(_node(n) for n in nodes)
    return (
        f'<div style="background:#1e1e2e;border-radius:10px;padding:16px 20px;margin:1.2rem 0;'
        f'font-family:\'JetBrains Mono\',monospace;">'
        f'{title_html}{inner}</div>'
    )


def _render_tabbed_code(b: dict) -> str:
    tabs = b.get("tabs", [])
    if not tabs:
        return ""
    uid = abs(hash(str(tabs))) % 100000
    labels = "".join(
        f'<label for="tc-{uid}-{i}" style="padding:6px 14px;cursor:pointer;font-size:0.78rem;'
        f'font-weight:600;border-bottom:2px solid {"#7c3aed" if i==0 else "transparent"};'
        f'color:{"#7c3aed" if i==0 else "#9ca3af"};">{t.get("label", t.get("language","Tab"))}</label>'
        for i, t in enumerate(tabs)
    )
    panels = "".join(
        f'<div style="{"display:block" if i==0 else "display:none"}">'
        f'<pre style="margin:0;padding:16px;background:#1e1e2e;font-size:0.82rem;color:#e2e8f0;overflow:auto;">'
        f'<code>{t.get("code","").replace("<","&lt;").replace(">","&gt;")}</code></pre></div>'
        for i, t in enumerate(tabs)
    )
    return (
        f'<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;">'
        f'<div style="display:flex;background:#f9fafb;border-bottom:1px solid #e5e7eb;gap:0;">{labels}</div>'
        f'{panels}</div>'
    )


def _render_http_request_block(b: dict) -> str:
    method  = b.get("method", "GET").upper()
    url     = b.get("url", "")
    headers = b.get("headers", {})
    body    = b.get("body", "")
    colors  = {"GET":"#2563eb","POST":"#16a34a","PUT":"#d97706","DELETE":"#dc2626","PATCH":"#7c3aed"}
    color   = colors.get(method, "#6b7280")
    hdrs_html = "".join(
        f'<div style="font-size:0.78rem;font-family:monospace;color:#374151;">'
        f'<span style="color:#6b7280;">{k}:</span> {v}</div>'
        for k, v in (headers or {}).items()
    )
    body_html = (
        f'<pre style="background:#f9fafb;border-radius:6px;padding:10px;margin-top:10px;'
        f'font-size:0.78rem;overflow:auto;color:#374151;">{body}</pre>'
    ) if body else ""
    return (
        f'<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;">'
        f'<div style="padding:10px 16px;display:flex;align-items:center;gap:10px;background:#f9fafb;">'
        f'<span style="background:{color};color:#fff;font-weight:700;font-size:0.75rem;'
        f'padding:3px 10px;border-radius:5px;font-family:monospace;">{method}</span>'
        f'<span style="font-family:monospace;font-size:0.85rem;color:#374151;">{url}</span>'
        f'</div>'
        f'{"<div style=padding:10px 16px;>" + hdrs_html + "</div>" if hdrs_html else ""}'
        f'{body_html}</div>'
    )


def _render_env_var_list(b: dict) -> str:
    variables = b.get("variables", [])
    rows = "".join(
        f'<tr>'
        f'<td style="padding:8px 12px;font-family:monospace;font-size:0.82rem;color:#7c3aed;'
        f'white-space:nowrap;border-bottom:1px solid #f3f4f6;">{v.get("key","")}</td>'
        f'<td style="padding:8px 12px;font-size:0.82rem;color:#374151;border-bottom:1px solid #f3f4f6;">{v.get("description","")}</td>'
        f'<td style="padding:8px 12px;font-family:monospace;font-size:0.78rem;color:#6b7280;border-bottom:1px solid #f3f4f6;">{v.get("default","—")}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">'
        f'{"<span style=color:#dc2626;font-size:0.72rem;font-weight:700;>required</span>" if v.get("required") else "<span style=color:#9ca3af;font-size:0.72rem;>optional</span>"}'
        f'</td></tr>'
        for v in variables
    )
    return (
        f'<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:#f9fafb;">'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Variable</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Description</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Default</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Required</th>'
        f'</tr></thead><tbody>{rows}</tbody></table></div>'
    )


def _render_prerequisite_checklist(b: dict) -> str:
    title = b.get("title", "Before you start")
    items = b.get("items", [])
    lis = "".join(
        f'<li style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;font-size:0.88rem;">'
        f'<span style="color:#16a34a;flex-shrink:0;margin-top:1px;">✓</span>'
        f'<span style="color:#374151;">{item}</span></li>'
        for item in items
    )
    return (
        f'<div style="border:1px solid #bbf7d0;border-radius:10px;padding:16px 20px;'
        f'background:#f0fdf4;margin:1.2rem 0;">'
        f'<div style="font-weight:700;color:#15803d;margin-bottom:10px;">{title}</div>'
        f'<ul style="list-style:none;padding:0;margin:0;">{lis}</ul></div>'
    )


def _render_keyboard_shortcut(b: dict) -> str:
    keys   = b.get("keys", [])
    action = b.get("action", "")
    key_html = " + ".join(
        f'<kbd style="display:inline-block;padding:2px 8px;font-family:monospace;font-size:0.8rem;'
        f'border:1px solid #d1d5db;border-bottom:3px solid #9ca3af;border-radius:4px;'
        f'background:#f9fafb;color:#374151;">{k}</kbd>'
        for k in keys
    )
    action_html = f'<span style="margin-left:10px;font-size:0.85rem;color:#6b7280;">{action}</span>' if action else ""
    return f'<div style="margin:0.5rem 0;display:inline-flex;align-items:center;">{key_html}{action_html}</div>'


def _render_api_param_table(b: dict) -> str:
    params = b.get("parameters", [])
    rows = "".join(
        f'<tr>'
        f'<td style="padding:8px 12px;font-family:monospace;font-size:0.82rem;color:#7c3aed;border-bottom:1px solid #f3f4f6;">{p.get("name","")}</td>'
        f'<td style="padding:8px 12px;font-family:monospace;font-size:0.78rem;color:#2563eb;border-bottom:1px solid #f3f4f6;">{p.get("type","")}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">'
        f'{"<span style=color:#dc2626;font-size:0.72rem;font-weight:700;>required</span>" if p.get("required") else "<span style=color:#9ca3af;font-size:0.72rem;>optional</span>"}'
        f'</td>'
        f'<td style="padding:8px 12px;font-family:monospace;font-size:0.78rem;color:#6b7280;border-bottom:1px solid #f3f4f6;">{p.get("default","—")}</td>'
        f'<td style="padding:8px 12px;font-size:0.82rem;color:#374151;border-bottom:1px solid #f3f4f6;">{p.get("description","")}</td>'
        f'</tr>'
        for p in params
    )
    return (
        f'<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;min-width:600px;">'
        f'<thead><tr style="background:#f9fafb;">'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Parameter</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Type</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Required</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Default</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Description</th>'
        f'</tr></thead><tbody>{rows}</tbody></table></div>'
    )


def _render_reading_progress_bar(b):
    color = b.get("color", "#7c3aed")
    pct   = b.get("percentage", 45)
    return (f'<div style="margin:1rem 0;">'
            f'<div style="font-size:0.75rem;color:#6b7280;margin-bottom:4px;">Reading progress</div>'
            f'<div style="height:3px;background:#e5e7eb;border-radius:2px;">'
            f'<div style="height:100%;width:{pct}%;background:{color};border-radius:2px;"></div>'
            f'</div>'
            f'<div style="font-size:0.7rem;color:#9ca3af;margin-top:2px;">{pct}% complete — fixed to top of page while scrolling</div>'
            f'</div>')

def _render_table_of_contents(b):
    items = b.get("items", b.get("headings", []))
    rows = ""
    for item in items:
        text  = item.get("text", item.get("title", ""))
        level = item.get("level", 1)
        indent = "padding-left:1.2rem;" if level > 1 else ""
        rows += (f'<li style="margin:4px 0;{indent}">'
                 f'<a href="#" style="color:#7c3aed;text-decoration:none;font-size:{0.9 if level==1 else 0.85}rem;">'
                 f'{"└ " if level > 1 else ""}{text}</a></li>')
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;'
            f'background:#f9fafb;margin:1.5rem 0;">'
            f'<div style="font-weight:700;color:#374151;margin-bottom:10px;font-size:0.85rem;">Contents</div>'
            f'<ul style="list-style:none;padding:0;margin:0;">{rows}</ul></div>')

def _render_article_hero(b):
    title    = b.get("title", "")
    subtitle = b.get("subtitle", b.get("overline", ""))
    img_url  = b.get("image", b.get("image_url", ""))
    img_html = (f'<img src="{_img_src(img_url)}" alt="{title}" '
                f'style="width:100%;height:220px;object-fit:cover;border-radius:12px;margin-bottom:16px;display:block;">'
                if img_url else "")
    sub_html = (f'<p style="margin:0 0 4px;font-size:0.78rem;font-weight:600;color:#7c3aed;'
                f'text-transform:uppercase;letter-spacing:0.05em;">{subtitle}</p>'
                if subtitle else "")
    return (f'<div style="margin:1.5rem 0;">{img_html}{sub_html}'
            f'<h1 style="margin:0;font-size:2rem;font-weight:800;color:#111827;line-height:1.2;">{title}</h1>'
            f'</div>')

def _render_scroll_to_top(b):
    return (f'<div style="margin:1rem 0;display:flex;align-items:center;gap:10px;">'
            f'<button style="width:40px;height:40px;border-radius:50%;background:#7c3aed;color:#fff;'
            f'border:none;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;">'
            f'↑</button>'
            f'<span style="font-size:0.8rem;color:#6b7280;">Scroll-to-top button — appears fixed bottom-right after scrolling 300px</span>'
            f'</div>')

def _render_article_series_nav(b):
    title = b.get("title", "This series")
    prev  = b.get("prev", "")
    nxt   = b.get("next", "")
    url   = b.get("url", "#")
    nav = ""
    if prev:
        nav += f'<a href="#" style="color:#7c3aed;text-decoration:none;font-size:0.82rem;">← {prev}</a>'
    if prev and nxt:
        nav += '<span style="margin:0 8px;color:#d1d5db;">|</span>'
    if nxt:
        nav += f'<a href="#" style="color:#7c3aed;text-decoration:none;font-size:0.82rem;">{nxt} →</a>'
    return (f'<div style="border:1px solid #ede9fe;border-radius:10px;padding:14px 18px;'
            f'background:#faf5ff;margin:1.5rem 0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">'
            f'<div style="font-weight:600;color:#7c3aed;font-size:0.85rem;">📚 <a href="{url}" style="color:#7c3aed;text-decoration:none;">{title}</a></div>'
            f'<div>{nav}</div>'
            f'</div>')

def _render_post_metadata_bar(b):
    author = b.get("author", "Anonymous")
    date = b.get("date", "")
    read_time = b.get("readTime", 0)
    
    parts = []
    if author:
        parts.append(f'<span style="font-weight: 600; color: #374151;">✍️ {author}</span>')
    if date:
        parts.append(f'<span style="color: #6b7280;">📅 {date}</span>')
    if read_time:
        parts.append(f'<span style="color: #6b7280;">⏱️ {read_time} min read</span>')
        
    inner = ' <span style="color: #e5e7eb; margin: 0 8px;">|</span> '.join(parts)
    return (f'<div class="post-metadata-bar" style="display: flex; align-items: center; gap: 8px; font-size: 0.82rem; '
            f'padding: 8px 12px; background: #f9fafb; border: 1px solid #f3f4f6; border-radius: 6px; margin: 1rem 0;">'
            f'{inner}'
            f'</div>')

def _render_notification_badge(b):
    text = b.get("text", "")
    color = b.get("color", "#ef4444")
    return (f'<div style="position:relative;display:inline-block;padding:8px;background:#f3f4f6;border-radius:8px;">'
            f'  <svg style="width:24px;height:24px;color:#4b5563;" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
            f'    <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>'
            f'  </svg>'
            f'  <span style="position:absolute;top:0;right:0;transform:translate(25%, -25%);background:{color};color:#fff;'
            f'               font-size:0.7rem;font-weight:700;border-radius:9999px;padding:2px 6px;line-height:1;min-width:16px;'
            f'               text-align:center;box-shadow:0 0 0 2px #fff;">{text}</span>'
            f'</div>')

def _render_expandable_list(b):
    items = b.get("items", [])
    def render_node(node):
        text = node.get("text", "")
        children = node.get("children", [])
        if children:
            child_html = "".join(f'<div style="margin-left: 16px;">{render_node(c)}</div>' for c in children)
            return (f'<details style="margin: 4px 0; font-size: 0.9rem;">'
                    f'  <summary style="cursor: pointer; font-weight: 500; color: #1f2937; outline: none; list-style-type: none;">'
                    f'    <span style="display: inline-block; margin-right: 4px;">▶</span> {text}'
                    f'  </summary>'
                    f'  <div style="padding-left: 12px; border-left: 1px dashed #d1d5db; margin-top: 2px;">{child_html}</div>'
                    f'</details>')
        else:
            return (f'<div style="margin: 4px 0; color: #4b5563; font-size: 0.9rem; padding-left: 14px;">'
                    f'  • {text}'
                    f'</div>')
    list_items = "".join(render_node(item) for item in items)
    return (f'<div class="expandable-list" style="padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; margin: 1rem 0;">'
            f'  {list_items}'
            f'</div>')

def _render_poll_block(b):
    question = b.get("question", "Question")
    options = b.get("options", [])
    total_votes = sum(o.get("votes", 0) for o in options) or 1
    opts_html = ""
    for opt in options:
        text = opt.get("text", "")
        votes = opt.get("votes", 0)
        pct = (votes / total_votes) * 100
        opts_html += (
            f'<div style="margin-bottom: 12px; position: relative;">'
            f'  <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 500; color: #374151; margin-bottom: 4px; z-index: 10; position: relative;">'
            f'    <span>{text}</span>'
            f'    <span>{votes} votes ({pct:.1f}%)</span>'
            f'  </div>'
            f'  <div style="height: 24px; background: #f3f4f6; border-radius: 6px; overflow: hidden; position: relative; border: 1px solid #e5e7eb;">'
            f'    <div style="width: {pct:.1f}%; height: 100%; background: #7c3aed; opacity: 0.15; position: absolute; left: 0; top: 0; border-radius: 5px;"></div>'
            f'  </div>'
            f'</div>'
        )
    return (f'<div class="poll-block" style="padding: 16px; border: 1px solid #ede9fe; border-radius: 12px; background: #fff; '
            f'box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin: 1.2rem 0;">'
            f'  <h4 style="margin: 0 0 16px; font-size: 1rem; font-weight: 700; color: #111827;">📊 {question}</h4>'
            f'  {opts_html}'
            f'</div>')

def _render_abbr_tooltip(b):
    text = b.get("text", "")
    title = b.get("title", "")
    return (f'<abbr title="{title}" style="text-decoration: underline dotted #7c3aed; text-underline-offset: 4px; '
            f'cursor: help; font-weight: 600; color: #4338ca;">{text}</abbr>')

def _render_copy_to_clipboard(b):
    text = b.get("text", "")
    val = b.get("value", "")
    return (f'<span class="copy-to-clipboard" style="display: inline-flex; align-items: center; gap: 6px; '
            f'background: #f3f4f6; border: 1px solid #e5e7eb; padding: 4px 10px; border-radius: 6px; font-family: monospace; font-size: 0.85rem; color: #1f2937;">'
            f'  <span>{text}</span>'
            f'  <button onclick="navigator.clipboard.writeText(\'{val}\'); this.textContent=\'✓\'; setTimeout(() => this.textContent=\'📋\', 1000)" '
            f'          style="border: none; background: none; cursor: pointer; font-size: 0.85rem; padding: 0; display: inline-flex; align-items: center; justify-content: center; outline: none; margin-left: 4px;" title="Copy to clipboard">'
            f'    📋'
            f'  </button>'
            f'</span>')

def _render_embed_codepen(b):
    pen_id = b.get("pen_id","")
    user = b.get("user_handle","")
    return (f'<p><iframe height="600" style="width:100%;border:1px solid #e5e7eb;border-radius:8px;'
            f'margin:1.2rem 0;" src="https://codepen.io/{user}/embed/{pen_id}?default-tab=result" '
            f'loading="lazy" allowtransparency="true" allowfullscreen="true"></iframe></p>')

def _render_embed_stackblitz(b):
    project_id = b.get("project_id","")
    return (f'<iframe src="https://stackblitz.com/edit/{project_id}?embed=1" '
            f'style="width:100%;height:500px;border:1px solid #e5e7eb;border-radius:8px;margin:1.2rem 0;" '
            f'loading="lazy"></iframe>')

def _render_embed_gist(b):
    gist_id = b.get("gist_id","")
    return (f'<script src="https://gist.github.com/{gist_id}.js"></script>')

def _render_embed_tweet(b):
    tweet_id = b.get("tweet_id","")
    return (f'<blockquote class="twitter-tweet" style="margin:1.2rem 0;"><a href="https://twitter.com/twitter/status/{tweet_id}"></a></blockquote>'
            f'<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>')

def _render_embed_google_slides(b):
    pres_id = b.get("presentation_id","")
    return (f'<iframe src="https://docs.google.com/presentation/d/{pres_id}/embed" '
            f'frameborder="0" width="100%" height="569" allowfullscreen="true" mozallowfullscreen="true" '
            f'webkitallowfullscreen="true" style="border:1px solid #e5e7eb;border-radius:8px;margin:1.2rem 0;"></iframe>')

def _render_lottie_animation(b):
    url = b.get("src_url","")
    loop = b.get("loop",True)
    return (f'<script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>'
            f'<lottie-player src="{url}" background="transparent" speed="1" style="width:100%;max-height:400px;margin:1.2rem 0;" '
            f'{"loop" if loop else ""} autoplay></lottie-player>')

def _render_figma_embed(b):
    url = b.get("embed_url","")
    return (f'<iframe style="border:1px solid #e5e7eb;border-radius:8px;width:100%;height:500px;margin:1.2rem 0;" '
            f'src="{url}" allowfullscreen></iframe>')


def _render_difficulty_badge(b):
    level = b.get("level", "beginner")
    cfg = {"beginner": ("#16a34a","#f0fdf4","Beginner"), "intermediate": ("#d97706","#fffbeb","Intermediate"), "advanced": ("#dc2626","#fef2f2","Advanced")}
    color, bg, label = cfg.get(level, cfg["beginner"])
    return (f'<span style="display:inline-flex;align-items:center;gap:5px;border:1px solid {color}44;'
            f'border-radius:100px;padding:3px 12px;font-size:0.75rem;font-weight:700;'
            f'color:{color};background:{bg};">{"⚡" if level=="beginner" else "🔧" if level=="intermediate" else "🚀"} {label}</span>')

def _render_caution_block(b):
    msg = b.get("message","")
    return (f'<div style="border:1px solid #fca5a5;border-left:4px solid #ef4444;border-radius:8px;'
            f'padding:14px 18px;background:#fef2f2;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#991b1b;margin-bottom:6px;">⚠ Caution</div>'
            f'<p style="margin:0;font-size:0.88rem;color:#7f1d1d;">{msg}</p></div>')

def _render_checklist_interactive(b):
    items = b.get("items", [])
    lis = "".join(
        f'<li style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid #f3f4f6;">'
        f'<input type="checkbox" style="width:16px;height:16px;accent-color:#7c3aed;cursor:pointer;">'
        f'<span style="font-size:0.88rem;color:#374151;">{item}</span></li>'
        for item in items
    )
    return (f'<ul style="list-style:none;padding:0;margin:1.2rem 0;'
            f'border:1px solid #e5e7eb;border-radius:10px;padding:12px 18px;">{lis}</ul>')

def _render_glossary_inline(b):
    term = b.get("term","")
    defn = b.get("definition","").replace('"','&quot;')
    return (f'<span style="position:relative;display:inline-block;">'
            f'<span style="border-bottom:2px dotted #7c3aed;cursor:help;color:#7c3aed;font-weight:600;" '
            f'title="{defn}">{term}</span></span>')

def _render_time_estimate(b):
    mins = b.get("minutes", 5)
    return (f'<span style="display:inline-flex;align-items:center;gap:5px;'
            f'font-size:0.78rem;color:#6b7280;background:#f3f4f6;'
            f'padding:3px 10px;border-radius:100px;">🕐 {mins} min read</span>')

def _render_progress_checkpoint(b):
    current = b.get("current_step", 1)
    total   = b.get("total_steps", 1)
    pct     = int(current / total * 100) if total else 0
    steps   = "".join(
        f'<div style="width:28px;height:28px;border-radius:50%;display:flex;align-items:center;'
        f'justify-content:center;font-size:0.75rem;font-weight:700;'
        f'background:{"#7c3aed" if i < current else "#e5e7eb"};'
        f'color:{"#fff" if i < current else "#9ca3af"};">{i}</div>'
        for i in range(1, total + 1)
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;margin:1.2rem 0;">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;">{steps}</div>'
            f'<div style="background:#f3f4f6;border-radius:100px;height:6px;overflow:hidden;">'
            f'<div style="height:100%;background:#7c3aed;width:{pct}%;border-radius:100px;"></div>'
            f'</div>'
            f'<div style="font-size:0.78rem;color:#6b7280;margin-top:6px;">Step {current} of {total}</div>'
            f'</div>')

def _render_social_share_bar(b):
    platforms = b.get("platforms", ["twitter","linkedin"])
    url       = b.get("url", "")
    cfg = {
        "twitter":  ("#1da1f2", "X / Twitter", f"https://twitter.com/intent/tweet?url={url}"),
        "linkedin": ("#0a66c2", "LinkedIn",     f"https://www.linkedin.com/sharing/share-offsite/?url={url}"),
        "facebook": ("#1877f2", "Facebook",     f"https://www.facebook.com/sharer/sharer.php?u={url}"),
        "reddit":   ("#ff4500", "Reddit",       f"https://reddit.com/submit?url={url}"),
    }
    btns = "".join(
        f'<a href="{cfg[p][2]}" target="_blank" rel="noopener" '
        f'style="display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:6px;'
        f'background:{cfg[p][0]};color:#fff;font-size:0.8rem;font-weight:600;text-decoration:none;">'
        f'{cfg[p][1]}</a>'
        for p in platforms if p in cfg
    )
    return f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin:1.2rem 0;">{btns}</div>'

def _render_newsletter_cta(b):
    headline    = b.get("headline", "Stay in the loop")
    button_label = b.get("button_label", "Subscribe")
    return (f'<div style="border:1px solid #e5e7eb;border-radius:12px;padding:24px 28px;'
            f'background:linear-gradient(135deg,#f9fafb,#f3f4f6);margin:1.5rem 0;text-align:center;">'
            f'<div style="font-size:1.1rem;font-weight:700;color:#111827;margin-bottom:8px;">{headline}</div>'
            f'<div style="display:flex;gap:8px;max-width:400px;margin:12px auto 0;">'
            f'<input type="email" placeholder="you@example.com" '
            f'style="flex:1;padding:8px 14px;border:1px solid #d1d5db;border-radius:6px;font-size:0.88rem;">'
            f'<button style="padding:8px 18px;background:#7c3aed;color:#fff;border:none;'
            f'border-radius:6px;font-weight:600;font-size:0.88rem;cursor:pointer;">{button_label}</button>'
            f'</div></div>')

def _render_author_bio_card(b):
    name   = b.get("name","")
    avatar = b.get("image", b.get("avatar_url", b.get("avatar","")))
    bio    = b.get("bio","")
    links  = b.get("links",{}) or {}
    avatar_html = (f'<img src="{_img_src(avatar)}" alt="{name}" '
                   f'style="width:56px;height:56px;border-radius:50%;object-fit:cover;flex-shrink:0;">'
                   if avatar else
                   f'<div style="width:56px;height:56px;border-radius:50%;background:#e5e7eb;'
                   f'display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0;">👤</div>')
    links_html = "".join(
        f'<a href="{v}" target="_blank" rel="noopener" '
        f'style="font-size:0.78rem;color:#6b7280;text-decoration:none;margin-right:10px;">{k}</a>'
        for k, v in links.items()
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:12px;padding:18px 22px;'
            f'display:flex;gap:16px;align-items:flex-start;margin:1.5rem 0;">'
            f'{avatar_html}'
            f'<div><div style="font-weight:700;color:#111827;margin-bottom:4px;">{name}</div>'
            f'<p style="margin:0 0 8px;font-size:0.85rem;color:#6b7280;line-height:1.5;">{bio}</p>'
            f'{"<div>" + links_html + "</div>" if links_html else ""}'
            f'</div></div>')

def _render_related_posts_grid(b):
    posts = b.get("posts",[])
    cards = "".join(
        f'<a href="{p.get("url","#")}" style="display:block;border:1px solid #e5e7eb;border-radius:8px;'
        f'padding:14px 16px;text-decoration:none;transition:box-shadow 0.15s;" '
        f'onmouseover="this.style.boxShadow=\'0 2px 8px rgba(0,0,0,0.08)\'" '
        f'onmouseout="this.style.boxShadow=\'none\'">'
        f'{"<div style=font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#7c3aed;margin-bottom:4px;>" + p.get("topic","") + "</div>" if p.get("topic") else ""}'
        f'<div style="font-size:0.88rem;font-weight:600;color:#111827;line-height:1.4;">{p.get("title","")}</div>'
        f'</a>'
        for p in posts
    )
    return (f'<div style="margin:1.5rem 0;">'
            f'<div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.08em;color:#6b7280;margin-bottom:10px;">Related reading</div>'
            f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;">'
            f'{cards}</div></div>')

def _render_series_overview_card(b):
    name  = b.get("series_name","")
    parts = b.get("parts",[])
    items = "".join(
        f'<a href="{p.get("url","#")}" style="display:flex;align-items:center;gap:10px;padding:8px 0;'
        f'border-bottom:1px solid #f3f4f6;text-decoration:none;">'
        f'<span style="width:22px;height:22px;border-radius:50%;display:flex;align-items:center;'
        f'justify-content:center;font-size:0.7rem;font-weight:700;flex-shrink:0;'
        f'background:{"#7c3aed" if p.get("current") else "#f3f4f6"};'
        f'color:{"#fff" if p.get("current") else "#6b7280"};">{i+1}</span>'
        f'<span style="font-size:0.85rem;{"font-weight:700;color:#7c3aed;" if p.get("current") else "color:#374151;"}">'
        f'{p.get("title","")}</span></a>'
        for i, p in enumerate(parts)
    )
    return (f'<div style="border:1px solid #ede9fe;border-radius:10px;padding:16px 20px;'
            f'background:#faf5ff;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#7c3aed;margin-bottom:10px;">📖 {name}</div>'
            f'{items}</div>')

def _render_reaction_group(b):
    emojis_cfg = {"thumbs_up":("👍","0"),"heart":("❤️","0"),"rocket":("🚀","0"),"mind_blown":("🤯","0")}
    enabled = b.get("enabled_emojis", list(emojis_cfg.keys()))
    btns = "".join(
        f'<button onclick="this.querySelector(\'span\').textContent=String(parseInt(this.querySelector(\'span\').textContent)+1)" '
        f'style="display:inline-flex;align-items:center;gap:4px;padding:6px 12px;border:1px solid #e5e7eb;'
        f'border-radius:100px;background:#f9fafb;cursor:pointer;font-size:0.88rem;">'
        f'{emojis_cfg[e][0]} <span style="font-size:0.78rem;color:#6b7280;">{emojis_cfg[e][1]}</span></button>'
        for e in enabled if e in emojis_cfg
    )
    return f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin:1rem 0;">{btns}</div>'

def _render_share_quote(b):
    text   = b.get("text","")
    author = b.get("author","")
    tweet_text = f"{text[:200]} — {author}" if author else text[:200]
    return (f'<div style="border-left:4px solid #7c3aed;padding:16px 20px;background:#faf5ff;'
            f'border-radius:0 10px 10px 0;margin:1.5rem 0;position:relative;">'
            f'<p style="font-size:1rem;font-style:italic;color:#1e1b4b;line-height:1.6;margin:0 0 10px;">"{text}"</p>'
            f'{"<div style=font-size:0.8rem;color:#7c3aed;font-weight:600;>— " + author + "</div>" if author else ""}'
            f'<a href="https://twitter.com/intent/tweet?text={tweet_text.replace(" ","+")}" target="_blank" rel="noopener" '
            f'style="display:inline-flex;align-items:center;gap:5px;font-size:0.75rem;color:#6b7280;'
            f'text-decoration:none;margin-top:8px;">Share this →</a></div>')

def _render_follow_cta(b):
    msg   = b.get("message","Follow for more")
    links = b.get("platform_links",{}) or {}
    btns  = "".join(
        f'<a href="{v}" target="_blank" rel="noopener" '
        f'style="padding:8px 18px;border:1px solid #d1d5db;border-radius:6px;font-size:0.85rem;'
        f'font-weight:600;color:#374151;text-decoration:none;">{k}</a>'
        for k, v in links.items()
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px 24px;'
            f'display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;'
            f'gap:12px;margin:1.5rem 0;background:#f9fafb;">'
            f'<span style="font-size:0.95rem;font-weight:600;color:#111827;">{msg}</span>'
            f'<div style="display:flex;gap:8px;flex-wrap:wrap;">{btns}</div></div>')

def _render_follow_button(b):
    handle   = b.get("target_handle","")
    platform = b.get("platform","twitter")
    urls = {"twitter": f"https://twitter.com/{handle}", "github": f"https://github.com/{handle}", "linkedin": f"https://linkedin.com/in/{handle}"}
    url = urls.get(platform, "#")
    return (f'<a href="{url}" target="_blank" rel="noopener" '
            f'style="display:inline-flex;align-items:center;gap:6px;padding:8px 18px;'
            f'border:1px solid #d1d5db;border-radius:6px;font-size:0.85rem;font-weight:600;'
            f'color:#374151;text-decoration:none;background:#f9fafb;">Follow @{handle}</a>')


def _render_version_badge(b):
    v = b.get("version","")
    status = b.get("status","stable")
    colors = {"stable":"#16a34a","beta":"#2563eb","alpha":"#d97706","rc":"#7c3aed"}
    c = colors.get(status,"#6b7280")
    return (f'<span style="display:inline-flex;align-items:center;gap:5px;border:1px solid {c};'
            f'border-radius:100px;padding:2px 10px;font-size:0.75rem;font-weight:700;color:{c};'
            f'font-family:monospace;">v{v}'
            f'{"<span style=opacity:0.7;font-weight:400;margin-left:2px;> · " + status + "</span>" if status != "stable" else ""}'
            f'</span>')

def _render_deprecation_notice(b):
    alt = b.get("alternative","")
    rv  = b.get("removal_version","")
    rv_html = f'<div style="margin-top:6px;font-size:0.8rem;color:#991b1b;">Removed in: <code>{rv}</code></div>' if rv else ""
    alt_html = f'<div style="margin-top:4px;font-size:0.85rem;">Use instead: <code style="background:#fef2f2;padding:1px 6px;border-radius:4px;">{alt}</code></div>' if alt else ""
    return (f'<div style="border:1px solid #fca5a5;border-left:4px solid #ef4444;border-radius:8px;'
            f'padding:14px 18px;background:#fef2f2;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#991b1b;margin-bottom:4px;">⚠ Deprecated</div>'
            f'{alt_html}{rv_html}</div>')

def _render_experimental_banner(b):
    msg = b.get("message","")
    return (f'<div style="border:1px solid #fbbf24;border-left:4px solid #f59e0b;border-radius:8px;'
            f'padding:14px 18px;background:#fffbeb;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#92400e;margin-bottom:4px;">🧪 Experimental</div>'
            f'{"<p style=font-size:0.85rem;color:#78350f;margin:0;>" + msg + "</p>" if msg else ""}</div>')

def _render_cli_command(b):
    cmd = b.get("command","").replace("<","&lt;").replace(">","&gt;")
    return (f'<div style="display:flex;align-items:center;background:#1e1e2e;border-radius:8px;'
            f'padding:10px 16px;margin:0.8rem 0;font-family:\'JetBrains Mono\',monospace;font-size:0.85rem;">'
            f'<span style="color:#a78bfa;margin-right:10px;user-select:none;">$</span>'
            f'<code style="color:#e2e8f0;flex:1;">{cmd}</code></div>')

def _render_copy_code_button(b):
    text = b.get("text_to_copy","").replace('"','&quot;').replace("<","&lt;").replace(">","&gt;")
    return (f'<div style="display:inline-block;margin:0.5rem 0;">'
            f'<button onclick="navigator.clipboard.writeText(\'{text}\')" '
            f'style="display:inline-flex;align-items:center;gap:6px;padding:6px 14px;'
            f'border:1px solid #d1d5db;border-radius:6px;background:#f9fafb;cursor:pointer;'
            f'font-size:0.82rem;color:#374151;">'
            f'<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">'
            f'<path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25Z"/>'
            f'<path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z"/>'
            f'</svg>Copy</button></div>')

def _render_log_output(b):
    logs = b.get("logs","").replace("<","&lt;").replace(">","&gt;")
    return (f'<div style="background:#0d1117;border-radius:8px;padding:14px 18px;margin:1.2rem 0;'
            f'max-height:300px;overflow-y:auto;">'
            f'<pre style="margin:0;font-family:\'JetBrains Mono\',monospace;font-size:0.78rem;'
            f'color:#9ca3af;white-space:pre-wrap;word-break:break-all;">{logs}</pre></div>')

def _render_json_tree_viewer(b):
    import json as _json2
    raw = b.get("data","")
    try:
        pretty = _json2.dumps(_json2.loads(raw), indent=2)
    except Exception:
        pretty = raw
    pretty = pretty.replace("<","&lt;").replace(">","&gt;")
    return (f'<div style="background:#1e1e2e;border-radius:10px;padding:16px;margin:1.2rem 0;'
            f'max-height:400px;overflow:auto;">'
            f'<pre style="margin:0;font-family:\'JetBrains Mono\',monospace;font-size:0.8rem;'
            f'color:#e2e8f0;">{pretty}</pre></div>')

def _render_key_takeaways(b):
    raw = b.get("items", b.get("points", []))
    points = [p.get("text", p) if isinstance(p, dict) else p for p in raw]
    lis = "".join(f'<li style="margin-bottom:6px;font-size:0.88rem;color:#1e3a5f;">{p}</li>' for p in points)
    return (f'<div style="border:1px solid #bfdbfe;border-left:4px solid #2563eb;border-radius:8px;'
            f'padding:16px 20px;background:#eff6ff;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#1d4ed8;margin-bottom:10px;">🔑 Key takeaways</div>'
            f'<ul style="margin:0;padding-left:1.2em;">{lis}</ul></div>')

def _render_summary_box(b):
    text = b.get("text","")
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:18px 22px;'
            f'background:#f9fafb;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#374151;margin-bottom:8px;font-size:0.82rem;'
            f'text-transform:uppercase;letter-spacing:0.08em;">Summary</div>'
            f'<p style="margin:0;color:#4b5563;font-size:0.9rem;line-height:1.6;">{text}</p></div>')

def _render_learning_objectives(b):
    objs = b.get("objectives",[])
    lis = "".join(
        f'<li style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;font-size:0.88rem;">'
        f'<span style="color:#2563eb;flex-shrink:0;margin-top:1px;">→</span>'
        f'<span style="color:#1e3a5f;">{o}</span></li>'
        for o in objs
    )
    return (f'<div style="border:1px solid #bfdbfe;border-radius:10px;padding:16px 20px;'
            f'background:#eff6ff;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#1d4ed8;margin-bottom:10px;">🎯 What you\'ll learn</div>'
            f'<ul style="list-style:none;padding:0;margin:0;">{lis}</ul></div>')

def _render_changelog_entry(b):
    version = b.get("version","")
    date    = b.get("date","")
    changes = b.get("changes",[])
    tag_colors = {"added":"#16a34a","fixed":"#2563eb","changed":"#d97706","removed":"#dc2626","deprecated":"#7c3aed"}
    items_html = "".join(
        f'<div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:4px;">'
        f'<span style="font-size:0.7rem;font-weight:700;padding:2px 6px;border-radius:4px;flex-shrink:0;'
        f'background:{tag_colors.get(str(c.get("type","changed")).lower(),"#6b7280")}22;'
        f'color:{tag_colors.get(str(c.get("type","changed")).lower(),"#6b7280")};">{c.get("type","changed").upper()}</span>'
        f'<span style="font-size:0.85rem;color:#374151;">{c.get("text","")}</span></div>'
        for c in changes
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;margin:1.2rem 0;">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
            f'<span style="font-family:monospace;font-weight:700;font-size:0.95rem;color:#374151;">v{version}</span>'
            f'{"<span style=font-size:0.8rem;color:#9ca3af;>" + date + "</span>" if date else ""}'
            f'</div>{items_html}</div>')

def _render_release_notes(b):
    title   = b.get("title","Release Notes")
    added   = b.get("added",[])
    fixed   = b.get("fixed",[])
    changed = b.get("changed",[])
    def section(label, items, color):
        if not items: return ""
        lis = "".join(f'<li style="font-size:0.85rem;color:#374151;margin-bottom:3px;">{i}</li>' for i in items)
        return (f'<div style="margin-bottom:14px;">'
                f'<div style="font-weight:700;font-size:0.78rem;text-transform:uppercase;'
                f'letter-spacing:0.08em;color:{color};margin-bottom:6px;">{label}</div>'
                f'<ul style="margin:0;padding-left:1.2em;">{lis}</ul></div>')
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:18px 22px;margin:1.2rem 0;">'
            f'<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:14px;">{title}</div>'
            f'{section("Added", added, "#16a34a")}'
            f'{section("Fixed", fixed, "#2563eb")}'
            f'{section("Changed", changed, "#d97706")}'
            f'</div>')

def _render_further_reading(b):
    links = b.get("links",[])
    items = "".join(
        f'<a href="{l.get("url","#")}" target="_blank" rel="noopener" '
        f'style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;'
        f'border-bottom:1px solid #f3f4f6;text-decoration:none;">'
        f'<span style="color:#2563eb;flex-shrink:0;margin-top:2px;">→</span>'
        f'<div><div style="font-size:0.88rem;font-weight:600;color:#1d4ed8;">{l.get("title","")}</div>'
        f'{"<div style=font-size:0.78rem;color:#6b7280;margin-top:2px;>" + l.get("annotation","") + "</div>" if l.get("annotation") else ""}'
        f'</div></a>'
        for l in links
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#374151;margin-bottom:4px;">📚 Further reading</div>'
            f'{items}</div>')

def _render_resources_list(b):
    items = b.get("items",[])
    rows = "".join(
        f'<a href="{i.get("url","#")}" target="_blank" rel="noopener" '
        f'style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;'
        f'border-bottom:1px solid #f3f4f6;text-decoration:none;">'
        f'<span style="font-size:0.88rem;color:#1d4ed8;font-weight:500;">{i.get("title","")}</span>'
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'{"<span style=font-size:0.75rem;color:#9ca3af;>" + i.get("size","") + "</span>" if i.get("size") else ""}'
        f'{"<span style=font-size:0.72rem;background:#f3f4f6;padding:2px 6px;border-radius:4px;color:#6b7280;>" + i.get("type","").upper() + "</span>" if i.get("type") else ""}'
        f'</div></a>'
        for i in items
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#374151;margin-bottom:4px;">📎 Resources</div>'
            f'{rows}</div>')

def _render_sidebar_note(b):
    title   = b.get("title","Note")
    content = b.get("content","")
    return (f'<div style="border-left:3px solid #7c3aed;border-radius:0 8px 8px 0;padding:12px 16px;'
            f'background:#faf5ff;margin:1.2rem 0;">'
            f'<div style="font-weight:700;font-size:0.8rem;color:#7c3aed;margin-bottom:4px;">{title}</div>'
            f'<p style="margin:0;font-size:0.85rem;color:#4b5563;">{content}</p></div>')


def _render_color_swatch_grid(b: dict) -> str:
    colors = b.get("colors", [])
    items = "".join(
        f'<div style="display:flex;flex-direction:column;gap:4px;">'
        f'<div style="width:100%;height:40px;background:{c.get("hex","#e5e7eb")};border-radius:4px;"></div>'
        f'<div style="font-size:0.65rem;color:#6b7280;text-align:center;">{c.get("name","")}</div>'
        f'<div style="font-size:0.6rem;color:#9ca3af;text-align:center;font-family:monospace;">{c.get("hex","")}</div>'
        f'</div>'
        for c in colors
    )
    cols = min(len(colors), 6) if colors else 4
    return f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:8px;margin:1rem 0;">{items}</div>'

def _render_live_demo_embed(b: dict) -> str:
    import html as _h
    url    = b.get("url", "#")
    height = b.get("height", "80vh")
    label  = b.get("label", "Open in new tab →")
    title  = b.get("title", "Live demo")
    safe_url = _h.escape(url)
    safe_label = _h.escape(label)
    safe_title = _h.escape(title)
    return (
        f'<div style="margin:1.5rem 0;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.06);">'
        f'<div style="padding:8px 14px;background:#f8fafc;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between;">'
        f'<span style="font-size:12px;color:#64748b;font-family:monospace;">{safe_url}</span>'
        f'<a href="{safe_url}" target="_blank" rel="noopener" style="font-size:12px;color:#6366f1;text-decoration:none;white-space:nowrap;">{safe_label}</a>'
        f'</div>'
        f'<iframe src="{safe_url}" title="{safe_title}" style="width:100%;height:{_h.escape(str(height))};border:none;display:block;" loading="lazy" sandbox="allow-scripts allow-same-origin allow-popups allow-forms"></iframe>'
        f'</div>'
    )

def _render_benchmark_comparison(b: dict) -> str:
    return '<div style="margin:1rem 0;padding:12px;border:1px solid #e5e7eb;border-radius:8px;"><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;"><div style="padding:8px;background:#f0f9ff;border-radius:4px;">Benchmark A: 95ms</div><div style="padding:8px;background:#f0fdf4;border-radius:4px;">Benchmark B: 120ms</div></div></div>'

def _render_chartjs_bar(b: dict) -> str:
    datasets = b.get("datasets", [])
    labels   = b.get("labels", [])
    if not datasets:
        return ""
    
    # Flatten datasets to find global max
    all_vals = []
    for ds in datasets:
        all_vals.extend(ds.get("data", []))
    if not all_vals:
        return ""
        
    mx = max(all_vals) or 1
    mn = min(all_vals)
    
    # SVG canvas coordinate dimensions
    w, h = 500, 200
    pad_l, pad_r, pad_t, pad_b = 60, 20, 30, 40
    chart_w = w - pad_l - pad_r
    chart_h = h - pad_t - pad_b
    
    chart_id = f"bar_{id(b)}"
    
    # Y-axis ticks and horizontal grid lines
    grid_lines = ""
    for grid_idx in range(5):
        grid_y = pad_t + (grid_idx / 4) * chart_h
        grid_v = mx - (grid_idx / 4) * (mx - mn if mx != mn else mx)
        val_str = f"{grid_v:,.1f}" if grid_v % 1 != 0 else f"{grid_v:,.0f}"
        grid_lines += f"""
        <line x1="{pad_l}" y1="{grid_y}" x2="{pad_l + chart_w}" y2="{grid_y}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
        <text x="{pad_l - 10}" y="{grid_y + 3}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="end">{val_str}</text>
        """
        
    # Draw bars and X axis labels
    num_labels = len(labels)
    num_series = len(datasets)
    
    colors = [
        {"fill": "#3b82f6", "stop": "#2563eb"}, # blue
        {"fill": "#10b981", "stop": "#059669"}, # emerald green
        {"fill": "#a855f7", "stop": "#7c3aed"}, # purple
        {"fill": "#f59e0b", "stop": "#d97706"}, # amber
    ]
    
    defs = []
    for di in range(num_series):
        color_set = colors[di % len(colors)]
        grad_id = f"bar_grad_{chart_id}_{di}"
        glow_id = f"bar_glow_{chart_id}_{di}"
        defs.append(f"""
        <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{color_set['fill']}" />
          <stop offset="100%" stop-color="{color_set['stop']}" stop-opacity="0.3" />
        </linearGradient>
        <filter id="{glow_id}" x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        """)
        
    bars_html = []
    x_labels = ""
    
    # Calculate group widths
    group_width_ratio = 0.7  # 70% of available slot
    slot_width = chart_w / (num_labels if num_labels > 0 else 1)
    bar_group_w = slot_width * group_width_ratio
    single_bar_w = bar_group_w / (num_series if num_series > 0 else 1)
    
    for i, lbl in enumerate(labels):
        group_x_start = pad_l + i * slot_width + (slot_width - bar_group_w) / 2
        
        # Add label text
        x_labels += f'<text x="{pad_l + i * slot_width + slot_width/2}" y="{pad_t + chart_h + 20}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="middle">{lbl}</text>'
        
        for di, ds in enumerate(datasets):
            data = ds.get("data", [])
            if i < len(data):
                val = data[i]
                bar_h = (val / mx) * chart_h if mx > 0 else 0
                bar_x = group_x_start + di * single_bar_w
                bar_y = pad_t + chart_h - bar_h
                
                grad_id = f"bar_grad_{chart_id}_{di}"
                glow_id = f"bar_glow_{chart_id}_{di}"
                
                # Draw rounded top bars using path or rect with rx
                bars_html.append(f"""
                <rect x="{bar_x}" y="{bar_y}" width="{max(2, single_bar_w - 2)}" height="{max(1, bar_h)}" fill="url(#{grad_id})" rx="3" ry="3" filter="url(#{glow_id})" />
                """)
                
    svg_defs = "\n".join(defs)
    bars_markup = "\n".join(bars_html)
    
    label = datasets[0].get("label", "") if datasets else ""
    label_html = f'<div style="font-size:0.75rem;font-weight:700;color:#94a3b8;margin-bottom:8px;font-family:monospace;letter-spacing:0.05em;text-transform:uppercase;">{label}</div>' if label else ""
    
    return f"""
    <div style="margin:1.5rem 0;padding:20px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {label_html}
      <div style="width:100%;height:200px;">
        <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
          <defs>
            {svg_defs}
          </defs>
          <!-- Grid & Y-Axes -->
          {grid_lines}
          <!-- X-Axes -->
          {x_labels}
          <!-- Bars -->
          {bars_markup}
        </svg>
      </div>
    </div>
    """

def _render_chartjs_line(b: dict) -> str:
    datasets = b.get("datasets", [])
    labels   = b.get("labels", [])
    if not datasets:
        return ""
    
    # Flatten data to get global min/max for scale matching across datasets
    all_vals = []
    for ds in datasets:
        all_vals.extend(ds.get("data", []))
    if not all_vals:
        return ""
        
    mn, mx = min(all_vals), max(all_vals)
    rng = (mx - mn) or 1
    
    # SVG canvas dimensions: 500x200
    w, h = 500, 200
    pad_l, pad_r, pad_t, pad_b = 60, 20, 30, 40
    chart_w = w - pad_l - pad_r
    chart_h = h - pad_t - pad_b
    
    chart_id = f"line_{id(b)}"
    
    # Draw horizontal grid lines (e.g., 4 intervals)
    grid_lines = ""
    for grid_idx in range(5):
        grid_y = pad_t + (grid_idx / 4) * chart_h
        grid_v = mx - (grid_idx / 4) * rng
        val_str = f"{grid_v:,.1f}" if grid_v % 1 != 0 else f"{grid_v:,.0f}"
        grid_lines += f"""
        <line x1="{pad_l}" y1="{grid_y}" x2="{pad_l + chart_w}" y2="{grid_y}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
        <text x="{pad_l - 10}" y="{grid_y + 3}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="end">{val_str}</text>
        """
        
    # Draw x-axis labels
    x_labels = ""
    n_labels = len(labels)
    if n_labels > 1:
        for i, lbl in enumerate(labels):
            # Only render some labels if there are too many (e.g., max 8 labels)
            if n_labels > 8 and i % (n_labels // 4) != 0 and i != n_labels - 1:
                continue
            x = pad_l + (i / (n_labels - 1)) * chart_w
            x_labels += f'<text x="{x}" y="{pad_t + chart_h + 20}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="middle">{lbl}</text>'
            
    # Draw paths for datasets
    colors = [
        {"stroke": "#3b82f6", "stop": "#3b82f6"}, # blue
        {"stroke": "#10b981", "stop": "#10b981"}, # emerald green
        {"stroke": "#a855f7", "stop": "#a855f7"}, # purple
        {"stroke": "#f59e0b", "stop": "#f59e0b"}, # amber
        {"stroke": "#ec4899", "stop": "#ec4899"}, # pink
    ]
    
    defs = []
    series_elements = []
    
    for di, ds in enumerate(datasets):
        vals = ds.get("data", [])
        if not vals:
            continue
        n = len(vals)
        coords = []
        for i, v in enumerate(vals):
            x = pad_l + (i / (n - 1) if n > 1 else 0.5) * chart_w
            y = pad_t + (1 - (v - mn) / rng) * chart_h
            coords.append((x, y))
            
        color_set = colors[di % len(colors)]
        stroke_color = color_set["stroke"]
        stop_color = color_set["stop"]
        
        grad_id = f"grad_{chart_id}_{di}"
        glow_id = f"glow_{chart_id}_{di}"
        
        defs.append(f"""
        <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{stop_color}" stop-opacity="0.22" />
          <stop offset="100%" stop-color="{stop_color}" stop-opacity="0.0" />
        </linearGradient>
        <filter id="{glow_id}" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        """)
        
        path_pts = " ".join(f"{x},{y}" for x, y in coords)
        area_pts = f"{pad_l},{pad_t + chart_h} " + path_pts + f" {pad_l + chart_w},{pad_t + chart_h}"
        
        series_elements.append(f'<polygon points="{area_pts}" fill="url(#{grad_id})" />')
        series_elements.append(f'<polyline points="{path_pts}" fill="none" stroke="{stroke_color}" stroke-width="2.5" filter="url(#{glow_id})" stroke-linecap="round" stroke-linejoin="round" />')
        for x, y in coords:
            series_elements.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#0f172a" stroke="{stroke_color}" stroke-width="2" />')
            
    svg_defs = "\n".join(defs)
    series_html = "\n".join(series_elements)
    
    label = datasets[0].get("label", "") if datasets else ""
    label_html = f'<div style="font-size:0.75rem;font-weight:700;color:#94a3b8;margin-bottom:8px;font-family:monospace;letter-spacing:0.05em;text-transform:uppercase;">{label}</div>' if label else ""
    
    return f"""
    <div style="margin:1.5rem 0;padding:20px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {label_html}
      <div style="width:100%;height:200px;">
        <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
          <defs>
            {svg_defs}
          </defs>
          <!-- Grid & Y-Axes -->
          {grid_lines}
          <!-- X-Axes -->
          {x_labels}
          <!-- Series -->
          {series_html}
        </svg>
      </div>
    </div>
    """

def _render_data_table_sortable(b: dict) -> str:
    return '<table style="width:100%;margin:1rem 0;border-collapse:collapse;"><thead><tr style="background:#f3f4f6;"><th style="padding:8px;text-align:left;border:1px solid #e5e7eb;">Header 1</th><th style="padding:8px;text-align:left;border:1px solid #e5e7eb;">Header 2</th></tr></thead><tbody><tr><td style="padding:8px;border:1px solid #e5e7eb;">Data 1</td><td style="padding:8px;border:1px solid #e5e7eb;">Data 2</td></tr></tbody></table>'

def _render_metric_comparison_card(b: dict) -> str:
    label    = b.get("label", "Metric")
    current  = b.get("value", 0)
    previous = b.get("previous", 0)
    try:
        pct = round((float(current) - float(previous)) / float(previous) * 100, 1) if previous else 0
        delta_color = "#059669" if pct <= 0 else "#dc2626"  # lower is better for response time etc
        delta_str = f"{'↓' if pct <= 0 else '↑'} {abs(pct)}%"
    except Exception:
        delta_str = ""
        delta_color = "#6b7280"
    return (f'<div style="margin:1rem 0;padding:14px;border:1px solid #e5e7eb;border-radius:8px;">'
            f'<div style="font-size:0.72rem;color:#6b7280;margin-bottom:8px;">{label}</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">'
            f'<div><div style="font-size:0.65rem;color:#9ca3af;">Now</div>'
            f'<div style="font-size:1.4rem;font-weight:700;color:#7c3aed;">{current}</div></div>'
            f'<div><div style="font-size:0.65rem;color:#9ca3af;">Before</div>'
            f'<div style="font-size:1.4rem;font-weight:700;color:#9ca3af;">{previous}</div></div>'
            f'</div>'
            f'<div style="margin-top:6px;font-size:0.72rem;color:{delta_color};font-weight:600;">{delta_str}</div>'
            f'</div>')

def _render_mini_sparkline_set(b: dict) -> str:
    series = b.get("series", [])
    cols = min(len(series), 4) if series else 2
    cards = []
    
    chart_id = f"spark_{id(b)}"
    
    for si, s in enumerate(series):
        label = s.get("label", "")
        data  = s.get("data", [])
        if not data: continue
        n = len(data); mn = min(data); mx = max(data); rng = (mx - mn) or 1
        
        # SVG dimensions: 150x40
        w, h = 150, 40
        pad_x, pad_y = 5, 5
        chart_w = w - 2 * pad_x
        chart_h = h - 2 * pad_y
        
        coords = []
        for i, v in enumerate(data):
            x = pad_x + (i / (n - 1) if n > 1 else 0.5) * chart_w
            y = pad_y + (1 - (v - mn) / rng) * chart_h
            coords.append((x, y))
            
        path_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
        area_pts = f"{pad_x},{pad_y + chart_h} " + path_pts + f" {pad_x + chart_w},{pad_y + chart_h}"
        
        latest = data[-1]
        
        # Color of sparkline
        colors = ["#a855f7", "#10b981", "#3b82f6", "#f59e0b"]
        stroke_color = colors[si % len(colors)]
        
        grad_id = f"spark_grad_{chart_id}_{si}"
        glow_id = f"spark_glow_{chart_id}_{si}"
        
        cards.append(f"""
        <div style="padding:16px;background:rgba(15,23,42,0.4);border:1px solid rgba(255,255,255,0.05);border-radius:10px;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);display:flex;flex-direction:column;justify-content:space-between;gap:8px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <span style="font-size:0.75rem;font-weight:600;color:#94a3b8;font-family:monospace;letter-spacing:0.02em;">{label}</span>
            <span style="font-size:1.1rem;font-weight:800;color:#f1f5f9;font-family:monospace;">{latest}</span>
          </div>
          <div style="width:100%;height:40px;">
            <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
              <defs>
                <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="{stroke_color}" stop-opacity="0.25" />
                  <stop offset="100%" stop-color="{stroke_color}" stop-opacity="0.0" />
                </linearGradient>
                <filter id="{glow_id}" x="-10%" y="-10%" width="120%" height="120%">
                  <feGaussianBlur stdDeviation="1.5" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>
              <polygon points="{area_pts}" fill="url(#{grad_id})" />
              <polyline points="{path_pts}" fill="none" stroke="{stroke_color}" stroke-width="2" filter="url(#{glow_id})" stroke-linecap="round" stroke-linejoin="round" />
              <circle cx="{coords[-1][0]}" cy="{coords[-1][1]}" r="3" fill="#0f172a" stroke="{stroke_color}" stroke-width="2" />
            </svg>
          </div>
        </div>
        """)
        
    return f'<div style="margin:1.5rem 0;display:grid;grid-template-columns:repeat({cols},1fr);gap:12px;">{"".join(cards)}</div>'

def _render_donut_stat(b: dict) -> str:
    value     = b.get("value", 0)
    max_value = b.get("max_value", 100) or 100
    label     = b.get("label", "")
    unit      = b.get("unit", "")
    color     = b.get("color", "#10b981")
    size      = b.get("size", "140px")
    
    percentage = (value / max_value) * 100
    percentage = min(100, max(0, percentage))
    
    r = 40
    stroke_dasharray = 251.327
    stroke_dashoffset = stroke_dasharray - (percentage / 100) * stroke_dasharray
    
    donut_id = f"donut_{id(b)}"
    
    svg_html = f"""
    <svg viewBox="0 0 100 100" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="{donut_id}_grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="{color}" />
          <stop offset="100%" stop-color="{color}" stop-opacity="0.6" />
        </linearGradient>
        <filter id="{donut_id}_glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <circle cx="50" cy="50" r="{r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="10" />
      <circle cx="50" cy="50" r="{r}" fill="none" stroke="url(#{donut_id}_grad)" stroke-width="10" 
              stroke-dasharray="{stroke_dasharray}" stroke-dashoffset="{stroke_dashoffset}"
              stroke-linecap="round" transform="rotate(-90 50 50)" filter="url(#{donut_id}_glow)" />
      <text x="50" y="48" fill="#f1f5f9" font-size="16" font-weight="800" font-family="monospace" text-anchor="middle">{value:,.0f}{unit}</text>
      <text x="50" y="64" fill="rgba(255,255,255,0.4)" font-size="7" font-weight="600" font-family="monospace" text-anchor="middle">{percentage:.1f}%</text>
    </svg>
    """
    
    return f"""
    <div style="margin:1.5rem 0;padding:20px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);display:flex;align-items:center;gap:24px;">
      <div style="width:{size};height:{size};flex-shrink:0;">
        {svg_html}
      </div>
      <div>
        <div style="font-size:0.75rem;font-weight:700;color:#94a3b8;font-family:monospace;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:4px;">{label}</div>
        <div style="font-size:1.5rem;font-weight:800;color:#f1f5f9;font-family:-apple-system,sans-serif;margin-bottom:6px;">
          {value:,.0f}{unit} <span style="font-size:0.9rem;font-weight:400;color:rgba(255,255,255,0.4);">/ {max_value:,.0f}{unit}</span>
        </div>
        <div style="font-size:0.8rem;color:#10b981;font-weight:600;display:flex;align-items:center;gap:4px;">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};"></span>
          Progress Status: {percentage:.1f}% Target Met
        </div>
      </div>
    </div>
    """

def _interpolate_color(c1: str, c2: str, weight: float) -> str:
    c1 = c1.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    c2 = c2.lstrip("#")
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = int(r1 + (r2 - r1) * weight)
    g = int(g1 + (g2 - g1) * weight)
    b = int(b1 + (b2 - b1) * weight)
    return f"#{r:02x}{g:02x}{b:02x}"

def _get_color_from_scale(scale: list[str], weight: float) -> str:
    if not scale:
        return "#10b981"
    if len(scale) == 1:
        return scale[0]
    weight = min(1.0, max(0.0, weight))
    num_segments = len(scale) - 1
    segment = int(weight * num_segments)
    if segment >= num_segments:
        segment = num_segments - 1
    segment_w = 1.0 / num_segments
    segment_percent = (weight - (segment * segment_w)) / segment_w
    return _interpolate_color(scale[segment], scale[segment+1], segment_percent)

def _render_heatmap(b: dict) -> str:
    data        = b.get("data", [])
    labels_x    = b.get("labels_x", [])
    labels_y    = b.get("labels_y", [])
    color_scale = b.get("color_scale", ["#1e293b", "#10b981"])
    unit        = b.get("unit", "")
    
    if not data or not data[0]:
        return ""
        
    num_rows = len(data)
    num_cols = len(data[0])
    
    flat_data = [val for row in data for val in row]
    mn, mx = min(flat_data), max(flat_data)
    rng = (mx - mn) or 1
    
    cell_size = 32
    cell_gap = 6
    
    pad_l, pad_r, pad_t, pad_b = 80, 20, 30, 20
    
    grid_w = num_cols * cell_size + (num_cols - 1) * cell_gap
    grid_h = num_rows * cell_size + (num_rows - 1) * cell_gap
    
    w = pad_l + grid_w + pad_r
    h = pad_t + grid_h + pad_b
    
    y_labels = ""
    for r_idx, lbl in enumerate(labels_y):
        if r_idx < num_rows:
            y = pad_t + r_idx * (cell_size + cell_gap) + cell_size / 2 + 3
            y_labels += f'<text x="{pad_l - 12}" y="{y}" fill="rgba(255,255,255,0.4)" font-size="10" font-family="monospace" text-anchor="end">{lbl}</text>'
            
    x_labels = ""
    for c_idx, lbl in enumerate(labels_x):
        if c_idx < num_cols:
            x = pad_l + c_idx * (cell_size + cell_gap) + cell_size / 2
            x_labels += f'<text x="{x}" y="{pad_t - 10}" fill="rgba(255,255,255,0.4)" font-size="10" font-family="monospace" text-anchor="middle">{lbl}</text>'
            
    cells_html = []
    heatmap_id = f"heat_{id(b)}"
    
    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            weight = (val - mn) / rng if rng > 0 else 0.5
            cell_color = _get_color_from_scale(color_scale, weight)
            
            x = pad_l + c_idx * (cell_size + cell_gap)
            y = pad_t + r_idx * (cell_size + cell_gap)
            
            glow_attr = ""
            if weight > 0.7:
                glow_attr = f'filter="url(#{heatmap_id}_glow)"'
                
            cells_html.append(f"""
            <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{cell_color}" rx="4" ry="4" {glow_attr}>
              <title>{val:,.1f}{unit}</title>
            </rect>
            """)
            
    svg_html = f"""
    <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
      <defs>
        <filter id="{heatmap_id}_glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="1.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {y_labels}
      {x_labels}
      {"".join(cells_html)}
    </svg>
    """
    
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      <div style="width:100%;overflow-x:auto;">
        <div style="min-width:{w}px;max-width:100%;height:{h}px;margin:0 auto;">
          {svg_html}
        </div>
      </div>
    </div>
    """

def _render_status_dashboard(b: dict) -> str:
    return '<div style="margin:1rem 0;display:grid;grid-template-columns:repeat(2,1fr);gap:8px;"><div style="padding:8px;border:1px solid #e5e7eb;border-radius:4px;"><span style="display:inline-block;width:8px;height:8px;background:#059669;border-radius:50%;margin-right:6px;"></span>API: Online</div><div style="padding:8px;border:1px solid #e5e7eb;border-radius:4px;"><span style="display:inline-block;width:8px;height:8px;background:#059669;border-radius:50%;margin-right:6px;"></span>DB: Online</div></div>'

def _render_uptime_timeline(b: dict) -> str:
    uptime = float(b.get("uptime", 99.9))
    days   = b.get("days", 30)
    import random, hashlib
    seed = int(hashlib.md5(str(uptime).encode()).hexdigest()[:8], 16)
    random.seed(seed)
    outage_rate = (100 - uptime) / 100
    blocks = []
    for _ in range(days):
        r = random.random()
        if r < outage_rate:
            color = "#dc2626"
        elif r < outage_rate * 3:
            color = "#f59e0b"
        else:
            color = "#059669"
        blocks.append(f'<div style="background:{color};height:20px;border-radius:2px;" title="{color}"></div>')
    return (f'<div style="margin:1rem 0;padding:12px;border:1px solid #e5e7eb;border-radius:8px;">'
            f'<div style="display:grid;grid-template-columns:repeat({days},1fr);gap:2px;">{"".join(blocks)}</div>'
            f'<div style="font-size:0.7rem;color:#6b7280;margin-top:6px;">{days}-day uptime: {uptime}%</div>'
            f'</div>')

def _render_command_palette(b: dict) -> str:
    return '<div style="margin:1rem 0;padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#1f2937;color:#e5e7eb;"><div style="font-size:0.75rem;margin-bottom:6px;">⌘K to open</div><div style="font-size:0.8rem;padding:6px;background:#111827;border-radius:4px;margin-bottom:4px;">▶ Command 1</div><div style="font-size:0.8rem;padding:6px;background:#374151;border-radius:4px;">Command 2</div></div>'

def _render_search_result_card(b: dict) -> str:
    return '<div style="margin:1rem 0;padding:12px;border:1px solid #e5e7eb;border-radius:8px;"><div style="font-weight:600;font-size:0.9rem;color:#7c3aed;margin-bottom:4px;">Result Title</div><div style="font-size:0.8rem;color:#6b7280;margin-bottom:6px;">Example result description with relevant content snippet.</div><div style="font-size:0.7rem;color:#9ca3af;">example.com › category › result</div></div>'

def _render_punch_card(b: dict) -> str:
    data        = b.get("data", [])
    labels_days = b.get("labels_days", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    color       = b.get("color", "#00f2ff")
    title       = b.get("title", "")
    subtitle    = b.get("subtitle", "")
    
    if not data or not data[0]:
        return ""
        
    num_rows = len(data)
    num_cols = len(data[0])
    
    flat_data = [float(val) for row in data for val in row]
    mn, mx = min(flat_data), max(flat_data)
    rng = (mx - mn) or 1
    
    cell_size = 28
    cell_gap = 5
    
    pad_l, pad_r, pad_t, pad_b = 60, 25, 40, 25
    
    grid_w = num_cols * cell_size + (num_cols - 1) * cell_gap
    grid_h = num_rows * cell_size + (num_rows - 1) * cell_gap
    
    w = pad_l + grid_w + pad_r
    h = pad_t + grid_h + pad_b
    
    x_labels = ""
    for c_idx in range(num_cols):
        x = pad_l + c_idx * (cell_size + cell_gap) + cell_size / 2
        lbl = f"{c_idx:02d}"
        x_labels += f'<text x="{x}" y="{pad_t - 12}" fill="rgba(255,255,255,0.4)" font-size="8" font-family="monospace" text-anchor="middle">{lbl}</text>'
        
    y_labels = ""
    for r_idx, lbl in enumerate(labels_days):
        if r_idx < num_rows:
            y = pad_t + r_idx * (cell_size + cell_gap) + cell_size / 2 + 3
            y_labels += f'<text x="{pad_l - 12}" y="{y}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="end">{lbl}</text>'
            
    bubbles_html = []
    punch_id = f"punch_{id(b)}"
    
    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            if val <= 0:
                x = pad_l + c_idx * (cell_size + cell_gap) + cell_size / 2
                y = pad_t + r_idx * (cell_size + cell_gap) + cell_size / 2
                bubbles_html.append(f'<circle cx="{x}" cy="{y}" r="2" fill="rgba(255,255,255,0.06)" />')
                continue
                
            weight = (val - mn) / rng if rng > 0 else 0.5
            r = 3 + weight * 10
            x = pad_l + c_idx * (cell_size + cell_gap) + cell_size / 2
            y = pad_t + r_idx * (cell_size + cell_gap) + cell_size / 2
            
            opacity = 0.3 + weight * 0.7
            
            glow_attr = ""
            if weight > 0.6:
                glow_attr = f'filter="url(#{punch_id}_glow)"'
                
            bubbles_html.append(f"""
            <circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{color}" fill-opacity="{opacity:.2f}" {glow_attr}>
              <title>{labels_days[r_idx]} {c_idx:02d}:00 - {val:,.0f} commits</title>
            </circle>
            """)
            
    svg_html = f"""
    <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
      <defs>
        <filter id="{punch_id}_glow" x="-30%" y="-30%" width="160%" height="140%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {y_labels}
      {x_labels}
      {"".join(bubbles_html)}
    </svg>
    """
    
    header_html = ""
    if title or subtitle:
        header_html = f"""
        <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:flex-end;">
          <div>
            {f'<div style="font-size:1.1rem;font-weight:800;color:#f1f5f9;margin-bottom:2px;">{title}</div>' if title else ''}
            {f'<div style="font-size:0.75rem;color:rgba(255,255,255,0.4);font-family:monospace;">{subtitle}</div>' if subtitle else ''}
          </div>
          <div style="display:flex;gap:12px;font-size:0.75rem;color:rgba(255,255,255,0.4);font-family:monospace;align-items:center;">
            <span>Less</span>
            <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:{color};opacity:0.3;"></span>
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};opacity:0.6;"></span>
            <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{color};opacity:1.0;"></span>
            <span>More</span>
          </div>
        </div>
        """
        
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      <div style="width:100%;overflow-x:auto;">
        <div style="min-width:{w}px;max-width:100%;height:{h}px;margin:0 auto;">
          {svg_html}
        </div>
      </div>
    </div>
    """

def _render_sankey_flow(b: dict) -> str:
    raw_nodes = b.get("nodes", [])
    raw_links = b.get("links", [])
    title     = b.get("title", "")
    
    if not raw_links:
        return ""
        
    nodes_map = {n["id"]: n for n in raw_nodes}
    
    for link in raw_links:
        s, t = link["source"], link["target"]
        if s not in nodes_map:
            nodes_map[s] = {"id": s, "label": s.capitalize(), "column": 0}
        if t not in nodes_map:
            nodes_map[t] = {"id": t, "label": t.capitalize(), "column": 1}
            
    left_nodes = []
    right_nodes = []
    
    node_out_totals = {}
    node_in_totals = {}
    for link in raw_links:
        s, t, v = link["source"], link["target"], float(link.get("value", 1))
        node_out_totals[s] = node_out_totals.get(s, 0.0) + v
        node_in_totals[t] = node_in_totals.get(t, 0.0) + v
        
    for nid, node in nodes_map.items():
        col = node.get("column", 0)
        if "column" not in node:
            if nid in node_out_totals:
                col = 0
            else:
                col = 1
                
        node_item = {
            "id": nid,
            "label": node.get("label", nid),
            "color": node.get("color", "#38bdf8" if col == 0 else "#10b981"),
            "total_out": node_out_totals.get(nid, 0.0),
            "total_in": node_in_totals.get(nid, 0.0),
        }
        node_item["total"] = max(node_item["total_out"], node_item["total_in"], 1.0)
        
        if col == 0:
            left_nodes.append(node_item)
        else:
            right_nodes.append(node_item)
            
    left_nodes.sort(key=lambda x: x["total"], reverse=True)
    right_nodes.sort(key=lambda x: x["total"], reverse=True)
    
    w, h = 640, 340
    pad_l, pad_r, pad_t, pad_b = 60, 60, 50, 40
    usable_h = h - pad_t - pad_b
    
    x_left = pad_l
    node_w = 16
    x_right = w - pad_r - node_w
    
    gap_l = 16
    total_gaps_l = (len(left_nodes) - 1) * gap_l if len(left_nodes) > 1 else 0
    avail_h_l = max(usable_h - total_gaps_l, 100)
    sum_left_totals = sum(n["total"] for n in left_nodes) or 1.0
    scale_l = avail_h_l / sum_left_totals
    
    y = pad_t
    left_positions = {}
    for n in left_nodes:
        n_h = max(n["total"] * scale_l, 10.0)
        left_positions[n["id"]] = {
            "x": x_left,
            "y": y,
            "w": node_w,
            "h": n_h,
            "color": n["color"],
            "label": n["label"],
            "total": n["total"],
            "curr_offset": 0.0,
            "scale": scale_l,
        }
        y += n_h + gap_l
        
    gap_r = 16
    total_gaps_r = (len(right_nodes) - 1) * gap_r if len(right_nodes) > 1 else 0
    avail_h_r = max(usable_h - total_gaps_r, 100)
    sum_right_totals = sum(n["total"] for n in right_nodes) or 1.0
    scale_r = avail_h_r / sum_right_totals
    
    y = pad_t
    right_positions = {}
    for n in right_nodes:
        n_h = max(n["total"] * scale_r, 10.0)
        right_positions[n["id"]] = {
            "x": x_right,
            "y": y,
            "w": node_w,
            "h": n_h,
            "color": n["color"],
            "label": n["label"],
            "total": n["total"],
            "curr_offset": 0.0,
            "scale": scale_r,
        }
        y += n_h + gap_r
        
    gradients_html = []
    links_html = []
    
    sankey_id = f"sankey_{id(b)}"
    
    for idx, link in enumerate(raw_links):
        s, t, v = link["source"], link["target"], float(link.get("value", 1))
        
        if s not in left_positions or t not in right_positions:
            continue
            
        lp = left_positions[s]
        rp = right_positions[t]
        
        link_h_l = v * lp["scale"]
        link_h_r = rp["scale"] * v if rp["total"] > 0 else rp["scale"] * v
        # Ensure we don't scale by RP if total sum doesn't match
        link_h_r = v * rp["scale"]
        
        y_l = lp["y"] + lp["curr_offset"]
        y_r = rp["y"] + rp["curr_offset"]
        
        lp["curr_offset"] += link_h_l
        rp["curr_offset"] += link_h_r
        
        x0 = lp["x"] + lp["w"]
        x1 = rp["x"]
        dx = (x1 - x0) / 2
        
        top_curve = f"C {x0 + dx} {y_l}, {x1 - dx} {y_r}, {x1} {y_r}"
        bot_curve = f"C {x1 - dx} {y_r + link_h_r}, {x0 + dx} {y_l + link_h_l}, {x0} {y_l + link_h_l}"
        
        path_data = f"M {x0} {y_l} {top_curve} L {x1} {y_r + link_h_r} {bot_curve} Z"
        
        grad_id = f"{sankey_id}_grad_{idx}"
        link_color = link.get("color")
        
        if link_color:
            fill_val = link_color
            opacity = 0.35
        else:
            gradients_html.append(f"""
            <linearGradient id="{grad_id}" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="{lp['color']}" stop-opacity="0.3" />
              <stop offset="100%" stop-color="{rp['color']}" stop-opacity="0.3" />
            </linearGradient>
            """)
            fill_val = f"url(#{grad_id})"
            opacity = 1.0
            
        links_html.append(f"""
        <path d="{path_data}" fill="{fill_val}" opacity="{opacity}" style="transition: opacity 0.2s;" onmouseover="this.setAttribute('opacity', '0.65')" onmouseout="this.setAttribute('opacity', '{opacity}')">
          <title>{lp['label']} → {rp['label']}: {v:,.0f}</title>
        </path>
        """)
        
    nodes_html = []
    labels_html = []
    
    for nid, lp in left_positions.items():
        node_glow_id = f"{sankey_id}_node_glow_{nid}"
        gradients_html.append(f"""
        <linearGradient id="{node_glow_id}_grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{lp['color']}" />
          <stop offset="100%" stop-color="{lp['color']}" stop-opacity="0.6" />
        </linearGradient>
        """)
        
        nodes_html.append(f"""
        <rect x="{lp['x']}" y="{lp['y']}" width="{lp['w']}" height="{lp['h']}" fill="url(#{node_glow_id}_grad)" rx="3" ry="3" />
        """)
        
        labels_html.append(f"""
        <text x="{lp['x'] - 8}" y="{lp['y'] + lp['h']/2 + 4}" fill="#f1f5f9" font-size="11" font-weight="700" font-family="monospace" text-anchor="end">{lp['label']}</text>
        <text x="{lp['x'] - 8}" y="{lp['y'] + lp['h']/2 + 15}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="end">{lp['total']:,.0f}</text>
        """)
        
    for nid, rp in right_positions.items():
        node_glow_id = f"{sankey_id}_node_glow_{nid}"
        gradients_html.append(f"""
        <linearGradient id="{node_glow_id}_grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{rp['color']}" />
          <stop offset="100%" stop-color="{rp['color']}" stop-opacity="0.6" />
        </linearGradient>
        """)
        
        nodes_html.append(f"""
        <rect x="{rp['x']}" y="{rp['y']}" width="{rp['w']}" height="{rp['h']}" fill="url(#{node_glow_id}_grad)" rx="3" ry="3" />
        """)
        
        labels_html.append(f"""
        <text x="{rp['x'] + rp['w'] + 8}" y="{rp['y'] + rp['h']/2 + 4}" fill="#f1f5f9" font-size="11" font-weight="700" font-family="monospace" text-anchor="start">{rp['label']}</text>
        <text x="{rp['x'] + rp['w'] + 8}" y="{rp['y'] + rp['h']/2 + 15}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="start">{rp['total']:,.0f}</text>
        """)
        
    svg_html = f"""
    <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
      <defs>
        {"".join(gradients_html)}
      </defs>
      {"".join(links_html)}
      {"".join(nodes_html)}
      {"".join(labels_html)}
    </svg>
    """
    
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:16px;">
          <div style="font-size:1.1rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px;">{title}</div>
        </div>
        """
        
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      <div style="width:100%;overflow-x:auto;">
        <div style="min-width:{w}px;max-width:100%;height:{h}px;margin:0 auto;">
          {svg_html}
        </div>
      </div>
    </div>
    """

def _render_cohort_retention(b: dict) -> str:
    cohorts     = b.get("cohorts", [])
    periods     = b.get("periods", [])
    color_scale = b.get("color_scale", ["#1e293b", "#10b981"])
    title       = b.get("title", "")
    
    if not cohorts or not periods:
        return ""
        
    num_periods = len(periods)
    
    headers = []
    headers.append('<div style="font-weight:700;color:rgba(255,255,255,0.4);font-size:0.75rem;font-family:monospace;text-transform:uppercase;padding:12px;letter-spacing:0.05em;">Cohort</div>')
    headers.append('<div style="font-weight:700;color:rgba(255,255,255,0.4);font-size:0.75rem;font-family:monospace;text-transform:uppercase;padding:12px;letter-spacing:0.05em;text-align:right;">Size</div>')
    for p in periods:
        headers.append(f'<div style="font-weight:700;color:rgba(255,255,255,0.4);font-size:0.75rem;font-family:monospace;text-transform:uppercase;padding:12px;letter-spacing:0.05em;text-align:center;">{p}</div>')
        
    rows_html = []
    for row_idx, cohort in enumerate(cohorts):
        name = cohort.get("cohort_name", f"Cohort {row_idx}")
        size = cohort.get("original_size", "—")
        if isinstance(size, (int, float)):
            size_str = f"{size:,.0f}"
        else:
            size_str = str(size)
            
        rates = cohort.get("retention_rates", [])
        
        row_cells = []
        row_cells.append(f'<div style="font-weight:700;color:#f1f5f9;font-size:0.85rem;padding:12px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;align-items:center;">{name}</div>')
        row_cells.append(f'<div style="color:rgba(255,255,255,0.6);font-size:0.85rem;font-family:monospace;padding:12px;border-bottom:1px solid rgba(255,255,255,0.04);text-align:right;display:flex;align-items:center;justify-content:flex-end;">{size_str}</div>')
        
        for p_idx in range(num_periods):
            if p_idx < len(rates):
                rate = float(rates[p_idx])
                weight = rate / 100.0
                cell_bg = _get_color_from_scale(color_scale, weight)
                
                text_color = "#f1f5f9"
                if weight > 0.65:
                    text_color = "#0f172a"
                    
                cell_style = (
                    f"background:{cell_bg};"
                    f"color:{text_color};"
                    f"font-weight:700;"
                    f"font-size:0.8rem;"
                    f"font-family:monospace;"
                    f"text-align:center;"
                    f"margin:2px;"
                    f"border-radius:4px;"
                    f"display:flex;"
                    f"align-items:center;"
                    f"justify-content:center;"
                    f"transition:transform 0.15s, box-shadow 0.15s;"
                )
                
                row_cells.append(f"""
                <div style="{cell_style}" onmouseover="this.style.transform='scale(1.05)';this.style.boxShadow='0 4px 12px rgba(0,0,0,0.3)';" onmouseout="this.style.transform='scale(1)';this.style.boxShadow='none';">
                  {rate:.1f}%
                </div>
                """)
            else:
                row_cells.append('<div style="background:transparent;margin:2px;"></div>')
                
        rows_html.append("".join(row_cells))
        
    grid_cols_style = f"grid-template-columns: 140px 100px repeat({num_periods}, 1fr);"
    
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:16px;">
          <div style="font-size:1.1rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px;">{title}</div>
        </div>
        """
        
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      <div style="width:100%;overflow-x:auto;">
        <div style="min-width:{240 + num_periods * 80}px;max-width:100%;display:grid;{grid_cols_style};background:rgba(15,23,42,0.3);border-radius:8px;padding:8px;gap:2px;">
          {"".join(headers)}
          {"".join(rows_html)}
        </div>
      </div>
    </div>
    """


def _render_task_list(b: dict) -> str:
    title = b.get("title", "")
    tasks = b.get("tasks", [])
    
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">
          <div style="font-size:1.15rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px; display:flex; align-items:center; gap:8px;">
            <span style="color:#00f2ff; font-weight:900;">⬡</span> {title}
          </div>
          <div style="font-size:0.75rem; font-family:monospace; color:rgba(255,255,255,0.4); background:rgba(255,255,255,0.04); padding:4px 8px; border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
            {len(tasks)} Tasks
          </div>
        </div>
        """
        
    tasks_html = []
    for task in tasks:
        text = task.get("text", "")
        completed = task.get("completed", False)
        priority = task.get("priority", "medium").lower()
        due_date = task.get("due_date", "")
        assignee = task.get("assignee", "")
        
        if completed:
            checkbox_style = "background:#10b981; border-color:#10b981; color:#0f172a; box-shadow: 0 0 10px rgba(16,185,129,0.4);"
            checkbox_inner = '<span style="font-size:11px; font-weight:900;">✓</span>'
            text_style = "text-decoration:line-through; color:rgba(255,255,255,0.4);"
        else:
            checkbox_style = "background:rgba(255,255,255,0.03); border-color:rgba(255,255,255,0.2); color:transparent;"
            checkbox_inner = ""
            text_style = "color:#f3f4f6;"
            
        if priority == "high":
            p_style = "background:rgba(239, 68, 68, 0.1); color:#ef4444; border: 1px solid rgba(239,68,68,0.25);"
            p_label = "HIGH"
        elif priority == "low":
            p_style = "background:rgba(59, 130, 246, 0.1); color:#3b82f6; border: 1px solid rgba(59,130,246,0.25);"
            p_label = "LOW"
        else:
            p_style = "background:rgba(245, 158, 11, 0.1); color:#f59e0b; border: 1px solid rgba(245,158,11,0.25);"
            p_label = "MED"
            
        assignee_html = ""
        if assignee:
            assignee_html = f"""
            <div style="width:24px; height:24px; border-radius:50%; background:linear-gradient(135deg, #00f2ff 0%, #0072ff 100%); display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:800; color:#fff; font-family:monospace; border:1px solid rgba(255,255,255,0.2); flex-shrink:0;" title="Assignee: {assignee}">
              {assignee[:2].upper()}
            </div>
            """
            
        due_html = ""
        if due_date:
            due_html = f"""
            <div style="font-size:0.75rem; font-family:monospace; color:rgba(255,255,255,0.5); display:flex; align-items:center; gap:4px; padding:3px 8px; border-radius:4px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.04); flex-shrink:0;">
              <span style="font-size:0.7rem;">📅</span> {due_date}
            </div>
            """
            
        tasks_html.append(f"""
        <div style="display:flex; align-items:center; justify-content:space-between; padding:12px 16px; background:rgba(15,23,42,0.2); border:1px solid rgba(255,255,255,0.04); border-radius:8px; gap:16px; transition:all 0.2s ease-in-out;" onmouseover="this.style.background='rgba(255,255,255,0.03)';this.style.borderColor='rgba(0,242,255,0.15)';" onmouseout="this.style.background='rgba(15,23,42,0.2)';this.style.borderColor='rgba(255,255,255,0.04)';">
          <div style="display:flex; align-items:center; gap:12px; flex-grow:1; min-width:0;">
            <div style="width:18px; height:18px; border-radius:4px; border:1.5px solid; display:flex; align-items:center; justify-content:center; flex-shrink:0; cursor:pointer; transition:all 0.15s ease-in-out; {checkbox_style}">
              {checkbox_inner}
            </div>
            <div style="font-size:0.9rem; font-weight:500; font-family:sans-serif; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; {text_style}">
              {text}
            </div>
          </div>
          
          <div style="display:flex; align-items:center; gap:10px; flex-shrink:0;">
            <div style="font-size:0.65rem; font-weight:800; font-family:monospace; padding:3px 6px; border-radius:4px; letter-spacing:0.05em; {p_style}">
              {p_label}
            </div>
            {due_html}
            {assignee_html}
          </div>
        </div>
        """)
        
    tasks_container = f'<div style="display:flex; flex-direction:column; gap:8px;">{"".join(tasks_html)}</div>'
    
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      {tasks_container}
    </div>
    """


def _render_sentiment_summary(b: dict) -> str:
    title = b.get("title", "")
    sentiment_index = b.get("sentiment_index", 75)
    emotional_journey = b.get("emotional_journey", [])
    themes = b.get("themes", [])
    
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:20px;">
          <div style="font-size:1.15rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px; display:flex; align-items:center; gap:8px;">
            <span style="color:#ec4899; font-weight:900;">⬡</span> {title}
          </div>
        </div>
        """
        
    gauge_id = f"sent_gauge_{id(b)}"
    stroke_dasharray = 109.956
    stroke_dashoffset = stroke_dasharray - (sentiment_index / 100.0) * stroke_dasharray
    
    if sentiment_index >= 75:
        sentiment_color = "#10b981"
        sentiment_label = "POSITIVE"
    elif sentiment_index >= 50:
        sentiment_color = "#38bdf8"
        sentiment_label = "BALANCED"
    else:
        sentiment_color = "#f59e0b"
        sentiment_label = "ATTENTION"
        
    gauge_svg = f"""
    <div style="width:160px; height:140px; display:flex; flex-direction:column; align-items:center; justify-content:center; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.04); border-radius:12px; padding:10px; flex-shrink:0;">
      <svg viewBox="0 0 100 80" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="{gauge_id}_grad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#f59e0b" />
            <stop offset="50%" stop-color="#38bdf8" />
            <stop offset="100%" stop-color="#10b981" />
          </linearGradient>
          <filter id="{gauge_id}_glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <path d="M 15 60 A 35 35 0 0 1 85 60" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8" stroke-linecap="round" />
        <path d="M 15 60 A 35 35 0 0 1 85 60" fill="none" stroke="url(#{gauge_id}_grad)" stroke-width="8" stroke-linecap="round"
              stroke-dasharray="{stroke_dasharray}" stroke-dashoffset="{stroke_dashoffset}" filter="url(#{gauge_id}_glow)" />
        <text x="50" y="53" text-anchor="middle" font-weight="900" font-size="18" fill="#f1f5f9" font-family="monospace">{sentiment_index}%</text>
        <text x="50" y="70" text-anchor="middle" font-weight="800" font-size="7" fill="{sentiment_color}" font-family="monospace" letter-spacing="0.1em">{sentiment_label}</text>
      </svg>
    </div>
    """
    
    journey_svg = ""
    if emotional_journey:
        points = []
        width = 280
        height = 120
        n_points = len(emotional_journey)
        center_y = height / 2.0
        x_min = 15
        x_max = width - 15
        y_min = 15
        y_max = height - 15
        
        for i, val in enumerate(emotional_journey):
            x = x_min + (i / max(1, n_points - 1)) * (x_max - x_min)
            y = center_y - val * (center_y - y_min)
            points.append((x, y))
            
        line_path = " ".join(f"{'M' if i == 0 else 'L'} {px:.1f} {py:.1f}" for i, (px, py) in enumerate(points))
        
        area_points = list(points)
        area_points.append((points[-1][0], center_y))
        area_points.append((points[0][0], center_y))
        area_path = " ".join(f"{'M' if i == 0 else 'L'} {px:.1f} {py:.1f}" for i, (px, py) in enumerate(area_points)) + " Z"
        
        journey_id = f"sent_journey_{id(b)}"
        
        journey_svg = f"""
        <div style="flex-grow:1; height:140px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.04); border-radius:12px; padding:10px; display:flex; flex-direction:column; justify-content:space-between; min-width:240px;">
          <div style="font-size:0.7rem; font-family:monospace; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Emotional Journey (Timeline)</div>
          <div style="width:100%; height:110px;">
            <svg viewBox="0 0 {width} {height}" width="100%" height="100%" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="{journey_id}_line_grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#10b981" />
                  <stop offset="50%" stop-color="#38bdf8" />
                  <stop offset="100%" stop-color="#ef4444" />
                </linearGradient>
                <linearGradient id="{journey_id}_area_grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#10b981" stop-opacity="0.25" />
                  <stop offset="50%" stop-color="#38bdf8" stop-opacity="0.1" />
                  <stop offset="100%" stop-color="#ef4444" stop-opacity="0.02" />
                </linearGradient>
                <filter id="{journey_id}_glow" x="-10%" y="-10%" width="120%" height="120%">
                  <feGaussianBlur stdDeviation="1.5" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>
              <line x1="{x_min}" y1="{center_y}" x2="{x_max}" y2="{center_y}" stroke="rgba(255,255,255,0.15)" stroke-dasharray="3,3" stroke-width="1" />
              <path d="{area_path}" fill="url(#{journey_id}_area_grad)" />
              <path d="{line_path}" stroke="url(#{journey_id}_line_grad)" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" filter="url(#{journey_id}_glow)" />
              <text x="{x_max}" y="{y_min+4}" text-anchor="end" font-size="8" fill="#10b981" font-family="monospace">Positive</text>
              <text x="{x_max}" y="{center_y-4}" text-anchor="end" font-size="8" fill="rgba(255,255,255,0.3)" font-family="monospace">Neutral</text>
              <text x="{x_max}" y="{y_max-4}" text-anchor="end" font-size="8" fill="#ef4444" font-family="monospace">Negative</text>
            </svg>
          </div>
        </div>
        """
        
    themes_html = []
    for theme in themes:
        theme_name = theme.get("theme", "")
        mood = theme.get("mood", "")
        score = theme.get("score", 50)
        
        if mood.lower() in ("analytical", "calm", "neutral"):
            theme_color = "#38bdf8"
        elif mood.lower() in ("engaged", "excited", "happy", "positive"):
            theme_color = "#10b981"
        elif mood.lower() in ("hesitant", "skeptical", "concerned", "negative"):
            theme_color = "#f59e0b"
        else:
            theme_color = "#a7f3d0"
            
        themes_html.append(f"""
        <div style="display:flex; flex-direction:column; gap:4px; padding:8px 12px; background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.03); border-radius:6px;">
          <div style="display:flex; align-items:center; justify-content:space-between; font-size:0.8rem;">
            <div style="font-weight:600; color:#f1f5f9; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; max-width:70%;">{theme_name}</div>
            <div style="font-size:0.7rem; font-family:monospace; color:{theme_color}; background:rgba(255,255,255,0.03); padding:1px 6px; border-radius:4px; border:1px solid rgba(255,255,255,0.05); text-transform:uppercase;">{mood}</div>
          </div>
          <div style="width:100%; height:4px; background:rgba(255,255,255,0.04); border-radius:2px; overflow:hidden;">
            <div style="width:{score}%; height:100%; background:{theme_color}; border-radius:2px; box-shadow:0 0 4px {theme_color};"></div>
          </div>
        </div>
        """)
        
    themes_container = ""
    if themes:
        themes_container = f"""
        <div style="display:flex; flex-direction:column; gap:8px;">
          <div style="font-size:0.7rem; font-family:monospace; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Top Moods & Themes Analysis</div>
          <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:10px;">
            {"".join(themes_html)}
          </div>
        </div>
        """
        
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px); display:flex; flex-direction:column; gap:20px;">
      {header_html}
      <div style="display:flex; flex-wrap:wrap; gap:16px;">
        {gauge_svg}
        {journey_svg}
      </div>
      {themes_container}
    </div>
    """


def _render_conversion_funnel(b: dict) -> str:
    title = b.get("title", "")
    steps = b.get("steps", [])
    if not steps:
        return ""
        
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">
          <div style="font-size:1.15rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px; display:flex; align-items:center; gap:8px;">
            <span style="color:#10b981; font-weight:900;">▼</span> {title}
          </div>
        </div>
        """
        
    # Standard width 480, height 260
    w, h = 480, 260
    pad_l, pad_r, pad_t, pad_b = 30, 30, 20, 20
    draw_w = w - pad_l - pad_r
    draw_h = h - pad_t - pad_b
    
    n_steps = len(steps)
    step_h = draw_h / max(1, n_steps)
    bar_h = step_h * 0.75
    
    max_val = max(float(s.get("value", 1)) for s in steps)
    
    funnel_id = f"funnel_{id(b)}"
    elements = []
    
    # Render defs for neon glow & linear gradients
    elements.append(f"""
      <defs>
        <linearGradient id="{funnel_id}_grad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#10b981" stop-opacity="0.3" />
          <stop offset="50%" stop-color="#00f2ff" stop-opacity="0.15" />
          <stop offset="100%" stop-color="#10b981" stop-opacity="0.3" />
        </linearGradient>
        <filter id="{funnel_id}_glow" x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
    """)
    
    for i, step in enumerate(steps):
        name = step.get("stage", "")
        val = float(step.get("value", 0))
        
        curr_ratio = val / max_val if max_val > 0 else 1.0
        
        next_ratio = curr_ratio
        if i + 1 < n_steps:
            next_ratio = float(steps[i+1].get("value", 0)) / max_val if max_val > 0 else 1.0
            
        y1 = pad_t + i * step_h
        y2 = y1 + bar_h
        
        half_w1 = (curr_ratio * draw_w) / 2.0
        half_w2 = (next_ratio * draw_w) / 2.0
        cx = pad_l + draw_w / 2.0
        
        x1_top = cx - half_w1
        x2_top = cx + half_w1
        x1_bot = cx - half_w2
        x2_bot = cx + half_w2
        
        pts = f"{x1_top:.1f},{y1:.1f} {x2_top:.1f},{y1:.1f} {x2_bot:.1f},{y2:.1f} {x1_bot:.1f},{y2:.1f}"
        
        leak_html = ""
        if i > 0:
            prev_val = float(steps[i-1].get("value", 1))
            drop_percent = ((prev_val - val) / prev_val) * 100 if prev_val > 0 else 0
            if drop_percent > 5:
                leak_html += f"""
                <path d="M {x1_top - 10:.1f} {y1 - 5:.1f} Q {x1_top - 25:.1f} {y1 + 10:.1f} {x1_top - 35:.1f} {y1 + 5:.1f}" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="2,2" />
                <polygon points="{x1_top - 35:.1f},{y1 + 2:.1f} {x1_top - 40:.1f},{y1 + 8:.1f} {x1_top - 32:.1f},{y1 + 8:.1f}" fill="#ef4444" />
                <text x="{x1_top - 42:.1f}" y="{y1 + 12:.1f}" fill="#ef4444" font-size="7.5" font-family="monospace" text-anchor="end">-{drop_percent:.0f}%</text>
                """
        
        percent_label = f"{val:,.0f}"
        if i > 0:
            first_val = float(steps[0].get("value", 1))
            retention = (val / first_val) * 100 if first_val > 0 else 100
            percent_label += f" ({retention:.0f}%)"
            
        elements.append(f"""
        <polygon points="{pts}" fill="url(#{funnel_id}_grad)" stroke="#00f2ff" stroke-width="1.5" filter="url(#{funnel_id}_glow)" style="transition:all 0.2s;" />
        <text x="{cx:.1f}" y="{y1 + bar_h / 2.0 + 3:.1f}" fill="#f1f5f9" font-size="9.5" font-weight="800" font-family="monospace" text-anchor="middle">{name}: {percent_label}</text>
        {leak_html}
        """)
        
    svg_content = f"""
    <div style="width:100%; height:260px; background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.03); border-radius:12px; padding:12px; box-sizing:border-box;">
      <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        {"".join(elements)}
      </svg>
    </div>
    """
    
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      {svg_content}
    </div>
    """


def _render_gauge_sla(b: dict) -> str:
    import math
    title = b.get("title", "")
    val = float(b.get("value", 0))
    max_val = float(b.get("max_value", 100))
    unit = b.get("unit", "")
    label = b.get("label", "SLA Status")
    
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:15px; display:flex; align-items:center; justify-content:space-between;">
          <div style="font-size:1.15rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px; display:flex; align-items:center; gap:8px;">
            <span style="color:#00f2ff; font-weight:900;">◵</span> {title}
          </div>
        </div>
        """
        
    pct = (val / max_val) * 100 if max_val > 0 else 0
    pct = min(100.0, max(0.0, pct))
    
    path_len = 314.159
    dash_offset = path_len - (pct / 100.0) * path_len
    
    angle = 180 + (pct / 100.0) * 180
    rad = math.radians(angle)
    nx = 150 + 85 * math.cos(rad)
    ny = 140 + 85 * math.sin(rad)
    
    gauge_id = f"gauge_sla_{id(b)}"
    
    if pct >= 95:
        status_color = "#10b981"
        status_label = "HEALTHY"
    elif pct >= 85:
        status_color = "#38bdf8"
        status_label = "WARNING"
    else:
        status_color = "#ef4444"
        status_label = "BREACHED"
        
    svg_html = f"""
    <div style="width:100%; height:200px; display:flex; justify-content:center; align-items:center;">
      <svg viewBox="0 0 300 180" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="{gauge_id}_grad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#ef4444" />
            <stop offset="60%" stop-color="#f59e0b" />
            <stop offset="100%" stop-color="#10b981" />
          </linearGradient>
          <filter id="{gauge_id}_glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        
        <path d="M 50 140 A 100 100 0 0 1 250 140" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="14" stroke-linecap="round" />
        
        <path d="M 50 140 A 100 100 0 0 1 250 140" fill="none" stroke="url(#{gauge_id}_grad)" stroke-width="14" stroke-linecap="round"
              stroke-dasharray="{path_len}" stroke-dashoffset="{dash_offset}" filter="url(#{gauge_id}_glow)" />
              
        <line x1="50" y1="140" x2="60" y2="140" stroke="rgba(255,255,255,0.2)" stroke-width="2" />
        <line x1="150" y1="40" x2="150" y2="50" stroke="rgba(255,255,255,0.2)" stroke-width="2" />
        <line x1="240" y1="140" x2="250" y2="140" stroke="rgba(255,255,255,0.2)" stroke-width="2" />
        
        <line x1="150" y1="140" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{status_color}" stroke-width="3" stroke-linecap="round" filter="url(#{gauge_id}_glow)" />
        <circle cx="150" cy="140" r="8" fill="#0f172a" stroke="{status_color}" stroke-width="3" />
        
        <text x="150" y="115" text-anchor="middle" font-size="24" font-weight="900" fill="#f1f5f9" font-family="monospace">{val:,.1f}{unit}</text>
        <text x="150" y="132" text-anchor="middle" font-size="8" font-weight="800" fill="{status_color}" font-family="monospace" letter-spacing="0.1em">{status_label} · {label.upper()}</text>
      </svg>
    </div>
    """
    
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      {svg_html}
    </div>
    """


def _render_stacked_area(b: dict) -> str:
    title = b.get("title", "")
    labels = b.get("labels", [])
    series = b.get("series", [])
    
    if not series or not labels:
        return ""
        
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">
          <div style="font-size:1.15rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px; display:flex; align-items:center; gap:8px;">
            <span style="color:#38bdf8; font-weight:900;">⬟</span> {title}
          </div>
        </div>
        """
        
    w, h = 520, 240
    pad_l, pad_r, pad_t, pad_b = 55, 20, 30, 35
    chart_w = w - pad_l - pad_r
    chart_h = h - pad_t - pad_b
    
    n_pts = len(labels)
    n_series = len(series)
    
    stacked_y_vals = []
    curr_stack = [0.0] * n_pts
    for s_idx, s in enumerate(series):
        data = [float(v) for v in s.get("data", [])]
        if len(data) < n_pts:
            data += [0.0] * (n_pts - len(data))
        for i in range(n_pts):
            curr_stack[i] += data[i]
        stacked_y_vals.append(list(curr_stack))
        
    max_stacked_val = max(curr_stack) if curr_stack else 1.0
    rng = max_stacked_val or 1.0
    
    layers_svg = []
    defs_html = []
    
    grid_lines = ""
    for grid_idx in range(5):
        grid_y = pad_t + (grid_idx / 4) * chart_h
        grid_v = max_stacked_val - (grid_idx / 4) * rng
        grid_lines += f"""
        <line x1="{pad_l}" y1="{grid_y}" x2="{pad_l + chart_w}" y2="{grid_y}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="3,3" />
        <text x="{pad_l - 12}" y="{grid_y + 3}" fill="rgba(255,255,255,0.4)" font-size="8.5" font-family="monospace" text-anchor="end">{grid_v:,.0f}</text>
        """
        
    x_labels_html = ""
    for i, lbl in enumerate(labels):
        x = pad_l + (i / max(1, n_pts - 1)) * chart_w
        x_labels_html += f'<text x="{x}" y="{pad_t + chart_h + 18}" fill="rgba(255,255,255,0.4)" font-size="8.5" font-family="monospace" text-anchor="middle">{lbl}</text>'
        
    for s_idx in range(n_series - 1, -1, -1):
        s = series[s_idx]
        color = s.get("color", "#38bdf8")
        
        coords = []
        for i in range(n_pts):
            val = stacked_y_vals[s_idx][i]
            x = pad_l + (i / max(1, n_pts - 1)) * chart_w
            y = pad_t + (1 - val / rng) * chart_h
            coords.append((x, y))
            
        path_pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in coords)
        area_pts = f"{pad_l:.1f},{pad_t + chart_h:.1f} " + path_pts + f" {pad_l + chart_w:.1f},{pad_t + chart_h:.1f}"
        
        layer_id = f"stack_layer_{s_idx}_{id(b)}"
        
        defs_html.append(f"""
        <linearGradient id="{layer_id}_area_grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{color}" stop-opacity="0.3" />
          <stop offset="100%" stop-color="{color}" stop-opacity="0.0" />
        </linearGradient>
        <filter id="{layer_id}_glow" x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation="1.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        """)
        
        layers_svg.append(f"""
        <polygon points="{area_pts}" fill="url(#{layer_id}_area_grad)" />
        <polyline points="{path_pts}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" filter="url(#{layer_id}_glow)" />
        """)
        
    legends_html = []
    for s_idx, s in enumerate(series):
        color = s.get("color", "#38bdf8")
        label_name = s.get("label", "")
        legends_html.append(f"""
        <div style="display:flex; align-items:center; gap:6px; font-size:0.75rem; font-family:monospace; color:rgba(255,255,255,0.7);">
          <div style="width:10px; height:10px; border-radius:3px; background:{color}; box-shadow: 0 0 6px {color};"></div>
          <span>{label_name}</span>
        </div>
        """)
    legends_container = f'<div style="display:flex; flex-wrap:wrap; gap:16px; margin-top:12px; justify-content:center;">{"".join(legends_html)}</div>'
    
    svg_html = f"""
    <div style="width:100%; height:240px; background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.03); border-radius:12px; padding:12px; box-sizing:border-box;">
      <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          {"".join(defs_html)}
        </defs>
        
        {grid_lines}
        {x_labels_html}
        
        {"".join(layers_svg)}
      </svg>
    </div>
    """
    
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      {svg_html}
      {legends_container}
    </div>
    """


def _render_scatter_trend(b: dict) -> str:
    title = b.get("title", "")
    data_points = b.get("data_points", [])
    label_x = b.get("label_x", "X Axis")
    label_y = b.get("label_y", "Y Axis")
    
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">
          <div style="font-size:1.15rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px; display:flex; align-items:center; gap:8px;">
            <span style="color:#10b981; font-weight:900;">⬡</span> {title}
          </div>
        </div>
        """
        
    if not data_points:
        return ""
        
    w, h = 520, 240
    pad_l, pad_r, pad_t, pad_b = 55, 25, 30, 45
    chart_w = w - pad_l - pad_r
    chart_h = h - pad_t - pad_b
    
    xs = [float(p[0]) for p in data_points]
    ys = [float(p[1]) for p in data_points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    rng_x = (max_x - min_x) or 1.0
    rng_y = (max_y - min_y) or 1.0
    
    n = len(data_points)
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x*y for x, y in data_points)
    sum_xx = sum(x*x for x in xs)
    
    denom = (n * sum_xx - sum_x * sum_x)
    if denom != 0:
        m = (n * sum_xy - sum_x * sum_y) / denom
        c = (sum_y - m * sum_x) / n
    else:
        m = 0.0
        c = sum_y / n
        
    x1_val = min_x
    y1_val = m * x1_val + c
    x2_val = max_x
    y2_val = m * x2_val + c
    
    x1_proj = pad_l + ((x1_val - min_x) / rng_x) * chart_w
    y1_proj = pad_t + (1 - (y1_val - min_y) / rng_y) * chart_h
    x2_proj = pad_l + ((x2_val - min_x) / rng_x) * chart_w
    y2_proj = pad_t + (1 - (y2_val - min_y) / rng_y) * chart_h
    
    grid_lines = ""
    for grid_idx in range(5):
        grid_y = pad_t + (grid_idx / 4) * chart_h
        grid_v = max_y - (grid_idx / 4) * rng_y
        grid_lines += f"""
        <line x1="{pad_l}" y1="{grid_y}" x2="{pad_l + chart_w}" y2="{grid_y}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="3,3" />
        <text x="{pad_l - 12}" y="{grid_y + 3}" fill="rgba(255,255,255,0.4)" font-size="8.5" font-family="monospace" text-anchor="end">{grid_v:,.1f}</text>
        """
        
    for tick_idx in range(5):
        tick_ratio = tick_idx / 4
        tick_x = pad_l + tick_ratio * chart_w
        tick_v = min_x + tick_ratio * rng_x
        grid_lines += f"""
        <line x1="{tick_x}" y1="{pad_t}" x2="{tick_x}" y2="{pad_t + chart_h}" stroke="rgba(255,255,255,0.03)" stroke-width="1" />
        <text x="{tick_x}" y="{pad_t + chart_h + 16}" fill="rgba(255,255,255,0.4)" font-size="8.5" font-family="monospace" text-anchor="middle">{tick_v:,.1f}</text>
        """
        
    dots_html = []
    for i, (px, py) in enumerate(data_points):
        cx = pad_l + ((px - min_x) / rng_x) * chart_w
        cy = pad_t + (1 - (py - min_y) / rng_y) * chart_h
        dots_html.append(f"""
        <circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5" fill="#10b981" stroke="#fff" stroke-width="1.5" filter="url(#scatter_glow_{id(b)})" style="cursor:pointer;" />
        """)
        
    svg_html = f"""
    <div style="width:100%; height:240px; background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.03); border-radius:12px; padding:12px; box-sizing:border-box;">
      <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <filter id="scatter_glow_{id(b)}" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        
        {grid_lines}
        
        <text x="{pad_l + chart_w / 2.0}" y="{pad_t + chart_h + 34}" fill="rgba(255,255,255,0.5)" font-size="9" font-family="monospace" text-anchor="middle" letter-spacing="0.05em">{label_x.upper()}</text>
        
        <line x1="{x1_proj:.1f}" y1="{y1_proj:.1f}" x2="{x2_proj:.1f}" y2="{y2_proj:.1f}" stroke="#00f2ff" stroke-width="2.5" stroke-dasharray="4,4" filter="url(#scatter_glow_{id(b)})" />
        
        {"".join(dots_html)}
      </svg>
    </div>
    """
    
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      {svg_html}
    </div>
    """


def _render_call_mood_board(b: dict) -> str:
    title = b.get("title", "")
    moods = b.get("moods", [])
    themes = b.get("themes", [])
    summary = b.get("summary", "")
    
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">
          <div style="font-size:1.15rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px; display:flex; align-items:center; gap:8px;">
            <span style="color:#d946ef; font-weight:900;">⬡</span> {title}
          </div>
        </div>
        """
        
    moods_html = []
    for mood in moods:
        name = mood.get("mood", "")
        intensity = mood.get("intensity", 50)
        color = mood.get("color", "#d946ef")
        moods_html.append(f"""
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.04); border-radius:10px; padding:12px; display:flex; flex-direction:column; gap:8px;">
          <div style="display:flex; align-items:center; justify-content:space-between;">
            <span style="font-size:0.85rem; font-weight:700; color:#e2e8f0; display:flex; align-items:center; gap:6px;">
              <span style="width:8px; height:8px; border-radius:50%; background:{color}; box-shadow:0 0 8px {color}; display:inline-block;"></span>
              {name}
            </span>
            <span style="font-size:0.75rem; font-family:monospace; font-weight:800; color:{color};">{intensity}%</span>
          </div>
          <div style="width:100%; height:6px; background:rgba(255,255,255,0.05); border-radius:10px; overflow:hidden;">
            <div style="width:{intensity}%; height:100%; background:linear-gradient(90deg, {color}88, {color}); border-radius:10px; box-shadow:0 0 6px {color}66;"></div>
          </div>
        </div>
        """)
        
    themes_html = []
    for theme in themes:
        term = theme.get("term", "")
        weight = theme.get("weight", 50)
        sentiment = theme.get("sentiment", "neutral").lower()
        
        if sentiment in ["positive", "joy"]:
            bg = "rgba(16,185,129,0.1)"
            border = "rgba(16,185,129,0.2)"
            color_theme = "#10b981"
        elif sentiment in ["concern", "negative", "anxious"]:
            bg = "rgba(239,68,68,0.1)"
            border = "rgba(239,68,68,0.2)"
            color_theme = "#ef4444"
        elif sentiment in ["confused", "curious"]:
            bg = "rgba(245,158,11,0.1)"
            border = "rgba(245,158,11,0.2)"
            color_theme = "#f59e0b"
        else:
            bg = "rgba(56,189,248,0.1)"
            border = "rgba(56,189,248,0.2)"
            color_theme = "#38bdf8"
            
        font_size = 0.75 + (weight / 200.0)
        themes_html.append(f"""
        <span style="display:inline-block; font-size:{font_size:.2f}rem; font-weight:700; color:{color_theme}; background:{bg}; border:1px solid {border}; padding:6px 12px; border-radius:20px; margin:4px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
          {term}
        </span>
        """)
        
    summary_html = ""
    if summary:
        summary_html = f"""
        <div style="margin-top:20px; padding:12px 16px; background:rgba(255,255,255,0.02); border-left:3px solid #d946ef; border-radius:0 8px 8px 0; font-size:0.85rem; line-height:1.6; color:rgba(255,255,255,0.7); font-style:italic;">
          {summary}
        </div>
        """
        
    moods_section = f"""
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:12px; margin-bottom:20px;">
      {"".join(moods_html)}
    </div>
    """ if moods else ""
    
    themes_section = f"""
    <div style="background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.03); border-radius:10px; padding:16px; display:flex; flex-wrap:wrap; align-items:center; justify-content:center;">
      {"".join(themes_html)}
    </div>
    """ if themes else ""
    
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      {moods_section}
      {themes_section}
      {summary_html}
    </div>
    """


def _render_github_activity_grid(b: dict) -> str:
    title = b.get("title", "")
    username = b.get("username", "")
    total = b.get("total_contributions", 342)
    streak = b.get("streak_days", 18)
    activity = b.get("activity", [])
    
    header_html = ""
    if title or username:
        user_badge = f"""
        <div style="display:flex; align-items:center; gap:8px;">
          <span style="font-size:0.75rem; font-family:monospace; color:rgba(255,255,255,0.4); background:rgba(255,255,255,0.04); padding:4px 8px; border-radius:12px; border:1px solid rgba(255,255,255,0.06); display:flex; align-items:center; gap:4px;">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="rgba(255,255,255,0.5)">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
            </svg>
            @{username}
          </span>
        </div>
        """ if username else ""
        
        header_html = f"""
        <div style="margin-bottom:20px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
          <div style="font-size:1.15rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px; display:flex; align-items:center; gap:8px;">
            <span style="color:#26a641; font-weight:900;">⬡</span> {title or "GitHub Contribution Stream"}
          </div>
          {user_badge}
        </div>
        """
        
    cols, rows = 28, 7
    squares = []
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    
    total_cells = cols * rows
    import random
    seed_val = len(username or title or "github")
    
    levels = []
    if activity and len(activity) >= total_cells:
        levels = activity[:total_cells]
    else:
        r_gen = random.Random(seed_val)
        for _ in range(total_cells):
            v = r_gen.choices([0, 1, 2, 3, 4], weights=[50, 20, 15, 10, 5])[0]
            levels.append(v)
            
    square_size = 9
    spacing = 3
    for col in range(cols):
        col_x = col * (square_size + spacing)
        for row in range(rows):
            row_y = row * (square_size + spacing)
            idx = col * rows + row
            lvl = levels[idx] if idx < len(levels) else 0
            color = colors[lvl]
            squares.append(f'<rect x="{col_x}" y="{row_y}" width="{square_size}" height="{square_size}" rx="1.5" fill="{color}" />')
            
    grid_svg = f"""
    <svg viewBox="0 0 {cols * (square_size + spacing) - spacing} {rows * (square_size + spacing) - spacing}" width="100%" height="95" xmlns="http://www.w3.org/2000/svg">
      {"".join(squares)}
    </svg>
    """
    
    stats_html = f"""
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:16px;">
      <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.04); border-radius:10px; padding:10px 16px; flex-grow:1; min-width:100px;">
        <div style="font-size:0.65rem; font-family:monospace; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:2px;">Contributions</div>
        <div style="font-size:1.3rem; font-weight:800; color:#f1f5f9; font-family:monospace; display:flex; align-items:baseline; gap:4px;">
          {total} <span style="font-size:0.75rem; color:#26a641; font-weight:bold;">YTD</span>
        </div>
      </div>
      <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.04); border-radius:10px; padding:10px 16px; flex-grow:1; min-width:100px;">
        <div style="font-size:0.65rem; font-family:monospace; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:2px;">Active Streak</div>
        <div style="font-size:1.3rem; font-weight:800; color:#f1f5f9; font-family:monospace; display:flex; align-items:baseline; gap:4px;">
          {streak} <span style="font-size:0.75rem; color:#39d353; font-weight:bold;">days 🔥</span>
        </div>
      </div>
    </div>
    """
    
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      {stats_html}
      <div style="background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.03); border-radius:10px; padding:16px; box-sizing:border-box; display:flex; align-items:center; justify-content:center;">
        <div style="width:100%; max-width:350px;">
          {grid_svg}
        </div>
      </div>
    </div>
    """


# ── OpenUI atoms (sourced from github.com/thesysdev/openui, MIT) ─────────────

def _form_field_html(field: dict) -> str:
    """Render one field inside a form."""
    ftype       = field.get("type", "text")
    label       = field.get("label", "")
    name        = field.get("name", "")
    placeholder = field.get("placeholder", "")
    rules       = field.get("rules", [])
    required    = "required" in rules

    req_star = '<span style="color:#ea4335;margin-left:2px;">*</span>' if required else ""
    label_html = (
        f'<label for="{name}" style="display:block;font-size:0.83rem;font-weight:600;'
        f'color:#3c4043;margin-bottom:5px;">{label}{req_star}</label>'
    )
    input_style = (
        "width:100%;padding:9px 12px;border:1px solid #dadce0;border-radius:6px;"
        "font-size:0.9rem;color:#3c4043;background:#fff;box-sizing:border-box;"
        "font-family:inherit;outline:none;"
    )
    if ftype == "textarea":
        ctrl = (f'<textarea id="{name}" name="{name}" placeholder="{placeholder}" '
                f'style="{input_style}height:88px;resize:vertical;" '
                f'{"required" if required else ""}></textarea>')
    elif ftype == "select":
        opts = f'<option value="">{placeholder or "Select…"}</option>' + "".join(
            f'<option value="{o["value"]}">{o["label"]}</option>'
            for o in field.get("options", [])
        )
        ctrl = (f'<select id="{name}" name="{name}" style="{input_style}" '
                f'{"required" if required else ""}>{opts}</select>')
    else:
        ctrl = (f'<input id="{name}" type="{ftype}" name="{name}" '
                f'placeholder="{placeholder}" style="{input_style}" '
                f'{"required" if required else ""}>')

    return f'<div style="display:flex;flex-direction:column;">{label_html}{ctrl}</div>'


def _render_form(b: dict) -> str:
    """Full form — field list with typed inputs, validation hints, submit/cancel."""
    title        = b.get("title", "")
    description  = b.get("description", "")
    fields       = b.get("fields", [])
    submit_label = b.get("submit_label", "Submit")
    cancel_label = b.get("cancel_label", "")

    title_html = (
        f'<div style="font-size:1.0rem;font-weight:700;color:#1a1a2e;margin-bottom:4px;">{title}</div>'
        if title else ""
    )
    desc_html = (
        f'<p style="font-size:0.85rem;color:#5f6368;margin-bottom:16px;">{_md_inline(description)}</p>'
        if description else ""
    )
    fields_html = "".join(_form_field_html(f) for f in fields)

    cancel_btn = (
        f'<button type="button" style="padding:9px 20px;border-radius:6px;border:1px solid #dadce0;'
        f'background:#fff;color:#3c4043;font-size:0.88rem;font-weight:500;cursor:pointer;">'
        f'{cancel_label}</button>'
    ) if cancel_label else ""

    return (
        f'<div style="border:1px solid #e0e0e0;border-radius:10px;padding:24px;margin:1.5rem 0;background:#fff;">'
        f'{title_html}{desc_html}'
        f'<div style="display:flex;flex-direction:column;gap:14px;">'
        f'{fields_html}'
        f'<div style="display:flex;gap:10px;justify-content:flex-end;padding-top:6px;">'
        f'{cancel_btn}'
        f'<button type="button" style="padding:9px 24px;border-radius:6px;border:none;'
        f'background:#1a73e8;color:#fff;font-size:0.88rem;font-weight:600;cursor:pointer;">'
        f'{submit_label}</button>'
        f'</div></div></div>'
    )


def _render_form_input(b: dict) -> str:
    """Standalone labeled text input."""
    label       = b.get("label", "")
    name        = b.get("name", "")
    ftype       = b.get("type", "text")
    placeholder = b.get("placeholder", "")
    value       = b.get("value", "")
    rules       = b.get("rules", [])
    required    = "required" in rules
    req_star = '<span style="color:#ea4335;margin-left:2px;">*</span>' if required else ""
    return (
        f'<div style="margin:1rem 0;">'
        f'<label for="{name}" style="display:block;font-size:0.83rem;font-weight:600;'
        f'color:#3c4043;margin-bottom:5px;">{label}{req_star}</label>'
        f'<input id="{name}" type="{ftype}" name="{name}" placeholder="{placeholder}" '
        f'value="{value}" style="width:100%;padding:9px 12px;border:1px solid #dadce0;'
        f'border-radius:6px;font-size:0.9rem;color:#3c4043;box-sizing:border-box;" '
        f'{"required" if required else ""}>'
        f'</div>'
    )


def _render_form_select(b: dict) -> str:
    """Standalone labeled select dropdown."""
    label       = b.get("label", "")
    name        = b.get("name", "")
    placeholder = b.get("placeholder", "")
    options     = b.get("options", [])
    rules       = b.get("rules", [])
    required    = "required" in rules
    req_star = '<span style="color:#ea4335;margin-left:2px;">*</span>' if required else ""
    opts = f'<option value="">{placeholder or "Select…"}</option>' + "".join(
        f'<option value="{o["value"]}">{o["label"]}</option>' for o in options
    )
    return (
        f'<div style="margin:1rem 0;">'
        f'<label for="{name}" style="display:block;font-size:0.83rem;font-weight:600;'
        f'color:#3c4043;margin-bottom:5px;">{label}{req_star}</label>'
        f'<select id="{name}" name="{name}" style="width:100%;padding:9px 12px;'
        f'border:1px solid #dadce0;border-radius:6px;font-size:0.9rem;color:#3c4043;'
        f'background:#fff;box-sizing:border-box;" {"required" if required else ""}>'
        f'{opts}</select>'
        f'</div>'
    )


def _render_form_radio_group(b: dict) -> str:
    """Group of radio buttons — single selection."""
    label         = b.get("label", "")
    name          = b.get("name", "")
    options       = b.get("options", [])
    default_value = b.get("default_value", "")

    items_html = ""
    for opt in options:
        val     = opt.get("value", "")
        lbl     = opt.get("label", "")
        desc    = opt.get("description", "")
        checked = "checked" if val == default_value else ""
        desc_html = f'<span style="font-size:0.78rem;color:#5f6368;margin-top:1px;">{desc}</span>' if desc else ""
        items_html += (
            f'<label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;'
            f'padding:10px 12px;border:1px solid #dadce0;border-radius:8px;background:#fff;">'
            f'<input type="radio" name="{name}" value="{val}" {checked} '
            f'style="margin-top:3px;accent-color:#1a73e8;flex-shrink:0;">'
            f'<span style="display:flex;flex-direction:column;">'
            f'<span style="font-size:0.88rem;font-weight:600;color:#3c4043;">{lbl}</span>'
            f'{desc_html}</span></label>'
        )

    return (
        f'<div style="margin:1rem 0;">'
        f'<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:8px;">{label}</div>'
        f'<div style="display:flex;flex-direction:column;gap:6px;">{items_html}</div>'
        f'</div>'
    )


def _render_form_checkbox_group(b: dict) -> str:
    """Group of checkboxes — multi-selection."""
    label   = b.get("label", "")
    name    = b.get("name", "")
    options = b.get("options", [])

    items_html = ""
    for opt in options:
        oname   = opt.get("name", "")
        lbl     = opt.get("label", "")
        desc    = opt.get("description", "")
        checked = "checked" if opt.get("default_checked") else ""
        desc_html = f'<span style="font-size:0.78rem;color:#5f6368;margin-top:1px;">{desc}</span>' if desc else ""
        items_html += (
            f'<label style="display:flex;align-items:flex-start;gap:10px;cursor:pointer;'
            f'padding:10px 12px;border:1px solid #dadce0;border-radius:8px;background:#fff;">'
            f'<input type="checkbox" name="{name}[{oname}]" {checked} '
            f'style="margin-top:3px;accent-color:#1a73e8;flex-shrink:0;">'
            f'<span style="display:flex;flex-direction:column;">'
            f'<span style="font-size:0.88rem;font-weight:600;color:#3c4043;">{lbl}</span>'
            f'{desc_html}</span></label>'
        )

    return (
        f'<div style="margin:1rem 0;">'
        f'<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:8px;">{label}</div>'
        f'<div style="display:flex;flex-direction:column;gap:6px;">{items_html}</div>'
        f'</div>'
    )


def _render_form_switch_group(b: dict) -> str:
    """Toggle switches with labels and optional descriptions — CSS-only."""
    import hashlib
    label = b.get("label", "")
    name  = b.get("name", "")
    items = b.get("items", [])

    label_html = (
        f'<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:8px;">{label}</div>'
        if label else ""
    )

    rows = ""
    for item in items:
        iname   = item.get("name", "")
        ilabel  = item.get("label", "")
        idesc   = item.get("description", "")
        checked = item.get("default_checked", False)
        sid     = "sw_" + hashlib.md5(f"{name}_{iname}".encode()).hexdigest()[:6]
        desc_html = f'<span style="font-size:0.78rem;color:#5f6368;">{idesc}</span>' if idesc else ""
        rows += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;'
            f'padding:12px 14px;border-bottom:1px solid #f0f0f0;">'
            f'<div style="display:flex;flex-direction:column;gap:2px;">'
            f'<span style="font-size:0.88rem;font-weight:600;color:#3c4043;">{ilabel}</span>'
            f'{desc_html}</div>'
            # CSS-only toggle: hidden checkbox + styled label
            f'<input type="checkbox" id="{sid}" name="{name}[{iname}]" '
            f'{"checked" if checked else ""} style="display:none;">'
            f'<label for="{sid}" style="position:relative;display:inline-block;'
            f'width:42px;height:24px;flex-shrink:0;cursor:pointer;">'
            f'<span style="position:absolute;inset:0;border-radius:12px;'
            f'background:{"#1a73e8" if checked else "#dadce0"};transition:background 0.2s;"></span>'
            f'<span style="position:absolute;top:3px;left:{"21px" if checked else "3px"};'
            f'width:18px;height:18px;border-radius:50%;background:#fff;'
            f'box-shadow:0 1px 4px rgba(0,0,0,0.2);transition:left 0.2s;"></span>'
            f'</label>'
            f'</div>'
        )

    header = (
        '<div style="padding:12px 14px;border-bottom:1px solid #e0e0e0;">' + label_html + '</div>'
        if label else ""
    )
    return (
        f'<div style="margin:1rem 0;border:1px solid #e0e0e0;border-radius:10px;overflow:hidden;background:#fff;">'
        f'{header}'
        f'{rows}'
        f'</div>'
    )


def _render_form_slider(b: dict) -> str:
    """Range slider — native <input type=range> so the thumb is actually draggable."""
    import hashlib
    label = b.get("label", "")
    name  = b.get("name", "")
    mn    = b.get("min", 0)
    mx    = b.get("max", 100)
    step  = b.get("step", 1)
    val   = b.get("value", mn)
    unit  = b.get("unit", "")
    sid   = "sl_" + hashlib.md5(name.encode()).hexdigest()[:6]
    unit_str = f" {unit}" if unit else ""

    return (
        f'<style>'
        f'#{sid}{{-webkit-appearance:none;appearance:none;width:100%;height:6px;'
        f'border-radius:3px;background:linear-gradient(to right,#1a73e8 0%,'
        f'#1a73e8 {int((val-mn)/max(mx-mn,1)*100)}%,'
        f'#e0e0e0 {int((val-mn)/max(mx-mn,1)*100)}%,#e0e0e0 100%);'
        f'outline:none;cursor:pointer;}}'
        f'#{sid}::-webkit-slider-thumb{{-webkit-appearance:none;appearance:none;'
        f'width:18px;height:18px;border-radius:50%;background:#1a73e8;'
        f'border:2px solid #fff;box-shadow:0 1px 4px rgba(26,115,232,0.5);cursor:pointer;}}'
        f'#{sid}::-moz-range-thumb{{width:18px;height:18px;border-radius:50%;'
        f'background:#1a73e8;border:2px solid #fff;cursor:pointer;box-sizing:border-box;}}'
        f'</style>'
        f'<div style="margin:1rem 0;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
        f'<label for="{sid}" style="font-size:0.83rem;font-weight:600;color:#3c4043;">{label}</label>'
        f'<span style="font-size:0.88rem;font-weight:700;color:#1a73e8;">{val}{unit_str}</span>'
        f'</div>'
        f'<input id="{sid}" type="range" name="{name}" min="{mn}" max="{mx}" step="{step}" value="{val}" '
        f'style="width:100%;margin:0;">'
        f'<div style="display:flex;justify-content:space-between;margin-top:6px;">'
        f'<span style="font-size:0.75rem;color:#9aa0a6;">{mn}{unit_str}</span>'
        f'<span style="font-size:0.75rem;color:#9aa0a6;">{mx}{unit_str}</span>'
        f'</div>'
        f'</div>'
    )


def _render_form_date_picker(b: dict) -> str:
    """Date input — single date or date-range display."""
    label = b.get("label", "")
    name  = b.get("name", "")
    mode  = b.get("mode", "single")
    value = b.get("value", "")
    mn    = b.get("min", "")
    mx    = b.get("max", "")
    rules = b.get("rules", [])
    required = "required" in rules
    req_star = '<span style="color:#ea4335;margin-left:2px;">*</span>' if required else ""

    if mode == "range":
        ctrl = (
            f'<div style="display:flex;gap:10px;">'
            f'<div style="flex:1;">'
            f'<label style="display:block;font-size:0.75rem;color:#5f6368;margin-bottom:3px;">From</label>'
            f'<input type="date" name="{name}_from" min="{mn}" max="{mx}" '
            f'style="width:100%;padding:9px 12px;border:1px solid #dadce0;border-radius:6px;'
            f'font-size:0.88rem;color:#3c4043;box-sizing:border-box;"></div>'
            f'<div style="flex:1;">'
            f'<label style="display:block;font-size:0.75rem;color:#5f6368;margin-bottom:3px;">To</label>'
            f'<input type="date" name="{name}_to" min="{mn}" max="{mx}" '
            f'style="width:100%;padding:9px 12px;border:1px solid #dadce0;border-radius:6px;'
            f'font-size:0.88rem;color:#3c4043;box-sizing:border-box;"></div>'
            f'</div>'
        )
    else:
        ctrl = (
            f'<input id="{name}" type="date" name="{name}" value="{value}" '
            f'min="{mn}" max="{mx}" '
            f'style="width:100%;padding:9px 12px;border:1px solid #dadce0;border-radius:6px;'
            f'font-size:0.9rem;color:#3c4043;box-sizing:border-box;" '
            f'{"required" if required else ""}>'
        )

    return (
        f'<div style="margin:1rem 0;">'
        f'<label for="{name}" style="display:block;font-size:0.83rem;font-weight:600;'
        f'color:#3c4043;margin-bottom:5px;">{label}{req_star}</label>'
        f'{ctrl}'
        f'</div>'
    )


def _render_modal(b: dict) -> str:
    """CSS-only modal — checkbox trigger, title, optional blocks, confirm/cancel buttons.

    Source: OpenUI/Thesys standard library (MIT), adapted for A2UI.
    """
    import hashlib
    title         = b.get("title", "")
    description   = b.get("description", "")
    trigger_label = b.get("trigger_label", "Open")
    confirm_label = b.get("confirm_label", "Confirm")
    cancel_label  = b.get("cancel_label", "Cancel")
    blocks        = b.get("blocks", [])
    mid           = "m_" + hashlib.md5(title.encode()).hexdigest()[:6]

    inner_html = ""
    for block in blocks:
        btype = block.get("component") or block.get("type")
        fn = _RENDERERS.get(btype)
        inner_html += fn(block) if fn else f'<p>{block}</p>'

    desc_html = f'<p style="font-size:0.88rem;color:#94a3b8;margin:4px 0 16px;">{_md_inline(description)}</p>' if description else ""

    return (
        f'<div style="margin:1rem 0;">'
        # CSS: hide backdrop by default; show when checkbox checked.
        # !important needed to beat the inline display:none that srcdoc would otherwise cache.
        f'<style>'
        f'#{mid}{{display:none;}}'
        f'.{mid}-bd{{display:none;position:fixed;inset:0;z-index:9000;'
        f'align-items:center;justify-content:center;background:rgba(0,0,0,0.45);}}'
        f'#{mid}:checked~.{mid}-bd{{display:flex!important;}}'
        f'</style>'
        # Trigger button
        f'<label for="{mid}" style="display:inline-block;padding:9px 22px;border-radius:6px;'
        f'background:#1a73e8;color:#fff;font-size:0.88rem;font-weight:600;cursor:pointer;">'
        f'{trigger_label}</label>'
        f'<input type="checkbox" id="{mid}">'
        # Backdrop + dialog
        f'<div class="{mid}-bd">'
        f'<div style="background:#1e293b;border-radius:12px;padding:28px 28px 20px;'
        f'max-width:480px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.5);">'
        f'<div style="font-size:1.0rem;font-weight:700;color:#f1f5f9;margin-bottom:4px;">{title}</div>'
        f'{desc_html}'
        f'{inner_html}'
        f'<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:20px;">'
        f'<label for="{mid}" style="padding:9px 20px;border-radius:6px;'
        f'border:1px solid rgba(255,255,255,0.15);'
        f'background:rgba(255,255,255,0.06);color:#e2e8f0;font-size:0.88rem;font-weight:500;cursor:pointer;">'
        f'{cancel_label}</label>'
        f'<label for="{mid}" style="padding:9px 22px;border-radius:6px;border:none;'
        f'background:#3b82f6;color:#fff;font-size:0.88rem;font-weight:600;cursor:pointer;">'
        f'{confirm_label}</label>'
        f'</div></div></div>'
        f'</div>'
    )


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert a #rrggbb hex color + alpha float to rgba(r,g,b,a)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return hex_color


def _render_follow_up_chips(b: dict) -> str:
    """Conversation follow-up suggestion chips — styled pill buttons.

    Source: OpenUI/Thesys FollowUpBlock (MIT), adapted for A2UI.
    On meet-stage: renders as static styled buttons (CSP blocks click handlers).
    """
    items  = b.get("items", [])
    label  = b.get("label", "")
    accent = b.get("accent", "#1a73e8")

    bg     = _hex_to_rgba(accent, 0.12)
    border = _hex_to_rgba(accent, 0.45)

    label_html = (
        f'<div style="font-size:0.75rem;font-weight:600;color:#9aa0a6;'
        f'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">{label}</div>'
    ) if label else ""

    chips = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;padding:8px 14px;'
        f'border-radius:100px;border:1px solid {border};background:{bg};'
        f'color:{accent};font-size:0.85rem;font-weight:500;cursor:pointer;white-space:nowrap;">'
        f'{item}'
        f'<svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M2 5h6M5.5 2l3 3-3 3"/>'
        f'</svg>'
        f'</span>'
        for item in items
    )

    return (
        f'<div style="margin:1rem 0;">'
        f'{label_html}'
        f'<div style="display:flex;flex-wrap:wrap;gap:8px;">{chips}</div>'
        f'</div>'
    )


def _render_choicebox_group(b: dict) -> str:
    """Card-style option selector. Each card wraps a hidden input — entire card is clickable.

    CSS :has(input:checked) highlights the selected card.
    Inspired by Vercel Geist Choicebox pattern.
    """
    import hashlib
    gid      = "cbg_" + hashlib.md5(b.get("name", "cb").encode()).hexdigest()[:6]
    label    = b.get("label", "")
    name     = b.get("name", "choice")
    multiple = b.get("multiple", False)
    accent   = b.get("accent", "#1a73e8")
    items    = b.get("items", [])
    submit_label = b.get("submit_label", "")

    bg_sel     = _hex_to_rgba(accent, 0.06)
    border_sel = _hex_to_rgba(accent, 0.70)
    input_type = "checkbox" if multiple else "radio"

    label_html = (
        f'<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:10px;">{label}</div>'
    ) if label else ""

    cards = ""
    for item in items:
        val      = item.get("value", "")
        title    = item.get("title", "")
        desc     = item.get("description", "")
        icon     = item.get("icon", "")
        disabled = item.get("disabled", False)
        iid      = f"{gid}_{hashlib.md5(val.encode()).hexdigest()[:4]}"
        icon_html = (
            f'<span style="font-size:1.6rem;line-height:1;margin-bottom:4px;">{icon}</span>'
        ) if icon else ""
        desc_html = (
            f'<span style="font-size:0.78rem;color:#5f6368;margin-top:2px;">{desc}</span>'
        ) if desc else ""
        opacity  = "opacity:0.45;" if disabled else ""
        cursor   = "default" if disabled else "pointer"
        dis_attr = "disabled" if disabled else ""
        cards += (
            f'<label for="{iid}" class="{gid}-card" '
            f'style="display:flex;flex-direction:column;gap:6px;padding:14px 16px;'
            f'border:1.5px solid #dadce0;border-radius:10px;cursor:{cursor};'
            f'background:#fff;{opacity}">'
            f'<input type="{input_type}" id="{iid}" name="{name}" value="{val}" {dis_attr} '
            f'style="display:none;">'
            f'{icon_html}'
            f'<span style="font-size:0.9rem;font-weight:600;color:#3c4043;">{title}</span>'
            f'{desc_html}'
            f'</label>'
        )

    submit_html = (
        f'<button type="submit" style="margin-top:12px;padding:9px 22px;border-radius:6px;'
        f'border:none;background:{accent};color:#fff;font-size:0.88rem;font-weight:600;'
        f'cursor:pointer;">{submit_label}</button>'
    ) if submit_label else ""

    return (
        f'<div style="margin:1rem 0;">'
        f'<style>'
        f'.{gid}-card{{transition:border-color 0.15s,background 0.15s;}}'
        f'.{gid}-card:has(input:checked){{border-color:{border_sel}!important;background:{bg_sel}!important;}}'
        f'.{gid}-card:not(:has(input[disabled])):hover{{border-color:rgba(0,0,0,0.28)!important;}}'
        f'</style>'
        f'{label_html}'
        f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;">'
        f'{cards}'
        f'</div>'
        f'{submit_html}'
        f'</div>'
    )


def _render_feedback_prompt(b: dict) -> str:
    """In-context feedback widget — thumbs up/down or 1–5 stars, CSS-only.

    Inspired by Vercel Geist Feedback pattern.
    thumbs: two pill buttons, :has(input:checked) highlights selection.
    stars: classic CSS row-reverse trick; input:checked ~ label fills preceding stars.
    """
    import hashlib
    fid         = "fp_" + hashlib.md5(b.get("question", "feedback").encode()).hexdigest()[:6]
    question    = b.get("question", "Was this helpful?")
    style       = b.get("style", "thumbs")
    placeholder = b.get("placeholder", "")
    action_url  = b.get("action_url", "")

    wrap_open  = f'<form action="{action_url}" method="post">' if action_url else ""
    wrap_close = "</form>" if action_url else ""

    q_html = (
        f'<div style="font-size:0.88rem;font-weight:500;color:#3c4043;margin-bottom:10px;">'
        f'{question}</div>'
    ) if question else ""

    if style == "stars":
        star_inputs = "".join(
            f'<input type="radio" id="{fid}_s{i}" name="{fid}_rating" value="{i}" style="display:none;">'
            f'<label for="{fid}_s{i}" title="{i} star{"s" if i>1 else ""}">★</label>'
            for i in range(5, 0, -1)
        )
        widget_html = (
            f'<style>'
            f'.{fid}-stars{{display:flex;flex-direction:row-reverse;gap:3px;}}'
            f'.{fid}-stars label{{font-size:1.7rem;color:#dadce0;cursor:pointer;line-height:1;transition:color 0.1s;}}'
            f'.{fid}-stars input:checked~label,'
            f'.{fid}-stars label:hover~label,'
            f'.{fid}-stars label:hover{{color:#f59e0b;}}'
            f'</style>'
            f'<div class="{fid}-stars">{star_inputs}</div>'
        )
    else:
        widget_html = (
            f'<style>'
            f'.{fid}-up:has(input:checked){{border-color:#1a73e8!important;'
            f'background:rgba(26,115,232,0.08)!important;color:#1a73e8!important;}}'
            f'.{fid}-dn:has(input:checked){{border-color:#ea4335!important;'
            f'background:rgba(234,67,53,0.08)!important;color:#ea4335!important;}}'
            f'</style>'
            f'<div style="display:flex;gap:8px;">'
            f'<label class="{fid}-up" style="display:inline-flex;align-items:center;gap:6px;'
            f'padding:8px 16px;border:1.5px solid #dadce0;border-radius:100px;cursor:pointer;'
            f'font-size:0.88rem;font-weight:500;color:#3c4043;background:#fff;">'
            f'<input type="radio" name="{fid}_rating" value="up" style="display:none;">👍 Yes</label>'
            f'<label class="{fid}-dn" style="display:inline-flex;align-items:center;gap:6px;'
            f'padding:8px 16px;border:1.5px solid #dadce0;border-radius:100px;cursor:pointer;'
            f'font-size:0.88rem;font-weight:500;color:#3c4043;background:#fff;">'
            f'<input type="radio" name="{fid}_rating" value="down" style="display:none;">👎 No</label>'
            f'</div>'
        )

    text_html = (
        f'<textarea name="{fid}_comment" placeholder="{placeholder}" '
        f'style="display:block;margin-top:10px;width:100%;box-sizing:border-box;padding:8px 10px;'
        f'border:1px solid #dadce0;border-radius:6px;font-size:0.85rem;color:#3c4043;'
        f'resize:vertical;min-height:64px;background:#fff;"></textarea>'
    ) if placeholder else ""

    submit_html = (
        f'<button type="submit" style="margin-top:8px;padding:7px 18px;border-radius:6px;'
        f'border:none;background:#1a73e8;color:#fff;font-size:0.85rem;font-weight:600;cursor:pointer;">'
        f'Submit</button>'
    ) if action_url else ""

    return (
        f'{wrap_open}'
        f'<div style="margin:1rem 0;padding:16px 18px;border:1px solid #e0e0e0;'
        f'border-radius:10px;background:#fff;">'
        f'{q_html}'
        f'{widget_html}'
        f'{text_html}'
        f'{submit_html}'
        f'</div>'
        f'{wrap_close}'
    )


# ── Aceternity UI-inspired atoms ──────────────────────────────────────────────

def _render_marquee_strip(b: dict) -> str:
    import hashlib
    mid      = "mq_" + hashlib.md5(str(b.get("items", "")).encode()).hexdigest()[:6]
    items    = b.get("items", [])
    speed    = b.get("speed", "normal")
    direction = b.get("direction", "left")
    pause    = b.get("pause_on_hover", True)
    label    = b.get("label", "")
    gap      = b.get("gap", "40px")

    durations = {"slow": "40s", "normal": "25s", "fast": "12s"}
    dur = durations.get(speed, "25s")
    anim_dir = "normal" if direction == "left" else "reverse"
    pause_css = f".{mid}-track:hover{{animation-play-state:paused!important;}}" if pause else ""

    def _item_html(item):
        if isinstance(item, dict):
            img = item.get("image_url", "")
            text = item.get("text", "")
            img_html = (
                f'<img src="{img}" alt="{text}" '
                f'style="height:28px;object-fit:contain;vertical-align:middle;opacity:0.75;">'
            ) if img else ""
            return (
                f'<span style="display:inline-flex;align-items:center;gap:8px;'
                f'white-space:nowrap;font-size:0.9rem;color:#5f6368;font-weight:500;">'
                f'{img_html}{text}</span>'
            )
        return (
            f'<span style="display:inline-block;white-space:nowrap;'
            f'font-size:0.9rem;color:#5f6368;font-weight:500;">{item}</span>'
        )

    items_content = "".join(_item_html(it) for it in items)
    # duplicate the full set for a seamless loop
    track_content = (
        f'<span style="display:inline-flex;align-items:center;gap:{gap};padding-right:{gap};">'
        f'{items_content}</span>'
        f'<span aria-hidden="true" style="display:inline-flex;align-items:center;gap:{gap};padding-right:{gap};">'
        f'{items_content}</span>'
    )

    label_html = (
        f'<div style="font-size:0.75rem;font-weight:600;color:#9ca3af;'
        f'letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;">'
        f'{label}</div>'
    ) if label else ""

    return (
        f'<style>'
        f'@keyframes {mid}-scroll{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}'
        f'.{mid}-track{{display:flex;animation:{mid}-scroll {dur} linear infinite;'
        f'animation-direction:{anim_dir};will-change:transform;}}'
        f'{pause_css}'
        f'</style>'
        f'<div style="margin:1rem 0;overflow:hidden;padding:12px 0;'
        f'border-top:1px solid #f0f0f0;border-bottom:1px solid #f0f0f0;">'
        f'{label_html}'
        f'<div class="{mid}-track">{track_content}</div>'
        f'</div>'
    )


def _render_typewriter_text(b: dict) -> str:
    import hashlib
    tid     = "tw_" + hashlib.md5(b.get("text", "type").encode()).hexdigest()[:6]
    text    = b.get("text", "")
    size    = b.get("size", "28px")
    weight  = b.get("weight", "700")
    color   = b.get("color", "#1a1a1a")
    speed   = b.get("speed", "normal")
    cursor  = b.get("cursor", True)
    delay   = b.get("delay", "0s")

    chars = len(text)
    durations = {"slow": f"{chars * 0.12:.1f}s", "normal": f"{chars * 0.07:.1f}s",
                 "fast": f"{chars * 0.04:.1f}s"}
    dur = durations.get(speed, f"{chars * 0.07:.1f}s")

    cursor_css = (
        f'.{tid}::after{{content:"|";animation:{tid}-blink 0.75s step-end infinite;'
        f'color:{color};margin-left:2px;}}'
        f'@keyframes {tid}-blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}'
    ) if cursor else ""

    return (
        f'<style>'
        f'.{tid}{{display:inline-block;overflow:hidden;white-space:nowrap;'
        f'width:0;animation:{tid}-type {dur} steps({chars},end) forwards;'
        f'animation-delay:{delay};}}'
        f'@keyframes {tid}-type{{to{{width:{chars}ch}}}}'
        f'{cursor_css}'
        f'</style>'
        f'<div style="margin:1rem 0;font-size:{size};font-weight:{weight};'
        f'color:{color};line-height:1.2;font-family:monospace;">'
        f'<span class="{tid}">{text}</span>'
        f'</div>'
    )


def _render_animated_border_card(b: dict) -> str:
    import hashlib
    cid     = "abc_" + hashlib.md5((b.get("title", "") + b.get("body", "")).encode()).hexdigest()[:6]
    title   = b.get("title", "")
    body    = b.get("body", "")
    accent  = b.get("accent", "#38bdf8")
    accent2 = b.get("accent2", "#818cf8")
    bg      = b.get("background", "#ffffff")
    speed   = b.get("speed", "normal")
    bw      = int(b.get("border_width", 2))

    durations = {"slow": "4s", "normal": "2.5s", "fast": "1.2s"}
    dur = durations.get(speed, "2.5s")
    pad = bw + 1  # inner card inset

    title_html = (
        f'<div style="font-size:1rem;font-weight:700;color:#202124;margin-bottom:8px;">'
        f'{title}</div>'
    ) if title else ""

    body_html = _md_inline(body) if body else ""

    return (
        f'<style>'
        f'.{cid}-wrap{{position:relative;border-radius:12px;padding:{pad}px;'
        f'overflow:hidden;background:{bg};margin:1rem 0;}}'
        f'.{cid}-wrap::before{{content:"";position:absolute;inset:-100%;'
        f'width:300%;height:300%;'
        f'background:conic-gradient(from 0deg,transparent 0deg,{accent} 60deg,'
        f'{accent2} 120deg,transparent 180deg);'
        f'animation:{cid}-spin {dur} linear infinite;z-index:0;}}'
        f'.{cid}-inner{{position:relative;z-index:1;background:{bg};'
        f'border-radius:{12 - pad}px;padding:20px 22px;}}'
        f'@keyframes {cid}-spin{{to{{transform:rotate(360deg)}}}}'
        f'</style>'
        f'<div class="{cid}-wrap">'
        f'<div class="{cid}-inner">'
        f'{title_html}'
        f'<div style="font-size:0.92rem;color:#3c4043;line-height:1.6;">{body_html}</div>'
        f'</div>'
        f'</div>'
    )


def _render_aurora_background(b: dict) -> str:
    import hashlib
    aid    = "au_" + hashlib.md5(str(b.get("colors", "")).encode()).hexdigest()[:6]
    colors = b.get("colors", ["#38bdf8", "#818cf8", "#34d399"])
    speed  = b.get("speed", "slow")
    title  = b.get("title", "")
    body   = b.get("body", "")
    opacity   = b.get("opacity", 0.5)
    background = b.get("background", "#0a0f1d")

    d1, d2, d3 = {"slow": ("14s","18s","11s"), "normal": ("7s","10s","6s"),
                  "fast": ("3s","5s","3s")}.get(speed, ("14s","18s","11s"))
    c1 = colors[0] if len(colors) > 0 else "#38bdf8"
    c2 = colors[1] if len(colors) > 1 else "#818cf8"
    c3 = colors[2] if len(colors) > 2 else "#34d399"

    title_html = (
        f'<div style="font-size:1.1rem;font-weight:700;color:#f1f5f9;margin-bottom:8px;">'
        f'{title}</div>'
    ) if title else ""
    body_html = (
        f'<div style="font-size:0.9rem;color:#94a3b8;line-height:1.65;">'
        f'{_md_inline(body)}</div>'
    ) if body else ""

    return (
        f'<style>'
        f'.{aid}{{position:relative;border-radius:16px;overflow:hidden;'
        f'background:{background};padding:40px 36px;margin:1rem 0;min-height:120px;}}'
        f'.{aid}-blobs{{position:absolute;inset:0;overflow:hidden;opacity:{opacity};}}'
        f'.{aid}-b1{{position:absolute;top:-20%;left:-10%;width:60%;height:80%;'
        f'background:radial-gradient(ellipse at center,{c1} 0%,transparent 70%);'
        f'animation:{aid}-b1 {d1} ease-in-out infinite;}}'
        f'.{aid}-b2{{position:absolute;top:10%;right:-15%;width:70%;height:70%;'
        f'background:radial-gradient(ellipse at center,{c2} 0%,transparent 70%);'
        f'animation:{aid}-b2 {d2} ease-in-out infinite;}}'
        f'.{aid}-b3{{position:absolute;bottom:-20%;left:30%;width:50%;height:60%;'
        f'background:radial-gradient(ellipse at center,{c3} 0%,transparent 70%);'
        f'animation:{aid}-b3 {d3} ease-in-out infinite;}}'
        f'.{aid}-content{{position:relative;z-index:1;}}'
        f'@keyframes {aid}-b1{{0%,100%{{transform:translate(0,0) scale(1)}}'
        f'50%{{transform:translate(25%,-15%) scale(1.2)}}}}'
        f'@keyframes {aid}-b2{{0%,100%{{transform:translate(0,0) scale(1.1)}}'
        f'50%{{transform:translate(-20%,25%) scale(0.85)}}}}'
        f'@keyframes {aid}-b3{{0%,100%{{transform:translate(0,0)}}'
        f'50%{{transform:translate(-15%,-20%) scale(1.1)}}}}'
        f'</style>'
        f'<div class="{aid}">'
        f'<div class="{aid}-blobs">'
        f'<div class="{aid}-b1"></div>'
        f'<div class="{aid}-b2"></div>'
        f'<div class="{aid}-b3"></div>'
        f'</div>'
        f'<div class="{aid}-content">{title_html}{body_html}</div>'
        f'</div>'
    )


def _render_dot_grid_background(b: dict) -> str:
    import hashlib
    did      = "dg_" + hashlib.md5(str(b.get("variant","dots")).encode()).hexdigest()[:6]
    variant  = b.get("variant", "dots")
    title    = b.get("title", "")
    body     = b.get("body", "")
    dot_color = b.get("dot_color", "rgba(148,163,184,0.35)")
    background = b.get("background", "#0d1525")
    spacing  = int(b.get("spacing", 24))
    dot_size = b.get("dot_size", 1)

    if variant == "grid":
        pattern = (f'linear-gradient({dot_color} 1px,transparent 1px),'
                   f'linear-gradient(90deg,{dot_color} 1px,transparent 1px)')
    elif variant == "cross":
        # thick "+" markers at each intersection
        pattern = (f'linear-gradient({dot_color} 1px,transparent 1px),'
                   f'linear-gradient(90deg,{dot_color} 1px,transparent 1px)')
    else:  # dots
        pattern = f'radial-gradient(circle,{dot_color} {dot_size}px,transparent {dot_size}px)'

    title_html = (
        f'<div style="font-size:1rem;font-weight:700;color:#f1f5f9;margin-bottom:8px;">'
        f'{title}</div>'
    ) if title else ""
    body_html = (
        f'<div style="font-size:0.9rem;color:#94a3b8;line-height:1.65;">'
        f'{_md_inline(body)}</div>'
    ) if body else ""

    return (
        f'<div style="margin:1rem 0;border-radius:12px;overflow:hidden;padding:36px;'
        f'background-color:{background};background-image:{pattern};'
        f'background-size:{spacing}px {spacing}px;">'
        f'{title_html}{body_html}'
        f'</div>'
    )


def _render_shimmer_button(b: dict) -> str:
    import hashlib
    sid    = "sb_" + hashlib.md5(b.get("label", "btn").encode()).hexdigest()[:6]
    label  = b.get("label", "Click me")
    href   = b.get("href", "")
    size   = b.get("size", "md")
    accent = b.get("accent", "#38bdf8")
    bg     = b.get("background", "#1e293b")
    speed  = b.get("speed", "normal")
    description = b.get("description", "")

    dur = {"slow": "3s", "normal": "1.8s", "fast": "0.9s"}.get(speed, "1.8s")
    pad, fsize = {"sm": ("8px 18px", "0.82rem"), "md": ("12px 28px", "0.92rem"),
                  "lg": ("16px 40px", "1.05rem")}.get(size, ("12px 28px", "0.92rem"))

    hl = _hex_to_rgba(accent, 0.5)

    tag = "a" if href else "button"
    href_attr = f' href="{href}"' if href else ' type="button"'
    desc_html = (
        f'<div style="margin-top:6px;font-size:0.78rem;color:#64748b;">{description}</div>'
    ) if description else ""

    return (
        f'<style>'
        f'@keyframes {sid}-sw{{0%{{background-position:-200% center}}'
        f'100%{{background-position:200% center}}}}'
        f'.{sid}{{display:inline-block;padding:{pad};font-size:{fsize};font-weight:600;'
        f'color:#f1f5f9;border:1px solid rgba(255,255,255,0.14);border-radius:8px;cursor:pointer;'
        f'background:linear-gradient(105deg,{bg} 38%,{hl} 50%,{bg} 62%);'
        f'background-size:200% auto;'
        f'animation:{sid}-sw {dur} linear infinite;'
        f'text-decoration:none;letter-spacing:0.01em;}}'
        f'</style>'
        f'<div style="margin:1rem 0;">'
        f'<{tag}{href_attr} class="{sid}">{label}</{tag}>'
        f'{desc_html}'
        f'</div>'
    )


def _render_card_stack(b: dict) -> str:
    import hashlib
    cid   = "csk_" + hashlib.md5(str(b.get("cards","")).encode()).hexdigest()[:6]
    cards = b.get("cards", [])[:4]
    if not cards:
        return ""
    bg    = b.get("background", "#1e293b")
    border = b.get("border_color", "rgba(255,255,255,0.08)")
    h     = int(b.get("height", 160))

    n = len(cards)
    # angles and vertical offsets per position (front → back)
    all_angles  = [0, -2.5, -4.5, -6.5][:n]
    all_offsets = [0,   6,   12,   18][:n]
    # z-index: front card highest
    z_indices   = list(range(n, 0, -1))

    cards_html = []
    for i, (card, ang, off, z) in enumerate(zip(cards, all_angles, all_offsets, z_indices)):
        is_front = (i == 0)
        z = i + 1
        title = card.get("title", "")
        body  = card.get("body", "")
        accent = card.get("accent", "#38bdf8")
        opacity = 1.0 if is_front else max(0.40, 1.0 - i * 0.22)

        title_html = (
            f'<div style="font-size:0.95rem;font-weight:700;color:#f1f5f9;margin-bottom:5px;">'
            f'{title}</div>'
        ) if title and is_front else ""
        body_html = (
            f'<div style="font-size:0.85rem;color:#94a3b8;line-height:1.5;'
            f'overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;">'
            f'{_md_inline(body)}</div>'
        ) if body and is_front else ""
        accent_bar = (
            f'<div style="width:28px;height:3px;background:{accent};'
            f'border-radius:2px;margin-bottom:10px;"></div>'
        ) if is_front else ""

        cards_html.append(
            f'<div style="position:absolute;top:0;left:0;right:0;height:{h}px;'
            f'border:1px solid {border};background:{bg};border-radius:12px;'
            f'padding:20px 22px;box-sizing:border-box;'
            f'transform:rotate({ang}deg) translateY({off}px);'
            f'z-index:{z};opacity:{opacity};">'
            f'{accent_bar}{title_html}{body_html}'
            f'</div>'
        )

    wrapper_h = h + 18  # extra room for back-card translateY
    return (
        f'<div style="position:relative;height:{wrapper_h}px;'
        f'margin:1.5rem 1rem 1rem;">'
        f'{"".join(cards_html)}'
        f'</div>'
    )


def _render_meteor_shower(b: dict) -> str:
    import hashlib
    mid   = "met_" + hashlib.md5(str(b.get("count",20)).encode()).hexdigest()[:6]
    count = min(int(b.get("count", 20)), 40)
    color = b.get("color", "#38bdf8")
    speed = b.get("speed", "normal")
    title = b.get("title", "")
    body  = b.get("body", "")
    background = b.get("background", "#0a0f1d")

    base = {"slow": 2.2, "normal": 1.2, "fast": 0.6}.get(speed, 1.2)

    meteors = []
    for i in range(count):
        left   = (i * 41 + 11) % 100
        delay  = round((i * 0.21) % 4.0, 2)
        dur    = round(base + (i % 7) * 0.18, 2)
        length = 40 + (i % 5) * 20
        thick  = 1 + (i % 2)
        meteors.append(
            f'<span style="position:absolute;left:{left}%;top:-{length}px;'
            f'width:{thick}px;height:{length}px;border-radius:9999px;'
            f'background:linear-gradient(transparent,{color});'
            f'transform:rotate(35deg);'
            f'animation:{mid}-fall {dur}s linear {delay}s infinite;"></span>'
        )

    title_html = (
        f'<div style="font-size:1.1rem;font-weight:700;color:#f1f5f9;margin-bottom:8px;">'
        f'{title}</div>'
    ) if title else ""
    body_html = (
        f'<div style="font-size:0.9rem;color:#94a3b8;line-height:1.65;">'
        f'{_md_inline(body)}</div>'
    ) if body else ""
    has_content = bool(title or body)

    padding    = "40px 36px" if has_content else "60px 0"
    min_h      = 140 if has_content else 120
    meteors_str = "".join(meteors)
    content_div = (
        f'<div style="position:relative;z-index:1;">{title_html}{body_html}</div>'
    ) if has_content else ""

    return (
        f'<style>'
        f'@keyframes {mid}-fall{{'
        f'0%{{opacity:0;transform:translateX(0) translateY(-80px) rotate(35deg)}}'
        f'10%{{opacity:1}}'
        f'90%{{opacity:1}}'
        f'100%{{opacity:0;transform:translateX(160px) translateY(420px) rotate(35deg)}}'
        f'}}</style>'
        f'<div style="position:relative;overflow:hidden;border-radius:16px;'
        f'background:{background};padding:{padding};'
        f'margin:1rem 0;min-height:{min_h}px;">'
        f'{meteors_str}'
        f'{content_div}'
        f'</div>'
    )


def _render_entity_list(b: dict) -> str:
    """Named resource rows: avatar/icon + title + subtitle + status badge + trailing meta."""
    STATUS_COLORS = {
        "active":      ("#d1fae5", "#059669"),
        "inactive":    ("#f3f4f6", "#6b7280"),
        "error":       ("#fee2e2", "#dc2626"),
        "pending":     ("#fef9c3", "#ca8a04"),
        "in-progress": ("#dbeafe", "#2563eb"),
    }
    items = b.get("items", [])
    rows = ""
    for item in items:
        name     = item.get("name", "")
        subtitle = item.get("subtitle", "")
        icon     = item.get("icon", "")
        status   = item.get("status", "")
        meta     = item.get("meta", "")
        icon_html = (
            f'<div style="width:36px;height:36px;border-radius:50%;background:#ede9fe;'
            f'display:flex;align-items:center;justify-content:center;font-size:1.1rem;'
            f'flex-shrink:0;">{icon}</div>'
        ) if icon else (
            f'<div style="width:36px;height:36px;border-radius:50%;background:#ede9fe;'
            f'display:flex;align-items:center;justify-content:center;font-size:0.88rem;'
            f'font-weight:700;color:#7c3aed;flex-shrink:0;">{name[:1].upper()}</div>'
        )
        badge_bg, badge_fg = STATUS_COLORS.get(status, ("#f3f4f6", "#6b7280"))
        status_html = (
            f'<span style="font-size:0.72rem;font-weight:600;padding:2px 8px;border-radius:100px;'
            f'background:{badge_bg};color:{badge_fg};">{status}</span>'
        ) if status else ""
        subtitle_html = (
            f'<div style="font-size:0.75rem;color:#6b7280;">{subtitle}</div>'
        ) if subtitle else ""
        meta_html = (
            f'<div style="font-size:0.75rem;color:#9ca3af;white-space:nowrap;">{meta}</div>'
        ) if meta else ""
        rows += (
            f'<div style="display:flex;align-items:center;gap:12px;padding:10px 0;'
            f'border-bottom:1px solid #f3f4f6;">'
            f'{icon_html}'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="font-size:0.88rem;font-weight:600;color:#111827;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>'
            f'{subtitle_html}'
            f'</div>'
            f'{status_html}'
            f'{meta_html}'
            f'</div>'
        )
    return f'<div style="margin:1rem 0;">{rows}</div>'


def _render_prompt_template(b: dict) -> str:
    """LLM prompt with {variable} slots highlighted. Copy button included."""
    import re, hashlib
    template  = b.get("template", "")
    accent    = b.get("accent", "#7c3aed")
    copyable  = b.get("copyable", True)
    label     = b.get("label", "")
    pid       = "pt_" + hashlib.md5(template.encode()).hexdigest()[:6]
    slot_bg   = _hex_to_rgba(accent, 0.10)
    slot_fg   = accent

    def _highlight(m):
        return (
            f'<span style="background:{slot_bg};color:{slot_fg};font-weight:600;'
            f'border-radius:3px;padding:0 3px;">{m.group(0)}</span>'
        )
    highlighted = re.sub(r"\{[^}]+\}", _highlight, template.replace("<", "&lt;").replace(">", "&gt;"))
    highlighted = highlighted.replace("\n", "<br>")

    label_html = (
        f'<div style="font-size:0.72rem;font-weight:600;color:#6b7280;'
        f'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">{label}</div>'
    ) if label else ""

    copy_btn = (
        f'<button onclick="navigator.clipboard.writeText(document.getElementById(\'{pid}-src\').innerText)" '
        f'style="padding:4px 10px;border-radius:4px;border:1px solid #dadce0;background:#fff;'
        f'font-size:0.75rem;color:#5f6368;cursor:pointer;flex-shrink:0;">Copy</button>'
    ) if copyable else ""

    return (
        f'<div style="margin:1rem 0;">'
        f'{label_html}'
        f'<div style="border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'padding:6px 12px;background:#f9fafb;border-bottom:1px solid #e0e0e0;">'
        f'<span style="font-size:0.72rem;color:#9ca3af;font-family:monospace;">prompt template</span>'
        f'{copy_btn}'
        f'</div>'
        f'<pre id="{pid}-src" style="margin:0;padding:14px 16px;font-size:0.84rem;'
        f'font-family:monospace;line-height:1.6;color:#374151;background:#fff;'
        f'white-space:pre-wrap;word-break:break-word;">{highlighted}</pre>'
        f'</div>'
        f'</div>'
    )


def _render_model_card(b: dict) -> str:
    """AI model spec card: name, provider, context window, pricing, capability badges."""
    name         = b.get("name", "")
    provider     = b.get("provider", "")
    context_win  = b.get("context_window", "")
    pricing      = b.get("pricing", "")
    capabilities = b.get("capabilities", [])
    accent       = b.get("accent", "#7c3aed")
    badge_bg     = _hex_to_rgba(accent, 0.08)
    badge_border = _hex_to_rgba(accent, 0.30)

    provider_html = (
        f'<span style="font-size:0.72rem;font-weight:600;color:{accent};'
        f'text-transform:uppercase;letter-spacing:0.07em;">{provider}</span>'
    ) if provider else ""

    meta_items = []
    if context_win:
        meta_items.append(("context", context_win))
    if pricing:
        meta_items.append(("pricing", pricing))
    meta_html = "".join(
        f'<div style="display:flex;flex-direction:column;gap:1px;">'
        f'<span style="font-size:0.68rem;color:#9ca3af;text-transform:uppercase;'
        f'letter-spacing:0.05em;">{k}</span>'
        f'<span style="font-size:0.82rem;font-weight:600;color:#374151;">{v}</span>'
        f'</div>'
        for k, v in meta_items
    )
    meta_wrap = (
        f'<div style="display:flex;gap:24px;margin-top:10px;padding-top:10px;'
        f'border-top:1px solid #f3f4f6;">{meta_html}</div>'
    ) if meta_items else ""

    badges = "".join(
        f'<span style="font-size:0.72rem;padding:3px 8px;border-radius:100px;'
        f'background:{badge_bg};color:{accent};border:1px solid {badge_border};'
        f'font-weight:500;">{cap}</span>'
        for cap in capabilities
    )
    badges_html = (
        f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;">{badges}</div>'
    ) if badges else ""

    return (
        f'<div style="margin:1rem 0;padding:16px 18px;border:1px solid #e0e0e0;'
        f'border-radius:10px;background:#fff;">'
        f'{provider_html}'
        f'<div style="font-size:1.1rem;font-weight:700;color:#111827;margin-top:2px;">{name}</div>'
        f'{badges_html}'
        f'{meta_wrap}'
        f'</div>'
    )


def _render_conversation_snippet(b: dict) -> str:
    """User prompt + AI response as chat bubbles."""
    user_label = b.get("user_label", "You")
    user_text  = b.get("user", "")
    ai_label   = b.get("ai_label", "Assistant")
    ai_text    = b.get("response", "")
    accent     = b.get("accent", "#1a73e8")
    user_bg    = _hex_to_rgba(accent, 0.10)
    user_bd    = _hex_to_rgba(accent, 0.25)

    def bubble(label, text, align, bg, bd, label_color):
        return (
            f'<div style="display:flex;flex-direction:column;'
            f'align-items:{"flex-end" if align == "right" else "flex-start"};gap:4px;">'
            f'<span style="font-size:0.7rem;font-weight:600;color:{label_color};'
            f'padding:0 4px;">{label}</span>'
            f'<div style="max-width:80%;padding:10px 14px;border-radius:12px;'
            f'border:1px solid {bd};background:{bg};font-size:0.86rem;'
            f'color:#374151;line-height:1.5;white-space:pre-wrap;">{text}</div>'
            f'</div>'
        )

    return (
        f'<div style="margin:1rem 0;display:flex;flex-direction:column;gap:12px;">'
        f'{bubble(user_label, user_text, "right", user_bg, user_bd, accent)}'
        f'{bubble(ai_label, ai_text, "left", "#f9fafb", "#e5e7eb", "#6b7280")}'
        f'</div>'
    )


def _render_shortcut_legend(b: dict) -> str:
    """Keyboard shortcut cheat-sheet grid — multiple combos with action labels."""
    title = b.get("title", "")
    items = b.get("items", [])

    title_html = (
        f'<div style="font-size:0.8rem;font-weight:700;color:#374151;margin-bottom:10px;">{title}</div>'
    ) if title else ""

    rows = ""
    for item in items:
        keys   = item.get("keys", [])
        action = item.get("action", "")
        kbd_html = "".join(
            f'<kbd style="display:inline-block;padding:2px 7px;border-radius:4px;'
            f'border:1px solid #d1d5db;background:#f9fafb;font-family:monospace;'
            f'font-size:0.78rem;color:#374151;box-shadow:0 1px 0 #d1d5db;">{k}</kbd>'
            for k in keys
        )
        rows += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:6px 0;border-bottom:1px solid #f3f4f6;">'
            f'<span style="font-size:0.82rem;color:#374151;">{action}</span>'
            f'<div style="display:flex;gap:3px;align-items:center;">{kbd_html}</div>'
            f'</div>'
        )
    return (
        f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e5e7eb;'
        f'border-radius:8px;background:#fff;">'
        f'{title_html}'
        f'{rows}'
        f'</div>'
    )


def _render_rating_summary_bar(b: dict) -> str:
    """Aggregate star-rating histogram with percentage bars per level."""
    average   = b.get("average", 0.0)
    total     = b.get("total", 0)
    breakdown = b.get("breakdown", [])
    accent    = b.get("accent", "#f59e0b")

    max_count = max((entry.get("count", 0) for entry in breakdown), default=1) or 1

    header = (
        f'<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:12px;">'
        f'<span style="font-size:2rem;font-weight:700;color:#111827;">{average:.1f}</span>'
        f'<span style="font-size:0.85rem;color:#9ca3af;">/ 5 · {total:,} ratings</span>'
        f'</div>'
    )

    bars = ""
    for entry in breakdown:
        stars = entry.get("stars", 0)
        count = entry.get("count", 0)
        pct   = round(count / total * 100) if total else 0
        width = round(count / max_count * 100)
        bars += (
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span style="font-size:0.78rem;color:#374151;width:2ch;text-align:right;">{stars}</span>'
            f'<span style="font-size:0.82rem;color:{accent};">★</span>'
            f'<div style="flex:1;height:8px;border-radius:100px;background:#f3f4f6;">'
            f'<div style="width:{width}%;height:100%;border-radius:100px;background:{accent};"></div>'
            f'</div>'
            f'<span style="font-size:0.75rem;color:#6b7280;width:3ch;text-align:right;">{pct}%</span>'
            f'</div>'
        )

    return (
        f'<div style="margin:1rem 0;padding:16px 18px;border:1px solid #e0e0e0;'
        f'border-radius:10px;background:#fff;">'
        f'{header}'
        f'<div style="display:flex;flex-direction:column;gap:6px;">{bars}</div>'
        f'</div>'
    )


def _render_roadmap_card(b: dict) -> str:
    """Quarter-based product roadmap with done / in-progress / planned status badges."""
    STATUS = {
        "done":        ("#d1fae5", "#059669", "✓"),
        "in-progress": ("#dbeafe", "#2563eb", "→"),
        "planned":     ("#f3f4f6", "#9ca3af", "○"),
    }
    title   = b.get("title", "")
    periods = b.get("periods", [])

    title_html = (
        f'<div style="font-size:0.9rem;font-weight:700;color:#111827;margin-bottom:14px;">{title}</div>'
    ) if title else ""

    cols = ""
    for period in periods:
        label = period.get("label", "")
        items = period.get("items", [])
        item_rows = ""
        for item in items:
            text   = item.get("text", "")
            status = item.get("status", "planned")
            bg, fg, icon = STATUS.get(status, STATUS["planned"])
            item_rows += (
                f'<div style="display:flex;align-items:flex-start;gap:7px;padding:5px 0;">'
                f'<span style="font-size:0.72rem;font-weight:700;padding:1px 5px;'
                f'border-radius:4px;background:{bg};color:{fg};flex-shrink:0;">{icon}</span>'
                f'<span style="font-size:0.8rem;color:#374151;">{text}</span>'
                f'</div>'
            )
        cols += (
            f'<div style="flex:1;min-width:120px;">'
            f'<div style="font-size:0.72rem;font-weight:700;color:#6b7280;'
            f'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">{label}</div>'
            f'{item_rows}'
            f'</div>'
        )

    return (
        f'<div style="margin:1rem 0;padding:16px 18px;border:1px solid #e0e0e0;'
        f'border-radius:10px;background:#fff;">'
        f'{title_html}'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap;">{cols}</div>'
        f'</div>'
    )


def _render_notification_stack(b: dict) -> str:
    """Persistent notification inbox: icon + title + body + time + unread dot."""
    title = b.get("title", "")
    items = b.get("items", [])

    title_html = (
        f'<div style="font-size:0.82rem;font-weight:700;color:#374151;'
        f'padding:0 14px 8px;border-bottom:1px solid #f3f4f6;">{title}</div>'
    ) if title else ""

    rows = ""
    for item in items:
        icon   = item.get("icon", "🔔")
        ntitle = item.get("title", "")
        body   = item.get("body", "")
        time   = item.get("time", "")
        unread = item.get("unread", False)

        body_html = (
            f'<div style="font-size:0.75rem;color:#6b7280;margin-top:1px;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{body}</div>'
        ) if body else ""
        time_html = (
            f'<div style="font-size:0.7rem;color:#9ca3af;white-space:nowrap;flex-shrink:0;">{time}</div>'
        ) if time else ""
        dot = (
            f'<div style="width:8px;height:8px;border-radius:50%;background:#1a73e8;'
            f'flex-shrink:0;margin-top:4px;"></div>'
        ) if unread else '<div style="width:8px;"></div>'

        rows += (
            f'<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 14px;'
            f'background:{"#f0f7ff" if unread else "#fff"};'
            f'border-bottom:1px solid #f3f4f6;">'
            f'<span style="font-size:1.2rem;line-height:1;flex-shrink:0;">{icon}</span>'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="display:flex;align-items:baseline;justify-content:space-between;gap:8px;">'
            f'<span style="font-size:0.82rem;font-weight:{"700" if unread else "500"};'
            f'color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{ntitle}</span>'
            f'{time_html}'
            f'</div>'
            f'{body_html}'
            f'</div>'
            f'{dot}'
            f'</div>'
        )

    return (
        f'<div style="margin:1rem 0;border:1px solid #e0e0e0;border-radius:10px;'
        f'overflow:hidden;background:#fff;">'
        f'{title_html}'
        f'{rows}'
        f'</div>'
    )


def _render_inline_alert(b: dict) -> str:
    """Compact inline alert: icon + message + optional detail."""
    PALETTES = {
        "info":    {"bg": "#eff6ff", "border": "#93c5fd", "text": "#1e40af", "icon": "ℹ️"},
        "warning": {"bg": "#fffbeb", "border": "#fcd34d", "text": "#92400e", "icon": "⚠️"},
        "error":   {"bg": "#fef2f2", "border": "#fca5a5", "text": "#991b1b", "icon": "🚫"},
        "success": {"bg": "#f0fdf4", "border": "#86efac", "text": "#166534", "icon": "✅"},
    }
    atype  = b.get("type", "info")
    msg    = b.get("message", "")
    detail = b.get("detail", "")
    p      = PALETTES.get(atype, PALETTES["info"])
    icon   = b.get("icon") or p["icon"]

    detail_html = (
        f'<div style="font-size:0.75rem;color:{p["text"]};opacity:0.8;margin-top:2px;">{detail}</div>'
    ) if detail else ""

    return (
        f'<div style="display:inline-flex;align-items:flex-start;gap:6px;'
        f'background:{p["bg"]};border:1px solid {p["border"]};border-radius:6px;'
        f'padding:5px 10px;margin:2px 0;max-width:100%;box-sizing:border-box;">'
        f'<span style="font-size:1rem;line-height:1.4;flex-shrink:0;">{icon}</span>'
        f'<div>'
        f'<span style="font-size:0.82rem;font-weight:600;color:{p["text"]};'
        f'line-height:1.4;">{msg}</span>'
        f'{detail_html}'
        f'</div>'
        f'</div>'
    )


def _render_source_citation(b: dict) -> str:
    """Numbered RAG source cards. Original a2ui-catalogue atom."""
    heading  = b.get("heading", "Sources")
    sources  = b.get("sources", [])

    heading_html = (
        f'<div style="font-size:0.78rem;font-weight:700;color:#374151;'
        f'letter-spacing:0.06em;text-transform:uppercase;margin-bottom:8px;">'
        f'{heading}</div>'
    ) if heading else ""

    cards = ""
    for s in sources:
        num     = s.get("number", "")
        title   = s.get("title", "")
        url     = s.get("url", "")
        excerpt = s.get("excerpt", "")
        author  = s.get("author", "")
        date    = s.get("date", "")
        meta    = " · ".join(filter(None, [author, date]))

        title_el = (
            f'<a href="{url}" style="font-size:0.82rem;font-weight:600;color:#1a73e8;'
            f'text-decoration:none;" target="_blank">{title}</a>'
        ) if url else (
            f'<span style="font-size:0.82rem;font-weight:600;color:#111827;">{title}</span>'
        )
        excerpt_el = (
            f'<div style="font-size:0.75rem;color:#6b7280;margin-top:3px;'
            f'font-style:italic;border-left:2px solid #e5e7eb;padding-left:8px;">'
            f'"{excerpt}"</div>'
        ) if excerpt else ""
        meta_el = (
            f'<div style="font-size:0.7rem;color:#9ca3af;margin-top:2px;">{meta}</div>'
        ) if meta else ""

        cards += (
            f'<div style="display:flex;gap:10px;padding:8px 10px;'
            f'border:1px solid #e5e7eb;border-radius:6px;background:#fafafa;">'
            f'<span style="font-size:0.72rem;font-weight:700;color:#fff;'
            f'background:#6b7280;border-radius:3px;padding:1px 5px;'
            f'flex-shrink:0;align-self:flex-start;margin-top:1px;">[{num}]</span>'
            f'<div style="flex:1;min-width:0;">{title_el}{excerpt_el}{meta_el}</div>'
            f'</div>'
        )

    return (
        f'<div style="margin:1rem 0;">'
        f'{heading_html}'
        f'<div style="display:flex;flex-direction:column;gap:6px;">{cards}</div>'
        f'</div>'
    )


def _render_llm_comparison_table(b: dict) -> str:
    """Side-by-side multi-model output comparison. Original a2ui-catalogue atom."""
    prompt    = b.get("prompt", "")
    models    = b.get("models", [])
    show_meta = b.get("show_meta", None)
    if show_meta is None:
        show_meta = any(m.get("latency_ms") or m.get("cost_usd") or m.get("tokens") for m in models)

    MODEL_COLORS = ["#4f85f6","#f06292","#66bb6a","#ffa726","#ab47bc"]

    prompt_html = (
        f'<div style="margin-bottom:10px;padding:8px 12px;background:#f8fafc;'
        f'border:1px solid #e2e8f0;border-radius:6px;font-size:0.8rem;'
        f'color:#475569;font-family:monospace;">'
        f'<span style="font-weight:700;color:#374151;">Prompt: </span>{prompt}</div>'
    ) if prompt else ""

    col_w = f"{100 // max(len(models), 1)}%"
    headers = ""
    outputs = ""
    meta_row = ""

    for idx, m in enumerate(models):
        color = MODEL_COLORS[idx % len(MODEL_COLORS)]
        name  = m.get("name", f"Model {idx+1}")
        out   = m.get("output", "")
        lat   = m.get("latency_ms")
        cost  = m.get("cost_usd")
        toks  = m.get("tokens")

        headers += (
            f'<th style="width:{col_w};padding:8px 10px;text-align:left;'
            f'border-bottom:2px solid {color};font-size:0.8rem;font-weight:700;'
            f'color:{color};">{name}</th>'
        )
        outputs += (
            f'<td style="width:{col_w};padding:8px 10px;vertical-align:top;'
            f'border-right:1px solid #f3f4f6;font-size:0.8rem;color:#111827;'
            f'line-height:1.55;">{out}</td>'
        )
        if show_meta:
            parts = []
            if lat:  parts.append(f"{lat} ms")
            if toks: parts.append(f"{toks} tok")
            if cost: parts.append(f"${cost:.4f}")
            meta_row += (
                f'<td style="padding:6px 10px;font-size:0.7rem;color:#9ca3af;'
                f'border-right:1px solid #f3f4f6;">{" · ".join(parts)}</td>'
            )

    meta_tr = (
        f'<tr style="background:#f9fafb;">{meta_row}</tr>'
    ) if show_meta and meta_row else ""

    return (
        f'<div style="margin:1rem 0;overflow-x:auto;">'
        f'{prompt_html}'
        f'<table style="width:100%;border-collapse:collapse;'
        f'border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">'
        f'<thead><tr style="background:#f9fafb;">{headers}</tr></thead>'
        f'<tbody>'
        f'<tr>{outputs}</tr>'
        f'{meta_tr}'
        f'</tbody></table></div>'
    )


def _render_confidence_bar(b: dict) -> str:
    """Colour-coded probability bar. Original a2ui-catalogue atom."""
    def _bar(label, value, color_override):
        pct    = max(0, min(100, float(value)))
        color  = color_override or (
            "#22c55e" if pct >= 70 else "#f59e0b" if pct >= 40 else "#ef4444"
        )
        return (
            f'<div style="margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;'
            f'font-size:0.78rem;color:#374151;margin-bottom:3px;">'
            f'<span>{label}</span>'
            f'<span style="font-weight:700;color:{color};">{round(pct)}%</span>'
            f'</div>'
            f'<div style="background:#f3f4f6;border-radius:4px;height:8px;overflow:hidden;">'
            f'<div style="width:{pct}%;height:100%;background:{color};'
            f'border-radius:4px;transition:width .4s;"></div>'
            f'</div>'
            f'</div>'
        )

    items  = b.get("items")
    color  = b.get("color", "")
    if items:
        bars = "".join(_bar(i.get("label",""), i.get("value", 0), color) for i in items)
    else:
        bars = _bar(b.get("label","Confidence"), b.get("value", 0), color)

    return f'<div style="margin:0.75rem 0;">{bars}</div>'


def _render_token_budget_meter(b: dict) -> str:
    """Context-window usage meter. Original a2ui-catalogue atom."""
    import hashlib
    used      = int(b.get("used", 0))
    total     = int(b.get("total", 1)) or 1
    label     = b.get("label", "Context window")
    model     = b.get("model", "")
    warn_at   = float(b.get("warn_at", 70))
    crit_at   = float(b.get("critical_at", 90))
    animate   = b.get("animate", False)
    duration  = float(b.get("duration", 2.0))

    pct = used / total * 100
    color = (
        "#ef4444" if pct >= crit_at else
        "#f59e0b" if pct >= warn_at else
        "#22c55e"
    )

    def _fmt(n):
        return f"{n/1000:.1f}k" if n >= 1000 else str(n)

    model_html = (
        f'<span style="font-size:0.72rem;color:#9ca3af;margin-left:6px;">{model}</span>'
    ) if model else ""

    if animate:
        uid = hashlib.md5(str(b).encode()).hexdigest()[:6]
        return (
            f'<style>'
            f'@property --tok_{uid}{{syntax:"<integer>";initial-value:0;inherits:false;}}'
            f'.tbm_{uid}{{--tok_{uid}:0;counter-reset:t{uid} var(--tok_{uid});'
            f'animation:tbmc_{uid} {duration}s ease-in-out forwards;}}'
            f'.tbm_{uid}::before{{content:counter(t{uid});}}'
            f'.tbf_{uid}{{width:0%;animation:tbmb_{uid} {duration}s ease-in-out forwards;}}'
            f'@keyframes tbmc_{uid}{{from{{--tok_{uid}:0}}to{{--tok_{uid}:{used}}}}}'
            f'@keyframes tbmb_{uid}{{from{{width:0%}}to{{width:{min(pct,100):.2f}%}}}}'
            f'</style>'
            f'<div style="margin:0.75rem 0;padding:10px 14px;border:1px solid #374151;'
            f'border-radius:8px;background:#111827;">'
            f'<div style="display:flex;align-items:baseline;justify-content:space-between;'
            f'margin-bottom:6px;">'
            f'<span style="font-size:1rem;font-weight:700;color:#ffffff;">'
            f'{label}{model_html}</span>'
            f'<span style="font-size:2rem;font-weight:800;color:#ffffff;font-family:monospace;">'
            f'<span class="tbm_{uid}"></span>'
            f'<span style="color:#6b7280;"> / {_fmt(total)}</span>'
            f'<span style="font-size:1rem;color:#9ca3af;margin-left:8px;">({round(pct)}%)</span>'
            f'</span>'
            f'</div>'
            f'<div style="background:#374151;border-radius:4px;height:10px;overflow:hidden;">'
            f'<div class="tbf_{uid}" style="height:100%;background:{color};border-radius:4px;"></div>'
            f'</div>'
            f'</div>'
        )

    return (
        f'<div style="margin:0.75rem 0;padding:10px 14px;border:1px solid #e5e7eb;'
        f'border-radius:8px;background:#fafafa;">'
        f'<div style="display:flex;align-items:baseline;justify-content:space-between;'
        f'margin-bottom:6px;">'
        f'<span style="font-size:0.8rem;font-weight:600;color:#374151;">'
        f'{label}{model_html}</span>'
        f'<span style="font-size:0.78rem;font-weight:700;color:{color};">'
        f'{_fmt(used)} / {_fmt(total)} ({round(pct)}%)</span>'
        f'</div>'
        f'<div style="background:#e5e7eb;border-radius:4px;height:10px;overflow:hidden;">'
        f'<div style="width:{min(pct,100):.1f}%;height:100%;background:{color};'
        f'border-radius:4px;"></div>'
        f'</div>'
        f'</div>'
    )


def _render_chartjs_pie(b: dict) -> str:
    """Multi-slice pie/donut SVG chart with legend. Source: OpenUI/Thesys MIT."""
    import math
    title       = b.get("title", "")
    variant     = b.get("variant", "donut")
    data        = b.get("data", [])
    show_legend = b.get("show_legend", True)
    show_labels = b.get("show_labels", True)
    custom_colors = b.get("colors", [])

    DEFAULT_COLORS = [
        "#4f85f6","#f06292","#66bb6a","#ffa726","#ab47bc",
        "#26c6da","#ef5350","#8d6e63","#78909c","#26a69a",
    ]

    total = sum(item.get("value", 0) for item in data) or 1
    cx, cy, r = 120, 120, 90
    hole = 54 if variant == "donut" else 0

    def polar(cx, cy, r, angle_deg):
        rad = math.radians(angle_deg - 90)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    slices_svg = ""
    legend_html = ""
    start = 0.0
    for idx, item in enumerate(data):
        label = item.get("label", f"Slice {idx+1}")
        value = item.get("value", 0)
        pct   = value / total
        sweep = pct * 360
        color = custom_colors[idx] if idx < len(custom_colors) else DEFAULT_COLORS[idx % len(DEFAULT_COLORS)]

        end = start + sweep
        large = 1 if sweep > 180 else 0

        x1, y1 = polar(cx, cy, r, start)
        x2, y2 = polar(cx, cy, r, end)

        if hole:
            xi1, yi1 = polar(cx, cy, hole, start)
            xi2, yi2 = polar(cx, cy, hole, end)
            path = (
                f"M {x1:.2f} {y1:.2f} "
                f"A {r} {r} 0 {large} 1 {x2:.2f} {y2:.2f} "
                f"L {xi2:.2f} {yi2:.2f} "
                f"A {hole} {hole} 0 {large} 0 {xi1:.2f} {yi1:.2f} Z"
            )
        else:
            path = (
                f"M {cx} {cy} "
                f"L {x1:.2f} {y1:.2f} "
                f"A {r} {r} 0 {large} 1 {x2:.2f} {y2:.2f} Z"
            )
        slices_svg += f'<path d="{path}" fill="{color}" stroke="#fff" stroke-width="2"/>'

        if show_labels and pct > 0.04:
            mid = start + sweep / 2
            lx, ly = polar(cx, cy, (r + hole) / 2 if hole else r * 0.65, mid)
            slices_svg += (
                f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="10" fill="#fff" font-weight="600">'
                f'{round(pct*100)}%</text>'
            )

        if show_legend:
            legend_html += (
                f'<div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:#374151;">'
                f'<span style="width:10px;height:10px;border-radius:2px;background:{color};flex-shrink:0;"></span>'
                f'<span>{label}</span>'
                f'<span style="margin-left:auto;font-weight:600;">{round(pct*100)}%</span>'
                f'</div>'
            )
        start = end

    title_html = (
        f'<div style="font-size:0.85rem;font-weight:700;color:#111827;text-align:center;'
        f'margin-bottom:6px;">{title}</div>'
    ) if title else ""

    legend_block = (
        f'<div style="display:flex;flex-direction:column;gap:5px;margin-top:10px;">{legend_html}</div>'
    ) if show_legend else ""

    return (
        f'<div style="margin:1rem 0;text-align:center;">'
        f'{title_html}'
        f'<svg viewBox="0 0 240 240" width="200" height="200" style="overflow:visible;">'
        f'{slices_svg}'
        f'</svg>'
        f'{legend_block}'
        f'</div>'
    )


def _render_text_callout(b: dict) -> str:
    """Lightweight tinted tip/note block. Source: OpenUI/Thesys MIT."""
    PALETTES = {
        "info":    {"bg": "#eff6ff", "border": "#dbeafe", "title": "#1e40af", "body": "#1e3a8a"},
        "success": {"bg": "#f0fdf4", "border": "#dcfce7", "title": "#166534", "body": "#14532d"},
        "warning": {"bg": "#fffbeb", "border": "#fef3c7", "title": "#92400e", "body": "#78350f"},
        "neutral": {"bg": "#f9fafb", "border": "#e5e7eb", "title": "#374151", "body": "#4b5563"},
    }
    variant = b.get("variant", "neutral")
    title   = b.get("title", "")
    desc    = b.get("description", "")
    p       = PALETTES.get(variant, PALETTES["neutral"])

    return (
        f'<div style="margin:0.5rem 0;padding:8px 12px;border-radius:6px;'
        f'background:{p["bg"]};border:1px solid {p["border"]};">'
        f'<div style="font-size:0.78rem;font-weight:700;color:{p["title"]};'
        f'margin-bottom:2px;">{title}</div>'
        f'<div style="font-size:0.8rem;color:{p["body"]};line-height:1.5;">{desc}</div>'
        f'</div>'
    )


def _render_tag_block(b: dict) -> str:
    """Horizontal wrap of neutral content chip labels. Source: OpenUI/Thesys MIT."""
    tags   = b.get("tags", [])
    color  = b.get("color", "")
    bg     = color or "#f3f4f6"
    border = color or "#d1d5db"
    text   = "#374151"

    chips = "".join(
        f'<span style="display:inline-block;padding:3px 10px;border-radius:9999px;'
        f'background:{bg};border:1px solid {border};color:{text};'
        f'font-size:0.78rem;font-weight:500;white-space:nowrap;">{t}</span>'
        for t in tags
    )
    return (
        f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin:0.75rem 0;">'
        f'{chips}'
        f'</div>'
    )


def _render_variant_selector(b: dict) -> str:
    """CSS-only radio card group for variant picking. Source: OpenUI/Thesys MIT."""
    name    = b.get("name", "variant")
    label   = b.get("label", "")
    items   = b.get("items", [])
    default = b.get("default_value", "")
    uid     = abs(hash(name + label)) % 999983

    label_html = (
        f'<div style="font-size:0.82rem;font-weight:600;color:#374151;margin-bottom:8px;">'
        f'{label}</div>'
    ) if label else ""

    style = (
        f'<style>'
        f'.vs{uid} label{{display:block;padding:10px 14px;border:1px solid #d1d5db;'
        f'border-radius:8px;cursor:pointer;transition:border-color .15s,background .15s;'
        f'background:#fff;}}'
        f'.vs{uid} label:has(input:checked){{border-color:#1a73e8;background:#eff6ff;}}'
        f'.vs{uid} label:hover{{border-color:#9ca3af;}}'
        f'.vs{uid} input{{position:absolute;opacity:0;width:0;height:0;}}'
        f'</style>'
    )

    cards = ""
    for item in items:
        val   = item.get("value", "")
        title = item.get("title", val)
        desc  = item.get("description", "")
        chk   = "checked" if val == default else ""
        desc_html = (
            f'<div style="font-size:0.75rem;color:#6b7280;margin-top:2px;">{desc}</div>'
        ) if desc else ""
        cards += (
            f'<label>'
            f'<input type="radio" name="{name}" value="{val}" {chk}>'
            f'<div style="font-size:0.85rem;font-weight:600;color:#111827;">{title}</div>'
            f'{desc_html}'
            f'</label>'
        )

    return (
        f'{style}'
        f'<div style="margin:0.75rem 0;">'
        f'{label_html}'
        f'<div class="vs{uid}" style="display:flex;flex-direction:column;gap:8px;">'
        f'{cards}'
        f'</div>'
        f'</div>'
    )


def _render_markdown_block(b: dict) -> str:
    """GFM markdown string rendered to HTML. Source: OpenUI/Thesys MIT."""
    content = b.get("content", "")
    variant = b.get("variant", "default")
    margin  = "0.5rem 0" if variant == "compact" else "1rem 0"

    html = _md.markdown(
        content,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    return (
        f'<div class="md-block" style="margin:{margin};'
        f'font-size:0.9rem;line-height:1.65;color:#202124;">'
        f'{html}'
        f'</div>'
    )


# ── React/Tailwind second wave ────────────────────────────────────────────────

def _render_multi_select_input(b: dict) -> str:
    """Tag/chip style multi-value select — shadcn multi-select pattern."""
    import html as _h
    label       = b.get("label", "")
    name        = b.get("name", "ms")
    options     = b.get("options", [])
    selected    = b.get("selected", [])
    placeholder = b.get("placeholder", "Add option…")

    chips_html = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:4px;padding:3px 9px 3px 10px;'
        f'background:#e8f0fe;color:#1a73e8;border-radius:14px;font-size:0.82rem;font-weight:500;">'
        f'{_h.escape(next((o.get("label", v) for o in options if o.get("value")==v), v))}'
        f'<span style="color:#5f6368;margin-left:1px;cursor:pointer;">×</span></span>'
        for v in selected
    )
    avail = [o for o in options if o.get("value") not in selected]
    avail_html = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;padding:8px 12px;'
        f'cursor:pointer;font-size:0.87rem;color:#3c4043;">'
        f'<span style="width:16px;height:16px;border:2px solid #dadce0;border-radius:3px;'
        f'flex-shrink:0;display:inline-block;"></span>'
        f'{_h.escape(o.get("label",""))}</div>'
        for o in avail[:6]
    )
    label_html = (
        f'<label style="display:block;font-size:0.83rem;font-weight:600;'
        f'color:#3c4043;margin-bottom:5px;">{_h.escape(label)}</label>'
    ) if label else ""
    return (
        f'<div style="margin:1rem 0;max-width:360px;">{label_html}'
        f'<div style="border:1px solid #dadce0;border-radius:6px;overflow:hidden;'
        f'box-shadow:0 4px 14px rgba(0,0,0,0.07);">'
        f'<div style="display:flex;flex-wrap:wrap;gap:6px;padding:8px 10px;background:#fff;'
        f'border-bottom:1px solid #f1f3f4;min-height:42px;align-items:center;">'
        f'{chips_html}'
        f'<input type="text" placeholder="{_h.escape(placeholder)}" '
        f'style="border:none;outline:none;font-size:0.87rem;color:#3c4043;'
        f'background:transparent;min-width:90px;flex:1;padding:2px 0;"></div>'
        f'{avail_html}</div></div>'
    )


def _render_otp_input(b: dict) -> str:
    """6-box one-time password input — shadcn OTP field pattern."""
    import html as _h
    length = int(b.get("length", 6))
    value  = str(b.get("value", ""))
    label  = b.get("label", "")

    boxes = ""
    for i in range(length):
        digit        = value[i] if i < len(value) else ""
        border_color = "#1a73e8" if digit else "#dadce0"
        bg           = "#f0f4ff" if digit else "#fff"
        boxes += (
            f'<input type="text" maxlength="1" value="{digit}" '
            f'style="width:44px;height:52px;text-align:center;font-size:1.3rem;'
            f'font-weight:700;border:2px solid {border_color};border-radius:8px;'
            f'background:{bg};color:#202124;outline:none;'
            f'transition:border-color .15s,background .15s;">'
        )
    label_html = (
        f'<div style="font-size:0.83rem;font-weight:600;color:#3c4043;margin-bottom:10px;">'
        f'{_h.escape(label)}</div>'
    ) if label else ""
    return f'<div style="margin:1rem 0;">{label_html}<div style="display:flex;gap:8px;">{boxes}</div></div>'


def _render_bento_grid(b: dict) -> str:
    """Asymmetric bento box feature grid — MagicUI/shadcn pattern."""
    import html as _h
    tiles   = b.get("tiles", [])
    heading = b.get("heading", "")
    cols    = int(b.get("columns", 3))

    heading_html = (
        f'<h3 style="font-size:1.3rem;font-weight:700;color:#202124;margin:0 0 16px;">'
        f'{_h.escape(heading)}</h3>'
    ) if heading else ""

    _COLORS = ["#1a73e8","#34a853","#ea4335","#fbbc04","#9c27b0","#00bcd4","#ff6d00","#00897b"]
    tiles_html = ""
    for i, tile in enumerate(tiles):
        title    = tile.get("title", "")
        subtitle = tile.get("subtitle", tile.get("description", ""))
        icon     = tile.get("icon", "")
        span     = int(tile.get("span", 1))
        color    = tile.get("color", _COLORS[i % len(_COLORS)])
        bg       = tile.get("background", f"{color}0d")
        col_span = f"1 / span {min(span, cols)}" if span > 1 else "auto"
        icon_html = f'<span style="font-size:1.7rem;margin-bottom:4px;">{icon}</span>' if icon else ""
        tiles_html += (
            f'<div style="grid-column:{col_span};background:{bg};border:1px solid {color}28;'
            f'border-radius:14px;padding:20px 22px;display:flex;flex-direction:column;gap:6px;">'
            f'{icon_html}'
            f'<div style="font-size:{"1.05rem" if span>1 else "0.92rem"};'
            f'font-weight:700;color:#202124;">{_h.escape(title)}</div>'
            f'<div style="font-size:0.82rem;color:#5f6368;line-height:1.55;">{_h.escape(subtitle)}</div>'
            f'</div>'
        )
    return (
        f'<div style="margin:1.5rem 0;">{heading_html}'
        f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:12px;">'
        f'{tiles_html}</div></div>'
    )


def _render_cta_section(b: dict) -> str:
    """Full-width call-to-action section — Tailwind UI pattern."""
    import html as _h
    heading   = b.get("heading", "")
    body      = b.get("body", b.get("description", ""))
    primary   = b.get("primary_cta", {})
    secondary = b.get("secondary_cta", {})
    bg        = b.get("background", "#1a73e8")

    primary_html = (
        f'<a href="{_h.escape(primary.get("url","#"))}" '
        f'style="display:inline-flex;align-items:center;padding:11px 22px;'
        f'background:#fff;color:{bg};font-size:0.9rem;font-weight:700;'
        f'border-radius:8px;text-decoration:none;">{_h.escape(primary.get("label",""))}</a>'
    ) if primary else ""
    secondary_html = (
        f'<a href="{_h.escape(secondary.get("url","#"))}" '
        f'style="display:inline-flex;align-items:center;padding:11px 22px;'
        f'background:rgba(255,255,255,0.15);color:#fff;font-size:0.9rem;font-weight:600;'
        f'border-radius:8px;text-decoration:none;border:1px solid rgba(255,255,255,0.4);">'
        f'{_h.escape(secondary.get("label",""))}</a>'
    ) if secondary else ""

    return (
        f'<div style="margin:1.5rem 0;background:{bg};border-radius:14px;padding:36px 32px;text-align:center;">'
        f'<h3 style="font-size:1.4rem;font-weight:800;color:#fff;margin:0 0 10px;">{_h.escape(heading)}</h3>'
        f'<p style="font-size:0.93rem;color:rgba(255,255,255,0.85);margin:0 auto 24px;'
        f'max-width:480px;line-height:1.65;">{_h.escape(body)}</p>'
        f'<div style="display:flex;justify-content:center;gap:12px;flex-wrap:wrap;">'
        f'{primary_html}{secondary_html}</div></div>'
    )


def _render_animated_counter(b: dict) -> str:
    """CSS @property counter animation — counts up to target values without JS."""
    counters = b.get("counters", [])
    if not counters and b.get("value") is not None:
        counters = [{"value": b.get("value"), "label": b.get("label", ""),
                     "suffix": b.get("suffix", ""), "prefix": b.get("prefix", "")}]
    duration = float(b.get("duration", 2))
    _COLORS  = ["#1a73e8","#34a853","#ea4335","#9c27b0","#ff6d00","#00bcd4"]
    uid      = abs(hash(str(counters))) % 100000

    style_parts = []
    items_html  = ""
    for i, c in enumerate(counters):
        raw_val = str(c.get("value", 0)).replace(",", "").rstrip("%+kKmM")
        try:
            val = int(float(raw_val))
        except ValueError:
            val = 0
        label  = c.get("label", "")
        suffix = c.get("suffix", "")
        prefix = c.get("prefix", "")
        color  = c.get("color", _COLORS[i % len(_COLORS)])
        prop   = f"--ac{uid}p{i}"
        cv     = f"ac{uid}cv{i}"
        cid    = f"ac{uid}i{i}"
        style_parts.append(
            f'@property {prop}{{syntax:"<integer>";initial-value:0;inherits:false;}}'
            f'@keyframes {cid}{{from{{{prop}:0}}to{{{prop}:{val}}}}}'
            f'.{cid}{{animation:{cid} {duration}s ease-out forwards;counter-reset:{cv} var({prop});}}'
            f'.{cid}::after{{content:"{prefix}" counter({cv}) "{suffix}";'
            f'font-size:2.2rem;font-weight:800;color:{color};}}'
        )
        items_html += (
            f'<div style="text-align:center;padding:16px 28px;">'
            f'<div class="{cid}"></div>'
            f'<div style="font-size:0.84rem;color:#5f6368;margin-top:4px;font-weight:500;">'
            f'{label}</div></div>'
        )

    return (
        f'<style>{"".join(style_parts)}</style>'
        f'<div style="margin:1.5rem 0;display:flex;flex-wrap:wrap;justify-content:center;'
        f'gap:8px;border:1px solid #e5e7eb;border-radius:12px;background:#fff;padding:12px 0;">'
        f'{items_html}</div>'
    )


# ── React/Tailwind ecosystem atoms (shadcn/ui, Radix, Tailwind UI patterns) ──

def _render_combobox(b: dict) -> str:
    """Searchable filterable dropdown — shadcn/Headless UI combobox pattern."""
    import html as _h
    label       = b.get("label", "")
    name        = b.get("name", "cb")
    placeholder = b.get("placeholder", "Search…")
    options     = b.get("options", [])
    selected    = b.get("selected", "")
    rules       = b.get("rules", [])
    req_star    = '<span style="color:#ea4335;margin-left:2px;">*</span>' if "required" in rules else ""

    datalist_id   = f"dl-{name}"
    datalist_opts = "".join(f'<option value="{_h.escape(o.get("label",""))}"></option>' for o in options)

    selected_label = next((o.get("label","") for o in options if o.get("value") == selected), "")

    opts_html = ""
    for o in options[:7]:
        is_sel  = o.get("value") == selected
        bg      = "#f0f4ff" if is_sel else "#fff"
        fw      = "600"     if is_sel else "400"
        check   = "✓ "      if is_sel else " "
        opts_html += (
            f'<div style="display:flex;align-items:center;gap:6px;padding:8px 12px;'
            f'cursor:pointer;background:{bg};font-size:0.88rem;color:#3c4043;font-weight:{fw};">'
            f'<span style="color:#1a73e8;width:14px;flex-shrink:0;">{check}</span>'
            f'{_h.escape(o.get("label",""))}</div>'
        )
    if len(options) > 7:
        opts_html += (
            f'<div style="padding:6px 12px;font-size:0.78rem;color:#5f6368;border-top:1px solid #f1f3f4;">'
            f'{len(options)-7} more options…</div>'
        )

    label_html = (
        f'<label for="{name}" style="display:block;font-size:0.83rem;font-weight:600;'
        f'color:#3c4043;margin-bottom:5px;">{_h.escape(label)}{req_star}</label>'
    ) if label else ""

    return (
        f'<div style="margin:1rem 0;max-width:360px;">'
        f'{label_html}'
        f'<div style="border:1px solid #dadce0;border-radius:6px;overflow:hidden;'
        f'box-shadow:0 4px 14px rgba(0,0,0,0.08);">'
        f'<div style="display:flex;align-items:center;padding:0 10px;gap:6px;background:#fff;'
        f'border-bottom:1px solid #f1f3f4;">'
        f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5f6368" stroke-width="2">'
        f'<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>'
        f'<input type="text" id="{name}" name="{name}" list="{datalist_id}" '
        f'placeholder="{_h.escape(placeholder)}" value="{_h.escape(selected_label)}" '
        f'style="flex:1;border:none;outline:none;padding:9px 0;font-size:0.9rem;'
        f'color:#3c4043;background:transparent;">'
        f'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5f6368" stroke-width="2">'
        f'<path d="M6 9l6 6 6-6"/></svg>'
        f'</div>'
        f'<datalist id="{datalist_id}">{datalist_opts}</datalist>'
        f'{opts_html}'
        f'</div>'
        f'</div>'
    )


def _render_feature_grid(b: dict) -> str:
    """Icon + title + description grid — Tailwind UI feature section pattern."""
    import html as _h
    heading     = b.get("heading", "")
    description = b.get("description", "")
    features    = b.get("features", [])
    columns     = int(b.get("columns", 3))

    heading_html = (
        f'<h3 style="font-size:1.3rem;font-weight:700;color:#202124;margin:0 0 8px;">'
        f'{_h.escape(heading)}</h3>'
    ) if heading else ""
    desc_html = (
        f'<p style="font-size:0.93rem;color:#5f6368;margin:0 0 28px;max-width:560px;line-height:1.6;">'
        f'{_h.escape(description)}</p>'
    ) if description else ""

    _COLORS = ["#1a73e8","#34a853","#ea4335","#fbbc04","#9c27b0","#00bcd4","#ff6d00","#00897b"]
    items_html = ""
    for i, feat in enumerate(features):
        icon  = feat.get("icon", "◆")
        title = feat.get("title", "")
        desc  = feat.get("description", "")
        badge = feat.get("badge", "")
        color = feat.get("color", _COLORS[i % len(_COLORS)])
        badge_html = (
            f'<span style="font-size:0.68rem;font-weight:600;letter-spacing:.05em;'
            f'text-transform:uppercase;color:{color};background:{color}1a;'
            f'padding:2px 7px;border-radius:10px;margin-left:8px;">{_h.escape(badge)}</span>'
        ) if badge else ""
        items_html += (
            f'<div style="display:flex;flex-direction:column;gap:10px;">'
            f'<div style="width:42px;height:42px;border-radius:10px;background:{color}18;'
            f'display:flex;align-items:center;justify-content:center;font-size:1.15rem;">{icon}</div>'
            f'<div style="font-size:0.95rem;font-weight:600;color:#202124;">'
            f'{_h.escape(title)}{badge_html}</div>'
            f'<div style="font-size:0.85rem;color:#5f6368;line-height:1.6;">{_h.escape(desc)}</div>'
            f'</div>'
        )

    return (
        f'<div style="margin:1.5rem 0;">'
        f'{heading_html}{desc_html}'
        f'<div style="display:grid;grid-template-columns:repeat({columns},1fr);gap:28px 24px;">'
        f'{items_html}'
        f'</div>'
        f'</div>'
    )


def _render_navigation_menu(b: dict) -> str:
    """Multi-level horizontal nav bar — Radix NavigationMenu pattern."""
    import html as _h
    brand     = b.get("brand", "")
    brand_url = b.get("brand_url", "#")
    items     = b.get("items", [])
    cta       = b.get("cta", None)

    brand_html = (
        f'<a href="{_h.escape(brand_url)}" style="font-size:0.97rem;font-weight:700;'
        f'color:#202124;text-decoration:none;margin-right:20px;white-space:nowrap;'
        f'letter-spacing:-.01em;">{_h.escape(brand)}</a>'
    ) if brand else ""

    nav_items_html = ""
    first_submenu_html = ""
    for idx, item in enumerate(items):
        label    = item.get("label", "")
        url      = item.get("url", "#")
        children = item.get("children", [])
        is_active = idx == 0
        active_style = "background:#f0f4ff;color:#1a73e8;" if is_active else "color:#3c4043;"
        if children:
            nav_items_html += (
                f'<span style="display:inline-flex;align-items:center;gap:3px;padding:6px 11px;'
                f'font-size:0.87rem;font-weight:500;border-radius:6px;cursor:pointer;{active_style}">'
                f'{_h.escape(label)}'
                f'<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>'
                f'</span>'
            )
            if is_active:
                child_items = ""
                for child in children:
                    c_url  = child.get("url", "#")
                    c_lbl  = child.get("label", "")
                    c_desc = child.get("description", "")
                    desc_h = (
                        f'<div style="font-size:0.77rem;color:#5f6368;margin-top:2px;">{_h.escape(c_desc)}</div>'
                    ) if c_desc else ""
                    child_items += (
                        f'<a href="{_h.escape(c_url)}" style="display:block;padding:9px 12px;'
                        f'border-radius:6px;text-decoration:none;">'
                        f'<div style="font-size:0.87rem;font-weight:500;color:#202124;">{_h.escape(c_lbl)}</div>'
                        f'{desc_h}</a>'
                    )
                first_submenu_html = (
                    f'<div style="border-top:1px solid #e8eaed;background:#fafafa;padding:8px 16px 12px;">'
                    f'<div style="font-size:0.72rem;font-weight:600;color:#80868b;letter-spacing:.07em;'
                    f'text-transform:uppercase;padding:6px 12px 4px;">{_h.escape(label)}</div>'
                    f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:2px;">'
                    f'{child_items}</div>'
                    f'</div>'
                )
        else:
            nav_items_html += (
                f'<a href="{_h.escape(url)}" style="padding:6px 11px;font-size:0.87rem;'
                f'font-weight:500;{active_style}text-decoration:none;border-radius:6px;">'
                f'{_h.escape(label)}</a>'
            )

    cta_html = (
        f'<a href="{_h.escape(cta.get("url","#"))}" style="margin-left:auto;padding:7px 16px;'
        f'background:#1a73e8;color:#fff;font-size:0.84rem;font-weight:600;'
        f'border-radius:6px;text-decoration:none;white-space:nowrap;">'
        f'{_h.escape(cta.get("label",""))}</a>'
    ) if cta else ""

    return (
        f'<div style="margin:1.5rem 0;border:1px solid #dadce0;border-radius:10px;overflow:hidden;">'
        f'<nav style="display:flex;align-items:center;padding:8px 16px;background:#fff;gap:2px;">'
        f'{brand_html}{nav_items_html}{cta_html}'
        f'</nav>'
        f'{first_submenu_html}'
        f'</div>'
    )


# ── Registry ─────────────────────────────────────────────────────────────────

_RENDERERS = {
    "intro":        _render_intro,
    "body":         _render_body,
    "heading":      _render_heading,
    "subheading":   _render_subheading,
    "quote":        _render_quote,
    "code":         _render_code,
    "pipeline":     _render_pipeline,
    "bullet_list":  _render_bullet_list,
    "divider":      _render_divider,
    "youtube":      _render_youtube,
    "image":        _render_image,
    "image_pair":   _render_image_pair,
    "diagram":      _render_diagram,
    "repo_links":              _render_repo_links,
    "github_repo_card":        _render_github_repo_card,
    "terminal_block":          _render_terminal_block,
    "file_tree":               _render_file_tree,
    "tabbed_code":             _render_tabbed_code,
    "http_request_block":      _render_http_request_block,
    "env_var_list":            _render_env_var_list,
    "prerequisite_checklist":  _render_prerequisite_checklist,
    "keyboard_shortcut":       _render_keyboard_shortcut,
    "api_param_table":         _render_api_param_table,
    "version_badge":           _render_version_badge,
    "deprecation_notice":      _render_deprecation_notice,
    "experimental_banner":     _render_experimental_banner,
    "cli_command":             _render_cli_command,
    "copy_code_button":        _render_copy_code_button,
    "log_output":              _render_log_output,
    "json_tree_viewer":        _render_json_tree_viewer,
    "key_takeaways":           _render_key_takeaways,
    "summary_box":             _render_summary_box,
    "learning_objectives":     _render_learning_objectives,
    "changelog_entry":         _render_changelog_entry,
    "release_notes":           _render_release_notes,
    "further_reading":         _render_further_reading,
    "resources_list":          _render_resources_list,
    "sidebar_note":            _render_sidebar_note,
    "difficulty_badge":        _render_difficulty_badge,
    "caution_block":           _render_caution_block,
    "checklist_interactive":   _render_checklist_interactive,
    "glossary_inline":         _render_glossary_inline,
    "time_estimate":           _render_time_estimate,
    "progress_checkpoint":     _render_progress_checkpoint,
    "social_share_bar":        _render_social_share_bar,
    "newsletter_cta":          _render_newsletter_cta,
    "author_bio_card":         _render_author_bio_card,
    "related_posts_grid":      _render_related_posts_grid,
    "series_overview_card":    _render_series_overview_card,
    "reaction_group":          _render_reaction_group,
    "share_quote":             _render_share_quote,
    "follow_cta":              _render_follow_cta,
    "follow_button":           _render_follow_button,
    "reading_progress_bar":    _render_reading_progress_bar,
    "table_of_contents":       _render_table_of_contents,
    "article_hero":            _render_article_hero,
    "scroll_to_top":           _render_scroll_to_top,
    "article_series_nav":      _render_article_series_nav,
    "post_metadata_bar":       _render_post_metadata_bar,
    "embed_codepen":           _render_embed_codepen,
    "embed_stackblitz":        _render_embed_stackblitz,
    "embed_gist":              _render_embed_gist,
    "embed_tweet":             _render_embed_tweet,
    "embed_google_slides":     _render_embed_google_slides,
    "lottie_animation":        _render_lottie_animation,
    "figma_embed":             _render_figma_embed,
    "closing":      _render_closing,
    "callout":      _render_callout,
    "steps":        _render_steps,
    "table":        _render_table,
    "tabs":          _render_tabs,
    "key_value":     _render_key_value,
    "before_after":   _render_before_after,
    "api_reference":  _render_api_reference,
    "timeline":       _render_timeline,
    "annotated_code": _render_annotated_code,
    "gallery":        _render_gallery,
    "video_pair":     _render_video_pair,
    "carousel":       _render_carousel,
    "stat_card":      _render_stat_card,
    "progress_bar":   _render_progress_bar,
    "badge_group":    _render_badge_group,
    "sparkline": _render_sparkline,
    "heatmap": _render_heatmap,
    "donut_stat": _render_donut_stat,
    "metric_delta": _render_metric_delta,
    "trend_indicator": _render_trend_indicator,
    "breadcrumb": _render_breadcrumb,
    "pagination": _render_pagination,
    "stepper": _render_stepper,
    "tab_bar": _render_tab_bar,
    "anchor_list": _render_anchor_list,
    "faq_accordion": _render_faq_accordion,
    "glossary_term": _render_glossary_term,
    "footnote": _render_footnote,
    "blockquote_with_avatar": _render_blockquote_with_avatar,
    "pull_stat": _render_pull_stat,
    "accordion_item": _render_accordion_item,
    "tooltip": _render_tooltip,
    "hover_card": _render_hover_card,
    "collapsible_panel": _render_collapsible_panel,
    "css_modal": _render_css_modal,
    "audio_player": _render_audio_player,
    "audio_link": _render_audio_link,
    "pdf_preview": _render_pdf_preview,
    "document_link": _render_document_link,
    "video_thumbnail": _render_video_thumbnail,
    "video_card": _render_video_card,
    "code_diff": _render_code_diff,
    "code_snippet_pair": _render_code_snippet_pair,
    "framed_screenshot": _render_framed_screenshot,
    "image_with_caption": _render_image_with_caption,
    "alert_banner": _render_alert_banner,
    "toast_notification": _render_toast_notification,
    "loading_skeleton": _render_loading_skeleton,
    "empty_state": _render_empty_state,
    "spinner": _render_spinner,
    "status_pill": _render_status_pill,
    "inline_feedback_message": _render_inline_feedback_message,
    "rating_stars": _render_rating_stars,
    "progress_circle": _render_progress_circle,
    "action_required_card": _render_action_required_card,
    "feature_matrix": _render_feature_matrix,
    "pricing_tier_card": _render_pricing_tier_card,
    "pricing_tier_group": _render_pricing_tier_group,
    "pros_cons_list": _render_pros_cons_list,
    "side_by_side_spec": _render_side_by_side_spec,
    "product_spec_table": _render_product_spec_table,
    "comparison_grid": _render_comparison_grid,
    "versus_block": _render_versus_block,
    "rating_comparison": _render_rating_comparison,
    "capability_checklist": _render_capability_checklist,
    "toggle_switch": _render_toggle_switch,
    "expandable_text": _render_expandable_text,
    "flip_card": _render_flip_card,
    "image_hotspots": _render_image_hotspots,
    "css_dropdown_menu": _render_css_dropdown_menu,
    "star_rating_input": _render_star_rating_input,
    "segmented_control": _render_segmented_control,
    "zoomable_image": _render_zoomable_image,
    "custom_checkbox_group": _render_custom_checkbox_group,
    "css_slide_panel": _render_css_slide_panel,
    "testimonial_card": _render_testimonial_card,
    "star_rating_display": _render_star_rating_display,
    "avatar_group": _render_avatar_group,
    "contributor_list": _render_contributor_list,
    "customer_logo_grid": _render_customer_logo_grid,
    "social_proof_banner": _render_social_proof_banner,
    "media_mention_card": _render_media_mention_card,
    "expert_endorsement": _render_expert_endorsement,
    "review_callout": _render_review_callout,
    "social_feed_embed": _render_social_feed_embed,
    "footnote_group":    _render_footnote_group,
    "color_swatch_grid": _render_color_swatch_grid,
    "live_demo_embed": _render_live_demo_embed,
    "benchmark_comparison": _render_benchmark_comparison,
    "chartjs_bar": _render_chartjs_bar,
    "chartjs_line": _render_chartjs_line,
    "data_table_sortable": _render_data_table_sortable,
    "donut_stat": _render_donut_stat,
    "heatmap": _render_heatmap,
    "punch_card": _render_punch_card,
    "sankey_flow": _render_sankey_flow,
    "cohort_retention": _render_cohort_retention,
    "task_list": _render_task_list,
    "sentiment_summary": _render_sentiment_summary,
    "conversion_funnel": _render_conversion_funnel,
    "gauge_sla": _render_gauge_sla,
    "stacked_area": _render_stacked_area,
    "scatter_trend": _render_scatter_trend,
    "metric_comparison_card": _render_metric_comparison_card,
    "mini_sparkline_set": _render_mini_sparkline_set,
    "status_dashboard": _render_status_dashboard,
    "uptime_timeline": _render_uptime_timeline,
    "command_palette": _render_command_palette,
    "search_result_card": _render_search_result_card,
    "notification_badge": _render_notification_badge,
    "expandable_list": _render_expandable_list,
    "poll_block": _render_poll_block,
    "abbr_tooltip": _render_abbr_tooltip,
    "copy_to_clipboard": _render_copy_to_clipboard,
    "call_mood_board": _render_call_mood_board,
    "github_activity_grid": _render_github_activity_grid,
    # OpenUI atoms (sourced from github.com/thesysdev/openui, MIT)
    "form":                 _render_form,
    "form_input":           _render_form_input,
    "form_select":          _render_form_select,
    "form_radio_group":     _render_form_radio_group,
    "form_checkbox_group":  _render_form_checkbox_group,
    "form_switch_group":    _render_form_switch_group,
    "form_slider":          _render_form_slider,
    "form_date_picker":     _render_form_date_picker,
    "modal":                _render_modal,
    "follow_up_chips":      _render_follow_up_chips,
    # Vercel Geist-inspired atoms
    "choicebox_group":      _render_choicebox_group,
    "feedback_prompt":      _render_feedback_prompt,
    # Aceternity UI-inspired atoms
    "marquee_strip":         _render_marquee_strip,
    "typewriter_text":       _render_typewriter_text,
    "animated_border_card":  _render_animated_border_card,
    "aurora_background":     _render_aurora_background,
    "dot_grid_background":   _render_dot_grid_background,
    "shimmer_button":        _render_shimmer_button,
    "card_stack":            _render_card_stack,
    "meteor_shower":         _render_meteor_shower,
    # AI-native & original atoms — v201
    "entity_list":          _render_entity_list,
    "prompt_template":      _render_prompt_template,
    "model_card":           _render_model_card,
    "conversation_snippet": _render_conversation_snippet,
    "shortcut_legend":      _render_shortcut_legend,
    "rating_summary_bar":   _render_rating_summary_bar,
    "roadmap_card":         _render_roadmap_card,
    "notification_stack":   _render_notification_stack,
    "inline_alert":         _render_inline_alert,
    "tag_block":            _render_tag_block,
    "variant_selector":     _render_variant_selector,
    "markdown_block":       _render_markdown_block,
    "chartjs_pie":          _render_chartjs_pie,
    "text_callout":         _render_text_callout,
    "source_citation":      _render_source_citation,
    "llm_comparison_table": _render_llm_comparison_table,
    "confidence_bar":       _render_confidence_bar,
    "token_budget_meter":   _render_token_budget_meter,
}


# ── Learning atoms ─────────────────────────────────────────────────────────────

def _render_quiz_question(b: dict) -> str:
    import hashlib
    uid      = "q" + hashlib.md5(str(b).encode()).hexdigest()[:6]
    question = b.get("question", "")
    options  = b.get("options", [])
    correct  = int(b.get("correct", 0))
    explain  = b.get("explanation", "")
    style    = b.get("style", "default")
    bg       = "#0f172a" if style == "dark" else "#fff"
    border   = "#1e293b" if style == "dark" else "#e2e8f0"
    text_col = "#f1f5f9" if style == "dark" else "#1e293b"
    sub_col  = "#94a3b8" if style == "dark" else "#64748b"

    inputs = ""
    labels = ""
    for i, opt in enumerate(options):
        inp_id = f"{uid}_o{i}"
        is_correct = (i == correct)
        correct_css = (
            f'#{inp_id}:checked ~ .{uid}_opts label[for="{inp_id}"]'
            f'{{background:#d1fae5;border-color:#10b981;color:#065f46;font-weight:600;}}'
        ) if is_correct else (
            f'#{inp_id}:checked ~ .{uid}_opts label[for="{inp_id}"]'
            f'{{background:#fee2e2;border-color:#ef4444;color:#991b1b;text-decoration:line-through;opacity:0.7;}}'
        )
        reveal_css = (
            f'#{inp_id}:checked ~ .{uid}_explain{{display:block;}}'
        ) if explain else ""
        inputs += f'<input type="radio" id="{inp_id}" name="{uid}" style="display:none;">'
        inputs += f'<style>{correct_css}{reveal_css}</style>'
        labels += (
            f'<label for="{inp_id}" style="display:block;padding:10px 14px;margin:6px 0;'
            f'border:1.5px solid {border};border-radius:8px;cursor:pointer;'
            f'font-size:0.9rem;color:{text_col};transition:all 0.2s;">'
            f'{opt}</label>'
        )

    explain_html = (
        f'<div class="{uid}_explain" style="display:none;margin-top:12px;padding:12px 14px;'
        f'background:#eff6ff;border-left:3px solid #3b82f6;border-radius:0 6px 6px 0;'
        f'font-size:0.85rem;color:#1e40af;">{explain}</div>'
    ) if explain else ""

    return (
        f'<div style="border:1.5px solid {border};border-radius:12px;padding:20px 24px;'
        f'margin:1.2rem 0;background:{bg};">'
        f'<p style="font-weight:600;font-size:0.95rem;color:{text_col};margin:0 0 14px;">{question}</p>'
        f'{inputs}'
        f'<div class="{uid}_opts">{labels}</div>'
        f'{explain_html}'
        f'<p style="font-size:0.75rem;color:{sub_col};margin:12px 0 0;">Select an option to reveal the answer.</p>'
        f'</div>'
    )


# ── Shopify Polaris atoms ──────────────────────────────────────────────────────

def _render_product_thumbnail(b: dict) -> str:
    title          = b.get("title", "Product")
    vendor         = b.get("vendor", "")
    sku            = b.get("sku", "")
    price          = b.get("price", "")
    compare_price  = b.get("compare_at_price", "")
    status         = b.get("status", "active")
    image_url      = b.get("image_url", "")
    tags           = b.get("tags", [])

    STATUS = {
        "active":   ("#d4edda", "#155724", "Active"),
        "draft":    ("#fff3cd", "#856404", "Draft"),
        "archived": ("#e2e3e5", "#383d41", "Archived"),
    }
    bg, fg, label = STATUS.get(status, STATUS["active"])

    img = (
        f'<img src="{image_url}" alt="{title}" style="width:100%;height:120px;object-fit:cover;border-radius:4px;margin-bottom:12px;">'
        if image_url else
        '<div style="width:100%;height:120px;background:#f4f6f8;border-radius:4px;margin-bottom:12px;display:flex;align-items:center;justify-content:center;color:#8c9196;font-size:24px;">🖼</div>'
    )
    price_html = f'<span style="font-size:18px;font-weight:700;color:#202223;">{price}</span>'
    if compare_price:
        price_html += f'<span style="font-size:14px;color:#8c9196;text-decoration:line-through;margin-left:8px;">{compare_price}</span>'

    tags_html = "".join(
        f'<span style="background:#f1f2f3;color:#6d7175;font-size:11px;padding:2px 8px;border-radius:20px;">{t}</span>'
        for t in tags
    )
    tags_section = f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:10px;">{tags_html}</div>' if tags else ""

    return (
        f'<div style="background:#fff;border:1px solid #e1e3e5;border-radius:8px;padding:16px;max-width:280px;">'
        f'{img}'
        f'<div style="font-size:13px;font-weight:600;color:#202223;margin-bottom:2px;">{title}</div>'
        + (f'<div style="font-size:12px;color:#6d7175;margin-bottom:8px;">{vendor}</div>' if vendor else '')
        + (f'<div style="font-size:11px;color:#8c9196;font-family:monospace;margin-bottom:8px;">SKU: {sku}</div>' if sku else '')
        + f'<div style="margin-bottom:10px;">{price_html}</div>'
        f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px;">{label}</span>'
        f'{tags_section}'
        f'</div>'
    )


def _render_order_status_card(b: dict) -> str:
    order_number = b.get("order_number", "#1001")
    date         = b.get("date", "")
    status       = b.get("status", "unfulfilled")
    customer     = b.get("customer", "")
    items        = b.get("items", [])
    total        = b.get("total", "")

    STATUS = {
        "fulfilled":   ("#d4edda", "#155724"),
        "unfulfilled": ("#fff3cd", "#856404"),
        "partial":     ("#cce5ff", "#004085"),
        "cancelled":   ("#f8d7da", "#721c24"),
        "refunded":    ("#e2e3e5", "#383d41"),
    }
    bg, fg = STATUS.get(status, STATUS["unfulfilled"])

    items_html = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f4f6f8;font-size:13px;">'
        f'<span style="color:#202223;">{item.get("title","")}</span>'
        f'<span style="color:#6d7175;">×{item.get("qty",1)} &mdash; {item.get("price","")}</span>'
        f'</div>'
        for item in items
    )

    return (
        f'<div style="background:#fff;border:1px solid #e1e3e5;border-radius:8px;padding:20px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        f'<span style="font-size:16px;font-weight:700;color:#202223;">{order_number}</span>'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        + (f'<span style="font-size:12px;color:#6d7175;">{date}</span>' if date else '')
        + f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:600;padding:2px 10px;border-radius:20px;">{status.capitalize()}</span>'
        f'</div></div>'
        + (f'<div style="font-size:12px;color:#6d7175;margin-bottom:12px;">Customer: {customer}</div>' if customer else '')
        + (f'<div style="margin-bottom:12px;">{items_html}</div>' if items_html else '')
        + (f'<div style="text-align:right;font-size:15px;font-weight:700;color:#202223;">Total: {total}</div>' if total else '')
        + '</div>'
    )


def _render_inventory_table(b: dict) -> str:
    title = b.get("title", "")
    items = b.get("items", [])

    rows_html = ""
    for item in items:
        available  = item.get("available", 0)
        threshold  = item.get("threshold")
        low_stock  = threshold is not None and available < threshold
        row_bg     = "background:#fff3cd;" if low_stock else ""
        qty_style  = "color:#856404;font-weight:600;" if low_stock else "color:#202223;"
        rows_html += (
            f'<tr style="{row_bg}">'
            f'<td style="padding:10px 12px;font-family:monospace;font-size:12px;color:#6d7175;">{item.get("sku","")}</td>'
            f'<td style="padding:10px 12px;font-size:13px;font-weight:500;color:#202223;">{item.get("product","")}</td>'
            f'<td style="padding:10px 12px;text-align:right;{qty_style}">{available}{"⚠" if low_stock else ""}</td>'
            f'<td style="padding:10px 12px;text-align:right;color:#6d7175;">{item.get("committed","—")}</td>'
            f'<td style="padding:10px 12px;font-size:12px;color:#6d7175;">{item.get("location","—")}</td>'
            f'</tr>'
        )

    title_html = f'<div style="background:#f1f2f3;padding:12px 16px;font-weight:600;font-size:13px;color:#202223;border-bottom:1px solid #e1e3e5;">{title}</div>' if title else ''
    return (
        f'<div style="border:1px solid #e1e3e5;border-radius:8px;overflow:hidden;">'
        f'{title_html}'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        f'<thead><tr style="background:#f6f6f7;border-bottom:1px solid #e1e3e5;">'
        f'<th style="padding:8px 12px;text-align:left;font-size:12px;font-weight:600;color:#6d7175;">SKU</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:12px;font-weight:600;color:#6d7175;">Product</th>'
        f'<th style="padding:8px 12px;text-align:right;font-size:12px;font-weight:600;color:#6d7175;">Available</th>'
        f'<th style="padding:8px 12px;text-align:right;font-size:12px;font-weight:600;color:#6d7175;">Committed</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:12px;font-weight:600;color:#6d7175;">Location</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>'
    )


# ── Atlassian Design System atoms ─────────────────────────────────────────────

def _render_jira_ticket(b: dict) -> str:
    key         = b.get("key", "PROJ-1")
    issue_type  = b.get("issue_type", "task")
    summary     = b.get("summary", "")
    status      = b.get("status", "To Do")
    priority    = b.get("priority", "medium")
    assignee    = b.get("assignee", "")
    description = b.get("description", "")
    labels      = b.get("labels", [])

    TYPE_ICONS = {
        "bug":     ("🐛", "#e34935"),
        "story":   ("📖", "#36b37e"),
        "task":    ("✓",  "#0052cc"),
        "epic":    ("⚡", "#6554c0"),
        "subtask": ("↗",  "#0052cc"),
    }
    icon, _ = TYPE_ICONS.get(issue_type, ("✓", "#0052cc"))

    PRIORITY_ICONS = {
        "highest": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "lowest": "⚪",
    }
    p_icon = PRIORITY_ICONS.get(priority, "🟡")

    STATUS_COLORS = {
        "To Do":      ("#dfe1e6", "#42526e"),
        "In Progress":("#deebff", "#0747a6"),
        "Done":       ("#e3fcef", "#006644"),
        "Blocked":    ("#ffebe6", "#bf2600"),
        "Review":     ("#fffae6", "#172b4d"),
    }
    s_bg, s_fg = STATUS_COLORS.get(status, ("#dfe1e6", "#42526e"))

    labels_html = "".join(
        f'<span style="background:#dfe1e6;color:#172b4d;font-size:11px;padding:2px 6px;border-radius:3px;">{lbl}</span>'
        for lbl in labels
    )

    return (
        f'<div style="background:#fff;border:1px solid #dfe1e6;border-radius:3px;padding:16px;font-family:-apple-system,sans-serif;">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
        f'<span style="font-size:15px;">{icon}</span>'
        f'<span style="font-size:12px;font-weight:600;color:#0052cc;">{key}</span>'
        f'<span style="margin-left:auto;background:{s_bg};color:{s_fg};font-size:10px;font-weight:700;padding:2px 8px;border-radius:3px;text-transform:uppercase;letter-spacing:0.05em;">{status}</span>'
        f'</div>'
        f'<div style="font-size:15px;font-weight:500;color:#172b4d;margin-bottom:10px;line-height:1.4;">{summary}</div>'
        + (f'<div style="font-size:13px;color:#5e6c84;margin-bottom:12px;line-height:1.5;">{description}</div>' if description else '')
        + f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
        f'<span style="font-size:12px;color:#5e6c84;">{p_icon} {priority.capitalize()}</span>'
        + (f'<span style="font-size:12px;color:#5e6c84;">👤 {assignee}</span>' if assignee else '')
        + labels_html
        + '</div></div>'
    )


def _render_sprint_board(b: dict) -> str:
    sprint_name = b.get("sprint_name", "")
    columns     = b.get("columns", [])

    TYPE_ICONS = {
        "bug": "🐛", "story": "📖", "task": "✓", "epic": "⚡", "subtask": "↗",
    }
    PRIORITY_COLORS = {
        "highest": "#e34935", "high": "#ff7a00", "medium": "#f79e1b",
        "low": "#0065ff", "lowest": "#6b778c",
    }

    def render_ticket(t):
        icon    = TYPE_ICONS.get(t.get("type", "task"), "✓")
        p_color = PRIORITY_COLORS.get(t.get("priority", "medium"), "#f79e1b")
        return (
            f'<div style="background:#fff;border:1px solid #dfe1e6;border-radius:3px;padding:10px;margin-bottom:6px;">'
            f'<div style="display:flex;align-items:flex-start;gap:6px;">'
            f'<span style="font-size:11px;flex-shrink:0;margin-top:1px;">{icon}</span>'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="font-size:12px;font-weight:500;color:#172b4d;line-height:1.3;margin-bottom:4px;">{t.get("summary","")}</div>'
            f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<span style="font-size:10px;color:#0052cc;font-weight:600;">{t.get("key","")}</span>'
            f'<span style="width:7px;height:7px;border-radius:50%;background:{p_color};flex-shrink:0;"></span>'
            f'</div></div></div></div>'
        )

    cols_html = ""
    for col in columns:
        items = col.get("items", [])
        cols_html += (
            f'<div style="background:#f4f5f7;border-radius:3px;padding:10px;flex:1;min-width:160px;">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">'
            f'<span style="font-size:11px;font-weight:700;color:#5e6c84;text-transform:uppercase;letter-spacing:0.05em;">{col.get("name","")}</span>'
            f'<span style="background:#dfe1e6;color:#172b4d;font-size:11px;font-weight:600;padding:1px 6px;border-radius:20px;">{len(items)}</span>'
            f'</div>'
            + "".join(render_ticket(t) for t in items)
            + '</div>'
        )

    name_html = f'<div style="font-size:14px;font-weight:700;color:#172b4d;margin-bottom:12px;">{sprint_name}</div>' if sprint_name else ''
    return (
        f'<div style="font-family:-apple-system,sans-serif;">'
        f'{name_html}'
        f'<div style="display:flex;gap:10px;overflow-x:auto;">{cols_html}</div>'
        f'</div>'
    )


def _render_lozenge(b: dict) -> str:
    items = b.get("items")
    if items is None:
        items = [{"text": b.get("text", "Status"), "appearance": b.get("appearance", "default")}]

    APPEARANCES = {
        "default":    ("#dfe1e6", "#172b4d"),
        "success":    ("#e3fcef", "#006644"),
        "removed":    ("#ffebe6", "#bf2600"),
        "inprogress": ("#deebff", "#0747a6"),
        "moved":      ("#fffae6", "#172b4d"),
        "new":        ("#e6fcff", "#008da6"),
    }

    pills = "".join(
        '<span style="display:inline-block;background:{};color:{};font-size:11px;font-weight:700;'
        'padding:2px 8px;border-radius:3px;text-transform:uppercase;letter-spacing:0.05em;">{}</span>'.format(
            *APPEARANCES.get(item.get("appearance", "default"), APPEARANCES["default"]),
            item.get("text", "")
        )
        for item in items
    )
    return f'<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">{pills}</div>'


# ── IBM Carbon Design System atoms ────────────────────────────────────────────

def _render_data_grid(b: dict) -> str:
    title      = b.get("title", "")
    columns    = b.get("columns", [])
    rows       = b.get("rows", [])
    selectable = b.get("selectable", False)
    pagination = b.get("pagination")
    per_page   = (pagination.get("per_page", 10) if pagination else len(rows)) or len(rows) or 10

    # Split rows into pages; if no pagination field, single page
    pages      = [rows[i:i+per_page] for i in range(0, max(len(rows), 1), per_page)] if pagination else [rows]
    multi      = len(pages) > 1
    total      = len(rows)
    uid        = abs(hash(title + str(len(columns)) + str(total) + str(per_page))) % 999983

    STATUS_COLORS = {
        "active":   ("#d4edda", "#155724"), "inactive": ("#e2e3e5", "#383d41"),
        "error":    ("#f8d7da", "#721c24"), "warning":  ("#fff3cd", "#856404"),
    }

    def _header():
        cells = ""
        if selectable:
            cells += '<th style="padding:10px 12px;width:36px;"><input type="checkbox"></th>'
        for col in columns:
            sort = ' <span style="color:#a8b0bd;font-size:10px;">⇅</span>' if col.get("sortable") else ""
            cells += (
                f'<th style="padding:10px 12px;text-align:left;font-size:12px;font-weight:600;'
                f'color:#161616;white-space:nowrap;border-right:1px solid #e0e0e0;">'
                f'{col.get("header","")}{sort}</th>'
            )
        return f'<tr style="background:#e0e0e0;border-bottom:2px solid #8d8d8d;">{cells}</tr>'

    def _tbody(page_rows, offset):
        html = ""
        for i, row in enumerate(page_rows):
            row_bg = "#fff" if (i + offset) % 2 == 0 else "#f4f4f4"
            cells  = '<td style="padding:10px 12px;"><input type="checkbox"></td>' if selectable else ""
            for col in columns:
                key      = col.get("key", "")
                col_type = col.get("type", "string")
                value    = row.get(key, "")
                border   = "border-right:1px solid #e0e0e0;"
                if col_type == "number":
                    cells += f'<td style="padding:10px 12px;text-align:right;font-size:13px;color:#161616;font-variant-numeric:tabular-nums;{border}">{value}</td>'
                elif col_type == "status":
                    sc_bg, sc_fg = STATUS_COLORS.get(str(value).lower(), ("#e2e3e5", "#383d41"))
                    cells += (f'<td style="padding:10px 12px;{border}"><span style="background:{sc_bg};'
                              f'color:{sc_fg};font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px;">{value}</span></td>')
                elif col_type == "tag":
                    cells += (f'<td style="padding:10px 12px;{border}"><span style="background:#d0e2ff;'
                              f'color:#0043ce;font-size:11px;padding:2px 8px;border-radius:3px;">{value}</span></td>')
                else:
                    cells += f'<td style="padding:10px 12px;font-size:13px;color:#161616;{border}">{value}</td>'
            html += f'<tr style="background:{row_bg};border-bottom:1px solid #e0e0e0;">{cells}</tr>'
        return html

    title_html = f'<div style="background:#161616;color:#fff;padding:12px 16px;font-size:14px;font-weight:600;">{title}</div>' if title else ''

    if not multi:
        # Simple render — no CSS pagination needed
        return (
            f'<div style="border:1px solid #e0e0e0;font-family:-apple-system,sans-serif;overflow:hidden;">'
            f'{title_html}'
            f'<table style="width:100%;border-collapse:collapse;">'
            f'<thead>{_header()}</thead>'
            f'<tbody>{_tbody(rows, 0)}</tbody>'
            f'</table>'
            f'<div style="padding:8px 16px;background:#f4f4f4;font-size:12px;color:#525252;">{total} items</div>'
            f'</div>'
        )

    # ── CSS-radio tab pagination ───────────────────────────────────────────────
    # Radio inputs must be siblings of the wrapper so ~ selector reaches inside it
    n = len(pages)
    css = (
        f'<style>'
        # hide all pages
        f'.dg{uid}pg{{display:none;}}'
        # show/highlight active page via checked radio
        + "".join(
            f'#dg{uid}r{i}:checked~.dg{uid}w .dg{uid}pg{i}{{display:block;}}'
            f'#dg{uid}r{i}:checked~.dg{uid}w .dg{uid}lbl{i}'
            f'{{background:#0043ce!important;color:#fff!important;}}'
            for i in range(n)
        )
        + f'.dg{uid}lbl{{display:inline-flex;align-items:center;justify-content:center;'
        f'width:28px;height:28px;border-radius:3px;cursor:pointer;font-size:12px;'
        f'font-weight:600;background:#e0e0e0;color:#525252;margin:0 2px;}}'
        f'</style>'
    )
    radios = "".join(
        f'<input type="radio" id="dg{uid}r{i}" name="dg{uid}" {"checked" if i==0 else ""} style="display:none;">'
        for i in range(n)
    )
    pages_html = "".join(
        f'<div class="dg{uid}pg dg{uid}pg{i}">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead>{_header()}</thead>'
        f'<tbody>{_tbody(pg, i * per_page)}</tbody>'
        f'</table></div>'
        for i, pg in enumerate(pages)
    )
    labels = "".join(
        f'<label for="dg{uid}r{i}" class="dg{uid}lbl dg{uid}lbl{i}">{i+1}</label>'
        for i in range(n)
    )
    footer = (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:10px 16px;border-top:1px solid #e0e0e0;background:#f4f4f4;">'
        f'<span style="font-size:12px;color:#525252;">{total} items &nbsp;·&nbsp; {n} pages</span>'
        f'<div>{labels}</div>'
        f'</div>'
    )

    return (
        f'{css}{radios}'
        f'<div class="dg{uid}w" style="border:1px solid #e0e0e0;font-family:-apple-system,sans-serif;overflow:hidden;">'
        f'{title_html}{pages_html}{footer}'
        f'</div>'
    )


def _render_tree_view(b: dict) -> str:
    title = b.get("title", "")
    nodes = b.get("nodes", [])

    def render_node(node, depth=0):
        label    = node.get("label", "")
        icon     = node.get("icon", "")
        meta     = node.get("meta", "")
        children = node.get("children", [])
        expanded = node.get("expanded", True)

        indent_px = depth * 20
        if children:
            expander = "▼" if expanded else "▶"
            exp_html = f'<span style="color:#525252;font-size:9px;width:14px;display:inline-block;flex-shrink:0;">{expander}</span>'
        else:
            exp_html = '<span style="width:14px;display:inline-block;flex-shrink:0;"></span>'

        icon_html = f'<span style="margin-right:4px;">{icon}</span>' if icon else ""
        meta_html = f'<span style="margin-left:auto;font-size:11px;color:#8d8d8d;white-space:nowrap;">{meta}</span>' if meta else ""
        children_html = "".join(render_node(c, depth + 1) for c in children) if (children and expanded) else ""

        return (
            f'<div style="padding-left:{indent_px}px;">'
            f'<div style="display:flex;align-items:center;padding:4px 8px;cursor:pointer;">'
            f'{exp_html}{icon_html}'
            f'<span style="font-size:13px;color:#161616;flex:1;">{label}</span>'
            f'{meta_html}'
            f'</div>'
            f'{children_html}'
            f'</div>'
        )

    title_html = f'<div style="background:#f4f4f4;padding:10px 16px;font-size:13px;font-weight:600;color:#161616;border-bottom:1px solid #e0e0e0;">{title}</div>' if title else ''
    nodes_html = "".join(render_node(n) for n in nodes)

    return (
        f'<div style="border:1px solid #e0e0e0;font-family:-apple-system,sans-serif;overflow:hidden;">'
        f'{title_html}'
        f'<div style="padding:8px 0;">{nodes_html}</div>'
        f'</div>'
    )


def _render_heatmap_calendar(b: dict) -> str:
    import math
    from datetime import date, timedelta
    import calendar as _cal

    title       = b.get("title", "")
    data        = b.get("data", [])
    months      = b.get("months", 3)
    color_scale = b.get("color_scale", ["#f4f4f4", "#d0e2ff", "#4589ff", "#0043ce", "#001d6c"])
    unit        = b.get("unit", "")

    data_dict = {item.get("date", ""): item.get("count", 0) for item in data} if isinstance(data, list) else dict(data)
    max_val = max(data_dict.values(), default=1) or 1

    def get_color(val):
        if val == 0:
            return color_scale[0]
        ratio = val / max_val
        idx = min(int(ratio * (len(color_scale) - 1)) + 1, len(color_scale) - 1)
        return color_scale[idx]

    today = date.today()
    DOW = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

    months_html = ""
    for m_offset in range(months - 1, -1, -1):
        month = today.month - m_offset
        year  = today.year
        while month <= 0:
            month += 12
            year  -= 1

        num_days     = _cal.monthrange(year, month)[1]
        first_dow    = date(year, month, 1).weekday()
        month_abbr   = _cal.month_abbr[month]

        cells = ['<td style="width:16px;height:16px;"></td>'] * first_dow
        for day in range(1, num_days + 1):
            d_str = f"{year}-{month:02d}-{day:02d}"
            count = data_dict.get(d_str, 0)
            color = get_color(count)
            tip   = f'{d_str}: {count}{" "+unit if unit else ""}'
            cells.append(
                f'<td title="{tip}" style="width:16px;height:16px;background:{color};'
                f'border-radius:2px;border:1px solid rgba(0,0,0,0.04);cursor:default;"></td>'
            )
        while len(cells) % 7:
            cells.append('<td style="width:16px;height:16px;"></td>')

        weeks    = [cells[i:i+7] for i in range(0, len(cells), 7)]
        dow_row  = "".join(f'<th style="font-size:8px;color:#8d8d8d;text-align:center;padding:0;width:16px;font-weight:400;">{d}</th>' for d in DOW)
        rows_html = "".join(f'<tr>{"".join(w)}</tr>' for w in weeks)

        months_html += (
            f'<div style="display:inline-block;margin-right:14px;vertical-align:top;">'
            f'<div style="font-size:11px;color:#525252;margin-bottom:6px;text-align:center;">{month_abbr} {year}</div>'
            f'<table style="border-collapse:separate;border-spacing:2px;">'
            f'<thead><tr>{dow_row}</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table></div>'
        )

    legend = (
        '<div style="display:flex;align-items:center;gap:4px;margin-top:12px;">'
        '<span style="font-size:10px;color:#8d8d8d;margin-right:2px;">Less</span>'
        + "".join(f'<span style="width:12px;height:12px;background:{c};border-radius:2px;border:1px solid rgba(0,0,0,0.04);display:inline-block;"></span>' for c in color_scale)
        + '<span style="font-size:10px;color:#8d8d8d;margin-left:2px;">More</span></div>'
    )

    title_html = f'<div style="font-size:14px;font-weight:600;color:#161616;margin-bottom:12px;">{title}</div>' if title else ''
    return (
        f'<div style="font-family:-apple-system,sans-serif;">'
        f'{title_html}'
        f'<div style="overflow-x:auto;">{months_html}</div>'
        f'{legend}'
        f'</div>'
    )


# ── Stage-first atoms ─────────────────────────────────────────────────────────

def _render_media_stream_card(b: dict) -> str:
    import html as _h, re
    url    = b.get("url", "")
    title  = b.get("title", "")
    height = b.get("height", "360px")

    embed_url = _h.escape(url)
    platform  = "Media"

    yt = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]+)', url)
    if yt:
        embed_url = f"https://www.youtube.com/embed/{yt.group(1)}?rel=0"
        platform  = "YouTube"

    loom = re.search(r'loom\.com/share/([a-zA-Z0-9]+)', url)
    if loom:
        embed_url = f"https://www.loom.com/embed/{loom.group(1)}"
        platform  = "Loom"

    slides = re.search(r'docs\.google\.com/presentation/d/([^/]+)', url)
    if slides:
        embed_url = f"https://docs.google.com/presentation/d/{slides.group(1)}/embed?start=false&loop=false"
        platform  = "Google Slides"

    vimeo = re.search(r'vimeo\.com/(\d+)', url)
    if vimeo:
        embed_url = f"https://player.vimeo.com/video/{vimeo.group(1)}"
        platform  = "Vimeo"

    label     = title or platform
    title_html = (
        f'<div style="padding:8px 14px;background:#1e293b;'
        f'font-size:0.78rem;color:#94a3b8;display:flex;align-items:center;gap:6px;">'
        f'<span style="color:#64748b;font-size:0.68rem;">▶</span>'
        f'<span style="font-weight:500;">{_h.escape(label)}</span>'
        f'</div>'
    )
    if not url:
        return (
            f'<div style="margin:1rem 0;border:1px solid #334155;border-radius:8px;overflow:hidden;">'
            f'{title_html}'
            f'<div style="height:{height};background:#0f172a;display:flex;align-items:center;'
            f'justify-content:center;color:#475569;font-size:0.85rem;">No URL provided</div>'
            f'</div>'
        )
    return (
        f'<div style="margin:1rem 0;border:1px solid #334155;border-radius:8px;overflow:hidden;background:#0f172a;">'
        f'{title_html}'
        f'<div style="position:relative;height:{height};background:#0f172a;">'
        f'<iframe src="{embed_url}" '
        f'style="position:absolute;inset:0;width:100%;height:100%;border:none;" '
        f'allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture" '
        f'allowfullscreen sandbox="allow-scripts allow-same-origin allow-popups allow-forms">'
        f'</iframe>'
        f'</div>'
        f'</div>'
    )


def _render_live_aggregator(b: dict) -> str:
    import html as _h
    items     = b.get("items", [])
    title     = b.get("title", "")
    max_val   = b.get("max_value", None)
    show_vals = b.get("show_values", True)

    if not items:
        return ""

    values = []
    for item in items:
        v = item.get("value", item.get("count", item.get("votes", 0)))
        try:
            values.append(float(v))
        except (ValueError, TypeError):
            values.append(0.0)

    auto_max      = max(values) if values else 1
    effective_max = float(max_val) if max_val is not None else auto_max
    if effective_max == 0:
        effective_max = 1

    _C = ["#1a73e8","#34a853","#9c27b0","#ea4335","#fbbc04","#00bcd4","#ff6d00","#00897b"]

    title_html = (
        f'<div style="font-size:0.78rem;font-weight:600;color:#94a3b8;'
        f'text-transform:uppercase;letter-spacing:.07em;margin-bottom:14px;">'
        f'{_h.escape(title)}</div>'
    ) if title else ""

    rows = ""
    for i, (item, val) in enumerate(zip(items, values)):
        label = item.get("label", f"Option {i+1}")
        pct   = min(100.0, (val / effective_max) * 100)
        color = item.get("color", _C[i % len(_C)])
        disp  = int(val) if val == int(val) else round(val, 1)
        val_html = (
            f'<span style="font-size:0.75rem;color:#94a3b8;white-space:nowrap;">{disp}</span>'
        ) if show_vals else ""
        rows += (
            f'<div style="margin-bottom:12px;">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px;">'
            f'<span style="font-size:0.85rem;color:#e2e8f0;font-weight:500;">{_h.escape(label)}</span>'
            f'{val_html}</div>'
            f'<div style="height:8px;background:#1e293b;border-radius:4px;overflow:hidden;">'
            f'<div style="height:100%;width:{pct:.1f}%;background:{color};border-radius:4px;'
            f'transition:width 0.5s ease;"></div>'
            f'</div></div>'
        )
    return (
        f'<div style="margin:1rem 0;padding:18px 20px;background:#0f172a;'
        f'border:1px solid #1e293b;border-radius:12px;">'
        f'{title_html}{rows}'
        f'</div>'
    )


def _render_vote_button_group(b: dict) -> str:
    import html as _h
    options = b.get("options", [])
    style   = b.get("style", "pill")
    title   = b.get("title", "")
    multi   = b.get("allow_multi", False)
    uid     = abs(hash(str(options) + style + title)) % 100000
    inp     = "checkbox" if multi else "radio"
    name    = f"vbg{uid}"

    title_html = (
        f'<div style="font-size:0.78rem;font-weight:600;color:#94a3b8;'
        f'text-transform:uppercase;letter-spacing:.07em;margin-bottom:12px;">'
        f'{_h.escape(title)}</div>'
    ) if title else ""

    if style == "neon":
        css = (
            f'<style>'
            f'.{name} label{{display:inline-block;padding:9px 20px;border-radius:8px;cursor:pointer;'
            f'font-size:0.87rem;font-weight:500;color:#94a3b8;border:1px solid #1e293b;'
            f'background:#0a0f1e;transition:all .18s;}}'
            f'.{name} input:checked+label,.{name} label:hover{{border-color:#00f2ff;color:#00f2ff;'
            f'box-shadow:0 0 10px rgba(0,242,255,.3),inset 0 0 10px rgba(0,242,255,.04);}}'
            f'.{name} input{{display:none;}}'
            f'</style>'
        )
        wrap = "background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px 18px;"
    elif style == "default":
        css = (
            f'<style>'
            f'.{name} label{{display:inline-block;padding:8px 18px;border-radius:6px;cursor:pointer;'
            f'font-size:0.87rem;font-weight:500;color:#3c4043;border:1px solid #dadce0;'
            f'background:#fff;transition:all .15s;}}'
            f'.{name} input:checked+label,.{name} label:hover{{background:#e8f0fe;border-color:#1a73e8;'
            f'color:#1a73e8;font-weight:600;}}'
            f'.{name} input{{display:none;}}'
            f'</style>'
        )
        wrap = "background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;"
    else:
        css = (
            f'<style>'
            f'.{name} label{{display:inline-block;padding:8px 18px;border-radius:20px;cursor:pointer;'
            f'font-size:0.87rem;font-weight:500;color:#cbd5e1;border:1px solid #334155;'
            f'background:#1e293b;transition:all .15s;}}'
            f'.{name} input:checked+label,.{name} label:hover{{background:#1a73e8;border-color:#1a73e8;color:#fff;}}'
            f'.{name} input{{display:none;}}'
            f'</style>'
        )
        wrap = "background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px 18px;"

    btns = ""
    for i, opt in enumerate(options):
        label    = opt.get("label", "")
        value    = opt.get("value", label)
        checked  = "checked" if opt.get("selected", False) else ""
        bid      = f"{name}_{i}"
        btns += (
            f'<span style="display:inline-block;">'
            f'<input type="{inp}" id="{bid}" name="{name}" value="{_h.escape(value)}" {checked}>'
            f'<label for="{bid}">{_h.escape(label)}</label>'
            f'</span>'
        )
    return (
        f'{css}'
        f'<div class="{name}" style="margin:1rem 0;{wrap}">'
        f'{title_html}'
        f'<div style="display:flex;flex-wrap:wrap;gap:8px;">{btns}</div>'
        f'</div>'
    )


def _render_effect_overlay(b: dict) -> str:
    import html as _h
    trigger = b.get("trigger", "confetti")
    status  = b.get("status", "")
    message = b.get("message", "")
    color   = b.get("color", "#00f2ff")
    uid     = abs(hash(trigger + status + message)) % 100000

    status_html = (
        f'<div style="font-size:0.68rem;color:#64748b;text-align:center;padding:6px 0 0;'
        f'text-transform:uppercase;letter-spacing:.09em;">{_h.escape(status)}</div>'
    ) if status else ""

    msg_html = (
        f'<div style="font-size:0.95rem;font-weight:700;color:#fff;z-index:1;margin-top:6px;">'
        f'{_h.escape(message)}</div>'
    ) if message else ""

    if trigger == "pulse":
        css = (
            f'<style>'
            f'@keyframes ep_pulse{uid}{{0%,100%{{transform:scale(1);box-shadow:0 0 0 0 {color}50}}'
            f'50%{{transform:scale(1.06);box-shadow:0 0 0 18px {color}00}}}}'
            f'</style>'
        )
        content = (
            f'<div style="display:flex;align-items:center;justify-content:center;gap:14px;padding:28px 0;">'
            f'<div style="width:44px;height:44px;border-radius:50%;background:{color};flex-shrink:0;'
            f'animation:ep_pulse{uid} 1.6s ease-in-out infinite;"></div>'
            f'{msg_html}'
            f'</div>'
        )
    else:
        _confetti_colors = ["#ff6b6b","#ffd93d","#6bcb77","#4d96ff","#ff6bd6","#00f2ff","#ff8c00","#c084fc"]
        icon = {"trophy": "🏆", "fireworks": "🎆"}.get(trigger, "🎉")
        trophy_anim = (
            f'animation:ep_trophy{uid} 0.5s cubic-bezier(.34,1.56,.64,1) forwards;'
            if trigger == "trophy" else ""
        )
        css = (
            f'<style>'
            f'@keyframes ep_fall{uid}{{0%{{transform:translateY(-10px) rotate(0deg);opacity:1}}'
            f'100%{{transform:translateY(220px) rotate(540deg);opacity:0}}}}'
            f'@keyframes ep_trophy{uid}{{0%{{transform:scale(0) rotate(-12deg);opacity:0}}'
            f'60%{{transform:scale(1.15) rotate(4deg);opacity:1}}'
            f'100%{{transform:scale(1) rotate(0);opacity:1}}}}'
            f'.ep_p{uid}{{position:absolute;border-radius:2px;'
            f'animation:ep_fall{uid} var(--d,1.4s) var(--dl,0s) ease-in forwards;}}'
            f'</style>'
        )
        particles = ""
        for i in range(26):
            c  = _confetti_colors[i % len(_confetti_colors)]
            lp = (i * 37 + 5) % 96
            dl = round((i * 0.07) % 1.1, 2)
            d  = round(1.1 + (i * 0.06) % 0.9, 1)
            w  = 7 if i % 3 == 0 else 9
            h  = 11 if i % 4 == 0 else 7
            r  = (i * 21) % 360
            particles += (
                f'<div class="ep_p{uid}" style="left:{lp}%;background:{c};'
                f'width:{w}px;height:{h}px;--d:{d}s;--dl:{dl}s;'
                f'transform:rotate({r}deg);"></div>'
            )
        content = (
            f'<div style="position:relative;overflow:hidden;height:160px;'
            f'display:flex;align-items:center;justify-content:center;flex-direction:column;">'
            f'<div style="position:absolute;inset:0;pointer-events:none;">{particles}</div>'
            f'<div style="font-size:3.2rem;z-index:1;{trophy_anim}">{icon}</div>'
            f'{msg_html}'
            f'</div>'
        )

    return (
        f'{css}'
        f'<div style="margin:1rem 0;background:#0a0f1e;border:1px solid #1e293b;'
        f'border-radius:14px;overflow:hidden;">'
        f'{status_html}'
        f'{content}'
        f'</div>'
    )


def _render_skeleton_stage_card(b: dict) -> str:
    variant = b.get("variant", "card")
    lines   = max(1, int(b.get("lines", 3)))
    count   = max(1, int(b.get("count", 1)))
    uid     = abs(hash(variant + str(lines) + str(count))) % 100000

    css = (
        f'<style>'
        f'@keyframes ssc_sh{uid}{{0%{{background-position:-200% 0}}'
        f'100%{{background-position:200% 0}}}}'
        f'.ssc{uid}{{background:linear-gradient(90deg,#1e293b 25%,#2d3a4a 50%,#1e293b 75%);'
        f'background-size:200% 100%;animation:ssc_sh{uid} 1.8s infinite linear;border-radius:4px;}}'
        f'</style>'
    )

    def _card():
        line_rows = "".join(
            f'<div class="ssc{uid}" style="height:11px;width:{"70%" if i==lines-1 else "100%"};'
            f'margin-bottom:8px;"></div>'
            for i in range(lines)
        )
        return (
            f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:16px;">'
            f'<div style="display:flex;gap:12px;align-items:flex-start;margin-bottom:14px;">'
            f'<div class="ssc{uid}" style="width:40px;height:40px;border-radius:50%;flex-shrink:0;"></div>'
            f'<div style="flex:1;">'
            f'<div class="ssc{uid}" style="height:12px;width:50%;margin-bottom:7px;"></div>'
            f'<div class="ssc{uid}" style="height:9px;width:32%;"></div>'
            f'</div></div>'
            f'{line_rows}</div>'
        )

    def _list():
        rows = "".join(
            f'<div style="display:flex;align-items:center;gap:10px;padding:9px 0;'
            f'border-bottom:1px solid #1e293b;">'
            f'<div class="ssc{uid}" style="width:32px;height:32px;border-radius:50%;flex-shrink:0;"></div>'
            f'<div style="flex:1;">'
            f'<div class="ssc{uid}" style="height:10px;width:58%;margin-bottom:6px;"></div>'
            f'<div class="ssc{uid}" style="height:8px;width:38%;"></div>'
            f'</div></div>'
            for _ in range(lines)
        )
        return (
            f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px;">'
            f'{rows}</div>'
        )

    def _media():
        return (
            f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;overflow:hidden;">'
            f'<div class="ssc{uid}" style="height:180px;border-radius:0;"></div>'
            f'<div style="padding:12px;">'
            f'<div class="ssc{uid}" style="height:12px;width:68%;margin-bottom:8px;"></div>'
            f'<div class="ssc{uid}" style="height:10px;width:44%;"></div>'
            f'</div></div>'
        )

    def _chat():
        bubbles = ""
        for i in range(lines):
            ml = "margin-left:auto;" if i % 2 == 1 else ""
            r  = "12px 12px 4px 12px" if i % 2 == 1 else "12px 12px 12px 4px"
            bubbles += (
                f'<div style="max-width:62%;{ml}margin-bottom:10px;">'
                f'<div class="ssc{uid}" style="height:38px;border-radius:{r};"></div>'
                f'</div>'
            )
        return (
            f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px;">'
            f'{bubbles}</div>'
        )

    fn = {"list": _list, "media": _media, "chat": _chat}.get(variant, _card)
    cards = "".join(
        f'<div style="{"margin-bottom:10px;" if count>1 else ""}">{fn()}</div>'
        for _ in range(count)
    )
    return f'{css}<div style="margin:1rem 0;">{cards}</div>'


# ── Functional state-driven atoms (Magic UI / CSS-only) ───────────────────────

def _render_word_flip(atom: dict) -> str:
    import hashlib
    words = atom.get("words", [])
    if not words or len(words) < 2:
        return f'<span>{words[0] if words else ""}</span>'
    uid      = hashlib.md5(str(atom).encode()).hexdigest()[:6]
    speed_s  = {"slow": 4.0, "normal": 2.5, "fast": 1.2}.get(atom.get("speed", "normal"), 2.5)
    n        = len(words)
    total    = round(speed_s * n, 2)
    color    = atom.get("color", "#38bdf8")
    size     = atom.get("size", "inherit")
    weight   = atom.get("weight", "700")
    prefix   = atom.get("prefix", "")
    suffix   = atom.get("suffix", "")
    # N+1 spans: words + duplicate first for seamless loop reset
    spans    = "".join(
        f'<span style="display:block;height:1.2em;line-height:1.2em;">{w}</span>'
        for w in [*words, words[0]]
    )
    # translateY target: -N/(N+1)*100% moves through N words; steps(N,end) snaps to each
    target   = round(n / (n + 1) * 100, 4)
    return (
        f'<style>'
        f'@keyframes wf_{uid}{{0%{{transform:translateY(0);}}100%{{transform:translateY(-{target}%);}}}}'
        f'.wfi_{uid}{{animation:wf_{uid} {total}s steps({n},end) infinite;display:block;}}'
        f'</style>'
        f'<span style="font-size:{size};">'
        f'{prefix}'
        f'<span style="display:inline-flex;overflow:hidden;height:1.2em;vertical-align:middle;'
        f'color:{color};font-weight:{weight};">'
        f'<span class="wfi_{uid}">{spans}</span>'
        f'</span>'
        f'{suffix}'
        f'</span>'
    )


def _render_sonar_pulse(atom: dict) -> str:
    import hashlib
    uid     = hashlib.md5(str(atom).encode()).hexdigest()[:6]
    variant = atom.get("variant", "critical")
    active  = atom.get("active", True)
    label   = atom.get("label", "")
    body    = atom.get("body", "")
    size_map = {"sm": 60, "md": 90, "lg": 130}
    sz      = size_map.get(str(atom.get("size", "md")), 90)
    color_map = {
        "critical": "#ef4444", "success": "#34d399",
        "info":     "#38bdf8", "warning": "#f59e0b",
    }
    color = color_map.get(variant, "#ef4444")
    dot_r = max(8, sz // 8)
    label_html = (
        f'<span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);'
        f'font-size:{dot_r - 1}px;font-weight:700;color:{color};z-index:2;'
        f'white-space:nowrap;">{label}</span>'
    ) if label else ""
    body_html = (
        f'<div style="font-size:0.82rem;color:#94a3b8;margin-top:10px;text-align:center;">{body}</div>'
    ) if body else ""
    rings_css = ""
    rings_html = ""
    if active:
        rings_css = (
            f'@keyframes sp_{uid}{{0%{{transform:scale(0.8);opacity:0.55;}}'
            f'100%{{transform:scale(2.6);opacity:0;}}}}'
        )
        rings_html = "".join(
            f'<div style="position:absolute;inset:0;border-radius:50%;'
            f'border:2px solid {color};opacity:0;'
            f'animation:sp_{uid} 3s ease-out {i}s infinite;"></div>'
            for i in range(3)
        )
    return (
        f'<style>{rings_css}</style>'
        f'<div style="display:flex;flex-direction:column;align-items:center;margin:1rem 0;">'
        f'<div style="position:relative;width:{sz}px;height:{sz}px;">'
        f'{rings_html}'
        f'<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);'
        f'width:{dot_r*2}px;height:{dot_r*2}px;border-radius:50%;background:{color};'
        f'box-shadow:0 0 {dot_r*2}px {color}88;z-index:1;"></div>'
        f'{label_html}'
        f'</div>{body_html}</div>'
    )


# ── Motion-primitive atoms (Magic UI-inspired, CSS-only) ──────────────────────

def _render_blur_fade_in(atom: dict) -> str:
    import hashlib
    uid       = hashlib.md5(str(atom).encode()).hexdigest()[:6]
    speed_map = {"slow": "1.2s", "normal": "0.7s", "fast": "0.35s"}
    dur       = speed_map.get(atom.get("speed", "normal"), "0.7s")
    delay     = atom.get("delay", "0s")
    blur      = atom.get("blur", "8px")
    bg        = atom.get("background", "transparent")
    direction = atom.get("direction", "up")
    drift_map = {
        "up":    "translateY(16px)", "down":  "translateY(-16px)",
        "left":  "translateX(16px)", "right": "translateX(-16px)",
        "none":  "translateY(0)",
    }
    from_transform = drift_map.get(direction, "translateY(16px)")
    title = atom.get("title", "")
    body  = atom.get("body", "")
    title_html = f'<div style="font-size:1.1rem;font-weight:700;color:#f1f5f9;margin-bottom:8px;">{title}</div>' if title else ""
    body_html  = f'<div style="font-size:0.9rem;color:#94a3b8;line-height:1.65;">{body}</div>' if body else ""
    content    = title_html + body_html if (title or body) else '<div style="font-size:0.9rem;color:#94a3b8;">Content fades in with blur reveal.</div>'
    return (
        f'<style>'
        f'@keyframes bfi_{uid}{{from{{opacity:0;filter:blur({blur});transform:{from_transform};}}'
        f'to{{opacity:1;filter:blur(0);transform:translate(0);}}}}'
        f'.bfi_{uid}{{animation:bfi_{uid} {dur} ease-out {delay} both;'
        f'background:{bg};border-radius:12px;padding:24px 28px;margin:1rem 0;}}'
        f'</style>'
        f'<div class="bfi_{uid}">{content}</div>'
    )


def _render_glow_button(atom: dict) -> str:
    import hashlib
    uid        = hashlib.md5(str(atom).encode()).hexdigest()[:6]
    label      = atom.get("label", "Button")
    state      = atom.get("state", "ready")
    href       = atom.get("href", "")
    color_r    = atom.get("color_ready", "#38bdf8")
    color_f    = atom.get("color_fired", "#34d399")
    desc       = atom.get("description", "")
    size_map   = {"sm": ("12px 22px", "13px"), "md": ("14px 28px", "15px"), "lg": ("18px 36px", "17px")}
    pad, fsize = size_map.get(atom.get("size", "md"), ("14px 28px", "15px"))
    if state == "disabled":
        bg, shadow, cursor, pulse = "#374151", "0 0 0 transparent", "not-allowed", ""
        text_color = "#6b7280"
    elif state == "fired":
        bg        = "#0f2e1e"
        shadow    = f"0 0 16px {color_f}, 0 0 32px {color_f}44"
        cursor    = "default"
        text_color = color_f
        pulse      = (
            f'@keyframes gb_pulse_{uid}{{0%,100%{{box-shadow:{shadow};}} '
            f'50%{{box-shadow:0 0 8px {color_f}88;}}}}'
            f'.gb_{uid}{{animation:gb_pulse_{uid} 1.8s ease-in-out infinite;}}'
        )
    else:  # ready
        bg        = "#0c1e2e"
        shadow    = f"0 0 14px {color_r}, 0 0 28px {color_r}44"
        cursor    = "pointer"
        text_color = color_r
        pulse      = (
            f'@keyframes gb_pulse_{uid}{{0%,100%{{box-shadow:{shadow};}} '
            f'50%{{box-shadow:0 0 6px {color_r}66;}}}}'
            f'.gb_{uid}{{animation:gb_pulse_{uid} 2.4s ease-in-out infinite;}}'
        )
    desc_html = f'<div style="font-size:12px;color:#6b7280;margin-top:6px;text-align:center;">{desc}</div>' if desc else ""
    tag = "a" if href else "button"
    href_attr = f' href="{href}"' if href else ""
    return (
        f'<style>'
        f'.gb_{uid}{{display:inline-block;background:{bg};color:{text_color};'
        f'font-size:{fsize};font-weight:600;padding:{pad};border-radius:8px;'
        f'border:1px solid {text_color}44;box-shadow:{shadow};cursor:{cursor};'
        f'text-decoration:none;transition:box-shadow 0.2s;}}'
        f'{pulse}</style>'
        f'<div style="margin:1rem 0;display:inline-block;">'
        f'<{tag} class="gb_{uid}"{href_attr}>{label}</{tag}>{desc_html}'
        f'</div>'
    )


def _render_animated_beam(atom: dict) -> str:
    import hashlib
    uid      = hashlib.md5(str(atom).encode()).hexdigest()[:6]
    from_lbl = atom.get("from_label", "Source")
    to_lbl   = atom.get("to_label", "Target")
    label    = atom.get("label", "")
    body     = atom.get("body", "")
    active   = atom.get("active", True)
    color    = atom.get("color", "#38bdf8")
    curved   = atom.get("curved", True)
    speed_map = {"slow": "3s", "normal": "1.8s", "fast": "1s"}
    dur      = speed_map.get(atom.get("speed", "normal"), "1.8s")
    # SVG layout constants
    W, H, NR = 340, 90, 18
    lx, rx   = NR + 10, W - NR - 10
    cy       = H // 2
    ctrl     = f"M{lx},{cy} C{lx+70},{cy-30} {rx-70},{cy-30} {rx},{cy}" if curved else f"M{lx},{cy} L{rx},{cy}"
    path_len = 260  # approximate
    anim_css = (
        f'@keyframes beam_{uid}{{0%{{stroke-dashoffset:{path_len};opacity:0;}}'
        f'10%{{opacity:1;}}90%{{opacity:1;}}100%{{stroke-dashoffset:0;opacity:0;}}}}'
        f'.bm_{uid}{{stroke-dasharray:{path_len};stroke-dashoffset:{path_len};'
        f'animation:beam_{uid} {dur} linear infinite;}}'
    ) if active else ""
    label_html = f'<div style="font-size:12px;font-weight:600;color:#64748b;margin-bottom:6px;letter-spacing:.05em;text-transform:uppercase;">{label}</div>' if label else ""
    body_html  = f'<div style="font-size:0.85rem;color:#94a3b8;margin-top:6px;">{body}</div>' if body else ""
    return (
        f'<style>{anim_css}</style>'
        f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:14px;'
        f'padding:20px 24px;margin:1rem 0;">'
        f'{label_html}'
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'style="display:block;max-width:100%;">'
        # path track
        f'<path d="{ctrl}" fill="none" stroke="{color}22" stroke-width="2"/>'
        # animated beam dot
        f'<path class="bm_{uid}" d="{ctrl}" fill="none" stroke="{color}" '
        f'stroke-width="2.5" stroke-linecap="round"/>'
        # nodes
        f'<circle cx="{lx}" cy="{cy}" r="{NR}" fill="#1e293b" stroke="{color}" stroke-width="2"/>'
        f'<circle cx="{rx}" cy="{cy}" r="{NR}" fill="#1e293b" stroke="{color}" stroke-width="2"/>'
        # labels inside nodes (truncated)
        f'<text x="{lx}" y="{cy+1}" text-anchor="middle" dominant-baseline="middle" '
        f'font-size="9" font-family="monospace" fill="{color}">{from_lbl[:6]}</text>'
        f'<text x="{rx}" y="{cy+1}" text-anchor="middle" dominant-baseline="middle" '
        f'font-size="9" font-family="monospace" fill="{color}">{to_lbl[:6]}</text>'
        f'</svg>'
        f'{body_html}</div>'
    )


def _render_encrypted_reveal(atom: dict) -> str:
    import hashlib, random, string
    uid      = hashlib.md5(str(atom).encode()).hexdigest()[:6]
    text     = atom.get("text", "LOADING")
    size     = atom.get("size", "28px")
    weight   = atom.get("weight", "700")
    color    = atom.get("color", "#f1f5f9")
    s_color  = atom.get("scramble_color", "#38bdf8")
    delay    = atom.get("delay", "0s")
    frames   = min(max(atom.get("frames", 8), 3), 20)
    bg       = atom.get("background", "transparent")
    speed_map = {"slow": "2.4s", "normal": "1.4s", "fast": "0.8s"}
    total_dur = speed_map.get(atom.get("speed", "normal"), "1.4s")
    rng      = random.Random(uid)
    charset  = string.ascii_uppercase + string.digits + "@#$%&*"
    # Build CSS @keyframes: each frame step shows one scrambled string,
    # final step shows the real text.
    pct_step = 100 // (frames + 1)
    kf_stops = []
    for i in range(frames):
        scrambled = "".join(rng.choice(charset) for _ in text)
        pct       = i * pct_step
        kf_stops.append(
            f'{pct}%{{content:"{scrambled}";color:{s_color};}}'
        )
    kf_stops.append(f'100%{{content:"{text}";color:{color};}}')
    kf_body = "".join(kf_stops)
    pad = "24px 28px" if bg != "transparent" else "0"
    br  = "12px" if bg != "transparent" else "0"
    return (
        f'<style>'
        f'@keyframes er_{uid}{{{kf_body}}}'
        f'.er_{uid}::after{{content:"{text}";font-size:{size};font-weight:{weight};'
        f'color:{color};letter-spacing:.04em;font-family:monospace;'
        f'animation:er_{uid} {total_dur} steps(1,end) {delay} forwards;}}'
        f'.er_wrap_{uid}{{background:{bg};border-radius:{br};padding:{pad};margin:1rem 0;}}'
        f'</style>'
        f'<div class="er_wrap_{uid}"><span class="er_{uid}"></span></div>'
    )


# Late-register Tier-2 vendor atoms (defined above, after _RENDERERS dict)
_RENDERERS.update({
    # Shopify Polaris (MIT)
    "product_thumbnail":    _render_product_thumbnail,
    "order_status_card":    _render_order_status_card,
    "inventory_table":      _render_inventory_table,
    # Atlassian Design System (Apache-2.0)
    "jira_ticket":          _render_jira_ticket,
    "sprint_board":         _render_sprint_board,
    "lozenge":              _render_lozenge,
    # IBM Carbon Design System (Apache-2.0)
    "data_grid":            _render_data_grid,
    "tree_view":            _render_tree_view,
    "heatmap_calendar":     _render_heatmap_calendar,
    # React/Tailwind ecosystem (shadcn/ui, Radix, Tailwind UI patterns)
    "combobox":             _render_combobox,
    "feature_grid":         _render_feature_grid,
    "navigation_menu":      _render_navigation_menu,
    "multi_select_input":   _render_multi_select_input,
    "otp_input":            _render_otp_input,
    "bento_grid":           _render_bento_grid,
    "cta_section":          _render_cta_section,
    "animated_counter":     _render_animated_counter,
    # Functional state-driven atoms
    "word_flip":            _render_word_flip,
    "sonar_pulse":          _render_sonar_pulse,
    # Motion-primitive atoms (Magic UI-inspired)
    "blur_fade_in":         _render_blur_fade_in,
    "glow_button":          _render_glow_button,
    "animated_beam":        _render_animated_beam,
    "encrypted_reveal":     _render_encrypted_reveal,
    # Stage-first atoms
    "media_stream_card":    _render_media_stream_card,
    "live_aggregator":      _render_live_aggregator,
    "vote_button_group":    _render_vote_button_group,
    "effect_overlay":       _render_effect_overlay,
    "skeleton_stage_card":  _render_skeleton_stage_card,
})

# ── Animation atoms ───────────────────────────────────────────────────────────

def _render_typewriter(b: dict) -> str:
    import hashlib
    uid      = hashlib.md5(str(b).encode()).hexdigest()[:6]
    text     = b.get("text", "Hello, world.")
    speed    = {"slow": 120, "normal": 60, "fast": 30}.get(b.get("speed", "normal"), 60)
    n        = len(text)
    dur      = round(n * speed / 1000, 2)
    cursor   = b.get("cursor", True)
    color    = b.get("color", "#0f172a")
    size     = b.get("size", "1.4rem")
    weight   = b.get("weight", "600")
    bg       = b.get("background", "#f8fafc")
    cursor_css = (
        f'@keyframes tw_blink_{uid}{{0%,100%{{border-color:transparent}}50%{{border-color:{color}}}}}'
        f'.tw_{uid}{{border-right:2px solid {color};animation:tw_{uid} {dur}s steps({n},end) forwards,'
        f'tw_blink_{uid} 0.75s step-end {dur}s infinite;}}'
    ) if cursor else (
        f'.tw_{uid}{{animation:tw_{uid} {dur}s steps({n},end) forwards;}}'
    )
    escaped = text.replace("'", "\\'")
    return (
        f'<style>'
        f'@keyframes tw_{uid}{{from{{width:0}}to{{width:{n}ch}}}}'
        f'{cursor_css}'
        f'</style>'
        f'<div style="padding:20px 24px;background:{bg};border-radius:10px;'
        f'border:1px solid #e2e8f0;margin:1rem 0;font-family:monospace;">'
        f'<span class="tw_{uid}" style="display:inline-block;overflow:hidden;'
        f'white-space:nowrap;font-size:{size};font-weight:{weight};color:{color};">'
        f'{text}</span></div>'
    )


def _render_number_odometer(b: dict) -> str:
    import hashlib
    uid    = hashlib.md5(str(b).encode()).hexdigest()[:6]
    value  = str(b.get("value", "1337"))
    label  = b.get("label", "")
    color  = b.get("color", "#0f172a")
    accent = b.get("accent", "#4f46e5")
    size   = b.get("size", "3rem")
    dur    = float(b.get("duration", 1.2))
    digits_html = ""
    for i, ch in enumerate(value):
        if ch.isdigit():
            d = int(ch)
            delay = round(i * 0.08, 2)
            strip = "".join(f'<div style="height:1.1em;line-height:1.1em;">{n}</div>' for n in range(10))
            digits_html += (
                f'<style>'
                f'@keyframes od_{uid}_{i}{{from{{transform:translateY(0)}}to{{transform:translateY(-{d * 10}%)}}}}'
                f'</style>'
                f'<div style="overflow:hidden;height:1.1em;">'
                f'<div style="animation:od_{uid}_{i} {dur}s cubic-bezier(.4,0,.2,1) {delay}s both;">'
                f'{strip}</div></div>'
            )
        else:
            digits_html += f'<div style="padding:0 2px;">{ch}</div>'
    label_html = f'<div style="font-size:0.8rem;color:#64748b;margin-top:6px;letter-spacing:0.05em;text-transform:uppercase;">{label}</div>' if label else ""
    return (
        f'<div style="display:inline-flex;flex-direction:column;align-items:center;'
        f'padding:20px 28px;background:#fff;border:1px solid #e2e8f0;border-radius:12px;margin:1rem 0;">'
        f'<div style="display:flex;align-items:center;font-size:{size};font-weight:800;'
        f'color:{color};font-family:monospace;gap:1px;">'
        f'{digits_html}</div>'
        f'{label_html}</div>'
    )


def _render_typing_indicator(b: dict) -> str:
    import hashlib
    uid     = hashlib.md5(str(b).encode()).hexdigest()[:6]
    name    = b.get("name", "Agent")
    variant = b.get("variant", "dark")
    bg      = "#1e293b" if variant == "dark" else "#f1f5f9"
    dot_col = "#94a3b8" if variant == "dark" else "#64748b"
    text_col= "#94a3b8" if variant == "dark" else "#64748b"
    return (
        f'<style>'
        f'@keyframes ti_bounce_{uid}{{0%,80%,100%{{transform:translateY(0)}}40%{{transform:translateY(-6px)}}}}'
        f'.ti_dot_{uid}{{width:8px;height:8px;border-radius:50%;background:{dot_col};display:inline-block;margin:0 2px;}}'
        f'.ti_dot_{uid}:nth-child(1){{animation:ti_bounce_{uid} 1.2s ease-in-out 0s infinite;}}'
        f'.ti_dot_{uid}:nth-child(2){{animation:ti_bounce_{uid} 1.2s ease-in-out 0.2s infinite;}}'
        f'.ti_dot_{uid}:nth-child(3){{animation:ti_bounce_{uid} 1.2s ease-in-out 0.4s infinite;}}'
        f'</style>'
        f'<div style="display:flex;align-items:flex-end;gap:8px;margin:1rem 0;">'
        f'<div style="width:32px;height:32px;border-radius:50%;background:{dot_col};'
        f'display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;'
        f'color:#fff;flex-shrink:0;">{name[0].upper()}</div>'
        f'<div style="display:flex;flex-direction:column;gap:3px;">'
        f'<span style="font-size:11px;color:{text_col};font-weight:500;">{name}</span>'
        f'<div style="background:{bg};border-radius:18px 18px 18px 4px;padding:12px 16px;'
        f'display:inline-flex;align-items:center;gap:2px;">'
        f'<span class="ti_dot_{uid}"></span>'
        f'<span class="ti_dot_{uid}"></span>'
        f'<span class="ti_dot_{uid}"></span>'
        f'</div></div></div>'
    )


def _render_countdown_timer(b: dict) -> str:
    import hashlib
    uid     = hashlib.md5(str(b).encode()).hexdigest()[:6]
    hours   = int(b.get("hours", 0))
    minutes = int(b.get("minutes", 4))
    seconds = int(b.get("seconds", 59))
    label   = b.get("label", "")
    variant = b.get("variant", "dark")
    bg      = "#0a0f1e" if variant == "dark" else "#fff"
    border  = "#1e293b" if variant == "dark" else "#e2e8f0"
    txt     = "#f1f5f9" if variant == "dark" else "#0f172a"
    sub_col = "#64748b"
    accent  = b.get("accent", "#00f2ff")

    def segment(val, lbl):
        d0, d1 = val // 10, val % 10
        return (
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:4px;">'
            f'<div style="display:flex;gap:4px;">'
            + "".join(
                f'<div style="width:44px;height:60px;background:{bg};border:1px solid {border};'
                f'border-radius:6px;display:flex;align-items:center;justify-content:center;'
                f'font-size:2rem;font-weight:800;color:{txt};font-family:monospace;">{d}</div>'
                for d in [d0, d1]
            )
            + f'</div>'
            f'<span style="font-size:10px;color:{sub_col};text-transform:uppercase;letter-spacing:0.1em;">{lbl}</span>'
            f'</div>'
        )

    sep = f'<div style="font-size:2rem;font-weight:800;color:{accent};padding-bottom:16px;align-self:flex-end;padding-right:2px;">:</div>'
    parts = []
    if hours:
        parts.append(segment(hours, "hrs"))
        parts.append(sep)
    parts.append(segment(minutes, "min"))
    parts.append(sep)
    parts.append(segment(seconds, "sec"))

    label_html = f'<div style="font-size:0.82rem;color:{sub_col};margin-top:10px;letter-spacing:0.06em;">{label}</div>' if label else ""
    return (
        f'<div style="display:inline-flex;flex-direction:column;align-items:center;'
        f'padding:24px 28px;background:{bg};border:1px solid {border};border-radius:14px;margin:1rem 0;">'
        f'<div style="display:flex;align-items:center;gap:8px;">'
        + "".join(parts)
        + f'</div>{label_html}</div>'
    )


def _render_gradient_text(b: dict) -> str:
    import hashlib
    uid    = hashlib.md5(str(b).encode()).hexdigest()[:6]
    text   = b.get("text", "Build something beautiful.")
    from_c = b.get("from", "#4f46e5")
    to_c   = b.get("to", "#06b6d4")
    via    = b.get("via", "")
    size   = b.get("size", "2rem")
    weight = b.get("weight", "800")
    dur    = float(b.get("duration", 4))
    grad   = f"{from_c}, {via}, {to_c}" if via else f"{from_c}, {to_c}"
    return (
        f'<style>'
        f'@keyframes gt_{uid}{{0%,100%{{background-position:0% 50%}}50%{{background-position:100% 50%}}}}'
        f'.gt_{uid}{{background:linear-gradient(90deg,{grad},{from_c});background-size:200% auto;'
        f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'
        f'animation:gt_{uid} {dur}s ease infinite;}}'
        f'</style>'
        f'<div style="margin:1rem 0;padding:16px 0;">'
        f'<span class="gt_{uid}" style="font-size:{size};font-weight:{weight};line-height:1.2;">'
        f'{text}</span></div>'
    )


def _render_reveal_on_scroll(b: dict) -> str:
    import hashlib
    uid       = hashlib.md5(str(b).encode()).hexdigest()[:6]
    title     = b.get("title", "Revealed on scroll")
    body      = b.get("body", "This content fades in as you scroll it into view using the Intersection Observer API.")
    direction = b.get("direction", "up")
    dur       = float(b.get("duration", 0.7))
    drift_map = {"up": "translateY(32px)", "down": "translateY(-32px)", "left": "translateX(32px)", "right": "translateX(-32px)"}
    from_t    = drift_map.get(direction, "translateY(32px)")
    bg        = b.get("background", "#f8fafc")
    accent    = b.get("accent", "#4f46e5")
    return (
        f'<style>'
        f'.ros_{uid}{{opacity:0;transform:{from_t};transition:opacity {dur}s ease,transform {dur}s ease;}}'
        f'.ros_{uid}.visible{{opacity:1;transform:translate(0);}}'
        f'</style>'
        f'<div class="ros_{uid}" style="padding:24px 28px;background:{bg};border-left:3px solid {accent};'
        f'border-radius:0 10px 10px 0;margin:1rem 0;">'
        f'<div style="font-weight:700;color:#0f172a;margin-bottom:6px;">{title}</div>'
        f'<div style="font-size:0.9rem;color:#64748b;line-height:1.6;">{body}</div>'
        f'</div>'
        f'<script>(function(){{var el=document.currentScript.previousElementSibling;'
        f'if(!el)return;'
        f'var io=new IntersectionObserver(function(entries){{entries.forEach(function(e){{if(e.isIntersecting){{e.target.classList.add("visible");io.unobserve(e.target);}}}})}},{{"threshold":0.15}});'
        f'io.observe(el);}})();</script>'
    )


def _render_word_scramble(b: dict) -> str:
    import hashlib, random
    uid    = hashlib.md5(str(b).encode()).hexdigest()[:6]
    text   = b.get("text", "A2UI")
    dur    = float(b.get("duration", 2.0))
    color  = b.get("color", "#0f172a")
    scramble_color = b.get("scramble_color", "#4f46e5")
    size   = b.get("size", "2.5rem")
    weight = b.get("weight", "800")
    n      = len(text)
    chars  = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&"
    frames = 10
    rng    = random.Random(uid)
    keyframe_steps = []
    for f in range(frames):
        pct = round(f / frames * 100)
        revealed = int(f / frames * n)
        scrambled = "".join(
            text[i] if i < revealed else rng.choice(chars)
            for i in range(n)
        )
        keyframe_steps.append(f'{pct}%{{content:"{scrambled}"}}')
    keyframe_steps.append(f'100%{{content:"{text}"}}')
    return (
        f'<style>'
        f'@keyframes ws_{uid}{{{";".join(keyframe_steps)}}}'
        f'.ws_{uid}::after{{content:"{text}";animation:ws_{uid} {dur}s steps({frames},end) forwards;}}'
        f'</style>'
        f'<div style="margin:1rem 0;padding:16px 0;">'
        f'<span class="ws_{uid}" style="font-size:{size};font-weight:{weight};'
        f'color:{color};font-family:monospace;letter-spacing:0.04em;">'
        f'<span style="display:none;">{text}</span>'
        f'</span></div>'
    )


def _render_svg_path_draw(b: dict) -> str:
    import hashlib
    uid   = hashlib.md5(str(b).encode()).hexdigest()[:6]
    color = b.get("color", "#4f46e5")
    dur   = float(b.get("duration", 1.5))
    label = b.get("label", "")
    label_html = f'<div style="font-size:0.8rem;color:#64748b;text-align:center;margin-top:4px;">{label}</div>' if label else ""

    # Text mode — SVG <text> stroke-dashoffset draw animation
    text = b.get("text", "")
    if text:
        font_size   = int(b.get("font_size", 48))
        weight      = b.get("weight", "900")
        font         = b.get("font", "monospace")
        char_by_char = b.get("letter_by_letter", False)

        char_w = font_size * 0.62   # monospace char width estimate
        vw     = max(len(text) * char_w + font_size * 0.4, 200)
        vh     = font_size * 1.6
        y      = font_size * 1.1

        if char_by_char:
            # Each character drawn sequentially with staggered delay
            char_dur  = dur / max(len(text), 1)     # time per character
            char_len  = int(font_size * 2.8)         # estimated stroke length per glyph
            chars_svg = []
            for i, ch in enumerate(text):
                delay = i * char_dur
                cid   = f"c{i}_{uid}"
                x     = font_size * 0.2 + i * char_w + char_w / 2
                chars_svg.append(
                    f'<style>'
                    f'@keyframes sc_{cid}{{from{{stroke-dashoffset:{char_len}}}to{{stroke-dashoffset:0}}}}'
                    f'.sc_{cid}{{stroke-dasharray:{char_len};stroke-dashoffset:{char_len};fill:none;'
                    f'animation:sc_{cid} {char_dur:.3f}s ease-out {delay:.3f}s forwards;}}'
                    f'</style>'
                    f'<text class="sc_{cid}" x="{x:.1f}" y="{y:.1f}" text-anchor="middle" '
                    f'font-size="{font_size}" font-weight="{weight}" font-family="{font}" '
                    f'stroke="{color}" stroke-width="1.5">{ch}</text>'
                )
            return (
                f'<div style="display:flex;flex-direction:column;align-items:center;margin:1rem 0;overflow-x:auto;">'
                f'<svg viewBox="0 0 {vw:.0f} {vh:.0f}" width="100%" style="max-width:{vw:.0f}px;">'
                + "".join(chars_svg) +
                f'</svg>{label_html}</div>'
            )

        # Single-element draw (whole text at once)
        length = int(len(text) * font_size * 0.85)
        return (
            f'<style>'
            f'@keyframes spt_{uid}{{from{{stroke-dashoffset:{length}}}to{{stroke-dashoffset:0}}}}'
            f'.spt_{uid}{{stroke-dasharray:{length};stroke-dashoffset:{length};fill:none;'
            f'animation:spt_{uid} {dur}s ease-out forwards;}}'
            f'</style>'
            f'<div style="display:flex;flex-direction:column;align-items:center;margin:1rem 0;overflow-x:auto;">'
            f'<svg viewBox="0 0 {vw:.0f} {vh:.0f}" width="100%" style="max-width:{vw:.0f}px;">'
            f'<text class="spt_{uid}" x="{vw/2:.0f}" y="{y:.0f}" '
            f'text-anchor="middle" font-size="{font_size}" font-weight="{weight}" '
            f'font-family="{font}" stroke="{color}" stroke-width="1.5">'
            f'{text}</text></svg>'
            f'{label_html}</div>'
        )

    # Shape mode
    width  = int(b.get("width", 3))
    shape  = b.get("shape", "arrow")

    # Tree — multi-path sequential draw
    if shape == "tree":
        # (path_d, approx_length, stroke_width)  — drawn trunk→branches→twigs
        segments = [
            ("M 100 220 L 100 155",    65, 4),   # trunk
            ("M 100 185 L 58 148",     55, 3),   # mid-left
            ("M 100 185 L 142 148",    55, 3),   # mid-right
            ("M 100 155 L 100 108",    47, 3),   # upper trunk
            ("M 100 130 L 48 92",      60, 2.5), # left main
            ("M 100 130 L 152 92",     60, 2.5), # right main
            ("M 48 92  L 22 62",       38, 2),   # left-left
            ("M 48 92  L 62 58",       36, 2),   # left-right
            ("M 152 92 L 138 58",      36, 2),   # right-left
            ("M 152 92 L 178 62",      38, 2),   # right-right
            ("M 100 108 L 72 72",      44, 2),   # top-left
            ("M 100 108 L 128 72",     44, 2),   # top-right
            ("M 100 108 L 100 68",     40, 2),   # top-center
            ("M 100 68  L 84 44",      28, 1.5), # apex-left
            ("M 100 68  L 116 44",     28, 1.5), # apex-right
            ("M 72 72   L 58 50",      27, 1.5), # twig ll
            ("M 128 72  L 142 50",     27, 1.5), # twig rr
        ]
        total     = sum(s[1] for s in segments)
        seg_parts = []
        t = 0.0
        for i, (pd, plen, sw) in enumerate(segments):
            delay    = t / total * dur
            seg_dur  = plen / total * dur
            sid      = f"tr{i}_{uid}"
            seg_parts.append(
                f'<style>'
                f'@keyframes {sid}{{from{{stroke-dashoffset:{plen}}}to{{stroke-dashoffset:0}}}}'
                f'</style>'
                f'<path stroke-dasharray="{plen}" stroke-dashoffset="{plen}" fill="none" '
                f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" '
                f'style="animation:{sid} {seg_dur:.3f}s ease-out {delay:.3f}s forwards;" d="{pd}"/>'
            )
            t += plen
        return (
            f'<div style="display:flex;flex-direction:column;align-items:center;margin:1rem 0;">'
            f'<svg viewBox="0 0 200 230" width="220" height="230">'
            + "".join(seg_parts) +
            f'</svg>{label_html}</div>'
        )

    if shape == "iso_city":
        import math
        u   = int(b.get("unit", 20))
        s32 = math.sqrt(3) / 2
        ox, oy = 220, 195
        vw, vh = 440, 290

        grid_data = b.get("grid", [
            (0,0,3),(1,0,5),(2,0,2),(3,0,4),
            (0,1,4),(1,1,7),(2,1,3),(3,1,2),
            (0,2,2),(1,2,4),(2,2,6),(3,2,3),
            (0,3,5),(1,3,3),(2,3,4),(3,3,2),
        ])
        # painter's order: back → front
        grid_sorted = sorted(grid_data, key=lambda b: (b[0]+b[1]))

        def iso_pts(*coords):
            out = []
            for ix, iy, iz in coords:
                sx = ox + (ix - iy) * u * s32
                sy = oy + (ix + iy) * u * 0.5 - iz * u
                out.append(f"{sx:.1f},{sy:.1f}")
            return " ".join(out)

        def poly(pts, fill, stroke, sw=1.2):
            return f'<polygon points="{iso_pts(*pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'

        parts  = []
        n      = len(grid_sorted)
        stagger = dur * 0.8 / n
        b_dur   = dur * 0.35

        for i, (gx, gy, h) in enumerate(grid_sorted):
            bid   = f"ic{i}_{uid}"
            delay = i * stagger
            # right wall (x=gx+1)
            rf = poly([(gx+1,gy,0),(gx+1,gy,h),(gx+1,gy+1,h),(gx+1,gy+1,0)],
                      "rgba(0,40,70,0.92)", "#0369a1", 1)
            # left wall (y=gy+1)
            lf = poly([(gx,gy+1,0),(gx,gy+1,h),(gx+1,gy+1,h),(gx+1,gy+1,0)],
                      "rgba(0,65,105,0.88)", "#0891b2", 1)
            # top face
            tf = poly([(gx,gy,h),(gx+1,gy,h),(gx+1,gy+1,h),(gx,gy+1,h)],
                      "rgba(0,210,240,0.18)", color, 1.8)
            parts.append(
                f'<style>@keyframes {bid}{{from{{opacity:0;transform:translateY(10px)}}'
                f'to{{opacity:1;transform:translateY(0)}}}}</style>'
                f'<g style="animation:{bid} {b_dur:.2f}s ease-out {delay:.2f}s both;">'
                + rf + lf + tf + '</g>'
            )

        return (
            f'<div style="display:flex;flex-direction:column;align-items:center;margin:1rem 0;">'
            f'<svg viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}">'
            + "".join(parts) +
            f'</svg>{label_html}</div>'
        )

    if shape == "neural_net":
        import math
        layers     = b.get("layers", [3, 5, 5, 2])
        r          = int(b.get("node_radius", 11))
        edge_color = b.get("edge_color", "#1e3a5f")
        vw, vh     = 400, 300
        circ       = int(2 * math.pi * r) + 1

        # Compute node positions
        n_layers = len(layers)
        xs = [vw * (i + 1) / (n_layers + 1) for i in range(n_layers)]
        nodes = []   # (layer, x, y)
        for li, (x, count) in enumerate(zip(xs, layers)):
            for ni in range(count):
                y = vh * (ni + 1) / (count + 1)
                nodes.append((li, x, y))

        parts = []
        t = 0.0
        node_phase = 0.35 * dur   # first 35% of duration: nodes appear
        edge_phase = 0.65 * dur   # remaining 65%: edges draw in layer order

        # ── Phase 1: nodes (circles) ──────────────────────────────────────
        n_nodes = len(nodes)
        for idx, (li, x, y) in enumerate(nodes):
            delay    = node_phase * idx / n_nodes
            seg_dur  = node_phase / n_nodes + 0.15
            nid      = f"nn{idx}_{uid}"
            # layer colour: input=cyan, hidden=purple, output=green
            ncol = [color, "#a78bfa", "#a78bfa", "#34d399"]
            nc   = ncol[li] if li < len(ncol) else color
            parts.append(
                f'<style>@keyframes {nid}{{from{{stroke-dashoffset:{circ};opacity:0}}'
                f'to{{stroke-dashoffset:0;opacity:1}}}}</style>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="rgba(0,0,0,0.6)" '
                f'stroke="{nc}" stroke-width="2" '
                f'stroke-dasharray="{circ}" stroke-dashoffset="{circ}" '
                f'style="animation:{nid} {seg_dur:.3f}s ease-out {delay:.3f}s forwards;opacity:0;"/>'
            )

        # ── Phase 2: edges, drawn layer by layer ──────────────────────────
        # Collect edges grouped by layer transition
        layer_edges = []
        for li in range(n_layers - 1):
            from_n = [(x, y) for (l, x, y) in nodes if l == li]
            to_n   = [(x, y) for (l, x, y) in nodes if l == li + 1]
            for fx, fy in from_n:
                for tx, ty in to_n:
                    layer_edges.append((li, fx, fy, tx, ty))

        n_edges     = len(layer_edges)
        # Spread edges evenly across edge_phase, but stagger within each layer
        layer_starts = {}
        for li in range(n_layers - 1):
            layer_starts[li] = node_phase + edge_phase * li / (n_layers - 1)

        layer_edge_counts = {}
        for li, *_ in layer_edges:
            layer_edge_counts[li] = layer_edge_counts.get(li, 0) + 1

        layer_edge_idx = {li: 0 for li in range(n_layers - 1)}
        layer_edge_dur = edge_phase / (n_layers - 1)

        for eidx, (li, fx, fy, tx, ty) in enumerate(layer_edges):
            elen     = math.sqrt((tx - fx) ** 2 + (ty - fy) ** 2)
            elen_i   = int(elen) + 1
            count_in_layer = layer_edge_counts[li]
            idx_in_layer   = layer_edge_idx[li]
            delay    = layer_starts[li] + layer_edge_dur * idx_in_layer / count_in_layer
            seg_dur  = layer_edge_dur / count_in_layer + 0.12
            eid      = f"ne{eidx}_{uid}"
            layer_edge_idx[li] += 1
            parts.append(
                f'<style>@keyframes {eid}{{from{{stroke-dashoffset:{elen_i};opacity:0}}'
                f'to{{stroke-dashoffset:0;opacity:0.35}}}}</style>'
                f'<line x1="{fx:.1f}" y1="{fy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" '
                f'stroke="{edge_color}" stroke-width="1" '
                f'stroke-dasharray="{elen_i}" stroke-dashoffset="{elen_i}" '
                f'style="animation:{eid} {seg_dur:.3f}s ease-out {delay:.3f}s forwards;opacity:0;"/>'
            )

        return (
            f'<div style="display:flex;flex-direction:column;align-items:center;margin:1rem 0;">'
            f'<svg viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}">'
            + "".join(parts) +
            f'</svg>{label_html}</div>'
        )

    shapes = {
        "arrow":    ("M 20 60 L 80 60 L 65 45 M 80 60 L 65 75", 100, 100),
        "check":    ("M 20 55 L 42 78 L 80 28",                   100, 100),
        "circle":   ("M 50 10 A 40 40 0 1 1 49.9 10",             100, 100),
        "zigzag":   ("M 10 50 L 30 20 L 50 50 L 70 20 L 90 50",   100, 70),
        "infinity": ("M 35 50 C 35 30 10 30 10 50 C 10 70 35 70 50 50 C 65 30 90 30 90 50 C 90 70 65 70 50 50", 100, 100),
    }
    path_d, vw, vh = shapes.get(shape, shapes["arrow"])
    length = {"arrow": 110, "check": 80, "circle": 252, "zigzag": 140, "infinity": 200}.get(shape, 150)
    return (
        f'<style>'
        f'@keyframes sp_{uid}{{from{{stroke-dashoffset:{length}}}to{{stroke-dashoffset:0}}}}'
        f'.sp_{uid}{{stroke-dasharray:{length};stroke-dashoffset:{length};'
        f'animation:sp_{uid} {dur}s ease-out forwards;}}'
        f'</style>'
        f'<div style="display:flex;flex-direction:column;align-items:center;margin:1rem 0;">'
        f'<svg viewBox="0 0 {vw} {vh}" width="160" height="160" fill="none" '
        f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">'
        f'<path class="sp_{uid}" d="{path_d}"/></svg>'
        f'{label_html}</div>'
    )


def _render_toast_notification(b: dict) -> str:
    import hashlib
    uid     = hashlib.md5(str(b).encode()).hexdigest()[:6]
    title   = b.get("title", "Changes saved")
    message = b.get("message", "Your updates have been applied successfully.")
    variant = b.get("variant", "success")
    pos     = b.get("position", "bottom-right")
    color_map = {"success": "#22c55e", "error": "#ef4444", "info": "#3b82f6", "warning": "#f59e0b"}
    icon_map  = {"success": "✓", "error": "✕", "info": "ℹ", "warning": "⚠"}
    accent = color_map.get(variant, "#22c55e")
    icon   = icon_map.get(variant, "✓")
    pos_css = {"bottom-right": "bottom:20px;right:20px", "bottom-left": "bottom:20px;left:20px",
               "top-right": "top:20px;right:20px", "top-left": "top:20px;left:20px"}.get(pos, "bottom:20px;right:20px")
    from_t  = "translateX(120%)" if "right" in pos else "translateX(-120%)"
    return (
        f'<style>'
        f'@keyframes tn_in_{uid}{{from{{transform:{from_t};opacity:0}}to{{transform:translateX(0);opacity:1}}}}'
        f'@keyframes tn_out_{uid}{{from{{transform:translateX(0);opacity:1}}to{{transform:{from_t};opacity:0}}}}'
        f'.tn_{uid}{{position:fixed;{pos_css};z-index:9999;min-width:280px;max-width:360px;'
        f'background:#fff;border-radius:10px;box-shadow:0 8px 32px rgba(0,0,0,0.12);'
        f'border:1px solid #e2e8f0;padding:14px 16px;display:flex;align-items:flex-start;gap:12px;'
        f'animation:tn_in_{uid} 0.3s ease forwards,tn_out_{uid} 0.3s ease 3.5s forwards;}}'
        f'</style>'
        f'<div style="position:relative;height:80px;margin:1rem 0;border:1px dashed #e2e8f0;'
        f'border-radius:10px;background:#f8fafc;display:flex;align-items:center;justify-content:center;">'
        f'<span style="font-size:0.8rem;color:#94a3b8;">Toast appears fixed in viewport →</span>'
        f'</div>'
        f'<div class="tn_{uid}">'
        f'<div style="width:28px;height:28px;border-radius:50%;background:{accent};flex-shrink:0;'
        f'display:flex;align-items:center;justify-content:center;font-size:14px;color:#fff;font-weight:700;">{icon}</div>'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="font-size:0.88rem;font-weight:700;color:#0f172a;margin-bottom:2px;">{title}</div>'
        f'<div style="font-size:0.8rem;color:#64748b;line-height:1.4;">{message}</div>'
        f'</div></div>'
    )


def _render_parallax_card(b: dict) -> str:
    import hashlib
    uid     = hashlib.md5(str(b).encode()).hexdigest()[:6]
    title   = b.get("title", "Parallax Card")
    body    = b.get("body", "Hover to see the 3D tilt effect.")
    badge   = b.get("badge", "")
    accent  = b.get("accent", "#4f46e5")
    bg      = b.get("background", "#0f172a")
    depth   = int(b.get("depth", 15))
    return (
        f'<style>'
        f'.pc_{uid}{{background:{bg};border-radius:16px;padding:28px;margin:1rem 0;'
        f'max-width:320px;border:1px solid rgba(255,255,255,0.08);'
        f'box-shadow:0 20px 60px rgba(0,0,0,0.3);transform-style:preserve-3d;'
        f'transition:transform 0.15s ease,box-shadow 0.15s ease;cursor:default;'
        f'perspective:800px;}}'
        f'.pc_{uid}:hover{{box-shadow:0 30px 80px rgba(0,0,0,0.4);}}'
        f'.pc_inner_{uid}{{transform-style:preserve-3d;}}'
        f'.pc_badge_{uid}{{display:inline-block;background:{accent};color:#fff;'
        f'font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;'
        f'margin-bottom:14px;transform:translateZ(20px);}}'
        f'.pc_title_{uid}{{font-size:1.25rem;font-weight:800;color:#f1f5f9;margin-bottom:8px;'
        f'transform:translateZ(30px);display:block;}}'
        f'.pc_body_{uid}{{font-size:0.85rem;color:#94a3b8;line-height:1.6;transform:translateZ(15px);display:block;}}'
        f'</style>'
        f'<div class="pc_{uid}">'
        f'<div class="pc_inner_{uid}">'
        + (f'<div class="pc_badge_{uid}">{badge}</div>' if badge else '')
        + f'<span class="pc_title_{uid}">{title}</span>'
        f'<span class="pc_body_{uid}">{body}</span>'
        f'</div></div>'
        f'<script>(function(){{'
        f'var c=document.currentScript.previousElementSibling;'
        f'if(!c)return;'
        f'c.addEventListener("mousemove",function(e){{'
        f'var r=c.getBoundingClientRect();'
        f'var x=(e.clientX-r.left)/r.width-0.5;'
        f'var y=(e.clientY-r.top)/r.height-0.5;'
        f'c.style.transform="perspective(800px) rotateY("+x*{depth}+"deg) rotateX("+(-y*{depth})+"deg) scale(1.02)";'
        f'}});'
        f'c.addEventListener("mouseleave",function(){{'
        f'c.style.transform="perspective(800px) rotateY(0) rotateX(0) scale(1)";'
        f'}});}})();</script>'
    )


def _render_hint_reveal(b: dict) -> str:
    import hashlib
    uid    = "hr" + hashlib.md5(str(b).encode()).hexdigest()[:6]
    hint   = b.get("hint", "")
    label  = b.get("label", "Show hint")
    accent = b.get("accent", "#6366f1")
    return (
        f'<details style="margin:0.8rem 0;border-left:3px solid {accent};'
        f'padding:8px 14px;border-radius:0 8px 8px 0;background:#f8fafc;">'
        f'<summary style="cursor:pointer;font-size:0.88rem;font-weight:600;'
        f'color:{accent};list-style:none;user-select:none;">💡 {label}</summary>'
        f'<p style="margin:8px 0 0;font-size:0.88rem;color:#475569;line-height:1.6;">{hint}</p>'
        f'</details>'
    )


def _render_match_exercise(b: dict) -> str:
    import hashlib, random as _random
    uid   = "mx" + hashlib.md5(str(b).encode()).hexdigest()[:6]
    pairs = b.get("pairs", [])
    if not pairs:
        return ""
    terms = [p.get("term", "") for p in pairs]
    defs  = [p.get("definition", "") for p in pairs]
    if b.get("shuffle", True):
        defs = defs[:]
        _random.shuffle(defs)

    left_col  = "".join(
        f'<div style="padding:8px 14px;border:1.5px solid #e2e8f0;border-radius:8px;'
        f'margin:4px 0;font-size:0.88rem;color:#1e293b;background:#f8fafc;">{t}</div>'
        for t in terms
    )
    right_col = "".join(
        f'<div style="padding:8px 14px;border:1.5px solid #ddd6fe;border-radius:8px;'
        f'margin:4px 0;font-size:0.88rem;color:#4c1d95;background:#f5f3ff;cursor:grab;">{d}</div>'
        for d in defs
    )
    return (
        f'<div style="margin:1.2rem 0;">'
        f'<p style="font-size:0.78rem;color:#64748b;margin-bottom:8px;">Match each term to its definition.</p>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">'
        f'<div>{left_col}</div><div>{right_col}</div>'
        f'</div></div>'
    )


def _render_fill_in_blank(b: dict) -> str:
    import hashlib, re
    uid      = "fib" + hashlib.md5(str(b).encode()).hexdigest()[:6]
    template = b.get("template", "")
    answers  = b.get("answers", [])
    hint     = b.get("hint", "")
    case_s   = b.get("case_sensitive", False)

    idx = [0]
    def make_input(m):
        i = idx[0]; idx[0] += 1
        ans = answers[i] if i < len(answers) else ""
        accepted = ans if isinstance(ans, list) else [ans]
        accepted_js = "[" + ",".join(f'"{a}"' for a in accepted) + "]"
        flag = "" if case_s else ".toLowerCase()"
        check_js = f'var v=this.value{flag};var ok=[{",".join(repr(a.lower() if not case_s else a) for a in accepted)}].indexOf(v)>-1;this.style.borderColor=ok?"#10b981":"#ef4444";this.style.background=ok?"#d1fae5":"#fee2e2";'
        return (
            f'<input id="{uid}_{i}" type="text" onblur="{check_js}" '
            f'style="border:1.5px solid #cbd5e1;border-radius:6px;padding:4px 8px;'
            f'font-size:0.9em;width:120px;margin:0 4px;transition:all 0.2s;" '
            f'placeholder="___" autocomplete="off"/>'
        )

    body = re.sub(r'\{blank\}', make_input, template)
    hint_html = f'<p style="font-size:0.8rem;color:#64748b;margin-top:10px;">💡 {hint}</p>' if hint else ""
    return (
        f'<div style="border:1.5px solid #e2e8f0;border-radius:12px;padding:20px 24px;margin:1.2rem 0;background:#fff;">'
        f'<p style="font-size:0.95rem;color:#1e293b;margin:0 0 8px;line-height:1.9;">{body}</p>'
        f'{hint_html}'
        f'</div>'
    )


_RENDERERS.update({
    # Animation atoms — added 2026-06-14
    "typewriter":           _render_typewriter,
    "number_odometer":      _render_number_odometer,
    "typing_indicator":     _render_typing_indicator,
    "countdown_timer":      _render_countdown_timer,
    "gradient_text":        _render_gradient_text,
    "reveal_on_scroll":     _render_reveal_on_scroll,
    "word_scramble":        _render_word_scramble,
    "svg_path_draw":        _render_svg_path_draw,
    "toast_notification":   _render_toast_notification,
    "parallax_card":        _render_parallax_card,
    # Learning atoms
    "quiz_question":        _render_quiz_question,
    "fill_in_blank":        _render_fill_in_blank,
    "match_exercise":       _render_match_exercise,
    "hint_reveal":          _render_hint_reveal,
})

def _render_linkedin_post_image(b: dict) -> str:
    mode    = b.get("mode", "conviction_card")
    caption = b.get("caption", "")
    accent  = b.get("accent", "#7c3aed")

    caption_html = (
        f'<p style="font-size:0.75rem;color:#5f6368;margin:10px 0 0;text-align:center;">'
        f'Preview — export as image for LinkedIn</p>'
    )

    if mode == "conviction_card":
        quote   = b.get("quote", "")
        attr    = b.get("attribution", "")
        attr_html = (
            f'<div style="margin-top:24px;font-size:0.85rem;color:{accent};'
            f'font-family:monospace;letter-spacing:0.05em;">{attr}</div>'
        ) if attr else ""
        return (
            f'<div style="aspect-ratio:1.91/1;background:#0f172a;border-radius:12px;'
            f'display:flex;align-items:center;justify-content:center;padding:48px;'
            f'position:relative;overflow:hidden;margin:1.5rem 0;">'
            f'<div style="position:absolute;bottom:0;left:0;right:0;height:4px;'
            f'background:linear-gradient(90deg,{accent},#3b82f6);"></div>'
            f'<div style="text-align:center;max-width:80%;">'
            f'<div style="font-size:clamp(1.1rem,2.5vw,1.8rem);color:#f1f5f9;'
            f'font-weight:700;line-height:1.4;font-style:italic;">&ldquo;{quote}&rdquo;</div>'
            f'{attr_html}'
            f'</div></div>'
            f'{caption_html}'
        )

    if mode == "split_screenshot":
        left  = b.get("left",  {})
        right = b.get("right", {})
        def _panel(side, border_right=False):
            label = side.get("label", "")
            url   = side.get("url", "")
            br    = "border-right:1px solid #e0e0e0;" if border_right else ""
            lbl_html = (
                f'<div style="padding:8px 12px;font-size:0.72rem;font-weight:600;'
                f'color:#5f6368;background:#f1f3f4;border-bottom:1px solid #e0e0e0;'
                f'letter-spacing:0.04em;text-transform:uppercase;">{label}</div>'
            ) if label else ""
            img_html = (
                f'<img src="{url}" alt="{label}" style="width:100%;height:100%;'
                f'object-fit:cover;object-position:top;display:block;"/>'
            ) if url else (
                f'<div style="flex:1;background:#f8f9fa;display:flex;align-items:center;'
                f'justify-content:center;color:#9aa0a6;font-size:0.8rem;">screenshot</div>'
            )
            return (
                f'<div style="flex:1;display:flex;flex-direction:column;{br}overflow:hidden;">'
                f'{lbl_html}{img_html}</div>'
            )
        inner_caption = (
            f'<div style="padding:10px 16px;font-size:0.8rem;color:#5f6368;'
            f'text-align:center;border-top:1px solid #e0e0e0;background:#f8f9fa;">{caption}</div>'
        ) if caption else ""
        return (
            f'<div style="aspect-ratio:1.91/1;border:1px solid #e0e0e0;border-radius:12px;'
            f'overflow:hidden;display:flex;flex-direction:column;margin:1.5rem 0;'
            f'box-shadow:0 2px 8px rgba(0,0,0,0.08);">'
            f'<div style="flex:1;display:flex;overflow:hidden;">'
            f'{_panel(left, border_right=True)}{_panel(right)}'
            f'</div>{inner_caption}</div>'
            f'{caption_html}'
        )

    if mode == "architecture_diagram":
        inputs  = b.get("inputs",  [])
        runtime = b.get("runtime", "Runtime")
        outputs = b.get("outputs", [])
        def _boxes(items, fill, border, color):
            boxes = "".join(
                f'<div style="background:{fill};border:1.5px solid {border};border-radius:8px;'
                f'padding:10px 16px;font-size:0.8rem;font-weight:600;color:{color};'
                f'text-align:center;white-space:nowrap;">{i.get("label","")}</div>'
                for i in items
            )
            return f'<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">{boxes}</div>'
        arrow = '<div style="text-align:center;font-size:1.2rem;color:#9aa0a6;margin:6px 0;">↓</div>'
        runtime_box = (
            f'<div style="background:#1e40af;border:2px solid #3b82f6;border-radius:10px;'
            f'padding:14px 24px;font-size:0.9rem;font-weight:700;color:#fff;'
            f'text-align:center;margin:0 auto;max-width:360px;">{runtime}</div>'
        )
        caption_bar = (
            f'<div style="font-size:0.78rem;color:#5f6368;text-align:center;'
            f'margin-top:12px;font-style:italic;">{caption}</div>'
        ) if caption else ""
        return (
            f'<div style="aspect-ratio:1.91/1;background:#f8f9fa;border:1px solid #e0e0e0;'
            f'border-radius:12px;display:flex;flex-direction:column;align-items:center;'
            f'justify-content:center;padding:32px;margin:1.5rem 0;">'
            f'{_boxes(inputs, "#e8f0fe", "#4285f4", "#1967d2")}'
            f'{arrow}{runtime_box}{arrow}'
            f'{_boxes(outputs, "#e6f4ea", "#34a853", "#1e7e34")}'
            f'{caption_bar}'
            f'</div>'
            f'{caption_html}'
        )

    return f'<div style="color:#9aa0a6;font-style:italic;">Unknown linkedin_post_image mode: {mode}</div>'


_RENDERERS["linkedin_post_image"] = _render_linkedin_post_image


def _stub(atom_type: str):
    def _r(b: dict) -> str:
        label = b.get("title", b.get("name", b.get("label", atom_type)))
        return f'<div style="border:1px dashed #cbd5e1;border-radius:8px;padding:12px 16px;margin:0.8rem 0;color:#94a3b8;font-size:0.82rem;font-style:italic;">{label}</div>'
    return _r

_RENDERERS.update({t: _stub(t) for t in [
    "achievement_badge", "score_summary", "xp_bar", "lesson_nav",
    "course_progress_card", "highlighted_text", "cursor_glow", "cursor_trail",
    "particle_burst", "spotlight_cursor", "magnetic_element", "tilt_card",
    "gradient_heading", "display_quote", "split_stat", "word_reveal",
    "section_label", "count_up_stat", "text_highlight", "reveal_line",
    "canvas_plexus", "spring_nodes", "isometric_mesh", "module_map",
    "knowledge_check", "quiz_result_summary", "scenario_branch",
    "completion_gate", "certification_card", "skill_radar", "badge_showcase",
    "learning_path_selector", "video_checkpoint", "cohort_progress_board",
    "reflection_prompt", "annotation_highlight", "onboarding_stepper",
    "case_study_card", "study_timer", "rubric_card", "spaced_repetition_card",
    "leaderboard_card", "nav_bar", "nav_link",
]})
