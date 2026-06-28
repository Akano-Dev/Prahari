# ScamShield API image. Installs the engine + API with production extras.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv

# Copy the engine package and the API service (monorepo build context = repo root).
COPY packages/ai_engine /srv/packages/ai_engine
COPY services/api /srv/services/api

RUN pip install --no-cache-dir -e /srv/packages/ai_engine \
 && pip install --no-cache-dir -e "/srv/services/api[postgres,redis,reports]"

WORKDIR /srv/services/api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
