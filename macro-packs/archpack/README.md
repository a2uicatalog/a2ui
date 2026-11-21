# archpack: architecture animation

One macro, `arch_motion`. It takes the `motion_arch` atom's contract (nodes, edges, messages, groups, sizes, colours) and returns a wide and a
narrow SVG, `{'wide', 'narrow', '_default'}`, with finite SMIL motion: the animations end within 5 seconds, there are at most 20 animated
elements, and there are no keyframes. Every SVG is checked by `verify_rich` before it is returned, and the macro raises if the check fails.
The macro uses only the Python standard library. It makes no network calls and uses no model, so the same input gives the same bytes.

## Demo

The architecture animation in the [trip planner demo](https://a2uicatalog.ai/what-is-a2ui/basic-catalog/demos/trip-planner/) is drawn by this macro.
The four SVG files it uses (wide and narrow, animated and still) are in [`public/bc-assets/`](../../public/bc-assets/).

## Use it

```python
import sys; sys.path.insert(0, "macro-packs")           # the import root
from archpack import arch_motion
from archpack.markup import mermaid_to_arch

graph = mermaid_to_arch("flowchart LR\n  A[Agent] -->|payload| B[Renderer]\n  B -->|screen| C[User]")
out = arch_motion(**dict(graph))
open("wide.svg", "w").write(out["wide"]["svg"])
open("narrow.svg", "w").write(out["narrow"]["svg"])
```

`mermaid_to_arch`, `d2_to_arch` and `json_to_arch` (in `archpack.markup`) turn Mermaid, D2 or a JSON graph into `arch_motion` keyword arguments.
You can also call `arch_motion(nodes=..., edges=..., messages=..., groups=...)` directly. Two ready inputs are `TRIP_PLANNER_DEMO` and `TRIP_CONTAINER_DEMO`.

## Where it comes from

`archpack/markup/` is a Python port of the JavaScript compiler in [`scripts/mermaid_arch/`](../../scripts/mermaid_arch/) (documented in
[`docs/mermaid_arch.md`](../../docs/mermaid_arch.md)). The tests run the JavaScript version over the 88 files in
[`tests/mermaid_corpus/`](../../tests/mermaid_corpus/) with eight option sets and compare the Python results with it.

## Tests

From the repository root:

    python3 -B macro-packs/tests/test_arch.py                  # 56 checks, standard library only
    python3 -m pytest -q macro-packs/archpack/markup           # parity with the JavaScript compiler; needs pytest and node

On the day this was published, the first printed `56 checks, 0 failed`, and the second passed 1,939 tests and skipped 940 (cases the test file
itself marks as covered elsewhere or not rendered by the JavaScript version either).

`tools/check_layout.py` and `tools/check360.py` measure real text and path geometry in a browser. They are optional and need Playwright and Chromium.

## Dependencies on the D3 pack

`arch_motion` imports two small helpers from the D3 macro pack, `common.py` and `rich.py`. Only those two files are published here, in
[`macro-packs/d3pack/`](../d3pack/), so that archpack runs on its own. The rest of the D3 pack is not part of this repository.

## Licence

MIT, like the rest of this repository (see the root `LICENSE`).
