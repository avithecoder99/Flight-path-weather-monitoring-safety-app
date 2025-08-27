FROM python:3.11-slim
<<<<<<< HEAD

# System deps for scientific libs + fonts for matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential fonts-dejavu-core ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Matplotlib writable config dir (headless)
=======
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential fonts-dejavu-core ca-certificates && \
    rm -rf /var/lib/apt/lists/*
>>>>>>> ac2cfa8 (final commit - updated code)
ENV MPLCONFIGDIR=/tmp/mplconfig \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
RUN mkdir -p /tmp/mplconfig
<<<<<<< HEAD

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Expose & launch (2 workers for a bit more concurrency)
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--timeout-keep-alive", "10"]
=======
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","2","--timeout-keep-alive","10"]
>>>>>>> ac2cfa8 (final commit - updated code)
