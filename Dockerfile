# Stage 1: Build the frontend
FROM node:22-slim AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Set up the Python environment
FROM python:3.12-slim
WORKDIR /app
RUN mkdir -p /app/logs
RUN mkdir -p /app/projects
RUN mkdir -p /app/projects_save
RUN pip install pip-tools
COPY backend/pyproject.toml ./
RUN pip-compile pyproject.toml --output-file=requirements.txt
RUN pip install -r requirements.txt

COPY --from=frontend-builder /app/dist /app/frontend/dist
COPY backend/ /app/backend/
RUN pip install ./backend

ENV FRONTEND_DIST=/app/frontend/dist
ENV LOG_DIR=/app/logs
ENV PROJECT_DIR=/app/projects
ENV PROJECT_SAVE_DIR=/app/projects_save
ENV APP_LOG_ON=1
EXPOSE 8000

# Command to run the router module by default
CMD ["python", "-m", "dac_web.main"]