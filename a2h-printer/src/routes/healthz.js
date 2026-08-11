// GET /status — registry-driven: reports which platform adapters are
// configured, without ever echoing secret VALUES (names only, matching
// config.js's mcpAllowedOwners "don't echo secrets, free recon" discipline).
import { adapters } from '../adapters/registry.js';
import { config } from '../config.js';

export async function handleHealthz(c) {
  const platforms = {};
  for (const a of adapters) {
    platforms[a.id] = { configured: a.isConfigured(), missing: a.missingConfig() };
  }
  return c.json({
    ok: true,
    platforms,
    storage: { backend: config.databaseUrl ? 'postgres (unimplemented)' : 'sqlite' },
    render_fallback: { configured: Boolean(config.renderSigningKey && config.renderBaseUrl) },
  });
}
