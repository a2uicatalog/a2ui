"""I66: spring_nodes' opt-in live layer (interactive: true) makes every node focusable for the arrow keys, so each
node needs a visible focus indicator and an accessible name (WCAG 2.4.7 focus visible, 4.1.2 name, role, value).

Before this fix focus only thickened the node's own outline from 2 to 4 in the same colour, and the focusable circles
had no name. The ring is two-tone (a dark band under a white band) so it shows against any `bg` the payload
picks. Measured in headless Chromium in both renderers.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_histogram_layout_box import _run  # noqa: E402
from test_motion_atoms import _gas_batch, _py, core_js  # noqa: E402,F401  (core_js is a fixture)

PAYLOADS = {
    "dark": {"type": "spring_nodes", "interactive": True, "title": "Services",
             "nodes": [{"id": "web", "label": "Web"}, {"id": "api", "label": "API"}, {"id": "db", "label": "Database"}],
             "edges": [{"a": 0, "b": 1}, {"a": 1, "b": 2}]},
    "light": {"type": "spring_nodes", "interactive": True, "bg": "#ffffff",
              "nodes": [{"id": "a", "label": "Alpha"}, {"id": "b", "label": "Beta"}], "edges": [{"a": 0, "b": 1}]},
}

HARNESS = r'''<script>
function lum(c){var m=/^#([0-9a-f]{6})$/i.exec(c||'');if(!m)return -1;var n=parseInt(m[1],16),v=[n>>16&255,n>>8&255,n&255].map(function(x){x/=255;return x<=0.03928?x/12.92:Math.pow((x+0.055)/1.055,2.4);});return 0.2126*v[0]+0.7152*v[1]+0.0722*v[2];}
var out=[];document.querySelectorAll('.case').forEach(function(c){var errs=[],svg=c.querySelector('svg');if(svg.getAttribute('role')==='img')errs.push('svg role img hides the focusable nodes from assistive tech');var us=svg.querySelectorAll('[data-n]'),ls=svg.querySelectorAll('[data-x]');
us.forEach(function(u,k){if(u.getAttribute('tabindex')!=='0')errs.push('node '+k+' not focusable');if(u.getAttribute('role')!=='button')errs.push('node '+k+' role '+u.getAttribute('role'));
 var name=u.getAttribute('aria-label')||'';if(name.indexOf(ls[k].textContent)!==0)errs.push('node '+k+' name "'+name+'"');});
var u=us[0];u.focus();var ring=svg.querySelector('[data-focus-ring]');
if(!ring)errs.push('no focus ring');else{
 if(getComputedStyle(ring).display==='none')errs.push('ring hidden while focused');
 var cs=ring.querySelectorAll('circle'),L=[];cs.forEach(function(q){L.push(lum(q.getAttribute('stroke')));
  if(Math.abs(+q.getAttribute('cx')-+u.getAttribute('cx'))>0.01||Math.abs(+q.getAttribute('cy')-+u.getAttribute('cy'))>0.01)errs.push('ring off the node');
  if(+q.getAttribute('r')<+u.getAttribute('r')+3)errs.push('ring inside the node');});
 if(!(Math.min.apply(0,L)>=0&&Math.min.apply(0,L)<0.05&&Math.max.apply(0,L)>0.9))errs.push('ring not two-tone '+JSON.stringify(L));
 u.blur();if(getComputedStyle(ring).display!=='none')errs.push('ring still shown after blur');}
if(u.getAttribute('stroke-width')!=='2')errs.push('node outline changed: '+u.getAttribute('stroke-width'));
out.push({id:c.id,errs:errs});});document.getElementById('out').textContent=JSON.stringify(out);
</script>'''


@pytest.mark.parametrize("renderer", ["python", "gas"])
def test_focused_node_shows_a_two_tone_ring_and_every_node_is_named(renderer, core_js):
    html = {n: _py(p) for n, p in PAYLOADS.items()} if renderer == "python" else dict(zip(PAYLOADS, _gas_batch(core_js, list(PAYLOADS.values()))))
    res = _run(html, harness=HARNESS)
    assert res and len(res) == len(PAYLOADS) * 5
    bad = {r["id"]: r["errs"] for r in res if r["errs"]}
    assert not bad, bad
