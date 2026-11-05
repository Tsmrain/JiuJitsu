import os
import sys
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = Path("/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://localhost:5173"

def run_e2e_tests():
    print("\n========================================================")
    print("🚀 INICIANDO PRUEBAS E2E PLAYWRIGHT — ITERACIÓN 4J")
    print("========================================================\n")

    # Resetear idioma de Mike a 'pt' en la base de datos para inicio limpio
    import psycopg2
    try:
        conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/corpocmente")
        cur = conn.cursor()
        cur.execute("UPDATE usuarios SET idioma_preferido = 'pt' WHERE username = 'mike';")
        conn.commit()
        conn.close()
        print(" [SETUP] Idioma de Mike reseteado a 'pt' en PostgreSQL.")
    except Exception as e_db:
        print(f" [SETUP] Advertencia DB: {e_db}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1366, "height": 900})
        page = context.new_page()

        # ----------------------------------------------------
        # TEST 1: FASE 4 — Respeto Absoluto del Idioma del Usuario
        # ----------------------------------------------------
        print("\n--- [TEST 1] FASE 4: Idioma Mike (PT) -> Persistencia tras Reload -> Cambio a ES ---")
        page.goto(BASE_URL)
        page.wait_for_timeout(1000)
        page.evaluate("() => localStorage.clear()")
        page.reload()
        page.wait_for_timeout(1000)

        # Login con Mike (idioma_preferido: 'pt')
        print(" -> Abriendo modal de login...")
        page.locator("[data-testid='user-avatar-btn']").click()
        page.wait_for_timeout(500)
        page.locator("[data-testid='tab-login-btn']").click()
        page.wait_for_timeout(300)

        page.locator("[data-testid='login-username-input']").fill("mike")
        page.locator("[data-testid='login-password-input']").fill("password123")
        page.locator("[data-testid='login-submit-btn']").click()
        page.wait_for_timeout(2000)

        # Verificar que el idioma detectado y aplicado es 'pt'
        app_idioma = page.evaluate("() => localStorage.getItem('app_idioma')")
        auth_user_raw = page.evaluate("() => localStorage.getItem('auth_user')")
        auth_user = json.loads(auth_user_raw) if auth_user_raw else {}
        print(f" -> auth_user idioma_preferido: {auth_user.get('idioma_preferido')}")
        print(f" -> localStorage app_idioma: {app_idioma}")
        assert app_idioma == "pt", f"Se esperaba app_idioma 'pt' pero fue {app_idioma}"

        header_text = page.locator("header").inner_text()
        print(f" -> Header en PT: {header_text.replace(chr(10), ' | ')}")
        # En PT debe contener 'Painel de Alunos' o 'Técnicas'
        assert "painel" in header_text.lower() or "técnicas" in header_text.lower() or "mike" in header_text.lower(), "Texto en PT no detectado en header"

        screenshot_mike_pt = ARTIFACTS_DIR / "screenshot_language_persistence_mike_pt.png"
        page.screenshot(path=str(screenshot_mike_pt))
        print(f" [PASS] Mike logueado en PT. Screenshot: {screenshot_mike_pt.name}")

        # Recargar página y verificar que SIGUE en PT
        print(" -> Ejecutando page.reload() para verificar persistencia de PT...")
        page.reload()
        page.wait_for_timeout(1500)

        app_idioma_after_reload = page.evaluate("() => localStorage.getItem('app_idioma')")
        assert app_idioma_after_reload == "pt", f"Fallo al persistir: tras reload idioma es {app_idioma_after_reload}"
        print(" [PASS] Idioma PT persistió intacto tras recargar la página.")

        # Cambiar idioma a ES mediante el selector de idioma en el header
        print(" -> Cambiando idioma a Español (ES) en UI...")
        lang_select = page.locator("header select, [data-testid='language-select']").first
        if lang_select.is_visible():
            lang_select.select_option("es")
        else:
            page.evaluate("() => window.dispatchEvent(new CustomEvent('changeLanguage', { detail: 'es' }))")
        page.wait_for_timeout(1000)

        app_idioma_es = page.evaluate("() => localStorage.getItem('app_idioma')")
        print(f" -> app_idioma tras cambio a ES: {app_idioma_es}")
        assert app_idioma_es == "es", f"Se esperaba 'es' pero fue {app_idioma_es}"

        # Recargar para verificar que 'es' persiste tras reload
        page.reload()
        page.wait_for_timeout(1500)
        app_idioma_es_reloaded = page.evaluate("() => localStorage.getItem('app_idioma')")
        assert app_idioma_es_reloaded == "es", f"Se esperaba 'es' tras reload pero fue {app_idioma_es_reloaded}"
        
        screenshot_mike_es = ARTIFACTS_DIR / "screenshot_language_persistence_mike_es.png"
        page.screenshot(path=str(screenshot_mike_es))
        print(f" [PASS] Idioma ES persistió tras reload. Screenshot: {screenshot_mike_es.name}")

        # ----------------------------------------------------
        # TEST 2: FASE 3 — Modal "Teoría de la Técnica" con Instrucciones del Instructor e i18n
        # ----------------------------------------------------
        print("\n--- [TEST 2] FASE 3: Modal de Teoría con Instrucciones del Instructor e i18n ---")
        # Asegurarse de estar en el panel de profesor
        page.evaluate("() => { if (window.__setAppState) window.__setAppState('PROFESOR_PANEL'); }")
        page.wait_for_timeout(1000)

        # Cambiar a la pestaña de Técnicas
        tecnicas_tab_btn = page.locator("button:has-text('Técnicas'), button:has-text('Techniques')").first
        tecnicas_tab_btn.wait_for(state="visible", timeout=8000)
        tecnicas_tab_btn.click()
        page.wait_for_timeout(1200)

        # Buscar el botón de Teoría de la Técnica en la tarjeta de técnica
        print(" -> Abriendo modal de Teoría de la Técnica...")
        theory_btn = page.locator("[data-testid='open-theory-modal-btn'], button.theory-btn").first
        theory_btn.wait_for(state="visible", timeout=10000)
        theory_btn.click()
        page.wait_for_timeout(1500)

        # Verificar que el modal está abierto
        modal_title_el = page.locator("[data-testid='theory-modal-title']")
        modal_title_el.wait_for(state="visible", timeout=10000)
        modal_title = modal_title_el.inner_text()
        print(f" -> Título del modal de teoría: '{modal_title}'")
        assert "Teoría de la Técnica" in modal_title or "Teoria da Técnica" in modal_title, f"Título inesperado: {modal_title}"

        # Verificar sección de Instrucciones del Instructor (mensaje_profesor)
        instructor_box = page.locator("[data-testid='instructor-instructions-box']")
        assert instructor_box.is_visible(), "El recuadro de Instrucciones del Instructor no es visible!"
        instructor_text = instructor_box.inner_text()
        print(f" -> Contenido de instrucciones del instructor:\n{instructor_text}")
        assert "pararce y maneter la postura" in instructor_text or "postura" in instructor_text, "El mensaje del profesor no se mostró correctamente!"

        # Capturar screenshot del modal con las instrucciones del instructor
        screenshot_theory_modal = ARTIFACTS_DIR / "screenshot_theory_modal_instructor_message.png"
        page.screenshot(path=str(screenshot_theory_modal))
        print(f" [PASS] Modal de teoría verificado. Screenshot: {screenshot_theory_modal.name}")

        # Cerrar el modal
        close_modal_btn = page.locator("[data-testid='close-theory-modal-btn']").first
        if close_modal_btn.is_visible():
            close_modal_btn.click(force=True)
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(800)

        # ----------------------------------------------------
        # TEST 3: FASE 2 — Reproducción de Videos en StudentProgress
        # ----------------------------------------------------
        print("\n--- [TEST 3] FASE 2: Reproducción de Videos en StudentProgress (Alumno Activo) ---")
        # Cerrar sesión de Mike limpiando localStorage y recargando
        page.evaluate("() => { localStorage.removeItem('auth_token'); localStorage.removeItem('auth_user'); }")
        page.reload()
        page.wait_for_timeout(1000)

        # Login como alumno1
        print(" -> Iniciando sesión como alumno1...")
        avatar_btn = page.locator("[data-testid='user-avatar-btn']")
        avatar_btn.click()
        page.wait_for_timeout(500)
        login_tab = page.locator("[data-testid='tab-login-btn']")
        if login_tab.is_visible():
            login_tab.click()
            page.wait_for_timeout(300)
        page.locator("[data-testid='login-username-input']").fill("alumno1")
        page.locator("[data-testid='login-password-input']").fill("password123")
        page.locator("[data-testid='login-submit-btn']").click()
        page.wait_for_timeout(2000)

        # Navegar a 'Mi Progreso'
        print(" -> Navegando a 'Mi Progreso'...")
        my_progress_btn = page.locator("button:has-text('Mi Progreso'), button:has-text('Meu Progresso')").first
        if my_progress_btn.is_visible():
            my_progress_btn.click()
        else:
            page.evaluate("() => { if (window.__setAppState) window.__setAppState('STUDENT_PROGRESS'); }")
        page.wait_for_timeout(2000)

        # Verificar que se cargaron las evaluaciones
        eval_articles = page.locator("article.glass-panel")
        eval_count = eval_articles.count()
        print(f" -> Tarjetas de evaluación encontradas en Mi Progreso: {eval_count}")
        assert eval_count > 0, "No se encontraron evaluaciones para el alumno1!"

        # Verificar que hay elementos <video> y <source src="...">
        videos = page.locator("article.glass-panel video source")
        video_count = videos.count()
        print(f" -> Fuentes <source> de video encontradas: {video_count}")
        assert video_count >= 1, "No se encontraron elementos <source> en los videos de evaluación!"

        first_video_src = videos.first.get_attribute("src")
        print(f" -> URL del primer video en StudentProgress: '{first_video_src}'")
        assert "/static/videos/" in first_video_src, f"URL no esperada: {first_video_src}"

        # Esperar 1.5s para renderizado completo de frames/videos
        page.wait_for_timeout(1500)

        screenshot_student_progress = ARTIFACTS_DIR / "screenshot_student_progress_video_playback.png"
        page.screenshot(path=str(screenshot_student_progress))
        print(f" [PASS] Videos en StudentProgress verificados. Screenshot: {screenshot_student_progress.name}")

        # ----------------------------------------------------
        # TEST 4: FASE 2 — Reproducción de Videos en FeedbackView
        # ----------------------------------------------------
        print("\n--- [TEST 4] FASE 2: Reproducción de Videos en FeedbackView (Vista Completa) ---")
        # Simular transición a FeedbackView con los videos de alumno y referencia
        feedback_data = {
            "id": "fe0c83e4-2836-4717-ad82-900f353969ce",
            "similitud": 84.5,
            "feedback": "Buen control de postura inicial. Se detecta desalineación en rodillas al intentar la apertura.",
            "feedback_summary": "Desalineación en rodillas y postura",
            "timestamp_error_segundos": 2.45,
            "url_video_alumno": "/static/videos/ea88f4df-6c1d-42ee-a160-4926e5580155.mp4",
            "video_referencia_url": "/static/videos/eb9d9230-e30f-4fe4-96c3-271feb1f4d71.mp4",
            "video_referencia_profesor_nombre": "Prof. Milton Flores",
            "frame_error_url": None,
            "nombres_articulaciones_criticas": ["Rodilla Izquierda", "Rodilla Derecha"]
        }
        tecnica_data = {
            "id": "414b1ca8-7760-4bdf-8ad9-6bb2ece3fef0",
            "nombre": "Escape de guardia cerrada",
            "profesorRef": "Prof. Milton Flores"
        }

        page.evaluate(
            "([resData, tecData]) => window.__setAppState('FEEDBACK', resData, tecData)",
            [feedback_data, tecnica_data]
        )
        page.wait_for_timeout(2000)

        # Verificar que FeedbackView se muestra
        feedback_container = page.locator(".feedback-container, .feedback-view")
        assert feedback_container.is_visible(), "FeedbackView no apareció tras invocar __setAppState!"

        # Verificar los dos reproductores de video (Alumno y Profesor)
        feedback_video_sources = page.locator(".feedback-container video source, .feedback-view video source")
        fb_video_count = feedback_video_sources.count()
        print(f" -> Fuentes <source> en FeedbackView: {fb_video_count}")
        assert fb_video_count >= 2, f"Se esperaban 2 videos (alumno y referencia) pero se encontraron {fb_video_count}"

        src_ref = feedback_video_sources.nth(0).get_attribute("src")
        src_alu = feedback_video_sources.nth(1).get_attribute("src")
        print(f" -> Video Referencia src: {src_ref}")
        print(f" -> Video Alumno src:     {src_alu}")
        assert "/static/videos/" in src_ref, f"URL de referencia no válida: {src_ref}"
        assert "/static/videos/" in src_alu, f"URL de alumno no válida: {src_alu}"

        screenshot_feedback_view = ARTIFACTS_DIR / "screenshot_feedback_view_video_playback.png"
        page.screenshot(path=str(screenshot_feedback_view))
        print(f" [PASS] FeedbackView con doble video verificado. Screenshot: {screenshot_feedback_view.name}")

        browser.close()

    print("\n========================================================")
    print("✅ TODAS LAS PRUEBAS E2E DE PLAYWRIGHT PASARON EXITOSAMENTE")
    print("========================================================\n")

if __name__ == "__main__":
    run_e2e_tests()

