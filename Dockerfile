# Imagen de la API (Flask). MongoDB NO va aqui: usa la imagen oficial "mongo"
# y se levanta junto con esta desde docker-compose.yml.

# pymongo 4.19 necesita Python 3.11 o superior.
FROM python:3.12-slim

# Sin archivos .pyc y con la salida de print() visible al instante en los logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero solo las dependencias: si no cambia requirements.txt, Docker
# reutiliza esta capa y el build siguiente es casi instantaneo.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Despues el codigo (.dockerignore deja fuera .env, .venv, etc.)
COPY . .

# Valores por defecto. docker-compose.yml los sobreescribe.
ENV HOST=0.0.0.0 \
    PORT=5000 \
    FLASK_DEBUG=0 \
    MONGO_URI=mongodb://mongo:27017 \
    MONGO_DB=catalogo

EXPOSE 5000

CMD ["python", "run.py"]
