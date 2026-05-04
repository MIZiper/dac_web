# Stage 1: Build the dac-frontend (Svelte 5)
FROM node:22-slim AS frontend-builder
WORKDIR /app
RUN npm install -g pnpm
COPY dac-frontend/package.json dac-frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY dac-frontend/ ./
RUN pnpm build

# Stage 2: Set up the Python environment
FROM python:3.12-slim
WORKDIR /app

RUN mkdir -p /app/storage/logs /app/storage/projects /app/storage/projects_save

# Install Python dependencies (layer cached when pyproject.toml unchanged)
RUN pip install pip-tools
COPY backend/pyproject.toml backend/README.md ./
RUN pip-compile pyproject.toml --output-file=requirements.txt
RUN pip install -r requirements.txt

# Copy backend source and install the package
COPY backend/ ./
RUN pip install .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/dist /app/frontend/dist

ENV FRONTEND_DIST=/app/frontend/dist
ENV LOG_DIR=/app/storage/logs
ENV PROJECT_DIR=/app/storage/projects
ENV PROJECT_SAVE_DIR=/app/storage/projects_save
ENV APP_LOG_ON=1
ENV DBSTORE=true
ENV POSTGRES_HOST=postgres
ENV KEYCLOAK_URL=""
ENV KEYCLOAK_REALM=""
ENV KEYCLOAK_CLIENT_ID=""
ENV KEYCLOAK_CLIENT_SECRET=""

EXPOSE 8000

CMD ["python", "-m", "dac_web.main"]
