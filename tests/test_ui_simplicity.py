# tests/test_ui_simplicity.py
"""
Pruebas de validación de simplicidad de interfaz de usuario y endpoints de instructores y fuentes.
Verifica:
1. Ausencia total de emojis en el HTML y CSS.
2. Ausencia de términos técnicos intimidantes en la interfaz visible del usuario.
3. Formulario del Instructor limitado estrictamente a 2 campos (nombre y video).
4. Flujo de alumno basado en selectores simples y panel comparador.
5. Endpoints de soporte para instructores, fuentes (RAG) y análisis visual con video patrón.
"""

import os
import re
import io
from html.parser import HTMLParser
import pytest
from fastapi.testclient import TestClient
from src.presentation.api import app, container
from src.application.controllers import EvaluacionController
from src.infrastructure.mocks import MockYOLOEngine, MockGeminiService, MockTecnicaRepository

class SimpleHTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self.in_script_or_style = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.in_script_or_style = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.in_script_or_style = False

    def handle_data(self, data):
        if not self.in_script_or_style:
            self.texts.append(data)

    def get_text(self):
        return " ".join(self.texts)

@pytest.fixture
def client():
    container["evaluacion_controller"] = EvaluacionController(
        inference_engine=MockYOLOEngine(desviacion_grados=12.0),
        generation_service=MockGeminiService(),
        tecnica_repository=MockTecnicaRepository()
    )
    yield TestClient(app)
    container.clear()

def test_no_hay_emojis_en_html():
    """Verifica que el HTML no contenga emojis."""
    html_path = "frontend/index.html"
    assert os.path.exists(html_path), "frontend/index.html no existe"
    
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Rango Unicode de emojis comunes
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]",
        flags=re.UNICODE
    )
    emojis_encontrados = emoji_pattern.findall(content)
    assert len(emojis_encontrados) == 0, f"Se encontraron emojis en index.html: {emojis_encontrados}"

def test_no_hay_terminos_tecnicos_visibles():
    """Verifica que index.html no contenga tecnicismos intimidantes en su texto visible."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        content = f.read()

    parser = SimpleHTMLTextExtractor()
    parser.feed(content)
    texto_visible = parser.get_text()

    terminos_prohibidos = [
        "yolo",
        "yolo26",
        "pgvector",
        "postgresql",
        "embedding",
        "matriz esqueletica",
        "keypoints",
        "rd-03",
        "rf-02",
        "cu-01",
        "cu-02",
        "cu-03",
        "cu-04",
        "as-02",
        "docker"
    ]

    for termino in terminos_prohibidos:
        assert termino not in texto_visible.lower(), f"Término técnico prohibido encontrado en UI: '{termino}'"

def test_instructor_solo_tiene_dos_campos():
    """Verifica que la vista del instructor para registrar técnica tenga estrictamente 2 campos de entrada."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Extraer el bloque del formulario form-tecnica
    form_match = re.search(r'<form\s+id="form-tecnica"[^>]*>(.*?)</form>', content, re.DOTALL)
    assert form_match is not None, "Formulario #form-tecnica no encontrado"
    form_html = form_match.group(1)

    # Contar inputs dentro del formulario
    inputs = re.findall(r'<input\s+[^>]*id="([^"]+)"', form_html)
    assert len(inputs) == 2, f"El formulario debe tener exactamente 2 inputs, encontrados: {len(inputs)} ({inputs})"

    # Verificar que sean nombre y video
    assert "tec-nombre" in inputs
    assert "tec-video" in inputs

    # Sin textarea de descripciones complejas
    assert "<textarea" not in form_html, "No debe haber campo de descripción en la vista simplificada"

def test_alumno_utiliza_selectores_y_comparador():
    """Verifica que la pantalla de inicio del alumno consista en selectores y el comparador tenga video y frame con canvas."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Extraer bloque pantalla-seleccion
    sel_match = re.search(r'<div\s+id="pantalla-seleccion"[^>]*>(.*?)</div>', content, re.DOTALL)
    assert sel_match is not None, "Pantalla #pantalla-seleccion no encontrada"
    sel_html = sel_match.group(1)

    selects = re.findall(r'<select\s+[^>]*id="([^"]+)"', sel_html)
    assert len(selects) >= 2, "La vista del alumno debe tener al menos selector de instructor y de técnica"
    assert "alumno-instructor" in selects
    assert "alumno-tecnica" in selects

    # Pantalla de resultado tiene comparador con video patron, frame alumno y canvas
    assert 'id="video-patron"' in content
    assert 'id="frame-alumno"' in content
    assert 'id="canvas-puntos"' in content
    assert 'id="texto-consejo"' in content

def test_api_crear_y_listar_instructores(client):
    """Verifica los endpoints para crear y listar instructores."""
    # 1. Crear instructor
    data_nuevo = {
        "id_instructor": "prof_test",
        "nombre_completo": "Prof. Test Automatizado"
    }
    resp_crear = client.post("/api/v1/instructores", data=data_nuevo)
    assert resp_crear.status_code == 200
    assert "id_instructor" in resp_crear.json()

    # 2. Listar instructores
    resp_list = client.get("/api/v1/instructores")
    assert resp_list.status_code == 200
    instructores = resp_list.json()
    assert isinstance(instructores, list)
    assert len(instructores) > 0
    assert any(i.get("id_instructor") == "prof_test" or i.get("id") == "prof_test" for i in instructores)

def test_api_subir_manual_fuente(client):
    """Verifica el endpoint de carga de manuales técnicos en PDF."""
    pdf_dummy_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    files = {
        "archivo": ("manual_test.pdf", io.BytesIO(pdf_dummy_bytes), "application/pdf")
    }
    data = {
        "id_instructor": "inst_carlos",
        "titulo": "Manual de Guardia Cerrada"
    }
    resp = client.post("/api/v1/fuentes", files=files, data=data)
    assert resp.status_code == 200
    resultado = resp.json()
    assert "Manual procesado y almacenado exitosamente" in resultado["message"]
    assert resultado["titulo"] == "Manual de Guardia Cerrada"

def test_evaluacion_retorna_video_patron_y_frame_alumno(client):
    """Verifica que la evaluación retorne video_patron_url, frame_alumno_base64, desviaciones y consejo."""
    video_bytes = b"fake-mp4-video-student-evaluation"
    files = {
        "file": ("movimiento.mp4", io.BytesIO(video_bytes), "video/mp4")
    }
    data = {
        "id_instructor": "inst_carlos",
        "id_tecnica": "armbar_guardia"
    }

    resp = client.post("/api/v1/evaluaciones/evaluar", files=files, data=data)
    assert resp.status_code == 200
    resultado = resp.json()

    assert "frame_alumno_base64" in resultado or "frame_url" in resultado
    assert "video_patron_url" in resultado
    assert "desviaciones" in resultado
    assert "consejo" in resultado
    assert "/static/videos_patron/" in resultado["video_patron_url"]

    # Verificar que el consejo no contenga tecnicismos
    assert "gemini" not in resultado["consejo"].lower()
    assert "yolo" not in resultado["consejo"].lower()

    for dev in resultado["desviaciones"]:
        assert "x" in dev
        assert "y" in dev
        assert isinstance(dev["x"], (int, float))
        assert isinstance(dev["y"], (int, float))

def test_api_evaluar_con_video_real(client):
    """Verifica el endpoint evaluar-real que persiste en uploads/ y retorna frame_alumno."""
    video_bytes = b"real-mp4-test-bytes"
    files = {
        "file": ("video_real_test.mp4", io.BytesIO(video_bytes), "video/mp4")
    }
    data = {
        "id_tecnica": "armbar_guardia"
    }
    resp = client.post("/api/v1/evaluaciones/evaluar-real", files=files, data=data)
    assert resp.status_code == 200
    resultado = resp.json()

    assert "frame_alumno" in resultado
    assert "video_patron_url" in resultado
    assert "desviaciones" in resultado
    assert "consejo" in resultado
    # Verificar persistencia física en uploads
    assert os.path.exists("uploads/video_real_test.mp4")

