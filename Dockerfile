FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy the application code
COPY ./backend ./backend
COPY ./frontend/dist ./frontend

# Expose the port the router module listens on
EXPOSE 5000

# Command to run the router module by default
CMD ["python", "backend/router.py"]
