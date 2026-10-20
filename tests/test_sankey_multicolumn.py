"""sankey_flow draws real columns (owner decision D3, 2026-10-20).

Before: the web renderer knew two columns (anything with column != 0 landed on the right, a node that was both a source and a target dropped its
incoming flow) and the Apps Script renderer drew a grouped bar list. Now both renderers run the same port of d3-sankey 0.12.3 and emit the same SVG.

What is pinned here:
* GOLDEN: node x0/x1/y0/y1/value, link width/y0/y1 and the link paths from REAL d3-sankey 0.12.3 (run in node, see the recipe below) against the Python and
  the Apps Script layout, to 1e-9. Payloads: the web-preview sample, a 3-column chain, an 8x8 with crossings, links-only, mixed `column` hints, a
  payload with a cycle (after the cycle pre-pass), and a 5-column chain.
* PARITY: Python and GAS emit the same HTML, byte for byte after the usual id normalisation, for each payload and for a fuzz of malformed ones.
* BROWSER: in headless Chromium nodes never overlap, link ends sit on nodes, and the chart never widens a 320 / 600 / 1200 px container.

Golden recipe (the script lives outside the repo): `npm pack d3-sankey@0.12.3 d3-shape@1.3.7 d3-path@1.0.9 d3-array@1.2.4`, and per payload run
`sankey().nodeId(d => d.id).nodeWidth(16).nodePadding(16).iterations(6).extent([[padL, 50], [W - padL', 300]])` over the flows in D3_KEPT with
`nodeAlign(n => n.column ?? sankeyJustify(n, x))` and read the nodes and links back. The cycle pre-pass is the renderers' own (d3 refuses a cyclic
graph), so D3_KEPT names, by hand, the flows that survive it.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from test_motion_atoms import _node, core_js  # noqa: F401  (core_js is a fixture)
from renderers import web_article as wa

CHROMIUM = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
browser = pytest.mark.skipif(not CHROMIUM, reason="no Chromium installed")


def _nodes(*specs):
    out = []
    for s in specs:
        n = {"id": s[0], "label": s[1]}
        if len(s) > 2 and s[2] is not None:
            n["column"] = s[2]
        out.append(n)
    return out


def _lcg_links():
    """8 sources x 8 targets, 24 crossing flows, deterministic."""
    seed, links = 12345, []
    for k in range(24):
        seed = (seed * 1103515245 + 12345) % 2147483648
        s = (seed >> 10) % 8
        seed = (seed * 1103515245 + 12345) % 2147483648
        t = (seed >> 10) % 8
        seed = (seed * 1103515245 + 12345) % 2147483648
        links.append({"source": f"s{s}", "target": f"t{t}", "value": 1 + (seed >> 10) % 40})
    out, seen = [], set()
    for l in links:
        if (l["source"], l["target"]) not in seen:
            seen.add((l["source"], l["target"]))
            out.append(l)
    return out


PAYLOADS = {
    # scripts/build_web_preview.py: 1 -> 3
    "sample_1to3": {
        "type": "sankey_flow", "title": "Atoms by surface",
        "nodes": [{"id": "atoms", "label": "220 Atoms", "column": 0, "color": "#6366f1"}, {"id": "web", "label": "Web", "column": 1, "color": "#3b82f6"},
                  {"id": "stage", "label": "Stage", "column": 1, "color": "#8b5cf6"}, {"id": "email", "label": "Email", "column": 1, "color": "#10b981"}],
        "links": [{"source": "atoms", "target": "web", "value": 220}, {"source": "atoms", "target": "stage", "value": 148}, {"source": "atoms", "target": "email", "value": 95}],
    },
    # no `column` anywhere: depth places the nodes (the old code dropped every flow into B)
    "three_col": {
        "type": "sankey_flow", "title": "Budget to outcome",
        "nodes": _nodes(("rev", "Revenue"), ("grant", "Grants"), ("ops", "Operations"), ("rnd", "R&D"), ("mkt", "Marketing"), ("ship", "Shipped"), ("cash", "Cash")),
        "links": [{"source": "rev", "target": "ops", "value": 60}, {"source": "rev", "target": "rnd", "value": 25}, {"source": "rev", "target": "mkt", "value": 15},
                  {"source": "grant", "target": "rnd", "value": 30}, {"source": "ops", "target": "ship", "value": 40}, {"source": "ops", "target": "cash", "value": 20},
                  {"source": "rnd", "target": "ship", "value": 45}, {"source": "rnd", "target": "cash", "value": 10}, {"source": "mkt", "target": "cash", "value": 15}],
    },
    "big_8x8": {
        "type": "sankey_flow", "title": "8 x 8",
        "nodes": [{"id": f"s{i}", "label": f"Source {i}"} for i in range(8)] + [{"id": f"t{i}", "label": f"Target {i}"} for i in range(8)],
        "links": _lcg_links(),
    },
    # links only: nodes are made up from the ids
    "links_only": {
        "type": "sankey_flow",
        "links": [{"source": "alpha", "target": "gamma", "value": 7}, {"source": "alpha", "target": "delta", "value": 3}, {"source": "beta", "target": "gamma", "value": 4},
                  {"source": "beta", "target": "delta", "value": 6}, {"source": "beta", "target": "epsilon", "value": 2}, {"source": "gamma", "target": "zeta", "value": 5}],
    },
    # some nodes carry a `column` hint, others do not
    "mixed_columns": {
        "type": "sankey_flow", "title": "Mixed",
        "nodes": _nodes(("p", "P", 0), ("q", "Q", 1), ("r", "R", 2), ("s", "S"), ("t", "T"), ("u", "U", 2)),
        "links": [{"source": "p", "target": "q", "value": 6}, {"source": "q", "target": "r", "value": 4}, {"source": "r", "target": "s", "value": 3},
                  {"source": "s", "target": "t", "value": 2}, {"source": "p", "target": "u", "value": 3}, {"source": "u", "target": "s", "value": 2}],
    },
    # b <-> c is a cycle: both of its flows are listed as not shown, the rest is drawn
    "cyclic_partial": {
        "type": "sankey_flow", "title": "Cycle inside",
        "nodes": _nodes(("a", "Alpha"), ("b", "Beta"), ("c", "Gamma"), ("d", "Delta"), ("e", "Epsilon")),
        "links": [{"source": "a", "target": "b", "value": 5}, {"source": "b", "target": "c", "value": 3}, {"source": "c", "target": "b", "value": 1},
                  {"source": "a", "target": "d", "value": 2}, {"source": "d", "target": "e", "value": 2}],
    },
    "five_col": {
        "type": "sankey_flow", "title": "Funnel",
        "nodes": _nodes(("v", "Visits", 0), ("s", "Signups", 1), ("t", "Trials", 2), ("p", "Paid", 3), ("r", "Renewed", 4), ("x", "Left", 4)),
        "links": [{"source": "v", "target": "s", "value": 100}, {"source": "s", "target": "t", "value": 60}, {"source": "t", "target": "p", "value": 30},
                  {"source": "p", "target": "r", "value": 22}, {"source": "p", "target": "x", "value": 8}, {"source": "v", "target": "x", "value": 5}],
    },
}

# the flows (indices into each payload's links) d3 is given; everything but cyclic_partial keeps all of them
D3_KEPT = {k: list(range(len(v["links"]))) for k, v in PAYLOADS.items()}
D3_KEPT["cyclic_partial"] = [0, 3, 4]
# five_col: v -> x skips ahead, which is fine; nothing is dropped
EXPECT_COLS = {"sample_1to3": 2, "three_col": 3, "big_8x8": 2, "links_only": 3, "mixed_columns": 5, "cyclic_partial": 3, "five_col": 5}

CYCLIC_SANKEY = {
    "type": "sankey_flow", "title": "Cyclic",
    "nodes": [{"id": "a", "label": "Alpha"}, {"id": "b", "label": "Beta"}],
    "links": [{"source": "a", "target": "b", "value": 5}, {"source": "b", "target": "a", "value": 0.3}],
}

# GOLDEN-BEGIN
GOLDEN = {"sample_1to3":{"nodes":[{"id":"atoms","layer":0,"x0":77,"x1":93,"y0":58.99455344468449,"y1":276.9945534446844,"value":463},{"id":"web","layer":1,"x0":564,"x1":580,"y0":50,"y1":153.58531317494598,"value":220},{"id":"stage","layer":1,"x0":564,"x1":580,"y0":169.58531317494598,"y1":239.26997840172785,"value":148},{"id":"email","layer":1,"x0":564,"x1":580,"y0":255.26997840172785,"y1":300.00000000000006,"value":95}],"links":[{"orig":0,"source":"atoms","target":"web","value":220,"width":103.58531317494601,"y0":110.7872100321575,"y1":101.792656587473,"d":"M93,110.7872100321575C328.5,110.7872100321575,328.5,101.792656587473,564,101.792656587473"},{"orig":1,"source":"atoms","target":"stage","value":148,"width":69.68466522678186,"y0":197.42219923302144,"y1":204.42764578833692,"d":"M93,197.42219923302144C328.5,197.42219923302144,328.5,204.42764578833692,564,204.42764578833692"},{"orig":2,"source":"atoms","target":"email","value":95,"width":44.73002159827214,"y0":254.6295426455484,"y1":277.6349892008639,"d":"M93,254.6295426455484C328.5,254.6295426455484,328.5,277.6349892008639,564,277.6349892008639"}],"padL":77,"padR":60,"W":640},"three_col":{"nodes":[{"id":"rev","layer":0,"x0":63,"x1":79,"y0":50,"y1":217.6923076923078,"value":100},{"id":"grant","layer":0,"x0":63,"x1":79,"y0":233.6923076923078,"y1":284.0000000000001,"value":30},{"id":"ops","layer":1,"x0":422,"x1":438,"y0":50,"y1":150.61538461538458,"value":60},{"id":"rnd","layer":1,"x0":422,"x1":438,"y0":166.61538461538458,"y1":258.8461538461538,"value":55},{"id":"mkt","layer":1,"x0":422,"x1":438,"y0":274.8461538461538,"y1":300,"value":15},{"id":"ship","layer":2,"x0":781,"x1":797,"y0":50,"y1":192.53846153846155,"value":85},{"id":"cash","layer":2,"x0":781,"x1":797,"y0":208.53846153846155,"y1":284,"value":45}],"links":[{"orig":0,"source":"rev","target":"ops","value":60,"width":100.61538461538461,"y0":100.3076923076923,"y1":100.3076923076923,"d":"M79,100.3076923076923C250.5,100.3076923076923,250.5,100.3076923076923,422,100.3076923076923"},{"orig":1,"source":"rev","target":"rnd","value":25,"width":41.92307692307693,"y0":171.57692307692307,"y1":187.57692307692304,"d":"M79,171.57692307692307C250.5,171.57692307692307,250.5,187.57692307692304,422,187.57692307692304"},{"orig":2,"source":"rev","target":"mkt","value":15,"width":25.153846153846153,"y0":205.1153846153846,"y1":287.4230769230769,"d":"M79,205.1153846153846C250.5,205.1153846153846,250.5,287.4230769230769,422,287.4230769230769"},{"orig":3,"source":"grant","target":"rnd","value":30,"width":50.30769230769231,"y0":258.8461538461539,"y1":233.69230769230768,"d":"M79,258.8461538461539C250.5,258.8461538461539,250.5,233.69230769230768,422,233.69230769230768"},{"orig":4,"source":"ops","target":"ship","value":40,"width":67.07692307692308,"y0":83.53846153846155,"y1":83.53846153846155,"d":"M438,83.53846153846155C609.5,83.53846153846155,609.5,83.53846153846155,781,83.53846153846155"},{"orig":5,"source":"ops","target":"cash","value":20,"width":33.53846153846154,"y0":133.84615384615384,"y1":225.30769230769232,"d":"M438,133.84615384615384C609.5,133.84615384615384,609.5,225.30769230769232,781,225.30769230769232"},{"orig":6,"source":"rnd","target":"ship","value":45,"width":75.46153846153847,"y0":204.3461538461538,"y1":154.80769230769232,"d":"M438,204.3461538461538C609.5,204.3461538461538,609.5,154.80769230769232,781,154.80769230769232"},{"orig":7,"source":"rnd","target":"cash","value":10,"width":16.76923076923077,"y0":250.46153846153842,"y1":250.46153846153848,"d":"M438,250.46153846153842C609.5,250.46153846153842,609.5,250.46153846153848,781,250.46153846153848"},{"orig":8,"source":"mkt","target":"cash","value":15,"width":25.153846153846153,"y0":287.4230769230769,"y1":271.42307692307696,"d":"M438,287.4230769230769C609.5,287.4230769230769,609.5,271.42307692307696,781,271.42307692307696"}],"padL":63,"padR":63,"W":860},"big_8x8":{"nodes":[{"id":"s0","layer":0,"x0":70,"x1":86,"y0":94.67901234567901,"y1":118.81481481481488,"value":85},{"id":"s1","layer":0,"x0":70,"x1":86,"y0":225.97530864197543,"y1":245.00000000000014,"value":67},{"id":"s2","layer":0,"x0":70,"x1":86,"y0":159.33333333333343,"y1":180.62962962962976,"value":75},{"id":"s3","layer":0,"x0":70,"x1":86,"y0":134.8148148148149,"y1":143.33333333333343,"value":30},{"id":"s4","layer":0,"x0":70,"x1":86,"y0":196.62962962962976,"y1":209.97530864197543,"value":47},{"id":"s5","layer":0,"x0":70,"x1":86,"y0":50,"y1":78.67901234567901,"value":101},{"id":"s6","layer":0,"x0":70,"x1":86,"y0":294.888888888889,"y1":300.00000000000017,"value":18},{"id":"s7","layer":0,"x0":70,"x1":86,"y0":261.0000000000001,"y1":278.888888888889,"value":63},{"id":"t0","layer":1,"x0":554,"x1":570,"y0":73.66666666666666,"y1":90.41975308641975,"value":59},{"id":"t1","layer":1,"x0":554,"x1":570,"y0":106.41975308641975,"y1":125.7283950617284,"value":68},{"id":"t2","layer":1,"x0":554,"x1":570,"y0":50,"y1":57.66666666666666,"value":27},{"id":"t3","layer":1,"x0":554,"x1":570,"y0":141.7283950617284,"y1":171.2592592592593,"value":104},{"id":"t4","layer":1,"x0":554,"x1":570,"y0":222.85185185185188,"y1":234.2098765432099,"value":40},{"id":"t5","layer":1,"x0":554,"x1":570,"y0":250.2098765432099,"y1":257.87654320987656,"value":27},{"id":"t6","layer":1,"x0":554,"x1":570,"y0":273.87654320987656,"y1":300,"value":92},{"id":"t7","layer":1,"x0":554,"x1":570,"y0":187.2592592592593,"y1":206.85185185185188,"value":69}],"links":[{"orig":0,"source":"s5","target":"t1","value":16,"width":4.54320987654321,"y0":69.30864197530865,"y1":108.69135802469135,"d":"M86,69.30864197530865C320,69.30864197530865,320,108.69135802469135,554,108.69135802469135"},{"orig":1,"source":"s5","target":"t7","value":25,"width":7.098765432098765,"y0":75.12962962962963,"y1":190.8086419753087,"d":"M86,75.12962962962963C320,75.12962962962963,320,190.8086419753087,554,190.8086419753087"},{"orig":2,"source":"s3","target":"t3","value":30,"width":8.518518518518517,"y0":139.07407407407416,"y1":156.7777777777778,"d":"M86,139.07407407407416C320,139.07407407407416,320,156.7777777777778,554,156.7777777777778"},{"orig":3,"source":"s4","target":"t1","value":20,"width":5.679012345679012,"y0":199.46913580246925,"y1":122.88888888888889,"d":"M86,199.46913580246925C320,199.46913580246925,320,122.88888888888889,554,122.88888888888889"},{"orig":4,"source":"s4","target":"t5","value":27,"width":7.666666666666666,"y0":206.14197530864212,"y1":254.04320987654324,"d":"M86,206.14197530864212C320,206.14197530864212,320,254.04320987654324,554,254.04320987654324"},{"orig":5,"source":"s6","target":"t6","value":18,"width":5.111111111111111,"y0":297.44444444444457,"y1":297.44444444444446,"d":"M86,297.44444444444457C320,297.44444444444457,320,297.44444444444446,554,297.44444444444446"},{"orig":6,"source":"s2","target":"t1","value":32,"width":9.08641975308642,"y0":163.87654320987664,"y1":115.50617283950618,"d":"M86,163.87654320987664C320,163.87654320987664,320,115.50617283950618,554,115.50617283950618"},{"orig":7,"source":"s0","target":"t3","value":38,"width":10.790123456790123,"y0":107.4567901234568,"y1":147.12345679012347,"d":"M86,107.4567901234568C320,107.4567901234568,320,147.12345679012347,554,147.12345679012347"},{"orig":8,"source":"s0","target":"t0","value":26,"width":7.382716049382716,"y0":98.37037037037037,"y1":86.72839506172838,"d":"M86,98.37037037037037C320,98.37037037037037,320,86.72839506172838,554,86.72839506172838"},{"orig":9,"source":"s7","target":"t6","value":17,"width":4.827160493827161,"y0":276.4753086419754,"y1":292.47530864197535,"d":"M86,276.4753086419754C320,276.4753086419754,320,292.47530864197535,554,292.47530864197535"},{"orig":10,"source":"s7","target":"t7","value":27,"width":7.666666666666666,"y0":264.8333333333334,"y1":203.01851851851856,"d":"M86,264.8333333333334C320,264.8333333333334,320,203.01851851851856,554,203.01851851851856"},{"orig":11,"source":"s1","target":"t6","value":31,"width":8.802469135802468,"y0":240.5987654320989,"y1":285.6604938271605,"d":"M86,240.5987654320989C320,240.5987654320989,320,285.6604938271605,554,285.6604938271605"},{"orig":12,"source":"s5","target":"t2","value":27,"width":7.666666666666666,"y0":53.833333333333336,"y1":53.833333333333336,"d":"M86,53.833333333333336C320,53.833333333333336,320,53.833333333333336,554,53.833333333333336"},{"orig":13,"source":"s2","target":"t7","value":17,"width":4.827160493827161,"y0":170.83333333333343,"y1":196.77160493827162,"d":"M86,170.83333333333343C320,170.83333333333343,320,196.77160493827162,554,196.77160493827162"},{"orig":14,"source":"s2","target":"t6","value":26,"width":7.382716049382716,"y0":176.9382716049384,"y1":277.5679012345679,"d":"M86,176.9382716049384C320,176.9382716049384,320,277.5679012345679,554,277.5679012345679"},{"orig":15,"source":"s1","target":"t3","value":36,"width":10.222222222222221,"y0":231.08641975308655,"y1":166.14814814814815,"d":"M86,231.08641975308655C320,231.08641975308655,320,166.14814814814815,554,166.14814814814815"},{"orig":16,"source":"s7","target":"t4","value":19,"width":5.395061728395062,"y0":271.3641975308643,"y1":231.51234567901236,"d":"M86,271.3641975308643C320,271.3641975308643,320,231.51234567901236,554,231.51234567901236"},{"orig":17,"source":"s5","target":"t0","value":33,"width":9.37037037037037,"y0":62.35185185185185,"y1":78.35185185185185,"d":"M86,62.35185185185185C320,62.35185185185185,320,78.35185185185185,554,78.35185185185185"},{"orig":18,"source":"s0","target":"t4","value":21,"width":5.962962962962963,"y0":115.83333333333334,"y1":225.83333333333337,"d":"M86,115.83333333333334C320,115.83333333333334,320,225.83333333333337,554,225.83333333333337"}],"padL":70,"padR":70,"W":640},"links_only":{"nodes":[{"id":"alpha","layer":0,"x0":60,"x1":76,"y0":50,"y1":156.36363636363637,"value":10},{"id":"gamma","layer":1,"x0":420.5,"x1":436.5,"y0":117.28612418485422,"y1":234.2861241848542,"value":11},{"id":"delta","layer":2,"x0":781,"x1":797,"y0":50,"y1":145.72727272727275,"value":9},{"id":"beta","layer":0,"x0":60,"x1":76,"y0":172.36363636363637,"y1":299.99999999999994,"value":12},{"id":"epsilon","layer":2,"x0":781,"x1":797,"y0":278.7272727272728,"y1":300,"value":2},{"id":"zeta","layer":2,"x0":781,"x1":797,"y0":161.72727272727275,"y1":214.90909090909085,"value":5}],"links":[{"orig":0,"source":"alpha","target":"gamma","value":7,"width":74.45454545454545,"y0":119.13636363636363,"y1":154.51339691212695,"d":"M76,119.13636363636363C248.25,119.13636363636363,248.25,154.51339691212695,420.5,154.51339691212695"},{"orig":1,"source":"alpha","target":"delta","value":3,"width":31.90909090909091,"y0":65.95454545454545,"y1":65.95454545454545,"d":"M76,65.95454545454545C428.5,65.95454545454545,428.5,65.95454545454545,781,65.95454545454545"},{"orig":2,"source":"beta","target":"gamma","value":4,"width":42.54545454545455,"y0":257.45454545454544,"y1":213.01339691212695,"d":"M76,257.45454545454544C248.25,257.45454545454544,248.25,213.01339691212695,420.5,213.01339691212695"},{"orig":3,"source":"beta","target":"delta","value":6,"width":63.81818181818182,"y0":204.27272727272728,"y1":113.81818181818181,"d":"M76,204.27272727272728C428.5,204.27272727272728,428.5,113.81818181818181,781,113.81818181818181"},{"orig":4,"source":"beta","target":"epsilon","value":2,"width":21.272727272727273,"y0":289.3636363636364,"y1":289.36363636363643,"d":"M76,289.3636363636364C428.5,289.3636363636364,428.5,289.36363636363643,781,289.36363636363643"},{"orig":5,"source":"gamma","target":"zeta","value":5,"width":53.18181818181819,"y0":143.87703327576332,"y1":188.31818181818184,"d":"M436.5,143.87703327576332C608.75,143.87703327576332,608.75,188.31818181818184,781,188.31818181818184"}],"padL":60,"padR":63,"W":860},"mixed_columns":{"nodes":[{"id":"p","layer":0,"x0":60,"x1":76,"y0":50,"y1":300.00000000000006,"value":9},{"id":"q","layer":1,"x0":351,"x1":367,"y0":50,"y1":216.66666666666669,"value":6},{"id":"r","layer":2,"x0":642,"x1":658,"y0":50,"y1":161.11111111111114,"value":4},{"id":"s","layer":3,"x0":933,"x1":949,"y0":83.33200016524557,"y1":222.2208890541345,"value":5},{"id":"t","layer":4,"x0":1224,"x1":1240,"y0":83.3306671937539,"y1":138.8862227493095,"value":2},{"id":"u","layer":2,"x0":642,"x1":658,"y0":216.66666666666669,"y1":300,"value":3}],"links":[{"orig":0,"source":"p","target":"q","value":6,"width":166.66666666666669,"y0":133.33333333333334,"y1":133.33333333333334,"d":"M76,133.33333333333334C213.5,133.33333333333334,213.5,133.33333333333334,351,133.33333333333334"},{"orig":1,"source":"q","target":"r","value":4,"width":111.11111111111111,"y0":105.55555555555556,"y1":105.55555555555556,"d":"M367,105.55555555555556C504.5,105.55555555555556,504.5,105.55555555555556,642,105.55555555555556"},{"orig":2,"source":"r","target":"s","value":3,"width":83.33333333333334,"y0":91.66666666666667,"y1":124.99866683191225,"d":"M658,91.66666666666667C795.5,91.66666666666667,795.5,124.99866683191225,933,124.99866683191225"},{"orig":3,"source":"s","target":"t","value":2,"width":55.55555555555556,"y0":111.10977794302335,"y1":111.10844497153167,"d":"M949,111.10977794302335C1086.5,111.10977794302335,1086.5,111.10844497153167,1224,111.10844497153167"},{"orig":4,"source":"p","target":"u","value":3,"width":83.33333333333334,"y0":258.33333333333337,"y1":258.33333333333337,"d":"M76,258.33333333333337C359,258.33333333333337,359,258.33333333333337,642,258.33333333333337"},{"orig":5,"source":"u","target":"s","value":2,"width":55.55555555555556,"y0":244.44444444444446,"y1":194.4431112763567,"d":"M658,244.44444444444446C795.5,244.44444444444446,795.5,194.4431112763567,933,194.4431112763567"}],"padL":60,"padR":60,"W":1300},"cyclic_partial":{"nodes":[{"id":"a","layer":0,"x0":60,"x1":76,"y0":51.06251636343419,"y1":285.0625163634342,"value":7},{"id":"b","layer":2,"x0":781,"x1":797,"y0":50,"y1":217.1428571428571,"value":5},{"id":"d","layer":1,"x0":420.5,"x1":436.5,"y0":226.41399799693662,"y1":293.2711408540796,"value":2},{"id":"e","layer":2,"x0":781,"x1":797,"y0":233.1428571428571,"y1":299.99999999999994,"value":2}],"links":[{"orig":0,"source":"a","target":"b","value":5,"width":167.14285714285717,"y0":134.63394493486277,"y1":133.57142857142858,"d":"M76,134.63394493486277C428.5,134.63394493486277,428.5,133.57142857142858,781,133.57142857142858"},{"orig":3,"source":"a","target":"d","value":2,"width":66.85714285714286,"y0":251.63394493486277,"y1":259.84256942550803,"d":"M76,251.63394493486277C248.25,251.63394493486277,248.25,259.84256942550803,420.5,259.84256942550803"},{"orig":4,"source":"d","target":"e","value":2,"width":66.85714285714286,"y0":259.84256942550803,"y1":266.57142857142856,"d":"M436.5,259.84256942550803C608.75,259.84256942550803,608.75,266.57142857142856,781,266.57142857142856"}],"padL":60,"padR":63,"W":860},"five_col":{"nodes":[{"id":"v","layer":0,"x0":60,"x1":76,"y0":50.000000000000014,"y1":300,"value":105},{"id":"s","layer":1,"x0":350.25,"x1":366.25,"y0":50,"y1":288.0952380952381,"value":100},{"id":"t","layer":2,"x0":640.5,"x1":656.5,"y0":51.82492216131598,"y1":194.68206501845884,"value":60},{"id":"p","layer":3,"x0":930.75,"x1":946.75,"y0":53.654458403245854,"y1":125.08302983181733,"value":30},{"id":"r","layer":4,"x0":1221,"x1":1237,"y0":50,"y1":102.38095238095238,"value":22},{"id":"x","layer":4,"x0":1221,"x1":1237,"y0":240.62965545663667,"y1":271.5820364090176,"value":13}],"links":[{"orig":0,"source":"v","target":"s","value":100,"width":238.0952380952381,"y0":169.04761904761907,"y1":169.04761904761904,"d":"M76,169.04761904761907C213.125,169.04761904761907,213.125,169.04761904761904,350.25,169.04761904761904"},{"orig":1,"source":"s","target":"t","value":60,"width":142.85714285714286,"y0":121.42857142857143,"y1":123.25349358988741,"d":"M366.25,121.42857142857143C503.375,121.42857142857143,503.375,123.25349358988741,640.5,123.25349358988741"},{"orig":2,"source":"t","target":"p","value":30,"width":71.42857142857143,"y0":87.5392078756017,"y1":89.36874411753158,"d":"M656.5,87.5392078756017C793.625,87.5392078756017,793.625,89.36874411753158,930.75,89.36874411753158"},{"orig":3,"source":"p","target":"r","value":22,"width":52.38095238095238,"y0":79.84493459372204,"y1":76.19047619047619,"d":"M946.75,79.84493459372204C1083.875,79.84493459372204,1083.875,76.19047619047619,1221,76.19047619047619"},{"orig":4,"source":"p","target":"x","value":8,"width":19.047619047619047,"y0":115.55922030800775,"y1":262.0582268852081,"d":"M946.75,115.55922030800775C1083.875,115.55922030800775,1083.875,262.0582268852081,1221,262.0582268852081"},{"orig":5,"source":"v","target":"x","value":5,"width":11.904761904761905,"y0":294.0476190476191,"y1":246.58203640901763,"d":"M76,294.0476190476191C648.5,294.0476190476191,648.5,246.58203640901763,1221,246.58203640901763"}],"padL":60,"padR":63,"W":1300}}
# GOLDEN-END


# ── the model, from either renderer, as plain data ───────────────────────────────────────────────────────────────
def _plain(m):
    nodes = m["nodes"]
    return {
        "ncols": m["ncols"], "w": m["w"], "h": m["h"], "padL": m["padL"], "padR": m["padR"],
        "dropped": m["dropped"],
        "nodes": [{k: n[k] for k in ("id", "label", "layer", "x0", "x1", "y0", "y1", "value")} for n in nodes],
        "links": [{"source": l["source"]["id"], "target": l["target"]["id"], "value": l["value"], "width": l["width"], "y0": l["y0"], "y1": l["y1"]} for l in m["links"]],
    }


def _py_model(payload):
    return _plain(wa._sk_model(json.loads(json.dumps(payload))))


_JS_PLAIN = """function _plain(m){return {ncols:m.ncols,w:m.w,h:m.h,padL:m.padL,padR:m.padR,dropped:m.dropped,
 nodes:m.nodes.map(function(n){return {id:n.id,label:n.label,layer:n.layer,x0:n.x0,x1:n.x1,y0:n.y0,y1:n.y1,value:n.value};}),
 links:m.links.map(function(l){return {source:l.source.id,target:l.target.id,value:l.value,width:l.width,y0:l.y0,y1:l.y1};})};}"""


def _gas_models(core_js, payloads):
    return _node(core_js, _JS_PLAIN + "var B = " + json.dumps(payloads) + "; console.log(JSON.stringify(B.map(function(b){ return _plain(_skModel(b)); })));")


def _gas_html(core_js, payloads):
    # the GAS renderer without its accessibility post-pass (_a11yFix): the Python twin is compared before that step, like tests/test_gas_twins.py
    payloads = [{"type": "sankey_flow", **p} for p in payloads]
    return _node(core_js, "_a11yFix = function(h) { return h; }; var B = " + json.dumps(payloads) + "; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")


def _py_html(payload):
    return wa._RENDERERS["sankey_flow"](json.loads(json.dumps(payload)))


def _nums(d):
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?", d)]


def _check_against_golden(got, gold, name):
    gn = {n["id"]: n for n in got["nodes"]}
    assert set(gn) == {n["id"] for n in gold["nodes"]}, name
    for g in gold["nodes"]:
        n = gn[g["id"]]
        assert n["layer"] == g["layer"], (name, g["id"], "layer")
        for k in ("x0", "x1", "y0", "y1", "value"):
            assert abs(n[k] - g[k]) < 1e-9, (name, g["id"], k, n[k], g[k])
    assert len(got["links"]) == len(gold["links"]), name
    for i, (l, g) in enumerate(zip(got["links"], gold["links"])):
        assert (l["source"], l["target"]) == (g["source"], g["target"]), (name, i)
        for k in ("value", "width", "y0", "y1"):
            assert abs(l[k] - g[k]) < 1e-9, (name, i, k, l[k], g[k])


def _golden_cases():
    return sorted(PAYLOADS)


def test_golden_is_present():
    assert set(GOLDEN) == set(PAYLOADS), "regenerate the golden vectors (see the module docstring)"


@pytest.mark.parametrize("name", _golden_cases())
def test_python_layout_matches_real_d3_sankey(name):
    got = _py_model(PAYLOADS[name])
    _check_against_golden(got, GOLDEN[name], name)
    assert got["ncols"] == EXPECT_COLS[name]
    assert (got["padL"], got["padR"]) == (GOLDEN[name]["padL"], GOLDEN[name]["padR"])


def test_gas_layout_matches_real_d3_sankey(core_js):
    names = _golden_cases()
    got = _gas_models(core_js, [PAYLOADS[n] for n in names])
    for n, g in zip(names, got):
        _check_against_golden(g, GOLDEN[n], n)
        assert g["ncols"] == EXPECT_COLS[n]
        assert (g["padL"], g["padR"]) == (GOLDEN[n]["padL"], GOLDEN[n]["padR"])


def test_python_and_gas_models_are_identical(core_js):
    names = _golden_cases() + ["cyclic_orig"]
    pl = {**PAYLOADS, "cyclic_orig": CYCLIC_SANKEY}
    gas = _gas_models(core_js, [pl[n] for n in names])
    for n, g in zip(names, gas):
        assert _py_model(pl[n]) == g, n


# ── path strings: d3's sankeyLinkHorizontal, to the 2 decimals we print ───────────────────────────────────────────
@pytest.mark.parametrize("name", _golden_cases())
def test_link_paths_are_d3s_horizontal_bezier(name):
    html = _py_html(PAYLOADS[name])
    paths = re.findall(r'<path class="sk-l" d="([^"]+)"', html)
    gold = GOLDEN[name]["links"]
    assert len(paths) == len(gold)
    for d, g in zip(paths, gold):
        a, b = _nums(d), _nums(g["d"])
        assert re.match(r"^M[\d.-]+,[\d.-]+C[\d.-]+,[\d.-]+,[\d.-]+,[\d.-]+,[\d.-]+,[\d.-]+$", d), d
        assert len(a) == len(b) == 8
        assert all(abs(x - y) <= 0.0051 for x, y in zip(a, b)), (d, g["d"])


# ── contract: columns, width, cycles, empty ────────────────────────────────────────────────────────────────────────
def test_column_hint_gives_real_columns():
    m = _py_model(PAYLOADS["five_col"])
    assert {n["id"]: n["layer"] for n in m["nodes"]} == {"v": 0, "s": 1, "t": 2, "p": 3, "r": 4, "x": 4}
    xs = sorted({n["x0"] for n in m["nodes"]})
    assert len(xs) == 5 and all(b > a for a, b in zip(xs, xs[1:]))


def test_width_rule_is_640_plus_220_per_extra_column():
    assert _py_model(PAYLOADS["sample_1to3"])["w"] == 640
    assert _py_model(PAYLOADS["three_col"])["w"] == 860
    assert _py_model(PAYLOADS["five_col"])["w"] == 1300
    assert 'viewBox="0 0 1300 340"' in _py_html(PAYLOADS["five_col"])
    assert 'viewBox="0 0 640 340"' in _py_html(PAYLOADS["sample_1to3"])


def test_zero_one_columns_keep_todays_sides():
    """0 stays left, 1 goes right, and a column-less sink goes right, as before."""
    m = _py_model({"nodes": [{"id": "a", "column": 0}, {"id": "b", "column": 1}, {"id": "c"}], "links": [{"source": "a", "target": "b", "value": 1}, {"source": "a", "target": "c", "value": 2}]})
    assert {n["id"]: n["layer"] for n in m["nodes"]} == {"a": 0, "b": 1, "c": 1}
    assert m["dropped"] == []
    # old behaviour kept: a flow from the right column back to the left is not drawn and is listed
    m = _py_model({"nodes": [{"id": "a", "column": 0}, {"id": "b", "column": 1}], "links": [{"source": "a", "target": "b", "value": 1}, {"source": "b", "target": "a", "value": 2}]})
    assert [d["value"] for d in m["dropped"]] == [1, 2] and m["links"] == []


def test_cycle_flows_are_dropped_and_noted_in_both_renderers(core_js):
    py = _py_model(PAYLOADS["cyclic_partial"])
    assert [(d["source"], d["target"]) for d in py["dropped"]] == [("Beta", "Gamma"), ("Gamma", "Beta")]
    assert [(l["source"], l["target"]) for l in py["links"]] == [("a", "b"), ("a", "d"), ("d", "e")]
    for html in (_py_html(PAYLOADS["cyclic_partial"]), _gas_html(core_js, [PAYLOADS["cyclic_partial"]])[0]):
        assert 'role="note"' in html and "2 flows not shown." in html
        assert "<li>Beta → Gamma: 3</li>" in html and "<li>Gamma → Beta: 1</li>" in html
    only = _py_html(CYCLIC_SANKEY)
    assert "<svg" not in only and "2 flows not shown." in only      # nothing left to draw: just the note


def test_empty_and_malformed_payloads_render_nothing_or_a_note_and_do_not_throw(core_js):
    cases = [{}, {"links": []}, {"links": "x", "nodes": 4}, {"links": [None, 3, {"source": "a"}, {"source": "a", "target": "a", "value": 2}]},
             {"links": [{"source": "a", "target": "b", "value": 0}, {"source": "a", "target": "b", "value": -3}, {"source": "a", "target": "b", "value": "nope"}]}]
    gas = _gas_html(core_js, cases)
    for c, g in zip(cases, gas):
        h = _py_html(c)
        assert "<svg" not in h and "<svg" not in g
    assert "1 flow not shown." in _py_html(cases[3])


def test_no_script_and_accessible_name_and_hidden_table(core_js):
    for html in [_py_html(p) for p in PAYLOADS.values()] + _gas_html(core_js, list(PAYLOADS.values())):
        assert "<script" not in html and "onmouse" not in html and "onclick" not in html
        assert '<svg role="img" aria-label="' in html
        assert "<title>" in html
        assert '<th scope="col">Source</th><th scope="col">Target</th><th scope="col">Value</th>' in html
        assert "clip:rect(0 0 0 0)" in html


def test_hidden_table_lists_every_drawn_flow():
    html = _py_html(PAYLOADS["sample_1to3"])
    assert "<tr><th scope=\"row\">220 Atoms</th><td>Web</td><td>220</td></tr>" in html
    assert html.count("<tr><th scope=\"row\">") == 3


ATTACK = '"><img src=x onerror=alert(1)><script>alert(2)</script>'


def test_hostile_labels_and_colors_are_escaped_in_both_renderers(core_js):
    p = {"title": ATTACK, "nodes": [{"id": "a", "label": ATTACK, "color": ATTACK}, {"id": "b", "label": ATTACK}], "links": [{"source": "a", "target": "b", "value": 3, "color": ATTACK}]}
    for html in (_py_html(p), _gas_html(core_js, [p])[0]):
        assert "<img" not in html and "<script>alert" not in html and "&lt;img" in html


# ── Python and GAS output are the same text ────────────────────────────────────────────────────────────────────────
def _fuzz_cases():
    base = PAYLOADS["mixed_columns"]
    cases = []
    for k in ("title", "nodes", "links"):
        for v in (None, 7, True, "", [], {}, ATTACK):
            cases.append({**base, k: v})
    cases.append({**base, "nodes": [{**n, "column": c} for n, c in zip(base["nodes"], (0, "1", 1.7, -2, 99, None))]})
    cases.append({**base, "links": [{**l, "value": v} for l, v in zip(base["links"], (None, "3", "1e2", 0.005, 1e12, True))]})
    cases.append({**base, "nodes": [{"id": 1, "label": 2}, {"id": "1", "label": "dup"}, {"id": ""}, None, 5]})
    cases.append({"links": [{"source": 1, "target": 2, "value": 3}, {"source": "2", "target": "x", "value": 1.5}]})
    cases.append({"nodes": [{"id": "long", "label": "x" * 80, "column": 0}, {"id": "b", "label": "y" * 80}], "links": [{"source": "long", "target": "b", "value": 4}]})
    return cases


def test_python_and_gas_emit_the_same_html(core_js):
    cases = [dict(p) for p in PAYLOADS.values()] + [CYCLIC_SANKEY] + _fuzz_cases()
    gas = _gas_html(core_js, cases)
    bad = [i for i, (c, g) in enumerate(zip(cases, gas)) if _py_html(c) != g]
    assert not bad, [(i, cases[i]) for i in bad[:3]]


def test_many_flows_stay_fast_and_finite():
    links = [{"source": f"a{i % 30}", "target": f"b{(i * 7) % 30}", "value": 1 + i % 9} for i in range(300)]
    h = _py_html({"links": links})
    assert "NaN" not in h and "Infinity" not in h and "<svg" in h


# ── a real browser ─────────────────────────────────────────────────────────────────────────────────────────────────
_PROBE = r"""
(function(){
  var out = {};
  var c = document.getElementById('c'), svg = c.querySelector('svg');
  out.cw = c.getBoundingClientRect().width; out.csw = c.scrollWidth; out.dsw = document.documentElement.scrollWidth; out.iw = window.innerWidth;
  var card = c.firstElementChild; out.cardw = card.getBoundingClientRect().width;
  var rects = [].slice.call(svg.querySelectorAll('rect')).map(function(r){ return {x:+r.getAttribute('x'), y:+r.getAttribute('y'), w:+r.getAttribute('width'), h:+r.getAttribute('height')}; });
  out.overlap = 0;
  for (var i = 0; i < rects.length; i++) for (var j = i + 1; j < rects.length; j++) {
    var a = rects[i], b = rects[j];
    if (a.x < b.x + b.w - 0.01 && b.x < a.x + a.w - 0.01 && a.y < b.y + b.h - 0.01 && b.y < a.y + a.h - 0.01) out.overlap++;
  }
  var vb = svg.viewBox.baseVal; out.vbw = vb.width; out.vbh = vb.height;
  out.outside = rects.filter(function(r){ return r.x < -0.01 || r.y < -0.01 || r.x + r.w > vb.width + 0.01 || r.y + r.h > vb.height + 0.01; }).length;
  out.badEnds = 0; out.paths = 0;
  [].forEach.call(svg.querySelectorAll('path.sk-l'), function(p){
    var n = p.getAttribute('d').match(/-?\d+(?:\.\d+)?/g).map(Number); out.paths++;
    var sx = n[0], sy = n[1], ex = n[6], ey = n[7];
    var s = rects.some(function(r){ return Math.abs(r.x + r.w - sx) < 0.011 && sy >= r.y - 0.011 && sy <= r.y + r.h + 0.011; });
    var e = rects.some(function(r){ return Math.abs(r.x - ex) < 0.011 && ey >= r.y - 0.011 && ey <= r.y + r.h + 0.011; });
    if (!s || !e) out.badEnds++;
  });
  var sb = svg.getBoundingClientRect(); out.svgw = sb.width; out.svgh = sb.height;
  out.texts = [].filter.call(svg.querySelectorAll('text'), function(t){ var b = t.getBoundingClientRect(); return b.width > 0 && (b.left < -1); }).length;
  document.documentElement.setAttribute('data-probe', JSON.stringify(out));
})();
"""


def _probe(html, width):
    page = ("<!doctype html><meta charset=utf-8><body style='margin:0;background:#fff'><div style='width:%dpx' id=c>" % width) + html + "</div><script>" + _PROBE + "</script>"
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        prof = tempfile.mkdtemp(prefix="skprof")
        try:
            dump = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--use-angle=swiftshader", f"--user-data-dir={prof}",
                                   "--window-size=1500,1000", "--virtual-time-budget=1500", "--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=90).stdout
        finally:
            shutil.rmtree(prof, ignore_errors=True)
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", dump)
    assert m, dump[:300]
    import html as _h
    return json.loads(_h.unescape(m.group(1) or m.group(2)))


@browser
@pytest.mark.parametrize("name", sorted(PAYLOADS))
def test_browser_layout_nodes_apart_links_on_nodes_never_wider_than_container(name, core_js):
    gas = _gas_html(core_js, [PAYLOADS[name]])[0]
    for source, html in (("python", _py_html(PAYLOADS[name])), ("gas", gas)):
        for width in (320, 600, 1200):
            r = _probe(html, width)
            ctx = (name, source, width, r)
            assert r["overlap"] == 0, ctx
            assert r["outside"] == 0, ctx
            assert r["badEnds"] == 0 and r["paths"] == len(PAYLOADS[name]["links"]) - (2 if name == "cyclic_partial" else 0), ctx
            assert r["cw"] == width and r["csw"] <= width, ctx           # the container is not widened
            assert r["dsw"] <= r["iw"], ctx                              # nor the page
            assert r["cardw"] <= width + 0.5, ctx
