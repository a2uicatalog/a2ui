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
        'var _useBack=!!(l.slug&&(!nav.slug||(nav.from&&l.slug===nav.from)));' +
        'if(_useBack){href=nav.from?nav.url+"?nav="+nav.from:nav.url;}' +
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
        // On a ?p= page (no named slug) we cannot resolve nav_slug targets.
        // Navigate top window: to from-slug if known, else exec root.
        // history.back() must NOT be used — it navigates the sandbox iframe, not the top window.
        'if(!nav.slug||(slug===nav.from&&nav.from)){' +
          'el.href=nav.from?nav.url+"?nav="+nav.from:nav.url;' +
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
// Schema: { dark_bg, position ('bottom-right'|'top-right'), label_dark, label_light }
_RENDERERS['theme_toggle'] = function(b) {
  var darkBg     = b.dark_bg    || '#0f172a';
  var pos        = b.position   || 'bottom-right';
  var labelDark  = b.label_dark  || '🌙';
  var labelLight = b.label_light || '☀️';
  var uid = 'tt' + Math.random().toString(36).substr(2, 6);

  var posStyle = pos === 'top-right'
    ? 'top:64px;right:12px;'
    : 'bottom:72px;right:12px;';

  return (
    '<button id="' + uid + '" ' +
    'title="Mode sombre" ' +
    'style="position:fixed;' + posStyle + 'z-index:500;' +
    'padding:7px 12px;border-radius:10px;border:1.5px solid rgba(0,0,0,0.12);' +
    'background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);' +
    'cursor:pointer;font-size:0.88rem;box-shadow:0 2px 8px rgba(0,0,0,0.1);' +
    'transition:all 0.2s;">' +
    _esc(labelDark) +
    '</button>' +
    '<script>(function(){' +
    'var btn=document.getElementById("' + uid + '");' +
    'var darkBg="' + darkBg + '";' +
    'var ld="' + _esc(labelDark) + '",ll="' + _esc(labelLight) + '";' +
    'var dark=false;' +
    'btn.addEventListener("click",function(){' +
    'dark=!dark;' +
    'document.body.classList.toggle("asw-dark-theme",dark);' +
    'document.body.style.background=dark?darkBg:"";' +
    'btn.textContent=dark?ll:ld;' +
    'btn.style.background=dark?"rgba(15,23,42,0.88)":"rgba(255,255,255,0.88)";' +
    'btn.style.borderColor=dark?"rgba(255,255,255,0.12)":"rgba(0,0,0,0.12)";' +
    'btn.style.color=dark?"#e2e8f0":"";' +
    'btn.style.boxShadow=dark?"0 2px 8px rgba(0,0,0,0.4)":"0 2px 8px rgba(0,0,0,0.1)";' +
    '});' +
    '})();<\/script>'
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
