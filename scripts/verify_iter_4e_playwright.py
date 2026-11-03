import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6"

async def run_visual_verification():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        print("1. Cargando aplicación en estado limpio...")
        await page.goto("http://localhost:5173", timeout=20000)
        await page.evaluate("localStorage.clear()")
        await page.reload()
        await page.wait_for_timeout(1500)

        print("2. Abriendo LoginModal...")
        avatar_btn = page.locator("[data-testid='user-avatar-btn']:visible, [data-testid='user-avatar-btn-mobile']:visible").first
        await avatar_btn.wait_for(state="visible", timeout=10000)
        await avatar_btn.click()
        await page.wait_for_timeout(600)

        # Localizar inputs y botón de toggle
        u_input = page.locator("[data-testid='login-username-input']").first
        p_input = page.locator("[data-testid='login-password-input']").first
        toggle_btn = page.locator("[data-testid='toggle-login-password-btn']").first

        await u_input.wait_for(state="visible", timeout=5000)
        await p_input.wait_for(state="visible", timeout=5000)
        await toggle_btn.wait_for(state="visible", timeout=5000)

        # Escribir contraseña para probar visualización
        await u_input.fill("admin")
        await p_input.fill("SuperSecretProdKey2026!")

        # Verificar que el botón contiene elemento SVG y ningún emoji
        btn_html = await toggle_btn.inner_html()
        print(f"   Contenido HTML del toggle button: {btn_html[:80]}...")
        assert "<svg" in btn_html, "ERROR: No se encontró etiqueta SVG en el botón de toggle."
        assert "👁" not in btn_html, "ERROR: El emoji de ojo sigue presente en el botón."
        assert "🙈" not in btn_html, "ERROR: El emoji de mono sigue presente en el botón."

        # Clic en el SVG de toggle para revelar contraseña
        print("3. Haciendo clic en botón SVG para alternar visibilidad de contraseña...")
        await toggle_btn.click()
        await page.wait_for_timeout(400)

        input_type_after = await p_input.get_attribute("type")
        print(f"   Tipo de input tras alternar con SVG: '{input_type_after}'")
        assert input_type_after == "text", "ERROR: El input debería ser de tipo 'text'."

        btn_html_toggled = await toggle_btn.inner_html()
        assert "<svg" in btn_html_toggled, "ERROR: El estado revelado también debe ser un SVG."
        assert "👁" not in btn_html_toggled
        assert "🙈" not in btn_html_toggled

        # Capturar pantalla
        path_shot = os.path.join(ARTIFACTS_DIR, "screenshot_login_svg_toggle.png")
        await page.screenshot(path=path_shot)
        print(f"✅ Captura LoginModal con Iconos SVG profesionales guardada en: {path_shot}")

        await browser.close()
        print("\n" + "=" * 70)
        print("✅ VERIFICACIÓN VISUAL PLAYWRIGHT (FASE 1 Y FASE 5) EXITOSA")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_visual_verification())

