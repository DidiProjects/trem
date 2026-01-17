FROM python:3.12-slim

WORKDIR /app

# Labels para identificação segura na limpeza
LABEL app=trem-api
LABEL project=trem
LABEL maintainer=diego
LABEL version=1.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/uploads

EXPOSE 3002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3002"]
