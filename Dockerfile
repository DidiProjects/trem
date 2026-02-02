FROM python:3.12-slim

WORKDIR /app

LABEL app=trem-api
LABEL project=trem
LABEL maintainer=diego
LABEL version=1.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmupdf-dev \
    ffmpeg \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/uploads

EXPOSE 3002

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3002/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3002"]
