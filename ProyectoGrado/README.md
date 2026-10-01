# Corpo e Mente - Sistema Biomecánico con IA

Este repositorio contiene el código fuente completo del sistema de evaluación biomecánica y gestión de conocimiento (RAG) para la academia Corpo e Mente.

El sistema se compone de cuatro grandes pilares:
1. **Base de Datos y Motores de Búsqueda:** PostgreSQL + PostgREST + Qdrant.
2. **Backend (API):** FastAPI (Orquestador de IA).
3. **Colab Worker:** Servidor de Inferencia Remota en GPU (YOLOv8 + Qwen3-VL).
4. **Frontend:** React 19 + Vite.

---

## 📋 Requisitos Previos

Asegúrate de tener instalado:
* **PostgreSQL** (versión 14 o superior)
* **Docker** y **Docker Compose**
* **Python 3.10+** (recomendado 3.11 o 3.12)
* **Node.js** (versión 18+ o 20+)
* Una cuenta de Google (para Google Colab y Gemini API)
* Una cuenta de [ngrok](https://ngrok.com/) (para exponer el Colab Worker)

---

## 🚀 Guía de Instalación y Ejecución

Sigue estos pasos en orden para levantar el sistema completo localmente.

### 1. Base de Datos Relacional (PostgreSQL)

El sistema requiere una base de datos local y ejecutar las migraciones para construir el esquema 3NF, funciones de seguridad (RLS) y tablas base.

1. Abre tu cliente de PostgreSQL (pgAdmin, DBeaver o psql).
2. Crea una base de datos llamada `corpocmente`:
   ```sql
   CREATE DATABASE corpocmente;
   ```
3. Ejecuta los scripts SQL ubicados en `codigo_fuente/database/` **en estricto orden**:
   * `01_schema_3nf.sql`
   * `02_auth_jwt.sql`
   * `03_rls_policies.sql`
   * `04_seed_data.sql`
   * `05_teoria_referencia.sql`

### 2. Base de Datos Vectorial (Qdrant)

Qdrant se utiliza para el sistema RAG (almacenamiento y recuperación semántica de la teoría de Jiu-Jitsu).

1. Abre una terminal en la carpeta principal `ProyectoGrado/`.
2. Levanta el contenedor usando Docker Compose:
   ```bash
   docker compose up -d
   ```
*Qdrant estará disponible en `http://localhost:6333`.*

### 3. Worker de Inferencia en GPU (Google Colab)

Debido al alto consumo de VRAM de los modelos YOLO y Qwen, la extracción biomecánica y embeddings se ejecutan de forma remota y gratuita en Google Colab.

1. Sube el archivo `codigo_fuente/backend/notebooks/colab_worker.ipynb` a tu cuenta de Google Colab (https://colab.research.google.com/).
2. Ve a **Entorno de ejecución > Cambiar tipo de entorno de ejecución** y selecciona **T4 GPU**.
3. Reemplaza el token de ngrok en la celda correspondiente por tu token real de ngrok.
4. Ejecuta todas las celdas (`Entorno de ejecución > Ejecutar todo`).
5. Al final de la última celda, ngrok imprimirá una URL pública (ej. `https://xxxx-xx-xx-xx.ngrok-free.app`). **Copia esa URL.**

### 4. Configuración del Backend (FastAPI + PostgREST)

El backend orquesta la comunicación entre el Frontend, PostgREST, Qdrant, Gemini y el Colab Worker.

1. Abre una terminal en `codigo_fuente/backend/`.
2. Crea y activa un entorno virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Linux/Mac
   # venv\Scripts\activate   # En Windows
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura las variables de entorno:
   * Copia el archivo `.env.example` y renómbralo a `.env`.
   * Pega la URL del paso anterior en `COLAB_TUNNEL_URL`.
   * Añade tu clave de la API de Gemini en `GEMINI_API_KEY`.
   * Configura una cadena larga y segura en `POSTGREST_JWT_SECRET` y `JWT_SECRET_KEY` (deben coincidir).
5. Inicia el servidor **PostgREST** (usando el binario incluido o instalandolo globalmente):
   ```bash
   ./postgrest postgrest.conf
   ```
6. En **otra terminal** (con el entorno virtual activado), inicia el servidor **FastAPI**:
   ```bash
   uvicorn corpocmente.ui.api.main:app --reload --port 8000
   ```

### 5. Interfaz de Usuario (Frontend React)

1. Abre una terminal en `codigo_fuente/frontend/`.
2. Instala las dependencias de Node:
   ```bash
   npm install
   ```
3. Inicia el servidor de desarrollo de Vite:
   ```bash
   npm run dev
   ```
4. Abre tu navegador en la URL que te indique (usualmente `http://localhost:5173`).

---

## 🔑 Credenciales de Prueba

Si ejecutaste el archivo `04_seed_data.sql`, cuentas con los siguientes usuarios predeterminados para probar los 3 roles del sistema:

* **Administrador:** `admin@corpocmente.com` / `admin123`
* **Profesor:** `mike@corpocmente.com` / `profesor123`
* **Alumno:** `alumno@corpocmente.com` / `alumno123`

---

## 🛑 Cómo detener el sistema
* **Frontend y Backend (FastAPI/PostgREST):** Usa `Ctrl + C` en las terminales donde los estés ejecutando.
* **Qdrant:** Ejecuta `docker compose down` en la carpeta raíz.
* **Colab Worker:** Ve a Google Colab y selecciona *Entorno de ejecución > Desconectar y eliminar entorno de ejecución*.
