# Authentication — A2UI Atomic Catalog

**Most agents need no credential at all.** The primary MCP server is public and
unauthenticated. If you are here because a scanner or a spec told you to look for
`/auth.md`, the short answer is: just call the endpoint.

```http
POST https://a2uicatalog.ai/mcp
Content-Type: application/json

{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
```

No API key, no signup, no OAuth, no account. Rate limits are enforced per client
without identity (see [Rate limits](#rate-limits)).

The rest of this document describes an **optional** authenticated endpoint that exists
only for enterprise platforms whose connector model cannot call an unauthenticated
service. You almost certainly do not need it.

## Discover

Two MCP endpoints serve the **same tools**:

| Endpoint | Auth | Who it is for |
|---|---|---|
| `https://a2uicatalog.ai/mcp` | None | Everyone. The default. |
| `https://a2uicatalog.ai/mcp-auth` | Required | Platforms that mandate credentialed, attributed access |

Machine-readable discovery documents:

- Protected resource metadata (RFC 9728): `https://a2uicatalog.ai/.well-known/oauth-protected-resource`
- Authorization server metadata (RFC 8414): `https://a2uicatalog.ai/.well-known/oauth-authorization-server`
- Live server descriptor: `GET https://a2uicatalog.ai/mcp` with `Accept: application/json`

An unauthenticated request to `/mcp-auth` returns `401` with a `WWW-Authenticate`
header carrying a `resource_metadata` pointer to the RFC 9728 document above.

## Pick a method

`/mcp-auth` accepts three credential types, in this precedence order. All three are
provisioned by hand — see [Register](#register).

1. **OAuth 2.0 Bearer token** — `Authorization: Bearer <access_token>`.
   The path enterprise platforms use; Gemini Enterprise's BYO-MCP data store offers
   OAuth 2.0 and nothing else.
2. **API key** — `X-Api-Key: <key>`.
   For platforms whose connector template offers an API key field but no OAuth
   (e.g. GCP Agent Registry / Integration Connectors).
3. **HTTP Basic** — `Authorization: Basic <base64(user:pass)>`.

## Register

**There is no self-service registration endpoint, and this server does not implement
RFC 7591 dynamic client registration.** Any `register_uri` you may have seen advertised
for this domain would be wrong — nothing would resolve.

Registration is manual and deliberate: one `client_id` per organization, because the
client *is* the tenant, and that tenant governs its own users. To request credentials,
open an issue or contact the maintainer via
[a2uicatalog.ai/contact](https://a2uicatalog.ai/contact/). You will be asked for the
exact `redirect_uri` values your platform uses — they are matched exactly, and an
unregistered value is refused with a diagnostic listing what *is* registered.

If you do not want to wait for a human, use the public `/mcp` endpoint instead. It is
the same server with the same tools.

## Use the credential

Once registered, run a standard OAuth 2.0 authorization-code flow:

```http
GET https://a2uicatalog.ai/mcp-oauth/authorize
  ?response_type=code
  &client_id=<your_client_id>
  &redirect_uri=<your_registered_redirect_uri>
  &state=<opaque>
  &code_challenge=<S256_challenge>        # optional, recommended
  &code_challenge_method=S256
```

Exchange the returned `code` for a token:

```http
POST https://a2uicatalog.ai/mcp-oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=<code>
&redirect_uri=<same_redirect_uri>
&client_id=<your_client_id>
&client_secret=<your_client_secret>
&code_verifier=<verifier>                 # if you sent a challenge
```

Response:

```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "...",
  "scope": ""
}
```

Then call the MCP endpoint with the token:

```http
POST https://a2uicatalog.ai/mcp-auth
Authorization: Bearer <access_token>
Content-Type: application/json

{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
```

Supported parameters, precisely: `response_type=code` only; `grant_type` of
`authorization_code` or `refresh_token`; PKCE optional but **`S256` only** (`plain` is
refused); client authentication via `client_secret_post` or `client_secret_basic`.
Access tokens live 1 hour, refresh tokens 30 days.

## Refresh

```http
POST https://a2uicatalog.ai/mcp-oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token=<refresh_token>
&client_id=<your_client_id>
&client_secret=<your_client_secret>
```

Refresh tokens are single-use and rotated: each refresh returns a new one and
invalidates the old.

## Errors

Errors follow OAuth 2.0 (RFC 6749 §5.2) — a JSON body with `error` and, where useful,
`error_description`.

| Error | Meaning |
|---|---|
| `invalid_client` | Unknown `client_id`, or wrong/missing `client_secret` |
| `invalid_grant` | Code or refresh token expired, already used, or issued to another client |
| `unsupported_grant_type` | Only `authorization_code` and `refresh_token` are supported |
| `unsupported_response_type` | Only `response_type=code` is supported |
| `invalid_request` | Malformed request; e.g. `code_challenge_method` other than `S256` |

An invalid `redirect_uri` is **not** redirected back (that would be an open redirect) —
it returns `400` with a plain-text diagnostic listing the registered values.

MCP tool-call failures are separate: they return a JSON-RPC result with `isError: true`
and a `_meta.errorCode` (a stable machine-matchable string such as `UNKNOWN_TOOL`) plus
`_meta.message`.

## Revocation

There is no public revocation endpoint (RFC 7009 is not implemented). Access tokens
expire in 1 hour and refresh tokens in 30 days; a refresh rotates and invalidates its
predecessor. To revoke a client outright — immediately invalidating its ability to mint
new tokens — contact the maintainer, who removes it from the registered client set.

## Rate limits

Rate limits apply to the public endpoint and are enforced against a **SHA-256 hash of
the client IP**, never the IP itself and never payload content. Current published
limits, also returned live from `GET /mcp` with `Accept: application/json`:

| Tool | Limit |
|---|---|
| `preview_url` | 10 per client per 7 days |
| `render_surface` / `render_ping` | 300 per IP per day |
| `publish_url` | 20 per IP per day |

Responses that hit a limit carry `X-RateLimit-Limit` and `X-RateLimit-Remaining`.

## Notes

Free and MIT licensed. Independent, unofficial project — not affiliated with, endorsed
by, or sponsored by Google or Anthropic. A2UI is Google's protocol; MCP is Anthropic's.

Source: <https://github.com/a2uicatalog/a2ui>
