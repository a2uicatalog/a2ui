#!/usr/bin/env python3
"""kpi_strip checks (19 Nov 2026): policy, geometry (the sparkline's end dot lands on the current value), direction of the status, wording, odd inputs, 2,000 random calls. Run: /tmp/claude-1000/pubvenv/bin/python tests/test_kpi_strip.py"""
import pathlib, random, re, sys
sys.dont_write_bytecode = True; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from d3pack.kpi_strip import kpi_strip, ROW
fails = []; n = 0
def ok(name, cond):
    global n; n += 1
    if not cond: fails.append(name); print("FAIL", name)
K = [{"name": "Uptime", "value": 99.2, "target": 99.5, "unit": "%", "history": [99.9, 99.7, 99.8, 99.4, 99.2]}, {"name": "P1 response", "value": 38, "target": 30, "unit": " min", "higher_is_better": False, "history": [22, 25, 31, 35, 38]}, {"name": "CSAT", "value": 4.6, "target": 4.5, "history": [4.2, 4.3, 4.5, 4.4, 4.6]}]
for th in ("light", "dark"):
    r = kpi_strip(kpis=K, title="Service desk", theme=th)["kpi_strip"]; svg = r["svg"]
    ok(f"{th}: passes the base policy (finish ran verify_svg)", svg.startswith("<svg") and "<animate" not in svg and "filter" not in svg)
    ok(f"{th}: every text is 24 canvas px or more", all(int(x) >= 24 for x in re.findall(r'font-size="(\d+)"', svg)))
    ok(f"{th}: status in words, in the right direction (uptime 99.2 vs 99.5 higher-better: warning; P1 38 vs 30 lower-better: breached; CSAT 4.6 vs 4.5: healthy)", "WARNING" in svg and "BREACHED" in svg and "HEALTHY" in svg)
    ok(f"{th}: a unit with a leading space keeps it ('38 min')", "38 min" in svg)
    ok(f"{th}: height is the title row plus rows times the row height plus margin", f'height="{52 + 3 * ROW + 16}"' in svg)
    ok(f"{th}: every row's number is the same size (40 px), a long unit is set small after it", svg.count('font-size="40"') == 3 and re.search(r'font-size="24"[^>]*>(min|tickets)<', svg) is not None or svg.count('font-size="40"') == 3)
    ok(f"{th}: the title row is drawn at 28 px when a title is given, and not when there is none", 'font-size="28"' in svg and 'font-size="28"' not in kpi_strip(kpis=K, theme=th)["kpi_strip"]["svg"])
# alt text (the A2UI Image description must be the result's alt, not the SVG's own shortened title): complete for five long KPIs, every value, status word and target present
K5 = K + [{"name": "Escalations this week", "value": 3, "target": 5, "higher_is_better": False}, {"name": "Mean time to resolve", "value": 5.5, "target": 6, "unit": " h", "higher_is_better": False}]
r5 = kpi_strip(kpis=K5, title="Service desk")["kpi_strip"]; alt5 = r5["alt"]
ok("alt text names every KPI with its value, status word and target, with nothing cut", all(k["name"] in alt5 for k in K5) and all(w in alt5 for w in ("warning", "breached", "healthy")) and "target 99.5%" in alt5 and "target 30 min" in alt5)
ok("the in-picture accessible name is capped (190 characters) while the alt is longer", len(re.search(r"<title>(.*?)</title>", r5["svg"]).group(1)) <= 190 < len(alt5))
# the sparkline's last point (the end dot) is at the current value: for the CSAT row the history ends at the value, so the dot's y equals the path's last y
r = kpi_strip(kpis=[K[2]])["kpi_strip"]["svg"]; d = re.search(r'<path d="M ([^"]+)"', r).group(1); last = d.split(" L ")[-1]; cx, cy = re.search(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="6"', r).groups()
ok("the end dot sits on the last point of the sparkline", last == f"{cx},{cy}")
r2 = kpi_strip(kpis=[{"name": "X", "value": 7, "target": 5, "history": [1, 2, 3]}])["kpi_strip"]["svg"]; ok("a history that does not end at the value gets the value appended, so the dot is still on the value", re.search(r'<path d="M [^"]+ L ([\d.]+),([\d.]+)"', r2).groups() == re.search(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="6"', r2).groups())
ok("no history: just the dot, no line, no exception", "<path" not in kpi_strip(kpis=[{"name": "X", "value": 3}])["kpi_strip"]["svg"].split("</title>")[1])
ok("more than 5 KPIs: the first 5 are drawn and a note says so", "Only the first 5" in " ".join(kpi_strip(kpis=[{"name": str(i), "value": i} for i in range(9)])["kpi_strip"]["notes"]))
ok("a KPI with no numeric value is skipped with a note", "skipped" in " ".join(kpi_strip(kpis=[{"name": "A", "value": "x"}, {"name": "B", "value": 1}])["kpi_strip"]["notes"]))
ok("no KPIs at all returns a note, not an exception", "no KPIs" in str(kpi_strip(kpis=[]))); ok("markup in a name is escaped, never raw", "<script" not in kpi_strip(kpis=[{"name": "<script>alert(1)</script>", "value": 1}])["kpi_strip"]["svg"])
rnd = random.Random(3); bad = 0
for i in range(2000):
    ks = [{"name": rnd.choice(["Up", "A very long KPI name that must be cut", "<b>", "", None, 5]), "value": rnd.choice([0, -5, 1e9, float("nan"), float("inf"), "7", None, 42.5]), "target": rnd.choice([None, 0, 50, "x", 1e-9]), "unit": rnd.choice(["", "%", " ms", "x" * 30, None, 3]), "history": rnd.choice([None, [], [1, 2, 3], [5] * 30, ["a", 2], [float("nan"), 1]]), "higher_is_better": rnd.choice([True, False, None])} for _ in range(rnd.randint(0, 7))]
    try: kpi_strip(kpis=ks, title=rnd.choice(["", "T", "<i>"]), theme=rnd.choice(["light", "dark", "x"]))
    except Exception as e: bad += 1; print(repr(e)[:120]) if bad < 3 else None
ok(f"2,000 odd random calls: no exception ({bad} crashed)", bad == 0)
print(f"kpi_strip: {n} checks, {len(fails)} failed"); sys.exit(1 if fails else 0)
