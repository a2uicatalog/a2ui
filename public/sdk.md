---
title: A2UI Atomic Catalog — SDK & Client Libraries
description: Official SDKs, CLI tools, Agent Skills, and client generators for A2UI Atomic Catalog.
canonical: https://a2uicatalog.ai/sdk.md
---

# A2UI Atomic Catalog — SDK & Client Libraries

Official client libraries, SDK packages, CLI tools, and agent integrations for the A2UI Atomic Catalog (540 atoms).

## Official Packages

- **npm CLI / Local MCP Server**: [`@a2uicatalog/mcp`](https://registry.npmjs.org/@a2uicatalog/mcp)
  - Direct render: `npx -p @a2uicatalog/mcp a2ui render page.json`
  - Local MCP server: `npx @a2uicatalog/mcp`
- **Agent Skills**: `npx skills add a2uicatalog/a2ui` (skills index at `https://a2uicatalog.ai/.well-known/agent-skills/index.json`)
- **Python / A2A Extension**: `renderers/a2a_extension.py` in the GitHub repo for A2A SDK interop.

## Generating Native Client SDKs

Generate typed client SDKs in any language from our OpenAPI 3.1 specification:

    npx @openapitools/openapi-generator-cli generate \
      -i https://a2uicatalog.ai/openapi.json \
      -g typescript-fetch \
      -o ./src/a2ui-client

## Reference

- Developer Portal: https://a2uicatalog.ai/developers/
- OpenAPI Specification: https://a2uicatalog.ai/openapi.json
- MCP Server Endpoint: https://a2uicatalog.ai/mcp
- Full Atom Vocabulary: https://a2uicatalog.ai/spec.json
- Full documentation: https://a2uicatalog.ai/docs/
