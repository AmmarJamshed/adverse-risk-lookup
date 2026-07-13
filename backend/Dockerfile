FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

COPY . .

RUN mkdir -p /app/uploads /app/logs /app/data/faiss_index /data \
    && chmod +x /app/docker-entrypoint.sh

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV USE_FAISS_FALLBACK=true
ENV APP_ENV=production
ENV APP_DEBUG=false
ENV DATABASE_URL=sqlite:////data/arl.db
# Hugging Face Spaces expects 7860
ENV PORT=7860

EXPOSE 7860

CMD ["/app/docker-entrypoint.sh"]
