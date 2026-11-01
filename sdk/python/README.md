# a2uicatalog

Official Python client for the [A2UI Atomic Catalog](https://a2uicatalog.ai): typed UI atoms an agent
composes into real interfaces. No account, no API key, no dependencies (standard library only).

```python
from a2uicatalog import Client

c = Client()                                         # https://a2uicatalog.ai
blocks = [{"type": "heading", "text": "This week"},
          {"type": "stat_card", "value": "1,234", "label": "Daily users", "delta": "+12%"}]
c.validate(blocks, strict=False)                     # local check, raises ValidationError on a bad atom
html = c.render(blocks, title="Weekly numbers")      # one self-contained HTML page
open("page.html", "w").write(html)
print(c.ask("countdown timer")["results"][0]["name"])  # ranked catalogue search
```

## Methods

| Method | Endpoint |
|---|---|
| `spec()` | `GET /spec.json` (cached in memory) |
| `catalogs()` | `GET /catalogue/index.json` |
| `atom_schema(type)`, `atom_types()` | from `GET /catalogue/atoms-json-schema.json` (cached) |
| `ask(question)` | `POST /ask` |
| `compose(prompt)` | `POST /api/compose` (free tier, 20 per IP per day) |
| `render(payload, surface=None)` | `POST /api/render` (50 per IP per day) |
| `render_batch(payloads)` | `POST /api/render/batch` (1 to 25 payloads) |
| `check(payload)`, `validate(payload)` | local, against the published schema |

`payload` is `{"blocks": [...]}`, a list of blocks, or one block. A 429 is retried once if the server's
`Retry-After` is 30 s or less; a longer wait raises `RateLimitError` with `.retry_after`.

`check`/`validate` follow the published per-atom schema, which is strict (unknown fields are problems).
Pass `strict=False` to report only unknown atoms and missing required fields.

Errors derive from `A2UIError`: `HTTPError`, `RateLimitError`, `NetworkError`, `UnknownAtomError`,
`ValidationError` (`.problems`).

Independent project, MIT licensed, not affiliated with Google or Anthropic.
Source: https://github.com/a2uicatalog/a2ui (`sdk/python/`).
