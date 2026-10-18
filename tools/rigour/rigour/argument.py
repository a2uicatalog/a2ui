"""Toulmin argument records: build them, check grounds verbatim, and compute the status exactly as the
toulmin_argument atom renders it (tests/test_rigour.py holds the two in parity)."""


def verified(quote, excerpt):
    """The atom's check: an exact substring of the source excerpt, no normalising, no fuzzy match."""
    return bool(quote) and bool(excerpt) and str(quote) in str(excerpt)


def status(rec):
    grounds = (rec.get('grounds') or [])[:8]
    rebuttals = (rec.get('rebuttals') or [])[:6]
    if any(isinstance(r, dict) and r.get('applies') for r in rebuttals):
        return 'REBUTTED'
    if not grounds:
        return 'UNGROUNDED'
    excerpt = rec.get('source_excerpt') or ''
    if sum(1 for g in grounds if isinstance(g, dict) and verified(g.get('quote'), excerpt)) < len(grounds):
        return 'UNVERIFIED GROUNDS'
    return 'STANDS'


GROUNDS_MAX, REBUTTALS_MAX = 8, 6   # what the atom reads; status() ignores the rest, so a record may never carry more


def record(title, claim, grounds, warrant, rebuttals=(), qualifier=None, backing=None, excerpt=''):
    if len(grounds) > GROUNDS_MAX or len(rebuttals) > REBUTTALS_MAX:
        raise ValueError(f'{title}: {len(grounds)} grounds / {len(rebuttals)} rebuttals; the atom reads only '
                         f'{GROUNDS_MAX} / {REBUTTALS_MAX}, so the rest would be silently ignored')
    rec = dict(type='toulmin_argument', title=title, claim=claim, source_excerpt=excerpt,
               grounds=list(grounds), warrant=warrant, rebuttals=list(rebuttals))
    if qualifier:
        rec['qualifier'] = qualifier
    if backing:
        rec['backing'] = backing
    return rec
