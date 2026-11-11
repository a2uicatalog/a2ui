# Official MCP Registry entries

`catalog.server.json` and `docs.server.json` are this project's entries in the official MCP Registry
(registry.modelcontextprotocol.io), under the `ai.a2uicatalog` namespace.

The namespace is proved by HTTP: `public/.well-known/mcp-registry-auth` holds the Ed25519 public key; the
private key never enters this repo. To publish a new version, bump `version` in the file, copy it to
`server.json`, then `mcp-publisher login http --domain a2uicatalog.ai --private-key <hex>` and
`mcp-publisher publish`.
