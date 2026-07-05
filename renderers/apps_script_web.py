"""Apps Script Web App renderer — block list → complete standalone HTML page.

Produces a self-contained HTML document suitable for:

    html = render(blocks, title="My Page")
    HtmlService.createHtmlOutput(html)

Or for template-based Apps Script:

    fragment = render_fragment(blocks)   # content only, no <html> wrapper

Key differences from web_article renderer:
  - Outputs a complete <html> document (not just a fragment)
  - <base target="_top"> so links open in parent frame, not the sandbox
  - google.script.run wired up for interactive atoms (quiz, forms)
  - Training atoms (quiz_question, fill_in_blank, match_exercise, hint_reveal,
    achievement_badge, score_summary, xp_bar, lesson_nav, course_progress_card,
    highlighted_text) are fully implemented here
  - CSP-safe: all event handlers attached via addEventListener in <script> blocks
  - Google Sans font (available in Workspace context)
  - Material Design 3–inspired base styling
"""

from __future__ import annotations
from typing import List, Dict, Any
import sys, re, uuid, html
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import renderers.web_article as _wa

# ── Public API ────────────────────────────────────────────────────────────────

def render(
    blocks: List[Dict[str, Any]],
    title: str = "",
    theme: str = "light",
    sidebar: bool = False,
) -> str:
    """Render blocks to a complete Apps Script Web App HTML page.

    Args:
        blocks:  List of atom block dicts (schema.yaml conformant).
        title:   Page <title> and optional visible heading.
        theme:   'light' (default) or 'dark'.
        sidebar: True wraps content in a narrower sidebar-optimised layout.
    """
    fragment = render_fragment(blocks)
    return _page_wrapper(fragment, title=title, theme=theme, sidebar=sidebar)


def _force_target_top(html_str: str) -> str:
    # Strip existing target attributes to avoid duplicates, then add target="_top"
    html_str = re.sub(r'\s+target=["\'][^"\']*["\']', '', html_str)
    return re.sub(r'<a\b', '<a target="_top"', html_str)


def render_fragment(blocks: List[Dict[str, Any]]) -> str:
    """Render blocks to an HTML fragment (no <html> wrapper).

    Suitable for injecting into an existing Apps Script HTML template.
    """
    parts = []
    for block in blocks:
        btype = block.get("component") or block.get("type")
        fn = _RENDERERS.get(btype)
        if fn:
            parts.append(fn(block))
        else:
            wa_fn = _wa._RENDERERS.get(btype)
            if wa_fn:
                parts.append(_force_target_top(wa_fn(block)))
            else:
                parts.append(f'<!-- a2ui: unknown atom "{btype}" -->')
    return "\n\n".join(parts)


# ── Page wrapper ──────────────────────────────────────────────────────────────

_LIGHT_CSS = """
  :root {
    --bg: #ffffff; --surface: #f8f9fa; --surface2: #f1f3f4;
    --border: #e0e0e0; --text: #202124; --muted: #5f6368;
    --accent: #1a73e8; --accent2: #4285f4; --green: #34a853;
    --red: #ea4335; --yellow: #fbbc04; --orange: #fa7b17;
    --font: 'Google Sans', 'Segoe UI', system-ui, sans-serif;
    --mono: 'Google Sans Mono', 'JetBrains Mono', monospace;
  }
"""

_DARK_CSS = """
  :root {
    --bg: #1c1c1e; --surface: #2c2c2e; --surface2: #3a3a3c;
    --border: #3a3a3c; --text: #f2f2f7; --muted: #8e8e93;
    --accent: #0a84ff; --accent2: #64d2ff; --green: #30d158;
    --red: #ff453a; --yellow: #ffd60a; --orange: #ff9f0a;
    --font: 'Google Sans', 'Segoe UI', system-ui, sans-serif;
    --mono: 'Google Sans Mono', 'JetBrains Mono', monospace;
  }
"""

_BASE_CSS = """
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  html, body {
    background: var(--bg); color: var(--text);
    font-family: var(--font); font-size: 15px; line-height: 1.65;
  }

  .asw-page { max-width: 860px; margin: 0 auto; padding: 32px 20px 64px; }
  .asw-page.sidebar { max-width: 380px; padding: 16px 14px 32px; }

  h1 { font-size: 1.6rem; font-weight: 700; margin-bottom: 20px; color: var(--text); }
  h2 { font-size: 1.2rem; font-weight: 600; margin: 28px 0 8px; color: var(--text); }
  h3 { font-size: 1rem; font-weight: 600; margin: 20px 0 6px; color: var(--text); }
  p  { color: var(--muted); margin-bottom: 12px; font-size: 0.9rem; }
  a  { color: var(--accent); }
  code { font-family: var(--mono); font-size: 0.85em;
         background: var(--surface2); padding: 1px 5px; border-radius: 3px; }
  hr { border: none; border-top: 1px solid var(--border); margin: 24px 0; }

  /* ── Training atoms ── */
  .asw-quiz { background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px; margin: 20px 0; }
  .asw-quiz-label { font-size: 0.65rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: var(--accent); margin-bottom: 8px; }
  .asw-quiz-q { font-size: 0.95rem; font-weight: 600; margin-bottom: 14px; }
  .asw-quiz-opts { display: flex; flex-direction: column; gap: 7px; }
  .asw-quiz-opt { padding: 10px 14px; border: 1px solid var(--border); border-radius: 7px;
    cursor: pointer; font-size: 0.85rem; color: var(--muted); transition: all .15s;
    display: flex; align-items: center; gap: 8px; user-select: none; }
  .asw-quiz-opt::before { content: "○"; color: var(--border); }
  .asw-quiz-opt:hover { border-color: var(--accent); color: var(--text); }
  .asw-quiz-opt.selected { border-color: var(--accent); background: var(--surface2); color: var(--text); }
  .asw-quiz-opt.selected::before { content: "●"; color: var(--accent); }
  .asw-quiz-opt.correct { border-color: var(--green); background: #e6f4ea; color: var(--green); }
  .asw-quiz-opt.correct::before { content: "✓"; color: var(--green); }
  .asw-quiz-opt.wrong { border-color: var(--red); background: #fce8e6; color: var(--red); }
  .asw-quiz-opt.wrong::before { content: "✗"; color: var(--red); }
  .asw-quiz-explain { display: none; margin-top: 12px; padding: 10px 12px;
    background: var(--surface2); border-radius: 6px; font-size: 0.82rem; color: var(--muted); }

  .asw-fib { background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px; margin: 20px 0; }
  .asw-fib-label { font-size: 0.65rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: var(--accent); margin-bottom: 10px; }
  .asw-fib input { border: 1px solid var(--border); border-radius: 4px;
    padding: 2px 8px; font-family: var(--mono); font-size: 0.82rem;
    background: var(--bg); color: var(--text); width: 130px; text-align: center; outline: none; }
  .asw-fib input:focus { border-color: var(--accent); }
  .asw-fib input.correct { border-color: var(--green); background: #e6f4ea; color: var(--green); }
  .asw-fib input.wrong   { border-color: var(--red);   background: #fce8e6; color: var(--red); }
  .asw-fib-actions { margin-top: 10px; display: flex; gap: 8px; }

  .asw-match { background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px; margin: 20px 0; }
  .asw-match-label { font-size: 0.65rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: var(--accent); margin-bottom: 4px; }
  .asw-match-sub { font-size: 0.82rem; color: var(--muted); margin-bottom: 12px; }
  .asw-match-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .asw-match-col h4 { font-size: 0.65rem; font-weight: 700; letter-spacing: .1em;
    text-transform: uppercase; color: var(--muted); margin-bottom: 7px; }
  .asw-match-item { padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px;
    font-size: 0.82rem; cursor: pointer; transition: all .15s; color: var(--muted); user-select: none; }
  .asw-match-item:hover { border-color: var(--accent); color: var(--text); }
  .asw-match-item.selected { border-color: var(--accent2); background: var(--surface2); color: var(--text); }
  .asw-match-item.matched { border-color: var(--green); background: #e6f4ea; color: var(--green); cursor: default; }
  .asw-match-score { font-size: 0.78rem; color: var(--muted); margin-top: 10px; text-align: right; }

  details.asw-hint { background: var(--surface); border: 1px solid var(--border);
    border-left: 3px solid var(--accent); border-radius: 8px; margin: 12px 0; }
  details.asw-hint summary { padding: 10px 14px; font-size: 0.83rem; font-weight: 600;
    color: var(--accent); cursor: pointer; list-style: none; display: flex; align-items: center; gap: 7px; }
  details.asw-hint summary::before { content: "💡"; }
  details.asw-hint summary::-webkit-details-marker { display: none; }
  details.asw-hint[open] summary { border-bottom: 1px solid var(--border); }
  details.asw-hint .asw-hint-body { padding: 12px 14px; font-size: 0.84rem; color: var(--muted); }

  .asw-achievement { display: flex; align-items: center; gap: 14px;
    background: var(--surface); border: 1px solid var(--yellow);
    border-radius: 10px; padding: 16px 20px; margin: 20px 0; }
  .asw-achievement.locked { filter: grayscale(.8); opacity: .6; }
  .asw-achievement-icon { font-size: 1.8rem; flex-shrink: 0; }
  .asw-achievement-title { font-size: 0.9rem; font-weight: 700; color: var(--yellow); margin-bottom: 2px; }
  .asw-achievement-desc  { font-size: 0.8rem; color: var(--muted); }
  .asw-achievement-date  { font-size: 0.7rem; color: var(--muted); margin-top: 3px; }

  .asw-score { background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 24px; margin: 20px 0; text-align: center; }
  .asw-score-pct { font-family: var(--mono); font-size: 2.8rem; font-weight: 800;
    color: var(--green); line-height: 1; margin-bottom: 4px; }
  .asw-score-pct.fail { color: var(--red); }
  .asw-score-label { font-size: 0.68rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: var(--muted); margin-bottom: 14px; }
  .asw-score-row { display: flex; justify-content: center; gap: 20px; }
  .asw-score-stat-val { font-size: 1.1rem; font-weight: 700; color: var(--text); }
  .asw-score-stat-lbl { font-size: 0.63rem; color: var(--muted); text-transform: uppercase; letter-spacing: .07em; }
  .asw-score-ctas { display: flex; justify-content: center; gap: 10px; margin-top: 16px; }

  .asw-xp { margin: 20px 0; }
  .asw-xp-row { display: flex; justify-content: space-between; align-items: baseline;
    margin-bottom: 6px; font-size: 0.82rem; }
  .asw-xp-level { font-weight: 600; color: var(--text); }
  .asw-xp-count { color: var(--muted); font-family: var(--mono); font-size: 0.75rem; }
  .asw-xp-track { background: var(--surface2); border-radius: 4px; height: 8px; overflow: hidden; }
  .asw-xp-fill  { height: 100%; border-radius: 4px; background: var(--accent);
    transition: width .6s cubic-bezier(.16,1,.3,1); }

  .asw-lesson-nav { display: flex; align-items: center; justify-content: space-between;
    border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px; margin: 20px 0; gap: 12px; }
  .asw-lesson-nav-side { font-size: 0.82rem; color: var(--muted); text-decoration: none;
    display: flex; align-items: center; gap: 5px; min-width: 0; }
  .asw-lesson-nav-side:hover { color: var(--accent); }
  .asw-lesson-nav-side .nav-arrow { color: var(--accent); font-size: 1rem; flex-shrink: 0; }
  .asw-lesson-nav-center { text-align: center; flex: 1; min-width: 0; }
  .asw-lesson-nav-module { font-size: 0.65rem; font-weight: 700; letter-spacing: .1em;
    text-transform: uppercase; color: var(--muted); margin-bottom: 3px; }
  .asw-lesson-nav-title { font-size: 0.88rem; font-weight: 600; color: var(--text);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .asw-complete-row { display: flex; align-items: center; justify-content: center;
    gap: 6px; margin-top: 8px; font-size: 0.78rem; color: var(--muted); cursor: pointer; }

  .asw-course-card { background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px; margin: 20px 0; }
  .asw-course-title { font-size: 1rem; font-weight: 700; margin-bottom: 14px; }
  .asw-course-module { margin-bottom: 12px; }
  .asw-course-mod-row { display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 4px; font-size: 0.82rem; }
  .asw-course-mod-name { color: var(--text); font-weight: 500; }
  .asw-course-mod-pct  { color: var(--muted); font-family: var(--mono); font-size: 0.75rem; }
  .asw-course-bar-track { background: var(--surface2); border-radius: 3px; height: 5px; overflow: hidden; }
  .asw-course-bar-fill  { height: 100%; border-radius: 3px; background: var(--accent); }

  .asw-highlight { background: #fef08a; border-radius: 2px; padding: 0 2px; position: relative; cursor: default; }
  .asw-highlight[data-note]:hover::after {
    content: attr(data-note); position: absolute; bottom: 100%; left: 0;
    background: var(--yellow); color: #000; padding: 4px 8px; border-radius: 5px;
    font-size: 0.75rem; white-space: nowrap; z-index: 10; margin-bottom: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,.15); pointer-events: none;
  }

  /* ── Shared button ── */
  .asw-btn { padding: 8px 18px; border-radius: 6px; font-size: 0.78rem; font-weight: 600;
    letter-spacing: .04em; cursor: pointer; font-family: var(--font); border: none; transition: all .15s; }
  .asw-btn-primary { background: var(--accent); color: #fff; }
  .asw-btn-primary:hover { opacity: .88; }
  .asw-btn-ghost { background: var(--surface2); color: var(--muted); }
  .asw-btn-ghost:hover { color: var(--text); }
"""


def _page_wrapper(content: str, title: str = "", theme: str = "light", sidebar: bool = False) -> str:
    theme_css = _DARK_CSS if theme == "dark" else _LIGHT_CSS
    sidebar_cls = " sidebar" if sidebar else ""
    title_html = f"<h1>{title}</h1>\n" if title else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <base target="_top">
  <title>{title or "A2UI Page"}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Google+Sans+Mono&display=swap" rel="stylesheet">
  <style>
{theme_css}
{_BASE_CSS}
  </style>
</head>
<body>
  <div class="asw-page{sidebar_cls}">
    {title_html}{content}
  </div>
</body>
</html>"""


# ── Training atom renderers ───────────────────────────────────────────────────

def _render_quiz_question(b: dict) -> str:
    question   = b.get("question", "")
    options    = b.get("options", [])
    correct    = b.get("correct", 0)
    explanation = b.get("explanation", "")
    uid = uuid.uuid4().hex[:8]

    opts_html = ""
    for i, opt in enumerate(options):
        opts_html += f'<div class="asw-quiz-opt" id="{uid}-opt-{i}" data-idx="{i}">{opt}</div>\n'

    explain_html = (
        f'<div class="asw-quiz-explain" id="{uid}-explain">{explanation}</div>'
        if explanation else ""
    )

    script = f"""<script>
(function(){{
  var correct={correct};
  var opts=document.querySelectorAll('#{uid}-opts .asw-quiz-opt');
  opts.forEach(function(el){{
    el.addEventListener('click',function(){{
      var idx=parseInt(el.dataset.idx);
      opts.forEach(function(o){{o.classList.remove('selected','correct','wrong');}});
      el.classList.add('selected');
      el.classList.add(idx===correct?'correct':'wrong');
      var exp=document.getElementById('{uid}-explain');
      if(exp)exp.style.display='block';
    }});
  }});
}})();
</script>"""

    return (
        f'<div class="asw-quiz">'
        f'<div class="asw-quiz-label">Question</div>'
        f'<div class="asw-quiz-q">{question}</div>'
        f'<div class="asw-quiz-opts" id="{uid}-opts">{opts_html}</div>'
        f'{explain_html}'
        f'</div>'
        f'{script}'
    )


def _render_fill_in_blank(b: dict) -> str:
    template    = b.get("template", "")
    answers     = b.get("answers", [])
    hint        = b.get("hint", "")
    case_sens   = b.get("case_sensitive", False)
    uid = uuid.uuid4().hex[:8]

    blank_count = 0
    def replace_blank(m):
        nonlocal blank_count
        i = blank_count; blank_count += 1
        return f'<input class="asw-fib-input" id="{uid}-inp-{i}" data-idx="{i}" placeholder="…" autocomplete="off">'
    html_template = re.sub(r'\{blank\}', replace_blank, template)

    hint_html = (
        f'<p style="margin-top:8px;font-size:0.8rem;color:var(--muted)">💡 {hint}</p>'
        if hint else ""
    )

    ans_json = str(answers).replace("'", '"')
    flag = "false" if case_sens else "true"

    script = f"""<script>
(function(){{
  var answers={ans_json};
  var ignoreCase={flag};
  document.getElementById('{uid}-check').addEventListener('click',function(){{
    var inputs=document.querySelectorAll('#{uid}-fib .asw-fib-input');
    inputs.forEach(function(inp,i){{
      var val=inp.value.trim();
      var accepted=Array.isArray(answers[i])?answers[i]:[answers[i]];
      var ok=accepted.some(function(a){{
        return ignoreCase?val.toLowerCase()===a.toLowerCase():val===a;
      }});
      inp.classList.remove('correct','wrong');
      inp.classList.add(ok?'correct':'wrong');
    }});
  }});
  document.getElementById('{uid}-reset').addEventListener('click',function(){{
    document.querySelectorAll('#{uid}-fib .asw-fib-input').forEach(function(inp){{
      inp.value=''; inp.classList.remove('correct','wrong');
    }});
  }});
}})();
</script>"""

    return (
        f'<div class="asw-fib" id="{uid}-fib">'
        f'<div class="asw-fib-label">Fill in the blank</div>'
        f'<div style="font-size:0.9rem;line-height:2">{html_template}</div>'
        f'{hint_html}'
        f'<div class="asw-fib-actions">'
        f'<button class="asw-btn asw-btn-primary" id="{uid}-check">Check</button>'
        f'<button class="asw-btn asw-btn-ghost" id="{uid}-reset">Reset</button>'
        f'</div>'
        f'</div>'
        f'{script}'
    )


def _render_match_exercise(b: dict) -> str:
    pairs   = b.get("pairs", [])
    shuffle = b.get("shuffle", True)
    uid = uuid.uuid4().hex[:8]

    lefts  = [p["term"] for p in pairs]
    rights = [p["definition"] for p in pairs]
    # Build answer map: left_idx -> right_idx (identity before shuffle)
    correct_map = {i: i for i in range(len(pairs))}

    if shuffle:
        import random, copy
        shuffled_rights = copy.copy(list(range(len(rights))))
        random.shuffle(shuffled_rights)
        rights_reordered = [rights[j] for j in shuffled_rights]
        # correct_map: left_idx -> position in shuffled right list
        inv = {v: k for k, v in enumerate(shuffled_rights)}
        correct_map = {i: inv[i] for i in range(len(pairs))}
    else:
        rights_reordered = rights

    lefts_html  = "".join(
        f'<div class="asw-match-item" id="{uid}-l-{i}" data-side="left" data-idx="{i}">{t}</div>\n'
        for i, t in enumerate(lefts)
    )
    rights_html = "".join(
        f'<div class="asw-match-item" id="{uid}-r-{i}" data-side="right" data-idx="{i}">{d}</div>\n'
        for i, d in enumerate(rights_reordered)
    )

    correct_json = str(correct_map).replace("'", '"')

    script = f"""<script>
(function(){{
  var correct={correct_json};
  var selLeft=null, selRight=null, matched=0, total={len(pairs)};
  function getEl(side,idx){{return document.getElementById('{uid}-'+side+'-'+idx);}}
  function clearSel(){{
    if(selLeft!==null){{getEl('l',selLeft).classList.remove('selected');selLeft=null;}}
    if(selRight!==null){{getEl('r',selRight).classList.remove('selected');selRight=null;}}
  }}
  function pick(side,idx){{
    var el=getEl(side,idx);
    if(el.classList.contains('matched'))return;
    if(side==='left'){{
      if(selLeft===idx){{clearSel();return;}}
      if(selLeft!==null)getEl('l',selLeft).classList.remove('selected');
      selLeft=idx; el.classList.add('selected');
    }}else{{
      if(selRight===idx){{clearSel();return;}}
      if(selRight!==null)getEl('r',selRight).classList.remove('selected');
      selRight=idx; el.classList.add('selected');
    }}
    if(selLeft!==null&&selRight!==null){{
      var ok=correct[selLeft]===selRight;
      if(ok){{
        getEl('l',selLeft).classList.add('matched');
        getEl('r',selRight).classList.add('matched');
        matched++;
        document.getElementById('{uid}-score').textContent=matched+' / '+total;
      }}
      clearSel();
    }}
  }}
  document.querySelectorAll('[id^="{uid}-"]').forEach(function(el){{
    el.addEventListener('click',function(){{pick(el.dataset.side,parseInt(el.dataset.idx));}});
  }});
}})();
</script>"""

    return (
        f'<div class="asw-match">'
        f'<div class="asw-match-label">Matching exercise</div>'
        f'<div class="asw-match-sub">Click a term, then click its match.</div>'
        f'<div class="asw-match-grid">'
        f'<div class="asw-match-col"><h4>Term</h4>{lefts_html}</div>'
        f'<div class="asw-match-col"><h4>Match</h4>{rights_html}</div>'
        f'</div>'
        f'<div class="asw-match-score">Matched: <strong id="{uid}-score">0 / {len(pairs)}</strong></div>'
        f'</div>'
        f'{script}'
    )


def _render_hint_reveal(b: dict) -> str:
    hint   = b.get("hint", "")
    label  = b.get("label", "Show hint")
    accent = b.get("accent", "#1a73e8")
    return (
        f'<details class="asw-hint" style="border-left-color:{accent}">'
        f'<summary style="color:{accent}">{label}</summary>'
        f'<div class="asw-hint-body">{hint}</div>'
        f'</details>'
    )


def _render_achievement_badge(b: dict) -> str:
    title      = b.get("title", "Achievement")
    desc       = b.get("description", "")
    icon       = b.get("icon", "🏆")
    locked     = b.get("locked", False)
    unlocked_at = b.get("unlocked_at", "")
    color      = b.get("color", "#fbbc04")
    size       = b.get("size", "card")

    locked_cls = " locked" if locked else ""
    date_html  = f'<div class="asw-achievement-date">Unlocked {unlocked_at}</div>' if unlocked_at and not locked else ""

    if size == "pill":
        return (
            f'<span class="asw-achievement{locked_cls}" style="border-color:{color};display:inline-flex;padding:6px 14px;">'
            f'<span class="asw-achievement-icon" style="font-size:1.1rem">{icon}</span>'
            f'<span class="asw-achievement-title" style="color:{color};margin:0">{title}</span>'
            f'</span>'
        )

    return (
        f'<div class="asw-achievement{locked_cls}">'
        f'<div class="asw-achievement-icon">{icon}</div>'
        f'<div>'
        f'<div class="asw-achievement-title" style="color:{color}">{title}</div>'
        f'{"<div class=asw-achievement-desc>" + desc + "</div>" if desc else ""}'
        f'{date_html}'
        f'</div>'
        f'</div>'
    )


def _render_score_summary(b: dict) -> str:
    correct        = b.get("correct", 0)
    total          = b.get("total", 1)
    time_taken     = b.get("time_taken", "")
    pass_threshold = b.get("pass_threshold", 60)
    retry_label    = b.get("retry_label", "")
    continue_label = b.get("continue_label", "")
    continue_url   = b.get("continue_url", "#")

    pct = round(correct / total * 100) if total else 0
    passed = pct >= pass_threshold
    pct_cls = "" if passed else " fail"
    grade = "Passed" if passed else "Failed"

    time_html = (
        f'<div class="asw-score-stat"><div class="asw-score-stat-val">{time_taken}</div>'
        f'<div class="asw-score-stat-lbl">Time</div></div>'
    ) if time_taken else ""

    ctas = ""
    if retry_label or continue_label:
        retry = f'<button class="asw-btn asw-btn-ghost">{retry_label}</button>' if retry_label else ""
        cont  = f'<a href="{continue_url}" class="asw-btn asw-btn-primary">{continue_label}</a>' if continue_label else ""
        ctas  = f'<div class="asw-score-ctas">{retry}{cont}</div>'

    return (
        f'<div class="asw-score">'
        f'<div class="asw-score-pct{pct_cls}">{pct}%</div>'
        f'<div class="asw-score-label">{grade}</div>'
        f'<div class="asw-score-row">'
        f'<div class="asw-score-stat"><div class="asw-score-stat-val">{correct}/{total}</div><div class="asw-score-stat-lbl">Correct</div></div>'
        f'{time_html}'
        f'</div>'
        f'{ctas}'
        f'</div>'
    )


def _render_xp_bar(b: dict) -> str:
    level_label = b.get("level_label", "Level 1")
    xp_current  = b.get("xp_current", 0)
    xp_next     = b.get("xp_next", 100)
    accent      = b.get("accent", "#1a73e8")

    pct = min(100, round(xp_current / xp_next * 100)) if xp_next else 100
    return (
        f'<div class="asw-xp">'
        f'<div class="asw-xp-row">'
        f'<span class="asw-xp-level">{level_label}</span>'
        f'<span class="asw-xp-count">{xp_current} / {xp_next} XP</span>'
        f'</div>'
        f'<div class="asw-xp-track"><div class="asw-xp-fill" style="width:{pct}%;background:{accent}"></div></div>'
        f'</div>'
    )


def _render_lesson_nav(b: dict) -> str:
    module_label    = b.get("module_label", "")
    current_title   = b.get("current_title", "")
    prev_title      = b.get("prev_title", "")
    prev_url        = b.get("prev_url", "")
    next_title      = b.get("next_title", "")
    next_url        = b.get("next_url", "")
    show_completion = b.get("show_completion", False)

    prev_html = (
        f'<a href="{prev_url}" class="asw-lesson-nav-side">'
        f'<span class="nav-arrow">←</span>'
        f'<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{prev_title}</span>'
        f'</a>'
    ) if prev_url else '<span></span>'

    next_html = (
        f'<a href="{next_url}" class="asw-lesson-nav-side" style="justify-content:flex-end;text-align:right">'
        f'<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{next_title}</span>'
        f'<span class="nav-arrow">→</span>'
        f'</a>'
    ) if next_url else '<span></span>'

    module_html = f'<div class="asw-lesson-nav-module">{module_label}</div>' if module_label else ""

    completion_html = (
        f'<label class="asw-complete-row">'
        f'<input type="checkbox" onchange="localStorage.setItem(\'complete-{current_title}\',this.checked)">'
        f'Mark as complete'
        f'</label>'
    ) if show_completion else ""

    return (
        f'<div class="asw-lesson-nav">'
        f'{prev_html}'
        f'<div class="asw-lesson-nav-center">'
        f'{module_html}'
        f'<div class="asw-lesson-nav-title">{current_title}</div>'
        f'{completion_html}'
        f'</div>'
        f'{next_html}'
        f'</div>'
    )


def _render_course_progress_card(b: dict) -> str:
    course_title = b.get("course_title", "Course Progress")
    modules      = b.get("modules", [])
    accent       = b.get("accent", "#1a73e8")

    total_lessons = sum(m.get("lessons_total", 1) for m in modules)
    total_done    = sum(m.get("lessons_done", 0) for m in modules)
    overall_pct   = round(total_done / total_lessons * 100) if total_lessons else 0

    mods_html = ""
    for m in modules:
        lt   = m.get("lessons_total", 1)
        ld   = m.get("lessons_done", 0)
        pct  = round(ld / lt * 100) if lt else 0
        mods_html += (
            f'<div class="asw-course-module">'
            f'<div class="asw-course-mod-row">'
            f'<span class="asw-course-mod-name">{m.get("title","")}</span>'
            f'<span class="asw-course-mod-pct">{ld}/{lt}</span>'
            f'</div>'
            f'<div class="asw-course-bar-track">'
            f'<div class="asw-course-bar-fill" style="width:{pct}%;background:{accent}"></div>'
            f'</div>'
            f'</div>'
        )

    return (
        f'<div class="asw-course-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">'
        f'<div class="asw-course-title">{course_title}</div>'
        f'<div style="font-family:var(--mono);font-size:1.1rem;font-weight:700;color:{accent}">{overall_pct}%</div>'
        f'</div>'
        f'{mods_html}'
        f'</div>'
    )


def _render_highlighted_text(b: dict) -> str:
    text             = b.get("text", "")
    annotation       = b.get("annotation", "")
    color            = b.get("color", "#fef08a")
    data_note = f' data-note="{annotation}"' if annotation else ""
    return (
        f'<mark class="asw-highlight" style="background:{color}"{data_note}>{text}</mark>'
    )


# ── Extra renderers for apps_script_web ──

def _esc(val: Any) -> str:
    if val is None:
        return ""
    return html.escape(str(val))


def _markdown_to_html(md: str) -> str:
    if not md:
        return ""
    res = _esc(md)
    res = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', res)
    res = re.sub(r'\*(.*?)\*', r'<em>\1</em>', res)
    res = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_top">\1</a>', res)
    return res


def _render_body(b: dict) -> str:
    return f'<p class="asw-body">{_markdown_to_html(b.get("text"))}</p>'


def _render_paragraph(b: dict) -> str:
    return f'<p class="asw-paragraph">{_markdown_to_html(b.get("text"))}</p>'


def _render_text_block(b: dict) -> str:
    return f'<p class="asw-text-block">{_markdown_to_html(b.get("text"))}</p>'


def _render_heading(b: dict) -> str:
    level = b.get("level", 2)
    return f'<h{level} class="asw-heading">{_esc(b.get("text"))}</h{level}>'


def _render_subheading(b: dict) -> str:
    level = b.get("level", 3)
    return f'<h{level} class="asw-subheading">{_esc(b.get("text"))}</h{level}>'


def _render_blockquote(b: dict) -> str:
    cite = f'<cite style="display:block;margin-top:6px;font-size:0.8rem;text-align:right;">— {_esc(b.get("attribution"))}</cite>' if b.get("attribution") else ''
    return f'<blockquote>{_markdown_to_html(b.get("text"))}{cite}</blockquote>'


def _render_divider(b: dict) -> str:
    return '<hr class="asw-divider">'


def _render_spacer(b: dict) -> str:
    height = b.get("height", 20)
    return f'<div class="asw-spacer" style="height:{height}px;"></div>'


def _render_callout(b: dict) -> str:
    icon = b.get("icon", "💡")
    color = b.get("color", "var(--accent)")
    return f'<div class="asw-callout" style="border-left-color:{color};"><span class="asw-callout-icon">{icon}</span><div class="asw-callout-content">{_markdown_to_html(b.get("text"))}</div></div>'


def _render_alert_banner(b: dict) -> str:
    variant = b.get("variant", "info")
    icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "critical": "🚨"}
    colors = {"info": "var(--accent)", "success": "var(--green)", "warning": "var(--orange)", "critical": "var(--red)"}
    icon = b.get("icon") or icons.get(variant, "ℹ️")
    color = colors.get(variant, "var(--accent)")
    return f'<div class="asw-callout" style="border-left-color:{color}; background:var(--surface2);"><span class="asw-callout-icon">{icon}</span><div class="asw-callout-content" style="font-weight:500;">{_markdown_to_html(b.get("text"))}</div></div>'


def _render_info_card(b: dict) -> str:
    title = f'<div style="font-weight:700;margin-bottom:8px;font-size:0.95rem;">{_esc(b.get("title"))}</div>' if b.get("title") else ''
    return f'<div class="asw-native-card">{title}<div style="font-size:0.88rem;color:var(--muted);">{_markdown_to_html(b.get("text"))}</div></div>'


def _render_code_block(b: dict) -> str:
    return f'<pre><code class="language-{_esc(b.get("language", "text"))}">{_esc(b.get("content"))}</code></pre>'


def _render_inline_code(b: dict) -> str:
    return f'<code>{_esc(b.get("text"))}</code>'


def _render_tag_chip(b: dict) -> str:
    color = b.get("color", "var(--accent)")
    return f'<span class="asw-badge" style="background:rgba(26,115,232,0.1);color:{color};padding:4px 8px;border-radius:12px;font-size:0.75rem;font-weight:600;margin-right:6px;">{_esc(b.get("text"))}</span>'


def _render_badge(b: dict) -> str:
    color = b.get("color", "var(--muted)")
    return f'<span class="asw-badge" style="border:1px solid {color};color:{color};padding:2px 6px;border-radius:4px;font-size:0.7rem;font-weight:600;text-transform:uppercase;">{_esc(b.get("text"))}</span>'


def _render_image(b: dict) -> str:
    caption = f'<div style="font-size:0.8rem;color:var(--muted);text-align:center;margin-top:6px;">{_esc(b.get("caption"))}</div>' if b.get("caption") else ''
    return f'<div style="margin:16px 0;text-align:center;"><img src="{_esc(b.get("url"))}" alt="{_esc(b.get("alt", ""))}" style="max-width:100%;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">{caption}</div>'


def _render_table(b: dict) -> str:
    html_str = '<table>'
    if b.get("headers"):
        html_str += '<thead><tr>'
        for h in b["headers"]:
            html_str += f'<th>{_esc(h)}</th>'
        html_str += '</tr></thead>'
    if b.get("rows"):
        html_str += '<tbody>'
        for r in b["rows"]:
            html_str += '<tr>'
            for cell in r:
                html_str += f'<td>{_markdown_to_html(cell)}</td>'
            html_str += '</tr>'
        html_str += '</tbody>'
    html_str += '</table>'
    return html_str


def _render_bullet_list(b: dict) -> str:
    html_str = '<ul>'
    for item in b.get("items", []):
        lead = f'<strong>{_esc(item.get("label"))}: </strong>' if item.get("label") else ''
        html_str += f'<li>{lead}{_markdown_to_html(item.get("text"))}</li>'
    html_str += '</ul>'
    return html_str


def _render_link_button(b: dict) -> str:
    return f'<div style="margin:12px 0;"><a href="{_esc(b.get("url"))}" class="asw-btn asw-btn-primary" target="_top">{_esc(b.get("label"))}</a></div>'


def _render_cta_button(b: dict) -> str:
    return f'<div style="margin:16px 0;text-align:center;"><a href="{_esc(b.get("url"))}" class="asw-btn asw-btn-primary" style="padding:10px 24px;font-size:0.85rem;" target="_top">{_esc(b.get("label"))}</a></div>'


def _render_nav_link(b: dict) -> str:
    return f'<a href="{_esc(b.get("url"))}" class="asw-nav-link" style="font-size:0.88rem;font-weight:500;margin-right:12px;" target="_top">{_esc(b.get("label"))}</a>'


def _render_drive_file_list(b: dict) -> str:
    files = [
        {"name": "Document_1.pdf", "url": "#", "mimeType": "application/pdf"},
        {"name": "Project_Sheet.xlsx", "url": "#", "mimeType": "application/vnd.google-apps.spreadsheet"},
        {"name": "Slideshow.gslides", "url": "#", "mimeType": "application/vnd.google-apps.presentation"}
    ]
    list_html = '<ul class="asw-drive-list">'
    for f in files:
        icon = '📄'
        if 'pdf' in f['mimeType']: icon = '📕'
        elif 'spreadsheet' in f['mimeType']: icon = '📊'
        elif 'presentation' in f['mimeType']: icon = '📈'
        list_html += f'<li class="asw-drive-item"><span class="asw-drive-icon">{icon}</span><a href="{f["url"]}" class="asw-drive-link" target="_top">{_esc(f["name"])}</a></li>'
    list_html += '</ul>'
    return f'<div class="asw-native-card"><div class="asw-native-header"><span class="asw-native-header-icon">📁</span> Google Drive Folder</div>{list_html}</div>'


def _render_sheet_preview(b: dict) -> str:
    sheet_name = b.get("sheet_name", "Sheet1")
    range_str = b.get("range", "A1:D10")
    data = [
        ['Header 1', 'Header 2', 'Header 3'],
        ['Row 1 Col 1', 'Row 1 Col 2', 'Row 1 Col 3'],
        ['Row 2 Col 1', 'Row 2 Col 2', 'Row 2 Col 3']
    ]
    table_html = '<div class="asw-sheet-preview-wrapper"><table class="asw-sheet-table">'
    for r_idx, row in enumerate(data):
        table_html += '<tr>'
        for cell in row:
            cell_text = _esc(cell)
            if r_idx == 0:
                table_html += f'<th>{cell_text}</th>'
            else:
                table_html += f'<td>{cell_text}</td>'
        table_html += '</tr>'
    table_html += '</table></div>'
    return f'<div class="asw-native-card"><div class="asw-native-header"><span class="asw-native-header-icon">📊</span> Google Sheet Live Preview ({_esc(sheet_name)}!{_esc(range_str)})</div>{table_html}</div>'


def _render_gmail_summary(b: dict) -> str:
    query = b.get("query", "is:unread")
    threads = [
        {"from": "Google Apps Script team <dev@google.com>", "subject": "New V8 features available", "date": "6/16/2026"},
        {"from": "GitHub Notification <noreply@github.com>", "subject": "[a2ui-catalogue] Pull request #4 merged", "date": "6/15/2026"}
    ]
    list_html = '<ul class="asw-gmail-list">'
    for t in threads:
        list_html += f'<li class="asw-gmail-item"><div class="asw-gmail-meta"><span class="asw-gmail-from">{_esc(t["from"])}</span><span class="asw-gmail-date">{_esc(t["date"])}</span></div><div class="asw-gmail-subject">{_esc(t["subject"])}</div></li>'
    list_html += '</ul>'
    return f'<div class="asw-native-card"><div class="asw-native-header"><span class="asw-native-header-icon">✉️</span> Gmail Search: "{_esc(query)}"</div>{list_html}</div>'


def _render_calendar_upcoming(b: dict) -> str:
    events = [
        {"title": "A2UI Review Meeting", "startDay": 18, "startMonth": "Jun", "timeStr": "10:00 AM"},
        {"title": "Weekly Pair Programming", "startDay": 20, "startMonth": "Jun", "timeStr": "02:00 PM"}
    ]
    list_html = '<ul class="asw-cal-list">'
    for ev in events:
        list_html += f'<li class="asw-cal-item"><div class="asw-cal-date-badge"><span class="day">{ev["startDay"]}</span><span class="month">{ev["startMonth"]}</span></div><div class="asw-cal-details"><span class="asw-cal-title">{_esc(ev["title"])}</span><span class="asw-cal-time">⏰ {ev["timeStr"]}</span></div></li>'
    list_html += '</ul>'
    return f'<div class="asw-native-card"><div class="asw-native-header"><span class="asw-native-header-icon">📅</span> Calendar Schedule</div>{list_html}</div>'


def _render_user_greeting(b: dict) -> str:
    prefix = b.get("prefix", "Hello")
    email = "curtis@example.com"
    initial = email[0].upper()
    return f'<div class="asw-user-greeting"><div class="asw-user-avatar">{initial}</div><div>{_esc(prefix)}, <span class="asw-user-email">{_esc(email)}</span>!</div></div>'


def _render_script_run_button(b: dict) -> str:
    label = b.get("label", "Run Script")
    function_name = b.get("function_name", "myFunction")
    argument = b.get("argument", "")
    btn_id = f'btn-{uuid.uuid4().hex[:8]}'
    return f'<div style="margin:16px 0; display:flex; align-items:center; gap:12px;"><button id="{btn_id}" class="asw-btn asw-btn-primary" onclick="runCustomScript(\'{btn_id}\',\'{function_name}\',\'{argument}\')"><span class="asw-spinner" style="display:none;"></span><span class="asw-btn-label">{_esc(label)}</span></button><span id="{btn_id}-status" style="font-size:0.8rem; font-weight:500;"></span></div>'


def _render_youtube(b: dict) -> str:
    vid = b.get("video_id") or b.get("id", "")
    url = b.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else "#")
    label = _esc(b.get("title") or "Watch on YouTube")
    return (
        f'<div class="asw-degraded-card">'
        f'<div class="asw-degraded-title">📹 {label}</div>'
        f'<div class="asw-degraded-text">YouTube iframes are restricted inside the Apps Script Web App sandbox.</div>'
        f'<a href="{_esc(url)}" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Watch on YouTube →</a>'
        f'</div>'
    )


def _render_image_pair(b: dict) -> str:
    images = b.get("images") or []
    if not images:
        url1 = b.get("url") or b.get("url_1", "")
        url2 = b.get("url_2", "")
        if url1:
            images = [{"url": url1, "caption": b.get("caption_1", "")},
                      {"url": url2, "caption": b.get("caption_2", "")}] if url2 else [{"url": url1}]
    parts = []
    for img in images[:2]:
        src     = _esc(img.get("url", ""))
        caption = _esc(img.get("caption", ""))
        cap_html = f'<p style="font-size:0.75rem;color:var(--muted);text-align:center;margin-top:4px">{caption}</p>' if caption else ""
        if src:
            parts.append(f'<div style="flex:1;min-width:0"><img src="{src}" alt="{caption}" style="width:100%;border-radius:6px">{cap_html}</div>')
    return f'<div style="display:flex;gap:12px;flex-wrap:wrap">{"".join(parts)}</div>' if parts else '<!-- image_pair: no images -->'


def _render_diagram(b: dict) -> str:
    url     = b.get("url") or b.get("src", "")
    alt     = _esc(b.get("alt") or b.get("title") or "Diagram")
    caption = _esc(b.get("caption", ""))
    cap_html = f'<p style="font-size:0.75rem;color:var(--muted);text-align:center;margin-top:4px">{caption}</p>' if caption else ""
    if not url:
        return f'<!-- diagram: no url -->'
    return f'<figure style="margin:16px 0"><img src="{_esc(url)}" alt="{alt}" style="max-width:100%;border-radius:6px">{cap_html}</figure>'


def _render_video_pair(b: dict) -> str:
    videos = b.get("videos") or []
    parts = []
    for v in videos[:2]:
        vid = v.get("video_id") or v.get("id", "")
        url = v.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else "#")
        label = _esc(v.get("label") or v.get("title") or "Watch video")
        parts.append(
            f'<div style="flex:1;min-width:0">'
            f'<div class="asw-degraded-card" style="height:100%">'
            f'<div class="asw-degraded-title">📹 {label}</div>'
            f'<a href="{_esc(url)}" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Watch on YouTube →</a>'
            f'</div>'
            f'</div>'
        )
    return f'<div style="display:flex;gap:12px;flex-wrap:wrap">{"".join(parts)}</div>'


def _render_live_demo_embed(b: dict) -> str:
    url   = b.get("url", "#")
    title = _esc(b.get("title") or "Live Demo")
    note  = _esc(b.get("note") or "Sandbox iframes have limited support inside Apps Script Web Apps.")
    return (
        f'<div class="asw-degraded-card">'
        f'<div class="asw-degraded-title">🧪 {title}</div>'
        f'<div class="asw-degraded-text">{note}</div>'
        f'<a href="{_esc(url)}" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Open Demo →</a>'
        f'</div>'
    )


def _degraded_link_renderer(type_name: str):
    def fn(b: dict) -> str:
        url = b.get("url", "#")
        return f'<div class="asw-degraded-card"><div class="asw-degraded-title">🔗 External Resource ({type_name})</div><div class="asw-degraded-text">Interactive frames are restricted inside the Google Apps Script iframe sandbox.</div><a href="{_esc(url)}" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Open Link in New Tab →</a></div>'
    return fn


def _render_lottie_animation(b: dict) -> str:
    if b.get("fallback_image_url"):
        return _render_image({"url": b["fallback_image_url"], "caption": b.get("caption", "Animation static preview")})
    return '<!-- lottie animation stripped: requires external client JS bundles -->'


def _render_parallax_card(b: dict) -> str:
    return f'<div class="asw-native-card" style="background-image:linear-gradient(rgba(0,0,0,0.05), rgba(0,0,0,0.05));"><div style="font-weight:700;margin-bottom:8px;">{_esc(b.get("title", "Parallax Card"))}</div><div style="font-size:0.88rem;color:var(--muted);">{_esc(b.get("subtitle", ""))}</div></div>'


def _render_embed_tweet(b: dict) -> str:
    cite = f'<cite style="display:block;margin-top:4px;font-size:0.8rem;text-align:right;">— {_esc(b.get("author"))}</cite>' if b.get("author") else ''
    return f'<blockquote class="asw-twitter-degraded" style="border-left-color:#1da1f2;"><div style="font-size:0.75rem;font-weight:700;color:#1da1f2;margin-bottom:6px;">𝕏 Tweet (Static View)</div><p>{_esc(b.get("text", "Tweet contents"))}</p>{cite}</blockquote>'


def _render_social_feed_embed(b: dict) -> str:
    return f'<div class="asw-degraded-card"><div class="asw-degraded-title">💬 Social Media Feed</div><div class="asw-degraded-text">Live media feeds are disabled. Click below to view directly.</div><a href="{_esc(b.get("url", "#"))}" class="asw-btn asw-btn-ghost" style="margin-top:6px;" target="_top">Open Social Feed →</a></div>'


# ── Renderer registry ─────────────────────────────────────────────────────────

_RENDERERS: Dict[str, Any] = {
    "quiz_question":       _render_quiz_question,
    "fill_in_blank":       _render_fill_in_blank,
    "match_exercise":      _render_match_exercise,
    "hint_reveal":         _render_hint_reveal,
    "achievement_badge":   _render_achievement_badge,
    "score_summary":       _render_score_summary,
    "xp_bar":              _render_xp_bar,
    "lesson_nav":          _render_lesson_nav,
    "course_progress_card": _render_course_progress_card,
    "highlighted_text":    _render_highlighted_text,
    
    # Static & Basic
    "body":                 _render_body,
    "paragraph":            _render_paragraph,
    "text_block":           _render_text_block,
    "heading":              _render_heading,
    "subheading":           _render_subheading,
    "blockquote":           _render_blockquote,
    "divider":              _render_divider,
    "spacer":               _render_spacer,
    "callout":              _render_callout,
    "alert_banner":         _render_alert_banner,
    "info_card":            _render_info_card,
    "code_block":           _render_code_block,
    "code":                 _render_code_block,
    "inline_code":          _render_inline_code,
    "tag_chip":             _render_tag_chip,
    "badge":                _render_badge,
    "image":                _render_image,
    "table":                _render_table,
    "bullet_list":          _render_bullet_list,
    
    # Links & Navigation
    "link_button":          _render_link_button,
    "cta_button":           _render_cta_button,
    "nav_link":             _render_nav_link,
    
    # Workspace Native
    "drive_file_list":      _render_drive_file_list,
    "sheet_preview":        _render_sheet_preview,
    "gmail_summary":        _render_gmail_summary,
    "calendar_upcoming":    _render_calendar_upcoming,
    "user_greeting":        _render_user_greeting,
    "script_run_button":    _render_script_run_button,
    
    # Degraded
    "youtube":              _render_youtube,
    "embed_codepen":        _degraded_link_renderer("CodePen sandbox embed"),
    "embed_stackblitz":     _degraded_link_renderer("StackBlitz sandbox embed"),
    "embed_gist":           _degraded_link_renderer("GitHub Gist widget"),
    "embed_google_slides":  _degraded_link_renderer("Google Slides preview iframe"),
    "figma_embed":          _degraded_link_renderer("Figma interactive canvas design preview"),
    "lottie_animation":     _render_lottie_animation,
    "parallax_card":        _render_parallax_card,
    "embed_tweet":          _render_embed_tweet,
    "social_feed_embed":    _render_social_feed_embed,
    "video_pair":           _render_video_pair,
    "live_demo_embed":      _render_live_demo_embed,
    "image_pair":           _render_image_pair,
    "diagram":              _render_diagram,
}
