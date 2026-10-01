# Built with repo root as build context — same reason + same mechanism as a2a_counterpart/Dockerfile's own
# comment (gcloud's auto-detected single root Dockerfile is already claimed by cloud-run-renderer/); see
# premium-render-api/cloudbuild.yaml for the explicit --file build.
FROM python:3.11-slim

WORKDIR /app

COPY premium-render-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY premium-render-api/server.py .

ENV PORT=8080
EXPOSE 8080
CMD exec gunicorn --bind :$PORT --workers 2 --timeout 60 server:app
