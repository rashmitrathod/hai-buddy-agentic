FROM python:3.11-slim

# avoid prompts during apt
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# system deps (minimal); add libs if any package needs them later
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy requirements first to leverage docker cache
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy app code and static frontend
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# expose Cloud Run port (Cloud Run uses 8080)
EXPOSE 8080

# run uvicorn on port 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]