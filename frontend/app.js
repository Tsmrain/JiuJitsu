// frontend/app.js - Logica Cliente BJJ Biomechanics

document.addEventListener('DOMContentLoaded', () => {
    // Registrar Service Worker para PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/service-worker.js')
            .catch(() => {});
    }

    // Verificar rol recordado
    const rolGuardado = localStorage.getItem('user_role');
    if (rolGuardado === 'instructor' || rolGuardado === 'alumno') {
        seleccionarRol(rolGuardado);
    }

    // Listener para habilitar boton comenzar practica al elegir tecnica
    const selectTecnica = document.getElementById('alumno-tecnica');
    const btnComenzar = document.getElementById('btn-comenzar-practica');
    if (selectTecnica && btnComenzar) {
        selectTecnica.addEventListener('change', () => {
            btnComenzar.disabled = !selectTecnica.value;
        });
    }
});

// Alias para compatibilidad
function selectRole(rol) {
    return seleccionarRol(rol);
}


// --- 1. Notificaciones Toast ---
function mostrarToast(mensaje, tipo = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${tipo === 'error' ? 'toast-error' : tipo === 'success' ? 'toast-success' : ''}`;
    toast.textContent = mensaje;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.25s ease';
        setTimeout(() => toast.remove(), 250);
    }, 3500);
}

// --- 2. Control de Roles (Instructor vs Alumno) ---
function renderizarNavegacion(rol) {
    const nav = document.getElementById('nav-pwa-bottom');
    if (!nav) return;

    if (rol === 'alumno') {
        nav.innerHTML = `
            <button class="nav-item nav-item-activo" id="nav-btn-evaluar" onclick="navegarAlumno('evaluar')">
                <svg class="nav-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                <span class="nav-label">Evaluar</span>
            </button>
            <button class="nav-item" id="nav-btn-progreso" onclick="navegarAlumno('progreso')">
                <svg class="nav-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                </svg>
                <span class="nav-label">Mi Progreso</span>
            </button>
            <button class="nav-item" id="nav-btn-recursos" onclick="navegarAlumno('recursos')">
                <svg class="nav-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                </svg>
                <span class="nav-label">Recursos</span>
            </button>
        `;
        nav.style.display = 'flex';
    } else if (rol === 'instructor') {
        nav.innerHTML = `
            <button class="nav-item nav-item-activo" id="nav-btn-reg-tec" onclick="navegarInstructor('tecnica')">
                <svg class="nav-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="23 7 16 12 23 17 23 7"></polygon>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                </svg>
                <span class="nav-label">Registrar Técnica</span>
            </button>
            <button class="nav-item" id="nav-btn-gest-prof" onclick="navegarInstructor('profesores')">
                <svg class="nav-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <span class="nav-label">Gestionar Profesores</span>
            </button>
            <button class="nav-item" id="nav-btn-gest-fuent" onclick="navegarInstructor('fuentes')">
                <svg class="nav-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                </svg>
                <span class="nav-label">Gestionar Fuentes</span>
            </button>
        `;
        nav.style.display = 'flex';
    } else {
        nav.style.display = 'none';
    }
}

function seleccionarRol(rol) {
    localStorage.setItem('user_role', rol);

    const pantallaRol = document.getElementById('pantalla-rol');
    const vistaInstructor = document.getElementById('vista-instructor');
    const vistaAlumno = document.getElementById('vista-alumno');
    const btnCambiarRol = document.getElementById('btn-cambiar-rol');

    if (pantallaRol) pantallaRol.style.display = 'none';
    if (btnCambiarRol) btnCambiarRol.style.display = 'block';

    renderizarNavegacion(rol);

    if (rol === 'instructor') {
        if (vistaInstructor) vistaInstructor.style.display = 'block';
        if (vistaAlumno) vistaAlumno.style.display = 'none';
        navegarInstructor('tecnica');
        cargarInstructores();
    } else {
        if (vistaInstructor) vistaInstructor.style.display = 'none';
        if (vistaAlumno) vistaAlumno.style.display = 'block';
        navegarAlumno('evaluar');
        cargarInstructores();
    }
}

function cambiarRol() {
    localStorage.removeItem('user_role');

    const pantallaRol = document.getElementById('pantalla-rol');
    const vistaInstructor = document.getElementById('vista-instructor');
    const vistaAlumno = document.getElementById('vista-alumno');
    const btnCambiarRol = document.getElementById('btn-cambiar-rol');
    const nav = document.getElementById('nav-pwa-bottom');

    if (vistaInstructor) vistaInstructor.style.display = 'none';
    if (vistaAlumno) vistaAlumno.style.display = 'none';
    if (btnCambiarRol) btnCambiarRol.style.display = 'none';
    if (nav) nav.style.display = 'none';
    if (pantallaRol) pantallaRol.style.display = 'block';
}

function navegarAlumno(seccion) {
    const pantallaSeleccion = document.getElementById('pantalla-seleccion');
    const pantallaUpload = document.getElementById('pantalla-upload');
    const pantallaResultado = document.getElementById('pantalla-resultado');
    const pantallaProgreso = document.getElementById('pantalla-progreso');
    const pantallaRecursos = document.getElementById('pantalla-recursos');

    const btnEvaluar = document.getElementById('nav-btn-evaluar');
    const btnProgreso = document.getElementById('nav-btn-progreso');
    const btnRecursos = document.getElementById('nav-btn-recursos');

    if (btnEvaluar) btnEvaluar.className = `nav-item ${seccion === 'evaluar' ? 'nav-item-activo' : ''}`;
    if (btnProgreso) btnProgreso.className = `nav-item ${seccion === 'progreso' ? 'nav-item-activo' : ''}`;
    if (btnRecursos) btnRecursos.className = `nav-item ${seccion === 'recursos' ? 'nav-item-activo' : ''}`;

    if (seccion === 'evaluar') {
        if (pantallaSeleccion) pantallaSeleccion.style.display = 'block';
        if (pantallaUpload) pantallaUpload.style.display = 'none';
        if (pantallaResultado) pantallaResultado.style.display = 'none';
        if (pantallaProgreso) pantallaProgreso.style.display = 'none';
        if (pantallaRecursos) pantallaRecursos.style.display = 'none';
    } else if (seccion === 'progreso') {
        if (pantallaSeleccion) pantallaSeleccion.style.display = 'none';
        if (pantallaUpload) pantallaUpload.style.display = 'none';
        if (pantallaResultado) pantallaResultado.style.display = 'none';
        if (pantallaProgreso) pantallaProgreso.style.display = 'block';
        if (pantallaRecursos) pantallaRecursos.style.display = 'none';
        cargarProgresoAlumno();
    } else if (seccion === 'recursos') {
        if (pantallaSeleccion) pantallaSeleccion.style.display = 'none';
        if (pantallaUpload) pantallaUpload.style.display = 'none';
        if (pantallaResultado) pantallaResultado.style.display = 'none';
        if (pantallaProgreso) pantallaProgreso.style.display = 'none';
        if (pantallaRecursos) pantallaRecursos.style.display = 'block';
        cargarRecursosAlumno();
    }
}

async function cargarProgresoAlumno() {
    const contenedor = document.getElementById('lista-progreso');
    if (!contenedor) return;
    contenedor.innerHTML = '<p>Consultando historial biomecánico...</p>';

    try {
        const res = await fetch('/api/v1/alumno/progreso');
        if (!res.ok) throw new Error('Error al cargar progreso.');
        const data = await res.json();
        const historial = data.historial || [];

        if (historial.length === 0) {
            contenedor.innerHTML = '<p class="texto-vacio">Aún no tienes evaluaciones registradas. Realiza tu primera práctica en la pestaña "Evaluar".</p>';
            return;
        }

        contenedor.innerHTML = historial.map(item => `
            <div class="tarjeta-abm">
                <div class="tarjeta-header">
                    <h4>${item.id_tecnica || 'Evaluación'}</h4>
                    <span class="badge ${item.es_valido ? 'badge-valido' : 'badge-desvio'}">
                        ${item.es_valido ? 'Válido' : 'Requiere Ajuste'}
                    </span>
                </div>
                <p><strong>Desviaciones:</strong> ${item.total_desviaciones || 0}</p>
                <p class="nota-muted">${item.fecha_evaluacion || 'Reciente'}</p>
            </div>
        `).join('');
    } catch (err) {
        contenedor.innerHTML = `<p class="error-msg">Error al cargar progreso: ${err.message}</p>`;
    }
}

async function cargarRecursosAlumno() {
    const contenedor = document.getElementById('lista-recursos');
    if (!contenedor) return;
    contenedor.innerHTML = '<p>Cargando recursos didácticos...</p>';

    try {
        const res = await fetch('/api/v1/alumno/recursos');
        if (!res.ok) throw new Error('Error al consultar recursos.');
        const data = await res.json();
        const recursos = data.recursos || [];

        if (recursos.length === 0) {
            contenedor.innerHTML = '<p class="texto-vacio">No hay técnicas o recursos registrados actualmente.</p>';
            return;
        }

        contenedor.innerHTML = recursos.map(rec => `
            <div class="tarjeta-abm">
                <div class="tarjeta-header">
                    <h4>${rec.nombre}</h4>
                    <span class="badge">${rec.categoria || 'Técnica'}</span>
                </div>
                <p>${rec.descripcion || 'Sin descripción detallada.'}</p>
                <p><strong>Profesor:</strong> ${rec.profesor || 'Instructor Oficial'}</p>
                ${rec.video_stream_url ? `
                    <a href="${rec.video_stream_url}" target="_blank" class="btn-secundario-pequeno" style="display:inline-block; margin-top:8px; text-decoration:none;">
                        Ver Video de Referencia
                    </a>
                ` : ''}
            </div>
        `).join('');
    } catch (err) {
        contenedor.innerHTML = `<p class="error-msg">Error al cargar recursos: ${err.message}</p>`;
    }
}

function navegarInstructor(seccion) {
    const btnRegTec = document.getElementById('nav-btn-reg-tec');
    const btnGestProf = document.getElementById('nav-btn-gest-prof');
    const btnGestFuent = document.getElementById('nav-btn-gest-fuent');

    if (btnRegTec) btnRegTec.className = `nav-item ${seccion === 'tecnica' ? 'nav-item-activo' : ''}`;
    if (btnGestProf) btnGestProf.className = `nav-item ${seccion === 'profesores' ? 'nav-item-activo' : ''}`;
    if (btnGestFuent) btnGestFuent.className = `nav-item ${seccion === 'fuentes' ? 'nav-item-activo' : ''}`;

    if (seccion === 'tecnica') {
        mostrarTab('tab-registro');
    } else if (seccion === 'profesores') {
        mostrarTab('tab-crear-inst');
    } else if (seccion === 'fuentes') {
        mostrarTab('tab-manual');
    }
}

// --- 3. Pestañas de Vista de Instructor ---
function mostrarTab(tabId) {
    const tabs = ['tab-registro', 'tab-manual', 'tab-crear-inst'];
    tabs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = (id === tabId) ? 'block' : 'none';
    });

    const btnRegistro = document.getElementById('btn-tab-registro');
    const btnManual = document.getElementById('btn-tab-manual');
    const btnCrear = document.getElementById('btn-tab-crear-inst');

    if (btnRegistro) btnRegistro.className = `tab-btn ${tabId === 'tab-registro' ? 'tab-activa' : ''}`;
    if (btnManual) btnManual.className = `tab-btn ${tabId === 'tab-manual' ? 'tab-activa' : ''}`;
    if (btnCrear) btnCrear.className = `tab-btn ${tabId === 'tab-crear-inst' ? 'tab-activa' : ''}`;
}

// --- 4. Carga Dinámica de Instructores ---
async function cargarInstructores() {
    const selectManual = document.getElementById('manual-instructor');
    const selectAlumno = document.getElementById('alumno-instructor');

    try {
        const res = await fetch('/api/v1/instructores');
        if (!res.ok) throw new Error('Error al cargar instructores');
        const instructores = await res.json();

        if (selectManual) {
            selectManual.innerHTML = '<option value="">-- Seleccionar Instructor --</option>';
            instructores.forEach(i => {
                const opt = document.createElement('option');
                opt.value = i.id_instructor || i.id;
                opt.textContent = i.nombre_completo || i.nombre;
                selectManual.appendChild(opt);
            });
        }

        if (selectAlumno) {
            selectAlumno.innerHTML = '<option value="">-- Seleccionar --</option>';
            instructores.forEach(i => {
                const opt = document.createElement('option');
                opt.value = i.id_instructor || i.id;
                opt.textContent = i.nombre_completo || i.nombre;
                selectAlumno.appendChild(opt);
            });
        }
    } catch (err) {
        console.warn('Error cargando instructores:', err);
    }
}

// --- 5. Formularios de Instructor ---

// 5.1 Crear Instructor
async function guardarInstructor(event) {
    event.preventDefault();
    const instIdInput = document.getElementById('inst-id');
    const instNombreInput = document.getElementById('inst-nombre');
    const btnSubmit = document.getElementById('btn-crear-inst');
    const statusBox = document.getElementById('status-instructor');

    const idInstructor = instIdInput ? instIdInput.value.trim() : '';
    const nombreCompleto = instNombreInput ? instNombreInput.value.trim() : '';

    if (!idInstructor || !nombreCompleto) {
        mostrarToast('Por favor completa todos los campos del instructor.', 'error');
        return;
    }

    if (btnSubmit) btnSubmit.disabled = true;
    if (statusBox) {
        statusBox.className = 'status-box';
        statusBox.style.display = 'block';
        statusBox.textContent = 'Registrando instructor...';
    }

    const formData = new FormData();
    formData.append('id_instructor', idInstructor);
    formData.append('nombre_completo', nombreCompleto);

    try {
        const res = await fetch('/api/v1/instructores', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Fallo al guardar el instructor.');
        }

        if (statusBox) {
            statusBox.className = 'status-box success';
            statusBox.textContent = `Instructor ${nombreCompleto} registrado exitosamente.`;
        }
        mostrarToast('Instructor registrado con éxito.', 'success');

        if (instIdInput) instIdInput.value = '';
        if (instNombreInput) instNombreInput.value = '';

        await cargarInstructores();
    } catch (err) {
        if (statusBox) {
            statusBox.className = 'status-box error';
            statusBox.textContent = `Error: ${err.message}`;
        }
        mostrarToast(err.message, 'error');
    } finally {
        if (btnSubmit) btnSubmit.disabled = false;
    }
}

// 5.2 Registrar Técnica Patrón
async function guardarTecnica(event) {
    event.preventDefault();
    const nombreInput = document.getElementById('tec-nombre');
    const videoInput = document.getElementById('tec-video');
    const btnSubmit = document.getElementById('btn-guardar-tec');
    const statusBox = document.getElementById('status-tecnica');

    const nombre = nombreInput ? nombreInput.value.trim() : '';
    const file = videoInput && videoInput.files ? videoInput.files[0] : null;

    if (!nombre || !file) {
        mostrarToast('Completa el nombre y selecciona el video de referencia.', 'error');
        return;
    }

    if (btnSubmit) btnSubmit.disabled = true;
    if (statusBox) {
        statusBox.className = 'status-box';
        statusBox.style.display = 'block';
        statusBox.textContent = 'Guardando técnica de referencia del Maestro...';
    }

    const formData = new FormData();
    formData.append('nombre', nombre);
    formData.append('file', file);

    try {
        const res = await fetch('/api/v1/tecnicas/registrar', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Fallo al registrar la técnica.');
        }

        if (statusBox) {
            statusBox.className = 'status-box success';
            statusBox.textContent = 'Técnica guardada y video disponible para los alumnos.';
        }
        mostrarToast('Técnica guardada con éxito.', 'success');

        if (nombreInput) nombreInput.value = '';
        if (videoInput) videoInput.value = '';
    } catch (err) {
        if (statusBox) {
            statusBox.className = 'status-box error';
            statusBox.textContent = `Error: ${err.message}`;
        }
        mostrarToast(err.message, 'error');
    } finally {
        if (btnSubmit) btnSubmit.disabled = false;
    }
}

// 5.3 Subir Manual (RAG)
async function guardarManual(event) {
    event.preventDefault();
    const instSelect = document.getElementById('manual-instructor');
    const tituloInput = document.getElementById('manual-titulo');
    const archivoInput = document.getElementById('manual-archivo');
    const btnSubmit = document.getElementById('btn-guardar-manual');
    const statusBox = document.getElementById('status-manual');

    const idInstructor = instSelect ? instSelect.value : '';
    const titulo = tituloInput ? tituloInput.value.trim() : '';
    const archivo = archivoInput && archivoInput.files ? archivoInput.files[0] : null;

    if (!idInstructor || !titulo || !archivo) {
        mostrarToast('Selecciona el instructor, escribe el título y adjunta el PDF.', 'error');
        return;
    }

    if (btnSubmit) btnSubmit.disabled = true;
    if (statusBox) {
        statusBox.className = 'status-box';
        statusBox.style.display = 'block';
        statusBox.textContent = 'Extrayendo texto del manual e indexando vectores...';
    }

    const formData = new FormData();
    formData.append('id_instructor', idInstructor);
    formData.append('titulo', titulo);
    formData.append('archivo', archivo);

    try {
        const res = await fetch('/api/v1/fuentes', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Fallo al procesar el manual PDF.');
        }

        const data = await res.json();
        if (statusBox) {
            statusBox.className = 'status-box success';
            statusBox.textContent = `Manual procesado con éxito (${data.chunks_indexados} bloques indexados).`;
        }
        mostrarToast('Manual guardado e indexado para retroalimentación.', 'success');

        if (tituloInput) tituloInput.value = '';
        if (archivoInput) archivoInput.value = '';
    } catch (err) {
        if (statusBox) {
            statusBox.className = 'status-box error';
            statusBox.textContent = `Error: ${err.message}`;
        }
        mostrarToast(err.message, 'error');
    } finally {
        if (btnSubmit) btnSubmit.disabled = false;
    }
}

// --- 6. Flujo de Alumno (Práctica y Diagnóstico) ---

// 6.1 Cargar Técnicas al Seleccionar Instructor
async function cargarTecnicas() {
    const selectInstructor = document.getElementById('alumno-instructor');
    const selectTecnica = document.getElementById('alumno-tecnica');
    const btnComenzar = document.getElementById('btn-comenzar-practica');

    const idInstructor = selectInstructor ? selectInstructor.value : '';
    if (!idInstructor) {
        if (selectTecnica) {
            selectTecnica.innerHTML = '<option value="">-- Primero selecciona un instructor --</option>';
            selectTecnica.disabled = true;
        }
        if (btnComenzar) btnComenzar.disabled = true;
        return;
    }

    if (selectTecnica) {
        selectTecnica.innerHTML = '<option value="">Cargando técnicas...</option>';
        selectTecnica.disabled = true;
    }

    try {
        const res = await fetch(`/api/v1/instructores/${encodeURIComponent(idInstructor)}/tecnicas`);
        if (!res.ok) throw new Error('Error al consultar técnicas del instructor');
        const tecnicas = await res.json();

        if (selectTecnica) {
            selectTecnica.innerHTML = '<option value="">-- Seleccionar Técnica --</option>';
            tecnicas.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.id || t.id_tecnica;
                opt.textContent = t.nombre;
                if (t.video_url) {
                    opt.setAttribute('data-video', t.video_url);
                }
                selectTecnica.appendChild(opt);
            });
            selectTecnica.disabled = false;
        }
    } catch (err) {
        if (selectTecnica) {
            selectTecnica.innerHTML = '<option value="">Error al cargar técnicas</option>';
        }
        mostrarToast('No se pudieron cargar las técnicas del instructor.', 'error');
    }
}

// 6.2 Pasar a Pantalla de Grabación / Upload
function mostrarUpload() {
    const selectTecnica = document.getElementById('alumno-tecnica');
    const nombreTecnica = selectTecnica && selectTecnica.selectedIndex >= 0
        ? selectTecnica.options[selectTecnica.selectedIndex].text
        : 'Técnica';

    const tituloUpload = document.getElementById('titulo-upload-tecnica');
    if (tituloUpload) {
        tituloUpload.textContent = `Grabar tu ejecución: ${nombreTecnica}`;
    }

    const pantallaSeleccion = document.getElementById('pantalla-seleccion');
    const pantallaUpload = document.getElementById('pantalla-upload');
    const pantallaResultado = document.getElementById('pantalla-resultado');

    if (pantallaSeleccion) pantallaSeleccion.style.display = 'none';
    if (pantallaResultado) pantallaResultado.style.display = 'none';
    if (pantallaUpload) pantallaUpload.style.display = 'block';
}

function volverASeleccion() {
    const pantallaSeleccion = document.getElementById('pantalla-seleccion');
    const pantallaUpload = document.getElementById('pantalla-upload');
    const pantallaResultado = document.getElementById('pantalla-resultado');

    if (pantallaUpload) pantallaUpload.style.display = 'none';
    if (pantallaResultado) pantallaResultado.style.display = 'none';
    if (pantallaSeleccion) pantallaSeleccion.style.display = 'block';
}

// 6.3 Enviar Evaluación Biomecánica
async function enviarAnalisis() {
    const videoInput = document.getElementById('alumno-video');
    const selectInstructor = document.getElementById('alumno-instructor');
    const selectTecnica = document.getElementById('alumno-tecnica');
    const btnAnalizar = document.getElementById('btn-enviar-analisis');
    const statusBox = document.getElementById('status-analisis');

    const video = videoInput && videoInput.files ? videoInput.files[0] : null;
    const idInstructor = selectInstructor ? selectInstructor.value : '';
    const idTecnica = selectTecnica ? selectTecnica.value : '';

    if (!video) {
        mostrarToast('Por favor selecciona o graba un video de tu movimiento.', 'error');
        return;
    }

    if (!idTecnica) {
        mostrarToast('Selecciona primero la técnica a practicar.', 'error');
        return;
    }

    if (btnAnalizar) btnAnalizar.disabled = true;
    if (statusBox) {
        statusBox.style.display = 'block';
        statusBox.textContent = 'Analizando tu movimiento frente al modelo del profesor...';
    }

    const formData = new FormData();
    formData.append('file', video);
    formData.append('id_instructor', idInstructor);
    formData.append('id_tecnica', idTecnica);

    try {
        const res = await fetch('/api/v1/evaluaciones/evaluar', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Fallo en la evaluación.');
        }

        const data = await res.json();

        // Renderizar resultado con fotograma real
        renderResultadoReal(data);

        // Cambiar a pantalla de resultado
        const pantallaUpload = document.getElementById('pantalla-upload');
        const pantallaResultado = document.getElementById('pantalla-resultado');
        if (pantallaUpload) pantallaUpload.style.display = 'none';
        if (pantallaResultado) pantallaResultado.style.display = 'block';

        mostrarToast('Análisis biomecánico completado.', 'success');

    } catch (err) {
        mostrarToast(`Error: ${err.message}`, 'error');
    } finally {
        if (btnAnalizar) btnAnalizar.disabled = false;
        if (statusBox) statusBox.style.display = 'none';
    }
}

// 6.3.1 Renderizar Fotograma Real y Datos de Evaluación
function renderResultadoReal(data) {
    const imgFrame = document.getElementById('frame-alumno');
    const videoPatron = document.getElementById('video-patron');
    const placeholder = document.getElementById('canvas-placeholder');

    const imageUrl = data.frame_alumno || data.frame_alumno_base64 || data.frame_url;

    // Renderizar fotograma real si existe
    if (imgFrame && imageUrl && imageUrl.length > 50) {
        imgFrame.src = imageUrl;
        imgFrame.style.display = 'block';
        if (placeholder) placeholder.style.display = 'none';

        imgFrame.onload = function() {
            const w = imgFrame.naturalWidth || imgFrame.width || 640;
            const h = imgFrame.naturalHeight || imgFrame.height || 480;
            dibujarPuntosError(data.desviaciones || [], w, h);
        };
    } else {
        console.warn("No se recibió fotograma real de Colab o backend.");
    }

    // Cargar video patrón
    if (videoPatron) {
        videoPatron.src = data.video_patron_url || '/static/videos_patron/armbar_guardia.mp4';
        videoPatron.load();
    }

    // Mostrar consejo pedagógico
    const textoConsejo = document.getElementById('texto-consejo');
    if (textoConsejo) {
        textoConsejo.textContent = data.consejo || data.consejo_pedagogico || 'Ajusta tu postura para mantener mayor firmeza articular.';
    }
}

// 6.4 Dibujar Puntos Rojos de Error sobre el Fotograma Real
function dibujarPuntosError(desviaciones, imgWidth, imgHeight) {
    const canvas = document.getElementById('canvas-puntos');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    canvas.width = imgWidth;
    canvas.height = imgHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!Array.isArray(desviaciones)) return;

    desviaciones.forEach(dev => {
        const magnitud = Number(dev.desviacion || dev.desviacion_grados || 0);
        if (magnitud > 5.0 || desviaciones.length === 1) {
            const x = typeof dev.x === 'number' ? dev.x : canvas.width * 0.5;
            const y = typeof dev.y === 'number' ? dev.y : canvas.height * 0.5;

            // Círculo rojo
            ctx.beginPath();
            ctx.arc(x, y, 14, 0, 2 * Math.PI);
            ctx.fillStyle = 'red';
            ctx.fill();
            ctx.lineWidth = 3;
            ctx.strokeStyle = 'white';
            ctx.stroke();

            // Halo visual
            ctx.beginPath();
            ctx.arc(x, y, 22, 0, 2 * Math.PI);
            ctx.strokeStyle = 'rgba(255, 0, 0, 0.4)';
            ctx.lineWidth = 2;
            ctx.stroke();
        }
    });
}

// 6.5 Reiniciar Práctica
function reiniciar() {
    const videoInput = document.getElementById('alumno-video');
    if (videoInput) videoInput.value = '';

    const canvas = document.getElementById('canvas-puntos');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    const videoPatron = document.getElementById('video-patron');
    if (videoPatron) {
        videoPatron.pause();
        videoPatron.removeAttribute('src');
    }

    const imgFrame = document.getElementById('frame-alumno');
    if (imgFrame) imgFrame.removeAttribute('src');

    const pantallaResultado = document.getElementById('pantalla-resultado');
    const pantallaUpload = document.getElementById('pantalla-upload');
    const pantallaSeleccion = document.getElementById('pantalla-seleccion');

    if (pantallaResultado) pantallaResultado.style.display = 'none';
    if (pantallaUpload) pantallaUpload.style.display = 'none';
    if (pantallaSeleccion) pantallaSeleccion.style.display = 'block';
}

// --- 7. Carga Diferida (Lazy Loading) de Módulos ABM (RP-02 / Larman UP) ---
let abmModulePromise = null;

function cargarModuloABM() {
    if (!abmModulePromise) {
        abmModulePromise = import('/static/js/components/abm_forms.js')
            .catch(err => {
                console.warn('Error al cargar módulo ABM diferido:', err);
                return null;
            });
    }
    return abmModulePromise;
}

function navegarASeccion(seccion) {
    if (seccion === 'evaluar') {
        window.location.href = '/';
    } else if (seccion === 'tecnicas' || seccion === 'profesores') {
        cargarModuloABM().then(() => {
            window.location.href = `/abm#${seccion}`;
        });
    }
}
