FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY chitara/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY chitara/ .
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

RUN mkdir -p /app/data

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
