#!/usr/bin/env python3
import sys
import os
import time
import json
import urllib.request
from playwright.sync_api import sync_playwright

output_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/baseline_before"
os.makedirs(output_dir, exist_ok=True)

# Helper to login via API and get user payload
def get_user_data(username, password):
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/auth/login",
        data=json.dumps({"username_or_email": username, "password": password}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

admin_data = get_user_data("admin", "admin123")
santi_data = get_user_data("santi", "password123")

# Fetch evaluation data for feedback view
eval_id = "b5a01854-3f66-47f4-b415-4e11da4d41a1"
eval_req = urllib.request.Request(
    f"http://localhost:8000/api/v1/evaluaciones/{eval_id}",
    headers={"Authorization": f"Bearer {santi_data['token']}"}
)
with urllib.request.urlopen(eval_req) as resp:
    eval_data = json.loads(resp.read().decode("utf-8"))

print("Admin:", admin_data["username"])
print("Santi:", santi_data["username"])
print("Eval status:", eval_data.get("estado"), "Similitud:", eval_data.get("similitud"))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    
    # 1. Login view
    print("Capturing login.png...")
    page.goto("http://localhost:5173")
    page.wait_for_selector(".app-container")
    time.sleep(1)
    page.evaluate("""() => {
        const el = document.querySelector('.app-container');
        const key = Object.keys(el).find(k => k.startsWith('__reactFiber'));
        let fiber = el[key];
        while (fiber && fiber.type?.name !== 'App') fiber = fiber.return;
        let hook = fiber.memoizedState;
        // Hook 7 is setIsLoginOpen
        for (let i = 0; i < 7; i++) hook = hook.next;
        hook.queue.dispatch(true);
    }""")
    time.sleep(0.5)
    page.screenshot(path=f"{output_dir}/login.png")
    print(f"Saved {output_dir}/login.png")

    # 2. Upload view (logged in as santi)
    print("Capturing upload.png...")
    page.evaluate("""(userData) => {
        const el = document.querySelector('.app-container');
        const key = Object.keys(el).find(k => k.startsWith('__reactFiber'));
        let fiber = el[key];
        while (fiber && fiber.type?.name !== 'App') fiber = fiber.return;
        
        let hooks = [];
        let h = fiber.memoizedState;
        while (h) { hooks.push(h); h = h.next; }
        
        // hooks[7]: setIsLoginOpen(false)
        hooks[7].queue.dispatch(false);
        // hooks[5]: setUser(userData)
        hooks[5].queue.dispatch(userData);
        // hooks[0]: setAppState('IDLE')
        hooks[0].queue.dispatch('IDLE');
    }""", santi_data)
    time.sleep(1)
    page.screenshot(path=f"{output_dir}/upload.png")
    print(f"Saved {output_dir}/upload.png")

    # 3. Feedback view
    print("Capturing feedback.png...")
    feedback_result = {
        "similitud": eval_data.get("similitud", 25.72),
        "feedback": eval_data.get("feedback", ""),
        "video_referencia_url": eval_data.get("video_referencia_url", ""),
        "video_referencia_nombre": eval_data.get("video_referencia_nombre", "Demostración Oficial"),
        "video_referencia_profesor_nombre": eval_data.get("video_referencia_profesor_nombre", "Mestre Mike Baigorria"),
        "frame_error_url": eval_data.get("frame_error_url", ""),
    }
    tecnica_info = {
        "id": "30a4afe4-23cc-4479-9f14-4f6d867de7dd",
        "nombre": "Mount Escape (Upa)",
        "profesorRef": "Mestre Mike Baigorria"
    }
    page.evaluate("""({ result, tecnica }) => {
        const el = document.querySelector('.app-container');
        const key = Object.keys(el).find(k => k.startsWith('__reactFiber'));
        let fiber = el[key];
        while (fiber && fiber.type?.name !== 'App') fiber = fiber.return;
        
        let hooks = [];
        let h = fiber.memoizedState;
        while (h) { hooks.push(h); h = h.next; }
        
        // hooks[2]: setResult
        hooks[2].queue.dispatch(result);
        // hooks[3]: setSelectedTecnica
        hooks[3].queue.dispatch(tecnica);
        // hooks[0]: setAppState('FEEDBACK')
        hooks[0].queue.dispatch('FEEDBACK');
    }""", {"result": feedback_result, "tecnica": tecnica_info})
    time.sleep(1)
    page.screenshot(path=f"{output_dir}/feedback.png")
    print(f"Saved {output_dir}/feedback.png")

    # 4. Admin view (logged in as admin)
    print("Capturing admin.png...")
    page.evaluate("""(adminUser) => {
        const el = document.querySelector('.app-container');
        const key = Object.keys(el).find(k => k.startsWith('__reactFiber'));
        let fiber = el[key];
        while (fiber && fiber.type?.name !== 'App') fiber = fiber.return;
        
        let hooks = [];
        let h = fiber.memoizedState;
        while (h) { hooks.push(h); h = h.next; }
        
        // hooks[5]: setUser(adminUser)
        hooks[5].queue.dispatch(adminUser);
        // hooks[0]: setAppState('ADMIN_PANEL')
        hooks[0].queue.dispatch('ADMIN_PANEL');
    }""", admin_data)
    time.sleep(1)
    page.screenshot(path=f"{output_dir}/admin.png")
    print(f"Saved {output_dir}/admin.png")

    browser.close()
    print("Done! All 4 screenshots captured successfully.")

