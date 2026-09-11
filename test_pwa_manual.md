# Protocolo de Prueba Manual: Progressive Web App (PWA) BJJ Biomechanics

Este documento detalla el procedimiento de verificación ergonómica y funcional de la PWA para dispositivos móviles según los requisitos **RD-03**, **RF-02**, **AS-02** y **RP-03**.

---

## 1. Preparación del Servidor Local

Asegúrate de que la API esté activa con el entorno virtual:

```bash
cd /home/santiago/Desktop/JiuJitsu
source .venv/bin/activate
uvicorn src.presentation.api:app --host 0.0.0.0 --port 8000 --reload
```

---

## 2. Verificación en Chrome DevTools (Modo Dispositivo Móvil)

1. Abre Google Chrome o Chromium e ingresa a:
   ```text
   http://localhost:8000/
   ```
2. Presiona `F12` o `Ctrl + Shift + I` para abrir las **Herramientas de Desarrollador (DevTools)**.
3. Activa el modo de emulación de dispositivos móviles haciendo clic en el icono **Toggle device toolbar** (`Ctrl + Shift + M`).
4. Selecciona las siguientes resoluciones en el selector superior:
   - **iPhone X / 12 / 13 / 14 Pro:** `375 x 812 px` (DPR 3.0)
   - **Samsung Galaxy S20 / S8:** `360 x 740 px`
   - **iPhone SE:** `375 x 667 px`

---

## 3. Lista de Comprobación Funcional (Checklist)

### A. Control de Acceso y Selección de Rol (Practicante vs Instructor)
1. Al cargar la app por primera vez:
   - [ ] Se despliega el **Modal de Selección de Rol** sobre un fondo difuminado (*blur*).
   - [ ] La barra de navegación principal permanece oculta hasta autenticar.
2. Ingreso como **Practicante**:
   - [ ] Escribe el PIN `1234` y presiona **"Soy Practicante"**.
   - [ ] El modal desaparece, la barra de navegación muestra solo **"Evaluar Técnica"** e **"Historial"** (la pestaña de instructor permanece oculta).
   - [ ] La insignia en el header muestra `Rol: Practicante` con acento cian.
3. Cambio de Rol a **Instructor**:
   - [ ] Presiona el enlace **"Cambiar Rol"** en el header.
   - [ ] Se abre nuevamente el modal. Escribe el PIN `9876` y presiona **"Soy Instructor"**.
   - [ ] El header adopta el modo instructor con borde ámbar (`#F59E0B`) y la insignia `Rol: Instructor (Master)`.
   - [ ] Aparece la tercera pestaña: **"Registrar Patrón"**.

### B. Registro de Técnica Patrón por el Instructor (CU-01)
1. Haz clic en la pestaña **"Registrar Patrón"**:
   - [ ] Se despliega el formulario con campos: `ID Técnico`, `Nombre`, `Descripción` y Dropzone del Maestro.
2. Ingresa los datos:
   - ID Técnico: `omoplata_invertida`
   - Nombre: `Omoplata Invertida`
   - Descripción: `Control de cintura escapular y torsión articular con las piernas`
3. Arrastra o selecciona el video del Maestro (`tests/fixtures/test_video.mp4`).
4. Presiona **"Guardar Patrón 3D"**:
   - [ ] Se envía `multipart/form-data` a `/api/v1/tecnicas/registrar`.
   - [ ] Se muestra notificación toast de éxito.
   - [ ] El selector de técnicas en la pestaña "Evaluar" se actualiza dinámicamente incluyendo la nueva técnica sin recargar la página.

### C. Inspección Visual y Ergonomía (AS-02)
- [ ] **Header y Branding:** El logotipo SVG y el título `BJJ BIOMECHANICS` se adaptan sin desbordamiento horizontal (`overflow-x: hidden`).
- [ ] **Touch Targets:** Todos los botones (`Evaluar Técnica`, `Historial`, `Registrar Patrón`, `Analizar Biomecánica`) y campos tienen una altura táctil $\ge 44\text{px}$.
- [ ] **Contraste y Paleta:** Modo oscuro en negro mate (`#07090E`) con acentos en cian eléctrico (`#00F0FF`) o ámbar (`#F59E0B`) en modo instructor.

### D. Validación de Entrada de Video (RF-02)
1. Intenta arrastrar o seleccionar un archivo mayor a 50MB:
   - [ ] Debe aparecer una notificación Toast roja indicando que el archivo excede el límite máximo.
2. Selecciona un video válido (`tests/fixtures/test_video.mp4`):
   - [ ] La zona de dropzone se oculta y aparece la ficha del archivo con el nombre y tamaño en MB.
   - [ ] El botón **Analizar Biomecánica 3D** pasa a estado activo.

### E. Flujo de Evaluación Asíncrona (CU-02 & CU-03)
1. Presiona **Analizar Biomecánica 3D**:
   - [ ] La tarjeta de estado se despliega con la barra de progreso animada y los hitos visuales (`1. Subida`, `2. YOLO26x 3D`, `3. Cinemática`, `4. Gemini IA`).
   - [ ] El cliente realiza polling no bloqueante cada 3 segundos a `/api/v1/evaluaciones/tareas/{id}`.
2. Al completar la tarea:
   - [ ] Se oculta la tarjeta de carga y se anima la tarjeta de **Resultados**.
   - [ ] Se muestra la insignia de estado (`EJECUCIÓN CORRECTA` o `DESVIACIONES DETECTADAS`).
   - [ ] Métrica en número grande: Desviación Promedio en grados (ej: `12.0°`).
   - [ ] **Canvas Esquelético:** El muñeco cinemático renderiza los keypoints COCO y resalta en rojo parpadeante las articulaciones que registraron desviaciones angulares.
   - [ ] **Consejo Pedagógico:** Se renderiza el diagnóstico de Google Gemini.

### F. Historial y Progreso (CU-04)
1. Haz clic en la pestaña **Historial**:
   - [ ] El ID de alumno se sincroniza automáticamente con el del header.
   - [ ] Se consultan las evaluaciones previas en PostgreSQL a través de `GET /api/v1/alumnos/{id}/progreso`.
   - [ ] Se visualiza el contador de evaluaciones totales y la tasa de aprobación.
   - [ ] Cada tarjeta histórica muestra la fecha formateada, técnica, etiqueta y consejo resumido.

### E. Service Worker y Auditoría PWA
1. En DevTools, ve a la pestaña **Application**:
   - [ ] **Manifest:** Verifica que detecte el nombre "Asistente Biomecánico BJJ", short_name "BJJ Bio", start_url `/`, theme_color `#0B0F19` y el icono SVG.
   - [ ] **Service Workers:** Verifica que el Service Worker `/static/service-worker.js` esté en estado `Activated and is running`.
   - [ ] **Cache Storage:** Verifica que exista la cache `bjj-bio-cache-v1` con los assets estáticos del shell (`style.css`, `app.js`, `manifest.json`, `icon.svg`).
2. En la pestaña **Console**:
   - [ ] Confirma que no existan errores rojos de Javascript o advertencias de bloqueo de recursos.

---

## 4. Prueba en Dispositivo Móvil Real (Tatami / Red Local)

Para abrir la PWA en tu smartphone real conectado a la misma red Wi-Fi:
1. Obtén la IP local de tu laptop:
   ```bash
   hostname -I | awk '{print $1}'
   ```
2. En el navegador de tu celular (Chrome en Android o Safari en iOS), ingresa:
   ```text
   http://<TU_IP_LOCAL>:8000/
   ```
3. Opcional: En Chrome/Safari, selecciona **"Agregar a la pantalla de inicio"** para instalar la PWA como aplicación nativa standalone.
