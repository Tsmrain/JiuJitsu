// frontend/app.js - Logica Cliente BJJ Biomechanics

// ---------------------------------------------------------------------------
// 1. Sistema de Credenciales y Sesión (API Rest)
// ---------------------------------------------------------------------------
function cambiarTabAuth(tab) {
    const tabLogin = document.getElementById('btn-tab-login');
    const tabRegistro = document.getElementById('btn-tab-registro');
    const formLogin = document.getElementById('form-login');
    const formRegistro = document.getElementById('form-registro');
    const errorLogin = document.getElementById('login-error');
    const errorRegistro = document.getElementById('registro-error');

    if (errorLogin) errorLogin.style.display = 'none';
    if (errorRegistro) errorRegistro.style.display = 'none';

    if (tab === 'login') {
        tabLogin.classList.add('active');
        tabRegistro.classList.remove('active');
        formLogin.style.display = 'block';
        formRegistro.style.display = 'none';
    } else {
        tabRegistro.classList.add('active');
        tabLogin.classList.remove('active');
        formRegistro.style.display = 'block';
        formLogin.style.display = 'none';
    }
}

function selectRole(role) {
    return seleccionarRol(role);
}

function getHeaders(isFormData = false) {
    const token = localStorage.getItem('token_bjj');
    const headers = {};
    if (token) {
        headers['Authorization'] = 'Bearer ' + token;
    }
    if (!isFormData) {
        headers['Content-Type'] = 'application/json';
    }
    return headers;
}

function seleccionarRol(rol) {
    localStorage.setItem('rol_usuario', rol);
    const pantallaLogin = document.getElementById('pantalla-login');
    if (pantallaLogin) pantallaLogin.style.display = 'none';
    const pantallaRol = document.getElementById('pantalla-rol');
    if (pantallaRol) pantallaRol.style.display = 'none';
    const btnCerrar = document.getElementById('btn-cerrar-sesion');
    if (btnCerrar) btnCerrar.style.display = 'inline-block';

    if (rol === 'alumno') {
        const vistaAlumno = document.getElementById('vista-alumno');
        if (vistaAlumno) vistaAlumno.style.display = 'block';
        const vistaProfesor = document.getElementById('vista-instructor');
        if (vistaProfesor) vistaProfesor.style.display = 'none';
        mostrarSeccionAlumno('evaluar');
        cargarTecnicas();
    } else {
        const vistaAlumno = document.getElementById('vista-alumno');
        if (vistaAlumno) vistaAlumno.style.display = 'none';
        const vistaProfesor = document.getElementById('vista-instructor');
        if (vistaProfesor) vistaProfesor.style.display = 'block';
        mostrarSeccionProfesor('tecnicas');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Registrar Service Worker para PWA móvil
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/service-worker.js')
            .catch(() => {});
    }

    const alumnoVideo = document.getElementById('alumno-video');
    const previewAlumno = document.getElementById('preview-video-alumno');
    if (alumnoVideo && previewAlumno) {
        alumnoVideo.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                previewAlumno.src = URL.createObjectURL(file);
                previewAlumno.style.display = 'block';
            }
        });
    }

    const tecVideo = document.getElementById('tec-video');
    const previewTec = document.getElementById('preview-video-profesor');
    if (tecVideo && previewTec) {
        tecVideo.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                previewTec.src = URL.createObjectURL(file);
                previewTec.style.display = 'block';
            }
        });
    }

    const formLogin = document.getElementById('form-login');
    const pantallaLogin = document.getElementById('pantalla-login');
    const btnCerrarSesion = document.getElementById('btn-cerrar-sesion');

    // Verificar si ya hay sesión activa en localStorage
    const sesionActiva = localStorage.getItem('rol_usuario');
    if (sesionActiva) {
        if (pantallaLogin) pantallaLogin.style.display = 'none';
        if (btnCerrarSesion) btnCerrarSesion.style.display = 'inline-block';

        if (sesionActiva === 'alumno') {
            const vistaAlumno = document.getElementById('vista-alumno');
            if (vistaAlumno) vistaAlumno.style.display = 'block';
            mostrarSeccionAlumno('evaluar');
            cargarTecnicas();
        } else {
            const vistaInstructor = document.getElementById('vista-instructor');
            if (vistaInstructor) vistaInstructor.style.display = 'block';
            mostrarSeccionProfesor('tecnicas');
        }
    } else {
        if (pantallaLogin) pantallaLogin.style.display = 'flex';
        if (btnCerrarSesion) btnCerrarSesion.style.display = 'none';
    }

    // Manejador del Formulario de Login
    if (formLogin) {
        formLogin.addEventListener('submit', async (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('login-email');
            const passwordInput = document.getElementById('login-password');
            const email = emailInput ? emailInput.value.trim() : '';
            const password = passwordInput ? passwordInput.value : '';
            const errorLogin = document.getElementById('login-error');
            const btnSubmit = formLogin.querySelector('button[type="submit"]');

            if (btnSubmit) btnSubmit.disabled = true;

            try {
                const resp = await fetch('/api/v1/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (resp.ok) {
                    const data = await resp.json();
                    const rol = data.rol;
                    localStorage.setItem('rol_usuario', rol);
                    localStorage.setItem('usuario_actual', data.id_usuario);
                    localStorage.setItem('user_role', rol); // compatibilidad
                    if (data.access_token) {
                        localStorage.setItem('token_bjj', data.access_token);
                    }

                    if (pantallaLogin) pantallaLogin.style.display = 'none';
                    if (errorLogin) errorLogin.style.display = 'none';
                    if (btnCerrarSesion) btnCerrarSesion.style.display = 'inline-block';

                    if (rol === 'alumno') {
                        const vistaAlumno = document.getElementById('vista-alumno');
                        if (vistaAlumno) vistaAlumno.style.display = 'block';
                        mostrarSeccionAlumno('evaluar');
                        cargarTecnicas();
                    } else {
                        const vistaInstructor = document.getElementById('vista-instructor');
                        if (vistaInstructor) vistaInstructor.style.display = 'block';
                        mostrarSeccionProfesor('tecnicas');
                    }
                } else {
                    const errorData = await resp.json().catch(() => ({}));
                    if (errorLogin) {
                        errorLogin.textContent = errorData.detail || 'Credenciales incorrectas';
                        errorLogin.style.display = 'block';
                    }
                }
            } catch (err) {
                console.error(err);
                if (errorLogin) {
                    errorLogin.textContent = 'Error de conexión con el servidor.';
                    errorLogin.style.display = 'block';
                }
            } finally {
                if (btnSubmit) btnSubmit.disabled = false;
            }
        });
    }

    // Manejador del Formulario de Registro
    const formRegistro = document.getElementById('form-registro');
    if (formRegistro) {
        formRegistro.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nombre = document.getElementById('registro-nombre').value.trim();
            const email = document.getElementById('registro-email').value.trim();
            const password = document.getElementById('registro-password').value;
            const rol = document.getElementById('registro-rol').value;
            const errorRegistro = document.getElementById('registro-error');
            const btnSubmit = formRegistro.querySelector('button[type="submit"]');

            if (btnSubmit) btnSubmit.disabled = true;

            try {
                const resp = await fetch('/api/v1/auth/registro', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nombre_completo: nombre, email, password, rol })
                });

                if (resp.ok) {
                    mostrarToast('Cuenta creada exitosamente. Por favor, inicia sesión.', 'success');
                    formRegistro.reset();
                    cambiarTabAuth('login');
                } else {
                    const errorData = await resp.json().catch(() => ({}));
                    if (errorRegistro) {
                        errorRegistro.textContent = errorData.detail || 'Error al registrar la cuenta';
                        errorRegistro.style.display = 'block';
                    }
                }
            } catch (err) {
                console.error(err);
                if (errorRegistro) {
                    errorRegistro.textContent = 'Error de conexión con el servidor.';
                    errorRegistro.style.display = 'block';
                }
            } finally {
                if (btnSubmit) btnSubmit.disabled = false;
            }
        });
    }

    // Listener para habilitar boton comenzar practica al elegir tecnica
    const selectTecnica = document.getElementById('alumno-tecnica');
    const btnComenzar = document.getElementById('btn-comenzar-practica');
    if (selectTecnica && btnComenzar) {
        selectTecnica.addEventListener('change', () => {
            btnComenzar.disabled = !selectTecnica.value;
        });
    }

    // Inicializar listeners para formularios CRUD del profesor
    inicializarFormulariosProfesor();
});

// Función para cerrar sesión
function cerrarSesion() {
    localStorage.removeItem('rol_usuario');
    localStorage.removeItem('usuario_actual');
    localStorage.removeItem('user_role');
    location.reload();
}

// ---------------------------------------------------------------------------
// 2. Notificaciones Toast
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// 3. Navegación y Funcionalidades del Rol Alumno
// ---------------------------------------------------------------------------
function mostrarSeccionAlumno(seccion) {
    const secEval = document.getElementById('seccion-evaluar');
    const secProg = document.getElementById('seccion-progreso');
    const secHist = document.getElementById('seccion-historial');

    if (secEval) secEval.style.display = 'none';
    if (secProg) secProg.style.display = 'none';
    if (secHist) secHist.style.display = 'none';

    const target = document.getElementById(`seccion-${seccion}`);
    if (target) target.style.display = 'block';

    if (seccion === 'evaluar') {
        reiniciar();
    } else if (seccion === 'progreso') {
        cargarProgresoAlumno();
    } else if (seccion === 'historial') {
        cargarHistorialAlumno();
    }
}

async function cargarProgresoAlumno() {
    const alumnoId = localStorage.getItem('usuario_actual') || 'alumno_demo';
    const contenedor = document.getElementById('contenedor-progreso');
    if (contenedor) {
        contenedor.innerHTML = '<p style="text-align:center; color:#6c757d;">Cargando progreso biomecánico...</p>';
    }

    try {
        const resp = await fetch(`/api/v1/alumno/${alumnoId}/progreso`);
        const data = await resp.json();
        const evals = data.evaluaciones || data.historial || [];

        if (evals && evals.length > 0) {
            const totalEvals = evals.length;
            const aprobadas = evals.filter(e => e.es_valido).length;
            const tasaAprobacion = ((aprobadas / totalEvals) * 100).toFixed(1);

            if (contenedor) {
                contenedor.innerHTML = `
                    <div style="text-align:center; padding:24px; background:#f8f9fa; border-radius:8px; border:1px solid #e9ecef;">
                        <h4 style="margin-bottom:8px;">Total de Evaluaciones: ${totalEvals}</h4>
                        <h4 style="color:#28a745;">Tasa de Aprobación: ${tasaAprobacion}%</h4>
                        <p style="color:#6c757d; margin-top:8px;">${aprobadas} aprobadas de ${totalEvals} ejecuciones evaluadas.</p>
                    </div>
                `;
            }
        } else {
            if (contenedor) {
                contenedor.innerHTML = '<p style="text-align:center; color:#6c757d; padding:20px;">Aún no tienes evaluaciones registradas.</p>';
            }
        }
    } catch (err) {
        console.error('Error cargando progreso:', err);
        if (contenedor) {
            contenedor.innerHTML = '<p style="text-align:center; color:#dc3545;">Error al cargar datos de progreso.</p>';
        }
    }
}

async function cargarHistorialAlumno() {
    const alumnoId = localStorage.getItem('usuario_actual') || 'alumno_demo';
    const contenedor = document.getElementById('contenedor-historial');
    if (contenedor) {
        contenedor.innerHTML = '<p style="text-align:center; color:#6c757d;">Cargando historial de evaluaciones...</p>';
    }

    try {
        const resp = await fetch(`/api/v1/alumno/${alumnoId}/progreso`);
        const data = await resp.json();
        const evals = data.evaluaciones || data.historial || [];

        if (evals && evals.length > 0) {
            if (contenedor) {
                contenedor.innerHTML = evals.map(eval_ => `
                    <div style="border:1px solid #ced4da; padding:14px; margin:10px 0; border-radius:8px; background:#ffffff; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <strong>${eval_.id_tecnica || 'Técnica'}</strong>
                            <span style="font-weight:600; color:${eval_.es_valido ? '#28a745' : '#dc3545'};">
                                ${eval_.es_valido ? '✅ Aprobado' : '❌ Reprobado'}
                            </span>
                        </div>
                        <small style="color:#6c757d;">${eval_.fecha ? new Date(eval_.fecha).toLocaleDateString() : 'Reciente'}</small><br>
                        <div style="margin-top:8px; font-size:0.9rem;">
                            <strong>Consejo:</strong> ${eval_.consejo_pedagogico || 'Sin consejo'}
                        </div>
                    </div>
                `).join('');
            }
        } else {
            if (contenedor) {
                contenedor.innerHTML = '<p style="text-align:center; color:#6c757d; padding:20px;">No hay evaluaciones en el historial.</p>';
            }
        }
    } catch (err) {
        console.error('Error cargando historial:', err);
        if (contenedor) {
            contenedor.innerHTML = '<p style="text-align:center; color:#dc3545;">Error al cargar historial.</p>';
        }
    }
}

// ---------------------------------------------------------------------------
// 4. Flujo de Evaluación y Práctica del Alumno
// ---------------------------------------------------------------------------
async function cargarTecnicas() {
    const selectTecnica = document.getElementById('alumno-tecnica');
    const btnComenzar = document.getElementById('btn-comenzar-practica');

    if (selectTecnica) {
        selectTecnica.innerHTML = '<option value="">Cargando técnicas disponibles...</option>';
        selectTecnica.disabled = true;
    }
    if (btnComenzar) btnComenzar.disabled = true;

    try {
        const res = await fetch('/api/v1/tecnicas');
        if (!res.ok) throw new Error('Error al consultar técnicas disponibles');
        const tecnicas = await res.json();

        if (selectTecnica) {
            selectTecnica.innerHTML = '<option value="">-- Seleccionar Técnica --</option>';
            tecnicas.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.id_tecnica || t.id;
                opt.textContent = t.nombre;
                if (t.video_url) {
                    opt.setAttribute('data-video', t.video_url);
                }
                selectTecnica.appendChild(opt);
            });
            selectTecnica.disabled = false;
        }
    } catch (err) {
        console.warn('Error cargando técnicas:', err);
        if (selectTecnica) {
            selectTecnica.innerHTML = '<option value="">Error al cargar técnicas</option>';
        }
        mostrarToast('No se pudieron cargar las técnicas disponibles.', 'error');
    }
}

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

async function enviarAnalisis() {
    const videoInput = document.getElementById('alumno-video');
    const selectTecnica = document.getElementById('alumno-tecnica');
    const btnAnalizar = document.getElementById('btn-enviar-analisis');
    const statusBox = document.getElementById('status-analisis');

    const video = videoInput && videoInput.files ? videoInput.files[0] : null;
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
    const idAlumno = localStorage.getItem('usuario_actual') || 'alumno_demo';
    formData.append('file', video);
    formData.append('id_tecnica', idTecnica);
    formData.append('id_alumno', idAlumno);

    try {
        const res = await fetch('/api/v1/evaluaciones/evaluar', {
            method: 'POST',
            headers: getHeaders(true),
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Fallo en la evaluación.');
        }

        const data = await res.json();
        renderResultadoReal(data);

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

function renderResultadoReal(data) {
    const imgFrame = document.getElementById('frame-alumno');
    const videoPatron = document.getElementById('video-patron');
    const imageUrl = data.frame_alumno || data.frame_alumno_base64 || data.frame_url;

    if (imgFrame && imageUrl && imageUrl.length > 50) {
        imgFrame.src = imageUrl;
        imgFrame.style.display = 'block';
        imgFrame.onload = function() {
            const w = imgFrame.naturalWidth || imgFrame.width || 640;
            const h = imgFrame.naturalHeight || imgFrame.height || 480;
            dibujarPuntosError(data.desviaciones, w, h);
        };
    }

    if (videoPatron) {
        const url = data.video_patron_url || '/static/videos_patron/armbar_guardia.mp4';
        videoPatron.src = url;
        videoPatron.load();
        videoPatron.onerror = () => {
            const placeholder = document.createElement('div');
            placeholder.style.cssText = 'padding:40px;background:#111;color:#aaa;text-align:center;border-radius:6px;';
            placeholder.textContent = 'Video patrón no disponible';
            if (videoPatron.parentNode) {
                videoPatron.parentNode.replaceChild(placeholder, videoPatron);
            }
        };
    }

    const textoConsejo = document.getElementById('texto-consejo');
    if (textoConsejo) {
        textoConsejo.textContent = data.consejo || data.consejo_pedagogico || 'Ajusta tu postura para mantener mayor firmeza articular.';
    }
}

function dibujarPuntosError(desviaciones, imgWidth, imgHeight) {
    const canvas = document.getElementById('canvas-puntos');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = imgWidth;
    canvas.height = imgHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!Array.isArray(desviaciones) || desviaciones.length === 0) return;

    const fallaCritica = desviaciones.reduce(
        (max, d) => (d.desviacion || d.desviacion_grados || 0) > (max.desviacion || max.desviacion_grados || 0) ? d : max,
        desviaciones[0]
    );

    desviaciones.forEach(dev => {
        const x = typeof dev.x === 'number' ? dev.x : canvas.width * 0.5;
        const y = typeof dev.y === 'number' ? dev.y : canvas.height * 0.5;
        const esCritica = dev === fallaCritica;

        ctx.beginPath();
        ctx.arc(x, y, esCritica ? 14 : 10, 0, 2 * Math.PI);
        ctx.fillStyle = esCritica ? 'rgba(255, 0, 0, 0.85)' : 'rgba(255, 40, 40, 0.75)';
        ctx.fill();
        ctx.lineWidth = esCritica ? 3 : 2;
        ctx.strokeStyle = 'white';
        ctx.stroke();

        const grados = Number(dev.desviacion || dev.desviacion_grados || 0).toFixed(1);
        ctx.fillStyle = 'white';
        ctx.font = `bold ${esCritica ? 16 : 13}px Arial`;
        ctx.fillText(`-${grados}°`, x + (esCritica ? 20 : 16), y + 4);
    });
}

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

// ---------------------------------------------------------------------------
// 5. Navegación y CRUD Completo del Rol Profesor
// ---------------------------------------------------------------------------
function mostrarSeccionProfesor(seccion) {
    const secTec = document.getElementById('seccion-tecnicas');
    const secFue = document.getElementById('seccion-fuentes');
    const secAna = document.getElementById('seccion-analitica');

    if (secTec) secTec.style.display = 'none';
    if (secFue) secFue.style.display = 'none';
    if (secAna) secAna.style.display = 'none';

    const target = document.getElementById(`seccion-${seccion}`);
    if (target) target.style.display = 'block';

    if (seccion === 'tecnicas') {
        cargarTecnicasProfesor();
    } else if (seccion === 'fuentes') {
        cargarFuentesProfesor();
    } else if (seccion === 'analitica') {
        cargarSelectAnalitica();
    }
}

// 5.1 CRUD Técnicas
async function cargarTecnicasProfesor() {
    try {
        const resp = await fetch('/api/v1/instructor/tecnicas');
        const tecnicas = await resp.json();
        const contenedor = document.getElementById('lista-tecnicas-profesor');
        if (!contenedor) return;

        if (tecnicas && tecnicas.length > 0) {
            contenedor.innerHTML = tecnicas.map(t => `
                <div style="border:1px solid #ced4da; padding:14px; margin:10px 0; border-radius:8px; display:flex; justify-content:space-between; align-items:center; background:#ffffff;">
                    <div>
                        <strong>${t.nombre}</strong><br>
                        <small style="color:#6c757d;">${t.descripcion || 'Sin descripción'}</small>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button onclick="editarTecnica('${t.id_tecnica}')" class="btn-secundario-pequeno">Editar</button>
                        <button onclick="eliminarTecnica('${t.id_tecnica}')" class="btn-peligro-pequeno">Eliminar</button>
                    </div>
                </div>
            `).join('');
        } else {
            contenedor.innerHTML = '<p style="color:#6c757d;">No hay técnicas registradas.</p>';
        }
    } catch (err) {
        console.error('Error cargando técnicas:', err);
    }
}

async function editarTecnica(id) {
    try {
        const resp = await fetch('/api/v1/instructor/tecnicas');
        const tecnicas = await resp.json();
        const tecnica = tecnicas.find(t => t.id_tecnica === id);

        if (tecnica) {
            document.getElementById('tecnica-id-editar').value = tecnica.id_tecnica;
            document.getElementById('tec-nombre').value = tecnica.nombre;
            document.getElementById('titulo-form-tecnica').textContent = 'Editar Técnica';
            document.getElementById('btn-cancelar-tecnica').style.display = 'inline-block';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    } catch (err) {
        console.error('Error al editar técnica:', err);
        mostrarToast('No se pudo cargar la técnica para editar.', 'error');
    }
}

async function eliminarTecnica(id) {
    if (confirm('¿Estás seguro de eliminar esta técnica?')) {
        try {
            const resp = await fetch(`/api/v1/instructor/tecnicas/${id}`, { method: 'DELETE', headers: getHeaders() });
            if (resp.ok) {
                alert('Técnica eliminada');
                cargarTecnicasProfesor();
            } else {
                alert('Error al eliminar la técnica');
            }
        } catch (err) {
            console.error('Error eliminando técnica:', err);
        }
    }
}

function cancelarEdicionTecnica() {
    const form = document.getElementById('form-tecnica') || document.getElementById('form-tecnica-crud');
    if (form) form.reset();
    const idInput = document.getElementById('tecnica-id-editar');
    if (idInput) idInput.value = '';
    const titulo = document.getElementById('titulo-form-tecnica');
    if (titulo) titulo.textContent = 'Registrar Nueva Técnica';
    const btnCancel = document.getElementById('btn-cancelar-tecnica');
    if (btnCancel) btnCancel.style.display = 'none';
}

// 5.2 CRUD Fuentes de Información
async function cargarFuentesProfesor() {
    try {
        const resp = await fetch('/api/v1/instructor/fuentes');
        const fuentes = await resp.json();
        const contenedor = document.getElementById('lista-fuentes-profesor');
        if (!contenedor) return;

        if (fuentes.length === 0) {
            contenedor.innerHTML = '<p class="texto-vacio" style="color:#6c757d; font-style:italic;">No hay fuentes didácticas registradas.</p>';
            return;
        }

        let html = '<ul style="list-style:none; padding:0;">';
        fuentes.forEach(f => {
            const idDoc = f.id_documento || f.id_fuente;
            const chunksBadge = f.total_chunks ? `<span style="display:inline-block; font-size:0.75rem; background:#e0e7ff; color:#3730a3; padding:2px 8px; border-radius:12px; margin-left:6px; font-weight:600;">${f.total_chunks} fragmento${f.total_chunks > 1 ? 's' : ''}</span>` : '';
            const tituloEscapado = (f.titulo || '').replace(/'/g, "\\'");
            html += `
                <li style="border:1px solid #dee2e6; border-radius:8px; padding:14px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; background:#fff; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    <div>
                        <strong style="font-size:1.05rem; color:#212529;">${f.titulo}</strong>
                        <span style="display:inline-block; font-size:0.8rem; background:#e9ecef; color:#495057; padding:2px 6px; border-radius:4px; margin-left:8px;">${f.tipo_recurso}</span>
                        ${chunksBadge}
                        ${f.id_tecnica ? `<br><small style="color:#6c757d;">Técnica: ${f.id_tecnica}</small>` : ''}
                    </div>
                    <div style="display:flex; gap:6px;">
                        <button onclick="editarFuente('${idDoc}', '${tituloEscapado}')" class="btn-secundario-pequeno">Editar</button>
                        <button onclick="eliminarFuente('${idDoc}')" class="btn-peligro-pequeno">Eliminar</button>
                    </div>
                </li>
            `;
        });
        html += '</ul>';
        contenedor.innerHTML = html;
    } catch (err) {
        console.error('Error cargando fuentes:', err);
    }
}

async function editarFuente(id, titulo) {
    const idInput = document.getElementById('fuente-id-editar');
    const tituloInput = document.getElementById('fuente-titulo');
    const tituloForm = document.getElementById('titulo-form-fuente');
    const btnCancel = document.getElementById('btn-cancelar-fuente');

    if (idInput && tituloInput) {
        idInput.value = id;
        tituloInput.value = titulo;
        if (tituloForm) tituloForm.textContent = 'Editar Fuente';
        if (btnCancel) btnCancel.style.display = 'inline-block';
        tituloInput.focus();
    }
}

async function eliminarFuente(id) {
    if (confirm('¿Estás seguro de eliminar esta fuente didáctica?')) {
        try {
            const resp = await fetch(`/api/v1/instructor/fuentes/${id}`, { method: 'DELETE', headers: getHeaders() });
            if (resp.ok) {
                cargarFuentesProfesor();
            } else {
                alert('Error al eliminar la fuente');
            }
        } catch (err) {
            console.error('Error eliminando fuente:', err);
        }
    }
}

function cancelarEdicionFuente() {
    const form = document.getElementById('form-fuente-crud');
    if (form) form.reset();
    const idInput = document.getElementById('fuente-id-editar');
    if (idInput) idInput.value = '';
    const titulo = document.getElementById('titulo-form-fuente');
    if (titulo) titulo.textContent = 'Registrar Nueva Fuente';
    const btnCancel = document.getElementById('btn-cancelar-fuente');
    if (btnCancel) btnCancel.style.display = 'none';
}

function inicializarFormulariosProfesor() {
    const formTec = document.getElementById('form-tecnica') || document.getElementById('form-tecnica-crud');
    if (formTec) {
        formTec.addEventListener('submit', async (e) => {
            e.preventDefault();

            const idEditar = (document.getElementById('tecnica-id-editar') || {}).value || '';
            const nombreElem = document.getElementById('tec-nombre') || document.getElementById('tecnica-nombre');
            const videoElem = document.getElementById('tec-video') || document.getElementById('tecnica-video');
            const nombre = nombreElem ? nombreElem.value : '';
            const videoFile = videoElem && videoElem.files ? videoElem.files[0] : null;

            const formData = new FormData();
            formData.append('nombre', nombre);
            formData.append('categoria', 'General');
            const id_profesor = localStorage.getItem('usuario_actual') || 'inst_santiago';
            formData.append('id_profesor', id_profesor);
            formData.append('descripcion', '');
            if (videoFile) formData.append('file', videoFile);

            try {
                let resp;
                if (idEditar) {
                    resp = await fetch(`/api/v1/instructor/tecnicas/${idEditar}`, {
                        method: 'PUT',
                        headers: getHeaders(),
                        body: formData
                    });
                } else {
                    resp = await fetch('/api/v1/instructor/tecnicas', {
                        method: 'POST',
                        headers: getHeaders(),
                        body: formData
                    });
                }

                if (resp.ok) {
                    alert(idEditar ? 'Técnica actualizada' : 'Técnica registrada');
                    cancelarEdicionTecnica();
                    cargarTecnicasProfesor();
                } else {
                    const errorData = await resp.json().catch(() => ({}));
                    alert('Error al guardar la técnica: ' + (errorData.detail || resp.statusText));
                }
            } catch (err) {
                console.error('Error guardando técnica:', err);
                alert('Error de conexión al guardar la técnica');
            }
        });
    }

    const formFue = document.getElementById('form-fuente-crud');
    if (formFue) {
        formFue.addEventListener('submit', async (e) => {
            e.preventDefault();

            const idEditar = document.getElementById('fuente-id-editar').value;
            const titulo = document.getElementById('fuente-titulo').value;
            const archivo = document.getElementById('fuente-archivo').files[0];

            const formData = new FormData();
            formData.append('titulo', titulo);
            // Semántica correcta: enviar un id_instructor real, no el id_usuario
            formData.append('id_instructor', 'inst_santiago');
            if (archivo) formData.append('archivo', archivo);

            try {
                let resp;
                if (idEditar) {
                    resp = await fetch(`/api/v1/instructor/fuentes/${idEditar}`, {
                        method: 'PUT',
                        headers: getHeaders(),
                        body: formData
                    });
                } else {
                    resp = await fetch('/api/v1/instructor/fuentes', {
                        method: 'POST',
                        headers: getHeaders(),
                        body: formData
                    });
                }

                if (resp.ok) {
                    alert(idEditar ? 'Fuente actualizada' : 'Fuente registrada');
                    cancelarEdicionFuente();
                    cargarFuentesProfesor();
                } else {
                    const errorData = await resp.json().catch(() => ({}));
                    alert('Error al guardar la fuente: ' + (errorData.detail || resp.statusText));
                }
            } catch (err) {
                console.error('Error guardando fuente:', err);
                alert('Error de conexión al guardar la fuente');
            }
        });
    }
}

// ---------------------------------------------------------------------------
// 6. Analítica de Tatami (CU-04)
// ---------------------------------------------------------------------------
async function cargarSelectAnalitica() {
    const select = document.getElementById('analitica-tecnica-select');
    if (!select) return;
    select.innerHTML = '<option value="">-- Cargando --</option>';

    try {
        const resp = await fetch('/api/v1/analitica/tecnicas/top?limite=100');
        const tecnicas = await resp.json();
        
        select.innerHTML = '<option value="">-- Seleccionar Técnica --</option>';
        tecnicas.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id_tecnica;
            opt.textContent = `${t.nombre || t.id_tecnica} (${t.total_evaluaciones} evals)`;
            select.appendChild(opt);
        });

        // Add event listener if not already attached
        if (!select.dataset.listenerAttached) {
            select.addEventListener('change', (e) => {
                if (e.target.value) {
                    cargarDashboardAnalitica(e.target.value);
                } else {
                    document.getElementById('analitica-contenido').style.display = 'none';
                    document.getElementById('analitica-vacio').style.display = 'none';
                }
            });
            select.dataset.listenerAttached = 'true';
        }
    } catch (err) {
        console.error('Error cargando top técnicas para analítica:', err);
        select.innerHTML = '<option value="">Error al cargar</option>';
    }
}

async function cargarDashboardAnalitica(id_tecnica) {
    const contenido = document.getElementById('analitica-contenido');
    const vacio = document.getElementById('analitica-vacio');
    
    contenido.style.display = 'none';
    vacio.style.display = 'none';
    
    try {
        const resp = await fetch(`/api/v1/analitica/tecnicas/${id_tecnica}`);
        if (!resp.ok) {
            vacio.style.display = 'block';
            return;
        }
        
        const data = await resp.json();
        
        if (data.total_evaluaciones === 0) {
            vacio.style.display = 'block';
            return;
        }
        
        document.getElementById('analitica-titulo').textContent = `Estadísticas: ${data.id_tecnica}`;
        document.getElementById('analitica-total').textContent = data.total_evaluaciones;
        document.getElementById('analitica-aprobadas').textContent = data.total_evaluaciones_aprobadas;
        document.getElementById('analitica-tasa').textContent = `${(data.tasa_aprobacion * 100).toFixed(1)}%`;
        
        renderizarGraficoAnalitica(data.articulaciones_criticas, data.total_evaluaciones);
        contenido.style.display = 'block';
    } catch (err) {
        console.error('Error cargando panel analítica:', err);
        vacio.textContent = 'Error al cargar los datos de analítica.';
        vacio.style.display = 'block';
    }
}

function renderizarGraficoAnalitica(articulaciones, total_evaluaciones) {
    const contenedor = document.getElementById('analitica-grafico');
    contenedor.innerHTML = '';
    
    if (!articulaciones || articulaciones.length === 0) {
        contenedor.innerHTML = '<p style="color:#6c757d; text-align:center; padding:20px;">No hay desviaciones críticas registradas.</p>';
        return;
    }
    
    articulaciones.forEach(art => {
        // Ancho de barras ∝ total_detecciones
        let pctAncho = (art.total_detecciones / total_evaluaciones) * 100;
        if (pctAncho > 100) pctAncho = 100;
        
        const fila = document.createElement('div');
        fila.style.marginBottom = '12px';
        
        const etiqueta = document.createElement('div');
        etiqueta.style.display = 'flex';
        etiqueta.style.justifyContent = 'space-between';
        etiqueta.style.fontSize = '14px';
        etiqueta.style.marginBottom = '4px';
        etiqueta.innerHTML = `<strong>${art.articulacion}</strong> <span>${art.total_detecciones} fallas (Avg: ${art.desviacion_promedio_grados.toFixed(1)}°)</span>`;
        
        const barraFondo = document.createElement('div');
        barraFondo.style.width = '100%';
        barraFondo.style.height = '12px';
        barraFondo.style.backgroundColor = '#e9ecef';
        barraFondo.style.borderRadius = '6px';
        barraFondo.style.overflow = 'hidden';
        
        const barra = document.createElement('div');
        barra.style.width = `${pctAncho}%`;
        barra.style.height = '100%';
        barra.style.backgroundColor = '#EF4444'; // Red para desviaciones
        
        barraFondo.appendChild(barra);
        fila.appendChild(etiqueta);
        fila.appendChild(barraFondo);
        contenedor.appendChild(fila);
    });
}

