// A2UI Basic Catalog demo controller (plain import(), replace() for variants)
(() => {
  'use strict';
  const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]):not([type="hidden"]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
  const CHECK_FUNCTIONS = new Set(['required', 'regex', 'length', 'numeric', 'email', 'and', 'or', 'not']);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const mobileNav = window.matchMedia('(max-width: 63.99rem)');
  let bundlePromise = null;

  // plain import() raced against the timeout (keeps the module cache; no blob: needed)
  function loadBundleOnce(url, timeoutMs) {
    if (bundlePromise) return bundlePromise;
    const abs = new URL(url, document.baseURI).href;
    bundlePromise = Promise.race([
      import(abs),
      new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), Number(timeoutMs) || 8000)),
    ]).catch((err) => { bundlePromise = null; throw err; });
    return bundlePromise;
  }
  function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
  function waitCommit() { return new Promise((r) => requestAnimationFrame(() => setTimeout(r, 30))); }
  function flattenModel(obj, prefix = '', out = {}) {
    if (!obj || typeof obj !== 'object') return out;
    for (const [k, v] of Object.entries(obj)) {
      const ptr = prefix + '/' + k;
      if (v && typeof v === 'object' && !Array.isArray(v)) flattenModel(v, ptr, out); else out[ptr] = v;
    }
    return out;
  }

  async function probeOnce(bundle, fnName, args, baseMessages, dataModel) {
    const scratch = document.createElement('div');
    scratch.hidden = true; document.body.append(scratch);
    const baseCreate = baseMessages.find((m) => m.createSurface)?.createSurface || {};
    const surfaceId = 'fn-probe';
    const messages = [{ version: '1.0', createSurface: { surfaceId, catalogId: baseCreate.catalogId } }];
    if (dataModel && typeof dataModel === 'object') messages.push({ version: '1.0', updateDataModel: { surfaceId, path: '/', value: dataModel } });
    if (fnName === 'openUrl') {
      messages.push({ version: '1.0', updateComponents: { surfaceId, components: [
        { id: 'root', component: 'Button', child: 'lbl', action: { functionCall: { '@call': 'openUrl', args } } },
        { id: 'lbl', component: 'Text', text: 'Open' }] } });
    } else if (CHECK_FUNCTIONS.has(fnName)) {
      messages.push({ version: '1.0', updateComponents: { surfaceId, components: [
        { id: 'root', component: 'Button', child: 'lbl', action: { event: { name: 'noop' } },
          checks: [{ condition: { '@call': fnName, args, returnType: 'boolean' }, message: 'BAD' }] },
        { id: 'lbl', component: 'Text', text: 'Check' }] } });
    } else {
      messages.push({ version: '1.0', updateComponents: { surfaceId, components: [
        { id: 'root', component: 'Text', text: { '@call': fnName, args, returnType: 'string' } }] } });
    }
    let loggedUrl = null;
    const instance = bundle.mount(scratch, messages, {
      onAction(act) { if (act?.name === 'openUrl') loggedUrl = act.url ?? act.context?.url ?? args?.url ?? ''; },
      onDataModel() {},
    });
    try {
      // wait until the renderer has drawn something (up to 2 s) instead of a fixed short wait
      for (let i = 0; i < 40; i++) { await waitCommit(); if (scratch.querySelector('button,[role="button"]') || (scratch.textContent || '').trim()) break; await new Promise((r) => setTimeout(r, 40)); }
      if (fnName === 'openUrl') { scratch.querySelector('button,[role="button"]')?.click(); await waitCommit(); return 'would open ' + (loggedUrl ?? args?.url ?? ''); }
      if (CHECK_FUNCTIONS.has(fnName)) {
        const btn = scratch.querySelector('button,[role="button"]');
        return 'disabled=' + (!btn || btn.disabled || btn.getAttribute('aria-disabled') === 'true' ? 'True' : 'False');
      }
      return (scratch.textContent || '').trim();
    } finally { instance.destroy(); scratch.remove(); }
  }

  // probes run one at a time (14 functions start together from the group button)
  let probeChain = Promise.resolve();
  function probeFunctionWithRenderer(...a) { const run = () => probeOnce(...a); probeChain = probeChain.then(run, run); return probeChain; }

  function initIndex() {
    const nav = document.querySelector('.catalog-index'); if (!nav) return;
    const toggle = nav.querySelector('.jump-toggle');
    if (toggle) {
      const sync = () => toggle.setAttribute('aria-expanded', mobileNav.matches ? 'false' : 'true');
      sync(); mobileNav.addEventListener('change', sync);
      toggle.addEventListener('click', () => toggle.setAttribute('aria-expanded', String(toggle.getAttribute('aria-expanded') !== 'true')));
      nav.addEventListener('click', (e) => { if (e.target.closest('a[href^="#"]') && mobileNav.matches) toggle.setAttribute('aria-expanded', 'false'); });
      nav.addEventListener('keydown', (e) => { if (e.key === 'Escape' && mobileNav.matches && toggle.getAttribute('aria-expanded') === 'true') { toggle.setAttribute('aria-expanded', 'false'); toggle.focus(); } });
    }
    const links = new Map();
    nav.querySelectorAll('a[href^="#"]').forEach((a) => { a.removeAttribute('aria-current'); links.set(a.getAttribute('href').slice(1), a); });
    const spy = new IntersectionObserver((entries) => {
      for (const en of entries) { if (!en.isIntersecting) continue; links.forEach((a) => a.removeAttribute('aria-current')); links.get(en.target.id)?.setAttribute('aria-current', 'location'); }
    }, { rootMargin: '-15% 0px -70% 0px', threshold: 0 });
    document.querySelectorAll('.catalog-card[id]').forEach((c) => spy.observe(c));
  }

  function initInspectorTabs(card) {
    const tablist = card.querySelector('.inspector-tabs [role="tablist"]'); if (!tablist) return;
    const tabs = Array.from(tablist.querySelectorAll('[role="tab"]'));
    function activate(next, focus) {
      tabs.forEach((t) => { const on = t === next; t.setAttribute('aria-selected', String(on)); t.tabIndex = on ? 0 : -1;
        const panel = card.querySelector('#' + CSS.escape(t.getAttribute('aria-controls'))); if (panel) panel.hidden = !on; });
      if (focus) next.focus();
    }
    tablist.addEventListener('click', (e) => { const t = e.target.closest('[role="tab"]'); if (t) activate(t, false); });
    tablist.addEventListener('keydown', (e) => {
      const i = tabs.indexOf(document.activeElement); if (i < 0) return;
      const map = { ArrowRight: tabs[(i + 1) % tabs.length], ArrowLeft: tabs[(i - 1 + tabs.length) % tabs.length], Home: tabs[0], End: tabs[tabs.length - 1] };
      if (map[e.key]) { e.preventDefault(); activate(map[e.key], true); }
    });
  }

  function attachModalTrap(card, mountEl, onEscape) {
    if (card.dataset.modalWrapper !== 'true') return;
    let triggerEl = null;
    const getDialog = () => mountEl.querySelector('[role="dialog"],dialog[open],[aria-modal="true"]');
    mountEl.addEventListener('click', (e) => { const b = e.target.closest('button,[role="button"]'); if (b && mountEl.dataset.modalOpen !== 'true') triggerEl = b; }, true);
    new MutationObserver(() => {
      const dlg = getDialog(), open = Boolean(dlg), was = mountEl.dataset.modalOpen === 'true';
      if (open === was) return; // writing data-modal-open re-triggered this observer forever; act only on a real change
      mountEl.dataset.modalOpen = String(open);
      if (open && !was) dlg.querySelector(FOCUSABLE)?.focus();
      else if (!open && was && triggerEl?.isConnected) { triggerEl.focus(); triggerEl = null; }
    }).observe(mountEl, { childList: true, subtree: true, attributes: true, attributeFilter: ['open', 'role', 'aria-modal'] });
    mountEl.addEventListener('keydown', (e) => {
      if (mountEl.dataset.modalOpen !== 'true') return;
      const dlg = getDialog() || mountEl;
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onEscape(dlg); }
      else if (e.key === 'Tab') {
        const nodes = Array.from(dlg.querySelectorAll(FOCUSABLE)).filter((n) => n.offsetParent !== null); if (!nodes.length) return;
        if (e.shiftKey && document.activeElement === nodes[0]) { e.preventDefault(); nodes[nodes.length - 1].focus(); }
        else if (!e.shiftKey && document.activeElement === nodes[nodes.length - 1]) { e.preventDefault(); nodes[0].focus(); }
      }
    });
  }

  function updateSnapshotHolder(holder, vMeta, name) {
    if (!holder || !vMeta) return;
    holder.textContent = '';
    if (!vMeta.snapshot) { const d = document.createElement('div'); d.className = 'snapshot-null'; d.setAttribute('role', 'note'); d.textContent = 'No static render: ' + (vMeta.reason || 'not rendered'); holder.append(d); return; }
    ['light', 'dark'].forEach((mode) => { const img = document.createElement('img'); img.className = 'snap-img snap-' + mode; img.src = vMeta.snapshot[mode]; img.width = 440; img.alt = mode === 'light' ? 'Recorded render of ' + name + ' (' + vMeta.value + ')' : ''; holder.append(img); });
  }

  function initCard(card) {
    const canonical = card.querySelector('.canonical-messages-json'); if (!canonical) return;
    const baseMessages = JSON.parse(canonical.textContent);
    const cardMeta = JSON.parse(card.querySelector('.card-meta-json')?.textContent || '{}');
    const q = (s) => card.querySelector(s);
    const statusEl = q('.demo-status'), liveRegion = q('.live-demo-region'), mountEl = q('.a2ui-mount-scope'),
      msgView = q('[data-slot="messages-view"]'), dataView = q('[data-slot="data-view"]'), dataAnnouncer = q('[data-slot="data-announcer"]'),
      logList = q('[data-slot="action-log"]'), logAnnouncer = q('[data-slot="log-announcer"]'), demoHeading = q('.live-demo-region h3, .live-demo-region h4'), snapHolder = q('[data-slot="snapshot-holder"]');
    let instance = null, loadedBundle = null, prevFlat = {}, activeMessages = structuredClone(baseMessages);
    const announceData = debounce((p, v) => { if (dataAnnouncer) dataAnnouncer.textContent = 'Data model ' + p + ': ' + JSON.stringify(v); }, 400);
    const announceLog = debounce((t) => { if (logAnnouncer) logAnnouncer.textContent = t; }, 400);
    function logEntry(name, detail) {
      if (!logList) return;
      const li = document.createElement('li'); const text = typeof detail === 'string' ? detail : JSON.stringify(detail ?? {});
      li.textContent = '[' + new Date().toLocaleTimeString('en-US', { hour12: false }) + '] ' + name + ' - ' + text; logList.prepend(li); announceLog(name + ': ' + text);
    }
    function updateDataPanel(model) {
      if (!dataView) return;
      const flat = flattenModel(model); let changed = null;
      for (const [k, v] of Object.entries(flat)) if (JSON.stringify(prevFlat[k]) !== JSON.stringify(v)) changed = k;
      prevFlat = flat; dataView.textContent = '';
      const keys = Object.keys(flat); if (!keys.length) { dataView.textContent = '{}'; return; }
      keys.forEach((p) => { const line = p + ': ' + JSON.stringify(flat[p]);
        if (p === changed) { const m = document.createElement('mark'); m.className = 'changed-path'; m.textContent = line; dataView.append(m, '\n'); announceData(p, flat[p]); } else dataView.append(line + '\n'); });
    }
    function setVariantProvenance(tested) {
      card.querySelectorAll('[data-slot="provenance-pill"],[data-slot="live-provenance-pill"]').forEach((p) => { p.dataset.verdict = tested ? 'PASS' : 'ILLUSTRATIVE'; p.textContent = tested ? 'What you try is exactly what we tested' : 'Illustrative, not tested'; });
      const b = q('[data-slot="evidence-badge"]'), v = q('[data-slot="evidence-verdict"]'), t = q('[data-slot="evidence-text"]');
      if (b && v && t) { v.dataset.verdict = tested ? b.dataset.recordedVerdict : 'UNTESTED'; v.textContent = tested ? b.dataset.recordedVerdict : 'UNTESTED'; t.textContent = tested ? b.dataset.recordedText : 'no test result for this variant'; }
    }
    initInspectorTabs(card);
    if (mountEl) new MutationObserver(() => { if (!reducedMotion.matches) return; mountEl.querySelectorAll('video,audio').forEach((m) => { m.autoplay = false; if (!m.paused) m.pause(); }); }).observe(mountEl, { childList: true, subtree: true });

    // round 6: one load path for arrival auto-load and the Reload / Verify buttons; never runs twice
    const loadBtn = q('[data-action="load-demo"]');
    const frameRecorded = q('[data-slot="frame-label-recorded"]'), frameLive = q('[data-slot="frame-label-live"]');
    async function runLoadDemo({ moveFocus = true } = {}) {
      if (card.dataset.demoState === 'loading' || card.dataset.demoState === 'loaded') return;
      const btn = loadBtn || { setAttribute() {}, removeAttribute() {} };
      card.dataset.demoState = 'loading'; btn.setAttribute('aria-busy', 'true');
      if (frameRecorded && frameRecorded.dataset.defaultLabel) frameRecorded.textContent = frameRecorded.dataset.defaultLabel;
      if (statusEl) { statusEl.hidden = false; statusEl.textContent = 'Loading live demo…'; }
      try {
        loadedBundle = await loadBundleOnce(card.dataset.bundleUrl, card.dataset.timeoutMs);
        activeMessages = structuredClone(baseMessages);
        if (msgView) msgView.textContent = JSON.stringify(activeMessages, null, 2);
        if (mountEl && card.dataset.kind === 'component') {
          instance = loadedBundle.mount(mountEl, activeMessages, {
            onAction(act) { if (act?.name === 'openUrl') { logEntry('openUrl', 'would open ' + (act.url ?? act.context?.url ?? '')); return; } logEntry(act?.name || 'action', act?.context ?? {}); },
            onDataModel(model) { const a = document.activeElement; updateDataPanel(model); if (a && mountEl.contains(a) && a.isConnected) a.focus(); },
          });
          attachModalTrap(card, mountEl, (dlg) => { const c = dlg.querySelector('[aria-label*="close" i],button:last-of-type'); if (c) c.click(); else instance.reset(); });
        }
        if (card.dataset.kind === 'function') {
          for (const row of card.querySelectorAll('tr[data-args-json]')) {
            const parsed = JSON.parse(row.dataset.argsJson); const dm = row.dataset.modelJson ? JSON.parse(row.dataset.modelJson) : null;
            const out = await probeFunctionWithRenderer(loadedBundle, card.dataset.name, parsed, baseMessages, dm);
            const c = row.querySelector('[data-cell="observed"] code'); if (c) c.textContent = out;
          }
        }
        btn.removeAttribute('aria-busy'); if (liveRegion) liveRegion.hidden = false;
        if (statusEl) { statusEl.hidden = false; statusEl.textContent = frameLive ? frameLive.textContent.replace(/\s+/g, ' ').trim() : 'Live demo mounted'; }
        card.dataset.demoState = 'loaded'; if (moveFocus) demoHeading?.focus({ preventScroll: true });
      } catch (err) {
        card.dataset.demoState = 'failed'; btn.removeAttribute('aria-busy');
        if (frameRecorded) frameRecorded.textContent = 'Recorded snapshot (live demo did not load)';
        if (statusEl) { statusEl.hidden = false; statusEl.textContent = 'Live demo did not load; this is the recorded result from ' + (card.dataset.evidenceDate || '14 Nov 2026'); }
      }
    }
    loadBtn?.addEventListener('click', () => runLoadDemo({ moveFocus: true }));
    if (card.dataset.autoload === 'true') requestAnimationFrame(() => setTimeout(() => runLoadDemo({ moveFocus: false }), 0));

    // variant picker: PM edit, rewrites the message and calls replace() (send() would re-create an existing surface)
    card.addEventListener('change', (e) => {
      const radio = e.target.closest('input[type="radio"][data-prop]'); if (!radio) return;
      const prop = radio.dataset.prop, tested = radio.dataset.tested === 'true';
      const vMeta = (cardMeta.variants || []).find((v) => v.prop === prop && String(v.value) === radio.value);
      if (vMeta) updateSnapshotHolder(snapHolder, vMeta, card.dataset.name);
      activeMessages = structuredClone(baseMessages);
      for (const m of activeMessages) {
        const list = m.createSurface?.components || m.updateComponents?.components || [];
        const t = list.find((c) => c.component === card.dataset.name || c.id === radio.dataset.targetId); if (t) t[prop] = radio.value;
      }
      setVariantProvenance(tested); if (msgView) msgView.textContent = JSON.stringify(activeMessages, null, 2);
      if (card.dataset.demoState === 'loaded' && instance) { prevFlat = {}; instance.replace(activeMessages); radio.focus(); }
    });

    q('[data-action="reset-surface"]')?.addEventListener('click', () => {
      activeMessages = structuredClone(baseMessages); prevFlat = {};
      const def = q('input[type="radio"][data-default="true"]');
      if (def) { def.checked = true; setVariantProvenance(def.dataset.tested === 'true'); instance?.replace(activeMessages); } else { setVariantProvenance(true); instance?.reset(); }
      if (msgView) msgView.textContent = JSON.stringify(activeMessages, null, 2);
      card.querySelectorAll('tr[data-custom-row="true"]').forEach((r) => r.remove());
      logEntry('reset', 'deleteSurface -> createSurface'); demoHeading?.focus();
    });
    q('[data-action="copy-message"]')?.addEventListener('click', async () => {
      const st = q('[data-slot="copy-status"]');
      try { await navigator.clipboard.writeText(JSON.stringify(activeMessages, null, 2)); if (st) st.textContent = 'Copied'; } catch { if (st) st.textContent = 'Copy unavailable'; }
    });
    q('[data-action="eval-custom-fn"]')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const input = e.currentTarget.elements.namedItem('args'), tbody = card.tagName === 'TBODY' ? card : q('[data-slot="fn-table"] tbody'), ann = q('[data-slot="fn-announcer"]');
      if (!input || !tbody) return;
      if (!loadedBundle) { try { loadedBundle = await loadBundleOnce(card.dataset.bundleUrl, card.dataset.timeoutMs); } catch { if (ann) ann.textContent = 'Live demo did not load.'; return; } }
      try {
        const parsed = JSON.parse(input.value);
        const observed = await probeFunctionWithRenderer(loadedBundle, card.dataset.name, parsed.args ?? parsed, baseMessages, parsed.dataModel ?? null);
        const tr = document.createElement('tr'); tr.dataset.customRow = 'true';
        tr.innerHTML = '<td><code></code></td><td>not in our test set</td><td><code></code></td><td><span class="verdict-pill" data-verdict="UNTESTED">UNTESTED</span></td>';
        const cs = tr.querySelectorAll('code'); cs[0].textContent = JSON.stringify(parsed); cs[1].textContent = observed; const tryRow = tbody.querySelector('.fn-try-row'); if (tryRow) tbody.insertBefore(tr, tryRow); else tbody.append(tr);
        if (ann) ann.textContent = 'Observed ' + observed + ' - not in our test set.'; input.focus();
      } catch { if (ann) ann.textContent = 'Invalid JSON arguments.'; input.focus(); }
    });
  }

  function initFnGroups() {
    document.querySelectorAll('[data-action="load-fn-group"]').forEach((btn) => {
      btn.addEventListener('click', () => {
        btn.setAttribute('aria-busy', 'true');
        btn.closest('.fn-group-section')?.querySelectorAll('tbody.catalog-card[data-demo-state="idle"] [data-action="load-demo"]').forEach((t) => t.click());
        btn.hidden = true;
      });
    });
  }
  function initFilter() {
    const input = document.querySelector('[data-action="filter-catalog"]'), count = document.querySelector('[data-slot="filter-count"]');
    if (!input) return;
    input.addEventListener('input', () => {
      const qv = input.value.trim().toLowerCase(); let shown = 0;
      document.querySelectorAll('[data-filter-item]').forEach((it) => { const m = !qv || (it.dataset.filterText || it.textContent || '').toLowerCase().includes(qv); it.hidden = !m; if (m) shown++; });
      document.querySelectorAll('[data-filter-group]').forEach((g) => { g.hidden = !g.querySelector('[data-filter-item]:not([hidden])'); });
      if (count) count.textContent = qv ? shown + ' matching entries' : '';
    });
  }
  function boot() { initFilter(); initIndex(); document.querySelectorAll('.catalog-card').forEach(initCard); initFnGroups(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true }); else boot();
})();
