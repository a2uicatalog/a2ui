#!/usr/bin/env python3
"""compose.py — two-field compose: 2 files in, 2 files out.

Many ITSM knowledge bases store an article in TWO fields (e.g. Case
Description and Resolution), so the pipeline speaks files-in-pairs:

  # one whole-article YAML → split into the two payload files
  python3 compose.py runs/utd412.lift.yaml -o runs/out/utd412

  # OR two partial YAMLs (already field-separated at the lift) → one file each
  python3 compose.py desc.yaml res.yaml -o runs/out/utd412

Either way, OUT is always exactly two self-contained HTML files:
  <out>-description.html   (scope hero · issue · environment · cause · cause_test)
  <out>-resolution.html    (resolution · action buttons — no hero)
"""
import sys, yaml
from render_kb import render

def main(argv):
    args = list(argv)
    out = "composed"
    if "-o" in args:
        i = args.index("-o"); out = args[i+1]; del args[i:i+2]
    files = args
    if len(files) not in (1, 2):
        sys.exit("usage: compose.py <article.yaml> [resolution.yaml] -o <outprefix>")

    if len(files) == 1:                    # whole article → split
        a = yaml.safe_load(open(files[0]))["article"]
        pairs = [("description", a), ("resolution", a)]
    else:                                  # already two payloads → render each as its section
        d = yaml.safe_load(open(files[0]))["article"]
        r = yaml.safe_load(open(files[1]))["article"]
        pairs = [("description", d), ("resolution", r)]

    for section, article in pairs:
        path = f"{out}-{section}.html"
        with open(path, "w") as f:
            f.write(render(article, section))
        print(f"wrote {path}")

if __name__ == "__main__":
    main(sys.argv[1:])
