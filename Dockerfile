# Stage 1: Build the dac-frontend (Svelte 5)
FROM node:22-slim AS frontend-builder
WORKDIR /app
RUN npm install -g pnpm
COPY dac-frontend/package.json dac-frontend/pnpm-workspace.yaml ./
RUN --mount=type=secret,id=ado_pat \
    ADO_PAT=$(cat /run/secrets/ado_pat) && \
    echo "@xdm:registry=https://pkgs.dev.azure.com/[org]/_packaging/[feed]/npm/registry/" >> .npmrc && \
    echo "//pkgs.dev.azure.com/[org]/_packaging/[feed]/npm/registry/:_authToken=${ADO_PAT}" >> .npmrc && \
    pnpm install && \
    rm .npmrc
COPY dac-frontend/ ./
RUN pnpm build

# Stage 2: Set up the Python environment
FROM python:3.12-slim
WORKDIR /app

RUN mkdir -p /app/storage/logs /app/storage/projects /app/storage/projects_save

# Install pip-tools from public PyPI (no secret needed)
RUN pip install pip-tools

COPY backend/pyproject.toml backend/README.md ./

RUN --mount=type=secret,id=ado_pat \
    ADO_PAT=$(cat /run/secrets/ado_pat) && \
    export PIP_EXTRA_INDEX_URL="https://[org]:${ADO_PAT}@pkgs.dev.azure.com/[org]/_packaging/[feed]/pypi/simple/" && \
    pip-compile pyproject.toml --output-file=requirements.txt && \
    pip install -r requirements.txt

# Copy backend source and install the package
COPY backend/ ./backend-src
RUN pip install ./backend-src

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/dist /app/frontend-dist

ENV FRONTEND_DIST=/app/frontend-dist
ENV LOG_DIR=/app/storage/logs
ENV PROJECT_DIR=/app/storage/projects
ENV PROJECT_SAVE_DIR=/app/storage/projects_save
ENV APP_LOG_ON=1
ENV DBSTORE=false
ENV POSTGRES_HOST=localhost
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=dac
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=password
ENV KEYCLOAK_URL=""
ENV KEYCLOAK_URL_PUBLIC=""
ENV KEYCLOAK_REALM=""
ENV KEYCLOAK_CLIENT_ID=""
ENV KEYCLOAK_CLIENT_SECRET=""

EXPOSE 8000

CMD ["uvicorn", "dac_web.main:app", "--host", "0.0.0.0", "--port", "8000"]
