"""Puts this folder and the catalogue root (for renderers.web_article) on sys.path for the command-line tools."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for p in (HERE, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
FIXTURES = os.path.join(HERE, 'fixtures')
OUT = os.path.join(HERE, 'out')
