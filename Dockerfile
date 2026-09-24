FROM python:3.12-slim

# Logs go straight to the container's stdout instead of sitting in a buffer.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The database lives on a volume mounted at /app/data so it survives rebuilds.
# Creating the directory here lets a fresh named volume inherit its ownership,
# which is what allows the non-root user below to write to it.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/data \
    && chown -R app:app /app/data
USER app

ENV DB_PATH=/app/data/main.db

CMD ["python", "client.py"]
