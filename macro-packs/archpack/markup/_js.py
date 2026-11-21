"""Small helpers that make Python behave like the JavaScript the mermaid_arch compiler was written in.

Only what the port needs: UTF-16 string lengths, JS rounding, JS whitespace, toFixed, a JS-style string
conversion for messages, and a regex translator (\\s and $ mean what they mean in JS).
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal


class _Undef:
    """The JavaScript `undefined` (a key that is not there), as opposed to None (`null`)."""
    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst

    def __repr__(self):
        return 'UNDEF'

    def __bool__(self):
        return False


UNDEF = _Undef()


def jsget(d, k):
    if isinstance(d, dict) and k in d:
        return d[k]
    return UNDEF


# ---------------------------------------------------------------- strings
_WS_IN = '\\t\\n\\x0b\\x0c\\r \\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000\\ufeff'
JS_WS = '\t\n\x0b\x0c\r \xa0                　﻿'


def trim(s: str) -> str:
    return s.strip(JS_WS)


def trim_end(s: str) -> str:
    return s.rstrip(JS_WS)


def trim_start(s: str) -> str:
    return s.lstrip(JS_WS)


def ulen(s: str) -> int:
    """JS String.length: UTF-16 code units."""
    if s.isascii():
        return len(s)
    return len(s.encode('utf-16-le', 'surrogatepass')) // 2


def uslice(s: str, a: int, b: int | None = None) -> str:
    """JS s.slice(a, b) for non-negative a, b (UTF-16 units)."""
    if s.isascii():
        return s[a:b]
    u = s.encode('utf-16-le', 'surrogatepass')
    return u[2 * a: None if b is None else 2 * b].decode('utf-16-le', 'surrogatepass')


def squash(s) -> str:
    return re.sub('[' + _WS_IN + ']+', ' ', str(s)).strip(JS_WS)


def js_round(x: float) -> int:
    """Math.round: ties go towards +infinity."""
    f = math.floor(x)
    return f + 1 if x - f >= 0.5 else f


def to_fixed(x: float, d: int) -> str:
    q = Decimal(x).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    s = format(q, 'f')
    if s.startswith('-') and float(q) == 0:
        s = s[1:]
    return s


def num_str(x) -> str:
    if isinstance(x, bool):
        return 'true' if x else 'false'
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        if math.isnan(x):
            return 'NaN'
        if math.isinf(x):
            return 'Infinity' if x > 0 else '-Infinity'
        if x == int(x) and abs(x) < 1e21:
            return str(int(x))
        r = repr(x)
        return r
    return str(x)


def js_str(x) -> str:
    """String(x) / template-literal conversion."""
    if x is UNDEF:
        return 'undefined'
    if x is None:
        return 'null'
    if isinstance(x, str):
        return x
    if isinstance(x, (bool, int, float)):
        return num_str(x)
    if isinstance(x, list):
        return ','.join('' if (v is None or v is UNDEF) else js_str(v) for v in x)
    return '[object Object]'


def _jsonable(x):
    if isinstance(x, float) and x == int(x) and abs(x) < 1e21:
        return int(x)
    return x


def js_json(x) -> str:
    return json.dumps(_jsonable(x), separators=(',', ':'), ensure_ascii=False)


def is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def is_finite_number(x) -> bool:
    return is_number(x) and math.isfinite(x)


# ---------------------------------------------------------------- regex
def _translate(p: str) -> str:
    out = []
    i = 0
    incls = False
    n = len(p)
    while i < n:
        c = p[i]
        if c == '\\' and i + 1 < n:
            d = p[i + 1]
            if d == 's':
                out.append(_WS_IN if incls else '[' + _WS_IN + ']')
            elif d == 'S':
                if incls:
                    raise ValueError('\\S inside a class is not supported')
                out.append('[^' + _WS_IN + ']')
            else:
                out.append(c + d)
            i += 2
            continue
        if c == '[' and not incls:
            incls = True
            out.append(c)
            i += 1
            if i < n and p[i] == '^':
                out.append('^')
                i += 1
            continue
        if c == ']' and incls:
            incls = False
        elif c == '$' and not incls:
            out.append('\\Z')
            i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def rx(pattern: str, flags: int = 0):
    return re.compile(_translate(pattern), flags | re.ASCII)


# ---------------------------------------------------------------- unicode classes
def is_letter_mark_number(ch: str) -> bool:
    """/^[\\p{L}\\p{M}\\p{N}_]$/u"""
    return ch == '_' or unicodedata.category(ch)[0] in 'LMN'


def strip_marks(s: str) -> str:
    return ''.join(c for c in s if not unicodedata.category(c).startswith('M'))
