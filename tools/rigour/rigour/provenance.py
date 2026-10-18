"""No rendered element without a standing ground. Builders return, next to each block, the list of elements they
drew and the slot ids each rests on; this check refuses any element that rests on nothing, on an unknown slot,
or on a slot whose argument did not stand."""


def check(elements, slot_status):
    """elements: [{'what', 'label', 'grounds': [slot ids]}]; slot_status: {slot id: status}. Returns findings."""
    findings = []
    for el in elements:
        gs = el.get('grounds') or []
        if not gs:
            findings.append(f"{el['what']} '{el['label']}' rests on no slot")
            continue
        for g in gs:
            if g not in slot_status:
                findings.append(f"{el['what']} '{el['label']}' rests on unknown slot {g}")
            elif slot_status[g] != 'STANDS':
                findings.append(f"{el['what']} '{el['label']}' rests on slot {g}, which is {slot_status[g]}")
    return findings
