import os
import sys
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VIEWPORTS = [
    ("mobile", {"width": 390, "height": 844}, "iPhone 13 (390x844)"),
    ("tablet", {"width": 768, "height": 1024}, "iPad (768x1024)"),
    ("desktop", {"width": 1920, "height": 1080}, "Desktop HD (1920x1080)"),
]

def verify_responsive():
    print("=================================================================")
    print("🚀 PLAYWRIGHT EMPIRICAL VERIFICATION — ITERACIÓN 3Z")
    print("   (Responsive Design, Mobile-First, Touch UI & Zero Horizontal Scroll)")
    print("=================================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for vp_name, vp_dims, vp_label in VIEWPORTS:
            print(f"\n" + "-" * 65)
            print(f"📱 Probando Viewport: {vp_label}")
            print("-" * 65)

            context = browser.new_context(viewport=vp_dims)
            page = context.new_page()
            page.goto("http://localhost:5173")
            page.wait_for_timeout(1000)

            # ---------------------------------------------------------
            # 1. VERIFICACIÓN DE HEADER Y NAVEGACIÓN
            # ---------------------------------------------------------
            if vp_name == "mobile":
                # Botón de Hamburguesa debe estar visible con target >= 44x44
                h_btn = page.locator(".hamburger-btn")
                assert h_btn.is_visible(), "Fallo: Botón de Hamburguesa no visible en móvil"
                box = h_btn.bounding_box()
                assert box["width"] >= 44 and box["height"] >= 44, f"Fallo: Touch target hamburguesa muy pequeño: {box}"
                print(f"  ✓ Botón Hamburguesa visible con touch target adecuado: {box['width']}x{box['height']}px")

                # Navegación desktop debe estar oculta
                nav_desktop = page.locator(".nav-desktop")
                assert not nav_desktop.is_visible(), "Fallo: Navegación desktop visible en móvil"
                print("  ✓ Barra de navegación desktop oculta en móvil")

                # Probar apertura del Drawer
                h_btn.click()
                page.wait_for_timeout(600)
                drawer = page.locator(".mobile-drawer")
                assert drawer.is_visible(), "Fallo: Mobile drawer no visible tras tocar hamburguesa"
                print("  ✓ Mobile Drawer (menú lateral) desplegado correctamente")

                drawer_shot = os.path.join(OUTPUT_DIR, "drawer_mobile.png")
                page.screenshot(path=drawer_shot, full_page=False)
                print(f"  📸 Captura guardada: {drawer_shot}")

                # Cerrar drawer
                page.locator(".drawer-close-btn").click()
                page.wait_for_timeout(500)
                assert not drawer.is_visible(), "Fallo: Drawer no se cerró"
                print("  ✓ Mobile Drawer cerrado correctamente")

            # ---------------------------------------------------------
            # 2. AUTENTICACIÓN
            # ---------------------------------------------------------
            # Login como santi / admin
            avatar_btn = page.locator("header .user-nav > div:last-child, .nav-mobile-right > div:first-child").first
            avatar_btn.click()
            page.wait_for_timeout(600)

            page.fill("input[placeholder*='admin or'], input[type='text']", "santi")
            page.fill("input[placeholder*='••••'], input[type='password']", "password123")
            page.click("button[type='submit']")
            page.wait_for_timeout(1200)

            # ---------------------------------------------------------
            # 3. VISTA 1: FeedbackView
            # ---------------------------------------------------------
            print(f"\n  [Vista 1/4] Evaluando FeedbackView en {vp_name}...")
            page.evaluate("""() => {
                window.__setAppState('FEEDBACK', {
                    similitud: 78.4,
                    feedback: 'Ajusta la postura vertical y asegura el bloqueo de cadera.',
                    video_referencia_url: null,
                    url_video_alumno: '/static/frames/critico_test_eval.jpg',
                    timestamp_error_segundos: 2.35
                }, { id: 'tec_test', nombre: 'Escape de Montada' });
            }""")
            page.wait_for_timeout(1000)

            # Verificación CERO SCROLL HORIZONTAL
            sw = page.evaluate("() => document.documentElement.scrollWidth")
            iw = page.evaluate("() => window.innerWidth")
            assert sw <= iw, f"FALLO: Scroll horizontal en FeedbackView {vp_name} (scrollWidth={sw} > innerWidth={iw})"
            print(f"  ✓ CERO SCROLL HORIZONTAL en FeedbackView (scrollWidth={sw} <= innerWidth={iw})")

            shot_feedback = os.path.join(OUTPUT_DIR, f"feedback_{vp_name}.png")
            page.screenshot(path=shot_feedback, full_page=True)
            print(f"  📸 Captura guardada: {shot_feedback}")

            # ---------------------------------------------------------
            # 4. VISTA 2: StudentProgress
            # ---------------------------------------------------------
            print(f"\n  [Vista 2/4] Evaluando StudentProgress en {vp_name}...")
            page.evaluate("() => window.__setAppState('STUDENT_PROGRESS')")
            page.wait_for_timeout(2000)

            sw = page.evaluate("() => document.documentElement.scrollWidth")
            iw = page.evaluate("() => window.innerWidth")
            assert sw <= iw, f"FALLO: Scroll horizontal en StudentProgress {vp_name} (scrollWidth={sw} > innerWidth={iw})"
            print(f"  ✓ CERO SCROLL HORIZONTAL en StudentProgress (scrollWidth={sw} <= innerWidth={iw})")

            shot_progress = os.path.join(OUTPUT_DIR, f"student_progress_{vp_name}.png")
            page.screenshot(path=shot_progress, full_page=True)
            print(f"  📸 Captura guardada: {shot_progress}")

            # ---------------------------------------------------------
            # 5. VISTA 3: LibraryView
            # ---------------------------------------------------------
            print(f"\n  [Vista 3/4] Evaluando LibraryView en {vp_name}...")
            page.evaluate("""() => {
                window.__setAppState('LIBRARY', null, null, {
                    libraryInitialQuery: 'Escape de Montada',
                    libraryInitialImage: '/static/frames/critico_test_eval.jpg'
                });
            }""")
            page.wait_for_timeout(2000)

            sw = page.evaluate("() => document.documentElement.scrollWidth")
            iw = page.evaluate("() => window.innerWidth")
            assert sw <= iw, f"FALLO: Scroll horizontal en LibraryView {vp_name} (scrollWidth={sw} > innerWidth={iw})"
            print(f"  ✓ CERO SCROLL HORIZONTAL en LibraryView (scrollWidth={sw} <= innerWidth={iw})")

            shot_library = os.path.join(OUTPUT_DIR, f"library_{vp_name}.png")
            page.screenshot(path=shot_library, full_page=True)
            print(f"  📸 Captura guardada: {shot_library}")

            # Si es móvil, probar el modal de PDF y visor de 70vh
            if vp_name == "mobile":
                # Ir a la pestaña Catálogo y abrir el primer PDF
                page.locator("button:has-text('Catálogo'), button:has-text('Catálogo de Libros')").first.click()
                page.wait_for_timeout(1000)
                read_btn = page.locator("button:has-text('Leer Manual'), button:has-text('Visualizar')").first
                if read_btn.count() > 0:
                    read_btn.click()
                    page.wait_for_timeout(1500)
                    pdf_iframe = page.locator(".pdf-iframe-holder iframe")
                    assert pdf_iframe.is_visible(), "Visor de PDF iframe no visible en móvil"
                    sw_pdf = page.evaluate("() => document.documentElement.scrollWidth")
                    iw_pdf = page.evaluate("() => window.innerWidth")
                    assert sw_pdf <= iw_pdf, f"FALLO: Scroll horizontal en visor PDF (scrollWidth={sw_pdf} > innerWidth={iw_pdf})"
                    print(f"  ✓ CERO SCROLL HORIZONTAL en Visor Modal PDF móvil (scrollWidth={sw_pdf} <= innerWidth={iw_pdf})")

                    shot_pdf_mobile = os.path.join(OUTPUT_DIR, "library_pdf_modal_mobile.png")
                    page.screenshot(path=shot_pdf_mobile, full_page=False)
                    print(f"  📸 Captura guardada: {shot_pdf_mobile}")

                    # Cerrar modal
                    page.locator("button:has-text('Cerrar')").first.click()
                    page.wait_for_timeout(500)

            # ---------------------------------------------------------
            # 6. VISTA 4: AdminSucursales
            # ---------------------------------------------------------
            print(f"\n  [Vista 4/4] Evaluando AdminSucursales en {vp_name}...")
            # Login como admin
            page.evaluate("""() => {
                fetch('http://localhost:8000/api/v1/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username_or_email: 'admin', password: 'admin123' })
                }).then(r => r.json()).then(userData => {
                    window.__setAppState('ADMIN_PANEL');
                });
            }""")
            page.wait_for_timeout(1500)

            sw = page.evaluate("() => document.documentElement.scrollWidth")
            iw = page.evaluate("() => window.innerWidth")
            assert sw <= iw, f"FALLO: Scroll horizontal en AdminSucursales {vp_name} (scrollWidth={sw} > innerWidth={iw})"
            print(f"  ✓ CERO SCROLL HORIZONTAL en AdminSucursales (scrollWidth={sw} <= innerWidth={iw})")

            shot_admin = os.path.join(OUTPUT_DIR, f"admin_sucursales_{vp_name}.png")
            page.screenshot(path=shot_admin, full_page=True)
            print(f"  📸 Captura guardada: {shot_admin}")

            context.close()

        browser.close()
        print("\n" + "=" * 65)
        print("🎉 TODAS LAS VERIFICACIONES RESPONSIVE MULTI-VIEWPORT COMPLETADAS")
        print("   (Mobile: 390px, Tablet: 768px, Desktop: 1920px -> CERO SCROLL HORIZONTAL)")
        print("=" * 65)

if __name__ == "__main__":
    verify_responsive()
