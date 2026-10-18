"""Write a high-level design (artifact.html) and its evidence report (report.html) for each source document.
  python3 hld.py                          # the sample documents -> out/hld/<topic>/
  python3 hld.py source.html -o out/hld   # your own"""
import argparse
import os
import re

import _paths
from reading import hld

SOURCES = {'web_dns': 'the Wikipedia "Domain Name System" extract (CC BY-SA)'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sources', nargs='*')
    ap.add_argument('-o', '--out', default=os.path.join(_paths.OUT, 'hld'))
    a = ap.parse_args()
    paths = a.sources or [os.path.join(_paths.FIXTURES, f + '.html') for f in ('web_dns', 'remote_access', 'mail_chain', 'names_only')]
    for p in paths:
        topic = os.path.splitext(os.path.basename(p))[0]
        h = hld.build(open(p, encoding='utf-8').read(), SOURCES.get(topic, f'the {topic.replace("_", " ")} document'))
        d = os.path.join(a.out, topic); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'artifact.html'), 'w', encoding='utf-8').write(hld.artifact_page(h))
        open(os.path.join(d, 'report.html'), 'w', encoding='utf-8').write(hld.report_page(h))
        print(f"{topic:<14} gate {h['status']:<9} components {len(h['names']):>2}  interactions {len(h['edges']):>2}  "
              f"open questions {len(h['r']['questions'])}  provenance {'ok' if not h['provenance'] else h['provenance']}")


if __name__ == '__main__':
    main()
