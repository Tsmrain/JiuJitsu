import os
import sys
import time
import json
import urllib.request
import urllib.error
from pathlib import Path
from uuid import uuid4

# Importar backend modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from corpocmente.infrastructure.ai.adapters import (
    obtener_nombres_articulaciones,
    COCO_JOINT_NAMES_ES,
    COCO_JOINT_NAMES_PT,
    COCO_JOINT_NAMES_EN
)

ARTIFACTS_DIR = Path("/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def test_fase_1_backend_username_validation():
    print("\n--- [PRUEBA 1] Backend: Validación Estricta de Username (Sin Espacios) ---")
    url = "http://localhost:8000/api/v1/auth/signup"

    # Caso 1.1: Username con espacios ("juan perez")
    payload_invalid = {
        "nombre_completo": "Juan Perez",
        "username": "juan perez",
        "password": "password123",
        "rol": "alumno"
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload_invalid).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req)
        raise AssertionError("ERROR: El backend aceptó 'juan perez' con espacios!")
    except urllib.error.HTTPError as e:
        assert e.code == 422, f"Se esperaba código 422 pero se obtuvo {e.code}"
        body = json.loads(e.read().decode("utf-8"))
        print(f" [PASS] 'juan perez' rechazado con HTTP 422:")
        print(f"   Detalle: {body.get('detail')}")

    # Caso 1.2: Username con símbolos ("juan@perez!")
    payload_invalid_symbols = {
        "nombre_completo": "Juan Perez",
        "username": "juan@perez!",
        "password": "password123",
        "rol": "alumno"
    }
    req_sym = urllib.request.Request(
        url,
        data=json.dumps(payload_invalid_symbols).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req_sym)
        raise AssertionError("ERROR: El backend aceptó 'juan@perez!' con símbolos!")
    except urllib.error.HTTPError as e:
        assert e.code == 422, f"Se esperaba 422 pero se obtuvo {e.code}"
        print(f" [PASS] 'juan@perez!' rechazado con HTTP 422.")

    # Caso 1.3: Username válido ("juan_perez_4h")
    temp_valid = f"juan_perez_{uuid4().hex[:6]}"
    payload_valid = {
        "nombre_completo": "Juan Perez Valido",
        "username": temp_valid,
        "password": "password123",
        "rol": "alumno"
    }
    req_ok = urllib.request.Request(
        url,
        data=json.dumps(payload_valid).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req_ok)
    assert res.code == 201, f"Se esperaba 201 pero se obtuvo {res.code}"
    res_data = json.loads(res.read().decode("utf-8"))
    assert res_data["username"] == temp_valid
    user_id = res_data["user_id"]
    token = res_data["token"]
    print(f" [PASS] '{temp_valid}' registrado exitosamente con HTTP 201 (user_id: {user_id}).")

    # Limpiar usuario temporal de la BD
    from corpocmente.ui.api.auth_routes import get_db, _sign_token
    try:
        db = get_db()
        admin_token = _sign_token({"uid": str(uuid4()), "role": "admin", "email": "admin@bjj.com"})
        db.rpc("admin_delete_user", {"p_user_id": str(user_id)}, token=admin_token)
        print(" [CLEAN] Usuario temporal eliminado de la BD con admin_delete_user.")
    except Exception as e_clean:
        print(f"   Aviso al limpiar usuario: {e_clean}")


def test_fase_3_catalogo_limpio_api():
    print("\n--- [PRUEBA 2] Backend: Catálogo de Libros Limpio (HTTP 200 con []) ---")
    from corpocmente.ui.api.auth_routes import _sign_token
    token = _sign_token({"uid": str(uuid4()), "role": "admin", "email": "admin@bjj.com"})
    url = "http://localhost:8000/api/v1/conocimiento/manuales"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    res = urllib.request.urlopen(req)
    assert res.code == 200
    data = json.loads(res.read().decode("utf-8"))
    print(f" [PASS] GET /api/v1/conocimiento/manuales retornó: {data}")
    assert data == [], f"El catálogo debía estar vacío ([]) pero contenía: {data}"
    print(" [PASS] Catálogo limpio verificado (0 libros residuales).")


def test_fase_4_i18n_articulaciones():
    print("\n--- [PRUEBA 3] Backend: i18n Total en Nombres de Articulaciones ---")
    # Caso 3.1: Índices COCO a Portugués
    indices = [13, 14, 7, 8]  # Rodilla izq, rodilla der, codo izq, codo der
    pt_names = obtener_nombres_articulaciones(indices, idioma="pt")
    print(f" [PASS] Índices {indices} -> PT: {pt_names}")
    assert pt_names == ["Joelho Esquerdo", "Joelho Direito", "Cotovelo Esquerdo", "Cotovelo Direito"]

    # Caso 3.2: Índices COCO a Español
    es_names = obtener_nombres_articulaciones(indices, idioma="es")
    print(f" [PASS] Índices {indices} -> ES: {es_names}")
    assert es_names == ["Rodilla izquierda", "Rodilla derecha", "Codo izquierdo", "Codo derecho"]

    # Caso 3.3: Índices COCO a Inglés
    en_names = obtener_nombres_articulaciones(indices, idioma="en")
    print(f" [PASS] Índices {indices} -> EN: {en_names}")
    assert en_names == ["Left Knee", "Right Knee", "Left Elbow", "Right Elbow"]

    # Caso 3.4: Traducción de Nombres en Inglés hacia Portugués
    translated_pt = obtener_nombres_articulaciones(["Left Knee", "Right Knee"], idioma="pt")
    print(f" [PASS] Strings ['Left Knee', 'Right Knee'] -> PT: {translated_pt}")
    assert translated_pt == ["Joelho Esquerdo", "Joelho Direito"]

    # Caso 3.5: Facade con idioma='pt'
    from unittest.mock import Mock
    from corpocmente.domain.services.intelligence_facade import IntelligenceAnalysisFacade
    from corpocmente.infrastructure.ai.adapters import YOLOPoseAdapter
    from corpocmente.infrastructure.ai.local_vlm_adapter import LocalVLMAdapter
    from corpocmente.infrastructure.persistence.qdrant_adapter import QdrantVectorAdapter, VectorSearchResultDTO
    from corpocmente.domain.entities.models import EsqueletoBiomecanico

    mock_yolo = Mock(spec=YOLOPoseAdapter)
    mock_qdrant = Mock(spec=QdrantVectorAdapter)
    mock_gemini = Mock(spec=LocalVLMAdapter)

    mock_esqueleto = Mock(spec=EsqueletoBiomecanico)
    mock_esqueleto.to_vector_array.return_value = [0.1] * 133
    mock_yolo.extraer_keypoints.return_value = [mock_esqueleto]

    vec_result = VectorSearchResultDTO(score=92.0, frame_path="/tmp/frame.jpg", discrepancias=[])
    vec_result.articulaciones_criticas = [13, 14]
    mock_qdrant.buscar_maxima_diferencia.return_value = vec_result

    facade = IntelligenceAnalysisFacade(mock_yolo, mock_qdrant, mock_gemini)
    res_pt = facade.ejecutar_analisis_completo("/tmp/nonexistent.mp4", uuid4(), "Passagem de Guarda", idioma="pt")
    print(f" [PASS] Facade resultado PT nombres_articulaciones_criticas: {res_pt.nombres_articulaciones_criticas}")
    assert res_pt.nombres_articulaciones_criticas == ["Joelho Esquerdo", "Joelho Direito"]


def test_fase_2_y_frontend_playwright():
    print("\n--- [PRUEBA 4] Frontend E2E (Playwright): Persistencia de Sesión y Validación UI ---")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # 4.1 Cargar frontend y asegurar estado limpio (Invitado)
        print(" -> Navegando a http://localhost:5173/ ...")
        page.goto("http://localhost:5173/")
        page.wait_for_timeout(1000)
        page.evaluate("() => { localStorage.clear(); }")
        page.reload()
        page.wait_for_timeout(1000)

        # 4.2 Abrir modal de login y probar validación de username con espacios
        print(" -> Abriendo modal de autenticación...")
        avatar_btn = page.locator("[data-testid='user-avatar-btn']")
        avatar_btn.click()
        page.wait_for_timeout(600)

        # Cambiar a pestaña Crear Cuenta / Signup
        print(" -> Cambiando a pestaña Crear Cuenta...")
        signup_tab_btn = page.locator("[data-testid='tab-signup-btn']")
        signup_tab_btn.click()
        page.wait_for_timeout(500)

        # Ingresar username con espacios
        print(" -> Ingresando username con espacios 'juan perez'...")
        username_input = page.locator("[data-testid='signup-username-input']")
        username_input.fill("juan perez")
        page.wait_for_timeout(400)

        # Verificar mensaje de error y botón deshabilitado
        error_msg = page.locator("[data-testid='username-error-msg']")
        assert error_msg.is_visible(), "El mensaje de error de username no apareció al tipear espacios!"
        submit_btn = page.locator("[data-testid='signup-submit-btn']")
        assert submit_btn.is_disabled(), "El botón de crear cuenta no se deshabilitó al haber espacios!"
        print(" [PASS] UI de Signup bloqueó username con espacios y mostró alerta.")

        # Tomar screenshot de la validación
        screenshot_signup = ARTIFACTS_DIR / "screenshot_signup_username_space_validation.png"
        page.screenshot(path=str(screenshot_signup))
        print(f" [SCREENSHOT] Guardado en: {screenshot_signup}")

        # 4.3 Iniciar sesión con Admin para probar persistencia tras reload
        print(" -> Cambiando a Login e iniciando sesión como Admin...")
        login_tab_btn = page.locator("[data-testid='tab-login-btn']")
        login_tab_btn.click()
        page.wait_for_timeout(400)

        page.locator("[data-testid='login-username-input']").fill("admin")
        page.locator("[data-testid='login-password-input']").fill("admin123")
        page.locator("[data-testid='login-submit-btn']").click()
        page.wait_for_timeout(2000)

        # Verificar que el usuario 'Administrador' o 'admin' está logueado
        header_text = page.locator("header").inner_text()
        print(f" -> Header tras login: {header_text.replace(chr(10), ' | ')}")
        assert "admin" in header_text.lower() or "administrador" in header_text.lower(), "Admin no aparece logueado!"

        # Verificar localStorage
        auth_token = page.evaluate("() => localStorage.getItem('auth_token')")
        auth_user = page.evaluate("() => localStorage.getItem('auth_user')")
        assert auth_token is not None and len(auth_token) > 10, "auth_token no guardado en localStorage!"
        assert auth_user is not None and "admin" in auth_user, "auth_user no guardado en localStorage!"
        print(f" [PASS] auth_token y auth_user correctamente almacenados en localStorage.")

        # 4.4 RECARGAR PÁGINA (F5 / page.reload())
        print(" -> Ejecutando page.reload() para verificar persistencia de sesión...")
        page.reload()
        page.wait_for_timeout(1500)

        # Verificar que el usuario SIGUE autenticado sin volver a 'Invitado'
        header_text_after = page.locator("header").inner_text()
        print(f" -> Header tras reload: {header_text_after.replace(chr(10), ' | ')}")
        assert "invitado" not in header_text_after.lower() and "guest" not in header_text_after.lower(), "La sesión se perdió tras recargar la página!"
        assert "admin" in header_text_after.lower() or "administrador" in header_text_after.lower(), "El usuario admin no se restauró tras reload!"
        print(" [PASS] SESIÓN PERSISTE EXITOSAMENTE TRAS RECARGAR LA PÁGINA (Fix Logout verificado).")

        # Tomar screenshot de la sesión restaurada
        screenshot_session = ARTIFACTS_DIR / "screenshot_session_persists_after_reload.png"
        page.screenshot(path=str(screenshot_session))
        print(f" [SCREENSHOT] Guardado en: {screenshot_session}")

        # 4.5 Navegar a la Biblioteca y verificar catálogo vacío
        print(" -> Navegando a la Biblioteca y revisando Catálogo de Libros...")
        library_btn = page.locator("button:has-text('Biblioteca'), button:has-text('Library')").first
        library_btn.click()
        page.wait_for_timeout(800)

        catalog_tab = page.locator("button:has-text('Catálogo')").first
        catalog_tab.click()

        # Esperar a que el catálogo cargue y muestre el mensaje de estado vacío
        empty_msg_el = page.wait_for_selector("text=No se encontraron manuales PDF disponibles", timeout=8000)
        assert empty_msg_el is not None, "El mensaje de catálogo vacío no se encontró!"
        print(" [PASS] Catálogo de Libros muestra el estado vacío ('No se encontraron manuales PDF disponibles').")

        # Tomar screenshot del catálogo limpio
        screenshot_catalog = ARTIFACTS_DIR / "screenshot_catalog_empty_state.png"
        page.screenshot(path=str(screenshot_catalog))
        print(f" [SCREENSHOT] Guardado en: {screenshot_catalog}")

        browser.close()


if __name__ == "__main__":
    print("=" * 70)
    print("EJECUTANDO PRUEBAS DE FUEGO ITERACIÓN 4H (RIGOR CRAIG LARMAN)")
    print("=" * 70)
    test_fase_1_backend_username_validation()
    test_fase_3_catalogo_limpio_api()
    test_fase_4_i18n_articulaciones()
    test_fase_2_y_frontend_playwright()
    print("\n" + "=" * 70)
    print("✅ TODAS LAS PRUEBAS DE FUEGO DE LA ITERACIÓN 4H PASARON EXITOSAMENTE!")
    print("=" * 70)
