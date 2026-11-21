"""archpack tests (pure Python, no browser): the architecture-animation macro. The layout collision check needs Chromium and lives in
archpack/tools/check_layout.py (run it from archpack/tools; it prints TOTAL problems). Here: guardrail, determinism, motion limits, contract."""
import os, re, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import archpack
from d3pack.rich import verify_rich
n = bad = 0
def check(ok, what):
    global n, bad
    n += 1
    if not ok: bad += 1; print('FAIL:', what)
F = archpack.PACK['arch_motion']; ARGS = F.__code__.co_varnames[:F.__code__.co_argcount]
def run(spec, motion):
    p = {k: v for k, v in spec.items() if k in ARGS}; p['motion'] = motion
    return F(**p)
for name, spec in (('trip', archpack.TRIP_PLANNER_DEMO), ('container', archpack.TRIP_CONTAINER_DEMO)):
    for motion in (True, False):
        r = run(spec, motion); r2 = run(spec, motion)
        check(set(r) == {'wide', 'narrow', '_default'}, f'{name} {motion}: result keys')
        for view in ('wide', 'narrow'):
            svg = r[view]['svg']; tag = f'{name} motion={motion} {view}'
            check(svg == r2[view]['svg'], f'{tag}: deterministic')
            try: verify_rich(svg); ok = True
            except Exception as e: ok = False; print('  ', e)
            check(ok, f'{tag}: verify_rich passes')
            check(r[view]['animated'] <= 20, f'{tag}: at most 20 animated elements ({r[view]["animated"]})')
            if not motion: check(r[view]['animated'] == 0, f'{tag}: no animation when motion is off')
            check('@keyframes' not in svg and '<script' not in svg and 'http://' not in svg.replace('http://www.w3.org/2000/svg', ''), f'{tag}: no keyframes, script or external reference')
            check(not re.search(r'font-size="(\d+(\.\d+)?)"', svg) or min(float(x) for x in re.findall(r'font-size="(\d+(?:\.\d+)?)"', svg)) >= 12, f'{tag}: font size at least 12')
            ends = [float(m) for m in re.findall(r'dur="([\d.]+)s"', svg)]
            check(all(e <= 5 for e in ends), f'{tag}: every duration within 5 s')
print(f'arch pack tests: {n} checks, {bad} failed'); sys.exit(1 if bad else 0)
