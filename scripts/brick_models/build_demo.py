#!/usr/bin/env python3
"""Build public/bricksdemo/index.html — the brick_build_3d gallery (a2uicatalog.ai/bricksdemo).

Runs the model generators (Harry Potter, Hogwarts tower, Sorting Hat, Golden Snitch, Microduck), packs them as compact
palette-indexed models, renders the atom through the web renderer's Python twin and wraps it in a self-contained page.
Deterministic: same generators in, same page out, so the committed page can be reviewed and regenerated.

  python3 scripts/brick_models/build_demo.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from renderers import web_article as w  # noqa: E402

OUT = ROOT / "public" / "bricksdemo" / "index.html"
MODELS = [("Harry Potter", "harry_potter"), ("Hogwarts Tower", "tower"), ("Sorting Hat", "sorting_hat"),
          ("Golden Snitch", "snitch"), ("Microduck", "microduck")]

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<title>Brick Build 3D</title>
<meta name="description" content="Self-assembling LEGO-style 3D models, each checked for collisions, anchoring and balance, with build steps and a parts list. Rendered by the A2UI brick_build_3d atom.">
<meta name="robots" content="noindex, nofollow">
<style>
:root{--bg:#f3f5f7;--fg:#0f1c28;--mute:#55636f;--rule:#d5dce3;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#10171e;--fg:#e6ecf1;--mute:#93a1ad;--rule:#26323d;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#10171e;--fg:#e6ecf1;--mute:#93a1ad;--rule:#26323d;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);padding-inline:16px;padding-block:24px;font:14px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:880px;margin:0 auto;display:flex;flex-direction:column;gap:16px}
h1{font-size:20px;margin:0;text-wrap:balance}
p{margin:0;color:var(--mute);font-size:13px;max-width:70ch}
footer{border-top:1px solid var(--rule);padding-top:12px}
footer p{font-size:12px}
a{color:inherit}
</style>
</head>
<body>
<main>
<div>
<h1>Brick Build 3D</h1>
<p>Pick a model from the dropdown, drag to orbit, or switch to Instructions and use the slider to step through the build. Each model is checked live: no collisions, every brick reaches the baseplate, and the balance point sits inside the footprint. The models are generated from equations and layered voxel rules, then tiled into bricks with a running bond so the layers lock together.</p>
</div>
{atom}
<footer>
<p>Rendered by the brick_build_3d atom in the <a href="/">A2UI Atomic Catalog</a>. Part prices are an indicative formula, not BrickLink data. These are fan-made models and are not affiliated with or endorsed by the LEGO Group or Warner Bros. Entertainment. LEGO and Harry Potter are trademarks of their respective owners.</p>
</footer>
</main>
</body>
</html>
"""


def compact(name, bricks):
    pal = []
    for r in bricks:
        if r["c"] not in pal:
            pal.append(r["c"])
    return {"name": name, "palette": pal,
            "bricks": [[r["x"], r["y"], r["z"], r["w"], r["d"], pal.index(r["c"])] for r in bricks]}


def build_models():
    """Run the generators and return the five models in compact, palette-indexed form."""
    with tempfile.TemporaryDirectory() as tmp:
        run = lambda *a: subprocess.run([sys.executable, *a], cwd=HERE, check=True, capture_output=True, text=True)  # noqa: E731
        run("harry_potter.py", f"{tmp}/harry_potter.json")
        run("models.py", tmp)
        return [compact(n, json.loads((Path(tmp) / f"{f}.json").read_text())) for n, f in MODELS]


def render_page(models):
    atom = w._RENDERERS["brick_build_3d"]({"models": models, "model": "Harry Potter", "height": 560, "parts": True})
    return PAGE.replace("{atom}", atom)


def main(out=OUT):
    models = build_models()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_page(models), encoding="utf-8")
    print(f"wrote {out} — {sum(len(m['bricks']) for m in models)} bricks in {len(models)} models, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
