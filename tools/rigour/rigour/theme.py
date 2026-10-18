"""Colours for the built artifacts. A theme is a JSON object of #rrggbb values for any of these slots; missing
slots fall back to DEFAULT. Presentation only: a theme never changes what an artifact may show."""
import json
import re

DEFAULT = dict(accent='#6d6bff', accent2='#22d3ee', bg='#07080f', panel='#0f1320', panel2='#1a1d3a',
               ink='#f4f6ff', ink2='#cdd3e6', muted='#9aa4bd')


def load(theme=None):
    """theme: None, a dict, or a path to a JSON file."""
    t = dict(DEFAULT)
    if isinstance(theme, str):
        theme = json.load(open(theme, encoding='utf-8'))
    for k, v in (theme or {}).items():
        if k not in DEFAULT:
            raise ValueError(f'theme: unknown slot {k!r}; slots are {sorted(DEFAULT)}')
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', str(v)):
            raise ValueError(f'theme: {k}={v!r} is not a #rrggbb colour')
        t[k] = v.lower()
    return t
