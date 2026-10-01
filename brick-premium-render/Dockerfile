# Built with repo root as build context (same reason + same mechanism as a2a_counterpart/Dockerfile's own
# comment: gcloud's auto-detected single root Dockerfile is already claimed by cloud-run-renderer/; see
# brick-premium-render/cloudbuild.yaml for the explicit --file build).
#
# Base image + system libraries confirmed live 2026-10-01 (not assumed): bpy==5.2.2's cp313 wheel + a real
# Cycles write_still render both work cleanly in this exact base+library combination, verified with a local
# `docker build`+`docker run` smoke test against this exact Dockerfile content before any Job/deploy work
# was built on top of it (see the premium-export plan's own "Mandatory first step").
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libxrender1 \
    libxi6 \
    libxkbcommon0 \
    libsm6 \
    libxxf86vm1 \
    libxfixes3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY brick-premium-render/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# render_blender.py imports `from scripts.brick_models import blender_view_math as bvm` and resolves its own
# ROOT as `Path(__file__).resolve().parent.parent.parent` -- preserve that same repo-relative path inside the
# image rather than flattening it, so the script runs completely unmodified.
COPY scripts/brick_models/render_blender.py /app/scripts/brick_models/render_blender.py
COPY scripts/brick_models/blender_view_math.py /app/scripts/brick_models/blender_view_math.py

COPY brick-premium-render/entrypoint.py .

CMD ["python3", "entrypoint.py"]
