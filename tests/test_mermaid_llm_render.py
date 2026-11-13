"""LLM-written diagrams through the whole motion_arch path: convert (scripts/mermaid_arch), render with both twins, and draw in a browser.

tests/mermaid_llm_corpus holds diagrams written by language models the way a user's assistant writes them, not hand-made edge cases
(those are tests/mermaid_corpus). Provenance, 2026-11-05: claude-sonnet-5-5 and claude-haiku-5-5 were each given plain user requests
("draw our OAuth2 PKCE login flow for a mobile app", ...) and no knowledge of the converter (files sonnet_* / haiku_*; the request is
the first comment line). The converter rejected 19 of the 22; each model was then handed its own error messages and asked to fix the
diagram, as a user would paste them back (files *_fit.*). expected.json records what each file must do.

Checks, per file:
  convert   the outcome in expected.json (ok, or a clean rejection whose message names the problem; never a crash)
  twins     for every film: the Python renderer (renderers/web_article.py) and the Apps Script renderer (core JS bundle, in node)
            give the same HTML; no script/handler injection from the labels; every node label is drawn; the payload fits the
            atom page editor (60,000 characters)
  browser   (Chromium installed) at the last frame every node's label sits inside its box; a screenshot of every film goes to
            A2UI_SHOT_DIR when set (a contact sheet, contact.html, is written beside them)
"""
import html as _html
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from test_motion_atoms import _gas_batch, _norm, _py, core_js  # noqa: F401  (core_js is a fixture)

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "mermaid_llm_corpus"
MANIFEST = json.loads((CORPUS / "expected.json").read_text(encoding="utf-8"))
FILES = sorted(p.name for p in CORPUS.iterdir() if p.suffix in (".mmd", ".d2"))
NEEDLES = ("<script src", "onerror=", "onload=", "<iframe", "javascript:")
EDITOR_MAX = 60000
CHROMIUM = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")


@pytest.fixture(scope="module")
def results():
    proc = subprocess.run(["node", str(HERE / "mermaid_corpus_runner.mjs"), str(CORPUS)],
                          capture_output=True, text=True, timeout=180, check=False)
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout)


def films(results):
    return {n: json.loads(r["payload"])["blocks"][0] for n, r in sorted(results.items()) if r["ok"]}


def arch_of(film):
    return next(b for b in film["blocks"] if b.get("type") == "motion_arch")


@pytest.fixture(scope="module")
def rendered(results, core_js):  # noqa: F811
    f = films(results)
    gas = _gas_batch(core_js, list(f.values()))
    return {n: (_py(b), g) for (n, b), g in zip(f.items(), gas)}


def test_the_manifest_covers_every_file_and_says_where_it_came_from():
    assert sorted(MANIFEST) == FILES
    for name in FILES:
        first = (CORPUS / name).read_text(encoding="utf-8").splitlines()[0]
        assert re.match(r"^(%%|#) request: \S", first), name
        assert MANIFEST[name]["model"] in ("claude-sonnet-5-5", "claude-haiku-5-5"), name
        assert MANIFEST[name]["outcome"] in ("ok", "rejected"), name


@pytest.mark.parametrize("name", FILES)
def test_convert(results, name):
    r, want = results[name], MANIFEST[name]
    assert not r.get("crash"), (name, r.get("stack"))
    assert r["deterministic"], name
    if want["outcome"] == "ok":
        assert r["ok"], (name, r.get("errors"))
        assert not r["blockErrors"], (name, r["blockErrors"])
        assert len(r["payload"]) <= EDITOR_MAX, name
    else:
        assert not r["ok"] and r.get("known"), name
        text = " ".join(r["errors"])
        for needle in want["errors_mention"]:
            assert needle in text, (name, needle, text[:300])


def test_twins_draw_the_same_film_and_every_label(results, rendered):
    assert rendered, "no diagram converted: the corpus tests nothing"
    for name, (py, gas) in rendered.items():
        assert _norm(py) == _norm(gas), name
        low = py.lower()
        assert not any(n in low for n in NEEDLES), name
        arch = arch_of(films(results)[name])
        drawn = _html.unescape(re.sub(r"<[^>]+>", " ", py))   # the text as a reader gets it (the renderer escapes ' as &#39;)
        assert f'viewBox="0 0 {arch["w"]} {arch["h"]}"' in py, name
        for n in arch["nodes"]:
            assert n["label"] in drawn, (name, n["label"])
            assert 0 <= n["x"] <= 100 and 0 <= n["y"] <= 100, (name, n["id"])


# ---- in a browser: the drawn film, at its last frame ---------------------------------------------------------------------
PAGE = """<!doctype html><meta charset=utf-8><style>body{margin:0;background:#0b0d12}.f{width:960px;margin:0 auto}</style>
<div class=f>%s</div>"""
PROBE = """(() => new Promise(r0 => setTimeout(r0, 600)))().then(() => {
  // the player autoplays from an IntersectionObserver after load: let that fire first, then pause and go to the last frame
  const mm = window.__a2uiMotion || {}; for (const k of Object.keys(mm)) { mm[k].pause(); mm[k].seek(mm[k].dur * 0.995); }
  return new Promise(r => setTimeout(() => {
    const out = [];
    const vis = [...document.querySelectorAll('svg[viewBox] g')].filter(g => g.querySelector(':scope > rect[rx="14"]'));
    if (vis.some(g => +getComputedStyle(g).opacity < 0.99)) { r([{label: '(film not at its last frame)', over: 999}]); return; }
    for (const g of document.querySelectorAll('svg[viewBox] g')) {
      const rect = g.querySelector(':scope > rect'), texts = g.querySelectorAll(':scope > text');
      if (!rect || !texts.length || !rect.getAttribute('rx') || rect.getAttribute('rx') !== '14') continue;
      const b = rect.getBoundingClientRect();
      for (const t of texts) { const c = t.getBoundingClientRect(); if (!c.width) continue;
        out.push({label: t.textContent, over: Math.max(b.left - c.left, c.right - b.right, b.top - c.top, c.bottom - b.bottom)}); }
    }
    r(out);
  }, 400));
})"""


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium installed")
def test_in_a_browser_every_label_fits_its_box(results, rendered):
    shots = os.environ.get("A2UI_SHOT_DIR")
    runner = HERE / "mermaid_llm_shoot.mjs"
    with tempfile.TemporaryDirectory() as td:
        jobs = []
        for name, (py, _) in rendered.items():
            page = Path(td) / (name.replace(".", "_") + ".html")
            page.write_text(PAGE % py, encoding="utf-8")
            jobs.append({"name": name, "page": str(page), "shot": str(Path(shots) / (name.replace(".", "_") + ".png")) if shots else None})
        (Path(td) / "jobs.json").write_text(json.dumps({"chromium": CHROMIUM, "probe": PROBE, "jobs": jobs}))
        proc = subprocess.run(["node", str(runner), str(Path(td) / "jobs.json")], capture_output=True, text=True, timeout=600, check=False)
        if proc.returncode == 3:
            pytest.skip(proc.stdout.strip() or "puppeteer-core is not available")
        assert proc.returncode == 0, proc.stderr[-2000:]
        found = json.loads(proc.stdout)
    bad = {n: [m for m in found[n] if m["over"] > 1.5] for n in found}
    bad = {n: m for n, m in bad.items() if m and not MANIFEST[n].get("known_gap", {}).get("label_overflow")}
    assert not bad, bad
    for n in found:
        assert found[n], f"{n}: no node labels found in the drawn film"
    if shots:
        cards = "".join(f'<figure><img src="{n.replace(".", "_")}.png" alt="{_html.escape(n)}" loading=lazy><figcaption>{_html.escape(n)}'
                        f' · {MANIFEST[n]["model"]} · {_html.escape(MANIFEST[n]["request"])}</figcaption></figure>' for n in found)
        Path(shots, "contact.html").write_text(
            "<!doctype html><meta charset=utf-8><title>LLM diagram films</title><style>body{font:14px system-ui;margin:16px;background:#f5f6fa}"
            "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,460px),1fr));gap:16px}figure{margin:0;background:#fff;"
            "border:1px solid #dadee5;border-radius:10px;padding:8px}img{width:100%;border-radius:6px}</style><main>" + cards + "</main>")
