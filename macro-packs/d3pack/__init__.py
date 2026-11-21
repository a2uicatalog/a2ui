"""d3pack (shared-helper subset). The public repository carries only common.py and rich.py from the D3 macro pack, because the
archpack macro imports them (`from d3pack import common`, `from d3pack.rich import verify_rich`). The full D3 pack is not published here.
This stub deliberately does not import the pack's macros."""
from . import common   # noqa: F401
