# Built with repo root as build context, not a2a_counterpart/ itself — this
# service imports renderers/a2a_extension.py and renderers/a2ui_v1.py for
# real (Gemini design review, 2026-08-24: "imported not duplicated"), and
# Docker can't COPY anything outside its build context. Same constraint and
# same fix as the repo-root Dockerfile serving cloud-run-renderer/ (see its
# own comment) — that file predicted exactly this: "If more containerized
# services get added later, this'll need a proper cloudbuild.yaml with an
# explicit --file per service instead of relying on gcloud's auto-detected
# single root Dockerfile." This is that second service; see
# a2a_counterpart/cloudbuild.yaml for the build invocation
# (`docker build -f a2a_counterpart/Dockerfile .` from repo root).
FROM python:3.11-slim

WORKDIR /app

COPY a2a_counterpart/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Single source of truth for the A2UI v1.0 emitter and its A2A transport
# binding — the SAME renderers/ every other surface in this repo uses, not
# a duplicated copy (the exact drift class Topic A just fixed elsewhere).
COPY renderers/ /app/renderers/
COPY a2a_counterpart/main.py .

ENV PORT=8080
EXPOSE 8080
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
