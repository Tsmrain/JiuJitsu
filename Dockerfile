FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instalar versión CPU ligera de PyTorch para el API Server (la inferencia GPU reside en Colab)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.presentation.api:app", "--host", "0.0.0.0", "--port", "8000"]
