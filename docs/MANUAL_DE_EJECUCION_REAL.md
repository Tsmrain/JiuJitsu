# Manual de Ejecución Real - BJJ Biomechanics Assistant

## 1. Levantar el Backend Local (Docker)
Abre una terminal en la carpeta del proyecto y ejecuta:
```bash
docker compose up --build -d
```
*Esto iniciará PostgreSQL con pgvector y la API FastAPI en el puerto 8000.*

## 2. Activar el Cerebro en Google Colab (Con GPU T4 / A100)

Tienes dos opciones equivalentes para ejecutarlo:

### Opción A: Desde tu IDE (Usando la Extensión de Google Colab)
1. Abre [`colab_backend.ipynb`](colab_backend.ipynb) en el editor.
2. En la esquina superior derecha del notebook, haz clic en el botón de **Seleccionar Kernel** (o el ícono de Colab).
3. Selecciona **Google Colab** y pulsa en **Connect to Google Colab** (o reconectar si la sesión anterior expiró).
4. **Importante:** Asegúrate de seleccionar un entorno con **GPU (T4 o A100)**, no CPU.
5. En la **Celda 5**, ingresa tu token de Ngrok (`NGROK_AUTH_TOKEN = "..."`).
6. Ejecuta las celdas en orden (o pulsa "Run All").
7. Copia la URL pública HTTPS de Ngrok (`https://xxxx.ngrok-free.app`).

### Opción B: Desde el Navegador Web (Alternativa directa)
1. Entra en [Google Colab](https://colab.research.google.com/).
2. Haz clic en **Archivo > Subir notebook** y sube [`colab_backend.ipynb`](colab_backend.ipynb).
3. En **Entorno de ejecución > Cambiar tipo de entorno de ejecución**, elige **GPU T4** o **A100**.
4. En la **Celda 5**, ingresa tu token de Ngrok y ejecuta todas las celdas.
5. Copia la URL de Ngrok generada.

## 3. Conectar los Puntos
1. Abre el archivo `.env` en la raíz.
2. Actualiza `COLAB_TUNNEL_URL` con la URL de Ngrok copiada.
3. Verifica que tu `GEMINI_API_KEY` esté correcta.

## 4. Prueba de Fuego (End-to-End)
Ejecuta el script de validación real desde la terminal:
```bash
.venv/bin/python demo_e2e.py
```
*Si ves respuestas exitosas de Colab y de la API Local, ¡el sistema está vivo!*
