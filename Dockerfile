# -------------------------------------------------------------
# 1. Base Python runtime
# -------------------------------------------------------------
FROM python:3.11-slim

# -------------------------------------------------------------
# 2. Install system dependencies (minimal)
# -------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------
# 3. Set working directory
# -------------------------------------------------------------
WORKDIR /app

# -------------------------------------------------------------
# 4. Copy project files
# -------------------------------------------------------------
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# -------------------------------------------------------------
# 5. Expose port
# Cloud Run ignores EXPOSE but good for documentation
# -------------------------------------------------------------
EXPOSE 8080

# -------------------------------------------------------------
# 6. Run FastAPI app on port 8080 (Cloud Run requirement)
# -------------------------------------------------------------
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]