# Built with repo root as build context — same reason + same mechanism as a2a_counterpart/Dockerfile's
# own comment (gcloud's auto-detected single root Dockerfile is already claimed by cloud-run-renderer/);
# see declaration-prealable-api/cloudbuild.yaml for the explicit --file build.
FROM python:3.11-slim

WORKDIR /app

# cairosvg (cairocffi) binds the NATIVE libcairo C library via ctypes -- not bundled by pip, and
# python:3.11-slim doesn't have it. Found live 2026-10-01: a local dev-venv test passed only because
# that machine already had libcairo2 installed system-wide (apt); the real container failed at request
# time with "no library called 'cairo-2' was found", not at build/import time.
RUN apt-get update && apt-get install -y --no-install-recommends libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY declaration-prealable-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The actual generation logic lives in declaration_prealable/ (repo-relative import path, same
# directory name the CLI tools already import as `declaration_prealable.xxx`) — copied in unmodified,
# not duplicated.
COPY declaration_prealable/ ./declaration_prealable/
COPY declaration-prealable-api/server.py .

ENV PORT=8080
EXPOSE 8080
CMD exec gunicorn --bind :$PORT --workers 2 --timeout 30 server:app
