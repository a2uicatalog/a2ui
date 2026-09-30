// threejs_view_math.js -- pure, dependency-free math for the Brick Design Lab's "View in Three.js" viewer.
// build_design_page.py embeds this file's text VERBATIM into the page (same "read the real source, embed
// it" pattern web_article.py already uses for atoms_brick.gs's _brickMount/_brickKit); tests/js/
// test_threejs_view_math.mjs runs it directly via Node's vm module. Single source of truth, not a hand-kept
// twin -- deliberately has NO THREE.js dependency (plain arrays/numbers only) so it's testable with nothing
// but Node itself.
//
// TJS_PART_ROT: twin of atoms_brick.gs's own table (also twinned in renderers/brick_parts_validate.py and
// mcp-worker/src/omr-import.js) -- edit all four together, in the same order, or rotation indices silently
// mean different things on each side.
var TJS_PART_ROT=[
  [1,0,0,0,1,0,0,0,1],[0,0,1,0,1,0,-1,0,0],[-1,0,0,0,1,0,0,0,-1],[0,0,-1,0,1,0,1,0,0],
  [-1,0,0,0,-1,0,0,0,1],[-1,0,0,0,0,-1,0,-1,0],[-1,0,0,0,0,1,0,1,0],[0,-1,0,-1,0,0,0,0,-1],
  [0,-1,0,0,0,-1,1,0,0],[0,-1,0,0,0,1,-1,0,0],[0,-1,0,1,0,0,0,0,1],[0,0,-1,-1,0,0,0,1,0],
  [0,0,-1,0,-1,0,-1,0,0],[0,0,-1,1,0,0,0,-1,0],[0,0,1,-1,0,0,0,-1,0],[0,0,1,0,-1,0,1,0,0],
  [0,0,1,1,0,0,0,1,0],[0,1,0,-1,0,0,0,0,1],[0,1,0,0,0,-1,-1,0,0],[0,1,0,0,0,1,1,0,0],
  [0,1,0,1,0,0,0,0,-1],[1,0,0,0,-1,0,0,0,-1],[1,0,0,0,0,-1,0,1,0],[1,0,0,0,0,1,0,-1,0]
];

function tjsRot(r,p){var m=TJS_PART_ROT[r];return [m[0]*p[0]+m[1]*p[1]+m[2]*p[2],m[3]*p[0]+m[4]*p[1]+m[5]*p[2],m[6]*p[0]+m[7]*p[1]+m[8]*p[2]];}

// Local part-mesh vertex (LDU, quant-scaled) -> world three.js unit, for one instance at world LDU
// position instPos with rotation index r. LDraw Y points down; three.js is Y-up, so Y is negated once here
// (not baked per-part like the live renderer's engine-space convention) -- instPos already comes straight
// from partsModel's own real, floor-computed LDU placement (toPartsModel/toTrayModel), so no extra per-part
// floor logic is needed at this layer.
function tjsToWorld(p,q,r,instPos){
  var rp=tjsRot(r,[p[0]/q,p[1]/q,p[2]/q]);
  return [(rp[0]+instPos[0])/20,-(rp[1]+instPos[1])/20,(rp[2]+instPos[2])/20];
}

// Row-major 16-value flat matrix, consumable directly via THREE.Matrix4.prototype.set(...values) (three.js's
// own .set() takes its 16 arguments in natural row-major reading order, though .elements is stored
// column-major internally -- that's three's own API, not a convention invented here). Deliberately does NOT
// include tjsToWorld's D=diag(1/20,-1/20,1/20) scale/flip -- only the part's own rotation R(r), its quant
// scale, and the instance's LDU translation, i.e. worldPreD = R(r)*(p/q) + instPos. D belongs on the
// InstancedMesh's own object-level .scale instead (set once per bucket, not per instance) -- found live
// 2026-09-30: baking D (a mirror, determinant -1) into every INSTANCE's matrix broke rendering, because
// three.js decides front-face winding and the FLIP_SIDED normal correction from object.matrixWorld's
// determinant alone (a CPU-side, per-OBJECT check -- see WebGLRenderer's frontFaceCW and the
// defaultnormal_vertex chunk), with no visibility into what an instanced vertex shader's own instanceMatrix
// does per-instance. Every instance shared the SAME mirror, so hoisting it onto the object (where that check
// actually looks) is the correct fix, not a workaround -- it also makes the instancing-only normal transform
// (mat3(instanceMatrix) applied directly, a shortcut that is only exact for pure rotation+uniform-scale)
// correct again, since a bare R(r)/q per instance is exactly that. Tested by composing this function's output
// with D exactly the way render() does (object scale applied after the instance matrix) and comparing the
// result to tjsToWorld's own point-by-point output in test_threejs_view_math.mjs, not just re-derived by eye.
function tjsInstanceMatrixRowMajor(r,instPos,q){
  var m=TJS_PART_ROT[r],s=1/q;
  return [
    m[0]*s, m[1]*s, m[2]*s, instPos[0],
    m[3]*s, m[4]*s, m[5]*s, instPos[1],
    m[6]*s, m[7]*s, m[8]*s, instPos[2],
    0,      0,      0,      1
  ];
}

function tjsSub(a,b){return [a[0]-b[0],a[1]-b[1],a[2]-b[2]];}
function tjsCross(a,b){return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];}
function tjsDot(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
function tjsLen(a){return Math.sqrt(tjsDot(a,a));}
function tjsNorm(a){var l=tjsLen(a)||1;return [a[0]/l,a[1]/l,a[2]/l];}

// Fits a camera to a real axis-aligned box (boxMin/boxMax, three.js Y-up world units) from a FIXED unit
// direction `dir` (pointing from the box centre TOWARD the camera), given vertical FOV (degrees) and
// aspect ratio. Projects all 8 box corners onto the camera's OWN right/up axes for that direction, so the
// true required half-width and half-height (in that specific view) drive the distance -- correct for any
// box shape, not a single-scalar heuristic (a bounding-sphere radius, or a "maxSize x maxSize" square)
// applied uniformly to both screen axes, which both fail for non-square builds (found live 2026-09-29: a
// diagonal-based sphere fit left a real 3-part test build tiny and off-centre in frame).
// Returns {position:[x,y,z], target:[x,y,z], distance, near, far}.
function tjsFitCamera(boxMin,boxMax,dir,fovYDeg,aspect,margin){
  margin=margin||1.15;
  var center=[(boxMin[0]+boxMax[0])/2,(boxMin[1]+boxMax[1])/2,(boxMin[2]+boxMax[2])/2];
  var unitDir=tjsNorm(dir);
  var forward=[-unitDir[0],-unitDir[1],-unitDir[2]];
  var worldUp=[0,1,0];
  var right=tjsCross(forward,worldUp);
  right=(tjsDot(right,right)<1e-8)?[1,0,0]:tjsNorm(right);
  var up=tjsNorm(tjsCross(right,forward));
  var corners=[
    [boxMin[0],boxMin[1],boxMin[2]],[boxMax[0],boxMin[1],boxMin[2]],
    [boxMin[0],boxMax[1],boxMin[2]],[boxMax[0],boxMax[1],boxMin[2]],
    [boxMin[0],boxMin[1],boxMax[2]],[boxMax[0],boxMin[1],boxMax[2]],
    [boxMin[0],boxMax[1],boxMax[2]],[boxMax[0],boxMax[1],boxMax[2]]
  ];
  var halfW=0,halfH=0;
  for(var i=0;i<corners.length;i++){
    var v=tjsSub(corners[i],center);
    halfW=Math.max(halfW,Math.abs(tjsDot(v,right)));
    halfH=Math.max(halfH,Math.abs(tjsDot(v,up)));
  }
  var halfFovY=(fovYDeg*Math.PI/180)/2;
  var halfFovX=Math.atan(Math.tan(halfFovY)*aspect);
  var dist=margin*Math.max(halfH/Math.tan(halfFovY),halfW/Math.tan(halfFovX),0.5);
  return {
    position:[center[0]+unitDir[0]*dist,center[1]+unitDir[1]*dist,center[2]+unitDir[2]*dist],
    target:center, distance:dist,
    near:Math.max(dist/100,0.1), far:dist*10,
  };
}
