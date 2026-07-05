// atoms_lms2.gs — Enterprise LMS atoms batch 2

// ── video_checkpoint ──────────────────────────────────────────────────────────
// YouTube video with quiz questions injected at specified timestamps.
// Video pauses at each checkpoint; learner must answer before playback resumes.
_RENDERERS['video_checkpoint'] = function(b) {
  var uid    = 'vpc' + Math.random().toString(36).substr(2, 6);
  var ytId   = b.youtube_id   || '';
  var title  = b.title        || '';
  var cps    = b.checkpoints  || [];

  var cpJson = JSON.stringify(cps.map(function(cp) {
    return {
      at:   parseInt(cp.at_seconds || 0),
      q:    cp.question    || '',
      opts: cp.options     || [],
      cor:  parseInt(cp.correct || 0),
      ex:   cp.explanation || '',
      done: false
    };
  }));

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;">' +
    (title ? '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#64748b;margin-bottom:10px;">🎬 ' + _esc(title) + '</div>' : '') +
    '<div style="position:relative;border-radius:12px;overflow:hidden;background:#000;aspect-ratio:16/9;">' +
      '<div id="' + uid + 'player" style="width:100%;height:100%;"></div>' +
      '<div id="' + uid + 'ov" style="display:none;position:absolute;inset:0;background:rgba(10,12,24,0.95);' +
        'backdrop-filter:blur(6px);align-items:center;justify-content:center;padding:24px;box-sizing:border-box;">' +
        '<div style="width:100%;max-width:460px;">' +
          '<div style="font-size:0.58rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#f59e0b;margin-bottom:12px;">⏸ Checkpoint</div>' +
          '<div id="' + uid + 'qq" style="font-size:0.9rem;font-weight:600;color:#f1f5f9;line-height:1.5;margin-bottom:14px;"></div>' +
          '<div id="' + uid + 'qo"></div>' +
          '<div id="' + uid + 'fb" style="display:none;margin-top:10px;padding:10px 14px;border-radius:8px;font-size:0.75rem;line-height:1.5;"></div>' +
          '<button id="' + uid + 'go" style="display:none;margin-top:12px;padding:9px 20px;border-radius:8px;' +
            'background:#34d399;color:#0f172a;font-size:0.75rem;font-weight:700;cursor:pointer;border:none;" ' +
            'onclick="' + uid + 'resume()">Continue ▶</button>' +
        '</div>' +
      '</div>' +
    '</div>' +
    '<script>(function(){' +
      'var uid="' + uid + '";' +
      'var cps=' + cpJson + ';' +
      'var player,poll;' +
      'function init(){' +
        'player=new YT.Player(uid+"player",{' +
          'videoId:"' + _esc(ytId) + '",' +
          'width:"100%",height:"100%",' +
          'playerVars:{rel:0,modestbranding:1,iv_load_policy:3},' +
          'events:{onStateChange:function(e){' +
            'if(e.data===YT.PlayerState.PLAYING){poll=setInterval(tick,700);}' +
            'else{clearInterval(poll);}' +
          '}}' +
        '});' +
      '}' +
      'function tick(){' +
        'if(!player||!player.getCurrentTime)return;' +
        'var t=player.getCurrentTime();' +
        'for(var i=0;i<cps.length;i++){if(!cps[i].done&&t>=cps[i].at&&t<cps[i].at+2){showCp(i);break;}}' +
      '}' +
      'function showCp(i){' +
        'clearInterval(poll);player.pauseVideo();' +
        'var cp=cps[i];' +
        'document.getElementById(uid+"qq").textContent=cp.q;' +
        'var qo=document.getElementById(uid+"qo");qo.innerHTML="";' +
        'cp.opts.forEach(function(opt,j){' +
          'var btn=document.createElement("button");' +
          'btn.textContent=String.fromCharCode(65+j)+"  "+opt;' +
          'btn.style.cssText="display:block;width:100%;text-align:left;padding:10px 14px;border-radius:8px;' +
            'margin-bottom:7px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.09);' +
            'color:#cbd5e1;font-size:0.78rem;cursor:pointer;";' +
          'btn.onclick=function(){' +
            'qo.querySelectorAll("button").forEach(function(b,k){' +
              'b.disabled=true;' +
              'if(k===cp.cor){b.style.background="rgba(52,211,153,0.12)";b.style.color="#34d399";}' +
              'else if(k===j&&j!==cp.cor){b.style.background="rgba(248,113,113,0.1)";b.style.color="#f87171";}' +
              'else{b.style.opacity="0.3";}' +
            '});' +
            'var fb=document.getElementById(uid+"fb");' +
            'fb.style.display="block";' +
            'fb.style.background=j===cp.cor?"rgba(52,211,153,0.09)":"rgba(248,113,113,0.09)";' +
            'fb.style.color=j===cp.cor?"#34d399":"#f87171";' +
            'fb.textContent=(j===cp.cor?"✓ Correct! ":"✗ Not quite — ")+cp.ex;' +
            'cps[i].done=true;' +
            'document.getElementById(uid+"go").style.display="block";' +
          '};' +
          'qo.appendChild(btn);' +
        '});' +
        'document.getElementById(uid+"fb").style.display="none";' +
        'document.getElementById(uid+"go").style.display="none";' +
        'var ov=document.getElementById(uid+"ov");ov.style.display="flex";' +
      '}' +
      'window["' + uid + 'resume"]=function(){' +
        'document.getElementById(uid+"ov").style.display="none";' +
        'player.playVideo();' +
      '};' +
      'if(window.YT&&window.YT.Player){init();}' +
      'else{var s=document.createElement("script");s.src="https://www.youtube.com/iframe_api";' +
        'document.head.appendChild(s);' +
        'var prev=window.onYouTubeIframeAPIReady;' +
        'window.onYouTubeIframeAPIReady=function(){if(prev)prev();init();};}' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── cohort_progress_board ─────────────────────────────────────────────────────
// Instructor-only view: table of all enrolled learners with module completion
// and average score. Reads live from the progress Sheet on GAS; static items[] on web.
_RENDERERS['cohort_progress_board'] = function(b) {
  var courseId = b.course_id || 'default';
  var title    = b.title     || 'Cohort Progress';
  var mods     = b.modules   || [];
  var rows     = [];

  if (typeof SpreadsheetApp !== 'undefined') {
    try { rows = a2uiCohortRead(courseId) || []; } catch(e) {}
  } else {
    rows = b.items || [
      {email:'alice@example.com', progress:{'done:mod1':true,'done:mod2':true,'score:quiz1':92}, updated_at:'2026-06-20'},
      {email:'bob@example.com',   progress:{'done:mod1':true,'score:quiz1':78},                  updated_at:'2026-06-19'},
      {email:'carol@example.com', progress:{},                                                   updated_at:'2026-06-18'}
    ];
  }

  var thStyle = 'text-align:left;padding:10px 12px;font-size:0.6rem;font-weight:700;letter-spacing:0.08em;color:#475569;text-transform:uppercase;border-bottom:1px solid rgba(255,255,255,0.07);white-space:nowrap;';
  var modThs = mods.map(function(m) {
    return '<th style="' + thStyle + 'text-align:center;">' + _esc(m.label || m.id || '') + '</th>';
  }).join('');

  var dataRows = rows.map(function(r) {
    var prog = r.progress || {};
    var name = (r.email || '?').split('@')[0];
    var init = name.charAt(0).toUpperCase();
    var doneCount = mods.filter(function(m) { return prog['done:' + m.id]; }).length;
    var pct  = mods.length ? Math.round((doneCount / mods.length) * 100) : null;
    var scores = Object.keys(prog).filter(function(k) { return k.indexOf('score:') === 0; }).map(function(k) { return prog[k]; });
    var avg  = scores.length ? Math.round(scores.reduce(function(a, b) { return a + b; }, 0) / scores.length) : null;
    var last = r.updated_at ? new Date(r.updated_at).toLocaleDateString('en-GB', {day:'numeric', month:'short'}) : '—';
    var tdS  = 'padding:9px 12px;border-bottom:1px solid rgba(255,255,255,0.04);';

    var modTds = mods.map(function(m) {
      var done = !!prog['done:' + m.id];
      return '<td style="' + tdS + 'text-align:center;">' +
        (done ? '<span style="color:#34d399;">✓</span>' : '<span style="color:#1e293b;">·</span>') +
        '</td>';
    }).join('');

    return '<tr>' +
      '<td style="' + tdS + '">' +
        '<div style="display:flex;align-items:center;gap:8px;">' +
          '<div style="width:28px;height:28px;border-radius:50%;background:#6366f1;flex-shrink:0;' +
            'display:flex;align-items:center;justify-content:center;font-size:0.68rem;font-weight:700;color:#fff;">' + init + '</div>' +
          '<span style="font-size:0.75rem;color:#e2e8f0;">' + _esc(name) + '</span>' +
        '</div>' +
      '</td>' +
      modTds +
      (pct !== null ? '<td style="' + tdS + 'text-align:center;"><span style="font-size:0.72rem;font-weight:700;color:' + (pct >= 80 ? '#34d399' : '#f59e0b') + ';">' + pct + '%</span></td>' : '<td style="' + tdS + 'text-align:center;color:#334155;font-size:0.72rem;">—</td>') +
      (avg !== null ? '<td style="' + tdS + 'text-align:center;"><span style="font-size:0.72rem;font-weight:700;color:' + (avg >= 70 ? '#34d399' : '#f87171') + ';">' + avg + '%</span></td>' : '<td style="' + tdS + 'text-align:center;color:#334155;font-size:0.72rem;">—</td>') +
      '<td style="' + tdS + 'text-align:right;font-size:0.68rem;color:#475569;">' + _esc(last) + '</td>' +
      '</tr>';
  }).join('');

  var active = rows.filter(function(r) { return Object.keys(r.progress || {}).length > 0; }).length;

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;">' +
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">' +
      '<span style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#64748b;">👥 ' + _esc(title) + '</span>' +
      '<div style="margin-left:auto;display:flex;gap:16px;">' +
        '<div style="text-align:center;"><div style="font-size:1.1rem;font-weight:800;color:#f1f5f9;">' + rows.length + '</div><div style="font-size:0.58rem;color:#475569;">Enrolled</div></div>' +
        '<div style="text-align:center;"><div style="font-size:1.1rem;font-weight:800;color:#34d399;">' + active + '</div><div style="font-size:0.58rem;color:#475569;">Active</div></div>' +
      '</div>' +
    '</div>' +
    '<div style="overflow-x:auto;border-radius:10px;border:1px solid rgba(255,255,255,0.07);">' +
    '<table style="width:100%;border-collapse:collapse;">' +
    '<thead><tr>' +
      '<th style="' + thStyle + '">Learner</th>' + modThs +
      '<th style="' + thStyle + 'text-align:center;">Progress</th>' +
      '<th style="' + thStyle + 'text-align:center;">Score</th>' +
      '<th style="' + thStyle + 'text-align:right;">Last active</th>' +
    '</tr></thead>' +
    '<tbody>' + (dataRows || '<tr><td colspan="10" style="padding:20px;text-align:center;color:#334155;font-size:0.75rem;">No learners yet.</td></tr>') + '</tbody>' +
    '</table></div></div>'
  );
};

// ── reflection_prompt ─────────────────────────────────────────────────────────
// Structured free-text reflection textarea. Saves response to progress_store
// keyed by prompt_id. On GAS this persists to the user's progress Sheet.
_RENDERERS['reflection_prompt'] = function(b) {
  var uid    = 'rp' + Math.random().toString(36).substr(2, 6);
  var prompt = b.prompt      || 'What was the most important thing you learned?';
  var pid    = b.prompt_id   || 'reflection';
  var ph     = b.placeholder || 'Write your reflection here…';
  var accent = b.accent      || '#6366f1';

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;padding:20px;border-radius:12px;' +
      'background:rgba(99,102,241,0.04);border:1px solid rgba(99,102,241,0.12);">' +
    '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:' + _esc(accent) + ';margin-bottom:10px;">✍️ Reflection</div>' +
    '<div style="font-size:0.88rem;font-weight:600;color:#f1f5f9;line-height:1.5;margin-bottom:14px;">' + _esc(prompt) + '</div>' +
    '<textarea id="' + uid + 'ta" placeholder="' + _esc(ph) + '" ' +
      'style="width:100%;min-height:90px;padding:12px;border-radius:9px;box-sizing:border-box;' +
        'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);' +
        'color:#e2e8f0;font-size:0.8rem;font-family:Inter,sans-serif;line-height:1.6;resize:vertical;outline:none;" ' +
      'onfocus="this.style.borderColor=\'' + _esc(accent) + '55\'" onblur="this.style.borderColor=\'rgba(255,255,255,0.1)\'"></textarea>' +
    '<div style="display:flex;align-items:center;gap:10px;margin-top:10px;">' +
      '<button id="' + uid + 'btn" onclick="' + uid + 'sub()" ' +
        'style="padding:9px 20px;border-radius:8px;background:' + _esc(accent) + ';color:#fff;font-size:0.75rem;font-weight:700;cursor:pointer;border:none;">' +
        'Submit</button>' +
      '<span id="' + uid + 'st" style="font-size:0.72rem;color:#475569;"></span>' +
    '</div>' +
    '<script>(function(){' +
      'var key="reflect:' + pid.replace(/"/g,'\\"') + '";' +
      'window["' + uid + 'sub"]=function(){' +
        'var ta=document.getElementById("' + uid + 'ta");' +
        'var st=document.getElementById("' + uid + 'st");' +
        'var btn=document.getElementById("' + uid + 'btn");' +
        'var txt=ta?ta.value.trim():"";' +
        'if(!txt){st.textContent="Please write something first.";st.style.color="#f87171";return;}' +
        'btn.disabled=true;btn.textContent="Saving…";' +
        'if(window._A2UI_STORE){' +
          'window._A2UI_STORE.set(key,txt,function(){' +
            'st.textContent="✓ Saved";st.style.color="#34d399";btn.textContent="Submitted";' +
          '});' +
        '}else{st.textContent="✓ Noted";st.style.color="#34d399";btn.textContent="Submitted";}' +
      '};' +
      // Restore if already answered
      'document.addEventListener("a2ui:store",function(e){' +
        'var v=e.detail.get(key);' +
        'if(v){var ta=document.getElementById("' + uid + 'ta");if(ta)ta.value=v;' +
          'var st=document.getElementById("' + uid + 'st");if(st){st.textContent="Previously saved";st.style.color="#64748b";}}' +
      '},{once:true});' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── annotation_highlight ──────────────────────────────────────────────────────
// Body text with clickable highlighted terms that reveal inline explanations.
// No state required. Pure CSS/JS enriched reading experience.
_RENDERERS['annotation_highlight'] = function(b) {
  var uid   = 'anhl' + Math.random().toString(36).substr(2, 6);
  var text  = b.text  || '';
  var notes = b.notes || [];

  // Server-side: replace annotated terms in text with tagged spans
  var out = _esc(text);
  for (var i = 0; i < notes.length; i++) {
    var n   = notes[i];
    var col = n.color || '#f59e0b';
    var esc_term = n.term.replace(/[&<>"']/g, function(c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
    out = out.replace(esc_term,
      '<span class="' + uid + 'a" data-i="' + i + '" onclick="' + uid + 'show(' + i + ',this)" ' +
        'style="background:' + col + '22;border-bottom:2px solid ' + col + ';color:' + col + ';' +
          'cursor:pointer;border-radius:3px;padding:0 3px;font-weight:600;">' +
        esc_term + '</span>'
    );
  }

  var notesJson = JSON.stringify(notes.map(function(n) {
    return { term: n.term, explanation: n.explanation || '', color: n.color || '#f59e0b' };
  }));

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;">' +
    '<div style="font-size:0.88rem;color:#cbd5e1;line-height:1.9;">' + out + '</div>' +
    '<div id="' + uid + 'panel" style="display:none;margin-top:12px;padding:14px 16px;border-radius:10px;' +
      'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.09);">' +
      '<div id="' + uid + 'pt" style="font-size:0.7rem;font-weight:700;margin-bottom:5px;"></div>' +
      '<div id="' + uid + 'pe" style="font-size:0.78rem;color:#94a3b8;line-height:1.6;"></div>' +
    '</div>' +
    '<script>(function(){' +
      'var ns=' + notesJson + ';var cur=-1;' +
      'window["' + uid + 'show"]=function(i,el){' +
        'var panel=document.getElementById("' + uid + 'panel");' +
        'if(cur===i){panel.style.display="none";cur=-1;return;}' +
        'cur=i;' +
        'document.querySelectorAll(".' + uid + 'a").forEach(function(s){s.style.background=ns[parseInt(s.dataset.i)||0].color+"22";});' +
        'el.style.background=ns[i].color+"44";' +
        'document.getElementById("' + uid + 'pt").textContent=ns[i].term;' +
        'document.getElementById("' + uid + 'pt").style.color=ns[i].color;' +
        'document.getElementById("' + uid + 'pe").textContent=ns[i].explanation;' +
        'panel.style.borderColor=ns[i].color+"44";panel.style.display="block";' +
      '};' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── onboarding_stepper ────────────────────────────────────────────────────────
// Guided first-time learner setup flow. Each step can link to a URL on completion.
// Completed steps marked in progress_store; restores state on revisit.
_RENDERERS['onboarding_stepper'] = function(b) {
  var uid    = 'obs' + Math.random().toString(36).substr(2, 6);
  var title  = b.title  || 'Get Started';
  var steps  = b.steps  || [];
  var accent = b.accent || '#6366f1';

  var ids     = JSON.stringify(steps.map(function(s, i) { return s.id || ('step' + i); }));
  var urls    = JSON.stringify(steps.map(function(s) { return s.action_url || ''; }));

  var stepHtml = '';
  for (var i = 0; i < steps.length; i++) {
    var s = steps[i];
    stepHtml +=
      '<div style="display:flex;gap:14px;padding:16px 0;' + (i < steps.length - 1 ? 'border-bottom:1px solid rgba(255,255,255,0.05);' : '') + '">' +
        '<div style="flex-shrink:0;display:flex;flex-direction:column;align-items:center;">' +
          '<div id="' + uid + 'ic' + i + '" style="width:36px;height:36px;border-radius:50%;transition:all 0.3s;' +
            'border:2px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.02);' +
            'display:flex;align-items:center;justify-content:center;font-size:0.82rem;color:#475569;">' +
            _esc(s.icon || String(i + 1)) + '</div>' +
          (i < steps.length - 1 ? '<div style="width:1px;flex:1;min-height:12px;margin-top:4px;background:rgba(255,255,255,0.06);"></div>' : '') +
        '</div>' +
        '<div style="flex:1;min-width:0;">' +
          '<div style="font-size:0.82rem;font-weight:700;color:#f1f5f9;margin-bottom:4px;">' + _esc(s.label || '') + '</div>' +
          (s.description ? '<div style="font-size:0.72rem;color:#64748b;line-height:1.5;margin-bottom:10px;">' + _esc(s.description) + '</div>' : '') +
          '<button id="' + uid + 'b' + i + '" onclick="' + uid + 'done(' + i + ')" ' +
            'style="padding:7px 16px;border-radius:7px;border:1px solid rgba(255,255,255,0.1);' +
              'background:rgba(255,255,255,0.04);color:#94a3b8;font-size:0.72rem;font-weight:600;cursor:pointer;transition:all 0.2s;">' +
            _esc(s.action_label || 'Mark complete') + '</button>' +
        '</div>' +
      '</div>';
  }

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;padding:20px;border-radius:14px;' +
      'background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);">' +
    '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#64748b;">🚀 ' + _esc(title) + '</div>' +
    '<div id="' + uid + 'pg" style="font-size:0.68rem;color:#334155;margin-bottom:16px;margin-top:3px;">0 / ' + steps.length + ' complete</div>' +
    stepHtml +
    '<script>(function(){' +
      'var ids=' + ids + ';var urls=' + urls + ';var n=' + steps.length + ';var done=0;' +
      'var ac="' + accent.replace(/"/g,'\\"') + '";' +
      'function tick(){document.getElementById("' + uid + 'pg").textContent=done+" / "+n+" complete";}' +
      'function markDone(i){' +
        'var btn=document.getElementById("' + uid + 'b"+i);' +
        'var ic=document.getElementById("' + uid + 'ic"+i);' +
        'if(btn&&!btn.dataset.done){btn.dataset.done="1";btn.disabled=true;btn.textContent="✓ Done";btn.style.background="rgba(52,211,153,0.1)";btn.style.borderColor="rgba(52,211,153,0.25)";btn.style.color="#34d399";done++;}' +
        'if(ic){ic.textContent="✓";ic.style.background=ac+"22";ic.style.borderColor=ac;ic.style.color=ac;}' +
        'tick();' +
      '}' +
      'window["' + uid + 'done"]=function(i){' +
        'markDone(i);' +
        'if(window._A2UI_STORE)window._A2UI_STORE.markComplete(ids[i]);' +
        'if(urls[i]){setTimeout(function(){var a=document.createElement("a");a.href=urls[i];a.target="_top";document.body.appendChild(a);a.click();},700);}' +
      '};' +
      'document.addEventListener("a2ui:store",function(e){' +
        'ids.forEach(function(id,i){if(e.detail.isComplete(id))markDone(i);});' +
      '},{once:true});' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── case_study_card ───────────────────────────────────────────────────────────
// Structured enterprise case study: situation, data points, analysis questions,
// and an optional reveal for the model answer. No state required.
_RENDERERS['case_study_card'] = function(b) {
  var uid       = 'csc' + Math.random().toString(36).substr(2, 6);
  var title     = b.title     || 'Case Study';
  var situation = b.situation || '';
  var dataPoints = b.data_points || [];
  var questions  = b.questions  || [];
  var answer     = b.model_answer || '';
  var accent     = b.accent    || '#38bdf8';

  var dpHtml = '';
  for (var i = 0; i < dataPoints.length; i++) {
    var dp = dataPoints[i];
    dpHtml +=
      '<div style="padding:10px 12px;border-radius:8px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);">' +
        '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#475569;margin-bottom:3px;">' + _esc(dp.label || '') + '</div>' +
        '<div style="font-size:0.88rem;font-weight:700;color:' + _esc(accent) + ';">' + _esc(dp.value || '') + '</div>' +
        (dp.note ? '<div style="font-size:0.62rem;color:#334155;margin-top:2px;">' + _esc(dp.note) + '</div>' : '') +
      '</div>';
  }

  var qHtml = '';
  for (var i = 0; i < questions.length; i++) {
    qHtml += '<div style="display:flex;gap:8px;margin-bottom:8px;">' +
      '<span style="color:' + _esc(accent) + ';font-weight:700;font-size:0.78rem;flex-shrink:0;">' + (i + 1) + '.</span>' +
      '<div style="font-size:0.78rem;color:#94a3b8;line-height:1.5;">' + _esc(questions[i]) + '</div>' +
    '</div>';
  }

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;border-radius:14px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);">' +
    // Header
    '<div style="padding:4px 20px;background:' + _esc(accent) + '18;border-bottom:1px solid rgba(255,255,255,0.06);">' +
      '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:' + _esc(accent) + ';margin-bottom:6px;margin-top:16px;">📋 Case Study</div>' +
      '<div style="font-size:1rem;font-weight:800;color:#f1f5f9;margin-bottom:16px;">' + _esc(title) + '</div>' +
    '</div>' +
    // Situation
    '<div style="padding:18px 20px;border-bottom:1px solid rgba(255,255,255,0.05);">' +
      '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#475569;margin-bottom:8px;">Situation</div>' +
      '<div style="font-size:0.82rem;color:#cbd5e1;line-height:1.7;">' + _esc(situation) + '</div>' +
    '</div>' +
    // Data points
    (dpHtml ? '<div style="padding:16px 20px;border-bottom:1px solid rgba(255,255,255,0.05);">' +
      '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#475569;margin-bottom:10px;">Key Data</div>' +
      '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;">' + dpHtml + '</div>' +
    '</div>' : '') +
    // Questions
    (qHtml ? '<div style="padding:16px 20px;' + (answer ? 'border-bottom:1px solid rgba(255,255,255,0.05);' : '') + '">' +
      '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#475569;margin-bottom:10px;">Analysis Questions</div>' +
      qHtml +
    '</div>' : '') +
    // Model answer reveal
    (answer ?
      '<div style="padding:16px 20px;">' +
        '<button onclick="var r=document.getElementById(\'' + uid + 'ans\');var b=document.getElementById(\'' + uid + 'revbtn\');r.style.display=r.style.display===\'none\'?\'block\':\'none\';b.textContent=r.style.display===\'none\'?\'Show model answer ▾\':\'Hide answer ▴\';" ' +
          'id="' + uid + 'revbtn" style="font-size:0.72rem;font-weight:600;color:#64748b;background:none;border:none;cursor:pointer;padding:0;">Show model answer ▾</button>' +
        '<div id="' + uid + 'ans" style="display:none;margin-top:12px;padding:14px 16px;border-radius:10px;' +
          'background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.18);">' +
          '<div style="font-size:0.72rem;color:#94a3b8;line-height:1.6;">' + _esc(answer) + '</div>' +
        '</div>' +
      '</div>' : '') +
    '</div>'
  );
};

// ── study_timer ───────────────────────────────────────────────────────────────
// Pomodoro-style focus/break timer. Session-scoped — no persistence required.
// Configurable focus duration, break duration, and accent colour.
_RENDERERS['study_timer'] = function(b) {
  var uid    = 'stmr' + Math.random().toString(36).substr(2, 6);
  var focus  = parseInt(b.focus_mins  || 25);
  var brk    = parseInt(b.break_mins  || 5);
  var accent = b.accent || '#6366f1';
  var label  = b.label  || 'Study Timer';

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;padding:24px;border-radius:14px;text-align:center;' +
      'background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);">' +
    '<div style="font-size:0.62rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#64748b;margin-bottom:16px;">⏱ ' + _esc(label) + '</div>' +
    // Mode label
    '<div id="' + uid + 'mode" style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:' + _esc(accent) + ';margin-bottom:8px;">Focus</div>' +
    // Timer display
    '<div id="' + uid + 'disp" style="font-size:3.5rem;font-weight:900;color:#f1f5f9;letter-spacing:-0.02em;line-height:1;margin-bottom:20px;">' + (focus < 10 ? '0' + focus : focus) + ':00</div>' +
    // Progress ring (SVG)
    '<div style="position:relative;display:inline-block;margin-bottom:20px;">' +
      '<svg width="100" height="100" viewBox="0 0 100 100">' +
        '<circle cx="50" cy="50" r="44" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="6"/>' +
        '<circle id="' + uid + 'ring" cx="50" cy="50" r="44" fill="none" stroke="' + _esc(accent) + '" stroke-width="6" ' +
          'stroke-dasharray="276.46" stroke-dashoffset="0" stroke-linecap="round" ' +
          'transform="rotate(-90 50 50)" style="transition:stroke-dashoffset 0.8s linear;"/>' +
      '</svg>' +
    '</div>' +
    // Controls
    '<div style="display:flex;gap:10px;justify-content:center;">' +
      '<button id="' + uid + 'start" onclick="' + uid + 'toggle()" ' +
        'style="padding:10px 28px;border-radius:99px;background:' + _esc(accent) + ';color:#fff;font-size:0.8rem;font-weight:700;cursor:pointer;border:none;min-width:100px;">Start</button>' +
      '<button onclick="' + uid + 'reset()" ' +
        'style="padding:10px 18px;border-radius:99px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#64748b;font-size:0.8rem;font-weight:600;cursor:pointer;">Reset</button>' +
    '</div>' +
    '<div id="' + uid + 'sessions" style="font-size:0.62rem;color:#334155;margin-top:12px;">0 sessions completed</div>' +
    '<script>(function(){' +
      'var focusSecs=' + (focus * 60) + ';var brkSecs=' + (brk * 60) + ';' +
      'var total=focusSecs;var left=focusSecs;var running=false;var timer=null;var isFocus=true;var sessions=0;' +
      'var CIRC=276.46;' +
      'function fmt(s){var m=Math.floor(s/60);var ss=s%60;return(m<10?"0":"")+m+":"+(ss<10?"0":"")+ss;}' +
      'function draw(){' +
        'document.getElementById("' + uid + 'disp").textContent=fmt(left);' +
        'var pct=left/total;' +
        'document.getElementById("' + uid + 'ring").setAttribute("stroke-dashoffset",CIRC*(1-pct));' +
        'document.getElementById("' + uid + 'mode").textContent=isFocus?"Focus":"Break";' +
        'document.getElementById("' + uid + 'mode").style.color=isFocus?"' + _esc(accent) + '":"#34d399";' +
      '}' +
      'function tick(){if(left<=0){if(isFocus)sessions++;isFocus=!isFocus;total=isFocus?focusSecs:brkSecs;left=total;document.getElementById("' + uid + 'sessions").textContent=sessions+" session"+(sessions===1?"":"s")+" completed";draw();return;}left--;draw();}' +
      'window["' + uid + 'toggle"]=function(){' +
        'var btn=document.getElementById("' + uid + 'start");' +
        'if(running){clearInterval(timer);running=false;btn.textContent="Resume";}' +
        'else{timer=setInterval(tick,1000);running=true;btn.textContent="Pause";}' +
      '};' +
      'window["' + uid + 'reset"]=function(){clearInterval(timer);running=false;isFocus=true;total=focusSecs;left=focusSecs;draw();document.getElementById("' + uid + 'start").textContent="Start";};' +
      'draw();' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── rubric_card ───────────────────────────────────────────────────────────────
// Grading rubric table — rows are criteria, columns are performance levels.
// Static display atom, no state required. Good for pre-assessment orientation.
_RENDERERS['rubric_card'] = function(b) {
  var title    = b.title    || 'Assessment Rubric';
  var levels   = b.levels   || ['Beginning', 'Developing', 'Proficient', 'Exemplary'];
  var criteria = b.criteria || [];
  var accent   = b.accent   || '#6366f1';

  var levelCols = levels.map(function(l, i) {
    var pct = Math.round(((i + 1) / levels.length) * 100);
    var col = i === levels.length - 1 ? '#34d399' : i >= levels.length - 2 ? accent : '#64748b';
    return '<th style="padding:10px 12px;text-align:center;font-size:0.6rem;font-weight:700;letter-spacing:0.08em;' +
      'text-transform:uppercase;color:' + col + ';border-bottom:1px solid rgba(255,255,255,0.07);min-width:100px;">' +
      _esc(l) + '</th>';
  }).join('');

  var rows = criteria.map(function(c) {
    var desc = c.descriptors || [];
    var cells = levels.map(function(l, i) {
      return '<td style="padding:10px 12px;font-size:0.72rem;color:#94a3b8;line-height:1.5;' +
        'border-bottom:1px solid rgba(255,255,255,0.04);vertical-align:top;text-align:center;">' +
        _esc(desc[i] || '—') + '</td>';
    }).join('');
    return '<tr>' +
      '<td style="padding:10px 12px;font-size:0.75rem;font-weight:600;color:#e2e8f0;' +
        'border-bottom:1px solid rgba(255,255,255,0.04);white-space:nowrap;vertical-align:top;">' +
        _esc(c.criterion || '') + '</td>' +
      cells + '</tr>';
  }).join('');

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;">' +
    '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#64748b;margin-bottom:12px;">📊 ' + _esc(title) + '</div>' +
    '<div style="overflow-x:auto;border-radius:10px;border:1px solid rgba(255,255,255,0.08);">' +
    '<table style="width:100%;border-collapse:collapse;">' +
    '<thead><tr>' +
      '<th style="padding:10px 12px;text-align:left;font-size:0.6rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#475569;border-bottom:1px solid rgba(255,255,255,0.07);">Criterion</th>' +
      levelCols +
    '</tr></thead>' +
    '<tbody>' + rows + '</tbody>' +
    '</table></div></div>'
  );
};

// ── spaced_repetition_card ────────────────────────────────────────────────────
// Flashcard with front/back flip and confidence rating 1-5.
// Logs rating to progress_store and computes a next-review hint.
_RENDERERS['spaced_repetition_card'] = function(b) {
  var uid   = 'spc' + Math.random().toString(36).substr(2, 6);
  var front = b.front   || 'Term or question';
  var back  = b.back    || 'Answer or definition';
  var cardId = b.card_id || ('card_' + Math.random().toString(36).substr(2, 6));
  var accent = b.accent  || '#a78bfa';

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;">' +
    // Card flip container
    '<div style="perspective:1000px;height:180px;cursor:pointer;margin-bottom:14px;" onclick="' + uid + 'flip()">' +
      '<div id="' + uid + 'card" style="position:relative;width:100%;height:100%;transition:transform 0.5s;transform-style:preserve-3d;">' +
        // Front
        '<div style="position:absolute;inset:0;border-radius:14px;padding:24px;box-sizing:border-box;' +
          'background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.2);' +
          'display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;' +
          'backface-visibility:hidden;-webkit-backface-visibility:hidden;">' +
          '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:' + _esc(accent) + ';margin-bottom:10px;">🃏 Tap to reveal</div>' +
          '<div style="font-size:0.96rem;font-weight:700;color:#f1f5f9;line-height:1.5;">' + _esc(front) + '</div>' +
        '</div>' +
        // Back
        '<div style="position:absolute;inset:0;border-radius:14px;padding:24px;box-sizing:border-box;' +
          'background:rgba(52,211,153,0.07);border:1px solid rgba(52,211,153,0.2);' +
          'display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;' +
          'backface-visibility:hidden;-webkit-backface-visibility:hidden;transform:rotateY(180deg);">' +
          '<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#34d399;margin-bottom:10px;">Answer</div>' +
          '<div style="font-size:0.88rem;color:#e2e8f0;line-height:1.6;">' + _esc(back) + '</div>' +
        '</div>' +
      '</div>' +
    '</div>' +
    // Confidence rating (shown after flip)
    '<div id="' + uid + 'rate" style="display:none;text-align:center;">' +
      '<div style="font-size:0.68rem;color:#64748b;margin-bottom:10px;">How well did you know this?</div>' +
      '<div style="display:flex;justify-content:center;gap:8px;">' +
        [1,2,3,4,5].map(function(n) {
          var labels = ['','Forgot','Hard','Okay','Good','Easy'];
          var cols   = ['','#f87171','#f59e0b','#facc15','#4ade80','#34d399'];
          return '<button onclick="' + uid + 'rate(' + n + ')" ' +
            'style="display:flex;flex-direction:column;align-items:center;gap:4px;padding:8px 12px;border-radius:9px;' +
              'background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);cursor:pointer;transition:all 0.15s;"' +
            ' onmouseover="this.style.borderColor=\'' + cols[n] + '44\';this.style.background=\'' + cols[n] + '11\'"' +
            ' onmouseout="if(!this.disabled){this.style.borderColor=\'rgba(255,255,255,0.08)\';this.style.background=\'rgba(255,255,255,0.03)\'}">' +
            '<span style="font-size:1rem;">' + ['','😰','😕','😐','🙂','😄'][n] + '</span>' +
            '<span style="font-size:0.6rem;color:#64748b;">' + labels[n] + '</span>' +
          '</button>';
        }).join('') +
      '</div>' +
      '<div id="' + uid + 'next" style="display:none;margin-top:12px;font-size:0.72rem;color:#64748b;"></div>' +
    '</div>' +
    '<script>(function(){' +
      'var flipped=false;var rated=false;' +
      'var cid="' + cardId.replace(/"/g,'\\"') + '";' +
      'window["' + uid + 'flip"]=function(){' +
        'if(rated)return;' +
        'flipped=!flipped;' +
        'document.getElementById("' + uid + 'card").style.transform=flipped?"rotateY(180deg)":"rotateY(0deg)";' +
        'if(flipped)document.getElementById("' + uid + 'rate").style.display="block";' +
      '};' +
      'window["' + uid + 'rate"]=function(n){' +
        'if(rated)return;rated=true;' +
        // Compute next review days: 1→1, 2→2, 3→4, 4→7, 5→14
        'var days=[0,1,2,4,7,14][n];' +
        'var nxt=document.getElementById("' + uid + 'next");' +
        'nxt.style.display="block";nxt.textContent="Next review: "+days+(days===1?" day":" days")+" from now";' +
        'document.querySelectorAll("#' + uid + 'rate button").forEach(function(b){b.disabled=true;b.style.opacity="0.4";});' +
        'if(window._A2UI_STORE)window._A2UI_STORE.set("srs:"+cid,{rating:n,next_days:days,rated_at:new Date().toISOString()});' +
      '};' +
    '})();<\/script>' +
    '</div>'
  );
};

// ── leaderboard_card ──────────────────────────────────────────────────────────
// Ranked list of learners by score. GAS reads from the course progress Sheet;
// web renders from static items[] array. Top 3 rows get medal indicators.
_RENDERERS['leaderboard_card'] = function(b) {
  var courseId = b.course_id || 'default';
  var title    = b.title     || 'Leaderboard';
  var scoreKey = b.score_key || 'quiz1';
  var limit    = Math.min(parseInt(b.limit || 10), 20);
  var rows     = [];

  if (typeof SpreadsheetApp !== 'undefined') {
    try {
      var cohort = a2uiCohortRead(courseId) || [];
      rows = cohort
        .map(function(r) {
          var score = r.progress && r.progress['score:' + scoreKey];
          return { name: (r.email || '?').split('@')[0], score: score != null ? parseInt(score) : null };
        })
        .filter(function(r) { return r.score !== null; })
        .sort(function(a, b) { return b.score - a.score; })
        .slice(0, limit);
    } catch(e) {}
  }
  if (!rows.length) {
    rows = b.items || [
      {name:'alice', score:94}, {name:'bob', score:87}, {name:'carol', score:81},
      {name:'dave', score:76}, {name:'eva', score:72}
    ];
  }

  var MEDALS = ['🥇','🥈','🥉'];
  var items = rows.map(function(r, i) {
    var isTop = i < 3;
    var barW  = rows[0] && rows[0].score > 0 ? Math.round((r.score / rows[0].score) * 100) : 0;
    var col   = i === 0 ? '#facc15' : i === 1 ? '#94a3b8' : i === 2 ? '#fb923c' : '#475569';
    return '<div style="display:flex;align-items:center;gap:10px;padding:10px 0;' + (i < rows.length - 1 ? 'border-bottom:1px solid rgba(255,255,255,0.04);' : '') + '">' +
      '<div style="width:24px;text-align:center;font-size:' + (isTop ? '1rem' : '0.72rem') + ';color:' + (isTop ? col : '#334155') + ';font-weight:700;flex-shrink:0;">' + (isTop ? MEDALS[i] : (i + 1)) + '</div>' +
      '<div style="flex:1;min-width:0;">' +
        '<div style="font-size:0.78rem;font-weight:600;color:#e2e8f0;">' + _esc(r.name) + '</div>' +
        '<div style="height:4px;border-radius:2px;background:rgba(255,255,255,0.05);margin-top:5px;">' +
          '<div style="height:100%;width:' + barW + '%;border-radius:2px;background:' + col + ';transition:width 0.6s;"></div>' +
        '</div>' +
      '</div>' +
      '<div style="font-size:0.82rem;font-weight:800;color:' + col + ';flex-shrink:0;">' + r.score + '%</div>' +
    '</div>';
  }).join('');

  return (
    '<div style="font-family:\'Inter\',system-ui,sans-serif;padding:18px;border-radius:14px;' +
      'background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);">' +
    '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#64748b;margin-bottom:14px;">🏆 ' + _esc(title) + '</div>' +
    items +
    '</div>'
  );
};
