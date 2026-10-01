#!/usr/bin/env python3
"""Builds public-full/declaration-prealable/index.html -- the web form version of intake.py's question
set, for full.a2uicatalog.ai (Cloudflare-Access-gated, curtis@krygier.fr / a2uicatalog@krygier.co.uk
only). Same house style as scripts/brick_models/build_design_page.py: a raw-string HTML/JS template with
__PLACEHOLDER__ tokens, no Jinja.

2D pieces only (DP2 + DP5) -- the optional 3D supplementary visual stays CLI-only
(`intake.py --3d`), per Curtis's own scoping choice: the form posts synchronously to
declaration-prealable-api's `/generate` and shows both images inline + download links, not a
multi-minute async job.

Gated: refuses to run unless A2UI_CATALOG_FULL=1, matching scripts/gen_authoring.py's own guard --
this generator must never write into public/, only public-full/ (gitignored, not shipped by the public
deploy.yml pipeline).

  A2UI_CATALOG_FULL=1 python3 declaration_prealable/build_intake_page.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "public-full" / "declaration-prealable" / "index.html"

# Hardcoded after the real Cloud Run deploy, same convention as
# scripts/brick_models/build_design_page.py's own PREMIUM_RENDER_BASE_URL (a Cloud Run service URL is
# stable across redeploys once first created). Live since 2026-10-01.
DP_API_BASE_URL = "https://declaration-prealable-api-1093160097419.europe-west1.run.app"

SIGNING_KEY_SECRET = "declaration-prealable-signing-key"
GCP_PROJECT = "artful-patrol-502116-b7"


def _guard():
    if os.environ.get("A2UI_CATALOG_FULL") != "1":
        print("build_intake_page: A2UI_CATALOG_FULL != 1, refusing to run "
              "(this generator only ever writes to public-full/)", file=sys.stderr)
        sys.exit(1)


def _signing_key():
    """The token embedded in the generated page's JS -- not a secret FROM Curtis (he's the only one who
    can load this Cloudflare-Access-gated page); it exists so other internet traffic can't hit the bare
    Cloud Run URL directly. DP_SIGNING_KEY env var overrides for local testing; otherwise reads the
    real deployed value from Secret Manager, same pattern as scripts/ldraw/gen_set_gallery.py's rb_key().
    Fails loudly rather than silently embedding a placeholder that would produce a page that LOOKS built
    but 403s on every real submit."""
    env = os.environ.get("DP_SIGNING_KEY")
    if env:
        return env
    return subprocess.check_output(
        ["gcloud", "secrets", "versions", "access", "latest",
         f"--secret={SIGNING_KEY_SECRET}", "--project", GCP_PROJECT]
    ).decode().strip()


PAGE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Déclaration préalable — intake</title>
<style>
  :root{--bg:#f7f8fa;--ink:#202124;--sub:#5f6368;--rule:#dadce0;--accent:#1a73e8;--err:#d93025}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 Roboto,Arial,sans-serif;padding:24px 16px 80px}
  main{max-width:720px;margin:0 auto}
  h1{font-size:22px;margin:0 0 4px}
  p.lede{color:var(--sub);margin:0 0 24px;font-size:13px}
  fieldset{border:1px solid var(--rule);border-radius:8px;padding:16px;margin:0 0 16px;background:#fff}
  legend{font-weight:700;padding:0 6px}
  label{display:block;font-size:13px;color:var(--sub);margin:10px 0 4px}
  input,select{width:100%;font:inherit;padding:7px 9px;border:1px solid var(--rule);border-radius:6px;color:var(--ink);background:#fff}
  .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  .row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
  button{font:inherit;font-weight:600;padding:10px 18px;border:none;border-radius:8px;background:var(--accent);color:#fff;cursor:pointer}
  button:disabled{opacity:.6;cursor:default}
  .note{font-size:13px;color:var(--sub);margin-top:10px}
  .note.err{color:var(--err)}
  .results{display:none;margin-top:24px}
  .results.show{display:block}
  .piece{background:#fff;border:1px solid var(--rule);border-radius:8px;padding:14px;margin-bottom:14px}
  .piece h3{margin:0 0 8px;font-size:15px}
  .piece img{width:100%;border:1px solid var(--rule);border-radius:4px}
  .piece a.dl{display:inline-block;margin-top:8px;font-size:13px}
  #existingFields{display:none}
  #existingFields.show{display:block}
</style>
</head>
<body>
<main>
  <h1>Déclaration préalable — mur de clôture</h1>
  <p class="lede">Génère DP2 (plan de masse) et DP5 (représentation de l'aspect extérieur) — voir
    declaration_prealable/README.md pour le détail des pièces requises. Ceci est une aide au
    brouillon, pas une garantie d'acceptation.</p>

  <form id="dpForm">
    <fieldset>
      <legend>Projet</legend>
      <label for="commune">Commune</label>
      <input id="commune" required>
      <label for="address">Adresse</label>
      <input id="address" required>
      <label for="date_iso">Date</label>
      <input id="date_iso" type="date">
    </fieldset>

    <fieldset>
      <legend>Mur</legend>
      <div class="row">
        <div>
          <label for="project_type">Type</label>
          <select id="project_type">
            <option value="cloture">Clôture</option>
            <option value="soutenement">Mur de soutènement</option>
          </select>
        </div>
        <div>
          <label for="block_id">Matériau</label>
          <select id="block_id">__BLOCK_OPTS__</select>
        </div>
      </div>
      <div class="row3">
        <div>
          <label for="length_m">Longueur (m)</label>
          <input id="length_m" type="number" step="0.1" min="0.2" max="100" value="3.0" required>
        </div>
        <div>
          <label for="height_m">Hauteur (m)</label>
          <input id="height_m" type="number" step="0.1" min="0.2" max="10" value="1.8" required>
        </div>
        <div>
          <label for="thickness_mm">Épaisseur (mm)</label>
          <input id="thickness_mm" type="number" step="10" min="50" max="1000" value="200" required>
        </div>
      </div>
      <label for="bond">Appareillage</label>
      <select id="bond"><option value="running">Panneresse</option><option value="stack">Droit</option></select>
      <label for="finish_label">Finition (texte DP5)</label>
      <input id="finish_label" value="Enduit lisse peint en blanc">
      <label for="finish_colour_hex">Couleur de finition</label>
      <input id="finish_colour_hex" type="color" value="#f2f1ec">
    </fieldset>

    <fieldset>
      <legend>Parcelle (pour DP2)</legend>
      <div class="row">
        <div><label for="plot_width_m">Largeur parcelle (m)</label>
          <input id="plot_width_m" type="number" step="0.5" min="1" max="1000" value="20"></div>
        <div><label for="plot_depth_m">Profondeur parcelle (m)</label>
          <input id="plot_depth_m" type="number" step="0.5" min="1" max="1000" value="25"></div>
      </div>
      <div class="row">
        <div><label for="wall_offset_x_m">Mur : distance limite gauche (m)</label>
          <input id="wall_offset_x_m" type="number" step="0.1" min="0" max="1000" value="0.5"></div>
        <div><label for="wall_offset_y_m">Mur : distance limite avant (m)</label>
          <input id="wall_offset_y_m" type="number" step="0.1" min="0" max="1000" value="2.0"></div>
      </div>
      <label for="north_angle_deg">Angle Nord (°, horaire depuis le haut de page)</label>
      <input id="north_angle_deg" type="number" step="1" min="-360" max="360" value="0">

      <label style="display:flex;align-items:center;gap:8px;margin-top:14px;font-size:13px;color:var(--ink)">
        <input type="checkbox" id="hasExisting" style="width:auto"> Afficher une construction existante (ex. maison)
      </label>
      <div id="existingFields">
        <div class="row">
          <div><label for="ex_x">Distance limite gauche (m)</label>
            <input id="ex_x" type="number" step="0.1" min="0" max="1000" value="3.0"></div>
          <div><label for="ex_y">Distance limite avant (m)</label>
            <input id="ex_y" type="number" step="0.1" min="0" max="1000" value="10.0"></div>
        </div>
        <div class="row">
          <div><label for="ex_w">Largeur (m)</label>
            <input id="ex_w" type="number" step="0.1" min="0.5" max="1000" value="10.0"></div>
          <div><label for="ex_d">Profondeur (m)</label>
            <input id="ex_d" type="number" step="0.1" min="0.5" max="1000" value="8.0"></div>
        </div>
      </div>
    </fieldset>

    <button id="go" type="submit">Générer DP2 + DP5</button>
    <p class="note" id="status"></p>
  </form>

  <div class="results" id="results">
    <div class="piece">
      <h3>DP5 — Représentation de l'aspect extérieur</h3>
      <img id="dp5Img" alt="DP5">
      <div><a class="dl" id="dp5Dl" download="DP5_elevation.png">Télécharger DP5_elevation.png</a></div>
    </div>
    <div class="piece">
      <h3>DP2 — Plan de masse</h3>
      <img id="dp2Img" alt="DP2">
      <div><a class="dl" id="dp2Dl" download="DP2_plan_masse.png">Télécharger DP2_plan_masse.png</a></div>
    </div>
  </div>
</main>
<script>
var API_BASE='__API_BASE__';
var TOKEN='__TOKEN__';
function $(id){return document.getElementById(id)}

$('date_iso').value=new Date().toISOString().slice(0,10);
$('hasExisting').onchange=function(){
  $('existingFields').className=this.checked?'show':'';
};

$('dpForm').onsubmit=function(ev){
  ev.preventDefault();
  var goBtn=$('go'),status=$('status'),results=$('results');
  status.className='note';status.textContent='';results.className='results';

  var planWidth=parseFloat($('plot_width_m').value),planDepth=parseFloat($('plot_depth_m').value);
  var ox=parseFloat($('wall_offset_x_m').value),oy=parseFloat($('wall_offset_y_m').value);
  var length=parseFloat($('length_m').value);

  var plot={
    boundary_points_m:[[0,0],[planWidth,0],[planWidth,planDepth],[0,planDepth]],
    wall_points_m:[[ox,oy],[ox+length,oy]],
    north_angle_deg:parseFloat($('north_angle_deg').value)||0,
    existing_structures:[]
  };
  if($('hasExisting').checked){
    var sx=parseFloat($('ex_x').value),sy=parseFloat($('ex_y').value);
    var sw=parseFloat($('ex_w').value),sd=parseFloat($('ex_d').value);
    plot.existing_structures=[{label:'Maison existante',
      points_m:[[sx,sy],[sx+sw,sy],[sx+sw,sy+sd],[sx,sy+sd]]}];
  }

  var body={
    commune:$('commune').value, address:$('address').value, date_iso:$('date_iso').value,
    wall:{
      project_type:$('project_type').value, block_id:$('block_id').value, bond:$('bond').value,
      length_m:length, height_m:parseFloat($('height_m').value),
      thickness_mm:parseFloat($('thickness_mm').value),
      finish_label:$('finish_label').value, finish_colour_hex:$('finish_colour_hex').value
    },
    plot:plot
  };

  goBtn.disabled=true;goBtn.textContent='Génération…';
  fetch(API_BASE+'/generate',{method:'POST',
    headers:{'Content-Type':'application/json','X-Render-Token':TOKEN},
    body:JSON.stringify(body)})
    .then(function(r){return r.json()})
    .then(function(j){
      goBtn.disabled=false;goBtn.textContent='Générer DP2 + DP5';
      if(!j.ok){status.className='note err';status.textContent=j.error||'Échec de la génération.';return}
      status.textContent='';
      var dp5Src='data:image/png;base64,'+j.dp5_png_base64;
      var dp2Src='data:image/png;base64,'+j.dp2_png_base64;
      $('dp5Img').src=dp5Src;$('dp5Dl').href=dp5Src;
      $('dp2Img').src=dp2Src;$('dp2Dl').href=dp2Src;
      results.className='results show';
    })
    .catch(function(){
      goBtn.disabled=false;goBtn.textContent='Générer DP2 + DP5';
      status.className='note err';status.textContent='Impossible de contacter le service de génération.';
    });
};
</script>
</body>
</html>
"""


def build():
    from declaration_prealable.dp5_elevation import BLOCKS
    block_opts = "".join(f'<option value="{k}">{v["label"]}</option>' for k, v in BLOCKS.items())
    return (PAGE.replace("__BLOCK_OPTS__", block_opts)
            .replace("__API_BASE__", DP_API_BASE_URL)
            .replace("__TOKEN__", _signing_key()))


def main():
    _guard()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
