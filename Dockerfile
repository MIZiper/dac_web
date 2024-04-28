FROM python:3.11-slim

WORKDIR /app

# Copy the application code
COPY ./backend ./backend
COPY ./frontend/dist ./frontend/dist
RUN mkdir -p ./projects
RUN mkdir -p ./projects_save

RUN pip install -r ./backend/requirements.txt

# Expose the port the router module listens on
EXPOSE 5000

# Command to run the router module by default
CMD ["python", "backend/router_entry.py"]
