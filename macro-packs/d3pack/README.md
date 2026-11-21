# d3pack (shared helpers only)

This folder holds two files from the D3 macro pack, `common.py` and `rich.py`, plus a small `__init__.py` written for this repository.
They are here because [`archpack`](../archpack/) imports them (`from d3pack import common`, `from d3pack.rich import verify_rich`).

- `common.py`: the shared base of the D3 macro pack. It holds the helpers that return a macro's output as SVG plus a text alternative, a data table
  and notes. Standard library only, no model, no browser.
- `rich.py`: `verify_rich`, the opt-in policy that checks an SVG before it is returned. It admits finite SMIL animation that ends within 5 seconds,
  at most 20 animated elements, and refuses keyframes, scripts and the other constructs its docstring lists. It fails closed and sanitises nothing.
- `__init__.py`: imports `common` only. The full pack's `__init__.py` imports its macros, which are not published here.

The rest of the D3 pack is not part of this repository.
