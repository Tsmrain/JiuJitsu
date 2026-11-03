import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6"

async def run_visual_verification():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # ------------------------------------------------------------------
        # 1. VERIFICACIÓN: LOGIN CON INPUTS VACÍOS Y TOGGLE DE CONTRASEÑA (👁️)
        # ------------------------------------------------------------------
        print("\n1. Verificando LoginModal: Inputs vacíos y toggle 👁️ / 🙈...")
        context_login = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page_login = await context_login.new_page()

        # Limpiar localStorage para asegurar estado no autenticado
        await page_login.goto("http://localhost:5173", timeout=20000)
        await page_login.evaluate("localStorage.clear()")
        await page_login.reload()
        await page_login.wait_for_timeout(1500)

        # Abrir LoginModal haciendo clic en el avatar / botón de inicio de sesión
        avatar_btn = page_login.locator("[data-testid='user-avatar-btn']:visible, [data-testid='user-avatar-btn-mobile']:visible").first
        await avatar_btn.wait_for(state="visible", timeout=10000)
        await avatar_btn.click()
        await page_login.wait_for_timeout(600)

        # Localizar inputs de usuario y contraseña
        u_input = page_login.locator("[data-testid='login-username-input']").first
        p_input = page_login.locator("[data-testid='login-password-input']").first
        toggle_btn = page_login.locator("[data-testid='toggle-login-password-btn']").first

        await u_input.wait_for(state="visible", timeout=5000)
        await p_input.wait_for(state="visible", timeout=5000)

        # Aserción 1: Ambos inputs inician estrictamente vacíos ("")
        u_val = await u_input.input_value()
        p_val = await p_input.input_value()
        print(f"   Valor inicial de username input: '{u_val}'")
        print(f"   Valor inicial de password input: '{p_val}'")
        assert u_val == "", f"ERROR: El campo de usuario NO está vacío: '{u_val}'"
        assert p_val == "", f"ERROR: El campo de contraseña NO está vacío: '{p_val}'"

        # Aserción 2: Escribir contraseña y probar toggle
        test_pass = "SegredoTatami2026!"
        await u_input.fill("santi")
        await p_input.fill(test_pass)
        
        type_initial = await p_input.get_attribute("type")
        print(f"   Tipo de input antes de toggle: '{type_initial}'")
        assert type_initial == "password", "ERROR: El input debería iniciar como 'password'"

        # Clic en el botón del ojo para revelar
        await toggle_btn.click()
        await page_login.wait_for_timeout(300)
        type_toggled = await p_input.get_attribute("type")
        print(f"   Tipo de input después de toggle: '{type_toggled}'")
        assert type_toggled == "text", "ERROR: El input debería cambiar a 'text' tras clic en 👁️"

        # Guardar captura de Login con ojo activo
        path_login_shot = os.path.join(ARTIFACTS_DIR, "screenshot_login_empty_and_eye_toggle.png")
        await page_login.screenshot(path=path_login_shot)
        print(f"✅ Captura Login (vacío + ojo revelado) guardada en: {path_login_shot}")

        # ------------------------------------------------------------------
        # 2. VERIFICACIÓN: UI FULL-SCREEN DE ANÁLISIS DE VIDEO (1920x1080)
        # ------------------------------------------------------------------
        print("\n2. Verificando UI Full-Screen de VideoUpload en Desktop 1920x1080...")
        context_desktop = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page_desktop = await context_desktop.new_page()

        await page_desktop.goto("http://localhost:5173", timeout=20000)
        await page_desktop.evaluate("localStorage.clear()")
        await page_desktop.reload()
        await page_desktop.wait_for_timeout(1000)

        # Iniciar sesión como alumno Santi
        avatar_btn_d = page_desktop.locator("[data-testid='user-avatar-btn']:visible, [data-testid='user-avatar-btn-mobile']:visible").first
        await avatar_btn_d.wait_for(state="visible", timeout=10000)
        await avatar_btn_d.click()
        await page_desktop.wait_for_timeout(500)

        u_input_d = page_desktop.locator("[data-testid='login-username-input']").first
        p_input_d = page_desktop.locator("[data-testid='login-password-input']").first
        await u_input_d.fill("santi")
        await p_input_d.fill("password123")
        submit_btn_d = page_desktop.locator("button[type='submit']").first
        await submit_btn_d.click()
        await page_desktop.wait_for_timeout(2500)

        # Esperar a que los instructores y técnicas carguen
        dropzone = page_desktop.locator(".drop-zone").first
        await dropzone.wait_for(state="visible", timeout=10000)
        await page_desktop.wait_for_timeout(1500)

        # Verificar dimensiones del contenedor principal
        upload_container = page_desktop.locator(".upload-container").first
        bounding_box = await upload_container.bounding_box()
        print(f"   Dimensiones de .upload-container: {bounding_box}")
        assert bounding_box["width"] > 900, f"ERROR: El contenedor sigue angosto ({bounding_box['width']}px) en vez de aprovechar la pantalla"

        path_desktop_shot = os.path.join(ARTIFACTS_DIR, "screenshot_videoupload_fullscreen_desktop.png")
        await page_desktop.screenshot(path=path_desktop_shot)
        print(f"✅ Captura VideoUpload Desktop 1920x1080 guardada en: {path_desktop_shot}")

        await browser.close()
        print("\n" + "=" * 70)
        print("✅ TODAS LAS PRUEBAS VISUALES PLAYWRIGHT PASARON EXITOSAMENTE")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_visual_verification())
