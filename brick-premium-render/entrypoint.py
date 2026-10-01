"""Cloud Run Job entrypoint for the premium-render pipeline. Reads a partsModel BOM + render settings from
env vars (set per-execution via the Cloud Run Admin API's containerOverrides, the SAME mechanism
agents/gcp-catalogue-agents's own live dispatch already uses -- see DISPATCH_ITEM_ID etc. in that system),
fetches only the specific part meshes this BOM actually needs from the live site (NOT baked into this image --
public/parts/ is 523MB and changes as the catalogue grows; baking it in would mean a stale, bloated image
rebuilt for no reason on every deploy), calls scripts/brick_models/render_blender.py's existing CLI UNMODIFIED,
then uploads the two real output files to GCS as raw bytes (no signing capability needed/granted here --
signing happens in premium-render-api, which holds the narrower-is-safer signing IAM role; this Job's own
service account only needs roles/storage.objectAdmin on the output bucket).

The BOM itself arrives as a GCS object path (PARTS_MODEL_GCS_PATH), not inline in an env var -- found live
2026-10-01 that Cloud Run Jobs caps total env var size at 32KiB, which a real complete kit (1798 parts)
blows past when base64-encoded (~87.5KB). premium-render-api stages the JSON to
gs://<OUT_GCS_BUCKET>/<PARTS_MODEL_GCS_PATH> before triggering; this Job just downloads it, same bucket/SA
already used for the output upload below.
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

PARTS_BASE_URL = os.environ.get("PARTS_BASE_URL", "https://a2uicatalog.ai")
WORK_DIR = Path("/tmp/premium_render")


def fatal(msg):
    print("FATAL:", msg, file=sys.stderr)
    sys.exit(1)


def fetch(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "brick-premium-render-job (a2uicatalog.ai)"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as out:
        out.write(resp.read())


def distinct_part_ids(parts_model_rows):
    ids = []
    for row in parts_model_rows:
        pid = row[0] if isinstance(row, list) else row.get("p")
        if pid and pid not in ids:
            ids.append(pid)
    return ids


def main():
    parts_model_gcs_path = os.environ.get("PARTS_MODEL_GCS_PATH")
    if not parts_model_gcs_path:
        fatal("PARTS_MODEL_GCS_PATH not set")
    out_gcs_bucket = os.environ.get("OUT_GCS_BUCKET")
    out_gcs_prefix = os.environ.get("OUT_GCS_PREFIX")
    if not out_gcs_bucket or not out_gcs_prefix:
        fatal("OUT_GCS_BUCKET / OUT_GCS_PREFIX not set")

    from google.cloud import storage
    storage_client = storage.Client()

    resolution = os.environ.get("RESOLUTION", "1600x1200")
    still_samples = os.environ.get("STILL_SAMPLES", "128")
    turntable_resolution = os.environ.get("TURNTABLE_RESOLUTION", "480x360")
    turntable_samples = os.environ.get("TURNTABLE_SAMPLES", "8")
    frames = os.environ.get("FRAMES", "48")
    fps = os.environ.get("FPS", "24")
    direction = os.environ.get("DIRECTION", "1,0.6,1")
    no_video = os.environ.get("NO_VIDEO", "") == "1"

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    bom_raw = storage_client.bucket(out_gcs_bucket).blob(parts_model_gcs_path).download_as_bytes()
    bom = json.loads(bom_raw)
    rows = bom["partsModel"] if isinstance(bom, dict) and "partsModel" in bom else bom

    bom_path = WORK_DIR / "bom.json"
    bom_path.write_text(json.dumps({"partsModel": rows}))

    parts_dir = WORK_DIR / "parts"
    for part_id in distinct_part_ids(rows):
        fetch(f"{PARTS_BASE_URL}/parts/{part_id}.json", parts_dir / f"{part_id}.json")
    print(f"fetched {len(distinct_part_ids(rows))} distinct part mesh(es)")

    colours_path = WORK_DIR / "colours.json"
    fetch(f"{PARTS_BASE_URL}/bricksdemo/ldraw_colours_full.json", colours_path)

    out_dir = WORK_DIR / "out"
    cmd = [
        sys.executable, "/app/scripts/brick_models/render_blender.py",
        "--parts-model", str(bom_path),
        "--parts-dir", str(parts_dir),
        "--colours", str(colours_path),
        "--out-dir", str(out_dir),
        "--resolution", resolution,
        "--still-samples", still_samples,
        "--direction", direction,
    ]
    if no_video:
        cmd.append("--no-video")
    else:
        # render_blender.py's turntable always renders at the SAME --resolution as the still (see its own
        # main()) -- this job intentionally uses a much cheaper resolution/sample setting for the turntable
        # than the hero (see this session's real measured timings, scripts/brick_models/requirements-blender.txt's
        # sibling docs/plan), which render_blender.py's CLI doesn't expose a separate flag for yet. Call it
        # TWICE instead: once --no-video for the full-quality hero, once --frames/--turntable-samples only
        # (cheap resolution) for just the turntable, matching the real cost split measured live.
        cmd.append("--no-video")

    print("rendering hero:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    if not no_video:
        # render_blender.py's own main() always renders a hero.png as part of its flow (there's no CLI flag
        # to skip it) -- calling it a second time at the turntable's own, much cheaper resolution/sample
        # settings would silently overwrite the good, full-quality hero.png just written above with a
        # low-quality one. render_blender.py is deliberately NOT modified (reused exactly as already tested)
        # -- back the good hero up, let the second call overwrite freely, then restore it.
        hero_path = out_dir / "hero.png"
        hero_backup = WORK_DIR / "hero_fullquality_backup.png"
        hero_backup.write_bytes(hero_path.read_bytes())

        turntable_cmd = [
            sys.executable, "/app/scripts/brick_models/render_blender.py",
            "--parts-model", str(bom_path),
            "--parts-dir", str(parts_dir),
            "--colours", str(colours_path),
            "--out-dir", str(out_dir),
            "--resolution", turntable_resolution,
            "--still-samples", turntable_samples,  # the throwaway hero this call also renders; keep it cheap too, it's discarded below
            "--turntable-samples", turntable_samples,
            "--frames", frames,
            "--fps", fps,
            "--direction", direction,
        ]
        print("rendering turntable:", " ".join(turntable_cmd))
        subprocess.run(turntable_cmd, check=True)

        hero_path.write_bytes(hero_backup.read_bytes())  # restore the real, full-quality hero over the cheap throwaway one

    print("uploading outputs to GCS")
    bucket = storage_client.bucket(out_gcs_bucket)
    for name in ("hero.png", "turntable.mp4"):
        local = out_dir / name
        if not local.exists():
            continue
        blob = bucket.blob(f"{out_gcs_prefix.rstrip('/')}/{name}")
        blob.upload_from_filename(str(local))
        print(f"uploaded {name} ({local.stat().st_size} bytes) -> gs://{out_gcs_bucket}/{blob.name}")

    print("DONE")


if __name__ == "__main__":
    main()
