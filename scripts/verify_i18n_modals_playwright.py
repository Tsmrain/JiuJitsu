import os
import sys
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://localhost:5173"

def test_i18n_and_modals():
    print("=" * 70)
    print("🧪 PLAYWRIGHT VERIFICATION: UI, I18N, GLOBAL KNOWLEDGE & THEORY MODALS")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1366, "height": 900})
        page = context.new_page()

        print("\n[1/4] Abriendo aplicación y configurando sesión...")
        page.goto(BASE_URL)
        page.wait_for_timeout(1000)
        page.evaluate("() => localStorage.clear()")
        page.reload()
        page.wait_for_timeout(1000)

        # Login como profesor Mike
        print("\n[2/4] Iniciando sesión como Coach Mike (profesor)...")
        page.locator("[data-testid='user-avatar-btn']").click()
        page.wait_for_timeout(500)
        page.locator("[data-testid='tab-login-btn']").click()
        page.wait_for_timeout(300)

        page.locator("[data-testid='login-username-input']").fill("mike")
        page.locator("[data-testid='login-password-input']").fill("password123")
        page.locator("[data-testid='login-submit-btn']").click()
        page.wait_for_timeout(2000)

        # Forzar idioma Español mediante selector o localStorage
        print("  -> Asegurando idioma en Español (es)...")
        page.evaluate("() => { localStorage.setItem('app_idioma', 'es'); }")
        lang_sel = page.locator("header select, [data-testid='language-select']").first
        if lang_sel.is_visible():
            lang_sel.select_option("es")
        else:
            page.evaluate("() => window.dispatchEvent(new CustomEvent('changeLanguage', { detail: 'es' }))")
        page.wait_for_timeout(1000)

        # Ir al panel de instructor
        print("  -> Navegando a panel de instructor...")
        page.evaluate("() => { if (window.__setAppState) window.__setAppState('PROFESOR_PANEL'); }")
        page.wait_for_timeout(1000)

        # Pestaña Técnicas
        print("\n[3/4] Navegando a pestaña 'Técnicas'...")
        tecnicas_tab = page.locator("button:has-text('Técnicas'), button:has-text('Techniques')").first
        tecnicas_tab.wait_for(state="visible", timeout=8000)
        tecnicas_tab.click()
        page.wait_for_timeout(1200)

        # ----------------------------------------------------
        # TEST: GlobalKnowledgeModal (Fuentes de Conocimiento Global)
        # ----------------------------------------------------
        print("\n  -> Verificando Modal 'Biblioteca Global' (Fuentes de Conocimiento Global)...")
        global_btn = page.locator("button:has-text('Biblioteca Global')").first
        assert global_btn.is_visible(), "Botón 'Biblioteca Global' no visible!"
        global_btn.click()
        page.wait_for_timeout(1200)

        # Verificar textos en español en GlobalKnowledgeModal
        modal_title = page.locator("#global-knowledge-title").inner_text()
        print(f"  ✓ Título modal: '{modal_title}'")
        assert "Fuentes de Conocimiento Global" in modal_title, f"Error: Título inesperado: {modal_title}"

        label_fuente = page.locator("label[for='global-source-name']").inner_text()
        print(f"  ✓ Etiqueta nombre: '{label_fuente}'")
        assert "Nombre de la Fuente" in label_fuente, f"Error: Etiqueta inesperada: {label_fuente}"

        input_placeholder = page.locator("#global-source-name").get_attribute("placeholder")
        print(f"  ✓ Placeholder: '{input_placeholder}'")
        assert "Manual Fundamental" in input_placeholder, f"Error: Placeholder inesperado: {input_placeholder}"

        label_archivo = page.locator("label[for='global-source-file']").inner_text()
        print(f"  ✓ Etiqueta archivo: '{label_archivo}'")
        assert "Manual, texto o imagen" in label_archivo, f"Error: Etiqueta archivo inesperada: {label_archivo}"

        save_btn_text = page.locator("button[type='submit']:has-text('Guardar Fuente Global')").inner_text()
        print(f"  ✓ Botón guardar: '{save_btn_text}'")
        assert "Guardar Fuente Global" in save_btn_text, f"Error: Botón guardar inesperado: {save_btn_text}"

        added_sources_h3 = page.locator("h3:has-text('Fuentes Agregadas')").inner_text()
        print(f"  ✓ Encabezado fuentes: '{added_sources_h3}'")
        assert "Fuentes Agregadas" in added_sources_h3, f"Error: Encabezado inesperado: {added_sources_h3}"

        screenshot_global = OUTPUT_DIR / "screenshot_global_knowledge_modal_es.png"
        page.screenshot(path=str(screenshot_global))
        print(f"  📸 Captura guardada: {screenshot_global.name}")

        # Cerrar modal global
        page.locator("button:has-text('Cerrar')").last.click()
        page.wait_for_timeout(800)

        # ----------------------------------------------------
        # TEST: TheoryManagerModal (Teoría de la Técnica)
        # ----------------------------------------------------
        print("\n[4/4] Verificando modal 'Teoría de la Técnica'...")
        theory_btn = page.locator("[data-testid='open-theory-modal-btn'], button.theory-btn").first
        theory_btn.wait_for(state="visible", timeout=8000)
        theory_btn.click()
        page.wait_for_timeout(1500)

        # Verificar título
        modal_title_el = page.locator("[data-testid='theory-modal-title']")
        modal_title_el.wait_for(state="visible", timeout=8000)
        modal_title = modal_title_el.inner_text()
        print(f"  ✓ Título modal teoría: '{modal_title}'")
        assert "Teoría de la Técnica" in modal_title, f"Error: Título inesperado: {modal_title}"

        # Verificar recuadro de instrucciones del instructor
        instructor_box = page.locator("[data-testid='instructor-instructions-box']")
        if instructor_box.count() > 0 and instructor_box.first.is_visible():
            box_text = instructor_box.first.inner_text()
            print("  ✓ Recuadro de instrucciones del instructor:")
            print(f"    {box_text.splitlines()[:2]}")
            assert "instrucciones del instructor" in box_text.lower(), "Error: Título de instrucciones no visible!"

        # Verificar el nuevo mensaje instructivo cuando chunks === 0
        modal_content = page.locator(".modal-content").inner_text()
        expected_msg = "No hay manuales bibliográficos vinculados a esta técnica. Para añadir material de lectura, sube tus libros en la sección 'Biblioteca Global'."
        
        if "extractos en total" not in modal_content:
            assert expected_msg in modal_content, f"Error: No se encontró el nuevo mensaje de teoría en modal. Contenido:\n{modal_content}"
            print(f"  ✓ Mensaje correcto cuando chunks=0 encontrado en UI:\n    '{expected_msg}'")
            assert "No hay teoría subida para esta técnica." not in modal_content, "Error: El mensaje viejo sigue apareciendo!"
            assert "Edita la técnica para adjuntar" not in modal_content, "Error: El texto engañoso viejo sigue apareciendo!"
            print("  ✓ Verificado: Textos engañosos eliminados por completo.")

        screenshot_theory = OUTPUT_DIR / "screenshot_theory_modal_fixed_es.png"
        page.screenshot(path=str(screenshot_theory))
        print(f"  📸 Captura guardada: {screenshot_theory.name}")

        # Cerrar modal
        page.locator("[data-testid='close-theory-modal-btn']").first.click()
        page.wait_for_timeout(600)

        browser.close()
        print("\n" + "=" * 70)
        print("✅ TODAS LAS PRUEBAS DE UI, I18N Y MODALES SUPERADAS EXITOSAMENTE!")
        print("=" * 70)

if __name__ == "__main__":
    test_i18n_and_modals()
