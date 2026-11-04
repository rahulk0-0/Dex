FROM node:22-bookworm-slim AS web
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src
COPY public ./public
RUN npm run build

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt && useradd --create-home --uid 10001 appuser
COPY companion/server.py companion/server.py
COPY companion/setup.py companion/setup.py
RUN python companion/setup.py
COPY companion/README.md companion/start.bat companion/
COPY companion/licenses companion/licenses
COPY backend backend
COPY --from=web /build/dist /app/web
RUN python backend/package_companion.py
ENV PYTHONUNBUFFERED=1 DEX_WEB_ROOT=/app/web DEX_MAX_HEAP_MB=320 DEX_CONCURRENCY=1 MAX_REQUEST_MB=32 PORT=10000
USER appuser
EXPOSE 10000
CMD ["sh","-c","exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 2 --timeout 240 --access-logfile /dev/null --error-logfile - backend.app:app"]
