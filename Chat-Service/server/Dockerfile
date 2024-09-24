# FastAPI Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY ../../requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI app source code
COPY . /app

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run FastAPI server
CMD ["uvicorn", "main:chat_service_app", "--host", "0.0.0.0", "--port", "8000"]
