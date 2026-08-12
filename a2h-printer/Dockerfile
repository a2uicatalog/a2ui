# a2uicatalog a2h Printer — self-hosted mode (this Dockerfile builds src/ only;
# copilotkit/ is a separate Node process, not part of this image). See
# README.md for the full deploy guide and the min-instances cost/latency
# tradeoff before choosing a MIN_INSTANCES setting.
FROM node:24-slim AS build
WORKDIR /app
# better-sqlite3 needs a native build toolchain — present in this stage only,
# not in the final image (keeps the runtime image small and free of a
# compiler, which is also a smaller attack surface).
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ \
    && rm -rf /var/lib/apt/lists/*
COPY package.json package-lock.json* ./
RUN npm install --omit=dev

FROM node:24-slim
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/node_modules ./node_modules
COPY package.json ./
COPY src ./src
# SQLite lives on a mounted volume in production (see README's Cloud Run
# GCS-FUSE instructions) — this default path is for local/docker-compose use.
ENV SQLITE_PATH=/data/a2h-printer.db
EXPOSE 8080
CMD ["node", "src/server.js"]
