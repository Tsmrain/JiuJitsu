import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6"

async def login_user(page, username, password="password123"):
    avatar = page.locator("[data-testid='user-avatar-btn']:visible, [data-testid='user-avatar-btn-mobile']:visible").first
    await avatar.wait_for(state="visible", timeout=10000)
    await avatar.click()
    await page.wait_for_timeout(600)

    u_input = page.locator("input[type='text'], input[name='username']").first
    p_input = page.locator("input[type='password']").first
    await u_input.fill(username)
    await p_input.fill(password)
    submit_btn = page.locator("button[type='submit']").first
    await submit_btn.click()
    await page.wait_for_timeout(2500)

async def run_visual_tests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # -------------------------------------------------------------
        # 1. Pases Pendientes de Milton Flores (Casa Matriz - 10 pendientes)
        # -------------------------------------------------------------
        print("\n1. Capturando Pases Pendientes de Prof. Milton Flores...")
        context_milton = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page_milton = await context_milton.new_page()

        await page_milton.goto("http://localhost:5173", timeout=20000)
        await page_milton.wait_for_timeout(1500)

        await login_user(page_milton, "milton")

        # Click en la pestaña de Pases Pendientes
        pases_tab = page_milton.locator("[data-testid='tab-pases-pendientes']").first
        await pases_tab.wait_for(state="visible", timeout=10000)
        await pases_tab.click()
        await page_milton.wait_for_timeout(2000)

        path_milton = os.path.join(ARTIFACTS_DIR, "screenshot_pases_pendientes_milton.png")
        await page_milton.screenshot(path=path_milton)
        print(f"✅ Captura Milton Flores (Pases Pendientes) guardada: {path_milton}")

        # -------------------------------------------------------------
        # 2. Alumno Activo (matriz_act_1)
        # -------------------------------------------------------------
        print("\n2. Capturando Vista y Perfil de Alumno Activo...")
        context_activo = await browser.new_context(viewport={'width': 414, 'height': 896}) # Mobile
        page_activo = await context_activo.new_page()

        await page_activo.goto("http://localhost:5173", timeout=20000)
        await page_activo.wait_for_timeout(1500)

        await login_user(page_activo, "matriz_act_1")
        await page_activo.wait_for_timeout(1500)

        path_activo = os.path.join(ARTIFACTS_DIR, "screenshot_alumno_activo.png")
        await page_activo.screenshot(path=path_activo, full_page=False)
        print(f"✅ Captura Alumno Activo guardada: {path_activo}")

        # -------------------------------------------------------------
        # 3. Alumno Expirado (knockout_exp_1)
        # -------------------------------------------------------------
        print("\n3. Capturando Vista y Muro de Alumno Expirado...")
        context_exp = await browser.new_context(viewport={'width': 414, 'height': 896}) # Mobile
        page_exp = await context_exp.new_page()

        await page_exp.goto("http://localhost:5173", timeout=20000)
        await page_exp.wait_for_timeout(1500)

        await login_user(page_exp, "knockout_exp_1")
        await page_exp.wait_for_timeout(1500)

        path_expirado = os.path.join(ARTIFACTS_DIR, "screenshot_alumno_expirado.png")
        await page_exp.screenshot(path=path_expirado, full_page=False)
        print(f"✅ Captura Alumno Expirado guardada: {path_expirado}")

        # -------------------------------------------------------------
        # 4. Modal de Perfil de Alumno Expirado
        # -------------------------------------------------------------
        print("\n4. Capturando Modal de Perfil de Alumno...")
        avatar_btn = page_exp.locator("[data-testid='user-avatar-btn-mobile']:visible, [data-testid='user-avatar-btn']:visible").first
        await avatar_btn.click()
        await page_exp.wait_for_timeout(1000)

        path_perfil = os.path.join(ARTIFACTS_DIR, "screenshot_perfil_alumno_expirado.png")
        await page_exp.screenshot(path=path_perfil)
        print(f"✅ Captura Modal de Perfil Alumno Expirado guardada: {path_perfil}")

        await browser.close()
        print("\n🎉 Todas las capturas visuales de la Iteración 4B generadas exitosamente.")

if __name__ == "__main__":
    asyncio.run(run_visual_tests())

