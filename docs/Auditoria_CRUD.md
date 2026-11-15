# Auditoría Exhaustiva de Operaciones CRUD y Cancelación en el Sistema

**Proyecto:** Corpo e Mente Biomechanics AI  
**Metodología:** Craig Larman (*Análisis de Brechas, Evidencia Empírica*) & Michael V. Mannino (*Integridad Referencial y Consistencia Transaccional Relacional/Vectorial*)  
**Fecha:** 14 de Noviembre de 2026  
**Objetivo:** Mapeo exhaustivo del soporte actual Frontend vs. Backend para las entidades principales del sistema e identificación de brechas de ciclo de vida, eliminación en cascada y mecanismos de aborto.

---

## 1. Matriz de Cobertura CRUD y Operaciones Críticas

| Entidad | Operación | Backend (API) | Frontend (UI) | Integridad Referencial / Efectos Secundarios |
|---|---|:---:|:---:|---|
| **Usuarios** | **Create (Admin)** | ❌ No | ❌ No | Solo existe auto-registro público de alumnos/profesores (`POST /auth/signup`). El administrador no puede aprovisionar usuarios arbitrarios directamente con contraseñas temporales. |
| | **Read** | ✅ Sí | ⚠️ Parcial | `GET /auth/usuarios` (lista admin), `GET /auth/me` (propio), `GET /auth/alumnos/pendientes` (lista profesor). UI solo muestra perfil individual (`UserProfileModal`) y lista de alumnos pendientes en Pase de Tatami (`ProfesorTecnicas`). No hay vista de gestión de usuarios general. |
| | **Update** | ✅ Sí | ✅ Sí | `PUT /auth/usuarios/{id}` (datos/rol/sucursal), `PUT /auth/usuarios/{id}/idioma`, `PUT /auth/usuarios/{id}/cambiar-sucursal`, `POST /auth/alumnos/{id}/activar`. En UI: `UserProfileModal` y Pase de Tatami. |
| | **Delete** | ❌ No | ❌ No | No existe endpoint `DELETE /auth/usuarios/{id}` ni interfaz para deshabilitar o purgar usuarios. |
| **Sucursales** | **Create (Admin)** | ✅ Sí | ✅ Sí | `POST /sucursales` + `POST /sucursales/parse-gmaps-link`. Formulario modal con geocodificación en `AdminSucursales.jsx`. |
| | **Read** | ✅ Sí | ✅ Sí | `GET /sucursales`. Vista completa en `AdminSucursales.jsx`. |
| | **Update** | ✅ Sí | ✅ Sí | `PUT /sucursales/{id}`. Edición en línea en `AdminSucursales.jsx`. |
| | **Delete** | ✅ Sí | ✅ Sí | `DELETE /sucursales/{id}` vía RPC `admin_delete_sucursal`. Botón con confirmación en `AdminSucursales.jsx`. Restricción FK en cascada/restrict según integridad. |
| **Técnicas** | **Create (Profesor)**| ✅ Sí | ✅ Sí | `POST /tecnicas` (nombre, cinturón, mensaje profesor). Modal en `ProfesorTecnicas.jsx`. |
| | **Read** | ✅ Sí | ✅ Sí | `GET /tecnicas` (incluye banderas `tiene_video`, `tiene_patron`, `video_url`). Lista interactiva en `ProfesorTecnicas.jsx`. |
| | **Update** | ✅ Sí | ✅ Sí | `PUT /tecnicas/{id}` (nombre, cinturón, mensaje). Modal de edición en `ProfesorTecnicas.jsx`. |
| | **Delete** | ⚠️ Parcial | ✅ Sí | En frontend existe botón de eliminar con confirmación. En backend `DELETE /tecnicas/{id}` elimina en PostgreSQL (`admin_delete_tecnica`), **pero NO elimina los vectores de poses en Qdrant (colección `vectores_poses_jiujitsu`) ni los chunks RAG locales en `rag_knowledge`**, dejando vectores huérfanos. |
| **Manuales RAG** | **Subido (Upload)** | ✅ Sí | ✅ Sí | `POST /conocimiento/fuentes/archivo` (PDF/Markdown/Texto). Sube archivo a `/tmp/corpocmente_data/manuales`, extrae chunks con Qwen, indexa en Qdrant `rag_knowledge` y registra en `teoria_referencia`. Soporte en `GlobalKnowledgeModal.jsx`. |
| | **Listado (Read)** | ✅ Sí | ✅ Sí | `GET /conocimiento/manuales`, `GET /conocimiento/fuentes/globales`. Visualización en `LibraryView.jsx` y visor PDF en modal. |
| | **Eliminado (Delete)**| ❌ No | ❌ No | **No existe endpoint para eliminar un archivo de manual (`DELETE /conocimiento/manuales/{filename}`).** Si se sube un documento erróneo, corrupto o desactualizado, queda persistido indefinidamente en disco y en Qdrant. (Existe únicamente `DELETE /conocimiento/teoria/{tecnica_id}` para notas de texto por técnica, pero no para archivos manuales). |
| **Evaluaciones** | **Subido (Upload)** | ✅ Sí | ✅ Sí | `POST /evaluaciones/primer-frame`, `POST /evaluaciones/{session_id}/seleccionar-persona`, `POST /evaluaciones/analizar`. Flujo en `VideoUpload.jsx` y `App.jsx`. |
| | **Listado (Read)** | ✅ Sí | ✅ Sí | `GET /auth/alumnos/{id}/evaluaciones`, `GET /evaluaciones/{evaluacion_id}`. Vista de progreso del alumno en `StudentProgress.jsx` y reporte en `FeedbackView.jsx`. |
| | **Cancelar / Abortar**| ❌ No | ❌ No | **No existe mecanismo de cancelación.** Si el pipeline de YOLO/DTW/VLM tarda o entra en timeout, la UI queda bloqueada en `<ProgressRing>` (`appState === 'PROCESSING'`) sin botón de "Cancelar" o "Abortar", y el cliente HTTP no cuenta con `AbortController` para interrumpir la conexión ni el backend con cancelación de tarea. |

---

## 2. Análisis Detallado por Entidad

### 2.1 Usuarios
* **Estado Actual:**
  * Auto-registro funcional para alumnos y profesores en `LoginModal.jsx`.
  * Los administradores pueden consultar alumnos pendientes y activar sus pases (`POST /auth/alumnos/{id}/activar`).
* **Brechas Críticas (Larman / Mannino):**
  * **Creación Administrativa Ausente:** El administrador no puede crear directamente profesores ni alumnos desde una interfaz administrativa; los profesores deben auto-registrarse.
  * **Eliminación Inexistente:** No existe endpoint `DELETE /api/v1/auth/usuarios/{id}` ni en API ni en UI. Un usuario dado de baja no puede ser eliminado ni desactivado administrativamente (solo esperar expiración del pase).

### 2.2 Sucursales
* **Estado Actual:**
  * **100% Completo.** Es el CRUD de referencia mejor estructurado del sistema:
    * `POST /api/v1/sucursales` con soporte para resolver enlaces de Google Maps.
    * `GET /api/v1/sucursales` para consumo de anon, profesor, alumno y admin.
    * `PUT /api/v1/sucursales/{id}` para actualización atómica.
    * `DELETE /api/v1/sucursales/{id}` con validación de roles en Postgres.
  * UI dedicada en `AdminSucursales.jsx`.

### 2.3 Técnicas
* **Estado Actual:**
  * Create, Read, Update completamente operativos en backend y en `ProfesorTecnicas.jsx`.
* **Brecha de Integridad Híbrida (Mannino):**
  * El endpoint `DELETE /api/v1/tecnicas/{tecnica_id}` invoca el RPC `admin_delete_tecnica`, que elimina el registro en PostgreSQL.
  * **Falta de limpieza vectorial:** No se invoca a `QdrantVectorAdapter.eliminar_patron()` ni se borran los puntos asociados a `tecnica_id` en `rag_knowledge` o `vectores_poses_jiujitsu`. Los vectores quedan huérfanos ocupando memoria en Qdrant.

### 2.4 Manuales RAG (Biblioteca de Conocimiento)
* **Estado Actual:**
  * Subida de archivos (`POST /api/v1/conocimiento/fuentes/archivo`) con segmentación multimodal e indexación vectorial (Qwen3-VL 2048 dims).
  * Listado en `LibraryView.jsx` con búsqueda densa y renderizado de páginas/imágenes.
* **Brecha Crítica:**
  * **Cero soporte de eliminación de manuales.** No hay `DELETE /api/v1/conocimiento/manuales/{filename}` ni botón en `LibraryView.jsx` o `GlobalKnowledgeModal.jsx`.
  * **Consecuencia:** Imposibilidad de retirar documentos obsoletos, reglas desactualizadas o archivos subidos por error. Una vez que un manual entra en Qdrant, permanece en el índice permanentemente.

### 2.5 Evaluaciones de Video (Ciclo de Vida y Aborto)
* **Estado Actual:**
  * Flujo de subida robusto en 3 etapas: validación anti-spam ViCoS -> selección interactiva de persona -> análisis biomecánico con DTW y VLM.
* **Brecha Operativa Crítica:**
  * **No existe botón de Cancelar/Abortar en la interfaz.**
  * Durante el estado `UPLOADING` o `PROCESSING`, la interfaz de usuario en `App.jsx` renderiza un anillo de progreso infinito:
    ```jsx
    {(appState === 'UPLOADING' || appState === 'PROCESSING') && (
      <ProgressRing value={appState === 'UPLOADING' ? uploadProgress : 'indeterminate'} />
    )}
    ```
  * No hay control `AbortController` en el `fetch` de JavaScript.
  * No hay endpoint en backend para cancelar o desechar la sesión de análisis en curso (`POST /api/v1/evaluaciones/{evaluacion_id}/abortar`).
  * **Experiencia de Usuario:** Si el modelo local o el worker tarda más de lo previsto, el usuario está forzado a recargar la pestaña del navegador (F5), dejando un proceso zombie en el backend.

---

## 3. Recomendación de Priorización para la Siguiente Iteración

1. **Prioridad 1 (Resiliencia y UX):** Implementar botón de **Cancelar/Abortar Evaluación** en `App.jsx` con `AbortController` en el cliente y liberación de sesión en backend.
2. **Prioridad 2 (Integridad de Datos Mannino):** Implementar **Eliminación de Manuales RAG** con limpieza atómica bidireccional (PostgreSQL `teoria_referencia` + Qdrant `rag_knowledge` + archivo físico).
3. **Prioridad 3 (Higiene Vectorial):** Conectar `DELETE /tecnicas/{id}` con la purga de vectores de poses y evidencias RAG en Qdrant.
4. **Prioridad 4 (Administración):** Implementar creación y eliminación administrativa de usuarios.
