// atoms_lms.gs — Enterprise LMS atoms for A2UI
// progress_store is the state foundation — always include it first on any LMS page.

// ── progress_store ────────────────────────────────────────────────────────────
// Invisible connector atom — no visual output.
// GAS: reads initial state from a Sheet at render time; writes async via google.script.run.
// Web: reads/writes localStorage keyed by course_id.
// Exposes window._A2UI_STORE for all other LMS atoms.
// Dispatches "a2ui:store" CustomEvent after init and every write.
_RENDERERS['progress_store'] = function(b) {
  var courseId = b.course_id || 'default';
  var initial  = '{}';
  if (typeof SpreadsheetApp !== 'undefined') {
    try { initial = JSON.stringify(a2uiProgressRead(courseId) || {}); } catch(e) {}
  }
  var cid = courseId.replace(/\\/g,'\\\\').replace(/"/g,'\\"');
  return (
    '<script>(function(){' +
      'var cid="' + cid + '";' +
      'var d=' + initial + ';' +
      'var isGAS=typeof google!=="undefined"&&google.script&&google.script.run;' +
      'if(!isGAS){try{var ls=localStorage.getItem("a2ui:"+cid);if(ls)d=JSON.parse(ls);}catch(e){}}' +
      'function _save(cb){' +
        'if(isGAS){google.script.run.withSuccessHandler(cb||function(){}).a2uiProgressWrite(cid,d);}' +
        'else{try{localStorage.setItem("a2ui:"+cid,JSON.stringify(d));}catch(e){}if(cb)cb();}' +
      '}' +
      'function _fire(){document.dispatchEvent(new CustomEvent("a2ui:store",{detail:window._A2UI_STORE}));}' +
      'window._A2UI_STORE={' +
        'get:function(k){return d[k]!==undefined?d[k]:null;},' +
        'set:function(k,v,cb){d[k]=v;_save(cb);_fire();},' +
        'getAll:function(){return JSON.parse(JSON.stringify(d));},' +
        'isComplete:function(id){return!!d["done:"+id];},' +
        'markComplete:function(id,cb){d["done:"+id]=true;_save(cb);_fire();},' +
        'setScore:function(id,score,cb){d["score:"+id]=score;_save(cb);_fire();},' +
        'getScore:function(id){return d["score:"+id]!=null?d["score:"+id]:null;},' +
        'getPath:function(){return d["path"]||null;},' +
        'setPath:function(p,cb){d["path"]=p;_save(cb);_fire();}' +
      '};' +
      'setTimeout(_fire,0);' +
    '})();<\/script>'
  );
};

// ── module_map ────────────────────────────────────────────────────────────────
// Visual curriculum grid — cards per module with live status from progress_store.
// Status: locked (greyed), available (Start →), complete (✓ Done).
_RENDERERS['module_map'] = function(b) {
  var uid     = 'mmap' + Math.random().toString(36).substr(2, 6);
  var title   = b.title   || 'Course Modules';
  var modules = b.modules || [];
  var cols    = Math.min(parseInt(b.columns || 3), 4);

  var cards = '';
  for (var i = 0; i < modules.length; i++) {
    var m = modules[i];
    cards +=
      '<a id="' + uid + 'a' + i + '" href="#" target="_top" style="text-decoration:none;">' +
      '<div id="' + uid + 'c' + i + '" style="border-radius:14px;padding:20px;min-height:150px;box-sizing:border-box;' +
        'background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);' +
        'display:flex;flex-direction:column;gap:10px;position:relative;overflow:hidden;transition:all 0.2s;">' +
        '<div id="' + uid + 's' + i + '" style="position:absolute;top:12px;right:12px;"></div>' +
        '<div style="font-size:0.58rem;font-weight:700;letter-spacing:0.12em;color:#334155;text-transform:uppercase;">Module ' + (i + 1) + '</div>' +
        '<div style="display:flex;align-items:center;gap:10px;">' +
          '<span style="font-size:1.4rem;flex-shrink:0;">' + _esc(m.icon || '📚') + '</span>' +
          '<div style="font-size:0.88rem;font-weight:700;color:#f1f5f9;line-height:1.3;">' + _esc(m.title || '') + '</div>' +
        '</div>' +
        (m.description ? '<div style="font-size:0.72rem;color:#64748b;line-height:1.5;">' + _esc(m.description) + '</div>' : '') +
        '<div style="display:flex;gap:12px;margin-top:auto;">' +
          (m.duration ? '<span style="font-size:0.6rem;color:#475569;">⏱ ' + _esc(m.duration) + '</span>' : '') +
          (m.lessons  ? '<span style="font-size:0.6rem;color:#475569;">' + m.lessons + ' lessons</span>' : '') +
        '</div>' +
      '</div></a>';
  }

  // Resolve all module URLs server-side so the GAS sandbox iframe never sees
  // a relative URL. Supports three patterns:
  //   page: [atoms]          → encode inline atom list as ?p= URL (fully self-contained)
  //   url: "?nav=<slug>"     → prefix with exec URL to make absolute
  //   url: "https://..."     → used as-is
  var base = _getWebAppUrl();
  var fromSlug = (typeof _CURRENT_NAV_SLUG !== 'undefined' && _CURRENT_NAV_SLUG) ? _CURRENT_NAV_SLUG : '';
  var modsJson = JSON.stringify(modules.map(function(m, i) {
    var url = '#';
    if (m.page && m.page.length) {
      try {
        var pg = JSON.stringify({ title: m.title || ('Module ' + (i+1)), theme: 'dark', blocks: m.page });
        var enc = Utilities.base64EncodeWebSafe(
          Utilities.gzip(Utilities.newBlob(pg, 'application/json')).getBytes()
        ).replace(/=+$/, '');
        url = base + '?p=' + enc + (fromSlug ? '&from=' + fromSlug : '');
      } catch(e) { url = m.url || '#'; }
    } else if (m.url) {
      var resolvedUrl = (m.url.charAt(0) === '?' && base) ? base + m.url : m.url;
      // Stamp &from= so back buttons work when hub was referenced by url field rather than page array
      url = (fromSlug && resolvedUrl.indexOf('from=') === -1)
        ? resolvedUrl + (resolvedUrl.indexOf('?') !== -1 ? '&' : '?') + 'from=' + fromSlug
        : resolvedUrl;
    }
    return { id: m.id || ('mod' + i), url: url, req: m.required || [] };
  }));

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;">' +
    '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#64748b;margin-bottom:16px;">📋 ' + _esc(title) + '</div>' +
    '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:12px;">' + cards + '</div>' +
    '<script>(function(){' +
      'var uid="' + uid + '";' +
      'var mods=' + modsJson + ';' +
      'function update(store){' +
        'mods.forEach(function(m,i){' +
          'var card=document.getElementById(uid+"c"+i);' +
          'var badge=document.getElementById(uid+"s"+i);' +
          'var link=document.getElementById(uid+"a"+i);' +
          'if(!card)return;' +
          'var done=store&&store.isComplete(m.id);' +
          'var locked=m.req.length>0&&m.req.some(function(k){return!store||!store.isComplete(k);});' +
          'card.onmouseover=null;card.onmouseout=null;' +
          'if(done){' +
            'card.style.background="rgba(52,211,153,0.07)";card.style.borderColor="rgba(52,211,153,0.25)";card.style.opacity="1";' +
            'badge.innerHTML=\'<span style="font-size:0.6rem;background:rgba(52,211,153,0.15);color:#34d399;padding:2px 8px;border-radius:99px;font-weight:700;">✓ Done</span>\';' +
            'if(link)link.href=m.url;' +
          '}else if(locked){' +
            'card.style.opacity="0.35";card.style.cursor="default";' +
            'badge.innerHTML=\'<span style="color:#334155;font-size:1rem;">🔒</span>\';' +
            'if(link){link.href="#";link.onclick=function(e){e.preventDefault();};}' +
          '}else{' +
            'card.style.background="rgba(255,255,255,0.03)";card.style.borderColor="rgba(255,255,255,0.08)";card.style.opacity="1";card.style.cursor="pointer";' +
            'badge.innerHTML=\'<span style="font-size:0.6rem;background:rgba(99,102,241,0.15);color:#818cf8;padding:2px 8px;border-radius:99px;font-weight:700;">Start →</span>\';' +
            'if(link)link.href=m.url;' +
            'card.onmouseover=function(){this.style.background="rgba(99,102,241,0.08)";this.style.transform="translateY(-2px)";};' +
            'card.onmouseout=function(){this.style.background="rgba(255,255,255,0.03)";this.style.transform="";};' +
          '}' +
        '});' +
      '}' +
      'document.addEventListener("a2ui:store",function(e){update(e.detail);});' +
      'update(window._A2UI_STORE||null);' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── knowledge_check ───────────────────────────────────────────────────────────
// Lightweight inline comprehension pulse — single question, no score pressure.
// Correct → green flash + explanation. Wrong → gentle red + explanation. No retry gate.
_RENDERERS['knowledge_check'] = function(b) {
  var uid      = 'kc' + Math.random().toString(36).substr(2, 6);
  var question = b.question    || 'Comprehension check';
  var options  = b.options     || [];
  var correct  = parseInt(b.correct || 0);
  var explain  = b.explanation || '';

  var opts = '';
  for (var i = 0; i < options.length; i++) {
    opts +=
      '<button id="' + uid + 'o' + i + '" onclick="' + uid + 'pick(' + i + ')" ' +
        'style="display:block;width:100%;text-align:left;padding:11px 14px;border-radius:9px;margin-bottom:7px;' +
          'background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);' +
          'color:#cbd5e1;font-size:0.8rem;cursor:pointer;transition:all 0.15s;"' +
        ' onmouseover="if(!this.disabled)this.style.background=\'rgba(99,102,241,0.08)\'"' +
        ' onmouseout="if(!this.disabled)this.style.background=\'rgba(255,255,255,0.03)\'">' +
        '<span style="color:#475569;font-size:0.65rem;font-weight:700;margin-right:8px;">' + String.fromCharCode(65 + i) + '</span>' +
        _esc(options[i]) +
      '</button>';
  }

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;padding:18px;border-radius:12px;' +
      'background:rgba(99,102,241,0.05);border:1px solid rgba(99,102,241,0.14);">' +
    '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#6366f1;margin-bottom:10px;">💡 Knowledge Check</div>' +
    '<div style="font-size:0.88rem;font-weight:600;color:#f1f5f9;line-height:1.5;margin-bottom:14px;">' + _esc(question) + '</div>' +
    '<div id="' + uid + 'opts">' + opts + '</div>' +
    '<div id="' + uid + 'fb" style="display:none;margin-top:10px;padding:12px 14px;border-radius:9px;font-size:0.75rem;line-height:1.5;"></div>' +
    '<script>(function(){' +
      'var cor=' + correct + ',total=' + options.length + ',done=false;' +
      'var ex="' + explain.replace(/"/g,'\\"').replace(/\n/g,' ') + '";' +
      'window["' + uid + 'pick"]=function(i){' +
        'if(done)return;done=true;' +
        'for(var j=0;j<total;j++){' +
          'var b=document.getElementById("' + uid + 'o"+j);if(!b)continue;' +
          'b.disabled=true;b.onmouseover=null;b.onmouseout=null;' +
          'if(j===cor){b.style.background="rgba(52,211,153,0.12)";b.style.borderColor="rgba(52,211,153,0.35)";b.style.color="#34d399";}' +
          'else if(j===i&&i!==cor){b.style.background="rgba(248,113,113,0.1)";b.style.borderColor="rgba(248,113,113,0.3)";b.style.color="#f87171";}' +
          'else{b.style.opacity="0.35";}' +
        '}' +
        'var fb=document.getElementById("' + uid + 'fb");if(!fb)return;' +
        'fb.style.display="block";' +
        'if(i===cor){fb.style.background="rgba(52,211,153,0.09)";fb.style.color="#34d399";fb.innerHTML="✓ Correct! "+ex;}' +
        'else{fb.style.background="rgba(248,113,113,0.09)";fb.style.color="#f87171";fb.innerHTML="✗ Not quite — "+ex;}' +
      '};' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── quiz_result_summary ───────────────────────────────────────────────────────
// End-of-quiz result screen: score, time, per-question dot breakdown, pass/fail badge.
// Writes score to progress_store. next_url and retry_url drive navigation.
_RENDERERS['quiz_result_summary'] = function(b) {
  var score     = parseInt(b.score || 0);
  var total     = parseInt(b.total || 10);
  var timeSecs  = parseInt(b.time_secs || 0);
  var passMark  = parseInt(b.pass_mark || 70);
  var quizId    = b.quiz_id   || 'quiz';
  var nextUrl   = b.next_url  || '';
  var retryUrl  = b.retry_url || '';
  var questions = b.questions || [];

  var pct    = total > 0 ? Math.round((score / total) * 100) : 0;
  var passed = pct >= passMark;
  var col    = passed ? '#34d399' : '#f87171';
  var bgCol  = passed ? 'rgba(52,211,153,0.07)'  : 'rgba(248,113,113,0.07)';
  var bdCol  = passed ? 'rgba(52,211,153,0.2)'   : 'rgba(248,113,113,0.2)';
  var mins   = Math.floor(timeSecs / 60);
  var secs   = timeSecs % 60;
  var timeStr = (mins > 0 ? mins + 'm ' : '') + secs + 's';

  var dots = '';
  for (var i = 0; i < questions.length; i++) {
    var ok = questions[i].correct;
    dots += '<div title="' + _esc((questions[i].label || ('Q' + (i + 1)))) + '" ' +
      'style="width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;' +
        'font-size:0.55rem;font-weight:700;color:#fff;background:' + (ok ? '#34d399' : '#f87171') + ';">' +
      (ok ? '✓' : '✗') + '</div>';
  }

  var btns = '';
  if (retryUrl) btns += '<a href="' + _esc(retryUrl) + '" target="_top" style="padding:10px 22px;border-radius:9px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);color:#94a3b8;font-size:0.8rem;font-weight:600;text-decoration:none;">↩ Retry</a>';
  if (nextUrl)  btns += '<a href="' + _esc(nextUrl)  + '" target="_top" style="padding:10px 22px;border-radius:9px;background:' + col + ';color:#0f172a;font-size:0.8rem;font-weight:700;text-decoration:none;">Continue →</a>';

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;padding:28px;border-radius:16px;background:' + bgCol + ';border:1px solid ' + bdCol + ';">' +
    '<div style="text-align:center;margin-bottom:24px;">' +
      '<div style="font-size:2.8rem;margin-bottom:10px;">' + (passed ? '🎉' : '📚') + '</div>' +
      '<div style="font-size:1.5rem;font-weight:800;color:' + col + ';">' + (passed ? 'Passed!' : 'Keep Going') + '</div>' +
      '<div style="font-size:0.72rem;color:#64748b;margin-top:5px;">' +
        (passed ? 'Well done — you cleared the pass mark.' : 'You need ' + passMark + '% to pass. Review the material and retry.') +
      '</div>' +
    '</div>' +
    '<div style="display:flex;justify-content:center;align-items:center;gap:32px;margin-bottom:24px;flex-wrap:wrap;">' +
      '<div style="text-align:center;">' +
        '<div style="font-size:3.2rem;font-weight:900;color:' + col + ';line-height:1;">' + pct + '<span style="font-size:1.4rem;">%</span></div>' +
        '<div style="font-size:0.62rem;color:#64748b;margin-top:4px;">' + score + ' / ' + total + ' correct</div>' +
      '</div>' +
      '<div style="display:flex;flex-direction:column;gap:8px;">' +
        '<div style="font-size:0.72rem;color:#94a3b8;">⏱ Time: <strong style="color:#e2e8f0;">' + timeStr + '</strong></div>' +
        '<div style="font-size:0.72rem;color:#94a3b8;">🎯 Pass mark: <strong style="color:#e2e8f0;">' + passMark + '%</strong></div>' +
      '</div>' +
    '</div>' +
    (questions.length ?
      '<div style="margin-bottom:20px;">' +
        '<div style="font-size:0.6rem;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Question breakdown</div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:6px;">' + dots + '</div>' +
      '</div>' : '') +
    (btns ? '<div style="display:flex;gap:10px;justify-content:center;">' + btns + '</div>' : '') +
    '<script>(function(){' +
      'var qid="' + quizId.replace(/"/g,'\\"') + '";' +
      'var pct=' + pct + ';' +
      'function wr(){if(window._A2UI_STORE)window._A2UI_STORE.setScore(qid,pct);}' +
      'if(window._A2UI_STORE)wr();else document.addEventListener("a2ui:store",wr,{once:true});' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── scenario_branch ───────────────────────────────────────────────────────────
// Narrative branching learning atom. Presents a real-world situation with 2-4 choices.
// Each choice reveals a consequence with good/neutral/bad outcome styling.
_RENDERERS['scenario_branch'] = function(b) {
  var uid     = 'sb' + Math.random().toString(36).substr(2, 6);
  var scene   = b.scenario || b.situation || '';
  var context = b.context  || '';
  var choices = b.choices  || [];
  var accent  = b.accent   || '#f59e0b';

  var btns = '';
  for (var i = 0; i < choices.length; i++) {
    var c = choices[i];
    btns +=
      '<button id="' + uid + 'c' + i + '" onclick="' + uid + 'pick(' + i + ')" ' +
        'style="display:block;width:100%;text-align:left;padding:12px 16px;border-radius:10px;margin-bottom:8px;' +
          'background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.09);' +
          'color:#cbd5e1;font-size:0.8rem;font-weight:500;cursor:pointer;transition:all 0.15s;"' +
        ' onmouseover="if(!this.disabled){this.style.background=\'rgba(245,158,11,0.07)\';this.style.borderColor=\'rgba(245,158,11,0.22)\';}"' +
        ' onmouseout="if(!this.disabled){this.style.background=\'rgba(255,255,255,0.03)\';this.style.borderColor=\'rgba(255,255,255,0.09)\';}">' +
        '<span style="color:' + _esc(accent) + ';font-weight:700;font-size:0.68rem;margin-right:8px;">' + String.fromCharCode(65 + i) + '</span>' +
        _esc(c.label || '') +
      '</button>';
  }

  var consJson = JSON.stringify(choices.map(function(c) {
    return { consequence: c.consequence || '', outcome: c.outcome || 'neutral', next_url: c.next_url || '' };
  }));

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;border-radius:14px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);">' +
    '<div style="padding:20px 24px;background:rgba(245,158,11,0.06);border-bottom:1px solid rgba(255,255,255,0.06);">' +
      '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:' + _esc(accent) + ';margin-bottom:8px;">🎭 Scenario</div>' +
      (context ? '<div style="font-size:0.72rem;color:#64748b;line-height:1.5;font-style:italic;margin-bottom:10px;">' + _esc(context) + '</div>' : '') +
      '<div style="font-size:0.92rem;font-weight:600;color:#f1f5f9;line-height:1.5;">' + _esc(scene) + '</div>' +
    '</div>' +
    '<div style="padding:20px 24px;">' +
      '<div style="font-size:0.62rem;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">What do you do?</div>' +
      btns +
    '</div>' +
    '<div id="' + uid + 'res" style="display:none;"></div>' +
    '<script>(function(){' +
      'var cons=' + consJson + ';' +
      'window["' + uid + 'pick"]=function(idx){' +
        'for(var j=0;j<cons.length;j++){var b=document.getElementById("' + uid + 'c"+j);if(b){b.disabled=true;b.onmouseover=null;b.onmouseout=null;b.style.opacity=j===idx?"1":"0.3";}}' +
        'var c=cons[idx];' +
        'var col=c.outcome==="good"?"#34d399":c.outcome==="bad"?"#f87171":"#f59e0b";' +
        'var icon=c.outcome==="good"?"✅":c.outcome==="bad"?"❌":"⚠️";' +
        'var bg=c.outcome==="good"?"rgba(52,211,153,0.07)":c.outcome==="bad"?"rgba(248,113,113,0.07)":"rgba(245,158,11,0.07)";' +
        'var res=document.getElementById("' + uid + 'res");' +
        'if(res){' +
          'res.style.display="block";res.style.padding="20px 24px";res.style.borderTop="1px solid rgba(255,255,255,0.06)";res.style.background=bg;' +
          'var hdr=\'<div style="font-size:0.68rem;font-weight:700;color:\'+col+\';margin-bottom:8px;">\'+icon+\' Outcome</div>\';' +
          'var body=\'<div style="font-size:0.82rem;color:#cbd5e1;line-height:1.6;">\'+c.consequence+\'</div>\';' +
          'var nav=c.next_url' +
            '?\'<a href="\'+c.next_url+\'" target="_top" style="display:inline-block;margin-top:14px;padding:9px 18px;border-radius:9px;background:\'+col+\';color:#0f172a;font-size:0.75rem;font-weight:700;text-decoration:none;">Continue →</a>\'' +
            ':\'<button onclick="' + uid + 'rst()" style="margin-top:14px;padding:9px 18px;border-radius:9px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#94a3b8;font-size:0.75rem;cursor:pointer;">↩ Try again</button>\';' +
          'res.innerHTML=hdr+body+nav;' +
        '}' +
      '};' +
      // Reset function for "try again"
      'window["' + uid + 'rst"]=function(){' +
        'var res=document.getElementById("' + uid + 'res");if(res)res.style.display="none";' +
        'for(var j=0;j<cons.length;j++){var b=document.getElementById("' + uid + 'c"+j);if(b){b.disabled=false;b.style.opacity="1";}}' +
      '};' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── completion_gate ───────────────────────────────────────────────────────────
// Renders a locked placeholder until a module id is marked complete in progress_store.
_RENDERERS['completion_gate'] = function(b) {
  var uid     = 'cgate' + Math.random().toString(36).substr(2, 6);
  var req     = b.requires || '';
  var message = b.message  || 'Complete the previous section to unlock this content.';
  var label   = b.label    || 'Locked';

  return (
    '<div id="' + uid + '" style="font-family:\'Inter\',system-ui,sans-serif;padding:28px;border-radius:14px;' +
      'border:2px dashed rgba(255,255,255,0.08);text-align:center;background:rgba(255,255,255,0.01);">' +
    '<div style="font-size:2rem;margin-bottom:10px;">🔒</div>' +
    '<div style="font-size:0.88rem;font-weight:700;color:#334155;margin-bottom:6px;">' + _esc(label) + '</div>' +
    '<div style="font-size:0.72rem;color:#1e293b;">' + _esc(message) + '</div>' +
    '</div>' +
    '<script>(function(){' +
      'var req="' + req.replace(/"/g,'\\"') + '";' +
      'function check(s){if(req&&s&&s.isComplete(req)){var el=document.getElementById("' + uid + '");if(el)el.style.display="none";}}' +
      'document.addEventListener("a2ui:store",function(e){check(e.detail);});' +
      'check(window._A2UI_STORE||null);' +
    '})();<\/script>'
  );
};

// ── certification_card ────────────────────────────────────────────────────────
// Completion certificate — unlocks when requires id is marked complete in progress_store.
// On GAS, earner name is derived from active user session if not supplied.
_RENDERERS['certification_card'] = function(b) {
  var uid    = 'cert' + Math.random().toString(36).substr(2, 6);
  var course = b.course  || 'Course Title';
  var issuer = b.issuer  || 'A2UI Learning';
  var req    = b.requires || '';
  var accent = b.accent  || '#6366f1';
  var earner = b.earner  || '';
  var date   = b.date    || new Date().toLocaleDateString('en-GB', {day:'numeric',month:'long',year:'numeric'});

  if (!earner && typeof Session !== 'undefined') {
    try {
      var email = Session.getActiveUser().getEmail();
      earner = email.split('@')[0].replace(/[._]/g,' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });
    } catch(e) {}
  }

  var cert =
    '<div style="border-radius:16px;padding:32px 28px;text-align:center;position:relative;overflow:hidden;' +
      'background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(167,139,250,0.07));' +
      'border:1px solid rgba(99,102,241,0.22);box-shadow:0 0 48px rgba(99,102,241,0.07);">' +
    '<div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,' + _esc(accent) + ',#a78bfa);"></div>' +
    '<div style="font-size:2.8rem;margin-bottom:14px;">🏆</div>' +
    '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:#6366f1;margin-bottom:8px;">' + _esc(issuer) + '</div>' +
    '<div style="font-size:0.72rem;color:#64748b;margin-bottom:14px;">This is to certify that</div>' +
    '<div id="' + uid + 'nm" style="font-size:1.6rem;font-weight:800;color:#f1f5f9;margin-bottom:6px;">' + _esc(earner || 'Learner') + '</div>' +
    '<div style="font-size:0.72rem;color:#64748b;margin-bottom:6px;">has successfully completed</div>' +
    '<div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;margin-bottom:16px;">' + _esc(course) + '</div>' +
    '<div style="font-size:0.65rem;color:#475569;">' + _esc(date) + '</div>' +
    '</div>';

  var locked =
    '<div id="' + uid + 'lk" style="padding:24px;border-radius:14px;border:2px dashed rgba(255,255,255,0.07);text-align:center;">' +
    '<div style="font-size:1.8rem;">🔒</div>' +
    '<div style="font-size:0.72rem;color:#334155;margin-top:8px;">Certificate unlocks on course completion.</div>' +
    '</div>';

  return (
    '<div id="' + uid + 'wrap" style="font-family:\'Inter\',system-ui,sans-serif;">' +
    '<div id="' + uid + 'cert" style="' + (req ? 'display:none;' : '') + '">' + cert + '</div>' +
    (req ? locked : '') +
    '<script>(function(){' +
      'var req="' + req.replace(/"/g,'\\"') + '";' +
      'function check(s){' +
        'if(!req||!s)return;' +
        'if(s.isComplete(req)){' +
          'var c=document.getElementById("' + uid + 'cert");var l=document.getElementById("' + uid + 'lk");' +
          'if(c)c.style.display="";if(l)l.style.display="none";' +
        '}' +
      '}' +
      'document.addEventListener("a2ui:store",function(e){check(e.detail);});' +
      'check(window._A2UI_STORE||null);' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── skill_radar ───────────────────────────────────────────────────────────────
// SVG spider/radar chart of competency levels across skill dimensions.
// Optional before values overlay as a dashed polygon for growth comparison.
_RENDERERS['skill_radar'] = function(b) {
  var title  = b.title  || 'Skill Profile';
  var accent = b.accent || '#6366f1';
  var skills = b.skills || [];
  var n      = Math.max(skills.length, 3);
  var SIZE   = 220;
  var CX     = SIZE / 2;
  var CY     = SIZE / 2;
  var R      = 82;
  var OUTER  = R + 22;

  function pt(angle, radius) {
    var rad = (angle - 90) * Math.PI / 180;
    return { x: CX + radius * Math.cos(rad), y: CY + radius * Math.sin(rad) };
  }

  function polygon(vals, r) {
    return vals.map(function(v, i) {
      var p = pt(i * (360 / n), r * Math.max(0, Math.min(100, v || 0)) / 100);
      return p.x.toFixed(2) + ',' + p.y.toFixed(2);
    }).join(' ');
  }

  // Grid rings
  var grid = '';
  for (var g = 1; g <= 4; g++) {
    var rpts = [];
    for (var k = 0; k < n; k++) { var p = pt(k * (360/n), R * g / 4); rpts.push(p.x.toFixed(2)+','+p.y.toFixed(2)); }
    grid += '<polygon points="' + rpts.join(' ') + '" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>';
  }

  // Axes and labels
  var axes = '', labels = '';
  for (var i = 0; i < n; i++) {
    var angle = i * (360 / n);
    var op = pt(angle, R);
    axes += '<line x1="' + CX + '" y1="' + CY + '" x2="' + op.x.toFixed(2) + '" y2="' + op.y.toFixed(2) + '" stroke="rgba(255,255,255,0.07)" stroke-width="1"/>';
    var lp = pt(angle, OUTER);
    var anchor = lp.x > CX + 5 ? 'start' : lp.x < CX - 5 ? 'end' : 'middle';
    labels += '<text x="' + lp.x.toFixed(2) + '" y="' + (lp.y + 4).toFixed(2) + '" text-anchor="' + anchor + '" fill="#64748b" font-size="9" font-family="Inter,sans-serif">' + _esc((skills[i] && skills[i].label) || ('Skill ' + (i + 1))) + '</text>';
  }

  var hasBefore = skills.some(function(s) { return s.before !== undefined; });
  var before = hasBefore ?
    '<polygon points="' + polygon(skills.map(function(s){return s.before||0;}), R) + '" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.18)" stroke-width="1.5" stroke-dasharray="4,3"/>' : '';

  var current =
    '<polygon points="' + polygon(skills.map(function(s){return s.value||0;}), R) + '" fill="' + _esc(accent) + '1f" stroke="' + _esc(accent) + '" stroke-width="2"/>';

  // Dot markers on current polygon
  var dots = '';
  for (var i = 0; i < n; i++) {
    var v = Math.max(0, Math.min(100, (skills[i] && skills[i].value) || 0));
    var dp = pt(i * (360/n), R * v / 100);
    dots += '<circle cx="' + dp.x.toFixed(2) + '" cy="' + dp.y.toFixed(2) + '" r="3" fill="' + _esc(accent) + '" stroke="#0f172a" stroke-width="1.5"/>';
  }

  var svgH = SIZE + 28;
  var svg = '<svg width="' + SIZE + '" height="' + svgH + '" viewBox="0 0 ' + SIZE + ' ' + svgH + '" style="max-width:280px;">' +
    grid + axes + before + current + dots + labels + '</svg>';

  var legend = hasBefore ?
    '<div style="display:flex;gap:16px;justify-content:center;margin-top:6px;">' +
      '<div style="display:flex;align-items:center;gap:5px;font-size:0.62rem;color:#64748b;"><div style="width:18px;height:0;border-top:2px dashed rgba(255,255,255,0.3);"></div>Before</div>' +
      '<div style="display:flex;align-items:center;gap:5px;font-size:0.62rem;color:#64748b;"><div style="width:18px;height:2px;background:' + _esc(accent) + ';"></div>Now</div>' +
    '</div>' : '';

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;text-align:center;">' +
    '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#64748b;margin-bottom:14px;">🎯 ' + _esc(title) + '</div>' +
    '<div style="display:flex;justify-content:center;">' + svg + '</div>' +
    legend +
    '</div>'
  );
};

// ── badge_showcase ────────────────────────────────────────────────────────────
// Badge wall — earned badges glow/animate, locked badges are greyed.
// Each badge checks its required_id against progress_store.
_RENDERERS['badge_showcase'] = function(b) {
  var uid    = 'bshow' + Math.random().toString(36).substr(2, 6);
  var title  = b.title  || 'Achievements';
  var badges = b.badges || [];
  var cols   = Math.min(parseInt(b.columns || 4), 6);

  var items = '';
  for (var i = 0; i < badges.length; i++) {
    var bg = badges[i];
    var reqId = bg.required_id || bg.id || ('badge' + i);
    items +=
      '<div id="' + uid + 'b' + i + '" data-req="' + _esc(reqId) + '" ' +
        'style="display:flex;flex-direction:column;align-items:center;gap:6px;padding:16px 10px;border-radius:12px;text-align:center;' +
          'background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);transition:all 0.3s;">' +
        '<div id="' + uid + 'i' + i + '" style="font-size:2rem;filter:grayscale(1);opacity:0.25;transition:all 0.4s;">' + _esc(bg.icon || '🏅') + '</div>' +
        '<div style="font-size:0.65rem;font-weight:700;color:#334155;">' + _esc(bg.label || '') + '</div>' +
        (bg.description ? '<div style="font-size:0.58rem;color:#1e293b;line-height:1.3;">' + _esc(bg.description) + '</div>' : '') +
      '</div>';
  }

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;">' +
    '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#64748b;margin-bottom:14px;">🏆 ' + _esc(title) + '</div>' +
    '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:8px;">' + items + '</div>' +
    '<script>(function(){' +
      'var uid="' + uid + '";var count=' + badges.length + ';' +
      'function update(s){' +
        'for(var i=0;i<count;i++){' +
          'var w=document.getElementById(uid+"b"+i);var ic=document.getElementById(uid+"i"+i);if(!w||!s)continue;' +
          'if(s.isComplete(w.dataset.req)){' +
            'ic.style.filter="none";ic.style.opacity="1";' +
            'w.style.background="rgba(99,102,241,0.09)";w.style.borderColor="rgba(99,102,241,0.22)";w.style.boxShadow="0 0 24px rgba(99,102,241,0.12)";' +
          '}' +
        '}' +
      '}' +
      'document.addEventListener("a2ui:store",function(e){update(e.detail);});' +
      'update(window._A2UI_STORE||null);' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── learning_path_selector ────────────────────────────────────────────────────
// Path chooser at course entry — learner picks a role/level path.
// Stores choice in progress_store and optionally navigates to path url.
_RENDERERS['learning_path_selector'] = function(b) {
  var uid   = 'lps' + Math.random().toString(36).substr(2, 6);
  var title = b.title || 'Choose Your Path';
  var intro = b.intro || 'Select the learning path that best matches your role and goals.';
  var paths = b.paths || [];

  var cards = '';
  for (var i = 0; i < paths.length; i++) {
    var p  = paths[i];
    var ac = p.accent || '#6366f1';
    cards +=
      '<div id="' + uid + 'p' + i + '" onclick="' + uid + 'pick(' + i + ')" ' +
        'style="border-radius:14px;padding:22px 18px;cursor:pointer;transition:all 0.2s;' +
          'background:rgba(255,255,255,0.03);border:2px solid rgba(255,255,255,0.08);' +
          'display:flex;flex-direction:column;gap:10px;"' +
        ' onmouseover="if(!this.dataset.sel){this.style.borderColor=\'' + ac + '55\';this.style.background=\'' + ac + '0d\';}"' +
        ' onmouseout="if(!this.dataset.sel){this.style.borderColor=\'rgba(255,255,255,0.08)\';this.style.background=\'rgba(255,255,255,0.03)\'}">' +
        '<span style="font-size:2rem;">' + _esc(p.icon || '🎯') + '</span>' +
        '<div style="font-size:0.92rem;font-weight:700;color:#f1f5f9;">' + _esc(p.label || '') + '</div>' +
        (p.description ? '<div style="font-size:0.72rem;color:#64748b;line-height:1.5;">' + _esc(p.description) + '</div>' : '') +
        (p.duration ? '<div style="font-size:0.62rem;color:#475569;margin-top:auto;">⏱ ' + _esc(p.duration) + '</div>' : '') +
      '</div>';
  }

  var lpsBase = _getWebAppUrl();
  var pathsJson = JSON.stringify(paths.map(function(p) {
    var purl = p.url || '';
    if (purl && purl.charAt(0) === '?' && lpsBase) purl = lpsBase + purl;
    return { id: p.id || p.label, url: purl, accent: p.accent || '#6366f1' };
  }));

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;">' +
    '<div style="margin-bottom:20px;">' +
      '<div style="font-size:1.1rem;font-weight:800;color:#f1f5f9;margin-bottom:6px;">' + _esc(title) + '</div>' +
      '<div style="font-size:0.78rem;color:#64748b;">' + _esc(intro) + '</div>' +
    '</div>' +
    '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;">' + cards + '</div>' +
    '<div id="' + uid + 'msg" style="display:none;margin-top:14px;padding:12px 16px;border-radius:8px;background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.2);font-size:0.75rem;color:#34d399;"></div>' +
    '<script>(function(){' +
      'var ps=' + pathsJson + ';' +
      'window["' + uid + 'pick"]=function(i){' +
        'var p=ps[i];' +
        'ps.forEach(function(pp,j){var c=document.getElementById("' + uid + 'p"+j);if(!c)return;' +
          'if(j===i){c.dataset.sel="1";c.style.borderColor=p.accent;c.style.background=p.accent+"15";}' +
          'else{c.style.opacity="0.4";c.style.cursor="default";c.onmouseover=null;c.onmouseout=null;}' +
        '});' +
        'var msg=document.getElementById("' + uid + 'msg");if(msg){msg.style.display="block";msg.textContent="✓ Path selected: "+p.id+". Your curriculum has been personalised.";}' +
        'if(window._A2UI_STORE)window._A2UI_STORE.setPath(p.id);' +
        'if(p.url){setTimeout(function(){var a=document.createElement("a");a.href=p.url;a.target="_top";document.body.appendChild(a);a.click();},900);}' +
      '};' +
      // Pre-select if path already stored
      'document.addEventListener("a2ui:store",function(e){' +
        'var cur=e.detail.getPath();if(!cur)return;' +
        'ps.forEach(function(p,j){if(p.id===cur){var c=document.getElementById("' + uid + 'p"+j);if(c)c.dataset.sel="1";}});' +
      '});' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── flashcard_deck ────────────────────────────────────────────────────────────
// Zero-infra flip-card study deck. Works standalone or as a playbook slide.
// Schema: cards [{front, back}], accent (hex), label_front, label_back
_RENDERERS['flashcard_deck'] = function(b) {
  var cards      = b.cards        || [];
  var accent     = b.accent       || '#6366f1';
  var lblFront   = b.label_front  || 'QUESTION';
  var lblBack    = b.label_back   || 'RÉPONSE';
  var uid        = 'fcd' + Math.random().toString(36).substr(2, 8);

  if (!cards.length) return '<p style="color:#64748b;font-style:italic;text-align:center;">No flashcards provided.</p>';

  var cardsHtml = '';
  for (var i = 0; i < cards.length; i++) {
    var front = _esc(cards[i].front || '').replace(/\n/g, '<br>');
    var back  = _esc(cards[i].back  || '').replace(/\n/g, '<br>');
    var show  = i === 0 ? 'opacity:1;pointer-events:auto;transform:scale(1);' : 'opacity:0;pointer-events:none;transform:scale(0.96);';
    cardsHtml +=
      '<div class="' + uid + 'w" data-idx="' + i + '" style="position:absolute;inset:0;transition:opacity 0.3s,transform 0.3s;' + show + '">' +
        '<div class="' + uid + 'i" style="position:relative;width:100%;height:100%;' +
          'transform-style:preserve-3d;transition:transform 0.6s cubic-bezier(0.4,0,0.2,1);cursor:pointer;">' +
          '<div style="position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden;' +
            'display:flex;flex-direction:column;justify-content:center;align-items:center;padding:2rem;' +
            'border-radius:18px;box-sizing:border-box;text-align:center;' +
            'background:rgba(15,23,42,0.97);border:1px solid rgba(255,255,255,0.09);' +
            'box-shadow:0 24px 48px rgba(0,0,0,0.5);">' +
            '<div style="font-size:0.55rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:#334155;margin-bottom:1.2rem;">' + _esc(lblFront) + '</div>' +
            '<div style="font-size:1.1rem;font-weight:600;line-height:1.6;color:#f1f5f9;">' + front + '</div>' +
            '<div style="position:absolute;bottom:1.1rem;font-size:0.62rem;color:#1e293b;letter-spacing:0.1em;">— espace / clic pour retourner —</div>' +
          '</div>' +
          '<div style="position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden;' +
            'transform:rotateY(180deg);' +
            'display:flex;flex-direction:column;justify-content:center;align-items:center;padding:2rem;' +
            'border-radius:18px;box-sizing:border-box;text-align:center;' +
            'background:' + _esc(accent) + ';box-shadow:0 24px 48px rgba(0,0,0,0.5);">' +
            '<div style="font-size:0.55rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.45);margin-bottom:1.2rem;">' + _esc(lblBack) + '</div>' +
            '<div style="font-size:1.05rem;font-weight:600;line-height:1.65;color:#fff;">' + back + '</div>' +
            '<div style="position:absolute;bottom:1.1rem;font-size:0.62rem;color:rgba(255,255,255,0.25);letter-spacing:0.1em;">— espace / clic pour retourner —</div>' +
          '</div>' +
        '</div>' +
      '</div>';
  }

  var n = cards.length;
  var firstPct = n > 1 ? Math.round(100 / n) : 100;

  return (
    '<div id="' + uid + '" style="display:flex;flex-direction:column;align-items:center;' +
      'width:100%;max-width:580px;margin:2rem auto;font-family:\'Inter\',system-ui,sans-serif;">' +
      '<div style="width:100%;display:flex;align-items:center;gap:12px;margin-bottom:1.2rem;">' +
        '<div style="flex:1;height:3px;background:rgba(255,255,255,0.07);border-radius:2px;">' +
          '<div id="' + uid + 'bar" style="height:100%;width:' + firstPct + '%;background:' + _esc(accent) + ';border-radius:2px;transition:width 0.35s;"></div>' +
        '</div>' +
        '<span id="' + uid + 'ctr" style="font-size:0.68rem;color:#475569;font-weight:700;white-space:nowrap;min-width:44px;text-align:right;">1 / ' + n + '</span>' +
      '</div>' +
      '<div style="position:relative;width:100%;height:300px;perspective:1200px;">' +
        cardsHtml +
      '</div>' +
      '<div style="display:flex;align-items:center;gap:10px;margin-top:1.4rem;">' +
        '<button id="' + uid + 'P" onclick="window[\'' + uid + '\'].prev()" disabled ' +
          'style="padding:8px 18px;border-radius:8px;border:1px solid rgba(255,255,255,0.08);' +
          'background:rgba(255,255,255,0.04);color:#64748b;cursor:pointer;font-size:0.78rem;font-weight:600;">← Préc.</button>' +
        '<button onclick="window[\'' + uid + '\'].flip()" ' +
          'style="padding:8px 22px;border-radius:8px;border:none;background:' + _esc(accent) + ';' +
          'color:#fff;cursor:pointer;font-size:0.78rem;font-weight:700;">Retourner</button>' +
        '<button id="' + uid + 'N" onclick="window[\'' + uid + '\'].next()" ' +
          'style="padding:8px 18px;border-radius:8px;border:1px solid rgba(255,255,255,0.08);' +
          'background:rgba(255,255,255,0.04);color:#94a3b8;cursor:pointer;font-size:0.78rem;font-weight:600;">Suiv. →</button>' +
      '</div>' +
    '</div>' +
    '<script>(function(){' +
      'var idx=0,tot=' + n + ';' +
      'window["' + uid + '"]={' +
        'flip:function(){' +
          'var w=document.querySelector("#' + uid + ' .' + uid + 'w[data-idx=\'"+idx+"\']");' +
          'if(!w)return;' +
          'var inn=w.querySelector(".' + uid + 'i");' +
          'inn.style.transform=inn.style.transform?"":"rotateY(180deg)";' +
        '},' +
        'go:function(n){' +
          'if(n<0||n>=tot)return;' +
          'document.querySelectorAll("#' + uid + ' .' + uid + 'w").forEach(function(w){' +
            'w.style.opacity="0";w.style.pointerEvents="none";w.style.transform="scale(0.96)";' +
            'var i=w.querySelector(".' + uid + 'i");if(i)i.style.transform="";' +
          '});' +
          'idx=n;' +
          'var a=document.querySelector("#' + uid + ' .' + uid + 'w[data-idx=\'"+idx+"\']");' +
          'if(a){a.style.opacity="1";a.style.pointerEvents="auto";a.style.transform="scale(1)";}' +
          'var pb=document.getElementById("' + uid + 'bar");if(pb)pb.style.width=Math.round((idx+1)/tot*100)+"%";' +
          'var ct=document.getElementById("' + uid + 'ctr");if(ct)ct.textContent=(idx+1)+" / "+tot;' +
          'var pv=document.getElementById("' + uid + 'P");if(pv)pv.disabled=(idx===0);' +
          'var nx=document.getElementById("' + uid + 'N");if(nx)nx.disabled=(idx===tot-1);' +
        '},' +
        'next:function(){window["' + uid + '"].go(idx+1);},' +
        'prev:function(){window["' + uid + '"].go(idx-1);}' +
      '};' +
      'document.querySelectorAll("#' + uid + ' .' + uid + 'i").forEach(function(el){' +
        'el.addEventListener("click",function(){window["' + uid + '"].flip();});' +
      '});' +
      'document.addEventListener("keydown",function(e){' +
        'var el=document.getElementById("' + uid + '");if(!el)return;' +
        'var r=el.getBoundingClientRect();' +
        'if(r.bottom<0||r.top>window.innerHeight)return;' +
        'if(e.key==="ArrowRight"||e.key==="ArrowDown")window["' + uid + '"].next();' +
        'else if(e.key==="ArrowLeft"||e.key==="ArrowUp")window["' + uid + '"].prev();' +
        'else if(e.key===" "||e.key==="Enter"){window["' + uid + '"].flip();e.preventDefault();}' +
      '});' +
    '})();<\/script>'
  );
};
