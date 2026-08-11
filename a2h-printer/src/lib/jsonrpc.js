// JSON-RPC 2.0 envelope helpers for routes/mcp.js. Small and single-purpose,
// matching this codebase's crypto-utils.js pattern — not a general JSON-RPC
// library, just the two shapes the MCP dispatcher needs.

export function mcpResult(id, result) {
  return { jsonrpc: '2.0', id, result };
}

export function mcpError(id, code, message) {
  return { jsonrpc: '2.0', id, error: { code, message } };
}

// Standard JSON-RPC 2.0 error codes (the ones this dispatcher actually uses —
// see routes/mcp.js's two-tier error mapping: these are for malformed
// requests/protocol errors only, never for a tool call that failed for a
// valid reason — that's a tools/call RESULT with isError:true instead).
export const PARSE_ERROR = -32700;
export const INVALID_REQUEST = -32600;
export const METHOD_NOT_FOUND = -32601;
export const INVALID_PARAMS = -32602;
export const INTERNAL_ERROR = -32603;
