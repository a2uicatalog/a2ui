"""Cross-surface field-contract parity: web (Python) vs GAS / MCP Apps.

The paradigm of the catalogue is that one payload renders the same content on
every surface that claims the atom. Each renderer is hand-written, so a field
one surface honours and the other ignores is silent drift -- the
`status_dashboard` web renderer ignored its whole payload for the repo's entire
history and nothing noticed.

Measure: render each stable atom's example block on both surfaces and count how
many of the block's display strings (>=4 letters, not URLs/colours/enum words)
appear in each output. An atom DIVERGES when the two coverages differ by
>= THRESHOLD, i.e. one surface shows content the other drops.

Known divergences are declared debt in tests/surface_parity_debt.json. The
list may only SHRINK: a new divergence fails, and so does a listed atom that
no longer diverges (remove it -- the debt is paid). Regenerate the file only
to record a deliberate, reviewed change: python3 tests/test_surface_parity.py
"""
import html as H
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

DEBT = ROOT / "tests" / "surface_parity_debt.json"
THRESHOLD = 0.5
CORE_ENV_NOTE = "GAS side is rendered through the same core the MCP Apps bundle ships"


# Schema-faithful payloads for atoms whose generic auto-example is structurally
# meaningless (structured arrays it can only fill with prose). These are what an
# agent following get_atom_schema would actually send, so they are the honest
# parity probe; the 8 that GAS used to drop entirely (2026-09-26 fix) live here.
CURATED = {
    "animated_border_card": {"title": "Release notes", "body": "Card body sentinel text"},
    "conversation_snippet": {"user": "What is A2UI exactly?", "response": "A declarative UI protocol."},
    "follow_up_chips": {"label": "You might also ask:", "items": ["What is the ROI?", "Show me by region"]},
    "metric_comparison_card": {"label": "Response latency", "value": 120, "previous": 150},
    "mini_sparkline_set": {"series": [{"label": "CPU load", "data": [1, 3, 2]}]},
    "order_status_card": {"order_number": "#1042", "status": "fulfilled", "customer": "Ada Lovelace",
                          "items": [{"title": "Blue widget", "qty": 2, "price": "$5"}], "total": "$10.00"},
    "text_callout": {"variant": "info", "title": "Good to know", "description": "Body text goes here"},
    "tooltip": {"trigger_text": "hover over me", "tooltip_content": "the hidden explanation"},
    "onboarding_stepper": {"title": "Get started now", "steps": [
        {"id": "a", "icon": "R", "label": "Install the CLI", "description": "Run the installer"}]},
    "timeline": {"title": "Project history", "events": [
        {"date": "2026", "label": "Public launch", "text": "We shipped it"}]},
    "further_reading": {"links": [{"title": "Guide to tokens", "url": "https://example.com/a",
                                   "description": "Background reading"}]},
    "resources_list": {"items": [{"title": "Design kit bundle", "size": "2 MB", "type": "zip",
                                  "url": "https://example.com/k.zip"}]},
}


def _example(atom, gap):
    t = atom["type"]
    b = dict(CURATED.get(t) or gap._EXAMPLE_BLOCKS.get(t) or json.loads(gap.example_payload(atom)))
    b["type"] = t
    return b


def _leaves(o, out):
    if isinstance(o, str):
        out.append(o)
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in ("type", "component"):
                _leaves(v, out)
    elif isinstance(o, list):
        for v in o:
            _leaves(v, out)


def _is_display(s):
    if len(re.findall(r"[A-Za-z]", s)) < 4 or re.match(r"^(https?:|#)", s):
        return False
    if " " in s.strip():
        return True
    return len(s) >= 6 and s.isalpha() and s[0].isupper()


def measure():
    import generate_atom_pages as gap
    import gen_mcp_apps_bundle as gen
    import renderers.web_article as w

    atoms = yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]
    cases = []
    for a in atoms:
        if a.get("stage") == "preview":
            continue
        works = (a.get("surfaces") or {}).get("works_on") or []
        if "web" not in works or not ({"mcp-apps", "google-apps-script-web"} & set(works)):
            continue                      # only atoms claiming BOTH surfaces
        b = _example(a, gap)
        L = []
        _leaves(b, L)
        L = [s for s in L if _is_display(s)]
        if L:
            cases.append({"t": a["type"], "b": {**b, "component": a["type"]}, "L": L})

    bundle = gen.build_bundle()
    core = [x for x in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
            if "a2ui-core" in x[:300]][0]
    with tempfile.TemporaryDirectory() as td:
        drv = Path(td) / "d.js"
        drv.write_text(
            "global.window=global;\n" + core + "\nvar cs=" +
            json.dumps([{"t": c["t"], "b": c["b"]} for c in cases]) +
            ";var r={};cs.forEach(function(c){try{r[c.t]=renderAtoms([c.b],{theme:'light'});}"
            "catch(e){r[c.t]='';}});console.log(JSON.stringify(r));")
        p = subprocess.run(["node", str(drv)], capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stderr[-1500:]
    gas = json.loads(p.stdout)

    def cov(html, L):
        text = H.unescape(re.sub(r"<[^>]+>", " ", html))
        return sum(1 for s in L if s in text or s in html or H.escape(s) in html) / len(L)

    out = {}
    for c in cases:
        try:
            py = w._RENDERERS[c["t"]](dict(c["b"]))
        except Exception:
            py = ""
        cp, cg = cov(py, c["L"]), cov(gas.get(c["t"], ""), c["L"])
        if abs(cp - cg) >= THRESHOLD:
            out[c["t"]] = {"web": round(cp, 2), "gas": round(cg, 2)}
    return out


@pytest.fixture(scope="module")
def measured():
    return measure()


def test_no_new_surface_divergence(measured):
    debt = json.loads(DEBT.read_text())["atoms"]
    new = {t: v for t, v in measured.items() if t not in debt}
    assert not new, (
        f"{len(new)} atom(s) render materially different content on web vs GAS/MCP "
        f"(field contract drift): {json.dumps(new, indent=1)}. Align the renderers "
        f"(GAS .gs and renderers/web_article.py) to the schema; do not add to the debt file."
    )


def test_paid_debt_is_removed(measured):
    debt = json.loads(DEBT.read_text())["atoms"]
    paid = sorted(t for t in debt if t not in measured)
    assert not paid, (f"{paid} no longer diverge -- remove them from "
                      f"tests/surface_parity_debt.json (debt list only shrinks).")


if __name__ == "__main__":       # record the current measurement as the debt baseline
    m = measure()
    DEBT.write_text(json.dumps({"threshold": THRESHOLD, "note": __doc__.split("\n\n")[2],
                                "atoms": dict(sorted(m.items()))}, indent=1) + "\n")
    print(len(m), "atoms recorded in", DEBT.relative_to(ROOT))
