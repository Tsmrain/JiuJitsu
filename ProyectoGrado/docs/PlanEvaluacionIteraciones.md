# Bitácora y Plan de Evaluación de Iteraciones (Agile UP - Craig Larman)

Este documento registra oficialmente la planificación, mitigación de riesgos y evaluación de cada incremento ejecutable del proyecto **Corpo e Mente**, alineado estrictamente con los principios del **Proceso Unificado (UP)** expuestos por Craig Larman en *"Applying UML and Patterns"*.

---

## 📌 Principios de Evaluación Iterativa de Larman
1. **Iteraciones acotadas en tiempo (Timeboxed):** Cada ciclo entrega un subconjunto de software funcional y probado.
2. **Desarrollo impulsado por riesgos (Risk-Driven Development):** Los aspectos de mayor incertidumbre (IA multimodal, arquitectura vectorial, cuotas de API) se abordan primero.
3. **Adaptación continua:** La retroalimentación directa del cliente/usuario en cada ciclo refina el diseño del ciclo subsiguiente.

---

## 📋 Histórico de Iteraciones Ejecutadas

### 🔹 Iteración 1 & 2 (Fase de Elaboración): Arquitectura de Datos e Inferencia
- **Objetivo:** Mitigar riesgos de rendimiento vectorial, diseño de esquema relacional (3NF) y desacoplamiento de modelos de IA.
- **Riesgos Mitigados:**
  - Definición del esquema multi-tenant en PostgreSQL con Row Level Security (RLS) y JWT.
  - Implementación del patrón *Adapter (GoF)* para YOLOv11 Pose (`yolo11n-pose.pt`) y Qdrant Vector DB.
- **Resultado:** Pruebas unitarias ejecutadas con éxito (`test_yolo_adapter.py`, `test_intelligence_facade.py`).

---

### 🔹 Iteración C3 (Fase de Construcción): Sistema de Diseño e Interfaz Web
- **Objetivo:** Construir la interfaz de usuario moderna de grado de producción (Web App).
- **Entregables:**
  - Aplicación Vite + React estilizada en Vanilla CSS (Tema Oscuro con Rojo Institucional `#d01118`, Glassmorphism).
  - Componente semántico `<progress>` nativo animado (`ProgressRing.jsx`).
  - Previsualización dinámica de video mediante `URL.createObjectURL` (`VideoUpload.jsx`).
  - Integración del logo oficial de la academia (`logo.jpeg`).
- **Verificación:** Evaluado y aprobado por el cliente directamente en el navegador.

---

### 🔹 Iteración C4-A (Fase de Construcción): Filtro Multimodal Anti-SPAM
- **Objetivo:** Probar en vivo el filtrado temprano de contenido no relacionado mediante Google Gemini API antes de consumir recursos de GPU.
- **Desafíos Técnicos y Lecciones Aprendidas:**
  - **Sintaxis de SDK:** Ajuste del parámetro `path` en `client.files.upload(path=...)` del SDK `google-genai`.
  - **Estados Multimodales:** Manejo del ciclo de vida del archivo en Gemini (`PROCESSING` -> `ACTIVE`).
  - **Desacoplamiento (Resiliencia):** Aplicación de *Lazy Loading* en los adaptadores pesados (`YOLOPoseAdapter` y `QdrantVectorAdapter`) para evitar fallos durante el arranque de FastAPI.
- **Verificación:** Probado y confirmado en vivo por el cliente rechazando videos ajenos a Jiu-Jitsu (HTTP 422) y dejando pasar ejecuciones válidas (HTTP 200).

### 🔹 Iteración C5 (Fase de Construcción): Autenticación por Roles y Sucursales con Mapa Gratuito
- **Objetivo:** Implementar la autenticación de roles (`alumno`, `profesor`, `admin`) y permitir al administrador crear sucursales mundiales fijando coordenadas mediante un mapa interactivo **100% gratuito (sin Google Maps API keys)**.
- **Entregables:**
  - Componente modal de autenticación (`LoginModal.jsx`) conectando con el backend `/api/v1/auth/login`.
  - Panel de Administración Multi-Tenant (`AdminSucursales.jsx`) integrado con **Leaflet.js + OpenStreetMap** para capturar `latitud` y `longitud` al hacer clic en cualquier lugar del mundo.
  - Actualización del esquema 3NF (`01_schema_3nf.sql`) añadiendo columnas de latitud y longitud.
  - Endpoints REST en FastAPI (`auth_routes.py`) para `/auth/login` y `/sucursales`.
- **Verificación:** Funciona en la interfaz web cambiando de perfil a Administrador y marcando cualquier sucursal en el mapa de OpenStreetMap.

---

## 🚀 Plan para las Próximas Iteraciones

| Iteración | Enfoque Principal | Riesgos / Objetivos a Resolver | Artefactos Impactados |
| :--- | :--- | :--- | :--- |
| **C6** | Integración Full-Stack con BD Persistente | Conectar PostgREST / PostgreSQL local con la interfaz y el Worker de Colab para completar el ciclo de evaluación. | `routes.py`, `App.jsx`, `AnalisiDiseno.md` |
| **Transición** | Pruebas Beta y Despliegue | Generación del cuaderno `.ipynb` listo para Colab Pro y pruebas de campo en academias. | `Colab_Worker.ipynb`, `Manual_Usuario.md` |
