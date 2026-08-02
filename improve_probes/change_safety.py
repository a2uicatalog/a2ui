import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from _lib import PRIVATE
ops = PRIVATE/"ops"
targets = {
 "MCP Apps bundle (ui:// template)": (ops/"check_ui_view_version.py").exists(),
 "Worker renderer module":           (ops/"check_worker_renderer.py").exists(),
 "GAS public deployment":            False,
 "GAS API deployment":               False,
 "Cloud Run renderer":               False,
}
ungated = [k for k,v in targets.items() if not v]
print(f"ungated deploy targets: {ungated}")
print(sum(1 for v in targets.values() if v)/len(targets))
