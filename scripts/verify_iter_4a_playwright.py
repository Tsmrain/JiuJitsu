import asyncio
import os
import psycopg2
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6"

def reset_carlos_pendiente():
    conn = psycopg2.connect(dbname='corpocmente', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET estado_suscripcion = 'pendiente', fecha_expiracion = NULL WHERE username = 'carlos';")
    conn.commit()
    cur.close()
    conn.close()
    print("Database: Carlos reseteado a 'pendiente'.")

async def login_user(page, username, password="password123"):
    avatar = page.locator("[data-testid='user-avatar-btn-mobile']:visible, [data-testid='user-avatar-btn']:visible").first
    await avatar.wait_for(state="visible", timeout=10000)
    await avatar.click()
    await page.wait_for_timeout(600)

    # Llenar formulario de login
    u_input = page.locator("input[type='text'], input[name='username']").first
    p_input = page.locator("input[type='password']").first
    await u_input.fill(username)
    await p_input.fill(password)
    submit_btn = page.locator("button[type='submit']").first
    await submit_btn.click()
    await page.wait_for_timeout(2500)

async def run_visual_tests():
    reset_carlos_pendiente()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # -------------------------------------------------------------
        # 1. Alumno Pendiente: Captura del Muro de Acceso (Bloqueo)
        # -------------------------------------------------------------
        print("\n1. Capturando Muro de Acceso (Alumno Pendiente)...")
        context_carlos = await browser.new_context(viewport={'width': 414, 'height': 896}) # iPhone XR / 11
        page_carlos = await context_carlos.new_page()

        await page_carlos.goto("http://localhost:5173", timeout=20000)
        await page_carlos.wait_for_timeout(1500)

        # Iniciar sesión como carlos
        await login_user(page_carlos, "carlos")

        # Tomar captura del Muro de Acceso
        path_bloqueo = os.path.join(ARTIFACTS_DIR, "screenshot_pase_tatami_bloqueo_alumno.png")
        await page_carlos.screenshot(path=path_bloqueo, full_page=False)
        print(f"✅ Captura Muro de Acceso guardada: {path_bloqueo}")

        # -------------------------------------------------------------
        # 2. Profesor Panel: Captura de Pases Pendientes y Activación
        # -------------------------------------------------------------
        print("\n2. Capturando Vista del Profesor (Pases Pendientes)...")
        context_mike = await browser.new_context(viewport={'width': 1280, 'height': 850})
        page_mike = await context_mike.new_page()

        # Aceptar alertas automáticamente si aparecen
        page_mike.on("dialog", lambda dialog: dialog.accept())

        await page_mike.goto("http://localhost:5173", timeout=20000)
        await page_mike.wait_for_timeout(1500)

        # Iniciar sesión como mike (profesor)
        await login_user(page_mike, "mike")

        # Ir a la pestaña "Pases Pendientes" usando data-testid
        pases_tab = page_mike.locator("[data-testid='tab-pases-pendientes']").first
        await pases_tab.wait_for(state="visible", timeout=10000)
        await pases_tab.click()
        await page_mike.wait_for_timeout(1500)

        path_profesor = os.path.join(ARTIFACTS_DIR, "screenshot_pase_tatami_profesor_pendientes.png")
        await page_mike.screenshot(path=path_profesor)
        print(f"✅ Captura Panel Profesor guardada: {path_profesor}")

        # Activar el pase de Carlos desde el botón con data-testid
        print("\n3. Activando Pase de Carlos desde la interfaz del profesor...")
        activar_btn = page_mike.locator("[data-testid='btn-activar-pase']").first
        await activar_btn.wait_for(state="visible", timeout=10000)
        await activar_btn.click()
        await page_mike.wait_for_timeout(2500)

        # -------------------------------------------------------------
        # 3. Alumno Activo: Captura de Alumno Habilitado con Pase Activo
        # -------------------------------------------------------------
        print("\n4. Capturando Vista del Alumno con Pase Activo...")
        # Recargar la página de Carlos y volver a iniciar sesión para obtener el estado de suscripción actualizado
        await page_carlos.reload()
        await page_carlos.wait_for_timeout(1500)

        await login_user(page_carlos, "carlos")

        path_activo = os.path.join(ARTIFACTS_DIR, "screenshot_pase_tatami_alumno_activo.png")
        await page_carlos.screenshot(path=path_activo, full_page=False)
        print(f"✅ Captura Alumno Activo guardada: {path_activo}")

        await browser.close()
        print("\n🎉 Todas las capturas visuales de la Iteración 4A generadas exitosamente.")

if __name__ == "__main__":
    asyncio.run(run_visual_tests())
