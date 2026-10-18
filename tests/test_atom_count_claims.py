"""The published-atom count is quoted by hand in a few public files (the MCP server card, the listing text, SKILL.md, the MCP README).
It went stale once (474 while 548 were published), and registries such as Smithery and MCP Market copy those files. Keep them tied to the real count."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = [
    ('public/.well-known/mcp/server-card.json', r'(\d+) typed UI atoms'),
    ('SKILL.md', r'(\d+) typed UI atoms'),
    ('SKILL.md', r'whole (\d+)-atom vocabulary'),
    ('mcp/LISTING.md', r'vocabulary of (\d+) typed atoms'),
    ('mcp/README.md', r'`a2ui-atoms-v1` \((\d+) atoms\)'),
]


def published_count():
    return len(json.loads((ROOT / 'public/catalogue/a2ui-atoms-v1.json').read_text())['components'])


def test_quoted_atom_counts_match_the_published_catalogue():
    n = published_count()
    stale = []
    for path, pattern in CLAIMS:
        found = re.findall(pattern, (ROOT / path).read_text())
        assert found, f'{path}: no claim matching {pattern!r}; update the CLAIMS list if the wording changed'
        stale += [f'{path} says {x}' for x in found if int(x) != n]
    assert not stale, f'{n} atoms are published, but: ' + '; '.join(stale)
