#!/usr/bin/env python3
"""atom_convert (20 Nov 2026): the deterministic motion-atom to macro conversion, first slice motion_shatter.
Run: /tmp/claude-1000/pubvenv/bin/python tests/test_atom_convert.py"""
import base64, pathlib, sys
sys.dont_write_bytecode = True; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from d3pack import gauge_modern as GM, atom_convert as AC, motion as MO, rich as RI
fails = []; n = 0
def ok(name, cond):
    global n; n += 1
    if not cond: fails.append(name); print("FAIL", name)
import re
still = re.sub(r'<animate(?:Transform)?\b[^>]*/>', '', GM.gauge_modern(value=62, max_value=100, threshold=80, unit='%', title='Free capacity', motion=True)['gauge']['svg'])
url = 'data:image/svg+xml;base64,' + base64.b64encode(still.encode()).decode()
atom = {'type': 'motion_shatter', 'shards': 8, 'origin': {'x': 22, 'y': 62}, 'cracks': True, 'fall': 'down', 'spin': 40, 'seed': 7, 'blocks': [{'type': 'motion_image', 'url': url}]}
r = AC.convert(atom)
ok("converts a motion_shatter that wraps an inline-svg motion_image", r['applied'] and r['svg'].count('<animateTransform') == 8)
def passes(fn, svg):
    try: fn(svg); return True
    except Exception as e: print("   policy said:", e); return False
ok("output passes the motion policy", passes(MO.verify_motion, r['svg']))
ok("output passes the rich policy", passes(RI.verify_rich, r['svg']))
ok("the checker really refuses: an extra animation breaks the policy", not passes(MO.verify_motion, r['svg'].replace('</svg>', '<animate attributeName="opacity" from="0" to="1" dur="1s"/></svg>')))
ok("deterministic: same atom, same bytes", AC.convert(atom)['svg'] == r['svg'])
ok("a different seed gives a different break", AC.convert(dict(atom, seed=8))['svg'] != r['svg'])
ok("the mapping table states each field", [m for m in r['mapping'] if m.startswith('shards')] and any(m.startswith('origin') for m in r['mapping']) and any(m.startswith('spin 40 -> max_angle 20') for m in r['mapping']))
ok("the exit-versus-entrance gap is reported, never hidden", any('exit semantics' in g for g in r['gaps']) and any("fall 'down'" in g for g in r['gaps']))
r12 = AC.convert(dict(atom, shards=12)); ok("12 shards is capped to 8 and says so", r12['params']['n'] == 8 and any('shards 12 became 8' in g for g in r12['gaps']))
rc = AC.convert(dict(atom, shards=99, spin=999, seed=99999)); ok("out-of-range fields are clamped and each clamp is reported", sum('clamped' in g for g in rc['gaps']) == 3)
vbw, vbh = [float(x) for x in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', still).groups()]
ok("named origins map to the edges and the middle", AC.convert(dict(atom, origin='left'))['params']['impact'] == (0.0, round(vbh / 2, 2)) and AC.convert(dict(atom, origin='center'))['params']['impact'] == (round(vbw / 2, 2), round(vbh / 2, 2)))
ok("cracks false removes the seams", AC.convert(dict(atom, cracks=False))['params']['seam_opacity'] == 0.0)
ok("child svg can be handed in directly", AC.convert({'type': 'motion_shatter', 'seed': 7}, child_svg=still)['applied'])
for name, bad in (("a non-shatter atom", {'type': 'motion_flash'}), ("no child", {'type': 'motion_shatter'}), ("a non-svg url", {'type': 'motion_shatter', 'blocks': [{'type': 'motion_image', 'url': 'https://x.test/a.png'}]}),
                  ("two children", {'type': 'motion_shatter', 'blocks': [{'type': 'motion_image', 'url': url}] * 2}), ("a text child", {'type': 'motion_shatter', 'blocks': [{'type': 'motion_text', 'text': 'x'}]})):
    rb = AC.convert(bad); ok(f"refuses {name} with a reason", (not rb['applied']) and len(rb['gaps']) >= 1)
ok("refuses a drawing with no viewBox", not AC.convert({'type': 'motion_shatter'}, child_svg='<svg xmlns="http://www.w3.org/2000/svg"></svg>')['applied'])
ok("the converter supplies a dark backing and says so in the mapping", '#7b8798' in r['svg'] and any('backing' in m for m in r['mapping']))
# the broader converters (20 Nov 2026): shake, group, assemble
for typ, extra in (("motion_shake", {}), ("motion_group", {"effect": "rise"}), ("motion_group", {"effect": "fade"}), ("motion_group", {"effect": "slide-left"}), ("motion_assemble", {})):
    a = dict({"type": typ}, **extra); rr = AC.convert(a, child_svg=still)
    ok(f"{typ} {extra or ''} converts and passes the motion policy", rr["applied"] and passes(MO.verify_motion, rr["svg"]))
    ok(f"{typ} {extra or ''} is deterministic", AC.convert(a, child_svg=still)["svg"] == rr["svg"])
    ok(f"{typ} {extra or ''} keeps the drawing's text whole inside the moving group", rr["svg"].count("<text") == still.count("<text"))
rs = AC.convert({"type": "motion_shake", "amount": 80, "frequency": 40, "tilt": 9}, child_svg=still)
ok("shake: amount 80 becomes the policy travel of 60 and frequency 40 becomes 7 jolts, both reported", rs["params"]["amp"] == 60 and rs["params"]["jolts"] == 7 and sum("became" in g for g in rs["gaps"]) == 2)
ok("shake: tilt 0 draws no rotation", "type=\"rotate\"" not in AC.convert({"type": "motion_shake", "tilt": 0}, child_svg=still)["svg"])
rg = AC.convert({"type": "motion_group", "effect": "pop", "duration": 3000, "delay": 2000}, child_svg=still)
ok("group: an effect the policy cannot draw (pop) is replaced by rise and says so; a long duration and delay are clamped and say so", rg["applied"] and rg["params"]["effect"] == "rise" and rg["params"]["dur"] <= 1.5 and rg["params"]["delay"] + rg["params"]["dur"] <= 1.5 and sum(("cannot be drawn" in g) or ("became" in g) for g in rg["gaps"]) >= 3)
ra = AC.convert({"type": "motion_assemble", "columns": 3, "gap": 14}, child_svg=still)
ok("assemble: one picture has no layout, the gap says so, and the fly-in is within the 60 px limit", ra["applied"] and any("no layout" in g for g in ra["gaps"]) and all(abs(v) <= 60 for v in ra["params"]["offset"]))
for typ in ("motion_flash", "motion_text", "motion_timeline", "motion_nonsense"):
    rr = AC.convert({"type": typ}, child_svg=still); ok(f"{typ} is refused, never silently passed through", (not rr["applied"]) and len(rr["gaps"]) == 1)
# the generative converters (20 Nov 2026): atoms that draw their own content
OWN = {"motion_shape": {"shape": "ring", "fill": "#dc2626", "fill2": "#f59e0b"}, "motion_mark": {}, "motion_rays": {}, "motion_cells": {"numbers": True}, "motion_scatter": {"items": ["a", "b", "c"]}, "motion_particles": {"shape": "star"}, "motion_lit": {},
       "motion_arcs": {}, "motion_dialog": {"title": "Delete?", "body": "This cannot be undone.", "actions": [{"label": "Cancel"}, {"label": "Delete", "primary": True}]}, "motion_discs": {}, "motion_dotgrid": {}}
for typ, extra in OWN.items():
    a = dict({"type": typ}, **extra); rr = AC.convert(a, child_svg=still)
    ok(f"{typ} draws a picture that passes the motion policy and the rich policy", rr["applied"] and passes(MO.verify_motion, rr["svg"]) and passes(RI.verify_rich, rr["svg"]))
    ok(f"{typ} is deterministic", AC.convert(a, child_svg=still)["svg"] == rr["svg"])
    ok(f"{typ} states its mapping and reports at least one gap", len(rr["mapping"]) >= 1 and len(rr["gaps"]) >= 1)
    ok(f"{typ} fits the rich budget (60 KB, 400 elements) and has an accessible name", rr["bytes"] <= 60000 and rr["elements"] <= 400 and 'aria-label="' in rr["svg"] and "<title>" in rr["svg"])
ok("shape: a bad colour falls back to the default and says so; a ring is an annulus path, not a stroke", any("not a #rrggbb" in g for g in AC.convert({"type": "motion_shape", "fill": "red;x"})["gaps"]) and "A " in AC.convert({"type": "motion_shape", "shape": "ring"})["svg"])
ok("shape: blur is dropped and reported (no filter on an animated picture)", any("blur" in g for g in AC.convert({"type": "motion_shape", "blur": 30})["gaps"]) and "filter" not in AC.convert({"type": "motion_shape", "blur": 30})["svg"])
ok("mark: three ellipse paths, a nucleus and an electron", AC.convert({"type": "motion_mark"})["svg"].count("<path") == 3 and AC.convert({"type": "motion_mark"})["svg"].count("<circle") == 2)
ok("rays: a spin above 90 degrees is clamped to 90 and reported", any("spin 360 became 90" in g for g in AC.convert({"type": "motion_rays", "spin": 360})["gaps"]))
ok("cells: the doubling numbers are drawn in the first 13 cells", "4096" in AC.convert({"type": "motion_cells", "numbers": True, "columns": 5, "rows": 3})["svg"] and "8192" not in AC.convert({"type": "motion_cells", "numbers": True, "columns": 5, "rows": 3})["svg"])
rsc = AC.convert({"type": "motion_scatter", "items": [str(i) for i in range(12)]}); ok("scatter: 12 cards become 8 and say why", rsc["params"]["cards"] == 8 and any("only the first 8" in g for g in rsc["gaps"]))
ok("particles: text is refused with the reason (the dot font is not built), a shape converts", not AC.convert({"type": "motion_particles", "text": "HELLO"})["applied"] and AC.convert({"type": "motion_particles", "shape": "heart"})["applied"])
ok("particles: the dots move in at most 8 groups", AC.convert({"type": "motion_particles"})["svg"].count("<animateTransform") <= 8)
ok("lit: several cards are refused with the reason, one card converts", not AC.convert({"type": "motion_lit", "blocks": [{"type": "motion_text"}, {"type": "motion_text"}]})["applied"])
ok("arcs: a spin of 400 is clamped to 90 and reported; more than 4 arcs keep the first 4", any("became 90" in g for g in AC.convert({"type": "motion_arcs", "arcs": [{"spin": 400}]})["gaps"]) and AC.convert({"type": "motion_arcs", "arcs": [{}] * 6})["params"]["arcs"] == 4)
ok("dialog: no title is refused; the title becomes the accessible name; the body is real text", not AC.convert({"type": "motion_dialog"})["applied"] and 'aria-label="Dialog: Delete?"' in AC.convert({"type": "motion_dialog", "title": "Delete?"})["svg"] and "This cannot be undone." in AC.convert(dict({"type": "motion_dialog"}, **OWN["motion_dialog"]))["svg"])
ok("dialog: markup in the title is escaped, never passed through", "<b>" not in AC.convert({"type": "motion_dialog", "title": "<b>x</b>"})["svg"])
ok("discs: one disc is refused; four are drawn", not AC.convert({"type": "motion_discs", "discs": [{"color": "#112233", "r": 20}]})["applied"] and AC.convert({"type": "motion_discs", "discs": [{}, {}, {}, {}]})["svg"].count("<circle") == 4)
ok("dotgrid: bad hops fall back to the seeded path and say so; the same seed gives the same path", any("hops is not" in g for g in AC.convert({"type": "motion_dotgrid", "hops": [[1]]})["gaps"]) and AC.convert({"type": "motion_dotgrid", "seed": 9})["svg"] == AC.convert({"type": "motion_dotgrid", "seed": 9})["svg"])
# long motion (20 Nov 2026): an explicit opt-in, up to 15 s; the defaults are unchanged
def last_end(svg):
    e = 0.0
    for x in re.findall(r'<animate(?:Transform)?\b[^>]*>', svg):
        b = re.search(r'begin="([0-9.]+)s"', x); d = re.search(r'dur="([0-9.]+)s"', x); e = max(e, (float(b.group(1)) if b else 0.0) + float(d.group(1)))
    return e
for typ in ("motion_shatter", "motion_shake", "motion_group", "motion_assemble", "motion_mark", "motion_discs", "motion_cells", "motion_dialog"):
    a = {"type": typ, "title": "Hi"} if typ == "motion_dialog" else {"type": typ}
    rl = AC.convert(a, child_svg=still, duration=15)
    ok(f"{typ}: 15 s long motion converts, ends at exactly 15 s, and passes the policy only with the long opt-in", rl["applied"] and abs(last_end(rl["svg"]) - 15.0) < 1e-6 and passes(lambda s: MO.verify_motion(s, max_seconds=15), rl["svg"]) and not passes(MO.verify_motion, rl["svg"]))
    ok(f"{typ}: the long picture keeps the same animation count and states the WCAG 2.2.2 point and the stretch factor", rl["svg"].count("<animate") == AC.convert(a, child_svg=still)["svg"].count("<animate") and any("WCAG 2.2.2" in g for g in rl["gaps"]) and any("stretched from" in m for m in rl["mapping"]))
ok("long motion: more than 15 s, below 0.2 s, a string and a bool are refused", all(not AC.convert({"type": "motion_group"}, child_svg=still, duration=d)["applied"] for d in (15.01, 40, 0.1, "15", True)))
ok("long motion is deterministic and 15 s of one animation keeps its order (begin times scale together)", AC.convert({"type": "motion_cells"}, child_svg=still, duration=15)["svg"] == AC.convert({"type": "motion_cells"}, child_svg=still, duration=15)["svg"])
ok("verify_motion: the ceiling is 15 s even as an opt-in, and max_seconds must be positive", not passes(lambda s: MO.verify_motion(s, max_seconds=16), AC.convert({"type": "motion_group"}, child_svg=still)["svg"]) and not passes(lambda s: MO.verify_motion(s, max_seconds=0), AC.convert({"type": "motion_group"}, child_svg=still)["svg"]))
ok("verify_motion default is unchanged: 1.6 s is still refused without the opt-in", (lambda r16: r16["applied"] and not passes(MO.verify_motion, r16["svg"]) and passes(lambda s: MO.verify_motion(s, max_seconds=1.6), r16["svg"]))(AC.convert({"type": "motion_group"}, child_svg=still, duration=1.6)))
# loop (20 Nov 2026): the normal-speed motion repeated for up to 15 s, by a list of begin times
def begins(svg): return [[float(x.rstrip("s")) for x in m.split(";")] for m in re.findall(r'begin="([^"]+)"', svg)]
for typ in ("motion_shatter", "motion_shake", "motion_group", "motion_assemble", "motion_mark", "motion_discs", "motion_cells", "motion_particles", "motion_dotgrid"):
    base = AC.convert({"type": typ}, child_svg=still); lp = AC.convert({"type": typ}, child_svg=still, loop=15)
    ok(f"{typ}: loop 15 converts, keeps the animation count and every speed (dur) of the single run", lp["applied"] and lp["svg"].count("<animate") == base["svg"].count("<animate") and re.findall(r'dur="[^"]+"', lp["svg"]) == re.findall(r'dur="[^"]+"', base["svg"]))
    bl = begins(lp["svg"]); ok(f"{typ}: every animation restarts several times, in order, after the previous run has finished, and the last run ends within 15 s", all(len(b) >= 2 for b in bl) and all(y > x for b in bl for x, y in zip(b, b[1:])) and max(b[-1] for b in bl) + max(float(d.rstrip("s")) for d in re.findall(r'dur="([^"]+)"', lp["svg"])) <= 15.0 + 1e-6)
    ok(f"{typ}: the looped picture passes the policy only with the long opt-in", passes(lambda s: MO.verify_motion(s, max_seconds=15), lp["svg"]) and not passes(MO.verify_motion, lp["svg"]) and not passes(RI.verify_rich, lp["svg"]))
    ok(f"{typ}: the loop is deterministic and states the run count, the rest and the WCAG 2.2.2 point", AC.convert({"type": typ}, child_svg=still, loop=15)["svg"] == lp["svg"] and any("runs" in m and "rest between runs" in m for m in lp["mapping"]) and any("WCAG 2.2.2" in g for g in lp["gaps"]))
ok("loop: duration and loop together are refused; a loop shorter than one run is refused; bad values are refused", not AC.convert({"type": "motion_group"}, child_svg=still, loop=15, duration=15)["applied"] and not AC.convert({"type": "motion_shake"}, child_svg=still, loop=0.5)["applied"] and all(not AC.convert({"type": "motion_group"}, child_svg=still, loop=v)["applied"] for v in (16, 0.1, "15", True)))
_mk = lambda b: '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10"><g><rect width="5" height="5" fill="#000000"/><animate attributeName="opacity" from="0" to="1" dur="1s" begin="' + b + '" repeatCount="1" fill="freeze"/></g></svg>'
ok("rich: a begin list is refused without the opt-in; overlapping restarts are refused even with it; a clean list is admitted", not passes(RI.verify_rich, _mk("0s;2s")) and not passes(lambda s: RI.verify_rich(s, max_seconds=15), _mk("0s;0.5s")) and passes(lambda s: RI.verify_rich(s, max_seconds=15), _mk("0s;2s;4s")))
ok("a list of more than 40 restart times is refused", not passes(lambda s: RI.verify_rich(s, max_seconds=15), _mk(";".join(f"{k * 1.01:.2f}s" for k in range(41)))))
print(f"atom_convert: {n} checks, {len(fails)} failed"); sys.exit(1 if fails else 0)
