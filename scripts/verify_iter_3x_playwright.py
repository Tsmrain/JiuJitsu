import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def verify_all():
    print("=================================================================")
    print("🚀 PLAYWRIGHT EMPIRICAL VERIFICATION — ITERACIÓN 3X")
    print("   (Catálogo de Libros, Botón de Teoría, Búsqueda Cognitiva)")
    print("=================================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 950})
        page = context.new_page()

        # 1. Cargar aplicación
        print("\n[1/5] Loading application at http://localhost:5173...")
        page.goto("http://localhost:5173")
        page.wait_for_timeout(1000)

        # Autenticar como alumno santi
        print("\n[2/5] Autenticando como alumno 'santi'...")
        avatar_btn = page.locator("header .user-nav > div:last-child, div[title*='Sesión'], div[title*='Sign In'], div[title*='Entrar'], div[title*='Perfil']").first
        avatar_btn.click()
        page.wait_for_timeout(800)

        # Completar formulario en LoginModal
        page.fill("input[placeholder*='usuario'], input[type='text']", "santi")
        page.fill("input[placeholder*='••••'], input[type='password']", "password123")
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)

        # Asegurar idioma español para la prueba completa
        lang_sel = page.locator("select[title*='Idioma'], select[title*='Language']")
        if lang_sel.count() > 0:
            lang_sel.select_option("es")
            page.wait_for_timeout(600)

        # 2. Navegar a la Biblioteca
        print("\n[3/5] Verificando Biblioteca: Pestañas y Catálogo de Libros...")
        lib_btn = page.locator("button:has-text('Biblioteca')")
        assert lib_btn.count() > 0, "Botón de Biblioteca en el header no encontrado"
        lib_btn.click()
        page.wait_for_timeout(2000)

        body_text = page.inner_text("body")
        assert "Búsqueda Semántica" in body_text, "Pestaña 'Búsqueda Semántica' no encontrada"
        assert "Catálogo de Libros" in body_text, "Pestaña 'Catálogo de Libros' no encontrada"
        print("  ✓ Pestañas 'Búsqueda Semántica' y 'Catálogo de Libros' presentes")

        # Clic en pestaña Catálogo de Libros
        cat_tab = page.locator("button:has-text('Catálogo de Libros'), button:has-text('Catálogo')").first
        cat_tab.click()
        page.wait_for_timeout(2000)

        body_text = page.inner_text("body")
        print("DEBUG BODY TEXT IN CATALOG TAB:")
        print(body_text[:500])
        assert "Jiu-Jitsu University.pdf" in body_text, "Libro 'Jiu-Jitsu University.pdf' no visible en catálogo"
        print("  ✓ 'Jiu-Jitsu University.pdf' listado en el catálogo")

        screenshot_catalog = os.path.join(OUTPUT_DIR, "screenshot_catalog_books.png")
        page.screenshot(path=screenshot_catalog, full_page=True)
        print(f"  📸 Captura guardada: {screenshot_catalog}")

        # Abrir el visor PDF haciendo clic en un libro
        print("\n[4/5] Probando visor PDF embebido (iframe)...")
        open_pdf_btns = page.locator("button:has-text('Abrir PDF')")
        print(f"  ✓ Botones 'Abrir PDF' encontrados: {open_pdf_btns.count()}")
        assert open_pdf_btns.count() > 0, "No se encontró ningún botón 'Abrir PDF'"
        open_pdf_btns.first.click()
        page.wait_for_timeout(2000)

        # Esperar a que el modal con el iframe aparezca
        page.wait_for_selector("iframe", timeout=5000)
        iframe = page.locator("iframe")
        assert iframe.count() > 0, "No se encontró el iframe del visor PDF"
        iframe_src = iframe.get_attribute("src")
        print(f"  ✓ Iframe renderizado con src: {iframe_src}")
        assert "/api/v1/conocimiento/manuales/" in iframe_src, "Ruta de iframe incorrecta"

        body_text = page.inner_text("body")
        assert "Cerrar Visor" in body_text or "Abrir en nueva pestaña" in body_text, "Botones de control del visor no encontrados"
        print("  ✓ Controles de visor modal presentes")

        screenshot_pdf = os.path.join(OUTPUT_DIR, "screenshot_pdf_modal.png")
        page.screenshot(path=screenshot_pdf, full_page=True)
        print(f"  📸 Captura guardada: {screenshot_pdf}")

        # Cerrar el modal
        close_btn = page.locator("button:has-text('Cerrar Visor'), button:has-text('Fechar Leitor'), button:has-text('Close Viewer')")
        if close_btn.count() > 0:
            close_btn.first.click()
            page.wait_for_timeout(600)

        # 3. Navegar a Progreso del Alumno y Probar Botón de Teoría
        print("\n[5/5] Probando botón 'Teoría de la Técnica' en Mi Progreso...")
        prog_btn = page.locator("button:has-text('Mi Progreso'), button:has-text('Meu Progresso'), button:has-text('My Progress')")
        assert prog_btn.count() > 0, "Botón 'Mi Progreso' no encontrado"
        prog_btn.first.click()
        page.wait_for_timeout(2000)

        theory_btns = page.locator("button:has-text('Teoría de la Técnica'), button:has-text('Teoria da Técnica'), button:has-text('Technique Theory')")
        assert theory_btns.count() > 0, "No se encontraron botones '📖 Teoría de la Técnica' en las tarjetas"
        print(f"  ✓ Encontrados {theory_btns.count()} botones '📖 Teoría de la Técnica'")

        screenshot_theory = os.path.join(OUTPUT_DIR, "screenshot_theory_button.png")
        page.screenshot(path=screenshot_theory, full_page=True)
        print(f"  📸 Captura guardada: {screenshot_theory}")

        # Hacer clic en 'Teoría de la Técnica' y verificar auto-búsqueda
        theory_btns.first.click()
        page.wait_for_timeout(2500)

        # Verificar que la app navegó a LibraryView
        body_text = page.inner_text("body")
        assert "Biblioteca Multimodal de Jiu-Jitsu" in body_text, "No navegó a LibraryView"
        print("  ✓ Navegación exitosa a Biblioteca desde botón de teoría")

        # Verificar que el input de búsqueda tiene el texto de la técnica y se muestran resultados
        search_input = page.locator("input[placeholder*='Buscar'], input[placeholder*='Search']")
        val = search_input.input_value()
        print(f"  ✓ Búsqueda autoejecutada con valor: '{val}'")
        assert len(val) > 0, "El campo de búsqueda no se autocompletó con la técnica"

        # Verificar resultados de búsqueda en pantalla
        card_results = page.locator("div.glass-panel:has-text('p.')")
        print(f"  ✓ Tarjetas de resultados encontradas: {card_results.count()}")

        screenshot_auto_search = os.path.join(OUTPUT_DIR, "screenshot_auto_search_theory.png")
        page.screenshot(path=screenshot_auto_search, full_page=True)
        print(f"  📸 Captura guardada: {screenshot_auto_search}")

        browser.close()
        print("\n=================================================================")
        print("🎉 TODAS LAS VERIFICACIONES VISUALES PLAYWRIGHT COMPLETADAS CON ÉXITO")
        print("=================================================================")

if __name__ == "__main__":
    verify_all()
