// === Meta Demo Kit — atoms for demoing the renderer itself ===
// All cross-surface compatible: GAS, Meet Stage, Web
// Depends on _RENDERERS and _esc() defined in atom.gs

// surface_unlocked — game-style "NEW SURFACE UNLOCKED" achievement notification
_RENDERERS['surface_unlocked'] = function(b) {
  var uid     = Math.random().toString(36).substr(2, 6);
  var icon    = b.icon    || '⚡';
  var surface = b.surface || 'New Surface';
  var sub     = b.sub     || 'NEW SURFACE UNLOCKED';
  var accent  = b.accent  || '#6366f1';
  return '<style>'
    + '@keyframes su-in-' + uid + '{0%{opacity:0;transform:translateY(-18px) scale(0.96);}100%{opacity:1;transform:none;}}'
    + '@keyframes su-glow-' + uid + '{0%,100%{box-shadow:0 0 0 0 ' + accent + '55;}60%{box-shadow:0 0 0 10px ' + accent + '00;}}'
    + '#su-' + uid + '{animation:su-in-' + uid + ' 0.5s cubic-bezier(0.34,1.56,0.64,1) both,su-glow-' + uid + ' 1.8s 0.5s ease-out 3;}'
    + '</style>'
    + '<div id="su-' + uid + '" style="margin:1.5rem 0;padding:22px 26px;background:' + accent + '12;border:2px solid ' + accent + ';border-radius:14px;display:flex;align-items:center;gap:22px;">'
    + '<div style="font-size:3rem;line-height:1;flex-shrink:0">' + icon + '</div>'
    + '<div>'
    + '<div style="font-size:0.6rem;font-weight:900;letter-spacing:0.22em;text-transform:uppercase;color:' + accent + ';margin-bottom:5px">' + _esc(sub) + '</div>'
    + '<div style="font-size:1.4rem;font-weight:800;color:var(--text);line-height:1.25">' + _esc(surface) + '</div>'
    + '</div>'
    + '</div>';
};

// schema_reveal — decodes the current page's ?p= URL parameter and displays the schema that built this page
_RENDERERS['schema_reveal'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var title  = b.title || 'This page was built from this schema';
  var accent = b.accent || '#6366f1';
  return '<style>'
    + '#srev-' + uid + '{background:#0f172a;border-radius:12px;overflow:hidden;margin:1rem 0;}'
    + '#srev-hd-' + uid + '{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#1e293b;}'
    + '#srev-hd-' + uid + ' span{font-size:0.75rem;font-weight:600;color:#94a3b8;font-family:monospace;}'
    + '#srev-copy-' + uid + '{padding:4px 12px;background:' + accent + ';color:#fff;border:none;border-radius:5px;font-size:0.75rem;font-weight:600;cursor:pointer;font-family:inherit;}'
    + '#srev-body-' + uid + '{padding:16px;overflow-x:auto;max-height:420px;overflow-y:auto;}'
    + '#srev-pre-' + uid + '{margin:0;font-family:monospace;font-size:0.78rem;line-height:1.65;color:#e2e8f0;white-space:pre;}'
    + '#srev-none-' + uid + '{padding:16px;font-size:0.85rem;color:#64748b;font-family:monospace;}'
    + '</style>'
    + '<div style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">' + _esc(title) + '</div>'
    + '<div id="srev-' + uid + '">'
    + '<div id="srev-hd-' + uid + '"><span>schema.json</span><button id="srev-copy-' + uid + '">Copy</button></div>'
    + '<div id="srev-body-' + uid + '"><pre id="srev-pre-' + uid + '"></pre><div id="srev-none-' + uid + '" style="display:none;">Schema not available.</div></div>'
    + '</div>'
    + '<script>(function(){'
    + 'var pre=document.getElementById("srev-pre-' + uid + '");'
    + 'var none=document.getElementById("srev-none-' + uid + '");'
    + 'var copyBtn=document.getElementById("srev-copy-' + uid + '");'
    + 'try{'
    + '  var schema=null;'
    + '  if(window.__A2UI_SCHEMA__){schema=window.__A2UI_SCHEMA__;}'
    + '  else{'
    + '    var m=window.location.search.match(/[?&]p=([^&]*)/);'
    + '    if(m){var b64=decodeURIComponent(m[1]);var bin=atob(b64);var bytes=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);schema=JSON.parse(new TextDecoder().decode(bytes));}'
    + '  }'
    + '  if(!schema){none.style.display="block";pre.style.display="none";return;}'
    + '  pre.textContent=JSON.stringify(schema,null,2);'
    + '  copyBtn.onclick=function(){navigator.clipboard.writeText(pre.textContent).then(function(){copyBtn.textContent="Copied!";setTimeout(function(){copyBtn.textContent="Copy";},1500);});};'
    + '}catch(e){none.textContent="Could not decode schema: "+e.message;none.style.display="block";pre.style.display="none";}'
    + '})();<\/script>';
};

// url_anatomy — visually dissects the shareable URL into its parts
_RENDERERS['url_anatomy'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var accent = b.accent || '#6366f1';
  return '<style>'
    + '#ua-' + uid + '{background:var(--surface);border:2px solid var(--border);border-radius:12px;padding:20px;margin:1rem 0;overflow:hidden;}'
    + '#ua-url-' + uid + '{font-family:monospace;font-size:0.78rem;word-break:break-all;color:var(--text);line-height:1.8;margin-bottom:16px;}'
    + '.ua-part-' + uid + '{display:inline;padding:2px 5px;border-radius:3px;}'
    + '.ua-label-row-' + uid + '{display:flex;gap:16px;flex-wrap:wrap;margin-top:4px;}'
    + '.ua-legend-' + uid + '{display:flex;align-items:center;gap:6px;font-size:0.72rem;color:var(--muted);}'
    + '.ua-dot-' + uid + '{width:10px;height:10px;border-radius:2px;flex-shrink:0;}'
    + '</style>'
    + '<div id="ua-' + uid + '">'
    + '<div style="font-size:0.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">How the URL works</div>'
    + '<div id="ua-url-' + uid + '">Loading current URL…</div>'
    + '<div class="ua-label-row-' + uid + '">'
    + '<div class="ua-legend-' + uid + '"><div class="ua-dot-' + uid + '" style="background:#bfdbfe;"></div>GAS endpoint (always running)</div>'
    + '<div class="ua-legend-' + uid + '"><div class="ua-dot-' + uid + '" style="background:#bbf7d0;"></div>?p= parameter</div>'
    + '<div class="ua-legend-' + uid + '"><div class="ua-dot-' + uid + '" style="background:' + accent + '44;"></div>base64 schema (the content)</div>'
    + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var el=document.getElementById("ua-url-' + uid + '");'
    + 'var url=window.location.href;'
    + 'var pi=url.indexOf("?p=");'
    + 'if(pi>-1){'
    + '  var base=url.substring(0,pi);'
    + '  var payload=url.substring(pi+3);'
    + '  el.innerHTML="<span class=\'ua-part-' + uid + '\' style=\'background:#bfdbfe;color:#1e3a5f;\'>"+base+"</span>"'
    + '    +"<span class=\'ua-part-' + uid + '\' style=\'background:#bbf7d0;color:#14532d;\'>?p=</span>"'
    + '    +"<span class=\'ua-part-' + uid + '\' style=\'background:' + accent + '22;color:' + accent + ';\'>"+payload.substring(0,60)+(payload.length>60?"…":"")+"</span>";'
    + '}else{el.textContent=url;}'
    + '})();<\/script>';
};

// schema_qr — generates a QR code for the current page URL via Google Charts API
_RENDERERS['schema_qr'] = function(b) {
  var uid   = Math.random().toString(36).substr(2, 6);
  var size  = parseInt(b.size || 220, 10);
  var label = b.label || 'Scan to open this page on any device';
  var url   = b.url || '';
  var sub   = b.sub || '';
  if (url) {
    var src = 'https://chart.googleapis.com/chart?chs=' + size + 'x' + size + '&cht=qr&chl=' + encodeURIComponent(url) + '&choe=UTF-8&chld=M|2';
    return '<div style="text-align:center;padding:24px 16px;">'
      + '<img src="' + src + '" width="' + size + '" height="' + size + '" style="border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">'
      + '<div style="font-size:0.88rem;font-weight:600;color:var(--text);margin-top:12px;">' + _esc(label) + '</div>'
      + (sub ? '<div style="font-size:0.78rem;color:var(--muted);margin-top:4px;">' + _esc(sub) + '</div>' : '')
      + '</div>';
  }
  return '<div id="sqr-' + uid + '" style="text-align:center;padding:24px 16px;">'
    + '<img id="sqr-img-' + uid + '" width="' + size + '" height="' + size + '" style="border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">'
    + '<div style="font-size:0.88rem;font-weight:600;color:var(--text);margin-top:12px;">' + _esc(label) + '</div>'
    + (sub ? '<div style="font-size:0.78rem;color:var(--muted);margin-top:4px;">' + _esc(sub) + '</div>' : '')
    + '</div>'
    + '<script>(function(){'
    + 'var u=encodeURIComponent(window.location.href);'
    + 'document.getElementById("sqr-img-' + uid + '").src="https://chart.googleapis.com/chart?chs=' + size + 'x' + size + '&cht=qr&chl="+u+"&choe=UTF-8&chld=M|2";'
    + '})();<\/script>';
};

// take_away_card — bold single-insight card, designed to be screenshot-able
_RENDERERS['take_away_card'] = function(b) {
  var headline   = b.headline || b.text || b.quote || b.insight || '';
  var sub        = b.sub || b.author || b.source || '';
  var accent     = b.accent || '#6366f1';
  var size       = b.size || '1.9rem';
  var gradient   = b.gradient ? b.gradient : null;
  var textColor  = b.text_color || (gradient ? '#fff' : 'var(--text)');
  var bg         = gradient
    ? 'linear-gradient(135deg,' + gradient[0] + ',' + gradient[1] + ')'
    : 'linear-gradient(135deg,' + accent + '0f,' + accent + '1a)';
  var border     = gradient ? 'none' : '2px solid ' + accent + '33';
  return '<div style="background:' + bg + ';border:' + border + ';border-radius:16px;padding:36px 32px;margin:1.5rem 0;text-align:center;">'
    + '<div style="font-size:2rem;margin-bottom:16px;opacity:0.5;color:' + (gradient ? 'rgba(255,255,255,0.7)' : accent) + ';">❝</div>'
    + '<div style="font-size:' + _esc(size) + ';font-weight:800;color:' + textColor + ';line-height:1.25;letter-spacing:-0.02em;">' + _esc(headline) + '</div>'
    + (sub ? '<div style="font-size:0.82rem;font-weight:600;color:' + (gradient ? 'rgba(255,255,255,0.7)' : accent) + ';margin-top:16px;text-transform:uppercase;letter-spacing:0.1em;">' + _esc(sub) + '</div>' : '')
    + '</div>';
};

// next_step_strip — horizontal step guide with optional links
_RENDERERS['next_step_strip'] = function(b) {
  var steps  = b.steps || [];
  var accent = b.accent || '#6366f1';
  var html = '<div style="display:flex;gap:0;margin:1.5rem 0;border-radius:12px;overflow:hidden;border:1px solid var(--border);">';
  steps.forEach(function(s, i) {
    var isLast = i === steps.length - 1;
    html += '<div style="flex:1;padding:20px 18px;background:var(--surface);' + (!isLast ? 'border-right:1px solid var(--border);' : '') + '">'
      + '<div style="font-size:1.4rem;font-weight:900;color:' + accent + ';margin-bottom:6px;">' + _esc(String(s.number || (i + 1))) + '</div>'
      + '<div style="font-size:0.9rem;font-weight:700;color:var(--text);margin-bottom:4px;">' + _esc(s.label || '') + '</div>'
      + '<div style="font-size:0.8rem;color:var(--muted);">' + _esc(s.detail || s.action || '') + '</div>'
      + (s.url ? '<a href="' + _esc(s.url) + '" target="_top" style="display:inline-block;margin-top:10px;font-size:0.78rem;font-weight:600;color:' + accent + ';text-decoration:none;">Open →</a>' : '')
      + '</div>';
  });
  return html + '</div>';
};

// copy_prompt — displays a copyable text block (for sharing Gemini prompts)
_RENDERERS['copy_prompt'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var label  = b.label || 'Copy this prompt';
  var prompt = b.prompt || b.text || b.content || '';
  var accent = b.accent || '#6366f1';
  return '<style>'
    + '#cp-wrap-' + uid + '{background:#0f172a;border-radius:12px;overflow:hidden;margin:1rem 0;}'
    + '#cp-hd-' + uid + '{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;background:#1e293b;}'
    + '#cp-lbl-' + uid + '{font-size:0.75rem;font-weight:600;color:#94a3b8;}'
    + '#cp-btn-' + uid + '{padding:4px 12px;background:' + accent + ';color:#fff;border:none;border-radius:5px;font-size:0.75rem;font-weight:600;cursor:pointer;font-family:inherit;}'
    + '#cp-body-' + uid + '{padding:16px;font-family:monospace;font-size:0.82rem;color:#e2e8f0;line-height:1.7;white-space:pre-wrap;max-height:300px;overflow-y:auto;}'
    + '</style>'
    + '<div id="cp-wrap-' + uid + '">'
    + '<div id="cp-hd-' + uid + '"><span id="cp-lbl-' + uid + '">' + _esc(label) + '</span><button id="cp-btn-' + uid + '">Copy</button></div>'
    + '<div id="cp-body-' + uid + '" data-text="' + _esc(prompt) + '">' + _esc(prompt) + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var btn=document.getElementById("cp-btn-' + uid + '");'
    + 'var text=document.getElementById("cp-body-' + uid + '").getAttribute("data-text");'
    + 'btn.onclick=function(){navigator.clipboard.writeText(text).then(function(){btn.textContent="Copied!";setTimeout(function(){btn.textContent="Copy";},1500);});};'
    + '})();<\/script>';
};

// atom_anatomy — shows a rendered output alongside its schema snippet
_RENDERERS['atom_anatomy'] = function(b) {
  var label  = b.label || 'atom';
  var schema = b.schema || {};
  var accent = b.accent || '#6366f1';
  var schemaStr = JSON.stringify(schema, null, 2);
  var rendered  = '';
  try { rendered = renderAtoms([schema]); } catch(e) { rendered = '<em style="color:var(--muted);">Could not render preview</em>'; }
  return '<div style="border:1px solid var(--border);border-radius:12px;overflow:hidden;margin:1rem 0;">'
    + '<div style="padding:8px 16px;background:var(--surface2);font-size:0.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;border-bottom:1px solid var(--border);">' + _esc(label) + '</div>'
    + '<div style="display:flex;gap:0;">'
    + '<div style="flex:1;padding:20px;border-right:1px solid var(--border);min-width:0;">'
    + '<div style="font-size:0.68rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Rendered</div>'
    + rendered
    + '</div>'
    + '<div style="flex:1;padding:20px;background:#0f172a;min-width:0;">'
    + '<div style="font-size:0.68rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Schema</div>'
    + '<pre style="margin:0;font-family:monospace;font-size:0.72rem;color:#e2e8f0;white-space:pre-wrap;line-height:1.6;">' + _esc(schemaStr) + '</pre>'
    + '</div>'
    + '</div></div>';
};

// renderer_stats — static stats grid about the renderer/page
_RENDERERS['renderer_stats'] = function(b) {
  var stats  = b.stats || [];
  var accent = b.accent || '#6366f1';
  var sub    = b.sub || '';
  var html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1px;background:var(--border);border-radius:12px;overflow:hidden;margin:1rem 0;">';
  stats.forEach(function(s) {
    html += '<div style="padding:20px 16px;background:var(--surface);text-align:center;">'
      + '<div style="font-size:1.7rem;font-weight:900;color:' + accent + ';line-height:1;">' + _esc(String(s.value || '')) + '</div>'
      + '<div style="font-size:0.75rem;color:var(--muted);margin-top:5px;font-weight:500;">' + _esc(s.label || '') + '</div>'
      + '</div>';
  });
  html += '</div>';
  if (sub) html += '<div style="font-size:0.75rem;color:var(--muted);text-align:center;margin-top:-8px;">' + _esc(sub) + '</div>';
  return html;
};

// prompt_to_schema — three panel stepped reveal: prompt → schema → output
_RENDERERS['prompt_to_schema'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var prompt = b.prompt || 'Describe a page…';
  var schema = b.schema || '{ "blocks": [] }';
  var output = b.output || 'The rendered page';
  var accent = b.accent || '#6366f1';
  var labels = b.labels || ['Natural language', 'Generated schema', 'Rendered page'];
  var schemaStr = typeof schema === 'object' ? JSON.stringify(schema, null, 2) : String(schema);

  return '<style>'
    + '#pts-' + uid + '{display:flex;gap:0;border-radius:12px;overflow:hidden;border:1px solid var(--border);margin:1rem 0;}'
    + '.pts-panel-' + uid + '{flex:1;display:flex;flex-direction:column;}'
    + '.pts-hd-' + uid + '{padding:10px 14px;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;border-bottom:1px solid var(--border);}'
    + '.pts-body-' + uid + '{flex:1;padding:16px;font-size:0.82rem;line-height:1.65;}'
    + '.pts-arrow-' + uid + '{display:flex;align-items:center;padding:0 8px;color:var(--muted);font-size:1.4rem;background:var(--surface2);}'
    + '</style>'
    + '<div id="pts-' + uid + '">'
    + '<div class="pts-panel-' + uid + '">'
    + '<div class="pts-hd-' + uid + '" style="background:#1e3a5f;color:#7dd3fc;">' + _esc(labels[0]) + '</div>'
    + '<div class="pts-body-' + uid + '" style="background:#0c2340;color:#bae6fd;font-style:italic;">"' + _esc(prompt) + '"</div>'
    + '</div>'
    + '<div class="pts-arrow-' + uid + '">→</div>'
    + '<div class="pts-panel-' + uid + '">'
    + '<div class="pts-hd-' + uid + '" style="background:#0f172a;color:#475569;">{ } &nbsp;' + _esc(labels[1]) + '</div>'
    + '<div class="pts-body-' + uid + '" style="background:#0f172a;"><pre style="margin:0;font-family:monospace;font-size:0.7rem;color:#94a3b8;white-space:pre-wrap;">' + _esc(schemaStr.substring(0, 320)) + (schemaStr.length > 320 ? '\n…' : '') + '</pre></div>'
    + '</div>'
    + '<div class="pts-arrow-' + uid + '">→</div>'
    + '<div class="pts-panel-' + uid + '">'
    + '<div class="pts-hd-' + uid + '" style="background:#14291e;color:#4ade80;">' + _esc(labels[2]) + '</div>'
    + '<div class="pts-body-' + uid + '" style="background:#0d1f16;color:#86efac;">' + _esc(output) + '</div>'
    + '</div>'
    + '</div>';
};

// before_after_stack — animated comparison: old stack items cross out, new way reveals
_RENDERERS['before_after_stack'] = function(b) {
  var uid          = Math.random().toString(36).substr(2, 6);
  var beforeLabel  = b.before_label || 'Traditional stack';
  var beforeItems  = b.items || b.before_items || ['Hosting','Framework','Deploy pipeline','Database','Auth','CDN','DevOps'];
  var afterLabel   = b.after_label  || 'This approach';
  var afterText    = b.result || b.after_text || 'A URL';
  var accent       = b.accent       || '#6366f1';
  var delay        = parseFloat(b.delay_ms || b.delay || 400) / (b.delay_ms ? 1 : 0.001);
  if (b.delay_ms) delay = parseInt(b.delay_ms, 10);
  else delay = parseFloat(b.delay || 0.4) * 1000;

  var leftItems = beforeItems.map(function(item, i) {
    return '<div id="bas-item-' + uid + '-' + i + '" style="display:flex;align-items:center;gap:8px;padding:7px 0;font-size:0.9rem;color:var(--text);transition:all 0.4s;">'
      + '<span style="color:var(--muted);font-size:0.75rem;">▸</span>' + _esc(item)
      + '</div>';
  }).join('');

  return '<style>'
    + '@keyframes bas-slide-' + uid + '{from{opacity:0;transform:translateX(30px);}to{opacity:1;transform:none;}}'
    + '#bas-after-' + uid + '{opacity:0;}'
    + '</style>'
    + '<div style="display:flex;gap:16px;margin:1.5rem 0;">'
    + '<div style="flex:1;padding:24px;background:#2d0f0f;border:2px solid #7f1d1d;border-radius:12px;">'
    + '<div style="font-size:0.72rem;font-weight:700;color:#f87171;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;">' + _esc(beforeLabel) + '</div>'
    + '<div id="bas-before-' + uid + '">' + leftItems + '</div>'
    + '</div>'
    + '<div style="display:flex;align-items:center;font-size:1.5rem;color:var(--muted);padding:0 4px;">→</div>'
    + '<div id="bas-after-' + uid + '" style="flex:1;padding:24px;background:' + accent + '0d;border:2px solid ' + accent + '44;border-radius:12px;display:flex;align-items:center;justify-content:center;">'
    + '<div style="text-align:center;">'
    + '<div style="font-size:0.72rem;font-weight:700;color:' + accent + ';text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;">' + _esc(afterLabel) + '</div>'
    + '<div style="font-size:2.2rem;font-weight:900;color:' + accent + ';">' + _esc(afterText) + '</div>'
    + '</div>'
    + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var items=document.getElementById("bas-before-' + uid + '").children;'
    + 'var after=document.getElementById("bas-after-' + uid + '");'
    + 'var total=items.length;var i=0;'
    + 'function strike(){'
    + '  if(i<total){'
    + '    items[i].style.textDecoration="line-through";items[i].style.opacity="0.35";'
    + '    i++;setTimeout(strike,' + delay + ');'
    + '  } else {'
    + '    after.style.opacity="1";after.style.animation="bas-slide-' + uid + ' 0.6s ease";'
    + '  }'
    + '}'
    + 'if("IntersectionObserver" in window){'
    + '  new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){setTimeout(strike,400);ob.disconnect();}},{threshold:0.3}).observe(after);'
    + '}else{setTimeout(strike,800);}'
    + '})();<\/script>';
};

// live_vote — Sheet-backed live voting with real-time results bar chart
_RENDERERS['live_vote'] = function(b) {
  var uid      = Math.random().toString(36).substr(2, 6);
  var question = b.question || 'What do you think?';
  var options  = b.options  || ['Yes', 'No'];
  var sheetUrl = b.sheet_url || '';
  var writeUrl = b.write_url || '';
  var poll     = parseInt(b.poll_interval || b.poll || 5000, 10);
  var accent   = b.accent || '#6366f1';
  var optsJson = JSON.stringify(options);

  var optBtns = options.map(function(o) {
    return '<button class="lv-opt-' + uid + '" data-opt="' + _esc(o) + '">' + _esc(o) + '</button>';
  }).join('');

  return '<style>'
    + '#lv-' + uid + '{max-width:620px;margin:1.5rem auto;padding:24px;background:var(--surface);border-radius:14px;box-shadow:0 2px 20px rgba(0,0,0,0.12);}'
    + '#lv-q-' + uid + '{font-size:1.05rem;font-weight:700;color:var(--text);margin-bottom:18px;line-height:1.5;}'
    + '#lv-btns-' + uid + '{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;}'
    + '.lv-opt-' + uid + '{flex:1;padding:12px 8px;background:var(--surface2);border:2px solid var(--border);border-radius:10px;font-size:0.9rem;font-weight:600;cursor:pointer;transition:all 0.15s;font-family:inherit;color:var(--text);}'
    + '.lv-opt-' + uid + ':hover{border-color:' + accent + ';background:' + accent + '0d;}'
    + '.lv-voted-' + uid + '{border-color:' + accent + '!important;background:' + accent + '!important;color:#fff!important;}'
    + '#lv-results-' + uid + '{display:none;}'
    + '.lv-bar-row-' + uid + '{display:flex;align-items:center;gap:10px;margin-bottom:10px;}'
    + '.lv-bar-label-' + uid + '{font-size:0.82rem;font-weight:600;color:var(--text);min-width:60px;}'
    + '.lv-bar-track-' + uid + '{flex:1;height:26px;background:var(--surface2);border-radius:6px;overflow:hidden;}'
    + '.lv-bar-fill-' + uid + '{height:100%;background:' + accent + ';border-radius:6px;transition:width 0.6s cubic-bezier(0.4,0,0.2,1);display:flex;align-items:center;padding-left:8px;}'
    + '.lv-bar-pct-' + uid + '{font-size:0.72rem;font-weight:700;color:#fff;}'
    + '#lv-total-' + uid + '{font-size:0.72rem;color:var(--muted);text-align:right;margin-top:6px;}'
    + '</style>'
    + '<div id="lv-' + uid + '">'
    + '<div id="lv-q-' + uid + '">' + _esc(question) + '</div>'
    + '<div id="lv-btns-' + uid + '">' + optBtns + '</div>'
    + '<div id="lv-results-' + uid + '">'
    + options.map(function(o, i) {
        return '<div class="lv-bar-row-' + uid + '">'
          + '<div class="lv-bar-label-' + uid + '">' + _esc(o) + '</div>'
          + '<div class="lv-bar-track-' + uid + '"><div id="lv-fill-' + uid + '-' + i + '" class="lv-bar-fill-' + uid + '" style="width:0%"><span class="lv-bar-pct-' + uid + '" id="lv-pct-' + uid + '-' + i + '">0%</span></div></div>'
          + '</div>';
      }).join('')
    + '<div id="lv-total-' + uid + '">0 votes</div>'
    + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var opts=' + optsJson + ';'
    + 'var sheetUrl=' + JSON.stringify(sheetUrl) + ';'
    + 'var writeUrl=' + JSON.stringify(writeUrl) + ';'
    + 'var poll=' + poll + ';'
    + 'var voted=false;'
    + 'var counts={};opts.forEach(function(o){counts[o]=0;});'
    + 'var btns=document.querySelectorAll(".lv-opt-' + uid + '");'
    + 'var resultsEl=document.getElementById("lv-results-' + uid + '");'

    + 'function updateBars(){'
    + '  var total=opts.reduce(function(s,o){return s+(counts[o]||0);},0);'
    + '  opts.forEach(function(o,i){'
    + '    var pct=total?Math.round((counts[o]||0)/total*100):0;'
    + '    document.getElementById("lv-fill-' + uid + '-"+i).style.width=pct+"%";'
    + '    document.getElementById("lv-pct-' + uid + '-"+i).textContent=pct+"% ("+(counts[o]||0)+")";'
    + '  });'
    + '  document.getElementById("lv-total-' + uid + '").textContent=total+" vote"+(total!==1?"s":"");'
    + '}'

    + 'function parseCSV(csv){'
    + '  var lines=csv.trim().split("\\n").slice(1);'
    + '  var map={};'
    + '  lines.forEach(function(l){var c=l.split(",");var o=(c[0]||"").trim().replace(/^"|"$/g,"");var n=parseInt(c[1]||"1",10);if(o)map[o]=(map[o]||0)+n;});'
    + '  return map;'
    + '}'

    + 'function fetchResults(){'
    + '  fetch(sheetUrl).then(function(r){return r.text();}).then(function(t){'
    + '    var m=parseCSV(t);opts.forEach(function(o){counts[o]=m[o]||0;});updateBars();'
    + '  }).catch(function(){});'
    + '}'

    + 'btns.forEach(function(btn){'
    + '  btn.addEventListener("click",function(){'
    + '    if(voted)return;voted=true;'
    + '    var opt=btn.getAttribute("data-opt");'
    + '    counts[opt]=(counts[opt]||0)+1;'
    + '    btn.classList.add("lv-voted-' + uid + '");'
    + '    btns.forEach(function(b){b.disabled=true;});'
    + '    resultsEl.style.display="block";updateBars();'
    + '    if(writeUrl)fetch(writeUrl+"?option="+encodeURIComponent(opt),{method:"GET",mode:"no-cors"}).catch(function(){});'
    + '  });'
    + '});'

    + 'if(sheetUrl){fetchResults();setInterval(fetchResults,poll);}'
    + '})();<\/script>';
};

// reaction_shower — emoji reaction buttons, reactions rain down the screen, Sheet-backed totals
_RENDERERS['reaction_shower'] = function(b) {
  var uid       = Math.random().toString(36).substr(2, 6);
  var reactions = b.reactions || ['🔥', '💡', '🤯', '👏'];
  var writeUrl  = b.write_url || '';
  var sheetUrl  = b.sheet_url || '';
  var poll      = parseInt(b.poll_interval || b.poll || 4000, 10);
  var accent    = b.accent || '#6366f1';
  var countsJson = JSON.stringify(reactions.reduce(function(m, r) { m[r] = 0; return m; }, {}));

  return '<style>'
    + '#rs-' + uid + '{position:relative;overflow:hidden;}'
    + '#rs-btns-' + uid + '{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;padding:20px;}'
    + '.rs-btn-' + uid + '{font-size:2rem;padding:10px 18px;background:var(--surface);border:2px solid var(--border);border-radius:12px;cursor:pointer;transition:transform 0.15s,border-color 0.15s;line-height:1;}'
    + '.rs-btn-' + uid + ':hover{transform:scale(1.18);border-color:' + accent + ';}'
    + '.rs-btn-' + uid + ':active{transform:scale(0.95);}'
    + '#rs-counts-' + uid + '{display:flex;gap:16px;justify-content:center;padding:0 20px 16px;flex-wrap:wrap;}'
    + '.rs-count-' + uid + '{font-size:0.8rem;color:var(--muted);}'
    + '@keyframes rs-fall-' + uid + '{0%{transform:translateY(-30px) rotate(0deg);opacity:1;}100%{transform:translateY(100vh) rotate(720deg);opacity:0;}}'
    + '.rs-particle-' + uid + '{position:fixed;pointer-events:none;font-size:2rem;z-index:9999;animation:rs-fall-' + uid + ' 2.2s ease-in forwards;}'
    + '</style>'
    + '<div id="rs-' + uid + '">'
    + '<div id="rs-btns-' + uid + '">'
    + reactions.map(function(r) {
        return '<button class="rs-btn-' + uid + '" data-r="' + _esc(r) + '">' + r + '</button>';
      }).join('')
    + '</div>'
    + '<div id="rs-counts-' + uid + '">'
    + reactions.map(function(r, i) {
        return '<span class="rs-count-' + uid + '">' + r + ' <span id="rs-c-' + uid + '-' + i + '">0</span></span>';
      }).join('')
    + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var reactions=' + JSON.stringify(reactions) + ';'
    + 'var counts=' + countsJson + ';'
    + 'var writeUrl=' + JSON.stringify(writeUrl) + ';'
    + 'var sheetUrl=' + JSON.stringify(sheetUrl) + ';'
    + 'var poll=' + poll + ';'

    + 'function shower(emoji){'
    + '  for(var i=0;i<6+Math.floor(Math.random()*6);i++)(function(){'
    + '    var el=document.createElement("div");'
    + '    el.className="rs-particle-' + uid + '";'
    + '    el.textContent=emoji;'
    + '    el.style.left=(10+Math.random()*80)+"%";'
    + '    el.style.top="-40px";'
    + '    el.style.animationDelay=(Math.random()*0.5)+"s";'
    + '    document.body.appendChild(el);'
    + '    setTimeout(function(){el.remove();},3000);'
    + '  })();'
    + '}'

    + 'function updateCounts(){'
    + '  reactions.forEach(function(r,i){'
    + '    var el=document.getElementById("rs-c-' + uid + '-"+i);'
    + '    if(el)el.textContent=counts[r]||0;'
    + '  });'
    + '}'

    + 'document.querySelectorAll(".rs-btn-' + uid + '").forEach(function(btn){'
    + '  btn.addEventListener("click",function(){'
    + '    var r=btn.getAttribute("data-r");'
    + '    counts[r]=(counts[r]||0)+1;'
    + '    shower(r);updateCounts();'
    + '    if(writeUrl)fetch(writeUrl+"?reaction="+encodeURIComponent(r),{method:"GET",mode:"no-cors"}).catch(function(){});'
    + '  });'
    + '});'

    + 'function fetchCounts(){'
    + '  fetch(sheetUrl).then(function(r){return r.text();}).then(function(t){'
    + '    var lines=t.trim().split("\\n").slice(1);'
    + '    lines.forEach(function(l){var c=l.split(",");var k=(c[0]||"").trim().replace(/^"|"$/g,"");var v=parseInt(c[1]||"0",10);if(k)counts[k]=v;});'
    + '    updateCounts();'
    + '  }).catch(function(){});'
    + '}'

    + 'if(sheetUrl){fetchCounts();setInterval(fetchCounts,poll);}'
    + 'updateCounts();'
    + '})();<\/script>';
};

// raise_hand — single button Sheet counter
_RENDERERS['raise_hand'] = function(b) {
  var uid      = Math.random().toString(36).substr(2, 6);
  var question = b.question || 'Raise your hand';
  var label    = b.label || '✋ Raise hand';
  var writeUrl = b.write_url || '';
  var sheetUrl = b.sheet_url || '';
  var poll     = parseInt(b.poll_interval || b.poll || 4000, 10);
  var accent   = b.accent || '#6366f1';

  return '<div style="text-align:center;padding:28px 20px;margin:1rem 0;">'
    + '<div style="font-size:1rem;font-weight:700;color:var(--text);margin-bottom:20px;">' + _esc(question) + '</div>'
    + '<button id="rh-btn-' + uid + '" style="font-size:1.5rem;padding:16px 32px;background:var(--surface);border:2px solid var(--border);border-radius:14px;cursor:pointer;transition:all 0.15s;font-family:inherit;color:var(--text);display:inline-block;">' + _esc(label) + '</button>'
    + '<div style="margin-top:16px;font-size:2rem;font-weight:900;color:' + accent + ';" id="rh-count-' + uid + '">0</div>'
    + '<div style="font-size:0.78rem;color:var(--muted);">hands raised</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var btn=document.getElementById("rh-btn-' + uid + '");'
    + 'var countEl=document.getElementById("rh-count-' + uid + '");'
    + 'var writeUrl=' + JSON.stringify(writeUrl) + ';'
    + 'var sheetUrl=' + JSON.stringify(sheetUrl) + ';'
    + 'var poll=' + poll + ';'
    + 'var raised=false;var count=0;'
    + 'btn.addEventListener("click",function(){'
    + '  if(raised)return;raised=true;count++;'
    + '  btn.style.borderColor="' + accent + '";btn.style.background="' + accent + '0d";'
    + '  countEl.textContent=count;'
    + '  if(writeUrl)fetch(writeUrl+"?hand=1",{method:"GET",mode:"no-cors"}).catch(function(){});'
    + '});'
    + 'function fetchCount(){'
    + '  fetch(sheetUrl).then(function(r){return r.text();}).then(function(t){'
    + '    var lines=t.trim().split("\\n").slice(1);var total=0;'
    + '    lines.forEach(function(l){var c=l.split(",");total+=parseInt(c[1]||"1",10)||1;});'
    + '    count=total;countEl.textContent=total;'
    + '  }).catch(function(){});'
    + '}'
    + 'if(sheetUrl){fetchCount();setInterval(fetchCount,poll);}'
    + '})();<\/script>';
};

// surface_map — visual diagram of the A2UI surfaces
_RENDERERS['surface_map'] = function(b) {
  var accent  = b.accent  || '#6366f1';
  var title   = b.title   || 'One schema. Three surfaces.';
  var surfaces = b.surfaces || [
    { name: 'GAS Web App',       icon: '⚡', desc: 'Live web app · GAS runtime · URL = content', color: '#6366f1' },
    { name: 'Meet Stage',        icon: '📺', desc: 'Full-screen · Live demos · Audience view',   color: '#8b5cf6' },
    { name: 'Google Sites HTML', icon: '📄', desc: 'Blog / docs · SEO · Static publish',         color: '#3b82f6' },
    { name: 'Google Chat',       icon: '💬', desc: 'Cards · Bots · Workspace native',            color: '#06b6d4' }
  ];

  // Google Workspace product SVGs — colors from official gstatic icons
  // Apps Script: 4-color (blue/red/yellow/green), Meet: yellow #FBBC04,
  // Sites: purple #4758B5, Chat: green #34A853
  var _gas  = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" width="28" height="28"><mask id="mgas"><rect width="28" height="28" rx="6" fill="white"/></mask><g mask="url(#mgas)"><rect width="14" height="14" fill="#4285F4"/><rect x="14" width="14" height="14" fill="#EA4335"/><rect y="14" width="14" height="14" fill="#FBBC04"/><rect x="14" y="14" width="14" height="14" fill="#34A853"/></g><path d="M10 9L6 14l4 5M18 9l4 5-4 5" stroke="white" stroke-width="2.2" stroke-linecap="round" fill="none"/></svg>';
  var _meet = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" width="28" height="28"><rect width="28" height="28" rx="6" fill="#FBBC04"/><rect x="4" y="9" width="14" height="10" rx="2" fill="white"/><path d="M18 12.5l6-3.5v10l-6-3.5z" fill="white"/></svg>';
  var _sites= '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" width="28" height="28"><rect width="28" height="28" rx="6" fill="#4758B5"/><rect x="6" y="6" width="7" height="7" rx="1" fill="white"/><rect x="15" y="6" width="7" height="7" rx="1" fill="white"/><rect x="6" y="15" width="7" height="7" rx="1" fill="white"/><rect x="15" y="15" width="7" height="7" rx="1" fill="white"/></svg>';
  var _chat = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" width="28" height="28"><rect width="28" height="28" rx="6" fill="#34A853"/><path d="M5 9a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-8l-4 3v-3H7a2 2 0 01-2-2z" fill="white"/></svg>';
  var _SVG = {
    'GAS Web App': _gas, 'Google Apps Script': _gas,
    'Meet Stage':  _meet, 'Google Meet': _meet,
    'Google Sites HTML': _sites, 'Google Sites': _sites, 'Web Article': _sites,
    'Google Chat': _chat
  };

  var html = '<div style="margin:1.5rem 0;">'
    + '<div style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.12em;text-align:center;margin-bottom:16px;">' + _esc(title) + '</div>'
    + '<div style="display:flex;align-items:center;justify-content:center;gap:0;flex-wrap:wrap;">'
    + '<div style="padding:14px 20px;background:#0f172a;border-radius:10px;text-align:center;margin-right:8px;">'
    + '<div style="font-size:0.65rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Schema</div>'
    + '<div style="font-family:monospace;font-size:0.72rem;color:#94a3b8;">{ blocks: […] }</div>'
    + '</div>'
    + '<div style="font-size:1.2rem;color:var(--muted);margin-right:8px;">→</div>';

  surfaces.forEach(function(s, i) {
    var iconHtml = _SVG[s.name]
      ? '<div style="margin-bottom:6px;display:flex;justify-content:center;">' + _SVG[s.name] + '</div>'
      : '<div style="font-size:1.6rem;margin-bottom:4px;">' + s.icon + '</div>';
    html += '<div style="flex:1;min-width:120px;padding:16px 14px;background:' + s.color + '0d;border:2px solid ' + s.color + '33;border-radius:10px;text-align:center;' + (i < surfaces.length - 1 ? 'margin-right:8px;' : '') + '">'
      + iconHtml
      + '<div style="font-size:0.8rem;font-weight:700;color:' + s.color + ';margin-bottom:4px;">' + _esc(s.name) + '</div>'
      + '<div style="font-size:0.7rem;color:var(--muted);line-height:1.5;">' + _esc(s.desc) + '</div>'
      + '</div>';
  });

  return html + '</div></div>';
};

// speed_counter — stopwatch that freezes when the page finishes loading
_RENDERERS['speed_counter'] = function(b) {
  var uid    = Math.random().toString(36).substr(2, 6);
  var label  = b.label  || 'Page loaded in';
  var sub    = b.sub    || '';
  var accent = b.accent || '#6366f1';
  return '<div style="text-align:center;padding:28px 20px;margin:1rem 0;">'
    + '<div style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">' + _esc(label) + '</div>'
    + '<div id="sc-' + uid + '" style="font-size:3.5rem;font-weight:900;color:' + accent + ';font-variant-numeric:tabular-nums;letter-spacing:-0.02em;line-height:1;">0.0s</div>'
    + (sub ? '<div style="font-size:0.82rem;color:var(--muted);margin-top:8px;">' + _esc(sub) + '</div>' : '')
    + '</div>'
    + '<script>(function(){'
    + 'var el=document.getElementById("sc-' + uid + '");'
    + 'var t0=window.performance&&performance.timing?performance.timing.navigationStart:Date.now();'
    + 'function fmt(ms){var s=ms/1000;return s<60?s.toFixed(2)+"s":Math.floor(s/60)+"m "+Math.round(s%60)+"s";}'
    + 'var iv=setInterval(function(){el.textContent=fmt(Date.now()-t0);},50);'
    + 'window.addEventListener("load",function(){'
    + '  clearInterval(iv);'
    + '  el.textContent=fmt(Date.now()-t0);'
    + '});'
    + '})();<\/script>';
};

// live_edit — embedded mini schema editor with live rendered preview
_RENDERERS['live_edit'] = function(b) {
  var uid         = Math.random().toString(36).substr(2, 6);
  var placeholder = b.placeholder || '{ "type": "heading", "level": 1, "text": "Hello" }';
  var accent      = b.accent || '#6366f1';
  var rendererUrl = b.renderer_url || '';

  return '<style>'
    + '#le-' + uid + '{border:1px solid var(--border);border-radius:12px;overflow:hidden;margin:1rem 0;}'
    + '#le-hd-' + uid + '{padding:10px 16px;background:#1e293b;display:flex;align-items:center;justify-content:space-between;}'
    + '#le-hd-' + uid + ' span{font-size:0.72rem;font-weight:700;color:#94a3b8;}'
    + '#le-ta-' + uid + '{width:100%;height:130px;background:#0f172a;border:none;padding:14px;color:#e2e8f0;font-family:monospace;font-size:0.8rem;resize:none;outline:none;border-bottom:1px solid #1e293b;}'
    + '#le-preview-' + uid + '{min-height:80px;padding:20px;background:var(--bg);}'
    + '#le-err-' + uid + '{display:none;padding:8px 16px;background:#2d0f0f;font-size:0.78rem;color:#f87171;font-family:monospace;}'
    + '#le-run-' + uid + '{padding:5px 14px;background:' + accent + ';color:#fff;border:none;border-radius:5px;font-size:0.75rem;font-weight:600;cursor:pointer;font-family:inherit;}'
    + '</style>'
    + '<div id="le-' + uid + '">'
    + '<div id="le-hd-' + uid + '"><span>live editor — type a single atom JSON block</span><button id="le-run-' + uid + '">Render ▶</button></div>'
    + '<textarea id="le-ta-' + uid + '" spellcheck="false" placeholder=\'' + _esc(placeholder) + '\'></textarea>'
    + '<div id="le-err-' + uid + '"></div>'
    + '<div id="le-preview-' + uid + '"><span style="color:var(--muted);font-size:0.82rem;">Preview will appear here…</span></div>'
    + '</div>'
    + '<script>(function(){'
    + 'var ta=document.getElementById("le-ta-' + uid + '");'
    + 'var preview=document.getElementById("le-preview-' + uid + '");'
    + 'var err=document.getElementById("le-err-' + uid + '");'
    + 'var btn=document.getElementById("le-run-' + uid + '");'
    + 'var rendererUrl=' + JSON.stringify(rendererUrl) + ';'
    + 'function run(){'
    + '  try{'
    + '    var obj=JSON.parse(ta.value.trim()||"{}");'
    + '    err.style.display="none";'
    + '    if(!rendererUrl){preview.innerHTML="<em style=\'color:#9ca3af;font-size:0.82rem;\'>Set renderer_url to enable live preview</em>";return;}'
    + '    var schema={blocks:[obj]};'
    + '    var enc=btoa(unescape(encodeURIComponent(JSON.stringify(schema))));'
    + '    preview.innerHTML="<iframe src=\'"+rendererUrl+"?p="+encodeURIComponent(enc)+"\' style=\'width:100%;min-height:120px;border:none;\' frameborder=\'0\'></iframe>";'
    + '  }catch(e){err.textContent=e.message;err.style.display="block";}'
    + '}'
    + 'btn.addEventListener("click",run);'
    + 'ta.addEventListener("keydown",function(e){if(e.key==="Enter"&&(e.ctrlKey||e.metaKey))run();});'
    + '})();<\/script>';
};
