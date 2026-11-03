import asyncio
import os
import sys
from playwright.async_api import async_playwright

CLOUDFLARE_URL = "https://platform-remainder-released-hans.trycloudflare.com"
ARTIFACTS_DIR = "/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6"

async def run_cloudflare_verification():
    print(f"🚀 Iniciando verificación de Playwright sobre Cloudflare Tunnel: {CLOUDFLARE_URL}")
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        print("1. Conectando al túnel público de Cloudflare...")
        response = await page.goto(CLOUDFLARE_URL, timeout=30000, wait_until="domcontentloaded")
        print(f"   Status HTTP inicial: {response.status}")
        assert response.status == 200, f"Error: Status HTTP {response.status} recibido desde Cloudflare."

        # Limpiar sesión previa y recargar
        await page.evaluate("localStorage.clear()")
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)

        print("2. Abriendo modal de autenticación...")
        avatar_btn = page.locator("[data-testid='user-avatar-btn']").first
        await avatar_btn.wait_for(state="visible", timeout=15000)
        await avatar_btn.click()
        await page.wait_for_timeout(800)

        print("3. Ingresando credenciales de Administrador (admin / admin123)...")
        u_input = page.locator("[data-testid='login-username-input']").first
        p_input = page.locator("[data-testid='login-password-input']").first
        submit_btn = page.locator("button[type='submit']").first

        await u_input.wait_for(state="visible", timeout=10000)
        await u_input.fill("admin")
        await p_input.fill("admin123")
        await page.wait_for_timeout(300)

        print("4. Enviando formulario de Login a través del túnel...")
        await submit_btn.click()

        # Esperar a que se refleje la sesión del administrador
        admin_name_locator = page.locator("text='Administrador General'").first
        await admin_name_locator.wait_for(state="visible", timeout=15000)
        print("   ✅ Sesión de administrador iniciada exitosamente.")

        # Captura de pantalla de Login Exitoso
        login_shot_path = os.path.join(ARTIFACTS_DIR, "screenshot_cloudflare_login.png")
        await page.screenshot(path=login_shot_path)
        print(f"   📸 Captura guardada: {login_shot_path}")

        print("5. Navegando a la vista de análisis / subida de video (VideoUpload)...")
        # El botón en el header dice 'Analizar Video' (o conmutar desde panel de admin)
        analyze_nav_btn = page.locator("button:has-text('Analizar Video'), button:has-text('Analisar Vídeo'), button:has-text('Analyze Video')").first
        if await analyze_nav_btn.is_visible():
            await analyze_nav_btn.click()
        else:
            await page.evaluate("window.__setAppState && window.__setAppState('IDLE')")

        await page.wait_for_timeout(1500)

        # Verificar presencia de elementos de VideoUpload (.upload-main-layout)
        upload_area = page.locator(".upload-main-layout, input[type='file']").first
        await upload_area.wait_for(state="visible", timeout=15000)
        print("   ✅ Vista VideoUpload renderizada correctamente a través del túnel.")

        # Captura de pantalla de VideoUpload
        videoupload_shot_path = os.path.join(ARTIFACTS_DIR, "screenshot_cloudflare_videoupload.png")
        await page.screenshot(path=videoupload_shot_path)
        print(f"   📸 Captura guardada: {videoupload_shot_path}")

        await browser.close()
        print("\n" + "=" * 70)
        print("✅ VERIFICACIÓN PLAYWRIGHT SOBRE CLOUDFLARE TUNNEL EXITOSA")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_cloudflare_verification())
