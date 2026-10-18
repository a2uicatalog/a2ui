# rigour

Builds an artifact only from what a source document states, and keeps the argument for each element.

Every element is a Toulmin record (`toulmin_argument`): a claim, the verbatim sentences it rests on, the
warrant that licenses it, and the rebuttals that were checked. A record stands only when its grounds are
found word for word in the source and no rebuttal applies. What the source does not state becomes an open
question, never a drawn guess.

What an artifact needs is declared in `boms/<artifact>.yaml`: its slots, the clarity rules checked against
the built result, and what to fall back to when a rule fires.

| Template | Builds | From |
| --- | --- | --- |
| `hld.py` | a high-level design: components, numbered flows, boundaries (`motion_arch`) | a document describing a system |
| `film.py` | a timed scene sequence: problem, then each step or case (`motion_timeline`) | a problem/fix document |
| `decision.py` | a CSS-only choice block, as a page or an iframe snippet | a document stating alternatives |

Each writes the artifact and a separate evidence report (`out/<template>/<topic>/`).

    python3 tools/rigour/hld.py
    python3 tools/rigour/film.py [doc.html] [--theme theme.json] [--captions proposed.json]
    python3 tools/rigour/decision.py [doc.html]

Captions supplied from elsewhere (`--captions`) are used only where every content word is in the sentence
they replace. Domain rules (relations, sections, cut points, icon words) live in `reading/*.yaml`.

Tests: `tests/test_rigour_templates.py`. `fixtures/web_dns.html` is an extract from Wikipedia
("Domain Name System"), CC BY-SA 4.0; the other fixtures were written for the tests.
