import os
import sys
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "/Users/santiago/.gemini/antigravity/brain/d07a6193-1740-4c78-b85f-7e4513ae45a6"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def verify_all():
    print("=================================================================")
    print("🚀 PLAYWRIGHT EMPIRICAL UX, I18N AND VIDEO VERIFICATION (3W)")
    print("=================================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 950})
        page = context.new_page()

        # Step 1: Open app
        print("\n[1/5] Loading application at http://localhost:5173...")
        page.goto("http://localhost:5173")
        page.wait_for_timeout(1000)

        # Set language to Portuguese (PT)
        page.evaluate("() => localStorage.setItem('app_idioma', 'pt')")
        page.reload()
        page.wait_for_timeout(1000)

        # Login as student 'santi'
        print("\n[2/5] Authenticating as student 'santi' (PT)...")
        sign_in_trigger = page.locator("div[title*='Entrar'], div[title*='Perfil'], button:has-text('Entrar'), button:has-text('Sign In')")
        if sign_in_trigger.count() > 0:
            sign_in_trigger.first.click()
            page.wait_for_timeout(500)
            page.fill("input[name='username_or_email'], input[type='text']", "santi")
            page.fill("input[name='password'], input[type='password']", "password123")
            page.click("button[type='submit']")
            page.wait_for_timeout(1500)

        # Ensure selector is PT
        lang_sel = page.locator("select[title*='Idioma'], select[title*='Language']")
        if lang_sel.count() > 0:
            lang_sel.select_option("pt")
            page.wait_for_timeout(600)

        # Step 2: Test StudentProgress
        print("\n[3/5] Testing StudentProgress View in Portuguese...")
        prog_btn = page.locator("button:has-text('Meu Progresso')")
        if prog_btn.count() > 0:
            prog_btn.click()
            page.wait_for_timeout(2000)

            body_text = page.inner_text("body")
            print("Checking StudentProgress strings in PT:")
            assert "Meu Progresso" in body_text, "Failed: 'Meu Progresso' not found"
            print("  ✓ 'Meu Progresso' found")
            assert "Revise suas correções técnicas" in body_text, "Failed: Portuguese subtitle not found"
            print("  ✓ Portuguese subtitle found")
            assert "Demonstração do Professor" in body_text, "Failed: 'Demonstração do Professor' not found"
            print("  ✓ 'Demonstração do Professor' found")
            assert "Meu Vídeo" in body_text, "Failed: 'Meu Vídeo' not found"
            print("  ✓ 'Meu Vídeo' found")
            assert "de similaridade" in body_text, "Failed: 'de similaridade' not found"
            print("  ✓ 'de similaridade' found")

            # Check that videos in progress cards are loaded
            videos = page.locator("video")
            print(f"  ✓ Found {videos.count()} <video> elements in StudentProgress")
            for i in range(min(2, videos.count())):
                src = videos.nth(i).locator("source").get_attribute("src") or videos.nth(i).get_attribute("src")
                print(f"    - Video {i} source: {src}")

            screenshot_progress = os.path.join(OUTPUT_DIR, "screenshot_student_progress_pt.png")
            page.screenshot(path=screenshot_progress, full_page=True)
            print(f"  📸 Screenshot saved: {screenshot_progress}")

        # Step 3: Test LibraryView Initial State
        print("\n[4/5] Testing LibraryView Initial State in Portuguese...")
        lib_btn = page.locator("button:has-text('Biblioteca')")
        if lib_btn.count() > 0:
            lib_btn.click()
            page.wait_for_timeout(2500) # wait for initial search 'guardia' to complete

            body_text = page.inner_text("body")
            assert "Biblioteca Multimodal de Jiu-Jitsu" in body_text, "Failed: Library title in PT not found"
            print("  ✓ 'Biblioteca Multimodal de Jiu-Jitsu' found")
            assert "Consulte manuais oficiais" in body_text, "Failed: Library subtitle in PT not found"
            print("  ✓ 'Consulte manuais oficiais' found")
            assert "Buscar" in body_text, "Failed: 'Buscar' button not found"
            print("  ✓ 'Buscar' button found")

            # Verify initial cards are populated
            card_count = page.locator("div.glass-panel:has-text('p.')").count()
            print(f"  ✓ Initial cards populated on mount without search: {card_count} cards")
            assert card_count > 0, "Failed: Library has NO initial cards on mount!"

            screenshot_lib = os.path.join(OUTPUT_DIR, "screenshot_library_view_pt.png")
            page.screenshot(path=screenshot_lib, full_page=True)
            print(f"  📸 Screenshot saved: {screenshot_lib}")

            # Close library
            close_btn = page.locator("button:has-text('Fechar')")
            if close_btn.count() > 0:
                close_btn.first.click()
                page.wait_for_timeout(600)

        # Step 4: Test FeedbackView in Portuguese
        print("\n[5/5] Testing FeedbackView in Portuguese with Coach Video...")
        # Use our test hook to transition to FEEDBACK
        page.evaluate("""
        () => {
            window.__setAppState('FEEDBACK', {
                similitud: 60.7,
                feedback: "### Correção Biomecânica\\n\\n1. **Postura Vertical:** Mantenha a coluna ereta ao subir.\\n2. **Pressão dos Joelhos:** Bloqueie o quadril adversário com os joelhos fechados.",
                feedback_summary: "Erro na postura vertical e controle de coxas",
                timestamp_error_segundos: 2.45,
                url_video_alumno: "/static/videos/413e62f2-92e0-40d3-bb0c-799a0da954ea.mp4",
                video_referencia_url: "/static/videos/67beb825-87d1-4c46-8380-9b0cb6ef0489.mp4",
                video_referencia_nombre: "67beb825-87d1-4c46-8380-9b0cb6ef0489.mp4",
                video_referencia_profesor_nombre: "Mestre Mike",
                nombres_articulaciones_criticas: ["left_knee", "right_knee", "spine"]
            }, {
                id: "59760071-a3ce-46ec-b9d9-75b6dc47eba7",
                nombre: "Escaping Closed Guard Stand UP",
                profesorRef: "Mestre Mike"
            });
        }
        """)
        page.wait_for_timeout(1500)

        fb_body = page.inner_text("body")
        print("Checking FeedbackView strings in PT:")
        assert "Análise Biomecânica Concluída" in fb_body, "Failed: 'Análise Biomecânica Concluída' not found"
        print("  ✓ 'Análise Biomecânica Concluída' found")
        assert "TÉCNICA AVALIADA" in fb_body, "Failed: 'TÉCNICA AVALIADA' not found"
        print("  ✓ 'TÉCNICA AVALIADA' found")
        assert "VÍDEO DE REFERÊNCIA DO INSTRUTOR" in fb_body, "Failed: 'VÍDEO DE REFERÊNCIA DO INSTRUTOR' not found"
        print("  ✓ 'VÍDEO DE REFERÊNCIA DO INSTRUTOR' found")
        assert "VÍDEO DO ALUNO" in fb_body, "Failed: 'VÍDEO DO ALUNO' not found"
        print("  ✓ 'VÍDEO DO ALUNO' found")
        assert "Pular para o Erro" in fb_body, "Failed: 'Pular para o Erro' not found"
        print("  ✓ 'Pular para o Erro' found")
        assert "ANÁLISE TÉCNICA DE IA" in fb_body, "Failed: 'ANÁLISE TÉCNICA DE IA' not found"
        print("  ✓ 'ANÁLISE TÉCNICA DE IA' found")
        assert "PRÁTICA RECOMENDADA" in fb_body, "Failed: 'PRÁTICA RECOMENDADA' not found"
        print("  ✓ 'PRÁTICA RECOMENDADA' found")
        assert "Analisar Outra Técnica" in fb_body, "Failed: 'Analisar Outra Técnica' not found"
        print("  ✓ 'Analisar Outra Técnica' found")

        # Verify coach video element
        coach_video = page.locator("section:has-text('VÍDEO DE REFERÊNCIA DO INSTRUTOR') video")
        assert coach_video.count() > 0, "Coach video element not found!"
        coach_video_src = coach_video.locator("source").get_attribute("src")
        print(f"  ✓ Coach video element source: {coach_video_src}")
        assert coach_video_src == "http://localhost:8000/static/videos/67beb825-87d1-4c46-8380-9b0cb6ef0489.mp4"

        screenshot_feedback = os.path.join(OUTPUT_DIR, "screenshot_feedback_view_pt.png")
        page.screenshot(path=screenshot_feedback, full_page=True)
        print(f"  📸 Screenshot saved: {screenshot_feedback}")

        browser.close()
        print("\n=================================================================")
        print("✅ ALL PLAYWRIGHT UX & I18N VERIFICATIONS PASSED WITH FLYING COLORS!")
        print("=================================================================")

if __name__ == "__main__":
    verify_all()
