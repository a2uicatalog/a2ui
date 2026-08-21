# Pricing — A2UI Atomic Catalog

**Free. No signup, no API key, no card.**

| Surface | Cost | Limits |
|---|---|---|
| MCP server — `https://a2uicatalog.ai/mcp` | Free | No authentication required. Fair-use rate limiting only. |
| `POST /api/render` | Free | 50 requests per day per client. Responses are edge-cached, and a cache hit does not count. |
| `POST /api/compose` | Free | 20 requests per day per client (free-tier inference). |
| `GET /ask` | Free | 60 requests per day per client. |
| Catalogue documents — `spec.json`, `openapi.json`, `llms.txt`, ARD catalog | Free | Unmetered. |
| Self-hosting | Free | MIT licensed. Deploy your own renderer for unlimited rendering. |

There is no paid tier, no enterprise plan and no upgrade path, because there is
nothing to upgrade to. The vocabulary is MIT licensed and the renderers are in
the public repository — anything you hit a limit on here, you can run yourself
without asking.

Rate limits exist to keep a free service available, not to sell a larger one.
They are returned in `X-RateLimit-*` headers with `Retry-After` on 429.

Source: https://github.com/a2uicatalog/a2ui · Licence: MIT
