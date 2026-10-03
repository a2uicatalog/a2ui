// atoms_studio.gs — the studio pack (2026-10-03): premium WebGL atoms that run on the film clock.
// Rules every atom here keeps (same model as motion_shader, see a2ui-private/briefs/webgl-spike-design.md):
//  1. Fixed code. The shader and driver are ONE top-level function per atom. GAS embeds it with Function.prototype.toString and the
//     Python twin (renderers/web_article.py) reads the same source text out of this file, so the browser code exists exactly once.
//  2. Config is numbers, colours parsed to 0-1 floats, enum indexes and (for 3D type) one JSON-escaped string. Nothing from the
//     payload becomes code.
//  3. Seekable. The frame is a pure function of the inherited --p and --s, read every animation frame, so seek(t) shows exactly
//     that frame. Standalone (no --p/--s) it runs on its own clock, or holds still under still:true or reduced motion.
//  4. Always a fallback: a CSS rendering of the same object under the canvas, shown when WebGL is missing, the context fails, the
//     page prints or the host strips scripts.
//  5. Robust: survives WebGL context loss (re-initialises on restore), draws only when time or size changed, stops off screen.

// ─── motion_object3d: a raymarched hero object ──────────────────────────────────────────────────────────────────────────────────
// Signed-distance shapes (sphere, torus, cube, pill, knot, blob, lattice, twist, rings) or extruded 3D type, in seven materials lit
// by a procedural photo studio (softboxes front, coloured rims behind, a backdrop the glass refracts). Two to four shapes morph into
// each other through the distance field as --p goes 0 to 1; --s turns it (turns per unit). Edges are anti-aliased from the ray's
// closest approach. 3D type: the text is drawn once to a 2D canvas, turned into a signed distance field (Felzenszwalb transform,
// sub-pixel initialisation from the glyph coverage) and extruded with a bevel.
function _moStudioObj(uid, C) {
  var r = document.getElementById('mt-' + uid); if (!r) return;
  var cv = r.querySelector('canvas'), gl = null;
  try { gl = cv.getContext('webgl', {alpha: true, premultipliedAlpha: true, antialias: false, preserveDrawingBuffer: true}); } catch (e) {}
  if (!gl) { cv.style.display = 'none'; return; }
  var VS = 'attribute vec2 a;void main(){gl_Position=vec4(a,0.0,1.0);}';
  var FS = [
    'precision highp float;',
    'uniform vec2 R;uniform float uSpin,uMorph,uTime,uA,uB,uMat,uFloor,uTilt,uZoom,uAsp,uDepth,uBg,uSd;',
    'uniform vec3 c1,c2,c3,cb;uniform sampler2D uTx;',
    '#define TAU 6.2831853',
    'mat2 rot(float a){float c=cos(a),s=sin(a);return mat2(c,-s,s,c);}',
    'float sdBox(vec3 p,vec3 b,float r){vec3 q=abs(p)-b+r;return length(max(q,0.0))+min(max(q.x,max(q.y,q.z)),0.0)-r;}',
    'float sdTor(vec3 p,vec2 t){vec2 q=vec2(length(p.xz)-t.x,p.y);return length(q)-t.y;}',
    'float sdText(vec3 p){float W=3.3,H=W/uAsp;float bx=sdBox(p,vec3(W*0.5,H*0.5,uDepth+0.04),0.0);if(bx>0.06)return bx;',
    ' vec2 uv=vec2(p.x/W+0.5,0.5-p.y/H);vec2 cl=clamp(uv,0.0,1.0);',
    ' float d2=(texture2D(uTx,cl).r-0.5)*uSd+length((uv-cl)*vec2(W,H));vec2 w=vec2(d2+0.05,abs(p.z)-uDepth+0.05);',
    ' return (min(max(w.x,w.y),0.0)+length(max(w,0.0))-0.05)*0.8;}',
    'float shp(vec3 p,float k){',
    ' if(k<0.5)return length(p)-1.0;',
    ' if(k<1.5)return sdTor(p.xzy,vec2(0.78,0.3));',
    ' if(k<2.5)return sdBox(p,vec3(0.78),0.16);',
    ' if(k<3.5){vec3 q=p;q.xy=rot(0.55)*q.xy;q.x-=clamp(q.x,-0.62,0.62);return length(q)-0.5;}',
    ' if(k<4.5){vec2 c=vec2(length(p.xz)-0.72,p.y);c=rot(atan(p.x,p.z)*1.5)*c;c.y=abs(c.y)-0.3;return (length(c)-0.15)*0.6;}',
    ' if(k<5.5){return (length(p)-0.95+0.11*sin(3.1*p.x+uTime*0.9)*sin(2.7*p.y+uTime*1.1)*sin(3.3*p.z+uTime*0.7))*0.8;}',
    ' if(k<6.5){vec3 q=p*4.2;float g=abs(dot(sin(q),cos(q.yzx)))/4.2-0.05;return max(length(p)-1.05,g*0.8);}',
    ' if(k<7.5){vec3 q=p;q.xz=rot(q.y*1.3)*q.xz;return sdBox(q,vec3(0.55,1.0,0.55),0.12)*0.8;}',
    ' if(k<8.5){float a=sdTor((p+vec3(0.36,0.0,0.0)).xzy,vec2(0.6,0.17));float b=sdTor(p-vec3(0.36,0.0,0.0),vec2(0.6,0.17));return min(a,b);}',
    ' return sdText(p);}',
    'vec3 xf(vec3 p){p.y-=0.05*sin(uTime*1.3);p.yz=rot(uTilt)*p.yz;p.xz=rot(uSpin)*p.xz;return p;}',
    'float map(vec3 p){vec3 q=xf(p);float m=smoothstep(0.0,1.0,uMorph);float a=shp(q,uA);if(m<0.001)return a;float b=shp(q,uB);return mix(a,b,m);}',
    'vec3 nrm(vec3 p){float ee=max(uA,uB)>8.5?0.0055:0.002;vec2 e=vec2(ee,-ee);return normalize(e.xyy*map(p+e.xyy)+e.yyx*map(p+e.yyx)+e.yxy*map(p+e.yxy)+e.xxx*map(p+e.xxx));}',
    'float sb(float a,float y,float ac,float w,float y0,float y1){return smoothstep(w,w*0.3,abs(a-ac))*smoothstep(y0-0.12,y0+0.12,y)*smoothstep(y1+0.12,y1-0.12,y)*(0.75+0.25*y);}',
    'vec3 env(vec3 d){float y=d.y,a=atan(d.x,d.z);',
    ' vec3 back=mix(cb*1.2,cb*0.5,clamp(length(d.xy)*0.85,0.0,1.0));',
    ' vec3 stu=mix(vec3(0.012),vec3(0.09)+cb*0.25,smoothstep(-0.7,0.9,y));',
    ' vec3 col=mix(stu,back,smoothstep(0.15,-0.45,d.z));',
    ' col+=vec3(1.0)*sb(a,y,0.68,0.36,-0.25,0.7)*2.6+vec3(1.0)*sb(a,y,-0.95,0.24,-0.1,0.55)*1.4;',
    ' col+=vec3(1.0)*smoothstep(0.62,0.95,y)*1.15+vec3(0.95,0.97,1.0)*smoothstep(1.1,0.15,abs(a+0.12))*smoothstep(-0.75,-0.1,y)*smoothstep(0.98,0.45,y)*(0.45+0.4*y);',
    ' col+=c2*sb(a,y,2.45,0.5,-0.5,0.5)*2.0+c3*sb(a,y,-2.45,0.5,-0.5,0.5)*2.0;',
    ' col+=mix(c2,c3,0.5)*0.12*smoothstep(0.0,-0.7,y);',
    ' return col;}',
    'float soft(vec3 ro,vec3 rd){float res=1.0,t=0.03;for(int i=0;i<28;i++){float h=map(ro+rd*t);res=min(res,9.0*h/t);t+=clamp(h,0.02,0.25);if(res<0.002||t>5.0)break;}return clamp(res,0.0,1.0);}',
    'float ao(vec3 p,vec3 n){float o=0.0,s=1.0;for(int i=1;i<6;i++){float h=0.06*float(i);o+=(h-map(p+n*h))*s;s*=0.6;}return clamp(1.0-2.2*o,0.0,1.0);}',
    'vec3 aces(vec3 x){return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.0,1.0);}',
    'vec3 shade(vec3 p,vec3 rd){vec3 L=normalize(vec3(-0.55,0.85,0.55));vec3 n=nrm(p),V=-rd,col;float nv=max(dot(n,V),0.0),fr=pow(1.0-nv,5.0);',
    ' vec3 rf=env(reflect(rd,n));',
    ' if(uMat<0.5){col=rf*mix(vec3(1.0),c1,0.3)*(0.55+0.45*fr)+rf*fr*0.6;}',
    ' else if(uMat<1.5){vec3 tr=vec3(env(refract(rd,n,0.7)).r,env(refract(rd,n,0.675)).g,env(refract(rd,n,0.65)).b);tr*=mix(vec3(1.0),c1,0.45+0.35*(1.0-nv));col=mix(tr*1.08,rf,0.05+0.95*fr)+rf*0.06+c1*0.03;}',
    ' else if(uMat<2.5){vec3 fl=0.62+0.38*cos(TAU*(vec3(0.0,0.33,0.67)+nv*1.3+0.12+uTime*0.03));col=rf*mix(vec3(1.0),fl,0.3+0.45*(1.0-nv))*mix(vec3(1.0),c1,0.2)+fl*0.04*(1.0-nv)+rf*fr*0.35;}',
    ' else if(uMat<3.5){float sh=soft(p+n*0.01,L),oc=ao(p,n);float df=clamp(dot(n,L)*0.8+0.2,0.0,1.0)*sh;col=c1*(df*1.05+(0.3+0.25*n.y)*oc*0.7)+c2*fr*0.25*oc+rf*0.03;}',
    ' else if(uMat<4.5){col=rf*c1*1.15*(0.6+0.4*fr)+rf*fr*0.5;}',
    ' else if(uMat<5.5){float oc=ao(p,n);vec3 fl=0.5+0.5*cos(TAU*(vec3(0.0,0.33,0.67)+nv*1.2));col=c1*(0.55+0.45*max(dot(n,L),0.0))*oc+fl*0.12*(1.0-nv)+rf*0.18*(0.3+fr);}',
    ' else{col=c1*0.03+rf*(0.035+0.965*fr)*mix(vec3(1.0),c1,0.15)+rf*0.025;}',
    ' return pow(aces(col*1.05),vec3(0.92));}',
    'void main(){vec2 uv=(gl_FragCoord.xy-0.5*R)/R.y;',
    ' vec3 ro=vec3(0.0,0.1,uZoom),rd=normalize(vec3(uv,-2.6));',
    ' float pk=1.0/(R.y*2.6),t=0.0,d=1.0,bm=1e9,bt=0.0;bool hit=false;',
    ' for(int i=0;i<128;i++){d=map(ro+rd*t);float rr=d/max(t*pk,1e-5);if(rr<bm){bm=rr;bt=t;}if(d<0.25*t*pk){hit=true;break;}t+=d*0.9;if(t>uZoom+4.0)break;}',
    ' float cov=hit?1.0:clamp(1.0-bm,0.0,1.0);',
    ' vec3 oc=vec3(0.0);if(cov>0.0)oc=shade(ro+rd*(hit?t:bt),rd);',
    ' float sa=0.0;if(uFloor>0.5&&cov<1.0&&rd.y<0.0){vec3 L=normalize(vec3(-0.55,0.85,0.55));float tf=(-1.18-ro.y)/rd.y;vec3 pf=ro+rd*tf;float sh=soft(pf+vec3(0.0,0.01,0.0),L);sa=(1.0-sh)*0.55*smoothstep(3.2,0.6,length(pf.xz));}',
    ' float pa=cov+sa*(1.0-cov);vec3 pc=oc*cov;',
    ' if(uBg>0.5){vec3 bg=mix(cb*1.15,cb*0.45,length(uv)*1.1);gl_FragColor=vec4(bg*(1.0-pa)+pc,1.0);}',
    ' else{gl_FragColor=vec4(pc,pa);}}'
  ].join('\n');
  function sh(ty, src) { var s = gl.createShader(ty); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) return null; return s; }
  var pg, u, tex, txd = null, dirty = true, lost = false;
  function init() {
  var vs = sh(gl.VERTEX_SHADER, VS), fs = sh(gl.FRAGMENT_SHADER, FS);
  if (!vs || !fs) return false;
  pg = gl.createProgram(); gl.attachShader(pg, vs); gl.attachShader(pg, fs); gl.linkProgram(pg);
  if (!gl.getProgramParameter(pg, gl.LINK_STATUS)) return false;
  gl.useProgram(pg);
  var bf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, bf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  var al = gl.getAttribLocation(pg, 'a'); gl.enableVertexAttribArray(al); gl.vertexAttribPointer(al, 2, gl.FLOAT, false, 0, 0);
  function U(nm) { return gl.getUniformLocation(pg, nm); }
  u = {}; ['R', 'uSpin', 'uMorph', 'uTime', 'uA', 'uB', 'uAsp', 'uSd'].forEach(function(k) { u[k] = U(k); });
  gl.uniform3fv(U('c1'), C.c1); gl.uniform3fv(U('c2'), C.c2); gl.uniform3fv(U('c3'), C.c3); gl.uniform3fv(U('cb'), C.cb);
  gl.uniform1f(U('uMat'), C.mat); gl.uniform1f(U('uFloor'), C.floor ? 1 : 0); gl.uniform1f(U('uTilt'), C.tilt * Math.PI / 180);
  gl.uniform1f(U('uZoom'), 8.0 / C.zoom); gl.uniform1f(U('uDepth'), C.depth); gl.uniform1f(U('uBg'), C.bg ? 1 : 0);
  gl.uniform1f(u.uAsp, 3); gl.uniform1f(u.uSd, 0.5);
  tex = gl.createTexture(); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, 1, 1, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE, new Uint8Array([255]));
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.uniform1i(U('uTx'), 0);
  if (txd) upTex(); dirty = true; return true;
  }
  function edt(f, w, h) {
    var g = new Float64Array(Math.max(w, h)), v = new Int32Array(Math.max(w, h)), z = new Float64Array(Math.max(w, h) + 1), INF = 1e20;
    function pass(n, get, set) {
      var k = 0, q, s; v[0] = 0; z[0] = -INF; z[1] = INF;
      for (q = 0; q < n; q++) g[q] = get(q);
      for (q = 1; q < n; q++) {
        do { var p = v[k]; s = ((g[q] + q * q) - (g[p] + p * p)) / (2 * q - 2 * p); } while (s <= z[k] && --k > -1);
        k++; v[k] = q; z[k] = s; z[k + 1] = INF;
      }
      for (k = 0, q = 0; q < n; q++) { while (z[k + 1] < q) k++; var d = q - v[k]; set(q, d * d + g[v[k]]); }
    }
    var x, y;
    for (x = 0; x < w; x++) pass(h, function(i) { return f[i * w + x]; }, function(i, val) { f[i * w + x] = val; });
    for (y = 0; y < h; y++) pass(w, function(i) { return f[y * w + i]; }, function(i, val) { f[y * w + i] = val; });
    return f;
  }
  function buildText() {
    var c2 = document.createElement('canvas'), x = c2.getContext('2d'), fs = 300;
    x.font = C.font.replace('%S', fs + 'px');
    var tw = Math.ceil(x.measureText(C.txt).width), pad = 70, w = Math.min(1600, tw + pad * 2), sc = w / (tw + pad * 2), h = Math.ceil((fs * 1.25 + pad * 2) * sc);
    c2.width = w; c2.height = h; x.font = C.font.replace('%S', Math.round(fs * sc) + 'px'); x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = '#fff';
    x.fillText(C.txt, w / 2, h / 2 + fs * sc * 0.06);
    var px = x.getImageData(0, 0, w, h).data, n = w * h, fo = new Float64Array(n), fi = new Float64Array(n), i;
    for (i = 0; i < n; i++) { var aa = px[i * 4 + 3] / 255; if (aa >= 1) { fo[i] = 0; fi[i] = 1e20; } else if (aa <= 0) { fo[i] = 1e20; fi[i] = 0; } else { var o1 = Math.max(0, 0.5 - aa), i1 = Math.max(0, aa - 0.5); fo[i] = o1 * o1; fi[i] = i1 * i1; } }
    edt(fo, w, h); edt(fi, w, h);
    var M = 44, out = new Uint8Array(n);
    for (i = 0; i < n; i++) { var dd = Math.sqrt(fo[i]) - Math.sqrt(fi[i]); out[i] = Math.max(0, Math.min(255, Math.round((0.5 + dd / (2 * M)) * 255))); }
    txd = {w: w, h: h, d: out, sd: 2 * M * 3.3 / w}; upTex(); dirty = true;
  }
  function upTex() {
    gl.bindTexture(gl.TEXTURE_2D, tex); gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, txd.w, txd.h, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE, txd.d);
    gl.uniform1f(u.uAsp, txd.w / txd.h); gl.uniform1f(u.uSd, txd.sd);
  }
  if (!init()) { cv.style.display = 'none'; return; }
  r.classList.add('gl');
  cv.addEventListener('webglcontextlost', function(e) { e.preventDefault(); lost = true; });
  cv.addEventListener('webglcontextrestored', function() { lost = false; lk = ''; if (!init()) cv.style.display = 'none'; });
  if (C.txt) {
    var fl = document.fonts && document.fonts.load ? document.fonts.load(C.font.replace('%S', '160px'), C.txt) : null;
    if (fl) { var done = false; fl.then(function() { if (!done) { done = true; buildText(); } }, function() { if (!done) { done = true; buildText(); } }); setTimeout(function() { if (!done) { done = true; buildText(); } }, 1500); }
    else buildText();
  }
  var t0 = performance.now(), lk = '', vis = true, red = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (window.IntersectionObserver) new IntersectionObserver(function(es) { vis = es[0].isIntersecting; }).observe(r);
  function num(nm) { var v = getComputedStyle(r).getPropertyValue(nm).trim(); return v === '' ? null : parseFloat(v); }
  function fr() {
    requestAnimationFrame(fr); if (!vis || lost) return;
    var d = Math.min(window.devicePixelRatio || 1, 1.5), w = Math.min(C.max, Math.round(cv.clientWidth * d)), hh = Math.round(w * cv.clientHeight / Math.max(1, cv.clientWidth));
    if (w < 2 || hh < 2) return;
    var s = num('--s'), p = num('--p'), clock = (C.still || red) ? 0 : (performance.now() - t0) / 1000 * C.speed;
    if (s === null || isNaN(s)) s = clock / Math.max(1, C.span);
    if (p === null || isNaN(p)) p = C.n > 1 ? 0.5 - 0.5 * Math.cos(clock * 0.6) : 1;
    var seg = Math.max(0, Math.min(C.n - 1, p * (C.n - 1))), i0 = Math.min(C.n - 2, Math.floor(seg)), m = seg - Math.max(0, i0);
    if (C.n < 2) { i0 = 0; m = 0; }
    var key = [w, hh, s, p, dirty].join('|'); if (key === lk) return; lk = key; dirty = false;
    if (cv.width !== w || cv.height !== hh) { cv.width = w; cv.height = hh; }
    gl.viewport(0, 0, w, hh);
    gl.uniform2f(u.R, w, hh); gl.uniform1f(u.uSpin, C.ang * Math.PI / 180 + s * C.turns * 6.2831853); gl.uniform1f(u.uTime, s * C.span);
    gl.uniform1f(u.uA, C.sh[i0]); gl.uniform1f(u.uB, C.sh[Math.min(C.n - 1, i0 + 1)]); gl.uniform1f(u.uMorph, m);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLES, 0, 3);
  }
  fr();
}

// ─── studio typefaces (2026-10-03): four OFL variable fonts whose AXES are the animation ────────────────────────────────────────
// recursive: code to display (MONO 1 is a monospace code face, MONO 0 a proportional sans), CASL casual, CRSV cursive, slnt, wght.
// anybody: width 50-150%. nabla: a COLRv1 colour font whose EDPT axis is extrusion depth (3D type in plain CSS), EHLT highlight.
// fraunces: an editorial serif with optical size, SOFT and WONK. Files are vendored at a2uicatalog.ai/vendors/fonts (latin subset
// from Google Fonts, SIL OFL 1.1, see THIRD-PARTY-NOTICES.md); each family also falls back to the same face loaded from Google
// Fonts by the page if present, then to a system stack. Axis ranges are the fonts' real fvar ranges.
var _MO_VFONT_BASE = 'https://a2uicatalog.ai/vendors/fonts/';
var _MO_VFONTS = {
  recursive: {fam: 'A2UI Recursive', stack: "'A2UI Recursive',Recursive,system-ui,sans-serif", file: 'recursive.woff2', desc: 'font-weight:300 1000;font-style:oblique 0deg 15deg;',
    axes: {wght: [300, 1000], MONO: [0, 1], CASL: [0, 1], slnt: [-15, 0], CRSV: [0, 1]}},
  anybody: {fam: 'A2UI Anybody', stack: "'A2UI Anybody',Anybody,system-ui,sans-serif", file: 'anybody.woff2', desc: 'font-weight:100 900;font-stretch:50% 150%;',
    axes: {wght: [100, 900], wdth: [50, 150]}},
  nabla: {fam: 'A2UI Nabla', stack: "'A2UI Nabla',Nabla,system-ui,sans-serif", file: 'nabla.woff2', desc: 'font-weight:400;',
    axes: {EDPT: [0, 200], EHLT: [0, 24]}},
  fraunces: {fam: 'A2UI Fraunces', stack: "'A2UI Fraunces',Fraunces,Georgia,serif", file: 'fraunces.woff2', desc: 'font-weight:100 900;',
    axes: {wght: [100, 900], opsz: [9, 144], SOFT: [0, 100], WONK: [0, 1]}}
};
function _moVfFace(k) {
  var f = _MO_VFONTS[k];
  return "<style>@font-face{font-family:'" + f.fam + "';src:url(" + _MO_VFONT_BASE + f.file + ") format('woff2');" + f.desc + 'font-display:swap;}</style>';
}
// Validated axis animation for a studio face: up to 4 {axis, from, to}, axis from the font's own table, values clamped to its range.
// Returns the font-variation-settings value as a function of --v, or '' when nothing valid was given.
function _moVfVary(k, vary) {
  if (!Object.prototype.hasOwnProperty.call(_MO_VFONTS, k) || !Array.isArray(vary)) return '';
  var axes = _MO_VFONTS[k].axes, out = [], seen = {}, i;
  for (i = 0; i < vary.length && out.length < 4; i++) {
    var v = vary[i];
    if (!v || typeof v !== 'object' || typeof v.axis !== 'string' || !Object.prototype.hasOwnProperty.call(axes, v.axis) || seen[v.axis]) continue;
    seen[v.axis] = 1;
    var r = axes[v.axis], a = _ffNum(v.from, r[0], r[0], r[1], 2), z = _ffNum(v.to, r[1], r[0], r[1], 2), d = _ffNum(parseFloat(z) - parseFloat(a), 0, r[0] - r[1], r[1] - r[0], 2);
    out.push("'" + v.axis + "' calc(" + a + ' + ' + d + '*var(--v,1))');
  }
  return out.join(',');
}
var _MO_VARY_ON = {unit: 1, dial: 1, wave: 1};

var _MO_OBJ_SHAPES = {sphere: 0, torus: 1, cube: 2, pill: 3, knot: 4, blob: 5, lattice: 6, twist: 7, rings: 8, text: 9};
var _MO_OBJ_MATS = {chrome: 0, glass: 1, iridescent: 2, clay: 3, gold: 4, pearl: 5, obsidian: 6};
// Per-material default colours: [tint, rim light 1, rim light 2, studio tone].
var _MO_OBJ_PAL = {
  chrome: ['#e3e8ff', '#ff4f8b', '#4cc3ff', '#14121c'], glass: ['#c4ecff', '#ff9a3d', '#8a6cff', '#12131c'],
  iridescent: ['#ffffff', '#ff4f8b', '#4cc3ff', '#0e0c14'], clay: ['#f2a7b6', '#ffd6a5', '#a0c4ff', '#ece4d8'],
  gold: ['#ffcf6b', '#ff7a3d', '#ffe9b0', '#140e08'], pearl: ['#f3eee8', '#b8a7ff', '#ffd1e8', '#d8d0c6'],
  obsidian: ['#0a0a14', '#4cc3ff', '#ff4f8b', '#0a0a10']
};
// Typeface tokens for 3D type: a fixed table of CSS font shorthands (%S = size). Payload text never reaches a font string.
var _MO_OBJ_FONT = {
  display: '800 %S system-ui,-apple-system,"Segoe UI",Roboto,sans-serif',
  serif: '700 %S Georgia,"Times New Roman",serif',
  mono: '700 %S ui-monospace,Menlo,Consolas,monospace',
  rounded: '800 %S ui-rounded,"SF Pro Rounded",system-ui,sans-serif',
  recursive: "900 %S 'A2UI Recursive',Recursive,system-ui,sans-serif",
  anybody: "900 %S 'A2UI Anybody',Anybody,system-ui,sans-serif",
  fraunces: "800 %S 'A2UI Fraunces',Fraunces,Georgia,serif"
};

_RENDERERS['motion_object3d'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6), src = Array.isArray(b.shapes) ? b.shapes : [], sh = [], i;
  for (i = 0; i < src.length && sh.length < 4; i++) if (typeof src[i] === 'string' && Object.prototype.hasOwnProperty.call(_MO_OBJ_SHAPES, src[i])) sh.push(src[i]);
  if (!sh.length) sh = ['blob'];
  var mat = _moOwn(_MO_OBJ_MATS, b.material, 'chrome'), pal = _MO_OBJ_PAL[mat], hasTxt = sh.indexOf('text') >= 0;
  var txt = hasTxt ? (_moStr(b.text, 14) || 'A2UI') : '', face = _moOwn(_MO_OBJ_FONT, b.typeface, 'display'), font = _MO_OBJ_FONT[face];
  var c1 = _ffHex(b.color, pal[0]), c2 = _ffHex(b.accent, pal[1]), c3 = _ffHex(b.accent2, pal[2]);
  var bgOn = typeof b.backdrop === 'string' && /^#[0-9a-fA-F]{6}$/.test(b.backdrop), cb = bgOn ? b.backdrop.toLowerCase() : pal[3];
  var turns = _ffNum(b.turns, 1, -8, 8, 2), ang = _ffNum(b.angle, 0, -360, 360, 1), tilt = _ffNum(b.tilt, 12, -60, 60, 1), zoom = _ffNum(b.size, 1, 0.4, 2, 2);
  var depth = _ffNum(b.depth, 0.22, 0.05, 0.6, 2), span = _ffNum(b.span, 20, 0, 600, 2), speed = _ffNum(b.speed, 1, 0, 5, 2), still = b.still === true, floor = b.floor !== false;
  var ratio = _ffPick(b.ratio, _MO_RATIO, '16:9'), fill = b.fill === true, rad = _ffInt(b.radius, 0, 0, 60);
  var idx = [];
  for (i = 0; i < sh.length; i++) idx.push(_MO_OBJ_SHAPES[sh[i]]);
  var label = _moStr(b.label, 80) || ('3D ' + mat + ' ' + (hasTxt ? txt : sh.join(' to ')));
  var cfg = '{c1:' + _moRgb3(c1) + ',c2:' + _moRgb3(c2) + ',c3:' + _moRgb3(c3) + ',cb:' + _moRgb3(cb) + ',mat:' + _MO_OBJ_MATS[mat] + ',floor:' + (floor ? 'true' : 'false')
    + ',tilt:' + tilt + ',zoom:' + zoom + ',depth:' + depth + ',bg:' + (bgOn ? 'true' : 'false') + ',ang:' + ang + ',turns:' + turns + ',span:' + span + ',speed:' + speed
    + ',still:' + (still ? 'true' : 'false') + ',max:1100,n:' + idx.length + ',sh:[' + idx.join(',') + '],txt:' + _jsJson(txt) + ',font:' + _jsJson(font) + '}';
  var fb = hasTxt
    ? '<div style="font:900 min(13vw,8rem)/1 system-ui,-apple-system,sans-serif;letter-spacing:-0.02em;color:' + c1 + ';background:linear-gradient(180deg,#ffffff,' + c1 + ' 45%,' + c2 + ');-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">' + _esc(txt) + '</div>'
    : '<div style="width:38%;aspect-ratio:1/1;border-radius:' + (sh[sh.length - 1] === 'cube' ? '22%' : '50%') + ';background:radial-gradient(circle at 34% 28%,#ffffff,' + c1 + ' 20%,' + c3 + ' 62%,' + c2 + ');box-shadow:0 2.4em 2em -1.6em rgba(0,0,0,0.45);"></div>';
  return (hasTxt && Object.prototype.hasOwnProperty.call(_MO_VFONTS, face) ? _moVfFace(face) : '') + '<div id="mt-' + uid + '" role="img" aria-label="' + _esc(label) + '" style="position:relative;width:100%;' + (fill ? 'height:100%;' : 'aspect-ratio:' + ratio + ';') + 'overflow:hidden;border-radius:' + rad + 'px;'
    + (bgOn ? 'background:radial-gradient(circle at 50% 45%,' + cb + ',#000 140%);' : '') + '">'
    + '<style>#mt-' + uid + '.gl>[data-fb]{display:none!important}@media print{#mt-' + uid + ' canvas{display:none}#mt-' + uid + '.gl>[data-fb]{display:flex!important}}</style>'
    + '<div data-fb="" style="position:absolute;left:0;top:0;width:100%;height:100%;display:flex;align-items:center;justify-content:center;">' + fb + '</div>'
    + '<canvas aria-hidden="true" style="position:absolute;left:0;top:0;width:100%;height:100%;display:block;"></canvas>'
    + '<script>(' + _moStudioObj.toString() + ')("' + uid + '",' + cfg + ');<\/script></div>';
};

// ─── motion_bricks: a LEGO-style brick sculpture on the film clock ─────────────────────────────────────────────────────────────
// Reuses brick_build_3d's engine (_brickKit in atoms_brick.gs, unchanged apart from its film-clock hook) inside a lean, transparent
// shell: bricks drop into place as --p goes 0 to 1 and the model turns with --s. A word is built in real bricks: each character of
// the same 5x7 dot font motion_particles uses, every row's runs of dots merged into 1x1 to 1x4 bricks, `depth` studs deep.
var _MO_BRICK_DEFAULT = ['#c91a09', '#f2cd37', '#0055bf', '#237841', '#fe8a18', '#36aebf'];
function _moBrickText(t, palette, color, depth) {
  if (typeof t !== 'string') return null;
  var chs = Array.from(t.toUpperCase().trim()).slice(0, 12), out = [], x0 = 0, i, r, c;
  var cols = color ? [color] : (palette.length ? palette : _MO_BRICK_DEFAULT);
  for (i = 0; i < chs.length; i++) {
    var g = Object.prototype.hasOwnProperty.call(_MO_FONT, chs[i]) ? _MO_FONT[chs[i]] : null;
    if (!g) { x0 += 3; continue; }
    var col = cols[i % cols.length];
    for (r = 0; r < 7; r++) {
      c = 0;
      while (c < 5) {
        if (!(g[r] & (16 >> c))) { c++; continue; }
        var c0 = c;
        while (c < 5 && (g[r] & (16 >> c))) c++;
        var len = c - c0, k = c0;
        while (len > 0) { var w = len >= 4 ? 4 : len; out.push({x: x0 + k, y: 6 - r, z: 0, w: w, d: depth, h: 1, c: col}); k += w; len -= w; }
      }
    }
    x0 += 6;
  }
  return out.length ? out : null;
}
_RENDERERS['motion_bricks'] = function(b) {
  var kit = _brickKit(), palette = _brickPalette(b.palette), color = _ffHex(b.color, '');
  var shape = Object.prototype.hasOwnProperty.call(kit.SHAPES, b.shape) ? b.shape : 'heart', depth = _ffInt(b.depth, 2, 1, 4);
  var text = _moStr(b.text, 12), bricks = _moBrickText(text, palette, color, depth) || _brickSanitise(b.bricks, palette);
  var ang = _ffNum(b.angle, 24, -360, 360, 1), el = _ffNum(b.elevation, 26, 7, 75, 1), turns = _ffNum(b.turns, 1, -8, 8, 2);
  var ratio = _ffPick(b.ratio, _MO_RATIO, '16:9'), fill = b.fill === true, uid = Math.random().toString(36).substr(2, 6);
  var label = _moStr(b.label, 80) || (text ? 'Brick lettering: ' + text : (bricks ? 'Brick model' : 'Brick model: ' + shape));
  var cfg = '{"shape":' + _jsJson(shape) + ',"bricks":' + _jsJson(bricks) + ',"speed":1,"orbit":false,"bg":null,"mode":"animate","step":1,"clock":"film","azDeg":' + ang + ',"elDeg":' + el + ',"turns":' + turns + ',"base":' + _jsJson(b.base === 'none' ? 'none' : (_ffHex(b.base, '') || null)) + ',"look":"' + (b.look === 'instructions' ? 'instructions' : 'studio') + '"}';
  return '<div id="mt-' + uid + '" style="position:relative;width:100%;' + (fill ? 'height:100%;' : 'aspect-ratio:' + ratio + ';') + '"><canvas role="img" aria-label="' + _esc(label) + '" style="position:absolute;left:0;top:0;width:100%;height:100%;display:block;"></canvas></div>'
    + '<script>(function(){var LEGO_MATERIAL_PROFILE = ' + _jsJson(LEGO_MATERIAL_PROFILE) + ';var K=(' + _brickKit.toString() + ')();var r=document.getElementById("mt-' + uid + '"),cv=r&&r.querySelector("canvas");if(cv)K.create(cv,' + cfg + ');})();<\/script>';
};
