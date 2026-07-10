#!/usr/bin/env python3
"""Generate the self-contained MCP Apps demo renderer bundle.

Ports a small, fixed atom subset (heading, body, paragraph, flashcard_deck)
out of the GAS renderer source (ground truth per CLAUDE.md) into a browser-
portable HTML/JS bundle that implements the MCP Apps View side of the
ui/initialize handshake (spec 2026-01-26, apps.mdx). Output is generated,
never hand-edited: public/mcp-apps-demo/renderer-bundle.html.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_DIR = ROOT / "apps-script-surface" / "gas-wired-renderer"
OUT = ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html"

STATIC_ATOM_TYPES = ["body", "paragraph", "heading"]
INTERACTIVE_ATOM_TYPES = ["flashcard_deck"]

# Official MCP connector-mark logo (MIT, modelcontextprotocol/ext-apps media/mcp.svg),
# inlined as a data URI rather than fetched externally -- the rocket badge originally
# loaded the Apps Script logo from fonts.gstatic.com; a live network fetch from inside
# a sandboxed MCP Apps view cuts against the "controlled opaqueness" story this surface
# is demonstrating, so this one has zero network dependency instead.
MCP_LOGO_DATA_URI = (
    "data:image/svg+xml;base64,"
    "PHN2ZyB3aWR0aD0iMTgwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDE4MCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+"
    "CjxnIGNsaXAtcGF0aD0idXJsKCNjbGlwMF8xOV8xMykiPgo8cGF0aCBkPSJNMTggODQuODUyOEw4NS44ODIyIDE2Ljk3MDZDOTUuMjU0OCA3LjU5Nzk4IDExMC40NTEgNy41OTc5OCAxMTkuODIzIDE2Ljk3MDZWMTYuOTcwNkMxMjkuMTk2IDI2LjM0MzEgMTI5LjE5NiA0MS41MzkxIDExOS44MjMgNTAuOTExN0w2OC41NTgxIDEwMi4xNzciIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMTIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8cGF0aCBkPSJNNjkuMjY1MiAxMDEuNDdMMTE5LjgyMyA1MC45MTE3QzEyOS4xOTYgNDEuNTM5MSAxNDQuMzkyIDQxLjUzOTEgMTUzLjc2NSA1MC45MTE3TDE1NC4xMTggNTEuMjY1MkMxNjMuNDkxIDYwLjYzNzggMTYzLjQ5MSA3NS44MzM4IDE1NC4xMTggODUuMjA2M0w5Mi43MjQ4IDE0Ni42Qzg5LjYwMDYgMTQ5LjcyNCA4OS42MDA2IDE1NC43ODkgOTIuNzI0OCAxNTcuOTEzTDEwNS4zMzEgMTcwLjUyIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjEyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPHBhdGggZD0iTTEwMi44NTMgMzMuOTQxMUw1Mi42NDgyIDg0LjE0NTdDNDMuMjc1NiA5My41MTgzIDQzLjI3NTYgMTA4LjcxNCA1Mi42NDgyIDExOC4wODdWMTE4LjA4N0M2Mi4wMjA4IDEyNy40NTkgNzcuMjE2NyAxMjcuNDU5IDg2LjU4OTMgMTE4LjA4N0wxMzYuNzk0IDY3Ljg4MjIiIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMTIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L2c+CjxkZWZzPgo8Y2xpcFBhdGggaWQ9ImNsaXAwXzE5XzEzIj4KPHJlY3Qgd2lkdGg9IjE4MCIgaGVpZ2h0PSIxODAiIGZpbGw9IndoaXRlIi8+CjwvY2xpcFBhdGg+CjwvZGVmcz4KPC9zdmc+Cg=="
)

# Not a catalog atom — hand-ported (not extracted) from the Meet Stage add-on's
# gdm-rocket-panel Lit component (gemini/addons/meetstudio/internal/components/
# gdm_stage_rocket_panel.ts), the same animation used in the "Apps Script is
# now a Workspace Core Service" did-you-know playbook. Registered into
# _RENDERERS under 'gdm_rocket_panel' so it fits the same block-type dispatch
# as every other atom, but there's no .gs source to regenerate this from — the
# Lit wrapper/Shadow DOM is stripped, the canvas drawing math is kept verbatim.
GDM_ROCKET_PANEL_JS = r"""
_RENDERERS['gdm_rocket_panel'] = function(b) {
  var uid = 'grp' + Math.random().toString(36).substr(2, 6);
  var height = b.height || 480;
  return (
    '<div id="' + uid + 'w" style="position:relative;width:100%;height:' + height + 'px;' +
      'background:#05070f;border-radius:12px;overflow:hidden;margin:1.5rem 0;">' +
      '<canvas id="' + uid + 'c" style="display:block;width:100%;height:100%;"></canvas>' +
    '</div>' +
    '<script>(function(){' +
      'var canvas=document.getElementById("' + uid + 'c");if(!canvas)return;' +
      'var ctx=canvas.getContext("2d");' +
      'var logo=null;' +
      'var img=new Image();' +
      'img.src="__MCP_LOGO_DATA_URI__";' +
      'img.onload=function(){logo=img;};' +
      'var y=1.2,trail=[],sparks=[],raf=null,landed=false;' +

      'function resize(){canvas.width=canvas.offsetWidth||540;canvas.height=canvas.offsetHeight||' + height + ';}' +
      'window.addEventListener("resize",resize);resize();' +

      'function drawRocket(cx,cy,w,h){' +
        'var s=Math.min(w,h)/7;' +
        'var pulse=0.85+0.15*Math.sin(Date.now()/90);' +
        'var glow=ctx.createRadialGradient(cx,cy+s*1.05,0,cx,cy+s*1.05,s*1.5*pulse);' +
        'glow.addColorStop(0,"rgba(255,255,200,0.98)");' +
        'glow.addColorStop(0.12,"rgba(255,180,0,0.9)");' +
        'glow.addColorStop(0.4,"rgba(255,60,0,0.55)");' +
        'glow.addColorStop(1,"rgba(255,20,0,0)");' +
        'ctx.beginPath();ctx.arc(cx,cy+s*1.05,s*1.5*pulse,0,Math.PI*2);' +
        'ctx.fillStyle=glow;ctx.fill();' +

        'ctx.save();ctx.translate(cx,cy);' +

        'ctx.beginPath();' +
        'ctx.moveTo(-s*0.28,s*0.55);ctx.lineTo(-s*0.72,s*1.02);ctx.lineTo(-s*0.28,s*0.82);' +
        'ctx.closePath();ctx.fillStyle="#0077b6";ctx.fill();' +

        'ctx.beginPath();' +
        'ctx.moveTo(s*0.28,s*0.55);ctx.lineTo(s*0.72,s*1.02);ctx.lineTo(s*0.28,s*0.82);' +
        'ctx.closePath();ctx.fillStyle="#0077b6";ctx.fill();' +

        'ctx.beginPath();' +
        'ctx.moveTo(-s*0.22,s*0.68);ctx.lineTo(-s*0.3,s*0.98);ctx.lineTo(s*0.3,s*0.98);ctx.lineTo(s*0.22,s*0.68);' +
        'ctx.closePath();' +
        'var bell=ctx.createLinearGradient(-s*0.3,0,s*0.3,0);' +
        'bell.addColorStop(0,"#4cc9f0");bell.addColorStop(0.5,"#e0f7ff");bell.addColorStop(1,"#4cc9f0");' +
        'ctx.fillStyle=bell;ctx.fill();' +

        'var body=ctx.createLinearGradient(-s*0.28,0,s*0.28,0);' +
        'body.addColorStop(0,"#0a8cce");body.addColorStop(0.25,"#00c8f0");body.addColorStop(0.55,"#c8f4ff");' +
        'body.addColorStop(0.8,"#00c8f0");body.addColorStop(1,"#0a6ca0");' +
        'ctx.beginPath();ctx.roundRect(-s*0.28,-s*0.6,s*0.56,s*1.3,s*0.05);' +
        'ctx.fillStyle=body;ctx.fill();' +

        'ctx.beginPath();' +
        'ctx.moveTo(0,-s*1.05);' +
        'ctx.bezierCurveTo(-s*0.07,-s*0.78,-s*0.24,-s*0.68,-s*0.28,-s*0.6);' +
        'ctx.lineTo(s*0.28,-s*0.6);' +
        'ctx.bezierCurveTo(s*0.24,-s*0.68,s*0.07,-s*0.78,0,-s*1.05);' +
        'ctx.closePath();' +
        'var nose=ctx.createLinearGradient(-s*0.28,0,s*0.28,0);' +
        'nose.addColorStop(0,"#0a6ca0");nose.addColorStop(0.45,"#d8f8ff");nose.addColorStop(1,"#0a6ca0");' +
        'ctx.fillStyle=nose;ctx.fill();' +

        'var badgeSize=s*0.38,badgeX=-badgeSize/2,badgeY=-s*0.38;' +
        'ctx.beginPath();' +
        'ctx.roundRect(badgeX-s*0.03,badgeY-s*0.03,badgeSize+s*0.06,badgeSize+s*0.06,s*0.06);' +
        'ctx.fillStyle="rgba(255,255,255,0.92)";ctx.fill();' +
        'if(logo){ctx.drawImage(logo,badgeX,badgeY,badgeSize,badgeSize);}' +
        'else{' +
          'ctx.beginPath();ctx.arc(0,badgeY+badgeSize/2,badgeSize*0.4,0,Math.PI*2);' +
          'ctx.fillStyle="#00c8f0";ctx.fill();' +
        '}' +

        'ctx.beginPath();ctx.roundRect(-s*0.28,s*0.2,s*0.56,s*0.06,s*0.02);' +
        'ctx.fillStyle="rgba(255,255,255,0.25)";ctx.fill();' +

        'ctx.restore();' +
      '}' +

      'function drawHud(w,h){' +
        'var fs=Math.min(w,h)*0.026;' +
        'var progress=Math.max(0,(1.2-y)/1.5);' +
        'var altStr=y<0.05?"∞":Math.round(progress*28000).toLocaleString()+" ft";' +
        'var spdStr=y<0.05?"MACH ∞":Math.round(Math.min(380,80+progress*2200))+" kt";' +
        'ctx.font=fs+"px monospace";ctx.textAlign="right";' +
        'ctx.fillStyle="rgba(0,255,136,0.42)";' +
        'ctx.fillText("ALT "+altStr+"  SPD "+spdStr+"  ·  MCP APPS · A2UI CATALOG",w-10,h-10);' +
      '}' +

      'function loop(){' +
        // Lit's disconnectedCallback() cancelled the rAF loop on unmount;
        // there's no unmount hook here, so check the canvas is still in the
        // document instead -- otherwise a repaint (a second tool-result)
        // leaves the old loop running forever against a detached canvas.
        'if(!canvas.isConnected)return;' +
        'var w=canvas.width,h=canvas.height,cx=w*0.5,s=Math.min(w,h)/7;' +
        'ctx.clearRect(0,0,w,h);' +

        // Launch once and hold at apex, rather than the original's endless
        // relaunch loop -- that reset made sense inside a Meet Stage slide
        // that only ever held for ~7s before advancing, but reads as
        // stuck/glitchy on a static page a visitor can sit on indefinitely.
        // Freeze the ascent just before exiting the frame; let the existing
        // trail/sparks finish fading, then stop scheduling frames entirely.
        'if(!landed){' +
          'y-=0.012+(1.2-y)*0.002;' +
          'if(y<=0.08){y=0.08;landed=true;}' +
        '}' +
        'var cy=y*h;' +

        'if(!landed){' +
          'trail.push({x:cx+(Math.random()-0.5)*s*0.08,y:cy+s*0.98,t:Date.now(),r:3+Math.random()*4});' +
        '}' +
        'trail=trail.filter(function(p){return Date.now()-p.t<260;});' +
        'trail.forEach(function(p){' +
          'var age=(Date.now()-p.t)/260;' +
          'var a=(1-age)*0.75;' +
          'var r=p.r*(1+age*3);' +
          'var g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r);' +
          'g.addColorStop(0,"rgba(255,230,100,"+a+")");' +
          'g.addColorStop(0.4,"rgba(255,90,0,"+(a*0.7)+")");' +
          'g.addColorStop(1,"rgba(255,20,0,0)");' +
          'ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fillStyle=g;ctx.fill();' +
        '});' +

        'if(!landed&&Math.random()<0.45){' +
          'sparks.push({x:cx+(Math.random()-0.5)*s*0.35,y:cy+s*0.98,' +
            'vx:(Math.random()-0.5)*3,vy:1.5+Math.random()*4,life:1});' +
        '}' +
        'sparks=sparks.filter(function(sp){return sp.life>0;});' +
        'sparks.forEach(function(sp){' +
          'ctx.beginPath();ctx.arc(sp.x,sp.y,sp.life*2.8,0,Math.PI*2);' +
          'ctx.fillStyle="rgba(255,"+Math.round(180+sp.life*75)+",40,"+sp.life+")";' +
          'ctx.fill();' +
          'sp.x+=sp.vx;sp.y+=sp.vy;sp.life-=0.065;' +
        '});' +

        'drawRocket(cx,cy,w,h);' +
        'drawHud(w,h);' +

        'if(landed&&trail.length===0&&sparks.length===0)return;' +
        'raf=requestAnimationFrame(loop);' +
      '}' +
      'loop();' +
    '})();<\/script>'
  );
};
""".strip()


def _extract_braced(source, anchor):
    """Return the substring starting at `anchor` through the matching closing
    brace of the first `{` found after it (plus a trailing `;` if present)."""
    start = source.index(anchor)
    brace_start = source.index("{", start)
    depth = 0
    i = brace_start
    while i < len(source):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    end = i + 1
    if source[end:end + 1] == ";":
        end += 1
    return source[start:end]


def extract_renderer(source, atom_type):
    return _extract_braced(source, "_RENDERERS['%s'] = function" % atom_type)


def extract_function(source, signature):
    return _extract_braced(source, signature)


def build_render_atoms():
    # Simplified renderAtoms(): the GAS original's PropertiesService pack-gate
    # is dropped here — this bundle's fixed atom subset is always enabled.
    return """
function renderAtoms(blocks, opts) {
  if (!blocks || !Array.isArray(blocks)) return '<!-- a2ui: blocks list is empty or invalid -->';
  opts = opts || {};
  var parts = [];
  for (var i = 0; i < blocks.length; i++) {
    var block = blocks[i];
    var btype = block.component || block.type;
    var fn = _RENDERERS[btype];
    if (fn) {
      try { parts.push(fn(block)); }
      catch (err) { parts.push('<div class="asw-callout">Error rendering ' + _esc(btype) + ': ' + _esc(err.message) + '</div>'); }
    } else {
      parts.push('<!-- a2ui: atom "' + _esc(btype) + '" is not included in this MCP Apps demo bundle -->');
    }
  }
  return parts.join('\\n\\n');
}
""".strip()


def build_bundle():
    atom_gs = (RENDERER_DIR / "atom.gs").read_text()
    atoms_lms_gs = (RENDERER_DIR / "atoms_lms.gs").read_text()
    atom_styles = (RENDERER_DIR / "AtomStyles.html").read_text()

    esc_fn = extract_function(atom_gs, "function _esc(str)")
    safe_url_fn = extract_function(atom_gs, "function _safeUrl(url)")
    markdown_fn = extract_function(atom_gs, "function _markdownToHtml(md)")

    renderer_fns = [extract_renderer(atom_gs, t) for t in STATIC_ATOM_TYPES]
    renderer_fns += [extract_renderer(atoms_lms_gs, t) for t in INTERACTIVE_ATOM_TYPES]

    render_atoms_fn = build_render_atoms()

    js = "\n\n".join([
        "var _RENDERERS = {};",
        esc_fn,
        safe_url_fn,
        markdown_fn,
        "\n\n".join(renderer_fns),
        GDM_ROCKET_PANEL_JS.replace("__MCP_LOGO_DATA_URI__", MCP_LOGO_DATA_URI),
        render_atoms_fn,
    ])

    handshake_js = """
// ---- MCP Apps View protocol handshake (spec 2026-01-26, apps.mdx) ----
(function() {
  var initId = 'init-' + Math.random().toString(36).slice(2);

  function post(msg) { window.parent.postMessage(msg, '*'); }

  function paint(payload) {
    var root = document.getElementById('a2ui-root');
    document.body.classList.toggle('asw-dark-theme', payload.theme === 'dark');
    root.innerHTML = renderAtoms(payload.blocks || [], { theme: payload.theme });
    // innerHTML-injected <script> tags never execute (browsers block it);
    // atoms like flashcard_deck ship inline <script>, so re-create + re-append
    // each one to actually run it.
    var scripts = root.querySelectorAll('script');
    for (var i = 0; i < scripts.length; i++) {
      var old = scripts[i];
      var fresh = document.createElement('script');
      fresh.textContent = old.textContent;
      old.parentNode.replaceChild(fresh, old);
    }
  }

  window.addEventListener('message', function(ev) {
    var msg = ev.data;
    if (!msg || msg.jsonrpc !== '2.0') return;

    if (msg.id === initId && msg.result) {
      post({ jsonrpc: '2.0', method: 'ui/notifications/initialized' });
      return;
    }

    if (msg.method === 'ui/notifications/tool-result') {
      var result = msg.params || {};
      paint(result.structuredContent || {});
    }
  });

  post({
    jsonrpc: '2.0',
    id: initId,
    method: 'ui/initialize',
    params: { appCapabilities: { availableDisplayModes: ['inline'] } }
  });
})();
""".strip()

    return """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>A2UI Catalog renderer — MCP Apps View</title>
%s
<style>body { padding: 24px; }</style>
</head>
<body class="asw-page">
<div id="a2ui-root"></div>
<script>
// Ported from apps-script-surface/gas-wired-renderer/atom.gs + atoms_lms.gs.
// Generated by scripts/gen_mcp_apps_bundle.py — do not hand-edit.
%s

%s
</script>
</body>
</html>
""" % (atom_styles.strip(), js, handshake_js)


def main():
    bundle = build_bundle()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(bundle)
    print("wrote %s (%d bytes)" % (OUT, len(bundle)))


if __name__ == "__main__":
    main()
