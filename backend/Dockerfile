FROM python:3.12-alpine

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY data/ /app/data/
COPY Clasmorfismo/ /app/Clasmorfismo/
COPY Glaymorfismo/ /app/Glaymorfismo/
COPY Minimalismo/ /app/Minimalismo/
COPY LiquidGlass/ /app/LiquidGlass/
COPY fork-core/ /app/fork-core/
COPY anteriores/PG1-Muni/Clasmorfismo/ /app/Anteriores/Clasmorfismo/
COPY anteriores/PG1-Muni/Glaymorfismo/ /app/Anteriores/Glaymorfismo/
COPY anteriores/PG1-Muni/Minimalismo/ /app/Anteriores/Minimalismo/
COPY anteriores/PG1-Muni/LiquidGlass/ /app/Anteriores/LiquidGlass/

ENV PORT=80
ENV ROUTES_CONFIG_PATH=/app/data/routes-config.json

EXPOSE 80

CMD ["python", "backend/app.py"]
