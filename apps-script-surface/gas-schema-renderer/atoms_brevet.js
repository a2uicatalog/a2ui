// atoms_brevet.gs — Specialized atoms for the French Brevet (DNB) 2026 curriculum.
// Surfaces: G W
//
// Atoms: domain_brief, brevet_timeline, text_analysis, brevet_automatismes

// ── domain_brief ──────────────────────────────────────────────────────────────
// Domain knowledge manifest — "what is this" card rendered from a structured schema.
// Generic enough for any knowledge domain (Brevet, TOGAF, etc.).
// Mirrors what an OKF manifest would declare: title, description, key_facts, areas, context.
// Schema: { title, badge?, accent?, description, key_facts [{icon?,text}|string],
//           areas [{label, color?, detail?}], areas_label?, context? }
_RENDERERS['domain_brief'] = function(b) {
  var title       = b.title       || '';
  var badge       = b.badge       || '';
  var description = b.description || '';
  var key_facts   = b.key_facts   || [];
  var areas       = b.areas       || [];
  var areas_label = b.areas_label || 'Périmètre';
  var context     = b.context     || '';
  var accent      = b.accent      || '#6366f1';
  var uid         = 'dbr' + Math.random().toString(36).substr(2, 8);

  // Key facts pills
  var factsHtml = '';
  if (key_facts.length) {
    factsHtml = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:1.2rem 0 1rem;">';
    for (var i = 0; i < key_facts.length; i++) {
      var f = typeof key_facts[i] === 'string' ? { text: key_facts[i] } : key_facts[i];
      factsHtml +=
        '<div style="display:flex;align-items:center;gap:5px;' +
          'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);' +
          'border-radius:20px;padding:5px 12px;">' +
          (f.icon ? '<span style="font-size:0.82rem;">' + _esc(f.icon) + '</span>' : '') +
          '<span style="font-size:0.75rem;color:#cbd5e1;font-weight:600;">' + _esc(f.text || '') + '</span>' +
        '</div>';
    }
    factsHtml += '</div>';
  }

  // Areas grid
  var areasHtml = '';
  if (areas.length) {
    areasHtml =
      '<div style="font-size:0.58rem;font-weight:700;letter-spacing:0.16em;' +
        'text-transform:uppercase;color:#475569;margin:1.1rem 0 0.6rem;">' + _esc(areas_label) + '</div>' +
      '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:9px;">';
    for (var j = 0; j < areas.length; j++) {
      var a = areas[j];
      var ac = a.color || accent;
      areasHtml +=
        '<div style="background:rgba(15,23,42,0.8);' +
          'border:1px solid ' + _esc(ac) + '28;border-left:3px solid ' + _esc(ac) + ';' +
          'border-radius:8px;padding:10px 12px;">' +
          '<div style="font-size:0.78rem;font-weight:700;color:' + _esc(ac) + ';margin-bottom:3px;">' + _esc(a.label || '') + '</div>' +
          (a.detail ? '<div style="font-size:0.69rem;color:#64748b;line-height:1.5;">' + _esc(a.detail) + '</div>' : '') +
        '</div>';
    }
    areasHtml += '</div>';
  }

  var image_url = b.image_url || '';

  return (
    '<div id="' + uid + '" style="font-family:\'Inter\',system-ui,sans-serif;margin:' + (image_url ? '0' : '1.5rem') + ' 0;">' +
    '<div style="background:rgba(15,23,42,0.97);border:1px solid rgba(255,255,255,0.07);' +
      (image_url ? '' : 'border-top:3px solid ' + _esc(accent) + ';') +
      'border-radius:' + (image_url ? '0 0 14px 14px' : '14px') + ';overflow:hidden;">' +
      (image_url
        ? '<div style="width:100%;height:220px;overflow:hidden;position:relative;">' +
            '<img src="' + _esc(image_url) + '" ' +
              'style="width:100%;height:100%;object-fit:cover;object-position:center 35%;display:block;" ' +
              'onerror="this.parentElement.style.display=\'none\'" />' +
            '<div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(15,23,42,0.0) 0%,rgba(15,23,42,0.3) 50%,rgba(15,23,42,0.97) 82%);"></div>' +
            '<div style="position:absolute;top:10px;right:12px;background:rgba(0,0,0,0.55);' +
              'border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:3px 9px;' +
              'font-size:0.6rem;font-weight:700;color:rgba(255,255,255,0.7);letter-spacing:0.05em;">' +
              '⚡ Imagen 3' +
            '</div>' +
          '</div>'
        : '') +
    '<div style="padding:1.75rem 1.75rem 1.5rem;">' +
      (badge
        ? '<div style="display:inline-block;background:' + _esc(accent) + '1a;' +
            'border:1px solid ' + _esc(accent) + '44;border-radius:20px;padding:3px 12px;' +
            'font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;' +
            'color:' + _esc(accent) + ';margin-bottom:1.5rem;">' + _esc(badge) + '</div>'
        : '') +
      '<div style="font-size:1.55rem;font-weight:800;color:#f1f5f9;line-height:1.2;margin-bottom:0.8rem;">' +
        _esc(title) +
      '</div>' +
      (description
        ? '<div style="font-size:0.9rem;color:#94a3b8;line-height:1.75;max-width:640px;">' +
            _esc(description).replace(/\n/g, '<br>') +
          '</div>'
        : '') +
      factsHtml +
      areasHtml +
      (context
        ? '<div style="margin-top:1.25rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,0.06);' +
            'font-size:0.72rem;color:#334155;">' + _esc(context) + '</div>'
        : '') +
    '</div>' +  // close padding div
    '</div>' +  // close card
    '</div>'
  );
};

// ── brevet_timeline ───────────────────────────────────────────────────────────
// Clickable chronological timeline — click an event to expand its Brevet impact.
// Schema: events [{date, title, desc}], accent (hex), title (optional label)
_RENDERERS['brevet_timeline'] = function(b) {
  var events = b.events || [];
  var accent = b.accent  || '#3b82f6';
  var label  = b.title   || '';
  var uid    = 'btl' + Math.random().toString(36).substr(2, 8);
  if (!events.length) return '';

  var evHtml = '';
  for (var i = 0; i < events.length; i++) {
    var ev = events[i];
    evHtml +=
      '<div class="' + uid + 'ev" style="position:relative;margin-bottom:1.25rem;padding-left:62px;">' +
        '<div style="position:absolute;left:0;top:6px;min-width:54px;max-width:54px;' +
          'padding:3px 4px;background:' + _esc(accent) + ';color:#fff;' +
          'font-size:0.58rem;font-weight:800;text-align:center;border-radius:6px;' +
          'letter-spacing:0.01em;line-height:1.4;z-index:2;">' +
          _esc(ev.date || '') +
        '</div>' +
        '<div class="' + uid + 'pn" style="background:rgba(15,23,42,0.97);' +
          'border:1px solid rgba(255,255,255,0.07);padding:0.85rem 1rem;' +
          'border-radius:12px;cursor:pointer;transition:border-color 0.2s;" ' +
          'onmouseover="this.style.borderColor=\'' + _esc(accent) + '44\'" ' +
          'onmouseout="this.style.borderColor=\'rgba(255,255,255,0.07)\'">' +
          '<div style="font-weight:700;color:#f1f5f9;font-size:0.92rem;line-height:1.4;">' +
            _esc(ev.title || '') +
          '</div>' +
          '<div class="' + uid + 'dd" style="max-height:0;overflow:hidden;opacity:0;margin-top:0;' +
            'color:#94a3b8;font-size:0.85rem;line-height:1.7;' +
            'transition:max-height 0.4s ease,opacity 0.3s ease,margin-top 0.3s ease;">' +
            _esc(ev.desc || '').replace(/\n/g, '<br>') +
          '</div>' +
          '<div style="font-size:0.6rem;color:#1e293b;margin-top:0.35rem;letter-spacing:0.07em;">▸ analyser l\'impact au Brevet</div>' +
        '</div>' +
      '</div>';
  }

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;margin:1.5rem 0;">' +
      (label ? '<div style="font-size:0.58rem;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;color:#475569;margin-bottom:1rem;">' + _esc(label) + '</div>' : '') +
      '<div id="' + uid + '" style="position:relative;padding:0.5rem 0;">' +
        '<div style="position:absolute;top:0;bottom:0;left:26px;width:2px;' +
          'background:linear-gradient(to bottom,' + _esc(accent) + '70,transparent);' +
          'border-radius:2px;z-index:1;"></div>' +
        evHtml +
      '</div>' +
    '</div>' +
    '<script>(function(){' +
      'document.querySelectorAll("#' + uid + ' .' + uid + 'pn").forEach(function(pn){' +
        'pn.addEventListener("click",function(){' +
          'var dd=pn.querySelector(".' + uid + 'dd");if(!dd)return;' +
          'var open=parseFloat(dd.style.maxHeight)>0;' +
          'dd.style.maxHeight=open?"":(dd.scrollHeight+"px");' +
          'dd.style.opacity=open?"0":"1";' +
          'dd.style.marginTop=open?"0":"0.65rem";' +
        '});' +
      '});' +
    '})();<\/script>'
  );
};

// ── text_analysis ─────────────────────────────────────────────────────────────
// Annotated document analysis — click underlined terms to reveal Brevet-method breakdown.
// Schema: passage (string), source (attribution label), highlights [{text, analysis}]
_RENDERERS['text_analysis'] = function(b) {
  var passage    = b.passage    || '';
  var highlights = b.highlights || [];
  var source     = b.source     || '';
  var uid        = 'txa' + Math.random().toString(36).substr(2, 8);

  // Escape the passage, then wrap each highlight phrase in a clickable span
  var passageHtml = _esc(passage).replace(/\n/g, '<br>');
  for (var i = 0; i < highlights.length; i++) {
    var hl = highlights[i];
    var escapedPhrase = _esc(hl.text || '');
    if (!escapedPhrase) continue;
    passageHtml = passageHtml.replace(
      escapedPhrase,
      '<span class="' + uid + 'hl" data-idx="' + i + '" ' +
        'style="background:rgba(217,119,6,0.18);border-bottom:2px solid #d97706;' +
        'cursor:pointer;padding:0 2px;border-radius:2px;transition:background 0.15s;">' +
        escapedPhrase + '</span>'
    );
  }

  // Store each analysis note in a hidden div to avoid JSON encoding issues
  var noteDivs = '';
  for (var j = 0; j < highlights.length; j++) {
    noteDivs += '<div id="' + uid + 'n' + j + '" style="display:none;">' + (highlights[j].analysis || '') + '</div>';
  }

  return (
    '<div id="' + uid + '" style="font-family:\'Inter\',system-ui,sans-serif;margin:1.5rem 0;">' +
      noteDivs +
      // Document passage
      '<div style="background:rgba(15,23,42,0.97);border:1px solid rgba(255,255,255,0.07);' +
        'border-left:3px solid #d97706;border-radius:12px;padding:1.4rem 1.5rem;margin-bottom:0.9rem;">' +
        (source ? '<div style="font-size:0.58rem;font-weight:700;letter-spacing:0.16em;' +
          'text-transform:uppercase;color:#d97706;margin-bottom:0.75rem;">' + _esc(source) + '</div>' : '') +
        '<div style="font-family:Georgia,\'Times New Roman\',serif;font-size:1.05rem;' +
          'line-height:1.9;color:#e2e8f0;font-style:italic;">' +
          passageHtml +
        '</div>' +
        '<div style="font-size:0.62rem;color:#1e293b;margin-top:0.8rem;letter-spacing:0.08em;">' +
          '↑ cliquer sur un terme souligné pour l\'analyser' +
        '</div>' +
      '</div>' +
      // Analysis panel
      '<div id="' + uid + 'box" style="background:rgba(15,23,42,0.97);' +
        'border:1px solid rgba(217,119,6,0.18);border-radius:10px;padding:1rem 1.2rem;' +
        'min-height:72px;transition:border-color 0.25s;">' +
        '<div style="font-size:0.58rem;font-weight:700;letter-spacing:0.16em;' +
          'text-transform:uppercase;color:#d97706;margin-bottom:0.5rem;">ANALYSE — Méthode Brevet</div>' +
        '<div id="' + uid + 'txt" style="font-size:0.88rem;color:#475569;line-height:1.65;' +
          'transition:opacity 0.18s;">' +
          'Cliquez sur un terme souligné pour afficher les clés de décryptage pour l\'examen.' +
        '</div>' +
      '</div>' +
    '</div>' +
    '<script>(function(){' +
      'var hlEls=document.querySelectorAll("#' + uid + ' .' + uid + 'hl");' +
      'var txt=document.getElementById("' + uid + 'txt");' +
      'var box=document.getElementById("' + uid + 'box");' +
      'hlEls.forEach(function(el){' +
        'el.addEventListener("mouseover",function(){' +
          'if(el.getAttribute("data-active")!=="1")el.style.background="rgba(217,119,6,0.3)";' +
        '});' +
        'el.addEventListener("mouseout",function(){' +
          'if(el.getAttribute("data-active")!=="1")el.style.background="rgba(217,119,6,0.18)";' +
        '});' +
        'el.addEventListener("click",function(){' +
          'var idx=parseInt(el.getAttribute("data-idx"),10);' +
          'var note=document.getElementById("' + uid + 'n"+idx);' +
          'if(!note)return;' +
          'hlEls.forEach(function(s){s.style.background="rgba(217,119,6,0.18)";s.removeAttribute("data-active");});' +
          'el.style.background="rgba(217,119,6,0.42)";el.setAttribute("data-active","1");' +
          'txt.style.opacity="0";' +
          'setTimeout(function(){' +
            'txt.innerHTML=note.innerHTML;' +
            'txt.style.color="#cbd5e1";' +
            'txt.style.opacity="1";' +
          '},130);' +
          'box.style.borderColor="rgba(217,119,6,0.45)";' +
        '});' +
      '});' +
    '})();<\/script>'
  );
};

// ── brevet_automatismes ───────────────────────────────────────────────────────
// Timed no-calculator drill — matches the DNB 2026 Part 1 format (20 min, 6 pts).
// Schema: questions [{question, answer}], duration (seconds, default 1200)
_RENDERERS['brevet_automatismes'] = function(b) {
  var questions = b.questions || [];
  var duration  = b.duration  || 1200;
  var uid       = 'bau' + Math.random().toString(36).substr(2, 8);
  if (!questions.length) return '';

  var mm      = Math.floor(duration / 60);
  var ss      = duration % 60;
  var initTmr = (mm < 10 ? '0' : '') + mm + ':' + (ss < 10 ? '0' : '') + ss;
  var n       = questions.length;
  var ptsPer  = Math.round(600 / n) / 100; // 6 pts divided equally, rounded to 2dp

  var rowsHtml = '';
  for (var i = 0; i < questions.length; i++) {
    var q = questions[i];
    rowsHtml +=
      '<div style="display:flex;align-items:center;justify-content:space-between;' +
        'padding:0.7rem 1rem;border-bottom:1px solid rgba(16,185,129,0.1);">' +
        '<span style="font-size:0.95rem;color:#f1f5f9;font-family:\'Courier New\',monospace;flex:1;padding-right:1rem;">' +
          '<span style="color:#10b981;font-weight:700;margin-right:0.4rem;">' + (i+1) + '.</span>' +
          _esc(q.question || '') +
        '</span>' +
        '<div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">' +
          '<input type="text" class="' + uid + 'in" data-ans="' + _esc(String(q.answer || '')) + '" ' +
            'placeholder="?" maxlength="16" autocomplete="off" ' +
            'style="width:68px;padding:5px 8px;text-align:center;box-sizing:border-box;' +
            'background:rgba(0,0,0,0.35);border:1px solid rgba(16,185,129,0.25);' +
            'color:#fff;border-radius:6px;font-size:0.9rem;font-family:\'Courier New\',monospace;">' +
          '<span class="' + uid + 'fb" style="font-size:0.9rem;width:28px;text-align:left;"></span>' +
        '</div>' +
      '</div>';
  }

  return (
    '<div id="' + uid + '" style="font-family:\'Inter\',system-ui,sans-serif;margin:1.5rem 0;' +
      'background:rgba(4,47,30,0.25);border:2px solid #059669;border-radius:14px;overflow:hidden;">' +
      // Header
      '<div style="display:flex;justify-content:space-between;align-items:center;' +
        'padding:0.85rem 1.2rem;background:rgba(6,95,70,0.45);' +
        'border-bottom:1px solid rgba(16,185,129,0.18);">' +
        '<div>' +
          '<div style="font-size:0.9rem;font-weight:800;color:#10b981;letter-spacing:0.02em;">⏱ Automatismes · DNB 2026</div>' +
          '<div style="font-size:0.65rem;color:rgba(167,243,208,0.65);margin-top:2px;">' +
            'Partie 1 · 6 pts · Calculatrice interdite</div>' +
        '</div>' +
        '<div id="' + uid + 'tmr" style="background:rgba(4,47,30,0.85);color:#a7f3d0;' +
          'padding:4px 14px;border-radius:6px;font-weight:800;' +
          'font-family:\'Courier New\',monospace;font-size:1.15rem;letter-spacing:0.05em;">' +
          initTmr +
        '</div>' +
      '</div>' +
      // Warning bar
      '<div style="padding:0.5rem 1.2rem;background:rgba(146,64,14,0.2);' +
        'border-bottom:1px solid rgba(217,119,6,0.2);">' +
        '<span style="font-size:0.72rem;color:#fbbf24;">⚠ Répondez rapidement — pas de calculatrice — appuyez Entrée pour passer à la question suivante</span>' +
      '</div>' +
      // Questions
      '<div>' + rowsHtml + '</div>' +
      // Footer
      '<div style="padding:0.9rem 1.2rem;">' +
        '<button id="' + uid + 'btn" ' +
          'style="width:100%;padding:10px;background:#059669;color:#fff;border:none;' +
          'font-weight:700;font-size:0.88rem;border-radius:8px;cursor:pointer;' +
          'letter-spacing:0.04em;transition:background 0.15s;" ' +
          'onmouseover="this.style.background=\'#047857\'" ' +
          'onmouseout="this.style.background=\'#059669\'" ' +
          'onclick="window[\'' + uid + '\'].validate()">' +
          'Corriger mon épreuve ✓' +
        '</button>' +
        '<div id="' + uid + 'sc" style="display:none;text-align:center;margin-top:0.8rem;' +
          'font-size:0.92rem;font-weight:700;color:#10b981;"></div>' +
      '</div>' +
    '</div>' +
    '<script>(function(){' +
      'var left=' + duration + ',done=false;' +
      'var tmrEl=document.getElementById("' + uid + 'tmr");' +
      'var iv=setInterval(function(){' +
        'if(done){clearInterval(iv);return;}' +
        'left--;' +
        'var m=Math.floor(left/60),s=left%60;' +
        'if(tmrEl)tmrEl.textContent=(m<10?"0":"")+m+":"+(s<10?"0":"")+s;' +
        'if(left<=60&&tmrEl)tmrEl.style.color="#f87171";' +
        'if(left<=0){clearInterval(iv);window["' + uid + '"].validate();}' +
      '},1000);' +
      'window["' + uid + '"]={' +
        'validate:function(){' +
          'if(done)return;done=true;clearInterval(iv);' +
          'var ins=document.querySelectorAll("#' + uid + ' .' + uid + 'in");' +
          'var fbs=document.querySelectorAll("#' + uid + ' .' + uid + 'fb");' +
          'var score=0;' +
          'ins.forEach(function(inp,i){' +
            'var user=inp.value.trim().replace(/,/g,".");' +
            'var ans=(inp.getAttribute("data-ans")||"").trim().replace(/,/g,".");' +
            'var ok=user.toLowerCase()===ans.toLowerCase();' +
            'if(ok){score++;' +
              'fbs[i].textContent="✓";fbs[i].style.color="#10b981";' +
              'inp.style.borderColor="rgba(16,185,129,0.5)";' +
            '}else{' +
              'fbs[i].textContent="✗ "+ans;fbs[i].style.color="#f87171";' +
              'fbs[i].style.fontSize="0.72rem";' +
              'inp.style.borderColor="rgba(248,113,113,0.5)";inp.style.color="#f87171";' +
            '}' +
            'inp.disabled=true;' +
          '});' +
          'var sc=document.getElementById("' + uid + 'sc");' +
          'var pts=Math.round(score/' + n + '*6*10)/10;' +
          'if(sc){' +
            'sc.style.display="block";' +
            'sc.textContent=score+"/' + n + ' correct — "+pts+"/6 pts";' +
            'if(score===' + n + ')sc.textContent+=" ✨ Parfait !";' +
          '}' +
          'var btn=document.getElementById("' + uid + 'btn");' +
          'if(btn)btn.style.display="none";' +
        '}' +
      '};' +
      // Enter key advances to next input
      'var ins=document.querySelectorAll("#' + uid + ' .' + uid + 'in");' +
      'ins.forEach(function(inp,i){' +
        'inp.addEventListener("keydown",function(e){' +
          'if(e.key!=="Enter")return;' +
          'if(i<ins.length-1){ins[i+1].focus();}' +
          'else{window["' + uid + '"].validate();}' +
        '});' +
      '});' +
    '})();<\/script>'
  );
};

// ── hub ───────────────────────────────────────────────────────────────────────
// Multi-subject navigation hub: subject tabs fixed at top, slide pills fixed at
// bottom (update per subject). Renders all atom types inline via _RENDERERS.
// Schema: { background, nav_background, subjects [{id, label, color, slides [{id, label, blocks}]}] }
// Light mode default: white content, light nav bars (#f8fafc, dark readable text).
// Responds to body.asw-dark-theme via MutationObserver — decoupled from theme_toggle.
_RENDERERS['hub'] = function(b) {
  var subjects = b.subjects || [];
  var bg  = b.background     || '#0f172a';  // dark mode content colour
  var nav = b.nav_background || bg;         // dark mode nav bar colour
  var uid = 'hub' + Math.random().toString(36).substr(2, 8);
  if (!subjects.length) return '';

  var contentHtml = '';
  var bottomNavHtml = '';
  var colorsJs = '[';
  var countsJs = '[';

  for (var si = 0; si < subjects.length; si++) {
    var subj    = subjects[si];
    var slides  = subj.slides || [];
    var accent  = subj.color || '#6366f1';
    colorsJs   += (si ? ',' : '') + '"' + accent + '"';
    countsJs   += (si ? ',' : '') + slides.length;

    contentHtml += '<div id="' + uid + 'S' + si + '" style="display:' + (si === 0 ? 'block' : 'none') + ';">';
    for (var sli = 0; sli < slides.length; sli++) {
      var slide     = slides[sli];
      var slideHtml = '';
      var blocks    = slide.blocks || [];
      for (var bi = 0; bi < blocks.length; bi++) {
        var fn = _RENDERERS[blocks[bi].type];
        if (fn) slideHtml += fn(blocks[bi]);
      }
      contentHtml += '<div id="' + uid + 'S' + si + 'L' + sli + '" style="display:' + (sli === 0 ? 'block' : 'none') + ';">' + slideHtml + '</div>';
    }
    contentHtml += '</div>';

    bottomNavHtml += '<div id="' + uid + 'N' + si + '" style="display:' + (si === 0 ? 'flex' : 'none') + ';gap:5px;overflow-x:auto;padding:8px 10px;scrollbar-width:none;-webkit-overflow-scrolling:touch;">';
    for (var sli2 = 0; sli2 < slides.length; sli2++) {
      var isActivePill = sli2 === 0;
      bottomNavHtml +=
        '<button id="' + uid + 'P' + si + '_' + sli2 + '" ' +
        'onclick="window[\'' + uid + '\'].sl(' + si + ',' + sli2 + ')" ' +
        'style="flex-shrink:0;padding:5px 11px;border-radius:20px;border:none;cursor:pointer;' +
        'font-size:0.72rem;font-weight:700;white-space:nowrap;transition:all 0.15s;' +
        'background:' + (isActivePill ? accent : 'rgba(0,0,0,0.06)') + ';' +
        'color:' + (isActivePill ? '#fff' : 'rgba(0,0,0,0.45)') + ';">' +
        _esc(slides[sli2].label || ('Slide ' + (sli2 + 1))) + '</button>';
    }
    bottomNavHtml += '</div>';
  }

  // Subject tabs — light mode default: dark text on light nav
  var tabsHtml = '<div style="display:flex;gap:5px;overflow-x:auto;padding:10px 12px 8px;scrollbar-width:none;-webkit-overflow-scrolling:touch;">';
  for (var si2 = 0; si2 < subjects.length; si2++) {
    var ac2 = subjects[si2].color || '#6366f1';
    var isFirstTab = si2 === 0;
    tabsHtml +=
      '<button id="' + uid + 'T' + si2 + '" ' +
      'onclick="window[\'' + uid + '\'].subj(' + si2 + ')" ' +
      'style="flex-shrink:0;padding:7px 14px;border-radius:10px;border:1.5px solid;cursor:pointer;' +
      'font-size:0.78rem;font-weight:800;white-space:nowrap;letter-spacing:0.02em;transition:all 0.18s;' +
      'background:' + (isFirstTab ? ac2 : 'transparent') + ';' +
      'color:' + (isFirstTab ? '#fff' : 'rgba(0,0,0,0.55)') + ';' +
      'border-color:' + (isFirstTab ? ac2 : 'rgba(0,0,0,0.15)') + ';">' +
      _esc(subjects[si2].label || ('Subject ' + (si2 + 1))) + '</button>';
  }
  tabsHtml += '</div>';

  colorsJs += ']';
  countsJs += ']';

  return (
    '<style>' +
    'body{background:#ffffff;margin:0;}' +
    '.asw-page>h1{display:none;}' +
    '#' + uid + 'body,#' + uid + 'content{transition:background 0.25s;}' +
    '#' + uid + 'TOPNAV,#' + uid + 'BOTNAV{transition:background 0.25s,border-color 0.25s,box-shadow 0.25s;}' +
    '</style>' +
    '<div id="' + uid + 'body" style="font-family:\'Inter\',system-ui,sans-serif;background:#ffffff;min-height:100vh;">' +
    '<div id="' + uid + 'TOPNAV" style="position:fixed;top:0;left:0;right:0;z-index:400;background:#f8fafc;' +
    'border-bottom:1px solid rgba(0,0,0,0.08);box-shadow:0 2px 8px rgba(0,0,0,0.06);">' +
    tabsHtml + '</div>' +
    '<div id="' + uid + 'content" style="padding-top:64px;padding-bottom:72px;background:#ffffff;">' + contentHtml + '</div>' +
    '<div id="' + uid + 'BOTNAV" style="position:fixed;bottom:0;left:0;right:0;z-index:400;background:#f8fafc;' +
    'border-top:1px solid rgba(0,0,0,0.08);box-shadow:0 -2px 8px rgba(0,0,0,0.06);">' +
    bottomNavHtml + '</div>' +
    '</div>' +
    '<script>(function(){' +
    'var C=' + colorsJs + ';' +
    'var BG="' + bg + '",NAV="' + nav + '";' +
    'var cs=0,cl=[],dark=false;' +
    'var counts=' + countsJs + ';' +
    'for(var i=0;i<counts.length;i++)cl.push(0);' +
    'function g(id){return document.getElementById("' + uid + '"+id);}' +
    'function iTab(){return dark?{c:"rgba(255,255,255,0.35)",b:"rgba(255,255,255,0.12)"}:{c:"rgba(0,0,0,0.55)",b:"rgba(0,0,0,0.15)"};}'  +
    'function iPill(){return dark?{bg:"rgba(255,255,255,0.07)",c:"rgba(255,255,255,0.4)"}:{bg:"rgba(0,0,0,0.06)",c:"rgba(0,0,0,0.45)"};}'  +
    'function applyTheme(d){' +
    'dark=d;' +
    'var cb=d?BG:"#ffffff",navb=d?NAV:"#f8fafc";' +
    'var bdr=d?"rgba(255,255,255,0.07)":"rgba(0,0,0,0.08)";' +
    'var shT=d?"0 2px 12px rgba(0,0,0,0.4)":"0 2px 8px rgba(0,0,0,0.06)";' +
    'var shB=d?"0 -2px 12px rgba(0,0,0,0.4)":"0 -2px 8px rgba(0,0,0,0.06)";' +
    'var wrap=g("body"),ct=g("content"),tn=g("TOPNAV"),bn=g("BOTNAV");' +
    'if(wrap)wrap.style.background=cb;' +
    'if(ct)ct.style.background=cb;' +
    'document.body.style.background=cb;' +
    'if(tn){tn.style.background=navb;tn.style.borderBottomColor=bdr;tn.style.boxShadow=shT;}' +
    'if(bn){bn.style.background=navb;bn.style.borderTopColor=bdr;bn.style.boxShadow=shB;}' +
    'var ts=iTab(),ps=iPill();' +
    'for(var i=0;i<counts.length;i++){' +
    'if(i!==cs){var t=g("T"+i);if(t){t.style.color=ts.c;t.style.borderColor=ts.b;}}' +
    'for(var j=0;j<counts[i];j++){if(!(i===cs&&j===cl[i])){var p=g("P"+i+"_"+j);if(p){p.style.background=ps.bg;p.style.color=ps.c;}}}' +
    '}' +
    '}' +
    'var obs=new MutationObserver(function(ms){ms.forEach(function(m){' +
    'if(m.attributeName==="class"){var d=document.body.classList.contains("asw-dark-theme");if(d!==dark)applyTheme(d);}' +
    '});});' +
    'obs.observe(document.body,{attributes:true,attributeFilter:["class"]});' +
    'window["' + uid + '"]={' +
    'subj:function(si){' +
    'if(si===cs)return;' +
    'var ts=iTab();' +
    'g("S"+cs).style.display="none";g("N"+cs).style.display="none";' +
    'var ot=g("T"+cs);ot.style.background="transparent";ot.style.color=ts.c;ot.style.borderColor=ts.b;' +
    'cs=si;' +
    'g("S"+si).style.display="block";g("N"+si).style.display="flex";' +
    'var nt=g("T"+si);nt.style.background=C[si];nt.style.color="#fff";nt.style.borderColor=C[si];' +
    'window["' + uid + '"].sl(si,cl[si]);window.scrollTo(0,0);' +
    '},' +
    'sl:function(si,sli){' +
    'var ps=iPill();' +
    'var op=g("P"+si+"_"+cl[si]),os=g("S"+si+"L"+cl[si]);' +
    'if(op){op.style.background=ps.bg;op.style.color=ps.c;}' +
    'if(os)os.style.display="none";' +
    'cl[si]=sli;' +
    'var np=g("P"+si+"_"+sli),ns=g("S"+si+"L"+sli);' +
    'if(np){np.style.background=C[si];np.style.color="#fff";}' +
    'if(ns)ns.style.display="block";' +
    'window.scrollTo(0,0);' +
    '}};' +
    '})();<\/script>'
  );
};
// ── catalogue_provenance ──────────────────────────────────────────────────────
// Demo flow-diagram atom — circles connected by gradient lines showing catalogue sources.
// Schema: { label?, sources [{icon?, what, catalogue, note?, color?}] }
_RENDERERS['catalogue_provenance'] = function(b) {
  var label   = b.label   || 'Assembled from';
  var sources = b.sources || [];
  var uid     = 'cpv' + Math.random().toString(36).substr(2, 8);
  if (!sources.length) return '';

  var CATALOGUE_COLORS = {
    'a2media':    '#8b5cf6',
    'a2UI':       '#6366f1',
    'a2ui':       '#6366f1',
    'a2knowledge':'#10b981',
    'ard':        '#f59e0b'
  };

  // Callout layout: circles at bottom, upward stems pointing to labelled target zones
  // Each source has an optional `target` string naming what it points at in the card above.
  // Without `target`, falls back to `what`.
  var n = sources.length;
  var cols = '';
  for (var i = 0; i < n; i++) {
    var s = sources[i];
    var color = s.color || CATALOGUE_COLORS[s.catalogue] || '#64748b';
    var stemH = 40 + (i % 2 === 0 ? 0 : 20); // stagger stem heights so labels don't collide
    cols +=
      '<div style="flex:1;display:flex;flex-direction:column;align-items:center;min-width:0;">' +
        // Target label at top (what in the card this points to)
        '<div style="font-size:0.6rem;font-weight:700;color:' + color + ';text-align:center;' +
          'padding:2px 8px;border:1px solid ' + color + '44;border-radius:8px;' +
          'background:' + color + '0d;white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis;">' +
          _esc(s.target || s.what || '') +
        '</div>' +
        // Stem line going down
        '<div style="width:2px;background:linear-gradient(' + color + '88,' + color + '22);' +
          'height:' + stemH + 'px;margin:0 auto;"></div>' +
        // Circle node
        '<div style="width:52px;height:52px;border-radius:50%;flex-shrink:0;' +
          'background:radial-gradient(circle at 35% 35%,' + color + '28,' + color + '08);' +
          'border:2px solid ' + color + ';' +
          'box-shadow:0 0 16px ' + color + '44;' +
          'display:flex;align-items:center;justify-content:center;font-size:1.25rem;">' +
          (s.icon || '◈') +
        '</div>' +
        // Catalogue name
        '<div style="margin-top:5px;font-size:0.6rem;font-weight:800;letter-spacing:0.08em;color:' + color + ';">' +
          _esc(s.catalogue || '') +
        '</div>' +
        // What + note
        '<div style="margin-top:2px;font-size:0.68rem;font-weight:600;color:#94a3b8;text-align:center;line-height:1.3;">' +
          _esc(s.what || '') +
        '</div>' +
      '</div>';
  }

  return (
    '<div id="' + uid + '" style="font-family:\'Inter\',system-ui,sans-serif;margin:0.25rem 0 1.5rem;">' +
    '<div style="text-align:center;margin-bottom:0.9rem;">' +
      '<span style="font-size:0.55rem;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;' +
        'color:#475569;background:rgba(255,255,255,0.03);padding:2px 12px;border-radius:20px;' +
        'border:1px solid rgba(255,255,255,0.07);">🔍 ' + _esc(label) + '</span>' +
    '</div>' +
    '<div style="display:flex;align-items:flex-end;justify-content:space-around;gap:8px;padding:0 4px;">' +
      cols +
    '</div>' +
    '</div>'
  );
};
