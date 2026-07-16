# cloud-run-renderer/'s Dockerfile, but living at repo root — `gcloud run
# deploy --source` only auto-detects a Dockerfile literally at the root of
# its source directory, and Docker itself won't let a build COPY anything
# outside its build context, so this can't live inside cloud-run-renderer/
# while still reusing the repo's real renderers/ package. If more
# containerized services get added later, this'll need a proper
# cloudbuild.yaml with an explicit --file per service instead of relying on
# gcloud's auto-detected single root Dockerfile.
#
# Official Playwright image: chromium preinstalled, same engine
# scripts/printer.py already uses locally, so this is a drop-in replacement
# for that rendering step, not a new/different render path.
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

COPY cloud-run-renderer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Single source of truth for atom->HTML: the SAME renderers/ every other
# surface in this repo uses, not a duplicated copy.
COPY renderers/ /app/renderers/
COPY cloud-run-renderer/server.py .

ENV PORT=8080
EXPOSE 8080

# 2 worker PROCESSES — server.py launches a fresh Playwright/chromium
# context per request (see its own comment: the sync API is thread-affined,
# so no long-lived browser is shared across requests/threads); workers just
# gives Cloud Run some request concurrency, not a work-around for that.
CMD ["gunicorn", "--bind", ":8080", "--workers", "2", "--timeout", "60", "server:app"]
