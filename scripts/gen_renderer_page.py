#!/usr/bin/env python3
"""gen_renderer_page.py — public/renderer/index.html ("Deploy your Google Apps Script renderer").

Was hand-maintained with its own copy-pasted header markup and full token CSS (comment on the old
file read "v0.3 tokens — keep in sync with SITE_BASE_CSS ... this page is hand-maintained, not
generator-emitted"). That is exactly the drift this repo's generators exist to prevent — found
stale 2026-09-26 by tests/test_brand.py the first time the token hash changed. Now built from the
same shared chrome (SITE_BASE_CSS, site_header, theme JS) as every other page; only this page's own
content (steps, demo tabs, feature grid) stays here.

Run:  python3 scripts/gen_renderer_page.py     # after generate_atom_pages.py (imports its chrome)
"""
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "public", "renderer", "index.html")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_atom_pages as _site  # noqa: E402  the site's shared chrome — one definition

PAGE_CSS = """
.wrap{max-width:860px}
.wrap a{color:var(--accent-2);text-decoration:none}
.wrap a:hover{text-decoration:underline}

.breadcrumb{font-size:13px;color:var(--muted);margin-bottom:40px}
.breadcrumb a{color:var(--muted)}
.breadcrumb a:hover{color:var(--cyan)}
.breadcrumb span{margin:0 6px}

h1{font-size:2.2rem;font-weight:800;letter-spacing:-1px;margin-bottom:8px}
.lead{font-size:1.1rem;color:var(--muted);margin-bottom:40px;max-width:600px}
.lead strong{color:var(--text)}

.steps{display:flex;flex-direction:column;gap:0;margin-bottom:48px}
.step{display:grid;grid-template-columns:40px 1fr;gap:0 20px;position:relative}
.step:not(:last-child)::before{content:'';position:absolute;left:19px;top:44px;bottom:-20px;width:2px;background:var(--border)}
.step-num{width:40px;height:40px;border-radius:50%;background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.4);display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:var(--accent);flex-shrink:0;margin-top:2px;position:relative;z-index:1}
.step-body{padding-bottom:32px}
.step-body h3{font-size:15px;font-weight:700;color:var(--text);margin-bottom:6px;margin-top:8px}
.step-body p{font-size:14px;color:var(--muted);margin-bottom:12px}

pre{background:var(--code-bg);border:1px solid var(--border);border-radius:8px;padding:18px 20px;overflow-x:auto;font-size:13px;font-family:ui-monospace,'SF Mono',Monaco,monospace;color:var(--text);position:relative}
.copy-btn{position:absolute;top:10px;right:10px;background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.3);border-radius:5px;color:var(--accent);font-size:11px;font-weight:700;padding:4px 10px;cursor:pointer;letter-spacing:.04em}
.copy-btn:hover{background:rgba(99,102,241,.25)}
.copy-btn.copied{color:var(--positive);border-color:rgba(63,185,80,.4);background:rgba(63,185,80,.1)}
.comment{color:var(--muted)}

.what-you-get{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin:32px 0 48px}
.feature{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 20px}
.feature-icon{font-size:20px;margin-bottom:10px}
.feature h4{font-size:14px;font-weight:700;color:var(--text);margin-bottom:4px}
.feature p{font-size:13px;color:var(--muted);line-height:1.5}

.cta-row{display:flex;gap:12px;flex-wrap:wrap;margin-top:48px;padding-top:32px;border-top:1px solid var(--border)}
.btn-primary{display:inline-block;padding:12px 24px;background:var(--accent);color:var(--accent-contrast);border-radius:8px;font-size:14px;font-weight:700;letter-spacing:.03em;transition:filter .15s,box-shadow .15s}
.btn-primary:hover{filter:brightness(1.08);box-shadow:var(--glow);text-decoration:none}
.btn-secondary{display:inline-block;padding:12px 24px;border:1px solid var(--border);color:var(--muted);border-radius:8px;font-size:14px;font-weight:600;background:var(--surface)}
.btn-secondary:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}

.note{background:rgba(99,102,241,.07);border:1px solid rgba(99,102,241,.2);border-radius:8px;padding:16px 20px;font-size:13px;color:var(--muted);margin:24px 0}
.note strong{color:var(--text)}

/* Try-it-now demo tabs — pill pattern borrowed from the MCP playground preset chips */
.try-kicker{font-size:11px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin-bottom:6px}
.try-lead{font-size:14px;color:var(--muted);margin-bottom:18px;max-width:640px}
.try-lead strong{color:var(--text)}
.demo-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 14px}
.demo-tab{font:inherit;display:flex;align-items:baseline;gap:8px;padding:8px 16px;border-radius:999px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;font-size:13px;font-weight:700;letter-spacing:.02em;transition:color .15s,border-color .15s,background .15s}
.demo-tab .k{font-size:10px;font-weight:800;letter-spacing:.09em;opacity:.65}
.demo-tab:hover{border-color:var(--accent);color:var(--accent)}
.demo-tab[aria-selected="true"]{border-color:var(--accent);color:var(--accent);background:var(--accent-soft-bg)}
.demo-panel{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:22px 24px;margin-bottom:48px;box-shadow:var(--shadow)}
.demo-panel[hidden]{display:none}
.demo-panel h3{font-size:16px;font-weight:800;margin-bottom:8px}
.demo-panel p{font-size:14px;color:var(--muted);margin-bottom:14px;max-width:640px}
.demo-panel p strong,.demo-panel p code{color:var(--text)}
.demo-cta{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.demo-url{margin:0;padding:10px 88px 10px 14px;font-size:12.5px;flex:1;min-width:230px}
"""

BODY = """
  <div class="breadcrumb">
    <a href="/">A2UI Catalog</a>
    <span>&rsaquo;</span>
    Deploy your Google Apps Script renderer
  </div>

  <h1>The Google&nbsp;Apps&nbsp;Script renderer</h1>
  <p class="lead">A <strong>Google Apps Script web app you deploy once</strong>, then call with any payload from the catalog. Open source, MIT licensed. You own the URL — no dependency on the demo endpoint.</p>

  <div class="try-kicker">Try it now — no setup</div>
  <p class="try-lead">Three <strong>permanent short links</strong>, rendered live by <strong>MCP Apps on a2uicatalog.ai</strong> — the same sandboxed host, the same renderer source the steps below put in your own Apps Script account. Each demo proves a different capability.</p>

  <div class="demo-tabs" role="tablist" aria-label="Renderer demos">
    <button class="demo-tab" role="tab" id="tab-atc" aria-controls="panel-atc" aria-selected="true"><span class="k">DEMO 1</span>ATC Ops Deck</button>
    <button class="demo-tab" role="tab" id="tab-americano" aria-controls="panel-americano" aria-selected="false"><span class="k">DEMO 2</span>Americano Night</button>
    <button class="demo-tab" role="tab" id="tab-learn" aria-controls="panel-learn" aria-selected="false"><span class="k">DEMO 3</span>Learn A2UI + MCP</button>
  </div>

  <div class="demo-panel" id="panel-atc" role="tabpanel" aria-labelledby="tab-atc">
    <h3>ATC Ops Deck — live data in a link</h3>
    <p>A slide playbook over Toulouse-Blagnac: <strong>live ADS-B and METAR feeds</strong>, an isometric takeoff scene, and a fullscreen airspace command deck with a real-time traffic ticker. Everything arrives as one declarative payload — the aircraft on the radar are actually up there right now.</p>
    <p>Proves: playbook slides, data-source atoms, fullscreen breakout — in a plain shareable link.</p>
    <div class="demo-cta">
      <a class="btn-primary" href="https://a2uicatalog.ai/s/atc" target="_blank" rel="noopener">Open demo &rarr;</a>
      <pre class="demo-url" id="url-atc">https://a2uicatalog.ai/s/atc<button class="copy-btn" onclick="copy('url-atc',this)">COPY</button></pre>
    </div>
  </div>

  <div class="demo-panel" id="panel-americano" role="tabpanel" aria-labelledby="tab-americano" hidden>
    <h3>Americano Night — a wired, interactive app</h3>
    <p>A padel tournament night as a <strong>wired surface</strong>: live scoring, rotation schedules, standings that update as you tap — state stores, actions, and sessions, still expressed as one declarative payload. Open it on two phones with the same link and score together.</p>
    <p>Proves: the wired dialect — real interactivity without the agent writing a line of imperative code.</p>
    <div class="demo-cta">
      <a class="btn-primary" href="https://a2uicatalog.ai/s/americano#t=renderer-demo" target="_blank" rel="noopener">Open demo &rarr;</a>
      <pre class="demo-url" id="url-americano">https://a2uicatalog.ai/s/americano<button class="copy-btn" onclick="copy('url-americano',this)">COPY</button></pre>
    </div>
  </div>

  <div class="demo-panel" id="panel-learn" role="tabpanel" aria-labelledby="tab-learn" hidden>
    <h3>Learn A2UI + MCP — the in-depth brief</h3>
    <p>A five-module curriculum on <strong>A2UI and the Model Context Protocol</strong>: the payload contract, atoms and the graduation pipeline, the <code>?p=</code> URL model, MCP fundamentals, and MCP Apps' sandboxed handshake. Flashcards, knowledge checks, and worked examples throughout.</p>
    <p>Proves: <code>module_map</code> pagination — five module cards, each its own permanently-published page, so depth is unbounded while every link stays shareable. Module 3 explains why: the same atom builds sub-pages differently depending on whether it's rendering on Apps Script or here, in the browser.</p>
    <div class="demo-cta">
      <a class="btn-primary" href="https://a2uicatalog.ai/s/learn-a2ui" target="_blank" rel="noopener">Open demo &rarr;</a>
      <pre class="demo-url" id="url-learn">https://a2uicatalog.ai/s/learn-a2ui<button class="copy-btn" onclick="copy('url-learn',this)">COPY</button></pre>
    </div>
  </div>

  <h2 style="font-size:1.2rem;font-weight:700;margin-bottom:8px;">Deploy your own</h2>
  <p style="font-size:13px;color:var(--muted);margin:0 0 32px;">Prerequisites: <strong>Node.js 18+</strong> (for <code>npm</code>, used to install clasp in step 2) and a Google account.</p>

  <div class="steps">

    <div class="step">
      <div class="step-num">1</div>
      <div class="step-body">
        <h3>Clone the repo</h3>
        <p>The renderer lives in <code>apps-script-surface/gas-wired-renderer/</code> — 501 atoms, no CDN, no external dependencies.</p>
        <pre id="code-clone"><span class="comment"># Clone and navigate to the renderer directory</span>
git clone https://github.com/a2uicatalog/a2ui
cd a2ui/apps-script-surface/gas-wired-renderer
<button class="copy-btn" onclick="copy('code-clone',this)">COPY</button></pre>
      </div>
    </div>

    <div class="step">
      <div class="step-num">2</div>
      <div class="step-body">
        <h3>Authenticate with clasp</h3>
        <p>clasp is Google's Apps Script CLI. One-time login — uses your Google account to deploy the renderer as a GAS web app.</p>
        <pre id="code-login">npm install -g @google/clasp
clasp login
<button class="copy-btn" onclick="copy('code-login',this)">COPY</button></pre>
      </div>
    </div>

    <div class="step">
      <div class="step-num">3</div>
      <div class="step-body">
        <h3>Create and push</h3>
        <p>Creates a new GAS project in your Google account and pushes all renderer files. Takes about 30 seconds.</p>
        <pre id="code-push">clasp create --type webapp --title "My A2UI Renderer"
clasp push
<button class="copy-btn" onclick="copy('code-push',this)">COPY</button></pre>
      </div>
    </div>

    <div class="step">
      <div class="step-num">4</div>
      <div class="step-body">
        <h3>Deploy</h3>
        <p>Deploy as a web app accessible to anyone. You'll get a URL — that's your renderer endpoint.</p>
        <pre id="code-deploy">clasp deploy --description "A2UI Renderer v1"
<span class="comment"># &rarr; https://script.google.com/macros/s/YOUR_ID/exec</span>
<button class="copy-btn" onclick="copy('code-deploy',this)">COPY</button></pre>
      </div>
    </div>

  </div>

  <h2 style="font-size:1.2rem;font-weight:700;margin-bottom:16px;">What you get</h2>
  <div class="what-you-get">
    <div class="feature">
      <div class="feature-icon">&#128274;</div>
      <h4>You own the deployment</h4>
      <p>Runs in your Google account. No dependency on the catalog's demo URL. Survives any catalog changes.</p>
    </div>
    <div class="feature">
      <div class="feature-icon">&#9889;</div>
      <h4>501 atoms, ready to go</h4>
      <p>Stat cards, charts, globes, animations, tables, forms — all render immediately. A handful of data-source atoms want their own API key (see below) and degrade gracefully without one.</p>
    </div>
    <div class="feature">
      <div class="feature-icon">&#127912;</div>
      <h4>Fully customisable</h4>
      <p>Fork the renderer, add your own atoms, change the CSS, restrict to specific surfaces. It's your code.</p>
    </div>
    <div class="feature">
      <div class="feature-icon">&#128260;</div>
      <h4>Stay up to date</h4>
      <p>Pull the latest from the repo and <code>clasp push</code> again when new atoms are added to the catalog.</p>
    </div>
  </div>

  <h2 style="font-size:1.2rem;font-weight:700;margin-bottom:12px;">Call it from your GAS project</h2>
  <p style="font-size:14px;color:var(--muted);margin-bottom:16px;">Once deployed, use your renderer URL with any payload from the catalog.</p>
  <pre id="code-usage"><span class="comment">// In any GAS project — call your renderer with atom blocks</span>
function doGet() {
  const blocks = [
    { type: "stat_card", value: "1,234", label: "Daily users", delta: "+12%", is_up: true },
    { type: "progress_bar", value: 75, label: "Q2 target" },
    { type: "globe_3d", theme: "earth", size: 300 }
  ];

  const payload = Utilities.base64EncodeWebSafe(
    Utilities.newBlob(JSON.stringify(blocks)).getBytes()
  );
  const url = "https://script.google.com/macros/s/YOUR_ID/exec?p=" + payload;

  return HtmlService.createHtmlOutput(
    '&lt;script&gt;window.location="' + url + '"&lt;/script&gt;'
  );
}
<button class="copy-btn" onclick="copy('code-usage',this)">COPY</button></pre>

  <div class="note">
    <strong>The "Try it live" button on each atom page</strong> uses the catalog's shared demo renderer — same code, same atoms. It's there so you can explore without deploying. For production use, deploy your own.
  </div>

  <div class="note">
    <strong>A few atoms want their own Script Properties</strong> — Trading212 (<code>T212_API_KEY</code>, <code>T212_API_SECRET</code>), Twelve Data (<code>TWELVE_API_KEY</code>) and Vertex AI (<code>VERTEX_PROJECT_ID</code>) each back one data-source atom. Set them under <strong>Project Settings &rarr; Script Properties</strong> in your Apps Script editor if you use those atoms; every other atom works with none set, and these three fail gracefully (return an explicit error, not a broken page) without their key.
  </div>

  <div class="cta-row">
    <a href="/" class="btn-primary">Browse atoms &rarr;</a>
    <a href="https://github.com/a2uicatalog/a2ui/tree/main/apps-script-surface/gas-wired-renderer" target="_blank" rel="noopener" class="btn-secondary">View source on GitHub</a>
    <a href="/.well-known/ai-catalog.json" class="btn-secondary">ARD manifest</a>
  </div>

  <footer>
    <span>A2UI Atomic Catalog &middot; <a href="https://github.com/a2uicatalog/a2ui">github.com/a2uicatalog/a2ui</a></span>
    <span>Independent, unofficial catalog — not affiliated with or endorsed by Google. A2UI is Google's protocol; official spec at <a href="https://a2ui.org">a2ui.org</a>.</span>
    <span>MIT License</span>
  </footer>
"""

FOOT_SCRIPT = """
    function copy(id, btn) {
      const pre = document.getElementById(id);
      const text = pre.innerText.replace(/COPY\\s*$/, '').trim();
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'COPIED';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = 'COPY'; btn.classList.remove('copied'); }, 2000);
      });
    }
    // Try-it-now demo tabs
    document.querySelectorAll('.demo-tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        document.querySelectorAll('.demo-tab').forEach(function (t) {
          t.setAttribute('aria-selected', t === tab ? 'true' : 'false');
        });
        document.querySelectorAll('.demo-panel').forEach(function (p) {
          p.hidden = (p.id !== tab.getAttribute('aria-controls'));
        });
      });
    });
"""


def render():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Deploy your Google Apps Script renderer — A2UI Catalog</title>
  <meta name="description" content="Deploy your own A2UI Google Apps Script renderer in 4 commands. Open source, MIT licensed. You own the URL, you own the deployment.">
  {_site.SITE_HEAD_JS}
  <style>{_site.SITE_BASE_CSS}
{PAGE_CSS}</style>
</head>
<body>
{_site.site_header("renderer")}
  <div class="wrap">
{BODY}
  </div>
<script>
{_site.SITE_FOOT_JS.replace("<script>", "").replace("</script>", "")}
{FOOT_SCRIPT}
</script>
</body>
</html>
"""


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render())
    print(f"wrote public/renderer/index.html ({os.path.getsize(OUT)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
