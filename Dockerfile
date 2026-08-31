# Imagen base oficial y ligera
FROM python:3.10-slim

# Metadatos del contenedor
LABEL maintainer="Santiago Borda Zambrana <01hanssantiago@gmail.com>"
LABEL description="Custom Container para Huawei Cloud FunctionGraph - Análisis Biomecánico BJJ"

# Variables de entorno para Python y buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

# 1. Dependencias de Sistema (OpenCV, FFmpeg y utilidades de compilación)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Usuario de Seguridad (Requisito estricto Huawei Cloud: UID 1003 no privilegiado)
RUN groupadd -g 1003 appgroup && useradd -u 1003 -g appgroup -m appuser

# 3. Instalación de PyTorch CPU-Only (Crítico para costos y optimización de tamaño < 1.5 GB)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 4. Integración de RTMPose3D
RUN git clone https://github.com/b-arac/rtmpose3d.git /opt/rtmpose3d
WORKDIR /opt/rtmpose3d
RUN pip install --no-cache-dir -r requirements.txt

# 5. Código y Dependencias del Proyecto
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/

# 6. Configuración de Permisos para Usuario UID 1003
RUN mkdir -p /app /opt/rtmpose3d /tmp && \
    chown -R 1003:1003 /app /opt/rtmpose3d /tmp

# Establecer usuario de ejecución no privilegiado
USER 1003

# 7. Exposición de Puerto Requerido por FunctionGraph (8000)
EXPOSE 8000

# 8. Punto de Entrada HTTP (FastAPI Wrapper / Uvicorn)
CMD ["uvicorn", "src.infrastructure.serverless.container_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
