FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set working directory to backend
WORKDIR /app/backend

# Default port (Railway will override via PORT env var)
ENV PORT=8000
EXPOSE 8000

# Run the application using shell form to expand $PORT
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
