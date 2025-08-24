﻿FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential fonts-dejavu-core ca-certificates && rm -rf /var/lib/apt/lists/*
ENV MPLCONFIGDIR=/tmp/mplconfig PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN mkdir -p /tmp/mplconfig
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
