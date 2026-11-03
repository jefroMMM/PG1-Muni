FROM python:3.12-alpine

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY data/ /app/data/

ENV PORT=80
ENV ROUTES_CONFIG_PATH=/app/data/routes-config.json

EXPOSE 80

CMD ["python", "-m", "backend.app"]
