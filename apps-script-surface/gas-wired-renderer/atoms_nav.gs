// atoms_nav.gs — In-page navigation atoms for A2UI named-page routing.
// All atoms here read window._A2UI_NAV at runtime for the current page context.
// Named pages are stored by a2uiNavSave() and served via ?nav=<slug>.

// ── nav_bar ───────────────────────────────────────────────────────────────────
// Horizontal (or vertical) navigation bar linking to other named pages.
// Generates correct ?nav=<slug>&from=<current_slug> URLs at runtime using
// window._A2UI_NAV so no deployment URL needs to be hard-coded in the JSON.
_RENDERERS['nav_bar'] = function(b) {
  var uid    = 'nvb' + Math.random().toString(36).substr(2, 6);
  var links  = b.links   || [];
  var label  = b.label   || '';
  var layout = b.layout  || 'horizontal';
  var accent = b.accent  || '#6366f1';
  var sticky = b.sticky  !== false; // default true

  // Server-side: build link list JSON for client resolution
  var linksJson = JSON.stringify(links.map(function(l) {
    return {
      slug:    l.nav_slug || '',
      url:     l.url      || '',
      label:   l.label    || '',
      icon:    l.icon     || '',
      active:  !!l.active
    };
  }));

  var isH = layout !== 'vertical';

  var wrapStyle = isH
    ? 'display:flex;flex-wrap:wrap;gap:6px;align-items:center;'
    : 'display:flex;flex-direction:column;gap:4px;';

  if (sticky) {
    wrapStyle += 'position:sticky;top:' + (b.top_offset || '52') + 'px;z-index:100;';
    wrapStyle += 'background:rgba(5,7,15,0.88);backdrop-filter:blur(10px);';
    wrapStyle += 'padding:10px 16px;border-radius:12px;margin-bottom:16px;';
    wrapStyle += 'border:1px solid rgba(255,255,255,0.07);';
  }

  return (
    '<div id="' + uid + '" style="font-family:\'Inter\',system-ui,sans-serif;">' +
    (label ? '<div style="font-size:0.58rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#334155;margin-bottom:8px;">' + _esc(label) + '</div>' : '') +
    '<div style="' + wrapStyle + '" id="' + uid + 'bar"></div>' +
    '<script>(function(){' +
      'var links=' + linksJson + ';' +
      'var nav=window._A2UI_NAV||{slug:"",from:"",url:""};' +
      'var bar=document.getElementById("' + uid + 'bar");' +
      'if(!bar)return;' +
      'links.forEach(function(l){' +
        // On a ?p= page (no named slug) nav_slug targets can't be resolved.
        // Navigate to from-slug if known, else exec root — always via target="_top" anchor.
        // Never use history.back(): it navigates the sandbox iframe not the top window.
        'var href=l.url||"#";' +
        // Relative "?nav=..." urls resolve against the SANDBOX iframe origin
        // (script.googleusercontent.com/userCodeAppPanel), not the app. Anchor
        // them to the injected exec URL (server-knows-its-url), same as slugs.
        // Found 2026-07-08: a benchmark-built app used url:"?nav=lesson1" in
        // nav_bar and its links broke exactly this way.
        'if(href.charAt(0)==="?"&&nav.url){href=nav.url+href;}' +
        // A target slug always resolves forward via nav.url + "?nav="+slug, regardless of
        // whether THIS page has its own nav.slug (true for any plain ?p= landing page, e.g.
        // a nav-budget-pagination nav page) — found live 2026-07-09: !nav.slug used to force
        // every link on such a page into the back-navigation branch, breaking all of them.
        // "Back" now only fires when this link's slug explicitly matches where we came from.
        'var _useBack=!!(l.slug&&nav.from&&l.slug===nav.from);' +
        'if(_useBack){href=nav.url+"?nav="+nav.from;}' +
        'else if(l.slug&&nav.url){href=nav.url+"?nav="+l.slug+(nav.slug?"&from="+nav.slug:"");}' +
        'var isActive=!!(l.active||(l.slug&&l.slug===nav.slug));' +
        'var baseStyle="display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:8px;' +
          'text-decoration:none;font-size:0.75rem;font-weight:600;transition:all 0.15s;white-space:nowrap;' +
          (isH ? '' : 'width:100%;') + '";' +
        'var activeStyle="border:1px solid rgba(99,102,241,0.3);background:rgba(99,102,241,0.12);color:#818cf8;";' +
        'var idleStyle="border:1px solid rgba(255,255,255,0.07);background:rgba(255,255,255,0.03);color:#94a3b8;";' +
        'var a=document.createElement("a");' +
        'a.href=href;' +
        'a.target="_top";' +
        'a.style.cssText=baseStyle+(isActive?activeStyle:idleStyle);' +
        'a.onmouseover=function(){if(!isActive){this.style.background="rgba(255,255,255,0.06)";this.style.color="#e2e8f0";this.style.borderColor="rgba(255,255,255,0.12)";}};' +
        'a.onmouseout=function(){if(!isActive){this.style.background="rgba(255,255,255,0.03)";this.style.color="#94a3b8";this.style.borderColor="rgba(255,255,255,0.07)";}};' +
        'a.innerHTML=(l.icon?"<span>"+l.icon+"</span>":"")+"<span>"+l.label+"</span>";' +
        'bar.appendChild(a);' +
      '});' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── nav_link ──────────────────────────────────────────────────────────────────
// Single CTA button that navigates to a named page, automatically appending
// the current page as the `from` param so the destination's back button works.
_RENDERERS['nav_link'] = function(b) {
  var uid   = 'nvl' + Math.random().toString(36).substr(2, 6);
  var slug  = b.nav_slug || '';
  var label = b.label    || 'Continue →';
  var icon  = b.icon     || '';
  var style = b.style    || 'primary'; // primary | ghost | text
  var align = b.align    || 'left';

  var btnBase = 'display:inline-flex;align-items:center;gap:8px;padding:10px 22px;border-radius:10px;' +
    'font-size:0.82rem;font-weight:700;text-decoration:none;cursor:pointer;transition:all 0.15s;';
  var btnStyle = {
    primary: btnBase + 'background:#6366f1;color:#fff;border:none;',
    ghost:   btnBase + 'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);color:#94a3b8;',
    text:    btnBase + 'background:none;border:none;color:#6366f1;padding:0;'
  }[style] || btnBase;

  return (
    '<div style="text-align:' + _esc(align) + ';font-family:\'Inter\',system-ui,sans-serif;">' +
    '<a id="' + uid + '" href="#" style="' + btnStyle + '">' +
      (icon ? '<span>' + _esc(icon) + '</span>' : '') +
      '<span>' + _esc(label) + '</span>' +
    '</a>' +
    '<script>(function(){' +
      'var el=document.getElementById("' + uid + '");if(!el)return;' +
      'var slug="' + slug.replace(/"/g,'\\"') + '";' +
      'var nav=window._A2UI_NAV||{slug:"",from:"",url:""};' +
      'el.target="_top";' +
      'if(slug&&nav.url){' +
        // A target slug always resolves forward via nav.url + "?nav="+slug, regardless of
        // whether THIS page has its own nav.slug — see nav_bar's matching fix, same bug,
        // same date. history.back() must NOT be used — it navigates the sandbox iframe,
        // not the top window.
        'if(slug===nav.from&&nav.from){' +
          'el.href=nav.url+"?nav="+nav.from;' +
        '}else{' +
          'el.href=nav.url+"?nav="+slug+(nav.slug?"&from="+nav.slug:"");' +
        '}' +
      '}else if(!slug&&nav.from&&nav.url){' +
        'el.href=nav.url+"?nav="+nav.from;' +
      '}' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── theme_toggle ──────────────────────────────────────────────────────────────
// Floating button that toggles body.asw-dark-theme. Atoms like hub react via
// MutationObserver — no direct coupling needed.
// Schema: { dark_bg, position ('bottom-right'|'top-right'), label_dark,
//           label_light, initial ('light'|'dark') }
//
// `initial` (2026-08-03) exists because the button used to assume every page
// starts light. On a dark-by-default surface the first click computed
// dark=!false=true, re-adding a class that was already there — so the first
// press did visibly nothing and the label flipped the wrong way. It must be
// told what the page it is mounted on already is.
//
// `dark_bg: ""` means DO NOT TOUCH the background: when a theme owns --bg (a
// terminal-skinned surface, say), writing an inline body background overrides
// the palette with a colour from this atom's defaults and quietly wins.
_RENDERERS['theme_toggle'] = function(b) {
  var darkBg     = b.dark_bg !== undefined ? b.dark_bg : '#0f172a';
  var pos        = b.position   || 'bottom-right';
  var labelDark  = b.label_dark  || '🌙';
  var labelLight = b.label_light || '☀️';
  var uid = 'tt' + Math.random().toString(36).substr(2, 6);

  var posStyle = pos === 'top-right'
    ? 'top:64px;right:12px;'
    : 'bottom:72px;right:12px;';

  // The button's INITIAL paint has to agree with `initial` too — label and
  // chrome both. Rendering light chrome on a dark page and correcting it on
  // first click is the same bug as the state one, just visible for longer.
  var startDark = b.initial === 'dark';
  return (
    '<button id="' + uid + '" ' +
    'title="' + (startDark ? 'Light mode' : 'Dark mode') + '" ' +
    'style="position:fixed;' + posStyle + 'z-index:500;' +
    'padding:7px 12px;border-radius:10px;' +
    'border:1.5px solid ' + (startDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)') + ';' +
    'background:' + (startDark ? 'rgba(15,23,42,0.88)' : 'rgba(255,255,255,0.88)') + ';' +
    (startDark ? 'color:#e2e8f0;' : '') +
    'backdrop-filter:blur(8px);' +
    'cursor:pointer;font-size:0.88rem;' +
    'box-shadow:0 2px 8px rgba(0,0,0,' + (startDark ? '0.4' : '0.1') + ');' +
    'transition:all 0.2s;">' +
    _esc(startDark ? labelLight : labelDark) +
    '</button>' +
    '<script>(function(){' +
    'var btn=document.getElementById("' + uid + '");' +
    'var darkBg="' + darkBg + '";' +
    'var ld="' + _esc(labelDark) + '",ll="' + _esc(labelLight) + '";' +
    'var dark=' + (b.initial === 'dark' ? 'true' : 'false') + ';' +
    'btn.addEventListener("click",function(){' +
    'dark=!dark;' +
    'document.body.classList.toggle("asw-dark-theme",dark);' +
    'if(darkBg)document.body.style.background=dark?darkBg:"";' +
    'btn.textContent=dark?ll:ld;' +
    'btn.style.background=dark?"rgba(15,23,42,0.88)":"rgba(255,255,255,0.88)";' +
    'btn.style.borderColor=dark?"rgba(255,255,255,0.12)":"rgba(0,0,0,0.12)";' +
    'btn.style.color=dark?"#e2e8f0":"";' +
    'btn.style.boxShadow=dark?"0 2px 8px rgba(0,0,0,0.4)":"0 2px 8px rgba(0,0,0,0.1)";' +
    // OPT-IN persistence (2026-08-04): every repaint (any nav click on a
    // wired surface that navigates via paint_result) re-declares this atom
    // fresh with a hardcoded `initial` — so a manual toggle got silently
    // reset on the next click, every time, until Curtis called it "annoying"
    // and asked to enforce a saved preference instead. Same direct-engine-
    // call pattern the claim/resolve buttons already use elsewhere in this
    // file (bypassing the standard wire-prop system, which has no event
    // carrying "which theme it became" to hand a collect{} spec) — inert
    // unless a surface passes BOTH persist_to (a ValueStore id) and
    // persist_action (an action id); every other theme_toggle in the
    // catalog is completely unaffected.
    (b.persist_to && b.persist_action ?
      'if(window._a2uiEngine){try{' +
      'window._a2uiEngine.trigger(' + JSON.stringify(String(b.persist_to)) + ',"setValue",dark?"dark":"light");' +
      'var _pa=window._a2uiEngine.nodes[' + JSON.stringify(String(b.persist_action)) + '];' +
      'if(_pa&&_pa._run)_pa._run();' +
      '}catch(e){}}' : '') +
    '});' +
    '})();<\/script>'
  );
};

// Icon token -> inline SVG markup (Curtis's spec, 2026-08-04). Inline, not a
// web font: icon_feature_grid's Material Symbols was rejected the SAME day
// for exactly this reason — it loads from fonts.googleapis.com, an external
// CDN the MCP Apps bundle's "CSP-clean by design" principle (resourceDomains
// deliberately empty, see mcp-worker's mcpUiCsp()) is very likely to block,
// degrading to raw ligature text ("person", "search") instead of an icon.
// Inline SVG has no such dependency — it is just markup, exactly as safe as
// the bundle's own inline <script> tags. Extend this table as more tokens
// are needed; an unrecognised token falls back to literal text (e.g. an
// emoji a caller passes directly) rather than rendering nothing.
var _TOOL_TILE_ICONS = {
  user: '<circle cx="12" cy="8" r="3.5"></circle><path d="M5 20c0-4 3-6.5 7-6.5s7 2.5 7 6.5"></path>',
  book: '<path d="M4 5.5C6 4.5 9 4.5 12 6c3-1.5 6-1.5 8-.5v13c-2-1-5-1-8 .5-3-1.5-6-1.5-8-.5z"></path><path d="M12 6v13"></path>',
  folder: '<path d="M3 7h6l2 2h10v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"></path>',
  magnifier: '<circle cx="10" cy="10" r="6"></circle><path d="M20 20l-5-5"></path>',
  bolt: '<path d="M12 2 4 13h6l-1 9 9-13h-6z"></path>',
  globe: '<circle cx="12" cy="12" r="9"></circle><path d="M3 12h18"></path><path d="M12 3a13 15 0 0 1 0 18a13 15 0 0 1 0-18"></path>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>'
};
function _toolTileIcon(token) {
  var inner = _TOOL_TILE_ICONS[token];
  if (!inner) return _esc(token);
  return '<svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="#fff" ' +
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" ' +
    'aria-hidden="true">' + inner + '</svg>';
}

// ── tool_tile ────────────────────────────────────────────────────────────────
// Large icon+title tile, the WHOLE tile clickable — for a small set of primary
// choices (an app/tool selector), not a data-dense card. Designed 2026-08-04
// for the Workspace's home screen: bigger visual weight than a plain button,
// pairs with the flat `row_open` grid wrapper (see tools.js) for a 3-column
// layout — the wired dialect's layout array has no nested-children atoms
// (unlike the blocks dialect), so there is no separate "tile_grid" container
// atom; each tile is its own flat layout element with its own wire.onClick,
// exactly like ripple_button, which is also why this renders a <button> as
// its own top-level element — the generic onClick binder finds it via
// domEl.querySelector('button').
_RENDERERS['tool_tile'] = function(b) {
  var uid   = 'tl' + Math.random().toString(36).substr(2, 6);
  var icon  = _toolTileIcon(b.icon || '');
  var label = _esc(b.label || '');
  var count = (b.count !== undefined && b.count !== null && b.count !== '')
    ? ' <span style="opacity:.75;font-weight:600;">(' + _esc(String(b.count)) + ')</span>' : '';
  var variant = b.variant === 'violet_magenta' ? 'violet_magenta' : 'indigo';
  var gradient = variant === 'violet_magenta'
    ? 'linear-gradient(135deg,#7c3aed,#c026d3)'
    : 'linear-gradient(135deg,#6d6af7,#4f46e5)';
  var glowShadow = variant === 'violet_magenta'
    ? '0 8px 20px -8px rgba(192,38,212,.4)'
    : '0 8px 20px -6px rgba(79,70,229,.45)';
  var highlightA = variant === 'violet_magenta' ? '.2' : '.25';
  var badgeHtml = b.badge
    ? '<span style="position:absolute;top:14px;right:14px;background:rgba(255,255,255,.25);' +
      'color:#fff;font-size:9px;font-weight:800;letter-spacing:.06em;padding:3px 8px;' +
      'border-radius:999px;">' + _esc(b.badge) + '</span>'
    : '';
  return (
    '<button id="' + uid + '" style="position:relative;display:flex;flex-direction:column;' +
    'gap:14px;align-items:flex-start;text-align:left;width:100%;' +
    'background:' + gradient + ';border-radius:22px;padding:22px;' +
    'box-shadow:' + glowShadow + ',inset 0 1px 0 rgba(255,255,255,' + highlightA + ');' +
    'border:none;cursor:pointer;font-family:inherit;transition:transform 0.15s;" ' +
    'onmouseover="this.style.transform=\'translateY(-2px)\'" ' +
    'onmouseout="this.style.transform=\'\'">' +
    badgeHtml +
    '<span style="width:38px;height:38px;border-radius:50%;background:rgba(255,255,255,.22);' +
    'display:flex;align-items:center;justify-content:center;font-size:19px;line-height:1;' +
    'flex-shrink:0;">' + icon + '</span>' +
    '<span style="font-size:16px;font-weight:600;color:#fff;">' + label + count + '</span>' +
    '</button>'
  );
};

// ── lens_grid ────────────────────────────────────────────────────────────────
// 2-column (configurable) grid of selectable cards — a config question with a
// small, fixed set of options, each worth a one-line explanation (unlike a
// dropdown, which hides the explanation until opened). Designed 2026-08-04
// for the Workspace's Read & Analyse screen (lens: explain/apply/challenge/
// situate). Same direct-engine pattern as theme_toggle's persist_to/
// persist_action (see that atom's header comment for why): the standard
// wire-prop system has no event carrying "which card was clicked", so this
// atom updates its own selected-state styling AND calls the engine directly,
// rather than going through wire.onClick.
_RENDERERS['lens_grid'] = function(b) {
  var uid     = 'lg' + Math.random().toString(36).substr(2, 6);
  var options = b.options || [];
  var target  = b.target || '';
  var cols    = parseInt(b.columns || 2, 10);
  var gap     = parseInt(b.gap || 10, 10);
  var selected = b.selected || (options[0] && options[0].value) || '';

  var cards = options.map(function(o) {
    var isSel = o.value === selected;
    return '<button type="button" data-lg-value="' + _esc(o.value) + '" style="' +
      'text-align:left;cursor:pointer;font-family:inherit;padding:14px;border-radius:12px;' +
      'border:1.5px solid ' + (isSel ? '#4f46e5' : '#e2e5ea') + ';background:#fff;">' +
      '<div style="font-size:14px;font-weight:700;color:#111827;">' + _esc(o.label || '') + '</div>' +
      (o.caption ? '<div style="font-size:12px;color:#6b7280;margin-top:2px;">' + _esc(o.caption) + '</div>' : '') +
      '</button>';
  }).join('');

  return (
    '<div id="' + uid + '" style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:' + gap + 'px;">' +
    cards +
    '</div>' +
    '<script>(function(){' +
    'var wrap=document.getElementById("' + uid + '");' +
    'var btns=wrap.querySelectorAll("button");' +
    'for(var i=0;i<btns.length;i++){' +
    '(function(btn){' +
    'btn.addEventListener("click",function(){' +
    'for(var j=0;j<btns.length;j++)btns[j].style.borderColor="#e2e5ea";' +
    'btn.style.borderColor="#4f46e5";' +
    (target ?
      'if(window._a2uiEngine){try{' +
      'window._a2uiEngine.trigger(' + JSON.stringify(String(target)) + ',"setValue",btn.getAttribute("data-lg-value"));' +
      '}catch(e){}}' : '') +
    '});' +
    '})(btns[i]);' +
    '}' +
    '})();<\/script>'
  );
};

// ── domain_picker ────────────────────────────────────────────────────────────
// One filled pill ("use my saved default") beside a free-text field — for a
// config question that almost always wants the same answer (whatever is
// already on the reader's profile) but sometimes needs a one-off override.
// Designed 2026-08-04 for the Workspace's Read & Analyse screen. Same
// direct-engine pattern as lens_grid/theme_toggle: the pill click resets the
// target ValueStore to default_domains; typing sets it to whatever was
// typed. Both write the SAME state atom, so whichever happened last wins —
// there is no separate "which mode is active" flag to keep in sync.
_RENDERERS['domain_picker'] = function(b) {
  var uid     = 'dp' + Math.random().toString(36).substr(2, 6);
  var target  = b.target || '';
  var pillLabel   = (b.default_option && b.default_option.label) || 'From my profile';
  var placeholder = (b.free_entry && b.free_entry.placeholder) || 'Or type a domain…';
  var defaultVal  = b.default_domains || '';

  return (
    '<div id="' + uid + '" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">' +
    '<button type="button" style="padding:7px 16px;border-radius:999px;border:1.5px solid #4f46e5;' +
    'background:#4f46e5;color:#fff;font-size:13px;font-weight:600;cursor:pointer;' +
    'font-family:inherit;white-space:nowrap;flex-shrink:0;">' + _esc(pillLabel) + '</button>' +
    '<input type="text" placeholder="' + _esc(placeholder) + '" style="flex:1 1 160px;min-width:160px;' +
    'padding:8px 12px;border-radius:8px;border:1.5px solid #d9dcf5;font-size:14px;font-family:inherit;">' +
    '</div>' +
    '<script>(function(){' +
    'var wrap=document.getElementById("' + uid + '");' +
    'var pill=wrap.querySelector("button");' +
    'var inp=wrap.querySelector("input");' +
    'pill.addEventListener("click",function(){' +
    'inp.value="";' +
    (target ?
      'if(window._a2uiEngine){try{' +
      'window._a2uiEngine.trigger(' + JSON.stringify(String(target)) + ',"setValue",' + JSON.stringify(String(defaultVal)) + ');' +
      '}catch(e){}}' : '') +
    '});' +
    'inp.addEventListener("input",function(){' +
    (target ?
      'if(window._a2uiEngine){try{' +
      'window._a2uiEngine.trigger(' + JSON.stringify(String(target)) + ',"setValue",inp.value);' +
      '}catch(e){}}' : '') +
    '});' +
    '})();<\/script>'
  );
};

// ── tab_group ────────────────────────────────────────────────────────────────
// Pill tabs that switch which ONE of several sibling atoms is visible — e.g.
// "how will you give me the source: a URL, a file, or pasted text" — rather
// than showing all three input areas stacked and unlabelled. Designed
// 2026-08-04 for the Workspace's Read & Analyse screen. Same direct-engine
// pattern as lens_grid/domain_picker/theme_toggle, PLUS direct DOM
// manipulation of sibling wrapper divs — `panels` maps a tab value to
// another layout element's id, and this atom toggles that element's
// #a2ui-<id> wrapper (the standard wrapper _a2uiRenderWiredLayout gives
// every id'd layout element) directly. Safe regardless of layout ORDER: the
// whole layout's HTML is inserted in one shot before any atom's own
// <script> runs, so every wrapper div already exists by the time this one
// looks for it, whichever position in the array either atom is at.
_RENDERERS['tab_group'] = function(b) {
  var uid     = 'tg' + Math.random().toString(36).substr(2, 6);
  var options = b.options || [];
  var target  = b.target || '';
  var panels  = b.panels || {};
  var preSel  = options.filter(function(o) { return o.selected; })[0];
  var selected = (preSel && preSel.value) || (options[0] && options[0].value) || '';

  var pills = options.map(function(o) {
    var isSel = o.value === selected;
    return '<button type="button" data-tg-value="' + _esc(o.value) + '" style="' +
      'padding:7px 16px;border-radius:999px;cursor:pointer;font-family:inherit;' +
      'font-size:13px;font-weight:600;border:1.5px solid ' + (isSel ? '#4f46e5' : '#d9dcf5') + ';' +
      'background:' + (isSel ? '#4f46e5' : '#fff') + ';color:' + (isSel ? '#fff' : '#374151') + ';">' +
      _esc(o.label || o.value) + '</button>';
  }).join('');

  function panelJs(valueExpr) {
    return Object.keys(panels).map(function(val) {
      return 'ez(' + JSON.stringify(String(panels[val])) + ',' + valueExpr + '===' + JSON.stringify(String(val)) + ');';
    }).join('');
  }

  return (
    '<div id="' + uid + '" style="display:inline-flex;gap:8px;flex-wrap:wrap;">' + pills + '</div>' +
    '<script>(function(){' +
    'function ez(id,show){var el=document.getElementById("a2ui-"+id);if(el)el.style.display=show?"":"none";}' +
    panelJs(JSON.stringify(String(selected))) +
    'var wrap=document.getElementById("' + uid + '");' +
    'var btns=wrap.querySelectorAll("button");' +
    'for(var i=0;i<btns.length;i++){' +
    '(function(btn){' +
    'btn.addEventListener("click",function(){' +
    'var v=btn.getAttribute("data-tg-value");' +
    'for(var j=0;j<btns.length;j++){btns[j].style.background="#fff";btns[j].style.color="#374151";btns[j].style.borderColor="#d9dcf5";}' +
    'btn.style.background="#4f46e5";btn.style.color="#fff";btn.style.borderColor="#4f46e5";' +
    panelJs('v') +
    (target ? 'if(window._a2uiEngine){try{window._a2uiEngine.trigger(' + JSON.stringify(String(target)) + ',"setValue",v);}catch(e){}}' : '') +
    '});' +
    '})(btns[i]);' +
    '}' +
    '})();<\/script>'
  );
};

// ── quiet_link ───────────────────────────────────────────────────────────────
// A secondary action with no button chrome — centered, small, muted text.
// Designed 2026-08-04 for a screen's ONE primary action to stay visually
// singular (a full-chrome ripple_button beside it would compete). Still a
// real <button> underneath (not an <a>, no href) so the SAME generic
// onClick wire binder every other clickable atom uses finds it via
// domEl.querySelector('button') — no special-cased wiring needed.
_RENDERERS['quiet_link'] = function(b) {
  var uid = 'ql' + Math.random().toString(36).substr(2, 6);
  return (
    '<div style="text-align:center;">' +
    '<button id="' + uid + '" type="button" style="background:none;border:none;' +
    'color:#6b7280;font-size:13px;font-family:inherit;cursor:pointer;text-decoration:underline;' +
    'text-underline-offset:2px;padding:4px;">' + _esc(b.text || '') + '</button>' +
    '</div>'
  );
};

// ── breadcrumb ────────────────────────────────────────────────────────────────
// Trail of page links — reads _A2UI_NAV at runtime to highlight the current page.
// Pass an ordered array of {slug, label, icon?} — the current page is highlighted.
_RENDERERS['breadcrumb'] = function(b) {
  var uid   = 'brd' + Math.random().toString(36).substr(2, 6);
  var items = b.items || [];

  var crumbsJson = JSON.stringify(items.map(function(c) {
    return { slug: c.slug || '', label: c.label || '', icon: c.icon || '' };
  }));

  return (
    '<div id="' + uid + '" style="font-family:\'Inter\',system-ui,sans-serif;display:flex;flex-wrap:wrap;align-items:center;gap:4px;"></div>' +
    '<script>(function(){' +
      'var items=' + crumbsJson + ';' +
      'var nav=window._A2UI_NAV||{slug:"",url:""};' +
      'var el=document.getElementById("' + uid + '");if(!el)return;' +
      'items.forEach(function(c,i){' +
        'var isCur=c.slug&&c.slug===nav.slug;' +
        'var href=c.slug&&nav.url?nav.url+"?nav="+c.slug:"#";' +
        'if(i>0){var sep=document.createElement("span");sep.textContent="›";sep.style.cssText="color:#334155;font-size:0.72rem;";el.appendChild(sep);}' +
        'var a=document.createElement("a");' +
        'a.href=isCur?"#":href;' +
        'a.target="_top";' +
        'a.style.cssText="font-size:0.72rem;font-weight:"+(isCur?"700":"500")+";color:"+(isCur?"#f1f5f9":"#64748b")+";text-decoration:none;padding:3px 6px;border-radius:5px;"+(isCur?"background:rgba(255,255,255,0.05);":"");' +
        'a.textContent=(c.icon?c.icon+" ":"")+c.label;' +
        'if(!isCur){a.onmouseover=function(){this.style.color="#e2e8f0";};a.onmouseout=function(){this.style.color="#64748b";};}' +
        'el.appendChild(a);' +
      '});' +
    '})();<\/script>'
  );
};
