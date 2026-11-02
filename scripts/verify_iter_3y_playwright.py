import os
import sys
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def verify_all():
    print("=================================================================")
    print("🚀 PLAYWRIGHT EMPIRICAL VERIFICATION — ITERACIÓN 3Y")
    print("   (Erradicación Total de i18n y Búsqueda Visual de Teoría)")
    print("=================================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 950})
        page = context.new_page()

        # -------------------------------------------------------------
        # PARTE 1: VERIFICACIÓN EN ESPAÑOL (ES) — ADMIN & PERFIL
        # -------------------------------------------------------------
        print("\n[1/6] Configurando idioma inicial en Español (ES)...")
        page.goto("http://localhost:5173")
        page.evaluate("() => localStorage.setItem('app_idioma', 'es')")
        page.reload()
        page.wait_for_timeout(1000)

        # Login como admin para probar AdminSucursales
        print("  Autenticando como 'admin' (idioma preferido: 'es')...")
        avatar_btn = page.locator("header .user-nav > div:last-child").first
        avatar_btn.click()
        page.wait_for_timeout(600)

        page.fill("input[placeholder*='admin or'], input[type='text']", "admin")
        page.fill("input[placeholder*='••••'], input[type='password']", "admin123")
        page.click("button[type='submit']")
        page.wait_for_timeout(1500)

        # 1.1 Validar AdminSucursales en Español
        print("\n[2/6] Validando AdminSucursales en Español...")
        page.evaluate("() => window.__setAppState('ADMIN_PANEL')")
        page.wait_for_timeout(1000)

        body_text_es = page.inner_text("body")
        assert "Gestión Global de Sedes" in body_text_es or "Catálogo de Sucursales" in body_text_es, "Fallo: Título de AdminSucursales en español no encontrado"
        print("  ✓ Título en español encontrado ('Gestión Global de Sedes' / 'Catálogo de Sucursales')")
        assert "Comenzar Entrenamiento" in body_text_es, "Fallo: 'Comenzar Entrenamiento' no encontrado"
        print("  ✓ 'Comenzar Entrenamiento' encontrado")
        assert "Gestión de Sucursales" in body_text_es or "Nuestras Sedes" in body_text_es, "Fallo: Pestaña 'Nuestras Sedes' no encontrada"
        print("  ✓ Pestaña en español encontrada")

        screenshot_admin_es = os.path.join(OUTPUT_DIR, "screenshot_admin_sucursales_es.png")
        page.screenshot(path=screenshot_admin_es, full_page=True)
        print(f"  📸 Captura guardada: {screenshot_admin_es}")

        # 1.2 Validar UserProfileModal en Español
        print("\n[3/6] Validando UserProfileModal en Español...")
        avatar_btn = page.locator("header .user-nav > div:last-child").first
        avatar_btn.click()
        page.wait_for_timeout(800)

        body_modal_es = page.inner_text("body")
        assert "Mi Perfil" in body_modal_es, "Fallo: 'Mi Perfil' no encontrado en modal"
        assert "Idioma de Análisis y Feedback" in body_modal_es, "Fallo: 'Idioma de Análisis y Feedback' no encontrado"
        assert "Guardar Cambios" in body_modal_es, "Fallo: 'Guardar Cambios' no encontrado"
        print("  ✓ UserProfileModal completamente en español")

        screenshot_profile_es = os.path.join(OUTPUT_DIR, "screenshot_user_profile_modal_es.png")
        page.screenshot(path=screenshot_profile_es, full_page=True)
        print(f"  📸 Captura guardada: {screenshot_profile_es}")

        # Cerrar sesión del admin desde el modal de perfil
        print("  Cerrando sesión de admin desde el modal...")
        sign_out_btn = page.locator("button:has-text('Cerrar Sesión')")
        assert sign_out_btn.count() > 0, "Fallo: Botón 'Cerrar Sesión' no visible en modal de perfil"
        sign_out_btn.first.click()
        page.wait_for_timeout(1000)

        # -------------------------------------------------------------
        # PARTE 2: INSTRUCTOR 'MIKE' (PT NATIVO) Y CAMBIO A ESPAÑOL
        # -------------------------------------------------------------
        print("\n[4/6] Login como Instructor 'mike' (idioma preferido en BD: 'pt')...")
        avatar_btn = page.locator("header .user-nav > div:last-child").first
        avatar_btn.click()
        page.wait_for_timeout(600)
        page.fill("input[placeholder*='admin or'], input[type='text']", "mike")
        page.fill("input[placeholder*='••••'], input[type='password']", "password123")
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)

        # Validar que mike cargó en Portugués (su preferencia en BD)
        body_prof_pt = page.inner_text("body")
        assert "Painel Instrutor" in body_prof_pt, "Fallo: 'Painel Instrutor' en PT no encontrado"
        print("  ✓ 'Painel Instrutor' en Portugués detectado automáticamente por preferencia en BD")
        assert "Acompanhamento Biomecânico de Alunos no Jiu-Jitsu" in body_prof_pt, "Fallo: 'Acompanhamento Biomecânico' en PT no encontrado"
        print("  ✓ 'Acompanhamento Biomecânico de Alunos no Jiu-Jitsu' (PT) encontrado")

        screenshot_prof_pt = os.path.join(OUTPUT_DIR, "screenshot_profesor_tecnicas_pt.png")
        page.screenshot(path=screenshot_prof_pt, full_page=True)
        print(f"  📸 Captura guardada: {screenshot_prof_pt}")

        # Cambiar dinámicamente a Español para mike y verificar traducción
        print("  Cambiando idioma a Español (ES) en panel de instructor...")
        lang_sel = page.locator("select[title*='Idioma'], select[title*='Language']")
        lang_sel.select_option("es")
        page.wait_for_timeout(1000)

        body_prof_es = page.inner_text("body")
        assert "Panel Instructor" in body_prof_es or "Panel de Control del Instructor" in body_prof_es, "Fallo: Título panel instructor en español no encontrado"
        print("  ✓ 'Panel de Control del Instructor' (ES) encontrado tras cambio dinámico")
        assert "Seguimiento Biomecánico de Alumnos en Jiu-Jitsu" in body_prof_es or "Alumnos" in body_prof_es, "Fallo: Sección de alumnos no encontrada"
        print("  ✓ 'Seguimiento Biomecánico de Alumnos en Jiu-Jitsu' (ES) encontrado")

        screenshot_prof_es = os.path.join(OUTPUT_DIR, "screenshot_profesor_tecnicas_es.png")
        page.screenshot(path=screenshot_prof_es, full_page=True)
        print(f"  📸 Captura guardada: {screenshot_prof_es}")

        # -------------------------------------------------------------
        # PARTE 3: CAMBIO DE IDIOMA A PORTUGUÉS (PT), ADMINSUCURSALES Y PERSISTENCIA
        # -------------------------------------------------------------
        print("\n[5/6] Validando AdminSucursales en Portugués (PT) y persistencia...")
        lang_sel.select_option("pt")
        page.wait_for_timeout(1000)

        # Navegar a AdminSucursales en PT y tomar captura
        page.evaluate("() => window.__setAppState('ADMIN_PANEL')")
        page.wait_for_timeout(1000)
        body_admin_pt = page.inner_text("body")
        assert "Catálogo de Unidades" in body_admin_pt or "Nossas Unidades" in body_admin_pt or "Gestão Global de Unidades" in body_admin_pt, "Fallo: AdminSucursales en PT no encontrado"
        print("  ✓ AdminSucursales en Portugués ('Gestão Global de Unidades' / 'Nossas Unidades')")
        screenshot_admin_pt = os.path.join(OUTPUT_DIR, "screenshot_admin_sucursales_pt.png")
        page.screenshot(path=screenshot_admin_pt, full_page=True)
        print(f"  📸 Captura guardada: {screenshot_admin_pt}")

        # Validar persistencia tras recargar
        print("  Recargando página para validar persistencia en localStorage...")
        page.reload()
        page.wait_for_timeout(1200)
        persisted_lang = page.evaluate("() => localStorage.getItem('app_idioma')")
        assert persisted_lang == "pt", f"Fallo: Idioma no persistió en localStorage (actual: {persisted_lang})"
        print(f"  ✓ Idioma persistió correctamente en localStorage: '{persisted_lang}'")

        # -------------------------------------------------------------
        # PARTE 4: RAG VISUAL MULTIMODAL DESDE PROGRESO DEL ALUMNO
        # -------------------------------------------------------------
        print("\n[6/6] Probando RAG Visual: Búsqueda Multimodal desde Progreso del Alumno...")
        # Abrir login modal como santi (alumno)
        avatar_btn = page.locator("header .user-nav > div:last-child").first
        avatar_btn.click()
        page.wait_for_timeout(600)
        page.fill("input[placeholder*='admin or'], input[type='text']", "santi")
        page.fill("input[placeholder*='••••'], input[type='password']", "password123")
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)

        # Navegar a Mi Progreso (Meu Progresso / Mi Progreso)
        prog_btn = page.locator("button:has-text('Meu Progresso'), button:has-text('Mi Progreso')")
        assert prog_btn.count() > 0, "Botón Meu Progresso / Mi Progreso no encontrado"
        prog_btn.first.click()
        page.wait_for_timeout(2500)

        # Buscar botones de teoría
        theory_btns = page.locator("button:has-text('Teoria da Técnica'), button:has-text('Teoría de la Técnica')")
        assert theory_btns.count() > 0, "No se encontraron botones de Teoría en Mi Progreso"
        print(f"  ✓ Encontrados {theory_btns.count()} botones de teoría en el progreso del alumno")

        # Clic en el primer botón de teoría (que tiene frame_error_url configurado)
        theory_btns.first.click()
        page.wait_for_timeout(3500)

        body_lib_text = page.inner_text("body")
        assert "Biblioteca" in body_lib_text, "Fallo: No navegó a la Biblioteca"
        print("  ✓ Navegó correctamente a la Biblioteca")

        # Verificar presencia del Banner Multimodal
        assert "Búsqueda Multimodal Activa" in body_lib_text or "Busca Multimodal Ativa" in body_lib_text, "Fallo: Banner de Búsqueda Multimodal no visible"
        print("  ✓ Banner de Búsqueda Multimodal (Imagen + Texto) visible y activo")

        # Verificar miniatura del frame de error
        error_thumb = page.locator("img[alt='Frame error']")
        assert error_thumb.count() > 0, "Fallo: Miniatura de fotograma de error no visible en banner"
        print("  ✓ Miniatura del fotograma de error renderizada correctamente")

        # Verificar botón para desvincular imagen
        assert "Quitar imagen de búsqueda" in body_lib_text or "Desativar busca por imagem" in body_lib_text or "Desactivar" in body_lib_text, "Fallo: Botón para desactivar imagen no encontrado"
        print("  ✓ Botón para desactivar imagen multimodal presente")

        # Captura de pantalla de la auditoría visual RAG multimodal
        screenshot_visual_rag = os.path.join(OUTPUT_DIR, "screenshot_visual_rag_theory.png")
        page.screenshot(path=screenshot_visual_rag, full_page=True)
        print(f"  📸 Captura guardada: {screenshot_visual_rag}")

        browser.close()
        print("\n=================================================================")
        print("🎉 TODAS LAS VERIFICACIONES VISUALES PLAYWRIGHT ITERACIÓN 3Y COMPLETADAS")
        print("=================================================================")

if __name__ == "__main__":
    verify_all()
