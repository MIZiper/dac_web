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

# Copy the built frontend files
COPY --from=frontend-builder /app/dist /app/frontend/dist
RUN mkdir -p /app/logs
RUN mkdir -p /app/projects
RUN mkdir -p /app/projects_save

# Copy the Python script and API files
COPY backend/ /app/backend/

# Install Python dependencies
RUN pip install -r /app/backend/requirements.txt

ENV FRONTEND_DIST=/app/frontend/dist
ENV LOG_DIR=/app/logs
ENV PROJECT_DIR=/app/projects
ENV PROJECT_SAVE_DIR=/app/projects_save
EXPOSE 8000

# Command to run the router module by default
CMD ["python", "-m", "dac_web.main"]