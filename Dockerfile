# Stage 1: Build frontend
FROM node:20-alpine AS build-frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Build backend
FROM python:3.11-slim AS build-backend
WORKDIR /app
COPY backend/pyproject.toml backend/
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -e backend/
COPY backend/ backend/

# Stage 3: Runtime
FROM python:3.11-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build-backend /opt/venv /opt/venv
COPY --from=build-backend /app/backend /app/backend
COPY --from=build-frontend /app/frontend/dist /app/frontend/dist

ENV PATH="/opt/venv/bin:$PATH"

COPY nginx.conf /etc/nginx/nginx.conf
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/app/docker-entrypoint.sh"]
