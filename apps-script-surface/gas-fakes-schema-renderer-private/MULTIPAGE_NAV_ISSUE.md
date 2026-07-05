# Multi-Page Nav Issue — GAS LMS Renderer

**Date:** 2026-06-20  
**Symptom URL:** `?nav=gen-ai-mod1&from=generative-ai-for-professionals`  
**Symptom:** Clicking a module card on a course hub page navigates to `?nav=gen-ai-mod1` which returns "Page not found: gen-ai-mod1" because nothing is stored under that slug in ScriptProperties.

---

## Root Cause Diagnosis

### How the nav system works

There are two distinct ways a page is served:

| Route | Mechanism | Requires save? |
|---|---|---|
| `?nav=<slug>` | Reads `nav:<slug>` from ScriptProperties → decodes stored payload | **Yes** — explicit or auto |
| `?p=<base64>` | Decodes payload inline from URL parameter | **No** |

The correct LMS pattern (per `Code.js` system prompt rule 8b) is:  
**module pages use inline `page: [...]` arrays** in `module_map` blocks. The `module_map` renderer in `atoms_lms.gs` encodes each module's `page` array into a `?p=<base64>&from=<hub-slug>` URL at server render time — no separate save needed.

### What went wrong

Gemini generated module entries with `url` fields pointing to `?nav=` slugs:

```json
{
  "type": "module_map",
  "modules": [
    { "id": "mod1", "title": "Module 1", "url": "?nav=gen-ai-mod1" }
  ]
}
```

...instead of inline `page` arrays:

```json
{
  "type": "module_map",
  "modules": [
    { "id": "mod1", "title": "Module 1", "page": [ ...atom blocks... ] }
  ]
}
```

When the `url` approach is used:
1. Hub page saves fine (or auto-saves from title)  
2. Module cards link to `?nav=gen-ai-mod1`  
3. `ScriptProperties.getProperty('nav:gen-ai-mod1')` returns null  
4. `_renderNamedPage` returns error page: **"Page not found: gen-ai-mod1"**

The module pages were never saved because the only automatic save is:
- In `_renderFromPayload` — fires when a `?p=` page containing `module_map` is visited for the first time
- Via manual `a2uiNavSave()` call from the Page Builder UI

Neither happens for module pages when they're referenced by `url` field alone.

---

## Secondary Issue: Auto-Save Fragility for Hub Pages

Even for hub pages (which DO auto-save), the mechanism is fragile:

```javascript
// Code.js _renderFromPayload()
var autoSlug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/, '');
props.setProperty('nav:' + autoSlug, ...);
```

**Problem 1 — Slug derived from title must match atom references.**  
If the hub title is "Generative AI for Professionals", the slug becomes `generative-ai-for-professionals`. But `nav_bar` and `nav_link` atoms inside module pages reference `nav_slug: "gen-ai-hub"` (the short form used in the system prompt examples). These won't match. The back button will navigate to `?nav=gen-ai-hub` which won't exist.

**Problem 2 — 9KB ScriptProperties limit per value.**  
Large course hub payloads (especially with multiple modules containing full `page` arrays) can exceed this limit. Auto-save has a silent catch block so this failure is invisible.

**Problem 3 — Auto-save only fires once.**  
`if (!props.getProperty('nav:' + autoSlug))` — if the page was updated/regenerated, the stored version is stale. The user must delete the old entry and revisit.

**Problem 4 — GAS execution concurrency.**  
`_CURRENT_NAV_SLUG` is a file-level global. In GAS, each request gets a fresh script instance, so this is actually safe — but it means `_CURRENT_NAV_SLUG` is only set when `_renderNamedPage` is called. When the hub is served via `?p=` (not `?nav=`), the auto-save code sets `_CURRENT_NAV_SLUG = autoSlug`, so module URLs in `module_map` get `&from=autoSlug`. This is correct when it works, but breaks if auto-save is skipped (e.g. ScriptProperties limit hit).

---

## The Correct Working Pattern

When the system works as designed:

1. **Page Builder generates** hub page JSON with `module_map` using `page` arrays (not `url` fields)

2. **User clicks Preview** → visits `?p=<hub-base64>`

3. **Auto-save fires** (`_renderFromPayload`): slug derived from hub title, stored as `nav:<hub-slug>`, `_CURRENT_NAV_SLUG` set

4. **`module_map` atom renders**: for each module with a `page` array, it server-side encodes:
   ```
   ?p=<encoded-module-blocks>&from=<_CURRENT_NAV_SLUG>
   ```

5. **User clicks Module 1 card** → navigates (via `target="_top"`) to `?p=<mod1>&from=gen-ai-hub`

6. **Module page loads** via `_renderFromPayload` (no save needed):
   - `_A2UI_NAV = { slug: '', from: 'gen-ai-hub', url: '...' }`
   - `nav_bar` and `nav_link` atoms see `nav.from = 'gen-ai-hub'` and build back links as `?nav=gen-ai-hub`

7. **Back button click** → `?nav=gen-ai-hub` → `_renderNamedPage('gen-ai-hub')` → hub reloads fresh from ScriptProperties, `progress_store` re-reads Sheets state

8. **Module completion badge appears** because hub re-renders with updated Sheets data

---

## Solutions

### Fix 1 — Enforce `page` arrays in Gemini output (already partially done)

The system prompt in `Code.js` (`_buildSystemPrompt`) already has rule 8b:

> NEVER use a "url" field pointing to ?nav=... for module destinations. The page array is encoded at render time into a self-contained URL with no extra saves required.

But this isn't being followed reliably. Strengthen it by adding a **validation pass** in `callGemini()` that detects `url` fields on module entries and rejects the response.

```javascript
// After JSON.parse(text), before encoding:
var blocks = Array.isArray(pageJson) ? pageJson : (pageJson.blocks || []);
blocks.forEach(function(b) {
  if (b.type === 'module_map') {
    (b.modules || []).forEach(function(m, i) {
      if (m.url && !m.page) {
        throw new Error(
          'Gemini used url: "' + m.url + '" for module "' + (m.title || i) +
          '" — must use page: [...] array instead. Regenerating.'
        );
      }
    });
  }
});
```

If validation throws, return an error to the UI telling the user to regenerate.

### Fix 2 — Explicit save slug, not title-derived

Replace title-derived auto-save slug with an explicit `hub_slug` field on the hub page JSON (or `progress_store`'s `course_id`):

```json
{ "title": "...", "theme": "dark", "hub_slug": "gen-ai-hub", "blocks": [...] }
```

In `_renderFromPayload`:
```javascript
var hubSlug = (!Array.isArray(payload) && payload.hub_slug) ? payload.hub_slug : autoSlug;
```

This makes the saved slug predictable and decoupled from the title. The system prompt should instruct Gemini to set `hub_slug` equal to `course_id` from `progress_store`.

### Fix 3 — Cascade-save module pages from hub

When a hub page with `module_map` is saved (auto or manual), walk the module list and save any `page` array modules individually under their `id` slug:

```javascript
// In _renderFromPayload, after auto-saving hub:
modules.forEach(function(m) {
  if (m.page && m.page.length && m.id) {
    var modPayload = { title: m.title, theme: 'dark', blocks: m.page };
    var modJson = JSON.stringify(modPayload);
    var modEnc = Utilities.base64EncodeWebSafe(
      Utilities.gzip(Utilities.newBlob(modJson, 'application/json')).getBytes()
    ).replace(/=+$/, '');
    var modMeta = JSON.stringify({ title: m.title, encoded: modEnc, saved: new Date().toISOString() });
    if (modMeta.length <= 9000) {
      try { props.setProperty('nav:' + m.id, modMeta); } catch(e) {}
    }
  }
});
```

This makes `?nav=gen-ai-mod1` work even if the module was originally defined with a `url` field (as long as the hub was saved with a `page` array).

### Fix 4 — Page Builder UI validation warning

In `Index.html` / `PageBuilder.html`, after generating a page, scan the JSON for module entries with `url` but no `page`, and show a red warning:

> ⚠️ Module "Module 1" uses a `url` field — this requires a separate save for each module. Consider regenerating with the `page` field pattern to avoid manual saves.

### Fix 5 — `?nav=` fallback to inline generation

When `_renderNamedPage` returns "Page not found", instead of an error page, redirect to the builder with a pre-filled prompt:

> "Page '{slug}' was not found. It may not have been saved yet. Go to the Builder to regenerate."

---

## Immediate Workaround (No Code Changes)

If you have a course hub already generated with `url`-based module references:

1. Open the Page Builder (`?mode=builder`)
2. For each module, use the builder to generate the module content
3. Use **Save Page** with the slug matching what the hub references (e.g. `gen-ai-mod1`)
4. Repeat for each module

OR: regenerate the entire hub, force Gemini to use `page` arrays by including this in the prompt:

> IMPORTANT: Do NOT use url fields for modules. Every module MUST have a "page" array with the full atom content inline. No ?nav= references.

---

## Files to Change

| File | Change |
|---|---|
| `Code.js` | `_renderFromPayload` — add `page`-array validation; add cascade-save; support `hub_slug` field |
| `Code.js` | `callGemini` — post-parse validation block rejecting `url`-only modules |
| `Code.js` | `_buildSystemPrompt` — add `hub_slug` instruction, add concrete failure example for `url` pattern |
| `atoms_lms.gs` | `module_map` — already correct for `page` arrays; no change needed |
| `atoms_nav.gs` | `nav_link` / `nav_bar` — already use `_top` target; no change needed |
| `Index.html` or `PageBuilder.html` | Add post-generation JSON scan warning for `url`-only modules |
